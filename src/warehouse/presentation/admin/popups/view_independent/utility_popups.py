"""
Utility Popups - Admin Presentation Layer
General purpose popup dialogs for feedback and debugging.
"""

import streamlit as st
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@st.dialog("✅ Erfolgreich!")
def show_success_popup(message: str = None, details: Dict[str, Any] = None):
    """Show success popup with optional details."""

    # Use session state or parameter message
    if not message:
        delivery_id = st.session_state.get('delivery_id', 'N/A')
        item_count = st.session_state.get('item_count', 0)
        message = f"✅ Lieferung {delivery_id} wurde erfolgreich erstellt! ({item_count} Artikel)"

    st.success(message)

    # Show details if available
    if details:
        st.write("### 📋 Details:")

        # Format details nicely
        for key, value in details.items():
            if isinstance(value, (dict, list)):
                st.write(f"**{key}:**")
                st.json(value)
            else:
                st.write(f"**{key}:** {value}")

    # Show session state details if available
    session_details = st.session_state.get('success_details', {})
    if session_details and not details:
        st.write("### 📊 Zusammenfassung:")
        for key, value in session_details.items():
            st.write(f"**{key}:** {value}")

    # Timestamp
    st.write(f"**Zeitstempel:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ OK", type="primary", use_container_width=True):
            # Clear success-related session state
            _clear_success_session_state()
            st.session_state.popup_action = 'close'
            st.rerun()

    with col2:
        if st.button("📋 Weitere Details", use_container_width=True):
            # Show additional session state info
            st.session_state.show_debug_info = True
            st.rerun()

    # Show debug info if requested
    if st.session_state.get('show_debug_info'):
        with st.expander("🔧 Debug-Informationen"):
            st.write("**Session State (relevante Teile):**")
            relevant_keys = ['delivery_id', 'item_count', 'last_extraction_result', 'save_result']
            debug_data = {k: v for k, v in st.session_state.items() if k in relevant_keys}
            if debug_data:
                st.json(debug_data)
            else:
                st.write("Keine relevanten Debug-Daten verfügbar")


@st.dialog("❌ Fehler aufgetreten")
def show_error_popup(error_message: str = None, error_details: Dict[str, Any] = None, show_debug: bool = True):
    """Show error popup with optional debug information."""

    # Use session state or parameter error
    if not error_message:
        error = st.session_state.get('save_error', 'Unbekannter Fehler')
        error_message = f"❌ Die Lieferung konnte nicht gespeichert werden!"
        st.error(error_message)
        st.code(str(error))
    else:
        st.error(error_message)

    # Show error details if available
    if error_details:
        st.write("### 🔍 Fehlerdetails:")

        if isinstance(error_details, dict):
            for key, value in error_details.items():
                if isinstance(value, Exception):
                    st.write(f"**{key}:** {type(value).__name__}: {str(value)}")
                else:
                    st.write(f"**{key}:** {value}")
        else:
            st.write(str(error_details))

    # Show session state error if available
    session_error = st.session_state.get('last_error_details')
    if session_error and not error_details:
        st.write("### ⚠️ Fehlerinformationen:")
        if isinstance(session_error, dict):
            st.json(session_error)
        else:
            st.code(str(session_error))

    # Show debug information if requested
    if show_debug:
        with st.expander("🔧 Debug-Informationen"):
            debug_info = _collect_error_debug_info()
            if debug_info:
                st.json(debug_info)
            else:
                st.write("Keine Debug-Informationen verfügbar")

    # Timestamp
    st.write(f"**Zeitstempel:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Erneut versuchen", type="primary", use_container_width=True):
            # Clear error state and try again
            _clear_error_session_state()
            st.session_state.popup_action = 'retry'
            st.rerun()

    with col2:
        if st.button("📋 Fehlerbericht kopieren", use_container_width=True):
            # Generate error report
            error_report = _generate_error_report(error_message, error_details)
            st.session_state.error_report = error_report
            st.success("📋 Fehlerbericht in Zwischenablage (Session State) gespeichert")

    with col3:
        if st.button("❌ Schließen", use_container_width=True):
            # Clear error state
            _clear_error_session_state()
            st.session_state.popup_action = 'close'
            st.rerun()


