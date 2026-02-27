#!/usr/bin/env python
"""Test password verification."""

import sys
from warehouse.infrastructure.security.password_hasher import PasswordHasher
from warehouse.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from warehouse.domain.value_objects.username import Username

# Get password from command line
if len(sys.argv) < 3:
    print("Usage: python test_password.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

print(f"Testing credentials for: {username}")

# Get user from DB
repo = UserRepositoryImpl()
user = repo.find_by_username(Username(username))

if not user:
    print(f"ERROR: User '{username}' not found in database!")
    sys.exit(1)

print(f"User found: {user.username}")
print(f"Email: {user.email}")
print(f"Role: {user.role.value}")
print(f"Active: {user.is_active}")
print(f"Password hash (first 30 chars): {user.password_hash[:30]}...")

# Test password
hasher = PasswordHasher()
is_valid = hasher.verify_password(password, user.password_hash)

print(f"\nPassword verification: {'SUCCESS' if is_valid else 'FAILED'}")

if not is_valid:
    print("\nThe password you entered does NOT match the hash in the database.")
    print("If you forgot the password, you need to reset it via admin tools.")
