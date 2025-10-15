# ===== src/warehouse/domain/exceptions/__init__.py =====
"""
Domain Exceptions Package für das Warehouse Management System.

Enthält alle domain-spezifischen Exceptions für Fehlerbehandlung.
Bietet strukturierte Fehlerbehandlung für Business-Logic-Verletzungen.

Modules:
    base_exceptions: Basis-Exception-Klasse
    item_exceptions: Item-spezifische Fehler
    delivery_exceptions: Delivery-spezifische Fehler
    validation_exceptions: Validierungsfehler

Architecture:
    Alle Domain-Exceptions erben von BaseDomainException und bieten
    strukturierte Fehlerinformationen für die Application Layer.
"""

from .base_exceptions import BaseDomainException
from .item_exceptions import (
    ItemNotFoundException,
    InvalidStatusTransitionException,
    ItemAlreadyExistsException,
    ItemNotEditableException,
)
from .delivery_exceptions import (
    DeliveryNotFoundException,
    DeliveryAlreadyCompletedException,
    DeliveryAlreadyExistsException,
    EmptyDeliveryException,
)
from .validation_exceptions import (
    ValidationException,
    MultipleValidationException,
    RequiredFieldException,
    InvalidFormatException,
)

__all__ = [
    # Base Exception
    "BaseDomainException",
    # Item Exceptions
    "ItemNotFoundException",
    "InvalidStatusTransitionException",
    "ItemAlreadyExistsException",
    "ItemNotEditableException",
    # Delivery Exceptions
    "DeliveryNotFoundException",
    "DeliveryAlreadyCompletedException",
    "DeliveryAlreadyExistsException",
    "EmptyDeliveryException",
    # Validation Exceptions
    "ValidationException",
    "MultipleValidationException",
    "RequiredFieldException",
    "InvalidFormatException",
]
