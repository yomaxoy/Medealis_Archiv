#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate Data from SQLite to PostgreSQL
Migriert alle Daten mit Batch-Processing und Validierung
"""

import sys
import io
import os
import sqlite3
from pathlib import Path

# Fix Windows Console Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# PostgreSQL Connection
POSTGRES_URL = (
    "postgresql://medealis_user:migration_test_password_2024@localhost:5432/medealis"
)
os.environ["DATABASE_URL"] = POSTGRES_URL

# SQLite DB Path
SQLITE_DB = Path.home() / ".medealis" / "warehouse_new.db"


def migrate_table(sqlite_conn, pg_session, table_name, batch_size=1000):
    """Migriert eine Tabelle von SQLite zu PostgreSQL."""
    print(f"\n📦 Migriere {table_name}...")

    # Zähle Rows in SQLite
    sqlite_cursor = sqlite_conn.cursor()
    count = sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    if count == 0:
        print(f"   ⏭️  Überspringe (leer)")
        return True

    # Hole alle Daten
    rows = sqlite_cursor.execute(f"SELECT * FROM {table_name}").fetchall()
    columns = [desc[0] for desc in sqlite_cursor.description]

    print(f"   📊 {count} Datensätze gefunden")

    # Insert in PostgreSQL (Batch)
    from sqlalchemy import text

    placeholders = ", ".join([f":{col}" for col in columns])
    insert_sql = (
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    )

    try:
        for i, row in enumerate(rows, 1):
            row_dict = dict(zip(columns, row))
            pg_session.execute(text(insert_sql), row_dict)

            if i % 100 == 0:
                print(f"   ... {i}/{count}")

        pg_session.commit()
        print(f"   ✅ {count} Datensätze migriert")
        return True

    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        pg_session.rollback()
        return False


def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("DATEN-MIGRATION: SQLite → PostgreSQL")
    print("=" * 60)

    # 1. SQLite Connection
    print("\n1. Verbinde mit SQLite...")
    if not SQLITE_DB.exists():
        print(f"❌ SQLite DB nicht gefunden: {SQLITE_DB}")
        return 1

    sqlite_conn = sqlite3.connect(SQLITE_DB)
    print(f"✅ SQLite: {SQLITE_DB}")

    # 2. PostgreSQL Connection
    print("\n2. Verbinde mit PostgreSQL...")
    from warehouse.infrastructure.database import initialize_database, get_session

    initialize_database(POSTGRES_URL)
    print("✅ PostgreSQL verbunden")

    # 3. Migration (in Reihenfolge wegen FK-Dependencies)
    migration_order = [
        "suppliers",
        "item_info",
        "orders",
        "order_items",
        "deliveries",
        "items",
        "item_workflow_steps",
        "item_status_steps",
    ]

    print("\n3. Migriere Tabellen...")
    print("=" * 60)

    success_count = 0
    with get_session() as pg_session:
        for table in migration_order:
            if migrate_table(sqlite_conn, pg_session, table):
                success_count += 1

    # 4. Validierung
    print("\n" + "=" * 60)
    print("4. VALIDIERUNG")
    print("=" * 60)

    with get_session() as pg_session:
        for table in migration_order:
            from sqlalchemy import text

            pg_count = pg_session.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()
            sqlite_count = sqlite_conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            if pg_count == sqlite_count:
                print(
                    f"✅ {table:25s} | SQLite: {sqlite_count:4d} | PostgreSQL: {pg_count:4d}"
                )
            else:
                print(
                    f"❌ {table:25s} | SQLite: {sqlite_count:4d} | PostgreSQL: {pg_count:4d} | FEHLER!"
                )

    sqlite_conn.close()

    print("\n" + "=" * 60)
    if success_count == len(migration_order):
        print("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
    else:
        print(f"⚠️  {success_count}/{len(migration_order)} Tabellen erfolgreich")
    print("=" * 60)

    return 0 if success_count == len(migration_order) else 1


if __name__ == "__main__":
    sys.exit(main())
