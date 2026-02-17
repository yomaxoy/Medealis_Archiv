"""
Inspection Control View Package - Shared utilities
"""
import streamlit as st


def get_current_username() -> str:
    """
    Helper function to extract username from current_user session state.

    Returns:
        Username string (e.g. 'admin') or 'System' if not available
    """
    current_user = st.session_state.get('current_user')

    # If current_user is a dict with username field
    if isinstance(current_user, dict):
        return current_user.get('username', 'System')

    # If current_user is already a string
    if isinstance(current_user, str):
        return current_user

    # Fallback
    return 'System'
