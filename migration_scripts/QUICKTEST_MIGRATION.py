#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCHNELLTEST: PostgreSQL Migration
OHNE Datenmigration - testet nur Schema + CRUD-Operationen
"""

import sys
import io
import os

# Fix Windows Console Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# PostgreSQL Connection
POSTGRES_URL = (
    "postgresql://medealis_user:migration_test_password_2024@localhost:5432/medealis"
)
os.environ["DATABASE_URL"] = POSTGRES_URL


def test_1_connection():
    """Test 1: Connection zu PostgreSQL."""
    print("\n" + "=" * 60)
    print("TEST 1: PostgreSQL Connection")
    print("=" * 60)

    try:
        from warehouse.infrastructure.database import (
            initialize_database,
            test_connection,
        )

        initialize_database(POSTGRES_URL)

        if test_connection():
            print("✅ Connection erfolgreich!")
            return True
        else:
            print("❌ Connection fehlgeschlagen!")
            return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_2_schema():
    """Test 2: Schema erstellen."""
    print("\n" + "=" * 60)
    print("TEST 2: Schema erstellen")
    print("=" * 60)

    try:
        from warehouse.infrastructure.database import create_tables
        from sqlalchemy import inspect
        from warehouse.infrastructure.database.connection import get_session

        # Schema erstellen
        print("Erstelle Tabellen...")
        create_tables()

        # Validiere
        with get_session() as session:
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()

            expected_tables = [
                "deliveries",
                "item_info",
                "item_workflow_steps",
                "items",
                "order_items",
                "orders",
                "suppliers",
            ]

            print(f"\n📊 Gefundene Tabellen: {len(tables)}")
            for table in sorted(tables):
                if table in expected_tables or "item_status" in table:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ⚠️  {table} (unbekannt)")

            if len(tables) >= 7:
                print("\n✅ Schema erfolgreich erstellt!")
                return True
            else:
                print(f"\n❌ Nur {len(tables)} Tabellen erstellt (erwartet: ≥7)")
                return False

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_3_crud_operations():
    """Test 3: CRUD-Operationen (Create, Read, Update, Delete)."""
    print("\n" + "=" * 60)
    print("TEST 3: CRUD-Operationen")
    print("=" * 60)

    try:
        from warehouse.infrastructure.database.connection import get_session
        from warehouse.infrastructure.database.models import (
            SupplierModel,
            ItemInfoModel,
            DeliveryModel,
            ItemModel,
        )
        from datetime import date

        with get_session() as session:
            # CREATE: Lieferant
            print("\n1. CREATE Supplier...")
            supplier = SupplierModel(
                supplier_id="TEST1",
                name="Test Supplier GmbH",
                contact_person="Max Mustermann",
                email="test@example.com",
                preferred_supplier="No",
            )
            session.add(supplier)
            session.flush()
            print("   ✅ Supplier erstellt")

            # CREATE: Artikel
            print("\n2. CREATE ItemInfo...")
            item_info = ItemInfoModel(
                article_number="TEST001",
                designation="Test-Artikel",
                revision_number=1,
                manufacturer="Test Manufacturer",
            )
            session.add(item_info)
            session.flush()
            print("   ✅ ItemInfo erstellt")

            # CREATE: Lieferung
            print("\n3. CREATE Delivery...")
            delivery = DeliveryModel(
                delivery_number="TEST-LS-001",
                supplier_id="TEST1",
                delivery_date=date.today(),
                employee_name="Test User",
                status="Empfangen",
            )
            session.add(delivery)
            session.flush()
            print("   ✅ Delivery erstellt")

            # CREATE: Item (mit FK zu allen obigen)
            print("\n4. CREATE Item...")
            item = ItemModel(
                article_number="TEST001",
                batch_number="TEST-BATCH-001",
                delivery_number="TEST-LS-001",
                delivered_quantity=100,
                material_certificate=True,
                employee="Test User",
            )
            session.add(item)
            session.flush()
            print("   ✅ Item erstellt")

            session.commit()

        # READ
        print("\n5. READ Operationen...")
        with get_session() as session:
            from sqlalchemy import select

            suppliers = session.execute(select(SupplierModel)).scalars().all()
            items_info = session.execute(select(ItemInfoModel)).scalars().all()
            deliveries = session.execute(select(DeliveryModel)).scalars().all()
            items = session.execute(select(ItemModel)).scalars().all()

            print(f"   Suppliers: {len(suppliers)}")
            print(f"   ItemInfo: {len(items_info)}")
            print(f"   Deliveries: {len(deliveries)}")
            print(f"   Items: {len(items)}")

            if len(suppliers) >= 1 and len(items) >= 1:
                print("   ✅ READ erfolgreich")
            else:
                print("   ❌ Daten nicht gefunden")
                return False

        # UPDATE
        print("\n6. UPDATE Operation...")
        with get_session() as session:
            supplier = session.execute(
                select(SupplierModel).where(SupplierModel.supplier_id == "TEST1")
            ).scalar_one()

            supplier.contact_person = "Updated Person"
            session.commit()
            print("   ✅ UPDATE erfolgreich")

        # DELETE
        print("\n7. DELETE Operations...")
        with get_session() as session:
            # Delete in richtiger Reihenfolge (FK-Dependencies)
            session.execute(
                select(ItemModel).where(ItemModel.article_number == "TEST001")
            )
            session.query(ItemModel).filter_by(article_number="TEST001").delete()
            session.query(DeliveryModel).filter_by(
                delivery_number="TEST-LS-001"
            ).delete()
            session.query(ItemInfoModel).filter_by(article_number="TEST001").delete()
            session.query(SupplierModel).filter_by(supplier_id="TEST1").delete()
            session.commit()
            print("   ✅ DELETE erfolgreich")

        print("\n✅ CRUD-Tests erfolgreich!")
        return True

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_4_foreign_keys():
    """Test 4: Foreign Key Constraints."""
    print("\n" + "=" * 60)
    print("TEST 4: Foreign Key Constraints")
    print("=" * 60)

    try:
        from warehouse.infrastructure.database.connection import get_session
        from warehouse.infrastructure.database.models import ItemModel
        from sqlalchemy.exc import IntegrityError

        with get_session() as session:
            # Versuch: Item mit nicht-existierender article_number
            print("\n1. Test: FK-Violation sollte fehlschlagen...")
            try:
                item = ItemModel(
                    article_number="FAKE001",  # 7 Zeichen (passt ins Schema)
                    batch_number="TEST",
                    delivery_number="FAKE-LS",  # 7 Zeichen (passt ins Schema)
                    delivered_quantity=1,
                    employee="Test",
                )
                session.add(item)
                session.flush()

                print("   ❌ FK-Constraint NICHT aktiv!")
                return False

            except IntegrityError:
                session.rollback()
                print("   ✅ FK-Constraint aktiv (wie erwartet)")
                return True

    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_5_performance():
    """Test 5: Performance-Test."""
    print("\n" + "=" * 60)
    print("TEST 5: Query Performance")
    print("=" * 60)

    try:
        from warehouse.infrastructure.database.connection import get_session
        from warehouse.infrastructure.database.models import SupplierModel
        from sqlalchemy import select
        import time

        # Erstelle Test-Daten
        with get_session() as session:
            for i in range(10):
                supplier = SupplierModel(
                    supplier_id=f"PERF{i:03d}",
                    name=f"Performance Test Supplier {i}",
                    preferred_supplier="No",
                )
                session.add(supplier)
            session.commit()

        # Performance Test
        with get_session() as session:
            start = time.time()

            for _ in range(100):
                suppliers = session.execute(select(SupplierModel)).scalars().all()

            end = time.time()
            avg_time = (end - start) / 100 * 1000  # ms

            print(f"\n📊 100 Queries in {(end-start)*1000:.2f}ms")
            print(f"   Durchschnitt: {avg_time:.2f}ms pro Query")

            # Cleanup
            session.query(SupplierModel).filter(
                SupplierModel.supplier_id.like("PERF%")
            ).delete()
            session.commit()

            if avg_time < 50:  # < 50ms ist gut
                print(f"   ✅ Performance OK ({avg_time:.2f}ms)")
                return True
            else:
                print(f"   ⚠️  Performance könnte besser sein ({avg_time:.2f}ms)")
                return True  # Nicht kritisch

    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def main():
    """Führt alle Tests aus."""
    print("=" * 60)
    print("POSTGRESQL MIGRATIONS-SCHNELLTEST")
    print("OHNE Datenmigration - Nur Schema + CRUD")
    print("=" * 60)

    tests = [
        ("Connection", test_1_connection),
        ("Schema", test_2_schema),
        ("CRUD Operations", test_3_crud_operations),
        ("Foreign Keys", test_4_foreign_keys),
        ("Performance", test_5_performance),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' abgestürzt: {e}")
            results.append((test_name, False))

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} | {test_name}")

    print("\n" + "=" * 60)
    print(f"Ergebnis: {passed}/{total} Tests bestanden")
    print("=" * 60)

    if passed == total:
        print("\n🎉 MIGRATION ERFOLGREICH!")
        print("\nNächster Schritt:")
        print(
            "  docker-compose --env-file .env.migration_test up -d medealis-admin medealis-user"
        )
        return 0
    else:
        print(f"\n⚠️  {total - passed} Test(s) fehlgeschlagen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
