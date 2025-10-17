# src/warehouse/domain/repositories/__init__.py

"""
Repository Interfaces Package für das Warehouse Management System.

Enthält abstrakte Repository-Interfaces, die von der Infrastructure
Layer implementiert werden. Definiert Contracts für Datenpersistierung
ohne konkrete Implementierungsdetails.

Modules:
    base_repository: Basis-Repository-Interface mit CRUD-Operationen
    item_repository: Item-Repository-Interface für Artikel-Datenzugriff
    delivery_repository: Delivery-Repository-Interface für Lieferungen
    supplier_repository: Supplier-Repository-Interface für Lieferanten

Architecture:
    Repository-Interfaces definieren Contracts für die Infrastructure
    Layer ohne konkrete Implementierung. Sie ermöglichen Dependency
    Inversion und Testbarkeit durch klare Abstraktionen.

Usage:
    from warehouse.domain.repositories import BaseRepository, ItemRepository
    from warehouse.domain.repositories.item_repository import ItemRepository

    # In Infrastructure Layer:
    class SqliteItemRepository(ItemRepository):
        def save(self, item: Item) -> Item:
            # Konkrete Implementierung
            pass
"""

from .base_repository import BaseRepository, ReadOnlyRepository
from .item_repository import ItemRepository
from .delivery_repository import DeliveryRepository
from .supplier_repository import SupplierRepository
from .order_repository import OrderRepository

__all__ = [
    # Base Repository Interfaces
    "BaseRepository",
    "ReadOnlyRepository",
    # Entity-specific Repository Interfaces
    "ItemRepository",
    "DeliveryRepository",
    "SupplierRepository",
    "OrderRepository",
]
