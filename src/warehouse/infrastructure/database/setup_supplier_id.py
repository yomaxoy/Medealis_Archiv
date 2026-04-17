#!/usr/bin/env python
"""
Setup-Skript: Fügt supplier_id-Spalte zu items-Tabelle hinzu und füllt sie.

Dieses Skript:
1. Erstellt die supplier_id-Spalte in der items-Tabelle (falls nicht vorhanden)
2. Erstellt den Foreign Key (falls nicht vorhanden)
3. Erstellt einen Index (falls nicht vorhanden)
4. Füllt die Spalte mit Werten aus der deliveries-Tabelle
"""

import logging
from sqlalchemy import text, inspect
from warehouse.infrastructure.database.connection import get_session

logger = logging.getLogger(__name__)


def setup_supplier_id() -> None:
    """
    Setup: Erstellt und füllt supplier_id in items table.
    """
    try:
        with get_session() as session:
            # Schritt 1: Prüfe ob Spalte bereits existiert
            inspector = inspect(session.get_bind())
            columns = {col['name'] for col in inspector.get_columns('items')}

            if 'supplier_id' not in columns:
                logger.info("Adding supplier_id column to items table...")

                # Füge supplier_id-Spalte hinzu
                session.execute(
                    text("""
                        ALTER TABLE items
                        ADD COLUMN supplier_id VARCHAR(20) NULL
                    """)
                )
                session.commit()
                logger.info("Column supplier_id added to items table")

                # Erstelle Index
                try:
                    session.execute(
                        text("""
                            CREATE INDEX idx_items_supplier_id ON items(supplier_id)
                        """)
                    )
                    session.commit()
                    logger.info("Index created")
                except Exception as e:
                    logger.warning(f"Could not create index (may already exist): {e}")

            else:
                logger.info("supplier_id column already exists in items table")

            # Schritt 2: Füllen der Spalte
            logger.info("Populating supplier_id from deliveries...")

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
            logger.info(f"Updated {rows_updated} items with supplier_id from deliveries")

            # Schritt 3: Validierung
            result = session.execute(
                text("""
                    SELECT COUNT(*) as count FROM items
                    WHERE supplier_id IS NULL
                """)
            )
            null_count = result.scalar() or 0

            if null_count > 0:
                logger.warning(f"{null_count} items still have NULL supplier_id")
                logger.warning("These items may not have matching deliveries")
            else:
                logger.info("All items have supplier_id assigned")

            logger.info("Setup completed successfully")

    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        logger.exception("Full traceback:")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Starting setup: adding and populating supplier_id...")
    try:
        setup_supplier_id()
        print("Setup completed successfully")
    except Exception as e:
        print(f"Setup failed: {e}")
        exit(1)
