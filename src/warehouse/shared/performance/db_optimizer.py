"""
Database Performance Optimizer

Verbessert DB-Performance durch Connection Pooling, Query Batching
und intelligente Caching-Strategien.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from functools import wraps
import sqlite3

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    SQLite Connection Pool für bessere Performance.

    Vermeidet wiederholte DB-Connections und nutzt Connection-Reuse.
    """

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._connections: List[sqlite3.Connection] = []
        self._in_use: Dict[sqlite3.Connection, bool] = {}
        self._init_pool()

    def _init_pool(self):
        """Initialisiert Connection Pool."""
        # Netzwerk-Pfad erkennen (UNC oder mapped drive, nicht C:)
        is_network = self.db_path.startswith("\\\\") or (
            len(self.db_path) >= 2
            and self.db_path[1] == ":"
            and not self.db_path.upper().startswith("C:")
        )

        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            # Performance Settings
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            if is_network:
                conn.execute("PRAGMA journal_mode = DELETE")
                conn.execute("PRAGMA synchronous = FULL")
            else:
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")

            self._connections.append(conn)
            self._in_use[conn] = False

        logger.info(f"Connection pool initialized with {self.pool_size} connections")

    @contextmanager
    def get_connection(self):
        """Context Manager für Connection-Nutzung."""
        conn = None
        try:
            # Freie Connection finden
            for connection in self._connections:
                if not self._in_use[connection]:
                    conn = connection
                    self._in_use[conn] = True
                    break

            if conn is None:
                # Fallback: neue Connection wenn Pool erschöpft
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                logger.warning("Connection pool exhausted, creating new connection")

            yield conn

        finally:
            if conn and conn in self._in_use:
                self._in_use[conn] = False

    def close_all(self):
        """Schließt alle Connections."""
        for conn in self._connections:
            conn.close()
        self._connections.clear()
        self._in_use.clear()


