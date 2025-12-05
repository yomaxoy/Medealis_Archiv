"""
Migration: Setze Workflow-Status für bereits existierende ItemInfos

Dieses Skript setzt den Workflow-Status "Artikeldetails vollständig" für alle Items,
die bereits eine ItemInfo haben, aber noch keinen Status gesetzt haben.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from datetime import datetime
from sqlalchemy import text
from warehouse.infrastructure.database.connection import get_session


def migrate_existing_iteminfos():
    """Setzt Workflow-Status für alle bestehenden ItemInfos."""

    with get_session() as session:
        # Finde alle Artikelnummern mit ItemInfo
        result = session.execute(
            text(
                """
            SELECT DISTINCT article_number
            FROM item_info
        """
            )
        )

        article_numbers = [row[0] for row in result]

        print(f"Gefunden: {len(article_numbers)} Artikel mit ItemInfo")

        # Für jede Artikelnummer: Setze Status für alle Workflow-Einträge
        updated_count = 0

        for article_number in article_numbers:
            # Update alle Workflow-Einträge dieser Artikelnummer
            result = session.execute(
                text(
                    """
                UPDATE item_workflow_steps
                SET iteminfo_complete_by = :user,
                    iteminfo_complete_at = :timestamp
                WHERE article_number = :article_number
                AND iteminfo_complete_at IS NULL
            """
                ),
                {
                    "user": "System (Migration)",
                    "timestamp": datetime.now(),
                    "article_number": article_number,
                },
            )

            if result.rowcount > 0:
                updated_count += result.rowcount
                print(
                    f"  ✓ {article_number}: {result.rowcount} Workflow-Einträge aktualisiert"
                )

        session.commit()

        print(f"\n✅ Migration abgeschlossen!")
        print(f"   Insgesamt {updated_count} Workflow-Einträge aktualisiert")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Setze Workflow-Status für existierende ItemInfos")
    print("=" * 60)
    print()

    try:
        migrate_existing_iteminfos()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
