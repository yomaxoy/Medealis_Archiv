#!/usr/bin/env python
"""Check users in database."""

import sqlite3
from pathlib import Path
from config.settings import Settings

# Get DB path
db_path = Settings.get_database_path()
print(f"Database: {db_path}")
print(f"Exists: {db_path.exists()}\n")

if not db_path.exists():
    print("ERROR: Database does not exist!")
    exit(1)

# Connect and query
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
table_exists = cursor.fetchone()

if not table_exists:
    print("ERROR: users table does not exist!")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Available tables: {tables}")
    conn.close()
    exit(1)

print("OK: users table exists\n")

# Get all users
cursor.execute("SELECT user_id, username, email, role, is_active, password_hash FROM users;")
users = cursor.fetchall()

print(f"Total users: {len(users)}\n")

if users:
    print("Users in DB:")
    print("-" * 80)
    for user_id, username, email, role, is_active, pwd_hash in users:
        status = "ACTIVE" if is_active else "INACTIVE"
        pwd_preview = pwd_hash[:20] + "..." if pwd_hash else "NO HASH"
        print(f"  {username:20} | {email:30} | {role:10} | {status:8} | {pwd_preview}")
else:
    print("No users found in database!")

conn.close()
