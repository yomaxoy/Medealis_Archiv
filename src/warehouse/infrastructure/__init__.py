# ===== src/warehouse/infrastructure/__init__.py =====
"""
Infrastructure Layer für das Warehouse Management System.

Enthält alle technischen Implementierungen für Datenpersistierung,
externe Services und andere Infrastructure-Concerns.

Modules:
    database: SQLAlchemy-basierte Datenpersistierung
    external_services: Integration mit externen APIs (geplant)
    file_system: Datei-Operationen (geplant)

Current Status: Database Layer implementiert
"""

# Database Layer
from . import database

# Convenience Imports für häufig verwendete Funktionen
from .database import initialize_database, get_session, create_tables, ItemModel

__all__ = [
    # Modules
    "database",
    # Convenience Functions
    "initialize_database",
    "get_session",
    "create_tables",
    # Models
    "ItemModel",
]
