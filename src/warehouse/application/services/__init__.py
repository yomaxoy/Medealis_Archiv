"""
Application Services Package

Dieses Paket enthält alle Application Layer Services für das Warehouse Management System.
Die Services implementieren die Business Logic und orchestrieren Domain Entities.

Available Services:
- DeliveryService: Lieferungsmanagement
- ItemService: Artikel-/Bestandsmanagement
- SupplierService: Lieferantenmanagement
- OrderService: Bestellungsmanagement
- InspectionService: Qualitätsprüfungen
- DocumentService: Dokumentenmanagement
- ReportingService: Reporting und Analytics
- AIExtractionService: KI-basierte Datenextraktion

NEW CENTRALIZED SERVICES:
- DocumentStorageService: Zentralisierte Dokument-Speicherung (Phase 1)
- DocumentGenerationService: Zentralisierte Dokument-Generierung (Phase 2)
- DeliveryWorkflowService: Lieferungs-Workflow Orchestrierung (Phase 3)
- DocumentOperations: Dokument-Operationen (Öffnen, PDF-Merge)
"""

# Core Domain Services
from .entity_services.delivery_service import DeliveryService
from .entity_services.item_service import ItemService
from .entity_services.supplier_service import SupplierService
from .entity_services.order_service import OrderService

# NEW: Centralized Document Services
from .document_storage import DocumentStorageService, determine_manufacturer
from .document_generation import DocumentGenerationService
from .delivery_workflow_service import DeliveryWorkflowService
from .document_operations import DocumentOpeningService, PDFMergeService, pdf_merge_service

# System Initialization Function
def initialize_system() -> bool:
    """
    Initialize application infrastructure.

    Provides a clean interface for the Presentation Layer to initialize
    the system without directly importing Infrastructure components.

    This function follows Clean Architecture principles by keeping
    Infrastructure dependencies within the Application Layer.

    Returns:
        bool: True if initialization successful, False on error

    Example:
        >>> from warehouse.application.services import initialize_system
        >>> if not initialize_system():
        ...     raise RuntimeError("System initialization failed")
    """
    try:
        # Import Infrastructure only within Application Layer
        from warehouse.infrastructure.database.connection import (
            initialize_database,
            create_tables,
            is_initialized
        )

        if not is_initialized():
            initialize_database()
            create_tables()
            _ensure_default_admin()

        return True

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"System initialization failed: {e}")
        return False


def _ensure_default_admin():
    """Erstellt Default-Admin falls kein User existiert."""
    try:
        import uuid
        from warehouse.infrastructure.database.connection import get_session
        from warehouse.infrastructure.database.models.user_model import UserModel
        from warehouse.infrastructure.security.password_hasher import PasswordHasher

        with get_session() as session:
            user_count = session.query(UserModel).count()
            if user_count == 0:
                hasher = PasswordHasher()
                admin = UserModel(
                    user_id=str(uuid.uuid4()),
                    username="admin",
                    email="admin@medealis.local",
                    password_hash=hasher.hash_password("Admin123!"),
                    role="admin",
                    is_active=True,
                    must_change_password=True,
                    full_name="System Administrator",
                )
                session.add(admin)
                session.commit()
                import logging
                logging.getLogger(__name__).info(
                    "Default-Admin erstellt (admin / Admin123!)"
                )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Default-Admin konnte nicht erstellt werden: {e}")


__all__ = [
    # Core Domain Services
    "DeliveryService",
    "ItemService",
    "SupplierService",
    "OrderService",
    # NEW: Document Services
    "DocumentStorageService",
    "DocumentGenerationService",
    "DeliveryWorkflowService",
    "DocumentOpeningService",
    "PDFMergeService",
    "pdf_merge_service",
    "determine_manufacturer",  # NEW: Centralized manufacturer determination
    # System Initialization
    "initialize_system",  # Clean Architecture-compliant system initialization
]
