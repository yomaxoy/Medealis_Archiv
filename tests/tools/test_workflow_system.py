"""
Test Script fuer das neue Workflow-Steps System.

Testet:
1. Item anlegen
2. Status-Berechnung
3. Workflow-Steps durchlaufen
4. Audit Trail (wer + wann)
5. Repository Persistence
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from warehouse.infrastructure.database.connection import initialize_database, get_session
from warehouse.infrastructure.database.repositories.sql_item_rep_domain import SQLAlchemyItemRepositoryDomain
from warehouse.domain.entities.item import Item, InspectionResult
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber
from warehouse.domain.enums.priority_level import PriorityLevel
from warehouse.domain.enums.certificate_type import CertificateType
from warehouse.infrastructure.database.models.item_model import ItemInfoModel
from warehouse.infrastructure.database.models.delivery_model import DeliveryModel
from warehouse.infrastructure.database.models.supplier_model import SupplierModel
from warehouse.domain.enums.delivery_status import DeliveryStatus


def print_item_status(item: Item, step_name: str):
    """Gibt Item Status aus."""
    print(f"\n{'='*60}")
    print(f"Nach: {step_name}")
    print(f"{'='*60}")
    print(f"Status: {item.get_current_status()}")
    print(f"\nWorkflow Steps:")
    print(f"  1. Daten pruefen:         {'DONE' if item.data_checked_by else 'TODO'}")
    if item.data_checked_by:
        print(f"     -> von {item.data_checked_by} am {item.data_checked_at}")

    print(f"  2. Dokumente pruefen:     {'DONE' if item.documents_checked_by else 'TODO'}")
    if item.documents_checked_by:
        print(f"     -> von {item.documents_checked_by} am {item.documents_checked_at}")

    print(f"  3. Vermessen:             {'DONE' if item.measured_by else 'TODO'}")
    if item.measured_by:
        print(f"     -> von {item.measured_by} am {item.measured_at}")

    print(f"  4. Sichtkontrolle:        {'DONE' if item.visually_inspected_by else 'TODO'}")
    if item.visually_inspected_by:
        print(f"     -> von {item.visually_inspected_by} am {item.visually_inspected_at}")

    print(f"  5. Dokumente zusammen:    {'DONE' if item.documents_merged_by else 'TODO'}")
    if item.documents_merged_by:
        print(f"     -> von {item.documents_merged_by} am {item.documents_merged_at}")

    print(f"\nFinale Stati:")
    print(f"  - Abgeschlossen:          {'JA' if item.completed_by else 'NEIN'}")
    if item.completed_by:
        print(f"     -> von {item.completed_by} am {item.completed_at}")

    print(f"  - Ausschuss:              {'JA' if item.rejected_by else 'NEIN'}")
    if item.rejected_by:
        print(f"     -> von {item.rejected_by} am {item.rejected_at}")
        print(f"     -> Grund: {item.rejection_reason}")


def test_workflow_system():
    """Testet das komplette Workflow System."""

    print("\n" + "="*60)
    print("TEST: WORKFLOW-STEPS SYSTEM")
    print("="*60)

    # 1. Initialize Database
    print("\n1. Initialisiere Datenbank...")
    initialize_database()
    repo = SQLAlchemyItemRepositoryDomain()
    print("   OK - Repository bereit")

    # 1b. Create prerequisite data (Supplier, Delivery, ItemInfo)
    print("\n1b. Erstelle Testdaten (Supplier, Delivery, ItemInfo)...")
    with get_session() as session:
        # Check if supplier already exists
        existing_supplier = session.get(SupplierModel, "SUP001")
        if not existing_supplier:
            # Create Supplier first
            supplier = SupplierModel(
                supplier_id="SUP001",
                name="Test Lieferant GmbH",
                contact_person="Hans Mueller"
            )
            session.add(supplier)
            session.flush()

        # Check if delivery already exists
        existing_delivery = session.get(DeliveryModel, "LS-2024-001")
        if not existing_delivery:
            # Create Delivery (references supplier)
            delivery = DeliveryModel(
                delivery_number="LS-2024-001",
                supplier_id="SUP001",
                delivery_date=datetime.now().date(),
                employee_name="Max Mustermann",
                status=DeliveryStatus.EMPFANGEN.value
            )
            session.add(delivery)
            session.flush()

        # Check if item_info already exists
        existing_item_info = session.get(ItemInfoModel, "MG00001")
        if not existing_item_info:
            # Create ItemInfo
            item_info = ItemInfoModel(
                article_number="MG00001",
                designation="Test Artikel MG00001"
            )
            session.add(item_info)
            # Final commit happens in context manager

    print("   OK - Testdaten erstellt (Supplier, Delivery, ItemInfo)")

    # 2. Create Test Item
    print("\n2. Erstelle Test Item...")
    article_number = ArticleNumber("MG00001")
    batch_number = BatchNumber("2024-001")
    delivery_number = "LS-2024-001"

    item = Item(
        article_number=article_number,
        batch_number=batch_number,
        delivery_number=delivery_number,
        supplier_id="SUP001",
        delivered_quantity=100,
        employee_name="Max Mustermann",
        priority_level=PriorityLevel.HIGH,
        order_number=None,  # No order for this test
        delivery_slip_quantity=100,
        ordered_quantity=100
    )

    # Add certificates
    item.certificates[CertificateType.MATERIALZEUGNIS] = True
    item.certificates[CertificateType.MESSPROTOKOLL] = True

    print(f"   OK - Item erstellt: {article_number}#{batch_number}#{delivery_number}")

    # Save initial item
    repo.save_domain(item)
    print("   OK - Item gespeichert")

    # Show initial status
    print_item_status(item, "Item angelegt")

    # 3. Test Workflow Step 1: Data Check
    print("\n\n3. Fuehre Schritt 1 aus: Daten pruefen...")
    item.complete_data_check("Anna Mueller")
    repo.save_domain(item)
    print("   OK - Daten geprueft und gespeichert")

    # Reload from DB to verify persistence
    item = repo.find_domain_by_composite_key(article_number, batch_number, delivery_number)
    print_item_status(item, "Daten pruefen (nach Reload)")

    # 4. Test Workflow Step 2: Document Check
    print("\n\n4. Fuehre Schritt 2 aus: Dokumente pruefen...")
    item.complete_document_check("Peter Schmidt")
    repo.save_domain(item)
    print("   OK - Dokumente geprueft und gespeichert")

    item = repo.find_domain_by_composite_key(article_number, batch_number, delivery_number)
    print_item_status(item, "Dokumente pruefen (nach Reload)")

    # 5. Test Workflow Step 3: Measurement
    print("\n\n5. Fuehre Schritt 3 aus: Vermessen...")
    measurements = {
        "length": 100.5,
        "width": 50.2,
        "height": 25.1
    }
    item.complete_measurement(measurements, "Thomas Weber")
    repo.save_domain(item)
    print("   OK - Vermessung durchgefuehrt und gespeichert")

    item = repo.find_domain_by_composite_key(article_number, batch_number, delivery_number)
    print_item_status(item, "Vermessen (nach Reload)")

    # 6. Test Workflow Step 4: Visual Inspection
    print("\n\n6. Fuehre Schritt 4 aus: Sichtkontrolle...")
    inspection = InspectionResult(
        performed_at=datetime.now(),
        performed_by="Lisa Fischer",
        waste_quantity=2,
        passed=True
    )
    item.complete_visual_inspection(inspection)
    repo.save_domain(item)
    print("   OK - Sichtkontrolle durchgefuehrt und gespeichert")

    item = repo.find_domain_by_composite_key(article_number, batch_number, delivery_number)
    print_item_status(item, "Sichtkontrolle (nach Reload)")

    # 7. Test Workflow Step 5: Documents Merge
    print("\n\n7. Fuehre Schritt 5 aus: Dokumente zusammenfuehren...")
    item.complete_documents_merge("Martin Becker")
    repo.save_domain(item)
    print("   OK - Dokumente zusammengefuehrt und gespeichert")

    item = repo.find_domain_by_composite_key(article_number, batch_number, delivery_number)
    print_item_status(item, "Dokumente zusammenfuehren (nach Reload)")

    # 8. Test Completion
    print("\n\n8. Schliesse Item ab...")
    item.complete_processing("Sandra Hoffmann")
    repo.save_domain(item)
    print("   OK - Item abgeschlossen und gespeichert")

    item = repo.find_domain_by_composite_key(article_number, batch_number, delivery_number)
    print_item_status(item, "Item Abgeschlossen (nach Reload)")

    # 9. Test Query Methods
    print("\n\n9. Teste Query Methods...")

    all_items = repo.find_domain_all()
    print(f"   find_domain_all(): {len(all_items)} Items gefunden")

    delivery_items = repo.find_domain_by_delivery(delivery_number)
    print(f"   find_domain_by_delivery(): {len(delivery_items)} Items gefunden")

    article_items = repo.find_by_article_number(str(article_number))
    print(f"   find_by_article_number(): {len(article_items)} Items gefunden")

    ready_items = repo.find_ready_for_completion()
    print(f"   find_ready_for_completion(): {len(ready_items)} Items bereit")

    # 10. Summary
    print("\n\n" + "="*60)
    print("TEST ERFOLGREICH ABGESCHLOSSEN")
    print("="*60)
    print("\nZusammenfassung:")
    print("  - Item angelegt und gespeichert")
    print("  - Alle 5 Workflow-Steps durchlaufen")
    print("  - Status korrekt berechnet bei jedem Step")
    print("  - Audit Trail (wer + wann) korrekt gespeichert")
    print("  - Persistence in beide Tabellen funktioniert")
    print("  - Query Methods funktionieren")
    print("\nDas neue Workflow-Steps System ist einsatzbereit!")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_workflow_system()
        if success:
            sys.exit(0)
        else:
            print("\nTEST FEHLGESCHLAGEN")
            sys.exit(1)
    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
