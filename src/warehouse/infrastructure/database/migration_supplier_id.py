#!/usr/bin/env python
"""
Migration: Populate supplier_id in items table from deliveries table.

Dieses Skript füllt die neu hinzugefügte supplier_id-Spalte in der items-Tabelle
mit den Werten aus der deliveries-Tabelle basierend auf der delivery_number.

Nur für Items ohne supplier_id wird aktualisiert.
"""

import logging
from sqlalchemy import text
from warehouse.infrastructure.database.connection import get_session

logger = logging.getLogger(__name__)


def migrate_supplier_ids() -> int:
    """
    Migriert supplier_id Werte von deliveries zu items.

    Returns:
        Anzahl der aktualisierten Zeilen
    """
    try:
        with get_session() as session:
            # SQL: UPDATE items SET supplier_id = deliveries.supplier_id
            # WHERE items.delivery_number = deliveries.delivery_number
            # AND items.supplier_id IS NULL

            result = session.execute(
                text("""
                    UPDATE items
                    SET supplier_id = (
                        SELECT d.supplier_id
                        FROM deliveries d
                        WHERE d.delivery_number = items.delivery_number
                        LIMIT 1
                    )
                    WHERE supplier_id IS NULL
                """)
            )

            session.commit()
            rows_updated = result.rowcount

            logger.info(f"✓ Migration completed: {rows_updated} items updated with supplier_id")
            return rows_updated

    except Exception as e:
        logger.error(f"✗ Migration failed: {str(e)}")
        logger.exception("Full traceback:")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Starting migration: populate supplier_id in items...")
    try:
        count = migrate_supplier_ids()
        print(f"✓ Successfully updated {count} items with supplier_id")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        exit(1)
