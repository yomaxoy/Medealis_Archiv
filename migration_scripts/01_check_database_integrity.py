#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Integrity Check Script
Prüft SQLite-Datenbank vor PostgreSQL-Migration
"""

import sqlite3
import sys
import io
from pathlib import Path
from datetime import datetime
import json

# Fix Windows Console Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Datenbank-Pfade
DB_PATHS = [
    Path.home() / ".medealis" / "warehouse_new.db",
    Path("./data/medealis_db/warehouse_new.db"),
]


def find_database():
    """Findet die aktuelle Datenbank."""
    for db_path in DB_PATHS:
        if db_path.exists():
            print(f"✅ Datenbank gefunden: {db_path}")
            print(f"   Größe: {db_path.stat().st_size / 1024:.2f} KB")
            print(
                f"   Letzte Änderung: {datetime.fromtimestamp(db_path.stat().st_mtime)}"
            )
            return db_path

    print("❌ Keine Datenbank gefunden!")
    return None


def check_integrity(db_path):
    """Führt PRAGMA integrity_check aus."""
    print("\n" + "=" * 60)
    print("1. SQLITE INTEGRITY CHECK")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    result = cursor.execute("PRAGMA integrity_check").fetchone()

    if result[0] == "ok":
        print("✅ Datenbank-Integrität: OK")
    else:
        print(f"❌ Integritätsfehler: {result[0]}")
        return False

    conn.close()
    return True


def check_foreign_keys(db_path):
    """Prüft Foreign Key Constraints."""
    print("\n" + "=" * 60)
    print("2. FOREIGN KEY CONSTRAINT CHECK")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Aktiviere Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Hole alle Tabellen
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    all_ok = True
    for (table,) in tables:
        violations = cursor.execute(f"PRAGMA foreign_key_check({table})").fetchall()
        if violations:
            print(f"❌ {table}: {len(violations)} FK-Verletzungen")
            for v in violations[:5]:  # Zeige erste 5
                print(f"   {v}")
            all_ok = False
        else:
            print(f"✅ {table}: Keine FK-Verletzungen")

    conn.close()
    return all_ok


def get_table_stats(db_path):
    """Sammelt Statistiken über alle Tabellen."""
    print("\n" + "=" * 60)
    print("3. TABELLEN-STATISTIKEN")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Hole alle Tabellen
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    stats = {}

    for (table,) in tables:
        # Row Count
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        # Spalten
        columns = cursor.execute(f"PRAGMA table_info({table})").fetchall()
        col_count = len(columns)

        # Indexes
        indexes = cursor.execute(f"PRAGMA index_list({table})").fetchall()
        idx_count = len(indexes)

        stats[table] = {"rows": count, "columns": col_count, "indexes": idx_count}

        print(
            f"📊 {table:25s} | Rows: {count:6d} | Cols: {col_count:2d} | Indexes: {idx_count}"
        )

    conn.close()
    return stats


def check_data_types(db_path):
    """Analysiert Datentypen für PostgreSQL-Kompatibilität."""
    print("\n" + "=" * 60)
    print("4. DATENTYP-ANALYSE (PostgreSQL-Kompatibilität)")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    warnings = []

    for (table,) in tables:
        columns = cursor.execute(f"PRAGMA table_info({table})").fetchall()

        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col

            # Prüfe problematische Typen
            col_type_upper = col_type.upper()

            if "BLOB" in col_type_upper:
                warnings.append(f"⚠️  {table}.{col_name}: BLOB → PostgreSQL BYTEA (OK)")
            elif col_type_upper in ["REAL", "NUMERIC", "DECIMAL"]:
                warnings.append(
                    f"⚠️  {table}.{col_name}: {col_type} → PostgreSQL NUMERIC (OK)"
                )

    if warnings:
        print("\n".join(warnings))
    else:
        print("✅ Alle Datentypen sind PostgreSQL-kompatibel")

    conn.close()
    return len(warnings)


def create_backup(db_path):
    """Erstellt Backup der Datenbank."""
    print("\n" + "=" * 60)
    print("5. BACKUP ERSTELLEN")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"warehouse_new_MIGRATION_BACKUP_{timestamp}.db"

    import shutil

    shutil.copy2(db_path, backup_path)

    print(f"✅ Backup erstellt: {backup_path}")
    print(f"   Größe: {backup_path.stat().st_size / 1024:.2f} KB")

    return backup_path


def export_schema(db_path):
    """Exportiert Schema als SQL."""
    print("\n" + "=" * 60)
    print("6. SCHEMA EXPORT")
    print("=" * 60)

    conn = sqlite3.connect(db_path)

    schema_sql = "\n".join(conn.iterdump())

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    schema_path = db_path.parent / f"schema_dump_{timestamp}.sql"

    schema_path.write_text(schema_sql, encoding="utf-8")

    print(f"✅ Schema exportiert: {schema_path}")
    print(f"   Größe: {len(schema_sql) / 1024:.2f} KB")

    conn.close()
    return schema_path


def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("MEDEALIS DATABASE INTEGRITY CHECK")
    print("Pre-Migration zu PostgreSQL")
    print("=" * 60)

    # 1. Datenbank finden
    db_path = find_database()
    if not db_path:
        sys.exit(1)

    # 2. Integrity Check
    if not check_integrity(db_path):
        print("\n❌ KRITISCH: Integrity Check fehlgeschlagen!")
        sys.exit(1)

    # 3. Foreign Key Check
    fk_ok = check_foreign_keys(db_path)

    # 4. Tabellen-Statistiken
    stats = get_table_stats(db_path)

    # 5. Datentyp-Analyse
    type_warnings = check_data_types(db_path)

    # 6. Backup erstellen
    backup_path = create_backup(db_path)

    # 7. Schema exportieren
    schema_path = export_schema(db_path)

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)

    total_rows = sum(s["rows"] for s in stats.values())

    print(f"📊 Gesamt-Datensätze: {total_rows:,}")
    print(f"📊 Anzahl Tabellen: {len(stats)}")
    print(f"✅ Backup: {backup_path.name}")
    print(f"✅ Schema: {schema_path.name}")

    if fk_ok and type_warnings == 0:
        print("\n✅ BEREIT FÜR MIGRATION!")
        return 0
    else:
        print("\n⚠️  WARNUNGEN VORHANDEN - Bitte prüfen!")
        return 0  # Nicht kritisch


if __name__ == "__main__":
    sys.exit(main())
