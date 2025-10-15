"""
Document Operations Services

This module contains services for physical document operations:
- DocumentOpeningService: Cross-platform file/folder opening
- PDFMergeService: PDF merging and manipulation

These services handle file system operations on already generated documents.
"""

from .document_opening_service import DocumentOpeningService
from .pdf_merge_service import PDFMergeService, pdf_merge_service

__all__ = [
    'DocumentOpeningService',
    'PDFMergeService',
    'pdf_merge_service'
]