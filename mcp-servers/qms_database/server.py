"""
Medealis QMS Database MCP Server.

Bietet Read-Only Zugriff auf die Warehouse-Datenbank
fuer Claude Code. Implementiert 7 Tools via MCP (Model
Context Protocol) ueber stdio-Transport.

Sicherheitskonzept:
- Nur SELECT-Queries erlaubt (Keyword-Blacklist)
- SQLite Read-Only Modus via URI
- Tabellen-Whitelist (nur freigegebene Tabellen)
- Ergebnis-Limit (max 1000 Zeilen)
- Audit-Logging aller Aufrufe in separater DB

Dateien:
- server.py  - MCP-Server und Tool-Implementierungen
- config.py  - Datenbank-Pfade, Whitelist, Limits
- audit.py   - Audit-Logging in separate SQLite-DB
"""

import sqlite3
import time
import re
import json
import logging
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from config import MCPDatabaseConfig
from audit import MCPAuditLogger

# Logging in Datei (nicht stderr, das stoert MCP stdio)
_log_file = Path(__file__).parent.parent.parent / "data" / "mcp_server.log"
_log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    filename=str(_log_file),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Konfiguration und Audit-Logger initialisieren
config = MCPDatabaseConfig.from_environment()
audit = MCPAuditLogger(config.audit_db_path)

# MCP Server-Instanz
app = Server("qms-database")


# -- Tool-Beschreibungen (separat fuer Lesbarkeit) ------

_DESC_LIST_TABLES = (
    "Listet alle Tabellen der Warehouse-Datenbank" " mit ihren Spalten auf."
)
_DESC_DB_STATS = "Gibt die Anzahl der Eintraege pro Tabelle zurueck."
_DESC_SUPPLIER = (
    "Gibt Lieferanten-Stammdaten inkl." " zugehoeriger Lieferungen zurueck."
)
_DESC_INSPECTION = (
    "Gibt Wareneingangspruefungs-Daten" " (Workflow-Steps + Items) zurueck."
)
_DESC_QUERY = (
    "Fuehrt eine validierte Read-Only SQL-Query"
    " gegen die Datenbank aus. Nur SELECT erlaubt."
)
_DESC_CAPAS = (
    "Gibt offene CAPA-Vorgaenge zurueck." " (Tabelle noch nicht implementiert)"
)
_DESC_DOCUMENTS = (
    "Gibt QM-Dokumente mit ablaufendem Review"
    " zurueck. (Tabelle noch nicht implementiert)"
)

_MSG_NOT_IMPLEMENTED = (
    "Noch nicht implementiert. Wird in einer"
    " zukuenftigen Phase als separate"
    " QMS-Datenbank erstellt."
)


# ============================================================
# Datenbank-Hilfsfunktionen
# ============================================================


