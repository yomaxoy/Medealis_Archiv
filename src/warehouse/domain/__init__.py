# ===== src/warehouse/domain/__init__.py =====
"""
Domain Layer für das Warehouse Management System.

Die Domain Layer enthält die Kerngeschäftslogik und ist unabhängig von
Infrastructure und Presentation Layers. Sie definiert Entities, Value Objects,
Enums, Services und Repository-Interfaces.

Architecture:
    - Entities: Geschäftsobjekte mit Identität (Item, Delivery, Supplier, Order)
    - Value Objects: Unveränderliche Objekte (ArticleNumber, BatchNumber)
    - Enums: Aufzählungstypen für Status und Kategorien
    - Exceptions: Domain-spezifische Fehlerbehandlung
    - Services: Domain-Services für komplexe Geschäftslogik
    - Repositories: Abstrakte Interfaces für Datenpersistierung

Usage:
    from warehouse.domain import entities, enums, value_objects, exceptions
    from warehouse.domain.entities import Item, Delivery
    from warehouse.domain.enums import ItemStatus, DeliveryStatus
    from warehouse.domain.value_objects import ArticleNumber, BatchNumber
"""

# Direkte Imports der am häufigsten verwendeten Klassen
from .entities import Item, Delivery, Supplier, Order
from .enums import ItemStatus, DeliveryStatus, CertificateType, PriorityLevel
from .value_objects import ArticleNumber, BatchNumber
from .exceptions import (
    BaseDomainException,
    ItemNotFoundException,
    DeliveryNotFoundException,
    ValidationException,
)

__version__ = "2.0.0"

__all__ = [
    # Packages
    "entities",
    "enums",
    "value_objects",
    "exceptions",
    # Core Entities
    "Item",
    "Delivery",
    "Supplier",
    "Order",
    # Core Enums
    "ItemStatus",
    "DeliveryStatus",
    "CertificateType",
    "PriorityLevel",
    # Core Value Objects
    "ArticleNumber",
    "BatchNumber",
    # Core Exceptions
    "BaseDomainException",
    "ItemNotFoundException",
    "DeliveryNotFoundException",
    "ValidationException",
]
