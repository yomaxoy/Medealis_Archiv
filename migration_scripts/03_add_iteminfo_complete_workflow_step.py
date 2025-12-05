"""
Migration Script: Add ItemInfo Complete Workflow Step

Fügt neue Workflow-Steps hinzu:
- iteminfo_complete_by (VARCHAR 100)
- iteminfo_complete_at (TIMESTAMP)

Dieser neue Schritt ist der erste im Workflow (vor "Daten prüfen").
"""

import os
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import logging
from sqlalchemy import text
from datetime import datetime

from warehouse.infrastructure.database.connection import (
    get_session,
    initialize_database,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_iteminfo_complete_columns():
    """Add iteminfo_complete workflow step columns to item_workflow_steps table if they don't exist."""

    logger.info("=" * 80)
    logger.info("Starting Migration: Add ItemInfo Complete Workflow Step")
    logger.info("=" * 80)

    # Initialize database
    initialize_database()

    try:
        with get_session() as session:
            # Check if columns already exist
            check_query = text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'item_workflow_steps'
                AND column_name IN ('iteminfo_complete_by', 'iteminfo_complete_at')
            """
            )

            result = session.execute(check_query)
            existing_columns = {row[0] for row in result}

            logger.info(
                f"Existing iteminfo_complete columns: {existing_columns if existing_columns else 'None'}"
            )

            # Add iteminfo_complete_by if not exists
            if "iteminfo_complete_by" not in existing_columns:
                logger.info("Adding column: iteminfo_complete_by (VARCHAR 100)")
                session.execute(
                    text(
                        """
                    ALTER TABLE item_workflow_steps
                    ADD COLUMN iteminfo_complete_by VARCHAR(100)
                """
                    )
                )
                logger.info("✅ Column iteminfo_complete_by added successfully")
            else:
                logger.info("⏭️  Column iteminfo_complete_by already exists - skipping")

            # Add iteminfo_complete_at if not exists
            if "iteminfo_complete_at" not in existing_columns:
                logger.info("Adding column: iteminfo_complete_at (TIMESTAMP)")
                session.execute(
                    text(
                        """
                    ALTER TABLE item_workflow_steps
                    ADD COLUMN iteminfo_complete_at TIMESTAMP
                """
                    )
                )
                logger.info("✅ Column iteminfo_complete_at added successfully")
            else:
                logger.info("⏭️  Column iteminfo_complete_at already exists - skipping")

            # Commit changes
            session.commit()

            # Verify all columns exist
            logger.info("\nVerifying migration...")
            result = session.execute(check_query)
            final_columns = {row[0] for row in result}

            required_columns = {"iteminfo_complete_by", "iteminfo_complete_at"}

            if required_columns.issubset(final_columns):
                logger.info("=" * 80)
                logger.info("✅ Migration completed successfully!")
                logger.info(f"All required columns present: {sorted(final_columns)}")
                logger.info("=" * 80)
                return True
            else:
                missing = required_columns - final_columns
                logger.error(f"❌ Migration incomplete - missing columns: {missing}")
                return False

    except Exception as e:
        logger.error(f"❌ Migration failed with error: {str(e)}")
        logger.exception("Full traceback:")
        return False


def show_table_info():
    """Display item_workflow_steps table structure after migration."""
    try:
        with get_session() as session:
            query = text(
                """
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable
                FROM information_schema.columns
                WHERE table_name = 'item_workflow_steps'
                ORDER BY ordinal_position
            """
            )

            result = session.execute(query)

            logger.info("\nCurrent item_workflow_steps table structure:")
            logger.info("-" * 80)
            logger.info(
                f"{'Column Name':<35} {'Type':<25} {'Max Length':<15} {'Nullable':<10}"
            )
            logger.info("-" * 80)

            for row in result:
                col_name, data_type, max_length, nullable = row
                max_len_str = str(max_length) if max_length else "N/A"
                logger.info(
                    f"{col_name:<35} {data_type:<25} {max_len_str:<15} {nullable:<10}"
                )

            logger.info("-" * 80)

    except Exception as e:
        logger.error(f"Could not display table info: {str(e)}")


if __name__ == "__main__":
    logger.info(f"Migration started at: {datetime.now()}")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")

    success = add_iteminfo_complete_columns()

    if success:
        show_table_info()
        logger.info("\n✅ Migration script completed successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration script failed")
        sys.exit(1)
