"""
Popup Components Package
Reusable UI components for building standardized popups.
"""

from .header_components import (
    render_article_header,
    render_status_badge,
)

from .form_components import (
    FormBuilder,
    render_quantity_inputs,
)

from .document_components import (
    render_document_uploader,
    render_folder_path,
)

from .footer_components import (
    render_action_buttons,
    render_two_button_footer,
    render_three_button_footer,
    render_quality_footer,
    render_standard_footer,
)

__all__ = [
    # Header
    "render_article_header",
    "render_status_badge",
    # Forms
    "FormBuilder",
    "render_quantity_inputs",
    # Documents
    "render_document_uploader",
    "render_folder_path",
    # Footer
    "render_action_buttons",
    "render_two_button_footer",
    "render_three_button_footer",
    "render_quality_footer",
    "render_standard_footer",
]
