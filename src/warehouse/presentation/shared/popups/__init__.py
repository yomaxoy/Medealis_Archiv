"""
Shared Popups - Für User-View UND Admin-View.

Alle Inspection-Popups sind hier zentralisiert:
- Weniger Code-Duplikation
- Konsistente UX zwischen Views
- Einfachere Wartung
- Permission-Ready

Author: Medealis
Version: 2.0.0
"""

from .measurement import show_measurement_popup, MeasurementPopup
from .visual_inspection import show_visual_inspection_popup, VisualInspectionPopup
from .data_confirmation import show_data_confirmation_popup, DataConfirmationPopup
from .document_check import show_document_check_popup, DocumentCheckPopup
from .document_merge import show_document_merge_popup

__all__ = [
    # Measurement
    'show_measurement_popup',
    'MeasurementPopup',
    # Visual Inspection
    'show_visual_inspection_popup',
    'VisualInspectionPopup',
    # Data Confirmation
    'show_data_confirmation_popup',
    'DataConfirmationPopup',
    # Document Check
    'show_document_check_popup',
    'DocumentCheckPopup',
    # Document Merge
    'show_document_merge_popup',
]