class QueryBatcher:
    """
    Batch Processing für DB-Queries.

    Sammelt ähnliche Queries und führt sie in Batches aus.
    """

    def __init__(self, batch_size: int = 50, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._pending_queries: Dict[str, List[Tuple]] = {}
        self._last_flush = time.time()

    def add_query(self, query_type: str, query_data: Tuple):
        """Fügt Query zum Batch hinzu."""
        if query_type not in self._pending_queries:
            self._pending_queries[query_type] = []

        self._pending_queries[query_type].append(query_data)

        # Auto-flush bei Batch-Size oder Zeit-Limit
        if (
            len(self._pending_queries[query_type]) >= self.batch_size
            or time.time() - self._last_flush > self.flush_interval
        ):
            self.flush(query_type)

    def flush(self, query_type: Optional[str] = None):
        """Führt gesammelte Queries aus."""
        if query_type:
            query_types = [query_type]
        else:
            query_types = list(self._pending_queries.keys())

        for qtype in query_types:
            if qtype in self._pending_queries and self._pending_queries[qtype]:
                batch = self._pending_queries[qtype]
                self._execute_batch(qtype, batch)
                self._pending_queries[qtype].clear()

        self._last_flush = time.time()

    def _execute_batch(self, query_type: str, batch: List[Tuple]):
        """Führt Batch aus - Override in Subclasses."""
        logger.info(f"Executing batch {query_type} with {len(batch)} queries")


def query_performance_monitor(func):
    """
    Decorator für Query Performance Monitoring.

    Misst Query-Zeiten und identifiziert langsame Queries.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log langsame Queries
            if execution_time > 0.1:  # > 100ms
                logger.warning(
                    f"Slow query detected: {func.__name__} took {execution_time:.3f}s"
                )
            elif execution_time > 0.5:  # > 500ms
                logger.error(
                    f"Very slow query: {func.__name__} took {execution_time:.3f}s"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Query failed: {func.__name__} after {execution_time:.3f}s - {e}"
            )
            raise

    return wrapper


class BulkOperationOptimizer:
    """
    Optimiert Bulk-Operationen durch intelligente Batching-Strategien.
    """

    def __init__(self, connection_pool: ConnectionPool):
        self.pool = connection_pool
        self.query_batcher = QueryBatcher()

    @query_performance_monitor
    def bulk_insert(self, table: str, records: List[Dict[str, Any]]) -> int:
        """
        Optimierter Bulk Insert.

        Args:
            table: Tabellen-Name
            records: Liste von Datensätzen

        Returns:
            Anzahl eingefügter Datensätze
        """
        if not records:
            return 0

        # Bereite Statement vor
        columns = list(records[0].keys())
        placeholders = ", ".join(["?" for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # Konvertiere zu Tupeln
        data_tuples = [tuple(record[col] for col in columns) for record in records]

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data_tuples)
            conn.commit()

        logger.info(f"Bulk inserted {len(records)} records into {table}")
        return len(records)

    @query_performance_monitor
    def bulk_update(
        self, table: str, updates: List[Dict[str, Any]], where_column: str
    ) -> int:
        """
        Optimierter Bulk Update.

        Args:
            table: Tabellen-Name
            updates: Liste von Update-Datensätzen
            where_column: Column für WHERE-Bedingung

        Returns:
            Anzahl aktualisierter Datensätze
        """
        if not updates:
            return 0

        # Gruppiere Updates nach Schema
        update_columns = [col for col in updates[0].keys() if col != where_column]
        set_clause = ", ".join([f"{col} = ?" for col in update_columns])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_column} = ?"

        # Bereite Daten vor
        data_tuples = []
        for update in updates:
            values = [update[col] for col in update_columns]
            values.append(update[where_column])  # WHERE value
            data_tuples.append(tuple(values))

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data_tuples)
            conn.commit()

        logger.info(f"Bulk updated {len(updates)} records in {table}")
        return len(updates)

    def optimize_table(self, table: str):
        """
        Optimiert Tabelle durch ANALYZE und VACUUM.

        Args:
            table: Tabellen-Name
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            # Sammle Statistiken
            cursor.execute(f"ANALYZE {table}")

            # Optional: VACUUM für kompakte Speicherung
            cursor.execute("VACUUM")
            conn.commit()

        logger.info(f"Table {table} optimized")


class IndexOptimizer:
    """
    Analysiert und optimiert DB-Indizes basierend auf Query-Patterns.
    """

    def __init__(self, connection_pool: ConnectionPool):
        self.pool = connection_pool
        self._query_patterns: Dict[str, int] = {}

    def track_query(self, query: str):
        """Verfolgt Query-Pattern für Index-Optimierung."""
        # Extrahiere WHERE-Bedingungen
        if "WHERE" in query.upper():
            pattern = self._extract_where_pattern(query)
            self._query_patterns[pattern] = self._query_patterns.get(pattern, 0) + 1

    def _extract_where_pattern(self, query: str) -> str:
        """Extrahiert WHERE-Pattern aus Query."""
        # Vereinfachte Pattern-Extraktion
        upper_query = query.upper()
        where_pos = upper_query.find("WHERE")
        if where_pos == -1:
            return ""

        where_clause = query[where_pos:].split("ORDER BY")[0].split("GROUP BY")[0]
        return where_clause.strip()

    def suggest_indexes(self) -> List[str]:
        """
        Schlägt Indizes basierend auf häufigen Query-Patterns vor.

        Returns:
            Liste von CREATE INDEX Statements
        """
        suggestions = []

        # Analysiere häufige Patterns
        for pattern, count in self._query_patterns.items():
            if count > 10:  # Häufig verwendete Patterns
                index_suggestion = self._pattern_to_index(pattern)
                if index_suggestion:
                    suggestions.append(index_suggestion)

        return suggestions

    def _pattern_to_index(self, pattern: str) -> Optional[str]:
        """Konvertiert Query-Pattern zu Index-Vorschlag."""
        # Vereinfachte Index-Vorschläge
        if "article_number" in pattern and "batch_number" in pattern:
            return (
                "CREATE INDEX IF NOT EXISTS idx_item_article_batch"
                " ON items(article_number, batch_number)"
            )
        elif "delivery_number" in pattern:
            return (
                "CREATE INDEX IF NOT EXISTS idx_delivery_number"
                " ON items(delivery_number)"
            )

        return None


# Global Instances
_connection_pool: Optional[ConnectionPool] = None
_bulk_optimizer: Optional[BulkOperationOptimizer] = None
_index_optimizer: Optional[IndexOptimizer] = None


def initialize_performance_optimizers(db_path: str, pool_size: int = 5):
    """Initialisiert Performance-Optimierer."""
    global _connection_pool, _bulk_optimizer, _index_optimizer

    _connection_pool = ConnectionPool(db_path, pool_size)
    _bulk_optimizer = BulkOperationOptimizer(_connection_pool)
    _index_optimizer = IndexOptimizer(_connection_pool)

    logger.info("Database performance optimizers initialized")


def get_connection_pool() -> ConnectionPool:
    """Gibt Connection Pool zurück."""
    if _connection_pool is None:
        raise RuntimeError("Connection pool not initialized")
    return _connection_pool


def get_bulk_optimizer() -> BulkOperationOptimizer:
    """Gibt Bulk Optimizer zurück."""
    if _bulk_optimizer is None:
        raise RuntimeError("Bulk optimizer not initialized")
    return _bulk_optimizer


def get_index_optimizer() -> IndexOptimizer:
    """Gibt Index Optimizer zurück."""
    if _index_optimizer is None:
        raise RuntimeError("Index optimizer not initialized")
    return _index_optimizer


def cleanup_performance_optimizers():
    """Räumt Performance-Optimierer auf."""
    global _connection_pool, _bulk_optimizer, _index_optimizer

    if _connection_pool:
        _connection_pool.close_all()
        _connection_pool = None

    _bulk_optimizer = None
    _index_optimizer = None

    logger.info("Database performance optimizers cleaned up")
