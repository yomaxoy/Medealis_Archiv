"""
Migration Script: Add QR-Code Columns to ItemInfo Table

Adds three columns to item_info table:
- qr_code_image (BYTEA): Binary image data
- qr_code_filename (VARCHAR(255)): Original filename
- qr_code_uploaded_at (TIMESTAMP): Upload timestamp

This migration is idempotent - can be run multiple times safely.
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


def add_qr_code_columns():
    """Add QR-Code columns to item_info table if they don't exist."""

    logger.info("=" * 80)
    logger.info("Starting Migration: Add QR-Code Columns to ItemInfo")
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
                WHERE table_name = 'item_info'
                AND column_name IN ('qr_code_image', 'qr_code_filename', 'qr_code_uploaded_at')
            """
            )

            result = session.execute(check_query)
            existing_columns = {row[0] for row in result}

            logger.info(
                f"Existing QR columns: {existing_columns if existing_columns else 'None'}"
            )

            # Add qr_code_image if not exists
            if "qr_code_image" not in existing_columns:
                logger.info("Adding column: qr_code_image (BYTEA)")
                session.execute(
                    text(
                        """
                    ALTER TABLE item_info
                    ADD COLUMN qr_code_image BYTEA
                """
                    )
                )
                logger.info("✅ Column qr_code_image added successfully")
            else:
                logger.info("⏭️  Column qr_code_image already exists - skipping")

            # Add qr_code_filename if not exists
            if "qr_code_filename" not in existing_columns:
                logger.info("Adding column: qr_code_filename (VARCHAR(255))")
                session.execute(
                    text(
                        """
                    ALTER TABLE item_info
                    ADD COLUMN qr_code_filename VARCHAR(255)
                """
                    )
                )
                logger.info("✅ Column qr_code_filename added successfully")
            else:
                logger.info("⏭️  Column qr_code_filename already exists - skipping")

            # Add qr_code_uploaded_at if not exists
            if "qr_code_uploaded_at" not in existing_columns:
                logger.info("Adding column: qr_code_uploaded_at (TIMESTAMP)")
                session.execute(
                    text(
                        """
                    ALTER TABLE item_info
                    ADD COLUMN qr_code_uploaded_at TIMESTAMP
                """
                    )
                )
                logger.info("✅ Column qr_code_uploaded_at added successfully")
            else:
                logger.info("⏭️  Column qr_code_uploaded_at already exists - skipping")

            # Commit changes
            session.commit()

            # Verify all columns exist
            logger.info("\nVerifying migration...")
            result = session.execute(check_query)
            final_columns = {row[0] for row in result}

            required_columns = {
                "qr_code_image",
                "qr_code_filename",
                "qr_code_uploaded_at",
            }

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
    """Display item_info table structure after migration."""
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
                WHERE table_name = 'item_info'
                ORDER BY ordinal_position
            """
            )

            result = session.execute(query)

            logger.info("\nCurrent item_info table structure:")
            logger.info("-" * 80)
            logger.info(
                f"{'Column Name':<30} {'Type':<20} {'Max Length':<15} {'Nullable':<10}"
            )
            logger.info("-" * 80)

            for row in result:
                col_name, data_type, max_length, nullable = row
                max_len_str = str(max_length) if max_length else "N/A"
                logger.info(
                    f"{col_name:<30} {data_type:<20} {max_len_str:<15} {nullable:<10}"
                )

            logger.info("-" * 80)

    except Exception as e:
        logger.error(f"Could not display table info: {str(e)}")


if __name__ == "__main__":
    logger.info(f"Migration started at: {datetime.now()}")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")

    success = add_qr_code_columns()

    if success:
        show_table_info()
        logger.info("\n✅ Migration script completed successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration script failed")
        sys.exit(1)
