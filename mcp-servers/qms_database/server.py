"""
Medealis QMS Database MCP Server.

Bietet Read-Only Zugriff auf die Warehouse-Datenbank fuer Claude Code.
7 Tools fuer Lieferanten, Inspektionen, Statistiken und freie Queries.

Sicherheit:
- Nur SELECT-Queries erlaubt
- SQLite Read-Only Modus
- Tabellen-Whitelist
- SQL-Keyword-Blacklist
- Ergebnis-Limit (max 1000 Zeilen)
- Audit-Logging aller Aufrufe
"""

import sqlite3
import time
import re
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from config import MCPDatabaseConfig
from audit import MCPAuditLogger

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Konfiguration laden
config = MCPDatabaseConfig.from_environment()
audit = MCPAuditLogger(config.audit_db_path)

# MCP Server erstellen
app = Server("qms-database")


# ============================================================
# Datenbank-Hilfsfunktionen
# ============================================================


def get_readonly_connection() -> sqlite3.Connection:
    """Oeffnet eine Read-Only SQLite-Verbindung."""
    if not config.database_path:
        raise RuntimeError(
            "Kein Datenbank-Pfad konfiguriert. "
            "Setze MEDEALIS_DB_PATH oder pruefe data/medealis_db/warehouse_new.db"
        )

    db_path = Path(config.database_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden: {config.database_path}")

    # Read-Only Modus via URI
    try:
        db_uri = f"file:{config.database_path}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True, timeout=config.query_timeout_seconds)
    except sqlite3.OperationalError:
        # Fallback: Normaler Modus (falls URI nicht unterstuetzt)
        conn = sqlite3.connect(
            config.database_path, timeout=config.query_timeout_seconds
        )
        logger.warning("Read-Only URI-Modus nicht verfuegbar, verwende normalen Modus")

    conn.row_factory = sqlite3.Row
    return conn


def validate_sql(sql: str) -> tuple:
    """
    Validiert eine SQL-Query.

    Returns:
        (is_valid: bool, error_message: str)
    """
    cleaned = sql.strip()
    upper = cleaned.upper()

    # Muss mit SELECT oder WITH beginnen
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "Nur SELECT-Queries sind erlaubt"

    # Verbotene Keywords pruefen
    for keyword in config.forbidden_keywords:
        # Word-Boundary Matching um False-Positives zu vermeiden
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper):
            return False, f"Verbotenes Keyword: {keyword}"

    # Semikolon-Check (nur eine Query erlaubt)
    # Entferne Strings und Comments bevor wir auf ; pruefen
    sql_no_strings = re.sub(r"'[^']*'", "", cleaned)
    sql_no_strings = re.sub(r'"[^"]*"', "", sql_no_strings)
    if sql_no_strings.count(";") > 1:
        return False, "Nur eine einzelne Query erlaubt"

    return True, "OK"


