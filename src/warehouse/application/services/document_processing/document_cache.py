"""
Document Cache - Einfacher Cache für Claude API Responses
Kosteneinsparung durch Caching von bereits analysierten Dokumenten
"""

import hashlib
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DocumentCache:
    """
    Einfacher SQLite-basierter Cache für Claude API Responses.
    Keine Over-Engineering - bewusst einfach gehalten.
    """

    def __init__(self, cache_db_path: str = "cache/document_analysis.db"):
        self.cache_db_path = Path(cache_db_path)
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(days=30)
        self.logger = logger
        self._init_database()

    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Holt gecachtes Ergebnis falls vorhanden und gültig.

        Args:
            cache_key: Eindeutiger Cache-Key

        Returns:
            Gecachtes Ergebnis oder None
        """
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Suche nach Cache-Entry
                cursor.execute(
                    "SELECT result_json, expires_at FROM document_cache WHERE cache_key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()

                if not row:
                    self.logger.debug(f"Cache miss for key: {cache_key[:16]}...")
                    return None

                result_json, expires_at_str = row

                # Prüfe Ablaufzeit
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now() > expires_at:
                    self.logger.debug(f"Cache expired for key: {cache_key[:16]}...")
                    # Expired entry löschen
                    cursor.execute("DELETE FROM document_cache WHERE cache_key = ?", (cache_key,))
                    conn.commit()
                    return None

                # Cache hit!
                self.logger.info(f"Cache hit for key: {cache_key[:16]}...")
                return json.loads(result_json)

        except Exception as e:
            self.logger.error(f"Error reading from cache: {e}")
            return None

    def cache_result(
        self,
        cache_key: str,
        result: Dict[str, Any],
        ttl: timedelta = None
    ) -> bool:
        """
        Speichert Ergebnis im Cache.

        Args:
            cache_key: Eindeutiger Cache-Key
            result: Zu cachendes Ergebnis
            ttl: Time-to-live (default: 30 Tage)

        Returns:
            True wenn erfolgreich gespeichert
        """
        if ttl is None:
            ttl = self.default_ttl

        try:
            expires_at = datetime.now() + ttl

            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Insert or replace
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO document_cache
                    (cache_key, result_json, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        cache_key,
                        json.dumps(result, ensure_ascii=False),
                        datetime.now().isoformat(),
                        expires_at.isoformat()
                    )
                )
                conn.commit()

            self.logger.info(f"Cached result for key: {cache_key[:16]}...")
            return True

        except Exception as e:
            self.logger.error(f"Error caching result: {e}")
            return False

    def generate_cache_key(
        self,
        document_data: bytes,
        document_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generiert eindeutigen Cache-Key.

        OPTIMIERUNG: Filtert validation-spezifische Keys aus dem Context um
        besseres Caching zu ermöglichen (gleiche Dokumente = gleicher Cache).

        Args:
            document_data: Dokument-Bytes
            document_type: Dokumenttyp
            context: Zusätzlicher Kontext

        Returns:
            SHA256 Hash als Cache-Key
        """
        try:
            # Hash-Input zusammenstellen
            hash_input = document_data

            # Document type hinzufügen
            hash_input += document_type.encode('utf-8')

            # Context filtern und hinzufügen (falls vorhanden)
            if context:
                # Nur cache-relevante Keys verwenden (validation-spezifische Keys ausschließen)
                cache_relevant_keys = {
                    # Caching-relevante Keys (ändern die Claude API Antwort)
                    "ocr_language", "ai_extraction", "quality_enhancement",
                    # Ausgeschlossen: expected_* Keys (sind validation-spezifisch)
                }

                # Filtere Context für Cache-Relevanz
                cache_context = {
                    k: v for k, v in context.items()
                    if k in cache_relevant_keys
                }

                # Nur wenn cache-relevanter Context vorhanden ist
                if cache_context:
                    sorted_context = sorted(cache_context.items())
                    context_str = json.dumps(sorted_context, sort_keys=True, ensure_ascii=False)
                    hash_input += context_str.encode('utf-8')

                # Debug-Info für besseres Verständnis
                if context.keys() - cache_context.keys():
                    filtered_keys = context.keys() - cache_context.keys()
                    self.logger.debug(f"Filtered validation keys from cache: {filtered_keys}")

            # SHA256 Hash generieren
            cache_key = hashlib.sha256(hash_input).hexdigest()
            return cache_key

        except Exception as e:
            self.logger.error(f"Error generating cache key: {e}")
            # Fallback: Einfacher Hash nur von document_data
            return hashlib.sha256(document_data).hexdigest()

    def cleanup_expired(self) -> int:
        """
        Entfernt abgelaufene Cache-Einträge.

        Returns:
            Anzahl gelöschter Einträge
        """
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Lösche abgelaufene Einträge
                cursor.execute(
                    "DELETE FROM document_cache WHERE expires_at < ?",
                    (datetime.now().isoformat(),)
                )
                deleted_count = cursor.rowcount
                conn.commit()

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} expired cache entries")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up expired cache entries: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Cache-Statistiken für Monitoring.

        Returns:
            Dictionary mit Cache-Statistiken
        """
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Gesamtanzahl Einträge
                cursor.execute("SELECT COUNT(*) FROM document_cache")
                total_entries = cursor.fetchone()[0]

                # Abgelaufene Einträge
                cursor.execute(
                    "SELECT COUNT(*) FROM document_cache WHERE expires_at < ?",
                    (datetime.now().isoformat(),)
                )
                expired_entries = cursor.fetchone()[0]

                # Aktive Einträge
                active_entries = total_entries - expired_entries

                # Datenbankgröße
                db_size_bytes = self.cache_db_path.stat().st_size if self.cache_db_path.exists() else 0
                db_size_mb = db_size_bytes / (1024 * 1024)

                return {
                    "total_entries": total_entries,
                    "active_entries": active_entries,
                    "expired_entries": expired_entries,
                    "database_size_mb": round(db_size_mb, 2),
                    "cache_db_path": str(self.cache_db_path)
                }

        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {
                "error": str(e),
                "total_entries": 0,
                "active_entries": 0,
                "expired_entries": 0,
                "database_size_mb": 0,
                "cache_db_path": str(self.cache_db_path)
            }

    def _init_database(self) -> None:
        """Initialisiert SQLite Cache-Datenbank."""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Erstelle Tabelle falls nicht vorhanden
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS document_cache (
                        cache_key TEXT PRIMARY KEY,
                        result_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    )
                    """
                )

                # Index für expires_at (für Cleanup)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_expires_at
                    ON document_cache(expires_at)
                    """
                )

                conn.commit()

            self.logger.debug(f"Cache database initialized: {self.cache_db_path}")

        except Exception as e:
            self.logger.error(f"Error initializing cache database: {e}")
            raise


# Global instance
document_cache = DocumentCache()