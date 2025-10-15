# src/warehouse/domain/events/__init__.py

"""
Domain Events Package für das Warehouse Management System.

Enthält alle Domain Events für Event-driven Architecture und lose Kopplung
zwischen Domain-Komponenten. Events werden ausgelöst wenn wichtige
Geschäftsereignisse auftreten.

Modules:
    base: BaseDomainEvent Klasse mit gemeinsamer Event-Funktionalität
    item_events: Item-spezifische Events (Created, Inspection, Completed)
    delivery_events: Delivery-spezifische Events (Created, Completed)

Architecture:
    Domain Events ermöglichen Event-driven Architecture und entkoppeln
    verschiedene Teile des Systems. Events werden von Entities ausgelöst
    und von Event Handlers in der Application/Infrastructure Layer verarbeitet.

Usage:
    from warehouse.domain.events import BaseDomainEvent
    from warehouse.domain.events.item_events import ItemDataConfirmedEvent
    from warehouse.domain.events import create_item_data_confirmed_event
"""

# Base Event
from .base_event import BaseDomainEvent

# Item Events
# from .item_events import (
#   ItemDataConfirmedEvent,
#  ItemInspectionCompletedEvent,
# ItemCompletedEvent,
## Factory Methods
#    create_item_data_confirmed_event,
#   create_item_inspection_completed_event,
#  create_item_completed_event,
# )

# Placeholder für zukünftige Delivery Events
# from .delivery_events import (
#     DeliveryCreatedEvent,
#     DeliveryCompletedEvent,
#     create_delivery_created_event,
#     create_delivery_completed_event,
# )

__all__ = [
    # Base Event
    "BaseDomainEvent",
    # Item Events
    # "ItemDataConfirmedEvent",
    # "ItemInspectionCompletedEvent",
    # "ItemCompletedEvent",
    # Item Event Factory Methods
    #   "create_item_data_confirmed_event",
    #  "create_item_inspection_completed_event",
    # "create_item_completed_event",
    # "DeliveryCreatedEvent",
    # "DeliveryCompletedEvent",
    # "create_delivery_created_event",
    # "create_delivery_completed_event",
]
