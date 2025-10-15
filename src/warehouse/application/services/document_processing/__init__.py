"""
Unified Document Processing Module

Standardisierter Ansatz für alle Dokumentanalysen:
- Lieferscheine (delivery)
- Bestelldokumente (order)
- Begleitpapiere (accompanying)

Usage:
    from warehouse.application.services.document_processing import process_document

    result = process_document(
        document_data=file_bytes,
        document_type="delivery"
    )
"""

# Main API exports
from .document_processing_service import (
    UnifiedDocumentProcessingService,
    document_processing_service,
)

from .claude_api_client import (
    ClaudeAPIClient,
    claude_api_client,
)

from .prompt_template_manager import (
    PromptTemplateManager,
    DocumentType,
    prompt_manager,
)

from .document_validator import (
    DocumentValidator,
    document_validator,
)

from .document_cache import (
    DocumentCache,
    document_cache,
)

# Convenience API
def process_document(document_data: bytes, document_type: str, **kwargs):
    """
    Convenience function für Dokumentverarbeitung.

    Args:
        document_data: Document bytes
        document_type: "delivery", "order", or "accompanying"
        **kwargs: Additional context

    Returns:
        Processed document with validation_status
    """
    return document_processing_service.process_document(
        document_data=document_data,
        document_type=document_type,
        context=kwargs
    )

# Storage convenience functions
def save_order_data_to_database(article_number: str, order_quantity: int, order_number: str = "", order_date: str = ""):
    """Convenience function for saving order data to database."""
    return document_processing_service.save_order_data_to_database(
        article_number=article_number,
        order_quantity=order_quantity,
        order_number=order_number,
        order_date=order_date
    )

def save_accompanying_document(document_data: bytes, document_name: str, article_number: str, batch_number: str, delivery_number: str = "", supplier_name: str = ""):
    """Convenience function for saving accompanying documents."""
    return document_processing_service.save_accompanying_document(
        document_data=document_data,
        document_name=document_name,
        article_number=article_number,
        batch_number=batch_number,
        delivery_number=delivery_number,
        supplier_name=supplier_name
    )

__all__ = [
    # Main services
    'UnifiedDocumentProcessingService',
    'document_processing_service',
    'process_document',  # Convenience function

    # Storage functions
    'save_order_data_to_database',
    'save_accompanying_document',

    # Components
    'ClaudeAPIClient', 'claude_api_client',
    'PromptTemplateManager', 'DocumentType', 'prompt_manager',
    'DocumentValidator', 'document_validator',
    'DocumentCache', 'document_cache',
]