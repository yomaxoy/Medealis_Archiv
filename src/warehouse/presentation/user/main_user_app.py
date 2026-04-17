"""
Main User Application - User Presentation Layer
Entry point for the simplified user interface.
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
    page_title="Medealis Warehouse - User",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",  # Hide sidebar by default
)


def main():
    """Main user application entry point."""
    try:
        # Initialize application (handles database, services, processors, session state)
        from warehouse.presentation.shared.app_initialization import (
            initialize_application
        )

        if not st.session_state.get("system_initialized"):
            logger.info("First run - initializing user system...")

            if not initialize_application(role="user"):
                st.error("Anwendungsfehler: Systeminitialisierung fehlgeschlagen")
                if st.button("Neu starten"):
                    st.cache_resource.clear()
                    if "system_initialized" in st.session_state:
                        del st.session_state.system_initialized
                    st.rerun()
                return

            logger.info("User system initialized successfully")

        # Authentication Gate
        from warehouse.presentation.auth.login_view import LoginView, is_authenticated

        if not is_authenticated():
            login_view = LoginView()
            login_view.show()
            return

        # Render user interface
        render_user_interface()

    except Exception as e:
        logger.error(f"User app error: {e}")
        st.error(f"Anwendungsfehler: {e}")

        if st.button("Neu starten"):
            # Clear cache and restart
            st.cache_resource.clear()
            if "system_initialized" in st.session_state:
                del st.session_state.system_initialized
            st.rerun()


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
