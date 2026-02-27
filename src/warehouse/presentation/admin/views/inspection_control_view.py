"""
Inspection Control View - Admin Presentation Layer
Wareneingangskontrolle (Goods Receipt Control) functionality.

NOTE: This view now uses the exact same workflow as the User-View
to ensure consistency and eliminate duplicate document generation.
"""

import streamlit as st
import logging
from typing import Dict, Any

# Import the proven User-View workflow
from warehouse.presentation.user.views.main_user_view import (
    show_item_table,
    handle_extraction_confirmation,
    SESSION_KEY_EXTRACTION_CONFIRMED,
)

# Import shared popups (used by both User & Admin)
from warehouse.presentation.shared.popups import (
    show_visual_inspection_popup,
    show_measurement_popup,
    show_document_check_popup,
    show_data_confirmation_popup,
)

# Import User-specific popups (now also used by Admin)
from warehouse.presentation.user.popups.delivery_scan import (
    show_delivery_scan_popup,
    show_extraction_confirmation_popup,
)
from warehouse.presentation.user.popups.iteminfo_edit_dialog import (
    show_iteminfo_edit_dialog,
)

# Admin-specific popup (only Merge remains Admin-only)
from warehouse.presentation.admin.popups.inspection_controll_view.merge_check_popup import (
    show_merge_check_popup,
)

logger = logging.getLogger(__name__)


def show_inspection_control_view():
    """
    Show Wareneingangskontrolle (Goods Receipt Control) - Admin View

    This view now uses the EXACT same workflow as User-View to ensure:
    - Consistency between User and Admin workflows
    - No duplicate document generation
    - Single source of truth for all popups
    """
    # Title, Scan button and User info in header
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.title("🔍 Wareneingangskontrolle")
    with col2:
        if st.button(
            "📄 Lieferschein scannen",
            type="primary",
            use_container_width=True,
            key="admin_scan_button_header",
        ):
            st.session_state.show_scan_popup = True
            st.rerun()
    with col3:
        user = st.session_state.get("current_user", {})
        st.caption(f"👤 {user.get('full_name') or user.get('username', '')}")
        if st.button("🚪 Abmelden", use_container_width=True, key="admin_logout_header"):
            from warehouse.presentation.auth.login_view import LoginView
            LoginView().logout()

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "item" not in services:
        st.error("Item Service nicht verfügbar")
        return

    # Handle Lieferschein-Scan Popup
    if st.session_state.get("show_scan_popup"):
        show_delivery_scan_popup()

    # Handle ItemInfo Edit Dialog
    if st.session_state.get("show_iteminfo_edit_dialog"):
        article_data = st.session_state.get("edit_iteminfo_item_data", {})
        if article_data:
            show_iteminfo_edit_dialog(article_data)

    # Handle Extraction Confirmation Popup
    if st.session_state.get("show_extraction_popup") and st.session_state.get(
        "extracted_delivery_data"
    ):
        show_extraction_confirmation_popup(st.session_state.extracted_delivery_data)

    # Handle popup actions (extraction confirm)
    if st.session_state.get("popup_action") == "extraction_confirm":
        handle_extraction_confirmation(services)

    # Main content: Use proven User-View item table
    show_item_table(services)
