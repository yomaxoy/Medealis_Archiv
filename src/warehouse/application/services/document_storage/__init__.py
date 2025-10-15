"""
Document Storage Module - Zentralisierte Storage-Architektur

Exportiert alle Storage-Komponenten über eine einheitliche API.
SINGLE POINT OF ACCESS für alle Storage-Operationen.
"""

# Core storage components
from .storage_context import (
    StorageContext,
    StorageContextData,
    storage_context,
    determine_manufacturer  # NEW: Centralized manufacturer determination
)

from .path_resolver import (
    PathResolver,
    PathResult,
    path_resolver
)

from .storage_validator import (
    StorageValidator,
    ValidationResult,
    ValidationLevel,
    SecurityRisk,
    storage_validator
)

# Main storage service (now in same directory)
try:
    from .document_storage_service import (
        DocumentStorageService,
        StorageResult,
        document_storage_service
    )

except ImportError as e:
    # Fallback if document_storage_service is not available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import DocumentStorageService: {e}")

    # Create minimal fallback
    class DocumentStorageService:
        def __init__(self):
            self.logger = logger
            self.logger.error("DocumentStorageService not available - using fallback")

    document_storage_service = None


# Public API - was externe Services verwenden sollen
__all__ = [
    # Main service
    'DocumentStorageService',
    'StorageResult',
    'document_storage_service',

    # Centralized manufacturer determination
    'determine_manufacturer',  # NEW: Central manufacturer logic

    # Core components (for advanced usage)
    'StorageContext',
    'StorageContextData',
    'storage_context',

    'PathResolver',
    'PathResult',
    'path_resolver',

    'StorageValidator',
    'ValidationResult',
    'ValidationLevel',
    'SecurityRisk',
    'storage_validator'
]


def get_storage_service(validation_level=None):
    """
    Factory function für DocumentStorageService mit konfigurierbarem Validation Level.

    Args:
        validation_level: ValidationLevel oder None für Standard

    Returns:
        DocumentStorageService Instanz
    """
    if validation_level is None:
        validation_level = ValidationLevel.STANDARD

    return DocumentStorageService(validation_level)


def get_storage_statistics():
    """
    Gibt Statistiken über das Storage-System zurück.

    Returns:
        Dictionary mit Storage-Statistiken
    """
    if document_storage_service:
        return document_storage_service.get_storage_statistics()
    else:
        return {"error": "DocumentStorageService not available"}


def validate_storage_setup():
    """
    Validiert dass alle Storage-Komponenten korrekt funktionieren.

    Returns:
        Dictionary mit Validierungsergebnissen
    """
    results = {
        'storage_context': False,
        'path_resolver': False,
        'storage_validator': False,
        'document_storage_service': False,
        'errors': []
    }

    try:
        # Test StorageContext
        test_context = storage_context.get_complete_storage_context(
            batch_number="TEST-123",
            delivery_number="TEST-DEL"
        )
        results['storage_context'] = isinstance(test_context, StorageContextData)
    except Exception as e:
        results['errors'].append(f"StorageContext test failed: {e}")

    try:
        # Test PathResolver
        test_context_data = StorageContextData(
            batch_number="TEST-123",
            delivery_number="TEST-DEL"
        )
        preview_path = path_resolver.get_path_preview(test_context_data)
        results['path_resolver'] = isinstance(preview_path, str)
    except Exception as e:
        results['errors'].append(f"PathResolver test failed: {e}")

    try:
        # Test StorageValidator
        test_validation = storage_validator.validate_storage_context(
            StorageContextData(batch_number="TEST-123", delivery_number="TEST-DEL")
        )
        results['storage_validator'] = isinstance(test_validation, ValidationResult)
    except Exception as e:
        results['errors'].append(f"StorageValidator test failed: {e}")

    try:
        # Test DocumentStorageService
        if document_storage_service:
            stats = document_storage_service.get_storage_statistics()
            results['document_storage_service'] = 'error' not in stats
        else:
            results['errors'].append("DocumentStorageService not available")
    except Exception as e:
        results['errors'].append(f"DocumentStorageService test failed: {e}")

    results['all_components_working'] = all([
        results['storage_context'],
        results['path_resolver'],
        results['storage_validator'],
        results['document_storage_service']
    ])

    return results