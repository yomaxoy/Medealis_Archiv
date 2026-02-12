"""
MCP Server Konfiguration.

Verwaltet Datenbank-Pfade, erlaubte Tabellen und Validierungsregeln.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List


@dataclass
class MCPDatabaseConfig:
    """Konfiguration fuer den QMS Database MCP Server."""

    # Pfad zur Warehouse-SQLite-Datenbank
    database_path: str = ""

    # Pfad fuer MCP-Audit-Log (separate SQLite-DB)
    audit_db_path: str = ""

    # Erlaubte Tabellen (Whitelist)
    allowed_tables: List[str] = field(
        default_factory=lambda: [
            "suppliers",
            "deliveries",
            "items",
            "item_info",
            "orders",
            "order_items",
            "users",
            "audit_log",
            "item_workflow_steps",
        ]
    )

    # Verbotene SQL-Keywords
    forbidden_keywords: List[str] = field(
        default_factory=lambda: [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
            "EXEC",
            "ATTACH",
            "DETACH",
            "PRAGMA",
        ]
    )

    # Query-Limits
    query_timeout_seconds: int = 30
    max_result_rows: int = 1000

    @classmethod
    def from_environment(cls) -> "MCPDatabaseConfig":
        """Laedt Konfiguration aus Umgebungsvariablen und Auto-Detection."""
        # Projekt-Root ermitteln (mcp-servers/qms_database -> Projekt-Root)
        project_root = Path(__file__).parent.parent.parent

        # Datenbank-Pfad
        db_path = os.getenv("MEDEALIS_DB_PATH", "")

        if not db_path:
            # Auto-Detection: Server-Pfad hat Prioritaet (gleiche DB wie App)
            server_path = Path(
                r"\\10.190.140.10\Allgemein\Qualitätsmanagement"
                r"\QM_MEDEALIS\03. Produkte\Produktprüfung"
                r"\Medealis Archiv\database\warehouse_new.db"
            )
            candidates = [
                server_path,
                project_root / "data" / "medealis_db" / "warehouse_new.db",
                Path.home() / ".medealis" / "warehouse_new.db",
            ]

            for candidate in candidates:
                try:
                    if candidate.exists():
                        db_path = str(candidate)
                        break
                except (OSError, PermissionError):
                    continue

        # Audit-DB Pfad
        audit_path = os.getenv(
            "MCP_AUDIT_DB_PATH", str(project_root / "data" / "mcp_audit_logs.db")
        )

        return cls(database_path=db_path, audit_db_path=audit_path)
