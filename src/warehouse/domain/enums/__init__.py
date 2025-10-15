# ===== src/warehouse/domain/enums/__init__.py =====
"""
Enums Package für das Warehouse Management System.

Enthält alle Aufzählungstypen (Enums) für die Geschäftslogik.
Enums definieren gültige Werte für bestimmte Eigenschaften und
stellen Typsicherheit sicher.

Modules:
    item_status: Status-Definitionen für Item-Lifecycle
    delivery_status: Status-Definitionen für Delivery-Workflow
    certificate_type: Medizinprodukte-spezifische Zertifikatstypen
    priority_level: Prioritätsstufen für Bearbeitung

Architecture:
    Alle Enums erben von Python's Enum-Klasse und bieten
    zusätzliche Business-Methoden für UI-Integration und
    Geschäftslogik-Unterstützung.
"""

from .item_status import ItemStatus
from .delivery_status import DeliveryStatus
from .certificate_type import CertificateType
from .priority_level import PriorityLevel

__all__ = [
    "ItemStatus",
    "DeliveryStatus",
    "CertificateType",
    "PriorityLevel",
]
