"""
Inspection Control View Package - Shared utilities
"""
import streamlit as st


def get_current_username() -> str:
    """
    Helper function to extract full name from current_user session state.

    Returns:
        Full name or username string (e.g. 'John Doe' or 'admin') or 'System' if not available
    """
    current_user = st.session_state.get('current_user')

    # If current_user is a dict with full_name field
    if isinstance(current_user, dict):
        # Priorisiere full_name, fallback auf username
        full_name = current_user.get('full_name')
        if full_name and full_name.strip():
            return full_name
        return current_user.get('username', 'System')

    # If current_user is already a string
    if isinstance(current_user, str):
        return current_user

    # Fallback
    return 'System'
