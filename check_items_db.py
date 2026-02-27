"""Quick script to check items in database"""
import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings

# Get database path
Settings.DATABASE_DIR = None
Settings.DATABASE_PATH = None
Settings.ensure_directories()
db_path = Settings.get_database_path()

print(f"Checking database: {db_path}")
print()

# Connect and query
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Count items
cursor.execute("SELECT COUNT(*) FROM items")
count = cursor.fetchone()[0]
print(f"Total items in DB: {count}")
print()

# Show latest items
cursor.execute("""
    SELECT article_number, batch_number, delivery_number, created_at
    FROM items
    ORDER BY created_at DESC
    LIMIT 10
""")
print("Latest 10 items:")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")

conn.close()