def rows_to_dicts(cursor: sqlite3.Cursor, rows: list) -> list:
    """Konvertiert SQLite Rows in Dicts."""
    if not cursor.description:
        return []
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# MCP Tools
# ============================================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Registriert die verfuegbaren MCP-Tools."""
    return [
        Tool(
            name="list_available_tables",
            description=(
                "Listet alle Tabellen der" " Warehouse-Datenbank mit ihren Spalten auf."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_database_statistics",
            description="Gibt die Anzahl der Eintraege pro Tabelle zurueck.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_supplier_data",
            description=(
                "Gibt Lieferanten-Stammdaten inkl." " zugehoeriger Lieferungen zurueck."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": (
                            "Lieferanten-ID" " (z.B. 'BEGO', 'CAMLOG', 'PRIMEC')"
                        ),
                    }
                },
                "required": ["supplier_id"],
            },
        ),
        Tool(
            name="get_inspection_data",
            description=(
                "Gibt Wareneingangspruefungs-Daten" " (Workflow-Steps + Items) zurueck."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "article_number": {
                        "type": "string",
                        "description": "Artikelnummer (optional, z.B. 'CT0003')",
                    },
                    "delivery_number": {
                        "type": "string",
                        "description": "Lieferscheinnummer (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximale Anzahl Ergebnisse (default: 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="query_database",
            description=(
                "Fuehrt eine validierte Read-Only SQL-Query"
                " gegen die Datenbank aus."
                " Nur SELECT erlaubt."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL SELECT-Query"},
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in Sekunden (default: 30)",
                        "default": 30,
                    },
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="get_open_capas",
            description=(
                "Gibt offene CAPA-Vorgaenge zurueck."
                " (Tabelle noch nicht implementiert)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "description": "Filter nach Prioritaet (optional)",
                        "enum": ["hoch", "mittel", "niedrig"],
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="get_expiring_documents",
            description=(
                "Gibt QM-Dokumente mit ablaufendem Review"
                " zurueck. (Tabelle noch nicht"
                " implementiert)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Tage bis Ablauf (default: 30)",
                        "default": 30,
                    }
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Dispatch fuer MCP-Tool-Aufrufe."""
    try:
        if name == "list_available_tables":
            return await tool_list_available_tables()
        elif name == "get_database_statistics":
            return await tool_get_database_statistics()
        elif name == "get_supplier_data":
            return await tool_get_supplier_data(arguments.get("supplier_id", ""))
        elif name == "get_inspection_data":
            return await tool_get_inspection_data(
                article_number=arguments.get("article_number"),
                delivery_number=arguments.get("delivery_number"),
                limit=arguments.get("limit", 50),
            )
        elif name == "query_database":
            return await tool_query_database(
                sql=arguments.get("sql", ""),
                timeout=arguments.get("timeout", 30),
            )
        elif name == "get_open_capas":
            return await tool_get_open_capas(arguments.get("priority"))
        elif name == "get_expiring_documents":
            return await tool_get_expiring_documents(arguments.get("days", 30))
        else:
            return [TextContent(type="text", text=f"Unbekanntes Tool: {name}")]
    except Exception as e:
        audit.log_invocation(name, params=arguments, error=str(e))
        return [TextContent(type="text", text=f"Fehler: {e}")]


# ============================================================
# Tool-Implementierungen
# ============================================================


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
            tables = [row[0] for row in cursor.fetchall()]

            result = {}
            for table in tables:
                if table in config.allowed_tables:
                    cursor = conn.execute(f"PRAGMA table_info([{table}])")
                    columns = [
                        {
                            "name": row[1],
                            "type": row[2],
                            "nullable": not row[3],
                            "primary_key": bool(row[5]),
                        }
                        for row in cursor.fetchall()
                    ]
                    result[table] = columns

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "list_available_tables",
                result_summary=f"{len(result)} Tabellen",
                duration_ms=duration,
            )

            return [
                TextContent(
                    type="text", text=json.dumps(result, indent=2, ensure_ascii=False)
                )
            ]
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "list_available_tables", error=str(e), duration_ms=duration
        )
        return [TextContent(type="text", text=f"Fehler: {e}")]


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
                    count = cursor.fetchone()[0]
                    result[table] = count
                except sqlite3.OperationalError:
                    result[table] = "Tabelle nicht vorhanden"

            duration = (time.time() - start) * 1000
            audit.log_invocation(
                "get_database_statistics",
                result_summary=f"{len(result)} Tabellen abgefragt",
                duration_ms=duration,
            )

            return [
                TextContent(
                    type="text", text=json.dumps(result, indent=2, ensure_ascii=False)
                )
            ]
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "get_database_statistics", error=str(e), duration_ms=duration
        )
        return [TextContent(type="text", text=f"Fehler: {e}")]


async def tool_get_supplier_data(supplier_id: str) -> list[TextContent]:
    """Gibt Lieferanten-Daten inkl. Lieferungen zurueck."""
    start = time.time()
    params = {"supplier_id": supplier_id}

    try:
        conn = get_readonly_connection()
        try:
            # Lieferanten-Stammdaten
            cursor = conn.execute(
                "SELECT * FROM suppliers WHERE supplier_id = ?", (supplier_id,)
            )
            supplier_row = cursor.fetchone()

            if not supplier_row:
                # Versuche Teilsuche
                cursor = conn.execute(
                    "SELECT * FROM suppliers WHERE supplier_id LIKE ? OR name LIKE ?",
                    (f"%{supplier_id}%", f"%{supplier_id}%"),
                )
                supplier_row = cursor.fetchone()

            if not supplier_row:
                audit.log_invocation(
                    "get_supplier_data",
                    params=params,
                    result_summary="Lieferant nicht gefunden",
                )
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": f"Lieferant '{supplier_id}' nicht gefunden",
                                "hint": (
                                    "Verwende list_available_tables"
                                    " oder query_database um"
                                    " verfuegbare Lieferanten"
                                    " zu finden"
                                ),
                            },
                            ensure_ascii=False,
                        ),
                    )
                ]

            supplier = dict(supplier_row)

            # Zugehoerige Lieferungen
            cursor = conn.execute(
                "SELECT * FROM deliveries"
                " WHERE supplier_id = ?"
                " ORDER BY delivery_date DESC"
                " LIMIT 20",
                (supplier.get("supplier_id", supplier_id),),
            )
            deliveries = [dict(row) for row in cursor.fetchall()]

            # Zugehoerige Items (ueber Lieferungen)
            delivery_numbers = [d.get("delivery_number", "") for d in deliveries]
            items_count = 0
            if delivery_numbers:
                placeholders = ",".join(["?" for _ in delivery_numbers])
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM items"
                    f" WHERE delivery_number IN ({placeholders})",
                    delivery_numbers,
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
                result_summary=f"Lieferant gefunden, {len(deliveries)} Lieferungen",
                duration_ms=duration,
            )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str, ensure_ascii=False),
                )
            ]
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "get_supplier_data", params=params, error=str(e), duration_ms=duration
        )
        return [TextContent(type="text", text=f"Fehler: {e}")]


async def tool_get_inspection_data(
    article_number: Optional[str] = None,
    delivery_number: Optional[str] = None,
    limit: int = 50,
) -> list[TextContent]:
    """Gibt Wareneingangspruefungs-Daten zurueck."""
    start = time.time()
    params = {
        "article_number": article_number,
        "delivery_number": delivery_number,
        "limit": limit,
    }

    try:
        conn = get_readonly_connection()
        try:
            # Query bauen
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
                    ws.documents_checked_by,
                    ws.documents_checked_at,
                    ws.measured_by,
                    ws.measured_at,
                    ws.visually_inspected_by,
                    ws.visually_inspected_at,
                    ws.documents_merged_by,
                    ws.documents_merged_at,
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

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str, ensure_ascii=False),
                )
            ]
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "get_inspection_data", params=params, error=str(e), duration_ms=duration
        )
        return [TextContent(type="text", text=f"Fehler: {e}")]


async def tool_query_database(sql: str, timeout: int = 30) -> list[TextContent]:
    """Fuehrt eine validierte Read-Only SQL-Query aus."""
    start = time.time()
    params = {"sql": sql, "timeout": timeout}

    # Validierung
    is_valid, error_msg = validate_sql(sql)
    if not is_valid:
        audit.log_invocation(
            "query_database", params=params, error=f"Abgelehnt: {error_msg}"
        )
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Query abgelehnt: {error_msg}",
                        "hint": (
                            "Nur SELECT-Queries sind erlaubt."
                            " Keine INSERT/UPDATE/DELETE/DROP."
                        ),
                    },
                    ensure_ascii=False,
                ),
            )
        ]

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

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str, ensure_ascii=False),
                )
            ]
        finally:
            conn.close()

    except Exception as e:
        duration = (time.time() - start) * 1000
        audit.log_invocation(
            "query_database", params=params, error=str(e), duration_ms=duration
        )
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": f"Query-Fehler: {e}", "sql": sql}, ensure_ascii=False
                ),
            )
        ]


async def tool_get_open_capas(priority: Optional[str] = None) -> list[TextContent]:
    """Placeholder: CAPA-Tabelle noch nicht implementiert."""
    audit.log_invocation(
        "get_open_capas",
        params={"priority": priority},
        result_summary="Tabelle nicht implementiert",
    )
    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "not_implemented",
                    "message": (
                        "Die CAPA-Tabelle ist noch nicht"
                        " implementiert. Sie wird in einer"
                        " zukuenftigen Phase als separate"
                        " QMS-Datenbank erstellt."
                    ),
                    "data": [],
                },
                ensure_ascii=False,
            ),
        )
    ]


async def tool_get_expiring_documents(days: int = 30) -> list[TextContent]:
    """Placeholder: Dokumentenlenkung noch nicht implementiert."""
    audit.log_invocation(
        "get_expiring_documents",
        params={"days": days},
        result_summary="Tabelle nicht implementiert",
    )
    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "not_implemented",
                    "message": (
                        "Die Dokumentenlenkung-Tabelle ist"
                        " noch nicht implementiert."
                        " Sie wird in einer zukuenftigen"
                        " Phase als separate"
                        " QMS-Datenbank erstellt."
                    ),
                    "data": [],
                },
                ensure_ascii=False,
            ),
        )
    ]


# ============================================================
# Server Entry Point
# ============================================================


async def main():
    """Startet den MCP-Server via stdio."""
    from mcp.server.stdio import stdio_server

    logger.info("QMS Database MCP Server startet...")
    logger.info(f"Datenbank: {config.database_path or 'NICHT KONFIGURIERT'}")
    logger.info(f"Audit-Log: {config.audit_db_path}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
