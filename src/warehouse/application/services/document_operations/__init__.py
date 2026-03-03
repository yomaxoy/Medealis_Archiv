"""
Document Operations Services

This module contains services for physical document operations:
- DocumentOpeningService: Cross-platform file/folder opening
- PDFMergeService: PDF merging and manipulation

These services handle file system operations on already generated documents.
"""

from .document_opening_service import DocumentOpeningService
from .pdf_merge_service import PDFMergeService, pdf_merge_service

# Singleton-Instanzen
document_opening_service = DocumentOpeningService()

__all__ = [
    'DocumentOpeningService',
    'document_opening_service',
    'PDFMergeService',
    'pdf_merge_service'
]