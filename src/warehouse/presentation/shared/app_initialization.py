"""
Shared Application Initialization Module
Centralized initialization for both Admin and User apps.
Single source of truth for services, processors, and session state.
"""

import streamlit as st
import logging
from typing import Dict, Any, Literal

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE INITIALIZATION (runs once per server, not per Streamlit rerun)
# ============================================================================

def initialize_database():
    """
    Initialize database layer (ONLY RUNS ONCE PER SERVER).

    This must be called BEFORE caching service/processor initialization,
    and only needs to happen once for the entire Streamlit server session,
    shared between Admin and User apps.

    Raises:
        RuntimeError: If database initialization fails
    """
    try:
        logger.info("Initializing database infrastructure...")
        from warehouse.application.services import initialize_system

        if not initialize_system():
            raise RuntimeError("System initialization failed")

        logger.info("Database infrastructure initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


# ============================================================================
# CACHED SERVICES & PROCESSORS (shared between Admin and User apps)
# ============================================================================

@st.cache_resource
def get_services() -> Dict[str, Any]:
    """
    Initialize and cache Application Services via ServiceContainer.

    Uses @st.cache_resource + Singleton ServiceContainer to keep service
    instances alive across page navigations and shared between Admin/User apps.
    This is the SINGLE SOURCE OF TRUTH for service initialization.

    Returns:
        dict: Service instances for delivery, item, supplier, order management
              (legacy dict format for compatibility with existing code)
    """
    try:
        logger.info("Initializing services via ServiceContainer...")

        from warehouse.shared.service_container import get_services_dict

        services = get_services_dict()
        logger.info("Services initialized successfully")
        return services

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@st.cache_resource
def get_processors() -> Dict[str, Any]:
    """
    Initialize and cache Processors (PDF, OCR, Claude).

    Uses @st.cache_resource to lazy-load processors only when first needed
    and keep them cached across sessions.
    This is the SINGLE SOURCE OF TRUTH for processor initialization.

    Returns:
        dict: Processor instances (pdf, ocr, claude, document_processing_service)
    """
    try:
        logger.info("Initializing cached processors...")

        from warehouse.application.processors import (
            pdf_processor, ocr_processor, claude_processor
        )
        from warehouse.application.services.document_processing import (
            document_processing_service, process_document
        )

        processors = {
            "pdf": pdf_processor,
            "ocr": ocr_processor,
            "claude": claude_processor,
            "document_processing_service": document_processing_service,
            "process_document": process_document,
        }

        logger.info("Processors initialized successfully")
        return processors

    except Exception as e:
        logger.error(f"Failed to initialize processors: {e}")
        raise


# ============================================================================
# SESSION STATE SCHEMA & INITIALIZATION
# ============================================================================

# Centralized session state schema - single source of truth
SESSION_STATE_SCHEMA = {
    # Common session keys (shared by all apps)
    "common": {
        "system_initialized": False,
        "current_user": {},
        "logging_initialized": False,
        "db_initialized": False,
        "extracted_delivery_data": None,
        "show_scan_popup": False,
        "show_iteminfo_edit_dialog": False,
        "edit_iteminfo_item_data": {},
        "show_extraction_popup": False,
        "pending_doc_confirmation": None,
    },
    # Admin-specific session keys
    "admin": {
        "current_page": "Dashboard",
        "popup_action": None,
        "confirmed_delivery": None,
        "confirmed_items": None,
        "edit_mode": False,
        "selected_item": None,
        "last_extracted_text": None,
        "claude_extraction_result": None,
        "delete_delivery_confirmed": None,
        "show_success_popup": False,
        "success_message": None,
        "show_error_popup": False,
        "error_message": None,
        "show_new_delivery_popup": False,
        "scan_file_to_process": None,
        "scan_options": {},
        "confirmed_supplier": None,
        "updated_supplier": None,
        "delete_supplier_id": None,
        "edit_supplier_result": None,
        "delete_supplier_confirmed": None,
        "show_supplier_notes": False,
        "show_supplier_details": False,
        "show_supplier_statistics": False,
        "show_document_check_popup": False,
        "document_check_saved": False,
    },
    # User-specific session keys
    "user": {
        "user_filter_delivery": "",
        "user_filter_article": "",
    },
}


def initialize_session_state(role: Literal["admin", "user"] = "user"):
    """
    Initialize session state variables based on app role.

    Sets up all necessary session state keys for the specified app role.
    Common keys are initialized for all roles, plus role-specific keys.

    Args:
        role: Either "admin" or "user" - determines which session keys to initialize
    """
    if role not in ("admin", "user"):
        logger.warning(f"Unknown role: {role}, defaulting to 'user'")
        role = "user"

    # Initialize common keys for all apps
    common_defaults = SESSION_STATE_SCHEMA["common"]
    for key, value in common_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize role-specific keys
    role_defaults = SESSION_STATE_SCHEMA.get(role, {})
    for key, value in role_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    logger.info(f"Session state initialized for role: {role}")


# ============================================================================
# APP INITIALIZATION ORCHESTRATOR
# ============================================================================

def initialize_application(role: Literal["admin", "user"] = "user") -> bool:
    """
    Complete application initialization orchestrator.

    Coordinates all initialization steps in the correct order:
    1. Database (once per server)
    2. Services & Processors (cached per app)
    3. Session state (per user session)

    Args:
        role: "admin" or "user"

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    try:
        # Step 1: Ensure database is initialized (once per server)
        if not st.session_state.get("db_initialized"):
            initialize_database()
            st.session_state.db_initialized = True

        # Step 2: Initialize services and processors (cached, per app)
        if not st.session_state.get("system_initialized"):
            logger.info(f"Initializing {role} app services and processors...")
            st.session_state.services = get_services()
            st.session_state.processors = get_processors()

            # Step 3: Initialize session state (role-aware)
            initialize_session_state(role=role)

            st.session_state.system_initialized = True
            logger.info(f"{role.capitalize()} application initialized successfully")

        return True

    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        return False
