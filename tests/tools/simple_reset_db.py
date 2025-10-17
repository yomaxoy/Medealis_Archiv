# simple_reset_db.py

"""
Simple Database Reset Script without emoji characters.
Deletes the existing database and creates new schema with order_quantity and order_number columns.
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Setup Python path for imports."""
    current_dir = Path(__file__).parent.absolute()
    src_dir = current_dir

    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    return True

def delete_existing_database():
    """Delete existing database files."""
    medealis_dir = Path.home() / ".medealis"

    # Delete all database files
    db_files = [
        medealis_dir / "warehouse.db",
        medealis_dir / "warehouse_new.db"
    ]

    deleted_count = 0
    for db_path in db_files:
        if db_path.exists():
            try:
                os.remove(db_path)
                print(f"[OK] Database deleted: {db_path}")
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to delete database {db_path}: {e}")
                return False

    if deleted_count == 0:
        print("[INFO] No existing database files found")
    else:
        print(f"[INFO] Deleted {deleted_count} database file(s)")

    return True

def create_fresh_database():
    """Create fresh database with new schema."""
    print("\n[INFO] Creating new database with updated schema...")

    try:
        # Import after path setup
        from warehouse.infrastructure.database.connection import get_session, Base, initialize_database, create_tables, get_engine

        # Clear any existing metadata
        Base.metadata.clear()

        # Initialize database
        initialize_database()

        # Import all models to register them
        from warehouse.infrastructure.database.models.item_model import ItemModel, ItemInfoModel
        from warehouse.infrastructure.database.models.delivery_model import DeliveryModel
        from warehouse.infrastructure.database.models.supplier_model import SupplierModel
        from warehouse.infrastructure.database.models.order_model import OrderModel

        # Force reload metadata
        Base.metadata.reflect(bind=get_engine())

        # Create all tables with new schema
        create_tables()

        # Test connection
        with get_session() as session:
            pass

        print("[OK] New database created successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Database creation failed: {e}")
        return False

def verify_schema():
    """Verify that the new schema includes order_quantity and order_number columns."""
    try:
        from warehouse.infrastructure.database.connection import get_session

        # Check if order_quantity and order_number columns exist in item_info table
        from sqlalchemy import text
        with get_session() as session:
            result = session.execute(text("PRAGMA table_info(item_info)"))
            columns = [row[1] for row in result.fetchall()]

            if 'order_quantity' in columns and 'order_number' in columns:
                print("[OK] Schema verification passed - order_quantity and order_number columns found")
                return True
            else:
                print(f"[ERROR] Schema verification failed - columns found: {columns}")
                return False

    except Exception as e:
        print(f"[ERROR] Schema verification failed: {e}")
        return False

def main():
    """Main function for database reset."""
    print("DATABASE RESET FOR NEW SCHEMA")
    print("=" * 40)
    print("Deletes old database and creates new with correct schema")
    print()

    # Setup path
    if not setup_python_path():
        print("[ERROR] DATABASE RESET FAILED - Python Path")
        return False

    # Delete old database
    if not delete_existing_database():
        print("[ERROR] DATABASE RESET FAILED - Deletion")
        return False

    # Create new database
    if not create_fresh_database():
        print("[ERROR] DATABASE RESET FAILED - Creation")
        return False

    # Verify schema
    if not verify_schema():
        print("[ERROR] DATABASE RESET FAILED - Schema Verification")
        return False

    print("\n[SUCCESS] DATABASE RESET COMPLETED!")
    print("[OK] Old database deleted")
    print("[OK] New database with correct schema created")
    print("[OK] order_quantity and order_number columns available")
    print("[OK] Ready for order document analysis")

    return True

if __name__ == "__main__":
    main()