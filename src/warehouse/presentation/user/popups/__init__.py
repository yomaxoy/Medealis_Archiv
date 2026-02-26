"""
User Popups Package
Simplified popup dialogs for warehouse users.

Note: Core inspection popups (visual_inspection, measurement, document_check, data_confirmation)
have been migrated to warehouse.presentation.shared.popups and are used by both User & Admin apps.
"""

from .delivery_scan import show_delivery_scan_popup, show_extraction_confirmation_popup
from .document_merge import show_document_merge_popup

# Re-export shared popups for backward compatibility
from warehouse.presentation.shared.popups import (
    show_visual_inspection_popup,
    show_data_confirmation_popup,
    show_measurement_popup,
    show_document_check_popup,
)

__all__ = [
    "show_delivery_scan_popup",
    "show_extraction_confirmation_popup",
    "show_visual_inspection_popup",
    "show_data_confirmation_popup",
    "show_measurement_popup",
    "show_document_check_popup",
    "show_document_merge_popup",
]