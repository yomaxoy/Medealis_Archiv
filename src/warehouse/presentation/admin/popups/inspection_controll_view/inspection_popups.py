"""
Inspection Popup Functions
Modular implementation of inspection-related popup dialogs
Based on original streamlit_app.py implementation

This file now imports from separate popup modules for better maintainability.
"""

# Import all popup functions from their separate modules
from .data_confirmation_step1_popup import (
    show_data_confirmation_step1_popup,
)
from .document_confirmation_step2_popup import (
    show_document_confirmation_step2_popup,
)
from .visual_inspection_popup import show_visual_inspection_popup
from .measurement_popup import show_measurement_popup
from .merge_check_popup import show_merge_check_popup
from .document_check_popup import show_document_check_popup

# Re-export all functions for backward compatibility
__all__ = [
    "show_data_confirmation_step1_popup",
    "show_document_confirmation_step2_popup",
    "show_visual_inspection_popup",
    "show_measurement_popup",
    "show_merge_check_popup",
    "show_document_check_popup",
]
