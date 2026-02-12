"""
MCP Audit Logger.

Protokolliert jeden MCP-Tool-Aufruf in einer separaten SQLite-Datenbank.
Unabhaengig vom Haupt-Audit-Log der Warehouse-App.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MCPAuditLogger:
    """Audit-Logging fuer MCP-Server Tool-Aufrufe."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Erstellt Audit-Datenbank und -Tabelle falls nicht vorhanden."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mcp_audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        server TEXT NOT NULL DEFAULT 'qms_database',
                        tool TEXT NOT NULL,
                        user TEXT DEFAULT 'claude_code',
                        params TEXT,
                        result_summary TEXT,
                        error TEXT,
                        duration_ms REAL,
                        rows_returned INTEGER
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_mcp_audit_timestamp
                    ON mcp_audit_log(timestamp)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_mcp_audit_tool
                    ON mcp_audit_log(tool)
                """
                )
        except Exception as e:
            logger.error(f"Audit-Datenbank Initialisierung fehlgeschlagen: {e}")

    @contextmanager
    def _get_connection(self):
        """Context-Manager fuer SQLite-Verbindung."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_invocation(
        self,
        tool: str,
        params: Optional[Dict[str, Any]] = None,
        result_summary: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        rows_returned: Optional[int] = None,
        user: Optional[str] = None,
    ) -> None:
        """
        Protokolliert einen MCP-Tool-Aufruf.

        Args:
            tool: Name des aufgerufenen Tools
            params: Uebergebene Parameter (als Dict)
            result_summary: Kurzbeschreibung des Ergebnisses
            error: Fehlermeldung (falls aufgetreten)
            duration_ms: Dauer in Millisekunden
            rows_returned: Anzahl zurueckgegebener Zeilen
            user: Aufrufender Benutzer
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT INTO mcp_audit_log
                       (timestamp, tool, user, params,
                        result_summary, error,
                        duration_ms, rows_returned)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now().isoformat(),
                        tool,
                        user or "claude_code",
                        json.dumps(params, default=str) if params else None,
                        result_summary,
                        error,
                        duration_ms,
                        rows_returned,
                    ),
                )
        except Exception as e:
            logger.error(f"Audit-Log Eintrag fehlgeschlagen: {e}")