def get_readonly_connection() -> sqlite3.Connection:
    """Oeffnet eine Read-Only SQLite-Verbindung.

    Versucht zuerst URI-Modus (?mode=ro), faellt auf
    normalen Modus zurueck falls nicht unterstuetzt.
    """
    if not config.database_path:
        raise RuntimeError(
            "Kein Datenbank-Pfad konfiguriert. "
            "Setze MEDEALIS_DB_PATH oder pruefe "
            "data/medealis_db/warehouse_new.db"
        )

    db_path = Path(config.database_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden: {db_path}")

    try:
        db_uri = f"file:{config.database_path}?mode=ro"
        conn = sqlite3.connect(
            db_uri,
            uri=True,
            timeout=config.query_timeout_seconds,
        )
    except sqlite3.OperationalError:
        # Fallback falls URI nicht unterstuetzt
        conn = sqlite3.connect(
            config.database_path,
            timeout=config.query_timeout_seconds,
        )
        logger.warning("Read-Only URI nicht verfuegbar, " "verwende normalen Modus")

    conn.row_factory = sqlite3.Row
    return conn


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validiert eine SQL-Query gegen Sicherheitsregeln.

    Prueft:
    - Muss mit SELECT oder WITH beginnen
    - Keine verbotenen Keywords (INSERT, DROP, etc.)
    - Maximal ein Statement (Semikolon-Check)

    Returns:
        (is_valid, error_message)
    """
    cleaned = sql.strip()
    upper = cleaned.upper()

    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "Nur SELECT-Queries sind erlaubt"

    for keyword in config.forbidden_keywords:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper):
            return False, f"Verbotenes Keyword: {keyword}"

    # Semikolon-Check: Strings entfernen, dann zaehlen
    no_strings = re.sub(r"'[^']*'", "", cleaned)
    no_strings = re.sub(r'"[^"]*"', "", no_strings)
    if no_strings.count(";") > 1:
        return False, "Nur eine einzelne Query erlaubt"

    return True, "OK"


def rows_to_dicts(cursor: sqlite3.Cursor, rows: list) -> list[dict]:
    """Konvertiert SQLite Rows in Dictionaries."""
    if not cursor.description:
        return []
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def _json_response(data) -> list[TextContent]:
    """Erzeugt eine JSON-TextContent-Antwort."""
    return [
        TextContent(
            type="text",
            text=json.dumps(
                data,
                indent=2,
                default=str,
                ensure_ascii=False,
            ),
        )
    ]


def _error_response(message: str) -> list[TextContent]:
    """Erzeugt eine Fehler-Antwort."""
    return [TextContent(type="text", text=message)]


# ============================================================
# MCP Tool-Registrierung
# ============================================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Registriert die verfuegbaren MCP-Tools."""
    return [
        Tool(
            name="list_available_tables",
            description=_DESC_LIST_TABLES,
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_database_statistics",
            description=_DESC_DB_STATS,
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_supplier_data",
            description=_DESC_SUPPLIER,
            inputSchema={
                "type": "object",
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": ("Lieferanten-ID" " (z.B. 'BEGO', 'PRIMEC')"),
                    }
                },
                "required": ["supplier_id"],
            },
        ),
        Tool(
            name="get_inspection_data",
            description=_DESC_INSPECTION,
            inputSchema={
                "type": "object",
                "properties": {
                    "article_number": {
                        "type": "string",
                        "description": ("Artikelnummer" " (optional, z.B. 'CT0003')"),
                    },
                    "delivery_number": {
                        "type": "string",
                        "description": ("Lieferscheinnummer (optional)"),
                    },
                    "limit": {
                        "type": "integer",
                        "description": ("Max. Ergebnisse (default: 50)"),
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="query_database",
            description=_DESC_QUERY,
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT-Query",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": ("Timeout in Sekunden (default: 30)"),
                        "default": 30,
                    },
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="get_open_capas",
            description=_DESC_CAPAS,
            inputSchema={
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "description": ("Filter nach Prioritaet"),
                        "enum": [
                            "hoch",
                            "mittel",
                            "niedrig",
                        ],
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="get_expiring_documents",
            description=_DESC_DOCUMENTS,
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": ("Tage bis Ablauf (default: 30)"),
                        "default": 30,
                    }
                },
                "required": [],
            },
        ),
    ]


# ============================================================
# Tool-Dispatch
# ============================================================

# Mapping: Tool-Name -> Handler-Funktion
_TOOL_HANDLERS = {}


