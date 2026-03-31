"""
Inspection Popup Functions
Modular implementation of inspection-related popup dialogs

Note: All inspection popups (including document merge) have been migrated to
warehouse.presentation.shared.popups and are used by both User & Admin apps.
"""

from warehouse.presentation.shared.popups import (
    show_visual_inspection_popup,
    show_measurement_popup,
    show_document_check_popup,
    show_data_confirmation_popup,
    show_document_merge_popup,
)

__all__ = [
    "show_visual_inspection_popup",
    "show_measurement_popup",
    "show_document_check_popup",
    "show_data_confirmation_popup",
    "show_document_merge_popup",
]
