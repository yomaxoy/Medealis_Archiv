# ===== src/warehouse/domain/value_objects/__init__.py =====
"""
Value Objects Package für das Warehouse Management System.

Value Objects sind unveränderliche Objekte, die durch ihre Eigenschaften
definiert werden, nicht durch ihre Identität. Sie kapseln einfache
Datentypen mit Geschäftslogik und Validierung.

Modules:
    article_number: 5-stellige Artikelnummer mit Validierung
    batch_number: 19-stellige Chargennummer für Rückverfolgbarkeit

Architecture:
    Value Objects sind immutable (frozen dataclasses) und führen
    Validierung in __post_init__ durch. Sie sind fundamental für
    die Typsicherheit und Geschäftsregeln des Systems.
"""

from .article_number import ArticleNumber
from .batch_number import BatchNumber

__all__ = [
    "ArticleNumber",
    "BatchNumber",
]
