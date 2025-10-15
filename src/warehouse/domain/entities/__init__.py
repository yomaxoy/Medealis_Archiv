# ===== src/warehouse/domain/entities/__init__.py =====
"""
Domain Entities Package für das Warehouse Management System.

Dieses Package enthält alle Domain Entities, die die Kerngeschäftsobjekte
des Systems repräsentieren. Entities haben Identität und können ihren
Zustand über die Zeit ändern.

Modules:
    item: Item Entity mit flexiblem Status-System für Medizinprodukte
    delivery: Delivery Aggregate Root für Lieferungsmanagement
    supplier: Supplier Entity für Lieferantenverwaltung
    order: Order Entity für Bestellungsverwaltung

Architecture:
    Die Entities bilden das Herzstück der Domain Layer und enthalten
    die gesamte Geschäftslogik. Sie sind unabhängig von Infrastructure
    und verwenden nur Value Objects und Enums aus der Domain.
"""

from .item import Item, InspectionResult
from .delivery import Delivery
from .supplier import Supplier
from .order import Order, OrderItem

__all__ = [
    # Item Entity und zugehörige Value Objects
    "Item",
    "InspectionResult",
    # Delivery Aggregate Root
    "Delivery",
    # Supplier Entity
    "Supplier",
    # Order Entity und Value Objects
    "Order",
    "OrderItem",
]
