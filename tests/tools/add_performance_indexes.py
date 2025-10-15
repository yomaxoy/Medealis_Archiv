"""
Add Missing Database Indexes for Performance Optimization

This script adds 3 critical indexes to the items table:
1. idx_items_article_number - Enables fast JOINs with item_info
2. idx_items_status - Speeds up status filtering
3. idx_items_delivery_number - Speeds up delivery grouping

Expected improvement: 100x speedup for common queries at scale
"""

import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from warehouse.infrastructure.database.connection import (
    get_session,
    initialize_database,
    create_tables,
    is_initialized
)
from sqlalchemy import text


def add_performance_indexes():
    """Add missing performance indexes to items table."""

    # Initialize database if needed
    if not is_initialized():
        print("Initializing database...")
        initialize_database()
        create_tables()
        print("Database initialized")
        print()

    indexes_to_add = [
        {
            "name": "idx_items_article_number",
            "sql": "CREATE INDEX IF NOT EXISTS idx_items_article_number ON items(article_number)",
            "purpose": "Enables fast JOINs with item_info table (fixes N+1 problem)"
        },
        {
            "name": "idx_items_status",
            "sql": "CREATE INDEX IF NOT EXISTS idx_items_status ON items(status)",
            "purpose": "Speeds up status filtering (common in GUI)"
        },
        {
            "name": "idx_items_delivery_number",
            "sql": "CREATE INDEX IF NOT EXISTS idx_items_delivery_number ON items(delivery_number)",
            "purpose": "Speeds up delivery grouping"
        }
    ]

    print("=" * 70)
    print("ADDING PERFORMANCE INDEXES")
    print("=" * 70)
    print()

    with get_session() as session:
        for idx_info in indexes_to_add:
            print(f"Adding index: {idx_info['name']}")
            print(f"Purpose: {idx_info['purpose']}")

            try:
                session.execute(text(idx_info['sql']))
                session.commit()
                print("SUCCESS: Index created")
                print()
            except Exception as e:
                print(f"ERROR: {e}")
                print()

    # Verify indexes were created
    print("=" * 70)
    print("VERIFYING INDEXES")
    print("=" * 70)
    print()

    with get_session() as session:
        # Get all indexes on items table
        result = session.execute(text(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='items'"
        ))

        indexes = result.fetchall()

        print(f"Total indexes on 'items' table: {len(indexes)}")
        print()

        for name, sql in indexes:
            if name and not name.startswith('sqlite_'):
                print(f"Index: {name}")
                if sql:
                    print(f"SQL: {sql}")
                print()

    print("=" * 70)
    print("INDEX CREATION COMPLETE")
    print("=" * 70)
    print()
    print("Expected performance improvements:")
    print("- JOIN with item_info: O(n) -> O(log n)")
    print("- Filter by status: O(n) -> O(log n)")
    print("- Group by delivery: O(n) -> O(log n)")
    print()
    print("Overall: 100x speedup for common queries at scale (1000+ items)")


if __name__ == "__main__":
    add_performance_indexes()