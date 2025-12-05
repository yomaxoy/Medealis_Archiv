"""
User Context Helper.

Zentraler Helper für User-Kontext aus Streamlit Session State.
Wird später mit Authentication-System integriert.
"""

import streamlit as st


def get_current_user() -> str:
    """
    Holt aktuellen Benutzer aus Session State.

    TODO: Später mit Authentication-System integrieren.
    Aktuell Fallback auf "System" wenn kein User gesetzt.

    Returns:
        Username oder "System" als Fallback
    """
    return st.session_state.get("current_user", "System")


def set_current_user(username: str) -> None:
    """
    Setzt aktuellen Benutzer in Session State.

    TODO: Wird vom Authentication-System aufgerufen.

    Args:
        username: Benutzername
    """
    st.session_state.current_user = username


def clear_current_user() -> None:
    """
    Löscht aktuellen Benutzer aus Session State (Logout).

    TODO: Wird vom Authentication-System beim Logout aufgerufen.
    """
    if "current_user" in st.session_state:
        del st.session_state.current_user
