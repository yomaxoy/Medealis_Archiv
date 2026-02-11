# ===== src/warehouse/domain/services/__init__.py =====
"""
Domain Services Package für das Warehouse Management System.

Domain Services enthalten Geschäftslogik, die nicht natürlich zu einer
einzelnen Entity gehört oder mehrere Entities koordiniert.

Modules:
    inspection_service: Prüfungslogik für Artikel

Architecture:
    Domain Services arbeiten mit Entities und Value Objects,
    sind aber selbst zustandslos. Sie kapseln komplexe
    Geschäftsregeln und Multi-Entity-Operationen.
"""

from .inspection_service import InspectionService

__all__ = [
    "InspectionService",
]
