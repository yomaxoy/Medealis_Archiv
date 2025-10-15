# src/warehouse/infrastructure/database/__init__.py

"""
Database Infrastructure Package.
Zentrale Exports für Database-Zugriff.
"""

from .connection import (
    initialize_database,
    get_session,
    create_tables,
    drop_tables,
    test_connection,
    Base,
)

# ⚠️ WICHTIG: Models müssen importiert werden, damit SQLAlchemy sie registriert!
from .models import BaseModel, ItemModel, DeliveryModel  # ← Das ist wichtig!

__all__ = [
    # Connection Management
    "initialize_database",
    "get_session",
    "create_tables",
    "drop_tables",
    "test_connection",
    "Base",
    # Models
    "BaseModel",
    "ItemModel",
    "DeliveryModel",
]
