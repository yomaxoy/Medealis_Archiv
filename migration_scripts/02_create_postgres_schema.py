#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create PostgreSQL Schema
Erstellt alle Tabellen in PostgreSQL basierend auf SQLAlchemy Models
"""

import sys
import io
import os

# Fix Windows Console Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Set DATABASE_URL for PostgreSQL
os.environ[
    "DATABASE_URL"
] = "postgresql://medealis_user:migration_test_password_2024@localhost:5432/medealis"

# Import nach Environment Variable setzen
from warehouse.infrastructure.database import (
    initialize_database,
    create_tables,
    test_connection,
    Base,
)
from warehouse.infrastructure.database.models import (
    ItemInfoModel,
    ItemModel,
    DeliveryModel,
    OrderModel,
    OrderItemModel,
    SupplierModel,
    ItemWorkflowStepsModel,
)


def main():
    """Erstellt PostgreSQL Schema."""
    print("=" * 60)
    print("POSTGRESQL SCHEMA CREATION")
    print("=" * 60)

    try:
        # 1. Initialisiere Database Connection
        print("\n1. Initialisiere PostgreSQL Connection...")
        initialize_database()
        print("✅ Connection initialisiert")

        # 2. Teste Connection
        print("\n2. Teste Database Connection...")
        if not test_connection():
            print("❌ Connection Test fehlgeschlagen!")
            return 1

        # 3. Erstelle Tabellen
        print("\n3. Erstelle Tabellen...")
        create_tables()
        print("✅ Tabellen erstellt")

        # 4. Validiere Schema
        print("\n4. Validiere Schema...")
        from sqlalchemy import inspect, text
        from warehouse.infrastructure.database.connection import get_session

        with get_session() as session:
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()

            print(f"\n📊 Anzahl Tabellen: {len(tables)}")
            for table in sorted(tables):
                columns = inspector.get_columns(table)
                fks = inspector.get_foreign_keys(table)
                indexes = inspector.get_indexes(table)

                print(
                    f"   ✅ {table:25s} | Cols: {len(columns):2d} | FKs: {len(fks):2d} | Indexes: {len(indexes):2d}"
                )

        print("\n" + "=" * 60)
        print("✅ SCHEMA ERFOLGREICH ERSTELLT!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
