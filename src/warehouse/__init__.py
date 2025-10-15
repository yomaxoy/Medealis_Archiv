# src/warehouse/__init__.py

"""
Warehouse Management System für Medizinprodukte.

Ein Python-basiertes System für Wareneingang, Qualitätskontrolle und
Rückverfolgbarkeit in der Medizinprodukte-Herstellung.

Architecture:
    - Domain Layer: Geschäftslogik und Entities
    - Infrastructure Layer: Datenpersistierung mit SQLAlchemy
    - Application Layer: Use Cases und Services (geplant)
    - Presentation Layer: GUI mit Tkinter (geplant)

Current Status: Infrastructure Layer Implementation
"""

# Version Info
__version__ = "2.0.0"
__author__ = "Medealis"

# Infrastructure Layer (verfügbar)
from . import infrastructure

# Domain Layer (verfügbar)
from . import domain

__all__ = ["infrastructure", "domain", "__version__", "__author__"]
