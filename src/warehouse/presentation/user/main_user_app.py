"""
Main User Application - User Presentation Layer
Entry point for the simplified user interface.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

# Load .env file BEFORE anything else - ALWAYS load to ensure API keys are available
try:
    from dotenv import load_dotenv
    env_file = src_dir / ".env"
    if env_file.exists():
        # Always load with override=True to ensure values are set
        load_dotenv(env_file, override=True)
except ImportError:
    pass  # python-dotenv not available
except Exception:
    pass  # Could not load .env file

import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application configuration
st.set_page_config(
    page_title="Medealis Warehouse - User",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",  # Hide sidebar by default
)


@st.cache_resource
def get_application_services():
    """
    Initialize and cache application services (Singleton).
    This ensures services are only initialized ONCE per Streamlit server session.
    """
    try:
        logger.info("Initializing application services (cached singleton)...")

        # Initialize database infrastructure
        from warehouse.application.services import initialize_system

        logger.info("Initializing database infrastructure...")
        if not initialize_system():
            raise RuntimeError("System initialization failed")
        logger.info("Database infrastructure initialized successfully")

        # Initialize Application Services
        from warehouse.application.services import (
            DeliveryService,
            ItemService,
            SupplierService,
            OrderService,
        )

        services = {
            "delivery": DeliveryService(),
            "item": ItemService(),
            "supplier": SupplierService(),
            "order": OrderService(),
        }

        logger.info("Application services initialized successfully (cached)")
        return services

    except Exception as e:
        logger.error(f"Failed to initialize application services: {e}")
        raise


@st.cache_resource
def get_document_processors():
    """
    Initialize and cache document processors (Singleton).
    This ensures processors are only initialized ONCE per Streamlit server session.
    """
    try:
        logger.info("Initializing document processors (cached singleton)...")

        from warehouse.application.processors import (
            pdf_processor,
            ocr_processor,
            claude_processor,
        )

        from warehouse.application.services.document_processing import (
            document_processing_service,
            process_document,
        )

        processors = {
            "pdf": pdf_processor,
            "ocr": ocr_processor,
            "claude": claude_processor,
            "document_processing_service": document_processing_service,
            "process_document": process_document,
        }

        logger.info("Document processors initialized successfully (cached)")
        return processors

    except Exception as e:
        logger.error(f"Failed to initialize document processors: {e}")
        raise


def main():
    """Main user application entry point."""
    try:
        # Initialize system ONCE using cached resources
        if "system_initialized" not in st.session_state:
            logger.info("First run - initializing user system...")

            # Get cached services (only initialized once)
            st.session_state.services = get_application_services()
            st.session_state.processors = get_document_processors()

            # Initialize session state defaults
            initialize_session_state()

            st.session_state.system_initialized = True
            logger.info("User system initialized successfully")

        # Render user interface
        render_user_interface()

    except Exception as e:
        logger.error(f"User app error: {e}")
        st.error(f"Anwendungsfehler: {e}")

        if st.button("🔄 Neu starten"):
            # Clear cache and restart
            st.cache_resource.clear()
            if "system_initialized" in st.session_state:
                del st.session_state.system_initialized
            st.rerun()


def initialize_session_state():
    """Initialize session state variables for user interface."""
    defaults = {
        "user_filter_delivery": "",
        "user_filter_article": "",
        "show_scan_popup": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_user_interface():
    """Render the main user interface."""
    # Main content area (no sidebar)
    render_user_main_content()


def render_user_main_content():
    """Render main content area."""
    try:
        from warehouse.presentation.user.views.main_user_view import (
            show_main_user_view,
        )

        show_main_user_view()

    except ImportError as e:
        logger.error(f"Could not import main user view: {e}")
        st.title("📦 Wareneingangskontrolle")
        st.error("Hauptansicht nicht verfügbar")
    except Exception as e:
        logger.error(f"Error in main user view: {e}")
        st.title("📦 Wareneingangskontrolle")
        st.error(f"Fehler in Hauptansicht: {e}")


if __name__ == "__main__":
    main()
