"""
Inspection Popup Functions
Modular implementation of inspection-related popup dialogs

Note: Core inspection popups (visual_inspection, measurement, document_check, data_confirmation)
have been migrated to warehouse.presentation.shared.popups and are used by both User & Admin apps.
"""

# Admin-specific popups (not migrated to shared)
from .merge_check_popup import show_merge_check_popup

# Re-export shared popups for backward compatibility
from warehouse.presentation.shared.popups import (
    show_visual_inspection_popup,
    show_measurement_popup,
    show_document_check_popup,
    show_data_confirmation_popup,
)

# Re-export all functions for backward compatibility
__all__ = [
    "show_visual_inspection_popup",
    "show_measurement_popup",
    "show_merge_check_popup",
    "show_document_check_popup",
    "show_data_confirmation_popup",
]
