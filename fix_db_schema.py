"""
Fix DB Schema - Add missing columns
"""
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

print(f"Fixing database schema: {db_path}")
print()

# Connect to database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check and add missing columns
print("Checking item_workflow_steps table...")
cursor.execute("PRAGMA table_info(item_workflow_steps)")
columns = {row[1] for row in cursor.fetchall()}

if 'iteminfo_complete_by' not in columns:
    print("  Adding iteminfo_complete_by column...")
    cursor.execute("ALTER TABLE item_workflow_steps ADD COLUMN iteminfo_complete_by VARCHAR(100)")
    print("  [OK] Added iteminfo_complete_by")
else:
    print("  [OK] iteminfo_complete_by exists")

if 'iteminfo_complete_at' not in columns:
    print("  Adding iteminfo_complete_at column...")
    cursor.execute("ALTER TABLE item_workflow_steps ADD COLUMN iteminfo_complete_at DATETIME")
    print("  [OK] Added iteminfo_complete_at")
else:
    print("  [OK] iteminfo_complete_at exists")

print()
print("Checking item_info table...")
cursor.execute("PRAGMA table_info(item_info)")
columns = {row[1] for row in cursor.fetchall()}

if 'qr_code_image' not in columns:
    print("  Adding qr_code_image column...")
    cursor.execute("ALTER TABLE item_info ADD COLUMN qr_code_image BLOB")
    print("  [OK] Added qr_code_image")
else:
    print("  [OK] qr_code_image exists")

if 'qr_code_filename' not in columns:
    print("  Adding qr_code_filename column...")
    cursor.execute("ALTER TABLE item_info ADD COLUMN qr_code_filename VARCHAR(255)")
    print("  [OK] Added qr_code_filename")
else:
    print("  [OK] qr_code_filename exists")

if 'qr_code_uploaded_at' not in columns:
    print("  Adding qr_code_uploaded_at column...")
    cursor.execute("ALTER TABLE item_info ADD COLUMN qr_code_uploaded_at DATETIME")
    print("  [OK] Added qr_code_uploaded_at")
else:
    print("  [OK] qr_code_uploaded_at exists")

# Commit changes
conn.commit()
conn.close()

print()
print("[SUCCESS] Database schema fixed successfully!")
