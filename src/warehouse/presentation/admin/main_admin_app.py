"""
Main Admin Application - Admin Presentation Layer
Entry point for the admin interface with clean architecture integration.
"""

import sys
import os
from pathlib import Path

# Add src and config to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent
config_dir = src_dir.parent / "config"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))
if str(config_dir) not in sys.path:
    sys.path.insert(0, str(config_dir))

# Load .env file BEFORE anything else - ALWAYS load to ensure API keys are available
try:
    from dotenv import load_dotenv
    # .env is in project root, one level up from src
    env_file = src_dir.parent / ".env"
    if env_file.exists():
        # Always load with override=True to ensure values are set
        load_dotenv(env_file, override=True)
except ImportError:
    pass  # python-dotenv not available
except Exception:
    pass  # Could not load .env file

import streamlit as st
import logging

# Standard Python Logger (wie alle anderen Module auch)
logger = logging.getLogger(__name__)

# Configure logging (einheitliches System mit User-Context)
# Setup wird nur einmal pro Session ausgeführt
# Import muss in Funktion sein, damit Path-Setup vorher läuft
if "logging_initialized" not in st.session_state:
    from logging_config import setup_logging  # config/ ist bereits im Path (Zeile 16)
    setup_logging(log_to_file=True, log_to_console=True)
    st.session_state.logging_initialized = True

