"""
Shared Components - Wiederverwendbare UI-Komponenten für Popups.

Komponenten die von User-View UND Admin-View genutzt werden.

Author: Medealis
Version: 2.0.0 - Shared across User & Admin
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

from .storage_warning_dialog import (
    check_and_show_storage_warning,
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
    # Storage Warning
    "check_and_show_storage_warning",
]
