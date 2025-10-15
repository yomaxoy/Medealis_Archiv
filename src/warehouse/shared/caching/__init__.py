"""
Caching Module - Performance-Optimierung durch intelligentes Caching.

Stellt TTL-Cache Decorator und Utilities für Method-Level Caching bereit.
"""

from .ttl_cache import (
    ttl_cache,
    TTLCache,
    CacheEntry,
    clear_all_caches,
    get_cache_stats_summary
)

__all__ = [
    'ttl_cache',
    'TTLCache',
    'CacheEntry',
    'clear_all_caches',
    'get_cache_stats_summary'
]