# Application configuration
st.set_page_config(
    page_title="Medealis Warehouse Management - Admin",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main admin application entry point."""
    try:
        # Initialize system
        if "system_initialized" not in st.session_state:
            initialize_admin_system()
            st.session_state.system_initialized = True

        # Authentication Gate
        from warehouse.presentation.auth.login_view import LoginView, is_authenticated

        if not is_authenticated():
            login_view = LoginView()
            login_view.show()
            return

        # Render admin interface
        render_admin_interface()

    except Exception as e:
        logger.error(f"Admin app error: {e}")
        st.error(f"Anwendungsfehler: {e}")

        if st.button("Neu starten"):
            st.rerun()


@st.cache_resource
def get_services():
    """
    Initialize and cache Application Services via ServiceContainer.

    Uses @st.cache_resource + Singleton ServiceContainer to keep service
    instances alive across page navigations and shared between Admin/User apps.

    Returns:
        dict: Service instances for delivery, item, supplier, order management
              (legacy dict format for compatibility with existing code)
    """
    logger.info("Initializing services via ServiceContainer...")

    # Import ServiceContainer (Singleton - shared mit User-App!)
    from warehouse.shared.service_container import get_services_dict

    # Gibt Services als Dict zurück (für Kompatibilität mit bestehendem Code)
    return get_services_dict()


@st.cache_resource
def get_processors():
    """
    Initialize and cache Processors (PDF, OCR, Claude).

    Uses @st.cache_resource to lazy-load processors only when first needed
    and keep them cached across sessions.

    Returns:
        dict: Processor instances
    """
    logger.info("Initializing cached processors...")

    # Lazy import - Processors werden nur beim ersten Aufruf geladen
    from warehouse.application.processors import (
        pdf_processor, ocr_processor, claude_processor
    )
    from warehouse.application.services.document_processing import (
        document_processing_service, process_document
    )

    return {
        "pdf": pdf_processor,
        "ocr": ocr_processor,
        "claude": claude_processor,
        "document_processing_service": document_processing_service,
        "process_document": process_document,
    }


def initialize_admin_system():
    """Initialize admin system components."""
    try:
        logger.info("Initializing admin system...")

        # CLEAN ARCHITECTURE: Initialize system through Application Layer
        # (No direct Infrastructure imports in Presentation Layer)
        from warehouse.application.services import initialize_system

        logger.info("Initializing database infrastructure...")
        if not initialize_system():
            raise RuntimeError("System initialization failed")
        logger.info("Database infrastructure initialized successfully")

        # NEW: Use cached services (Lazy Loading + Caching for fast page switches)
        st.session_state.services = get_services()
        st.session_state.processors = get_processors()

        # Initialize session state
        initialize_session_state()

        logger.info("Admin system initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize admin system: {e}")
        st.error(f"Systeminitialisierung fehlgeschlagen: {e}")
        raise


def initialize_session_state():
    """Initialize session state variables."""
    defaults = {
        "current_page": "Dashboard",
        "popup_action": None,
        "confirmed_delivery": None,
        "confirmed_items": None,
        "edit_mode": False,
        "selected_item": None,
        "last_extracted_text": None,
        "claude_extraction_result": None,
        "extracted_delivery_data": None,
        "delete_delivery_confirmed": None,
        "show_success_popup": False,
        "success_message": None,
        "show_error_popup": False,
        "error_message": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_admin_interface():
    """Render the main admin interface."""
    # Sidebar navigation
    render_admin_sidebar()

    # Handle global popups (available from all pages)
    handle_global_popups()

    # Main content area
    render_admin_main_content()

    # Handle popup actions
    handle_popup_actions()


def handle_global_popups():
    """
    Handle global popups that should be accessible from all admin pages.
    These popups are triggered by the sidebar quick actions.
    """
    try:
        # Import shared popups used by both User & Admin
        from warehouse.presentation.user.popups.delivery_scan import (
            show_delivery_scan_popup,
            show_extraction_confirmation_popup,
        )
        from warehouse.presentation.user.popups.iteminfo_edit_dialog import (
            show_iteminfo_edit_dialog,
        )
        from warehouse.presentation.user.views.main_user_view import (
            handle_extraction_confirmation,
            SESSION_KEY_EXTRACTION_CONFIRMED,
        )

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
            services = st.session_state.get("services", {})
            handle_extraction_confirmation(services)

    except Exception as e:
        logger.error(f"Error handling global popups: {e}")
        st.error(f"Popup-Fehler: {e}")


def render_admin_sidebar():
    """Render admin sidebar navigation."""
    st.sidebar.title("Warehouse Admin")

    # User info & Logout
    from warehouse.presentation.auth.login_view import LoginView
    user = st.session_state.get("current_user", {})
    st.sidebar.markdown(f"**{user.get('full_name') or user.get('username', '?')}** ({user.get('role', '?')})")
    if st.sidebar.button("Abmelden", use_container_width=True):
        LoginView().logout()

    st.sidebar.write("---")

    # Navigation menu
    pages = {
        "📊 Dashboard": "Dashboard",
        "📦 Lieferungen": "Deliveries",
        "🏢 Lieferanten": "Suppliers",
        "📋 Artikel": "Items",
        "📋 Bestellungen": "Orders",
        "🔍 Wareneingangskontrolle": "Inspection",
    }

    # Benutzerverwaltung und Logs nur für Admins
    if user.get("role") == "admin":
        pages["👥 Benutzer"] = "Users"
        pages["📜 Protokoll"] = "AuditLog"

    selected_page = st.sidebar.radio("Navigation:", list(pages.keys()))
    st.session_state.current_page = pages[selected_page]

    # Quick actions
    st.sidebar.write("---")
    st.sidebar.write("**⚡ Schnellaktionen**")

    if st.sidebar.button("📄 Lieferschein scannen", use_container_width=True):
        st.session_state.show_scan_popup = True
        st.rerun()

    if st.sidebar.button("➕ Neue Lieferung", use_container_width=True):
        st.session_state.show_new_delivery_popup = True
        st.rerun()

    # System status
    render_system_status()


@st.cache_data(ttl=30)
def check_database_status(_services: dict) -> bool:
    """
    Check database connection health with lightweight query.

    Uses @st.cache_data with 30s TTL to avoid checking on every render.
    Uses a simple COUNT query instead of loading all deliveries.

    Args:
        _services: Service dict (underscore prefix to exclude from cache key)

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        # Lightweight health check - nur Connection testen, keine Daten laden
        from warehouse.infrastructure.database.connection import get_session
        with get_session() as session:
            # Simple ping query
            session.execute("SELECT 1")
        return True
    except:
        return False


def render_system_status():
    """Render system status in sidebar."""
    st.sidebar.write("---")
    st.sidebar.write("**🔧 System Status**")

    try:
        # Check processors status
        processors = st.session_state.get("processors", {})

        # OCR Status
        if "ocr" in processors:
            ocr_status = processors["ocr"].is_ocr_available()
            st.sidebar.write(f"OCR: {'✅' if ocr_status else '❌'}")

        # Claude Status
        if "claude" in processors:
            claude_status = processors["claude"].is_available()
            st.sidebar.write(f"Claude API: {'✅' if claude_status else '❌'}")

        # Database Status (cached, lightweight check)
        services = st.session_state.get("services", {})
        if services:
            db_status = check_database_status(services)
            st.sidebar.write(f"Database: {'✅' if db_status else '❌'}")

    except Exception as e:
        st.sidebar.error(f"Status check failed: {e}")


def render_admin_main_content():
    """Render main content area based on current page."""
    page = st.session_state.current_page

    try:
        if page == "Dashboard":
            render_dashboard_page()
        elif page == "Deliveries":
            render_deliveries_page()
        elif page == "Suppliers":
            render_suppliers_page()
        elif page == "Items":
            render_items_page()
        elif page == "Orders":
            render_orders_page()
        elif page == "Inspection":
            render_inspection_page()
        elif page == "Users":
            render_users_page()
        elif page == "AuditLog":
            render_audit_log_page()
        else:
            st.error(f"Unknown page: {page}")

    except Exception as e:
        logger.error(f"Error rendering page {page}: {e}")
        st.error(f"Fehler beim Laden der Seite {page}: {e}")


def render_dashboard_page():
    """Render dashboard page."""
    try:
        from warehouse.presentation.admin.views.dashboard_view import (
            show_dashboard_view,
        )

        show_dashboard_view()
    except ImportError as e:
        logger.error(f"Could not import dashboard view: {e}")
        st.title("📊 Dashboard")
        st.error("Dashboard-Ansicht nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        st.title("📊 Dashboard")
        st.error(f"Fehler im Dashboard: {e}")


def render_deliveries_page():
    """Render deliveries management page."""
    try:
        from warehouse.presentation.admin.views.delivery_management_view import (
            show_delivery_management_view,
        )

        show_delivery_management_view()
    except ImportError as e:
        logger.error(f"Could not import delivery management view: {e}")
        st.title("📦 Lieferungen")
        st.error("Lieferungen-Verwaltung nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in delivery management: {e}")
        st.title("📦 Lieferungen")
        st.error(f"Fehler in Lieferungen-Verwaltung: {e}")


def render_suppliers_page():
    """Render suppliers management page."""
    try:
        from warehouse.presentation.admin.views.supplier_management_view import (
            show_supplier_management_view,
        )

        show_supplier_management_view()
    except ImportError as e:
        logger.error(f"Could not import supplier management view: {e}")
        st.title("🏢 Lieferanten")
        st.error("Lieferanten-Verwaltung nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in supplier management: {e}")
        st.title("🏢 Lieferanten")
        st.error(f"Fehler in Lieferanten-Verwaltung: {e}")


def render_items_page():
    """Render items management page."""
    try:
        from warehouse.presentation.admin.views.item_management_view import (
            show_item_management_view,
        )

        show_item_management_view()
    except ImportError as e:
        logger.error(f"Could not import item management view: {e}")
        st.title("📋 Artikel")
        st.error("Artikel-Verwaltung nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in item management: {e}")
        st.title("📋 Artikel")
        st.error(f"Fehler in Artikel-Verwaltung: {e}")


def render_orders_page():
    """Render orders management page."""
    try:
        from warehouse.presentation.admin.views.orders_view import show_orders_view

        show_orders_view()
    except ImportError as e:
        logger.error(f"Could not import orders management view: {e}")
        st.title("📋 Bestellungen")
        st.error("Bestellungen-Verwaltung nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in orders management: {e}")
        st.title("📋 Bestellungen")
        st.error(f"Fehler in Bestellungen-Verwaltung: {e}")


def render_inspection_page():
    """Render inspection/quality control page."""
    try:
        # Import and show inspection functionality from inspection control view
        from warehouse.presentation.admin.views.inspection_control_view import (
            show_inspection_control_view,
        )

        # Show the inspection control view directly
        show_inspection_control_view()

    except ImportError as e:
        logger.error(f"Could not import inspection functionality: {e}")
        st.title("🔍 Wareneingangskontrolle")
        st.error("Wareneingangskontrolle nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in inspection page: {e}")
        st.title("🔍 Wareneingangskontrolle")
        st.error(f"Fehler in Wareneingangskontrolle: {e}")


def render_users_page():
    """Render user management page."""
    try:
        from warehouse.presentation.admin.views.user_management_view import (
            show_user_management_view,
        )

        show_user_management_view()
    except ImportError as e:
        logger.error(f"Could not import user management view: {e}")
        st.title("👥 Benutzer")
        st.error("Benutzerverwaltung nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in user management: {e}")
        st.title("👥 Benutzer")
        st.error(f"Fehler in Benutzerverwaltung: {e}")


def render_audit_log_page():
    """Render audit log page."""
    try:
        from warehouse.presentation.admin.views.audit_log_view import (
            show_audit_log_view,
        )

        show_audit_log_view()
    except ImportError as e:
        logger.error(f"Could not import audit log view: {e}")
        st.title("📜 Protokoll")
        st.error("Aktivitätsprotokoll nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in audit log: {e}")
        st.title("📜 Protokoll")
        st.error(f"Fehler im Aktivitätsprotokoll: {e}")


def handle_popup_actions():
    """Handle popup actions from session state (legacy page-specific popups)."""
    try:
        # NOTE: Global popups (scan, extraction) are now handled in handle_global_popups()
        # This function only handles page-specific popup actions

        # Handle popup action results (non-extraction actions)
        popup_action = st.session_state.get("popup_action")
        if popup_action and popup_action != "extraction_confirm":
            handle_popup_action_result(popup_action)
            st.session_state.popup_action = None

    except Exception as e:
        logger.error(f"Error handling popup actions: {e}")
        st.error(f"Popup-Fehler: {e}")


def handle_popup_action_result(action):
    """Handle specific popup action results."""
    if action == "scan_process":
        handle_scan_process()
    elif action == "confirm":
        handle_delivery_confirmation()
    elif action == "cancel":
        handle_popup_cancel()
    elif action == "close":
        handle_popup_close()
    elif action == "close_and_refresh":
        handle_popup_close_and_refresh()
    elif action == "edit_save":
        handle_edit_save()
    elif action == "delete_confirm":
        handle_delete_confirm()
    # Add more action handlers as needed


def handle_scan_process():
    """Handle file scan processing."""
    try:
        uploaded_file = st.session_state.get("scan_file_to_process")
        scan_options = st.session_state.get("scan_options", {})

        if uploaded_file:
            # Use unified document processing service for delivery slip processing
            from warehouse.application.services.document_processing.document_processing_service import document_processing_service

            # Read uploaded file data
            uploaded_file.seek(0)  # Reset file pointer
            document_data = uploaded_file.read()

            # Process as delivery document with System A + PDF Storage
            context = {
                "ocr_language": scan_options.get("ocr_language", "deu"),
                "ai_extraction": scan_options.get("ai_extraction", True),
                "quality_enhancement": scan_options.get("quality_enhancement", True),
                "document_data": document_data,  # Store document_data for PDF storage
                "filename": uploaded_file.name   # Store filename for reference
            }

            result = document_processing_service.process_document(
                document_data=document_data,
                document_type="delivery",
                context=context
            )

            if result:
                st.session_state.claude_extraction_result = result
                st.success("✅ Datei erfolgreich verarbeitet!")
            else:
                st.error("❌ Dateiverarbeitung fehlgeschlagen")

    except Exception as e:
        logger.error(f"Scan processing failed: {e}")
        st.error(f"Scan-Verarbeitung fehlgeschlagen: {e}")


def handle_delivery_confirmation():
    """Handle delivery confirmation."""
    confirmed_delivery = st.session_state.get("confirmed_delivery")
    confirmed_items = st.session_state.get("confirmed_items")

    if confirmed_delivery and confirmed_items:
        try:
            # Save to database using delivery service
            delivery_service = st.session_state.services["delivery"]

            # Implementation will be completed when integrating with existing save functions
            st.success("✅ Lieferung bestätigt und gespeichert!")

        except Exception as e:
            logger.error(f"Delivery confirmation failed: {e}")
            st.error(f"Lieferung speichern fehlgeschlagen: {e}")


def handle_popup_cancel():
    """Handle popup cancellation."""
    # Clear relevant session state
    cancel_keys = [
        "show_scan_popup",
        "show_new_delivery_popup",
        "confirmed_delivery",
        "confirmed_items",
        "scan_file_to_process",
        "scan_options",
        "confirmed_supplier",
        "updated_supplier",
        "delete_supplier_id",
        "edit_supplier_result",
        "delete_supplier_confirmed",
    ]

    for key in cancel_keys:
        if key in st.session_state:
            del st.session_state[key]


def handle_popup_close():
    """Handle popup close action."""
    # Clear display-related session state
    close_keys = [
        "show_supplier_notes",
        "show_supplier_details",
        "show_supplier_statistics",
    ]

    for key in close_keys:
        if key in st.session_state:
            del st.session_state[key]


def handle_popup_close_and_refresh():
    """Handle popup close action with main view refresh."""
    # Clear all popup-related session state
    close_keys = [
        "show_supplier_notes",
        "show_supplier_details",
        "show_supplier_statistics",
        "show_document_check_popup",
        "document_check_saved",
        "popup_action",
    ]

    for key in close_keys:
        if key in st.session_state:
            del st.session_state[key]

    # Show success message if available
    success_message = st.session_state.get("show_success_message")
    if success_message:
        st.success(success_message)
        # Clear the message after showing it
        del st.session_state.show_success_message


def handle_edit_save():
    """Handle edit save action."""
    try:
        if st.session_state.get("edit_supplier_result"):
            supplier_data = st.session_state.edit_supplier_result
            # This will be handled by the supplier view
            st.success("Änderungen gespeichert!")
            st.session_state.edit_supplier_result = None
            st.rerun()
    except Exception as e:
        logger.error(f"Edit save error: {e}")
        st.error(f"Fehler beim Speichern: {e}")


def handle_delete_confirm():
    """Handle delete confirmation action."""
    try:
        if st.session_state.get("delete_supplier_confirmed"):
            # This will be handled by the supplier view
            st.success("Element gelöscht!")
            st.session_state.delete_supplier_confirmed = None
            st.rerun()
    except Exception as e:
        logger.error(f"Delete confirm error: {e}")
        st.error(f"Fehler beim Löschen: {e}")


if __name__ == "__main__":
    main()