@st.dialog("🔧 Debug-Informationen")
def show_debug_information(debug_data: Dict[str, Any] = None, title: str = "System Debug"):
    """Show comprehensive debug information popup."""

    st.write(f"### {title}")

    # Use provided data or collect from session state
    if not debug_data:
        debug_data = _collect_comprehensive_debug_info()

    if not debug_data:
        st.info("Keine Debug-Informationen verfügbar")
        if st.button("✅ Schließen", type="primary"):
            st.session_state.popup_action = 'close'
            st.rerun()
        return

    # Categories for better organization
    categories = {
        'System': ['system_initialized', 'services', 'processors'],
        'Current Operation': ['current_data', 'last_extraction_result', 'claude_extraction_result'],
        'Session State': ['delivery_id', 'item_count', 'popup_action'],
        'Errors': ['save_error', 'last_error_details'],
        'Processing': ['last_extracted_text', 'extracted_delivery_data']
    }

    # Show organized debug information
    for category, keys in categories.items():
        category_data = {}
        for key in keys:
            if key in debug_data:
                category_data[key] = debug_data[key]

        if category_data:
            with st.expander(f"📊 {category}"):
                for key, value in category_data.items():
                    st.write(f"**{key}:**")

                    if isinstance(value, (dict, list)):
                        if len(str(value)) > 500:  # Truncate large objects
                            st.write(f"Type: {type(value).__name__}, Length: {len(value) if hasattr(value, '__len__') else 'N/A'}")
                            st.code(str(value)[:500] + "..." if len(str(value)) > 500 else str(value))
                        else:
                            st.json(value)
                    elif isinstance(value, Exception):
                        st.code(f"{type(value).__name__}: {str(value)}")
                    else:
                        st.code(str(value))

    # Full session state (collapsed by default)
    with st.expander("🗂️ Vollständiger Session State (Vorsicht: Sehr viele Daten)"):
        st.warning("⚠️ Enthält möglicherweise sensible Daten!")

        # Filter sensitive keys
        sensitive_keys = ['api_key', 'password', 'token', 'secret']
        filtered_state = {}

        for key, value in st.session_state.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                filtered_state[key] = "[SENSIBLE DATEN AUSGEBLENDET]"
            else:
                # Truncate very large objects
                if hasattr(value, '__len__') and len(str(value)) > 1000:
                    filtered_state[key] = f"[GROSSES OBJEKT: {type(value).__name__}, Länge: {len(value) if hasattr(value, '__len__') else 'N/A'}]"
                else:
                    filtered_state[key] = value

        st.json(filtered_state)

    # Export functionality
    st.write("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Debug-Export erstellen", use_container_width=True):
            export_data = _create_debug_export(debug_data)
            st.session_state.debug_export = export_data
            st.success("📥 Debug-Export erstellt! Verfügbar in Session State.")

    with col2:
        if st.button("🔄 Aktualisieren", use_container_width=True):
            st.rerun()

    with col3:
        if st.button("✅ Schließen", type="primary", use_container_width=True):
            st.session_state.popup_action = 'close'
            st.rerun()


def _clear_success_session_state():
    """Clear success-related session state variables."""
    success_keys = [
        'delivery_id', 'item_count', 'success_details',
        'show_success_popup', 'success_message'
    ]
    for key in success_keys:
        if key in st.session_state:
            del st.session_state[key]


def _clear_error_session_state():
    """Clear error-related session state variables."""
    error_keys = [
        'save_error', 'last_error_details', 'show_error_popup',
        'error_message', 'error_report'
    ]
    for key in error_keys:
        if key in st.session_state:
            del st.session_state[key]


def _collect_error_debug_info() -> Dict[str, Any]:
    """Collect relevant debug information for error diagnosis."""
    debug_info = {}

    # Error-relevant session state keys
    error_keys = [
        'save_error', 'last_error_details', 'last_extraction_result',
        'extracted_delivery_data', 'current_data', 'services', 'processors'
    ]

    for key in error_keys:
        if key in st.session_state:
            value = st.session_state[key]
            if isinstance(value, Exception):
                debug_info[key] = f"{type(value).__name__}: {str(value)}"
            elif hasattr(value, '__len__') and len(str(value)) > 200:
                debug_info[key] = f"[TRUNCATED] {str(value)[:200]}..."
            else:
                debug_info[key] = value

    return debug_info


def _collect_comprehensive_debug_info() -> Dict[str, Any]:
    """Collect comprehensive debug information from session state."""
    debug_info = {}

    # Important keys for debugging
    important_keys = [
        'system_initialized', 'services', 'processors', 'current_page',
        'current_data', 'last_extraction_result', 'claude_extraction_result',
        'delivery_id', 'item_count', 'popup_action', 'save_error',
        'last_error_details', 'last_extracted_text', 'extracted_delivery_data'
    ]

    for key in important_keys:
        if key in st.session_state:
            debug_info[key] = st.session_state[key]

    return debug_info


def _generate_error_report(error_message: str, error_details: Dict[str, Any] = None) -> str:
    """Generate a formatted error report."""
    report_lines = [
        "=== FEHLER-BERICHT ===",
        f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Fehler: {error_message}",
        ""
    ]

    if error_details:
        report_lines.append("Details:")
        for key, value in error_details.items():
            report_lines.append(f"  {key}: {value}")
        report_lines.append("")

    # Add relevant session state
    debug_info = _collect_error_debug_info()
    if debug_info:
        report_lines.append("Debug-Informationen:")
        for key, value in debug_info.items():
            report_lines.append(f"  {key}: {value}")

    report_lines.append("=== ENDE BERICHT ===")
    return "\n".join(report_lines)


def _create_debug_export(debug_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a comprehensive debug export."""
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'debug_data': debug_data,
        'session_summary': {
            'total_keys': len(st.session_state),
            'system_initialized': st.session_state.get('system_initialized', False),
            'current_page': st.session_state.get('current_page', 'Unknown')
        }
    }

    return export_data


def handle_utility_popup_actions():
    """Handle utility popup actions from session state."""
    try:
        # Handle retry action
        if st.session_state.get('popup_action') == 'retry':
            # Clear retry action
            st.session_state.popup_action = None

            # Here you could trigger a retry of the last failed operation
            st.info("🔄 Erneuter Versuch wird gestartet...")

        # Handle close action
        elif st.session_state.get('popup_action') == 'close':
            # Clear all popup-related session state
            popup_keys = [
                'show_success_popup', 'show_error_popup', 'show_debug_info',
                'popup_action', 'success_details', 'error_report'
            ]
            for key in popup_keys:
                if key in st.session_state:
                    del st.session_state[key]

    except Exception as e:
        logger.error(f"Error in utility popup actions: {e}")
        st.error(f"Utility-Popup-Fehler: {e}")