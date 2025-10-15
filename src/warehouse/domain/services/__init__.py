# ===== src/warehouse/domain/services/__init__.py =====
"""
Domain Services Package für das Warehouse Management System.

Domain Services enthalten Geschäftslogik, die nicht natürlich zu einer
einzelnen Entity gehört oder mehrere Entities koordiniert.

Modules:
    inspection_service: Prüfungslogik für Artikel
    certificate_service: Zertifikatsverwaltung
    audit_service: Audit Trail und Compliance

Architecture:
    Domain Services arbeiten mit Entities und Value Objects,
    sind aber selbst zustandslos. Sie kapseln komplexe
    Geschäftsregeln und Multi-Entity-Operationen.
"""

# Placeholder für zukünftige Domain Services
from .inspection_service import InspectionService

# from .certificate_service import CertificateService

# from .audit_service import AuditService

__all__ = [
    "InspectionService",
    #   "CertificateService",
    #   "AuditService",
]
