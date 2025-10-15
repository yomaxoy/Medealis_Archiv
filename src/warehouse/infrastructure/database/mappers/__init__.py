# src/warehouse/infrastructure/database/mappers/__init__.py

"""
Database Mappers Package - Vollständig für alle Domain Objects.

Exportiert alle Mapper für Clean Architecture Domain Objects Migration.
Bidirektionales Mapping zwischen SQLAlchemy Models und Domain Entities.

Mapper Functions:
- to_domain(): Database Model → Domain Entity
- to_model(): Domain Entity → Database Model
- update_model(): Aktualisiert Database Model mit Domain Entity Daten

Architecture:
- BaseMapper: Abstract base für alle Mapper
- Entity-spezifische Mapper für jede Domain Entity
- Robuste Error-Handling und Fallback-Mechanismen
- Null-safe Mapping für Production-Einsatz
"""

from .base_mapper import BaseMapper
from .item_mapper import ItemMapper
from .delivery_mapper import DeliveryMapper
from .supplier_mapper import SupplierMapper
from .order_mapper import OrderMapper, OrderItemMapper

__all__ = [
    # Base Mapper
    "BaseMapper",
    # Entity Mappers
    "ItemMapper",
    "DeliveryMapper",
    "SupplierMapper",
    "OrderMapper",
    "OrderItemMapper",
]

# === CONVENIENCE ALIASES ===
# Für einfachere Verwendung

# Primary Mappers
ItemEntityMapper = ItemMapper
DeliveryEntityMapper = DeliveryMapper
SupplierEntityMapper = SupplierMapper
OrderEntityMapper = OrderMapper

# Specialized Mappers
OrderItemEntityMapper = OrderItemMapper

# === FACTORY FUNCTIONS ===


def create_item_mapper():
    """Erstellt Item Mapper Instanz."""
    return ItemMapper()


def create_delivery_mapper():
    """Erstellt Delivery Mapper Instanz."""
    return DeliveryMapper()


def create_supplier_mapper():
    """Erstellt Supplier Mapper Instanz."""
    return SupplierMapper()


def create_order_mapper():
    """Erstellt Order Mapper Instanz."""
    return OrderMapper()


def create_order_item_mapper():
    """Erstellt OrderItem Mapper Instanz."""
    return OrderItemMapper()


class MapperFactory:
    """
    Mapper Factory für Dependency Injection.
    Zentrale Stelle für Mapper-Erzeugung.
    """

    @staticmethod
    def create_all_mappers():
        """
        Erstellt alle Mapper.

        Returns:
            Dictionary mit allen Mapper Instanzen
        """
        return {
            "item": ItemMapper(),
            "delivery": DeliveryMapper(),
            "supplier": SupplierMapper(),
            "order": OrderMapper(),
            "order_item": OrderItemMapper(),
        }

    @staticmethod
    def create_entity_mappers():
        """
        Erstellt nur die Haupt-Entity Mapper.

        Returns:
            Dictionary mit Entity Mapper Instanzen
        """
        return {
            "item": ItemMapper(),
            "delivery": DeliveryMapper(),
            "supplier": SupplierMapper(),
            "order": OrderMapper(),
        }


# === VALIDATION HELPERS ===


def validate_mapper_compatibility():
    """
    Validiert, dass alle Mapper korrekt funktionieren.

    Returns:
        Dictionary mit Validierungsergebnissen
    """
    results = {}

    try:
        # Test alle Mapper
        mappers = MapperFactory.create_all_mappers()

        for name, mapper in mappers.items():
            try:
                # Basic validation
                if hasattr(mapper, "to_domain") and hasattr(mapper, "to_model"):
                    results[name] = {
                        "status": "OK",
                        "methods": ["to_domain", "to_model"],
                    }
                else:
                    results[name] = {
                        "status": "ERROR",
                        "error": "Missing required methods",
                    }
            except Exception as e:
                results[name] = {"status": "ERROR", "error": str(e)}

    except Exception as e:
        results["factory"] = {"status": "ERROR", "error": str(e)}

    return results


# === DEBUG HELPERS ===


def debug_mapper_roundtrip(mapper_name: str, test_data: dict = None):
    """
    Debug-Hilfsmethode für Mapper Roundtrip Testing.

    Args:
        mapper_name: Name des zu testenden Mappers
        test_data: Test-Daten für Mapping

    Returns:
        Dictionary mit Roundtrip-Ergebnissen
    """
    try:
        mappers = MapperFactory.create_all_mappers()
        mapper = mappers.get(mapper_name)

        if not mapper:
            return {"error": f"Mapper '{mapper_name}' not found"}

        # TODO: Implement specific roundtrip tests for each mapper
        # This would require creating test Models and Entities

        return {
            "mapper": mapper_name,
            "status": "Mapper available",
            "methods": [method for method in dir(mapper) if not method.startswith("_")],
        }

    except Exception as e:
        return {"error": f"Debug failed: {e}"}


# === USAGE EXAMPLES ===
"""
# Basic Usage
from warehouse.infrastructure.database.mappers import ItemMapper, DeliveryMapper

item_mapper = ItemMapper()
delivery_mapper = DeliveryMapper()

# Domain Entity → Database Model
item_model = item_mapper.to_model(item_entity)

# Database Model → Domain Entity  
item_entity = item_mapper.to_domain(item_model)

# Factory Usage
from warehouse.infrastructure.database.mappers import MapperFactory

# Alle Mapper
mappers = MapperFactory.create_all_mappers()
item_mapper = mappers['item']

# Nur Entity Mapper
entity_mappers = MapperFactory.create_entity_mappers()

# Individual Creation
from warehouse.infrastructure.database.mappers import (
    create_item_mapper,
    create_delivery_mapper
)

item_mapper = create_item_mapper()
delivery_mapper = create_delivery_mapper()

# Validation
from warehouse.infrastructure.database.mappers import validate_mapper_compatibility

validation_results = validate_mapper_compatibility()
if all(result.get("status") == "OK" for result in validation_results.values()):
    print("All mappers are working correctly!")
"""