def _register(name: str):
    """Decorator zum Registrieren eines Tool-Handlers."""

    def wrapper(func):
        _TOOL_HANDLERS[name] = func
        return func

    return wrapper


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Zentraler Dispatch fuer alle MCP-Tool-Aufrufe."""
    handler = _TOOL_HANDLERS.get(name)
    if not handler:
        return _error_response(f"Unbekanntes Tool: {name}")

    try:
        return await handler(**arguments)
    except Exception as e:
        audit.log_invocation(name, params=arguments, error=str(e))
        return _error_response(f"Fehler: {e}")


# ============================================================
# Tool-Implementierungen
# ============================================================


@_register("list_available_tables")
async def tool_list_available_tables() -> list[TextContent]:
    """Listet alle Tabellen mit Spalteninformationen."""
    start = time.time()
    try:
        conn = get_readonly_connection()
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master"
                " WHERE type='table'"
                " AND name NOT LIKE 'sqlite_%'"
                " ORDER BY name"
            )
            tables = [
                row[0] for row in cursor.fetchall() if row[0] in config.allowed_tables
            ]

            result = {}
            for table in tables:
                cursor = conn.execute(f"PRAGMA table_info([{table}])")
                result[table] = [
                    {
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "primary_key": bool(row[5]),
                    }
                    for row in cursor.fetchall()
                ]

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "list_available_tables",
                result_summary=f"{len(result)} Tabellen",
                duration_ms=duration,
            )
            return _json_response(result)
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "list_available_tables",
            error=str(e),
            duration_ms=duration,
        )
        return _error_response(f"Fehler: {e}")


@_register("get_database_statistics")
async def tool_get_database_statistics() -> list[TextContent]:
    """Gibt Eintragsanzahl pro Tabelle zurueck."""
    start = time.time()
    try:
        conn = get_readonly_connection()
        try:
            result = {}
            for table in config.allowed_tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table}]")
                    result[table] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    result[table] = "Tabelle nicht vorhanden"

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "get_database_statistics",
                result_summary=(f"{len(result)} Tabellen abgefragt"),
                duration_ms=duration,
            )
            return _json_response(result)
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "get_database_statistics",
            error=str(e),
            duration_ms=duration,
        )
        return _error_response(f"Fehler: {e}")


@_register("get_supplier_data")
async def tool_get_supplier_data(supplier_id: str = "", **kwargs) -> list[TextContent]:
    """Gibt Lieferanten-Daten inkl. Lieferungen zurueck.

    Sucht zuerst exakt nach supplier_id, dann per
    Teiltext-Suche in ID und Name.
    """
    start = time.time()
    params = {"supplier_id": supplier_id}

    try:
        conn = get_readonly_connection()
        try:
            # Exakte Suche
            cursor = conn.execute(
                "SELECT * FROM suppliers" " WHERE supplier_id = ?",
                (supplier_id,),
            )
            supplier_row = cursor.fetchone()

            # Fallback: Teilsuche
            if not supplier_row:
                cursor = conn.execute(
                    "SELECT * FROM suppliers"
                    " WHERE supplier_id LIKE ?"
                    " OR name LIKE ?",
                    (
                        f"%{supplier_id}%",
                        f"%{supplier_id}%",
                    ),
                )
                supplier_row = cursor.fetchone()

            if not supplier_row:
                audit.log_invocation(
                    "get_supplier_data",
                    params=params,
                    result_summary="Nicht gefunden",
                )
                return _json_response(
                    {
                        "error": (f"Lieferant '{supplier_id}'" " nicht gefunden"),
                        "hint": (
                            "Verwende query_database mit" " SELECT * FROM suppliers"
                        ),
                    }
                )

            supplier = dict(supplier_row)
            sid = supplier.get("supplier_id", supplier_id)

            # Zugehoerige Lieferungen
            cursor = conn.execute(
                "SELECT * FROM deliveries"
                " WHERE supplier_id = ?"
                " ORDER BY delivery_date DESC"
                " LIMIT 20",
                (sid,),
            )
            deliveries = [dict(row) for row in cursor.fetchall()]

            # Items zaehlen
            items_count = 0
            d_numbers = [d["delivery_number"] for d in deliveries]
            if d_numbers:
                ph = ",".join("?" * len(d_numbers))
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM items" f" WHERE delivery_number IN ({ph})",
                    d_numbers,
                )
                items_count = cursor.fetchone()[0]

            result = {
                "supplier": supplier,
                "deliveries": deliveries,
                "delivery_count": len(deliveries),
                "total_items": items_count,
            }

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "get_supplier_data",
                params=params,
                result_summary=(f"Gefunden, {len(deliveries)}" " Lieferungen"),
                duration_ms=duration,
            )
            return _json_response(result)
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "get_supplier_data",
            params=params,
            error=str(e),
            duration_ms=duration,
        )
        return _error_response(f"Fehler: {e}")


@_register("get_inspection_data")
async def tool_get_inspection_data(
    article_number: Optional[str] = None,
    delivery_number: Optional[str] = None,
    limit: int = 50,
    **kwargs,
) -> list[TextContent]:
    """Gibt Wareneingangspruefungs-Daten zurueck.

    Verbindet items mit item_workflow_steps via
    LEFT JOIN (article_number + batch_number +
    delivery_number).
    """
    start = time.time()
    params = {
        "article_number": article_number,
        "delivery_number": delivery_number,
        "limit": limit,
    }

    try:
        conn = get_readonly_connection()
        try:
            query = """
                SELECT
                    i.article_number,
                    i.batch_number,
                    i.delivery_number,
                    i.delivered_quantity,
                    i.ordered_quantity,
                    i.waste_quantity,
                    i.measurement_protocol,
                    i.coating_certificate,
                    i.material_certificate,
                    i.hardness_certificate,
                    i.employee,
                    i.visual_inspector,
                    i.notes,
                    ws.data_checked_by,
                    ws.data_checked_at,
                    ws.measured_by,
                    ws.measured_at,
                    ws.visually_inspected_by,
                    ws.visually_inspected_at,
                    ws.completed_by,
                    ws.completed_at,
                    ws.rejected_by,
                    ws.rejected_at,
                    ws.rejection_reason
                FROM items i
                LEFT JOIN item_workflow_steps ws
                    ON i.article_number = ws.article_number
                    AND i.batch_number = ws.batch_number
                    AND i.delivery_number = ws.delivery_number
            """

            conditions = []
            query_params = []

            if article_number:
                conditions.append("i.article_number = ?")
                query_params.append(article_number)
            if delivery_number:
                conditions.append("i.delivery_number = ?")
                query_params.append(delivery_number)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            max_rows = min(limit, config.max_result_rows)
            query += " ORDER BY i.created_at DESC" f" LIMIT {max_rows}"

            cursor = conn.execute(query, query_params)
            rows = cursor.fetchall()
            result = rows_to_dicts(cursor, rows)

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "get_inspection_data",
                params=params,
                result_summary=f"{len(result)} Items",
                duration_ms=duration,
                rows_returned=len(result),
            )
            return _json_response(result)
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "get_inspection_data",
            params=params,
            error=str(e),
            duration_ms=duration,
        )
        return _error_response(f"Fehler: {e}")


@_register("query_database")
async def tool_query_database(
    sql: str = "", timeout: int = 30, **kwargs
) -> list[TextContent]:
    """Fuehrt eine validierte Read-Only SQL-Query aus.

    Akzeptiert nur SELECT/WITH-Queries. Verbotene
    Keywords werden per Regex geprueft. Ergebnisse
    werden auf max_result_rows limitiert.
    """
    start = time.time()
    params = {"sql": sql, "timeout": timeout}

    # SQL-Validierung
    is_valid, error_msg = validate_sql(sql)
    if not is_valid:
        audit.log_invocation(
            "query_database",
            params=params,
            error=f"Abgelehnt: {error_msg}",
        )
        return _json_response(
            {
                "error": f"Query abgelehnt: {error_msg}",
                "hint": (
                    "Nur SELECT-Queries erlaubt." " Kein INSERT/UPDATE/DELETE/DROP."
                ),
            }
        )

    try:
        conn = get_readonly_connection()
        try:
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(config.max_result_rows)
            result = rows_to_dicts(cursor, rows)

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "query_database",
                params=params,
                result_summary=f"{len(result)} Zeilen",
                duration_ms=duration,
                rows_returned=len(result),
            )
            return _json_response(result)
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "query_database",
            params=params,
            error=str(e),
            duration_ms=duration,
        )
        return _json_response(
            {
                "error": f"Query-Fehler: {e}",
                "sql": sql,
            }
        )


@_register("get_open_capas")
async def tool_get_open_capas(
    priority: Optional[str] = None, **kwargs
) -> list[TextContent]:
    """Placeholder: CAPA-Tabelle noch nicht implementiert."""
    audit.log_invocation(
        "get_open_capas",
        params={"priority": priority},
        result_summary="Nicht implementiert",
    )
    return _json_response(
        {
            "status": "not_implemented",
            "message": _MSG_NOT_IMPLEMENTED,
            "data": [],
        }
    )


@_register("get_expiring_documents")
async def tool_get_expiring_documents(days: int = 30, **kwargs) -> list[TextContent]:
    """Placeholder: Dokumentenlenkung noch nicht implementiert."""
    audit.log_invocation(
        "get_expiring_documents",
        params={"days": days},
        result_summary="Nicht implementiert",
    )
    return _json_response(
        {
            "status": "not_implemented",
            "message": _MSG_NOT_IMPLEMENTED,
            "data": [],
        }
    )


# ============================================================
# Server Entry Point
# ============================================================


async def main():
    """Startet den MCP-Server via stdio-Transport."""
    from mcp.server.stdio import stdio_server

    db = config.database_path or "NICHT KONFIGURIERT"
    logger.info("QMS Database MCP Server startet...")
    logger.info(f"Datenbank: {db}")
    logger.info(f"Audit-Log: {config.audit_db_path}")

    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
