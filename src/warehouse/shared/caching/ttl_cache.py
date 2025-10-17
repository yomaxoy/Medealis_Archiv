"""
TTL Cache Decorator - Time-To-Live Caching für Method-Level Optimierung

Bietet einfaches, thread-safe Caching mit automatischer Ablaufzeit.
Reduziert wiederholte DB-Abfragen und teure Operationen.
"""

import time
import threading
import hashlib
import pickle
import logging
from functools import wraps
from typing import Any, Dict, Optional, Callable, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Einzelner Cache-Eintrag mit Metadaten."""
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: int) -> bool:
        """Prüft ob Eintrag abgelaufen ist."""
        return (time.time() - self.timestamp) > ttl_seconds

    def touch(self):
        """Aktualisiert Access-Statistiken."""
        self.access_count += 1
        self.last_access = time.time()


class TTLCache:
    """
    Thread-safe TTL Cache mit LRU Eviction.

    Features:
    - Automatische Ablaufzeit (TTL)
    - LRU Eviction bei Größenlimit
    - Thread-safe
    - Statistiken
    - Memory-effizient
    """

    def __init__(self, maxsize: int = 128, ttl_seconds: int = 300):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistiken
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def _generate_key(self, args: Tuple, kwargs: Dict) -> str:
        """Generiert konsistenten Cache-Key aus Argumenten."""
        try:
            # Erstelle serialisierbaren Key
            key_data = {
                'args': args,
                'kwargs': sorted(kwargs.items())
            }
            serialized = pickle.dumps(key_data, protocol=pickle.HIGHEST_PROTOCOL)
            return hashlib.md5(serialized).hexdigest()
        except Exception as e:
            # Fallback für nicht-serialisierbare Objekte
            logger.warning(f"Key generation failed, using string fallback: {e}")
            return str(hash((str(args), str(sorted(kwargs.items())))))

    def get(self, key: str) -> Optional[Any]:
        """Holt Wert aus Cache wenn vorhanden und nicht abgelaufen."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Prüfe Ablaufzeit
            if entry.is_expired(self.ttl_seconds):
                del self._cache[key]
                self._expirations += 1
                self._misses += 1
                return None

            # Cache Hit - aktualisiere Access-Info und verschiebe nach Ende (LRU)
            entry.touch()
            self._cache.move_to_end(key)
            self._hits += 1

            return entry.value

    def put(self, key: str, value: Any) -> None:
        """Speichert Wert in Cache."""
        with self._lock:
            # Entferne älteste Einträge wenn Cache voll
            while len(self._cache) >= self.maxsize:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1

            # Speichere neuen Eintrag
            self._cache[key] = CacheEntry(value=value, timestamp=time.time())

    def clear(self) -> None:
        """Leert kompletten Cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0

    def cleanup_expired(self) -> int:
        """Entfernt alle abgelaufenen Einträge. Gibt Anzahl zurück."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired(self.ttl_seconds)
            ]

            for key in expired_keys:
                del self._cache[key]
                self._expirations += 1

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / max(total_requests, 1) * 100

            return {
                'size': len(self._cache),
                'maxsize': self.maxsize,
                'ttl_seconds': self.ttl_seconds,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'evictions': self._evictions,
                'expirations': self._expirations,
                'total_requests': total_requests
            }


def ttl_cache(seconds: int = 300, maxsize: int = 128, key_prefix: Optional[str] = None):
    """
    TTL Cache Decorator für Methoden.

    Args:
        seconds: TTL in Sekunden (default: 5 Minuten)
        maxsize: Maximale Cache-Größe (default: 128)
        key_prefix: Optional Prefix für Cache-Keys

    Usage:
        @ttl_cache(seconds=600, maxsize=64)
        def expensive_method(self, param1, param2):
            return do_expensive_operation(param1, param2)
    """

    def decorator(func: Callable) -> Callable:
        # Erstelle Cache-Instanz für diese Funktion
        cache = TTLCache(maxsize=maxsize, ttl_seconds=seconds)

        # Füge Cache-Referenz zur Funktion hinzu für externe Zugriffe
        func._cache = cache

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generiere Cache-Key
            try:
                # Entferne 'self' aus args für Instanz-Methoden
                cache_args = args[1:] if args and hasattr(args[0], '__dict__') else args
                key_base = cache._generate_key(cache_args, kwargs)

                # Füge Prefix hinzu wenn vorhanden
                cache_key = f"{key_prefix}:{key_base}" if key_prefix else key_base

                # Versuche aus Cache zu laden
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result

                # Cache Miss - führe Funktion aus
                logger.debug(f"Cache miss for {func.__name__}")
                result = func(*args, **kwargs)

                # Speichere Result im Cache
                cache.put(cache_key, result)

                return result

            except Exception as e:
                # Bei Cache-Fehlern führe Funktion normal aus
                logger.warning(f"Cache error for {func.__name__}: {e}")
                return func(*args, **kwargs)

        # Füge Cache-Management Methoden hinzu
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats
        wrapper.cache_cleanup = cache.cleanup_expired

        return wrapper

    return decorator


def clear_all_caches():
    """Hilfsfunktion um alle TTL Caches zu leeren."""
    import gc
    cleared = 0

    for obj in gc.get_objects():
        try:
            if hasattr(obj, '_cache') and isinstance(obj._cache, TTLCache):
                obj._cache.clear()
                cleared += 1
        except (AttributeError, TypeError):
            # Skip objects that cause issues during inspection
            continue

    logger.info(f"Cleared {cleared} TTL caches")
    return cleared


def get_cache_stats_summary() -> Dict[str, Any]:
    """Sammelt Statistiken aller TTL Caches."""
    import gc
    total_stats = {
        'total_caches': 0,
        'total_size': 0,
        'total_hits': 0,
        'total_misses': 0,
        'average_hit_rate': 0,
        'caches': []
    }

    for obj in gc.get_objects():
        try:
            if hasattr(obj, '_cache') and isinstance(obj._cache, TTLCache):
                stats = obj._cache.get_stats()
                stats['function_name'] = getattr(obj, '__name__', 'unknown')
                total_stats['caches'].append(stats)

                total_stats['total_caches'] += 1
                total_stats['total_size'] += stats['size']
                total_stats['total_hits'] += stats['hits']
                total_stats['total_misses'] += stats['misses']
        except (AttributeError, TypeError):
            # Skip objects that cause issues during inspection
            continue

    # Berechne durchschnittliche Hit Rate
    if total_stats['total_caches'] > 0:
        total_requests = total_stats['total_hits'] + total_stats['total_misses']
        if total_requests > 0:
            total_stats['average_hit_rate'] = round(
                total_stats['total_hits'] / total_requests * 100, 2
            )

    return total_stats