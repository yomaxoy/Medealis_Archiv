"""
User Context Helper.

Zentraler Helper für User-Kontext aus Streamlit Session State.
Integriert mit dem Authentication-System (login_view.py).
"""

import streamlit as st
from typing import Optional


def get_current_user() -> Optional[dict]:
    """
    Holt aktuellen Benutzer aus Session State.

    Wenn das Auth-System aktiv ist, gibt dies ein Dictionary zurück:
        {"user_id": ..., "username": ..., "email": ..., "role": ..., "full_name": ...}

    Falls kein User eingeloggt ist, wird None zurückgegeben.

    Returns:
        User-Dict oder None
    """
    return st.session_state.get("current_user")


def get_current_username() -> str:
    """
    Gibt den Benutzernamen des aktuell eingeloggten Users zurück.

    Fallback auf "System" wenn kein User eingeloggt ist.

    Returns:
        Username als String
    """
    user = st.session_state.get("current_user")
    if user is None:
        return "System"
    if isinstance(user, dict):
        return user.get("username", "System")
    return str(user)


def set_current_user(user_data: dict) -> None:
    """
    Setzt aktuellen Benutzer in Session State.

    Wird vom Authentication-System (LoginView) aufgerufen.

    Args:
        user_data: Dictionary mit user_id, username, email, role, full_name
    """
    st.session_state.current_user = user_data


def clear_current_user() -> None:
    """
    Löscht aktuellen Benutzer aus Session State (Logout).

    Wird vom Authentication-System beim Logout aufgerufen.
    """
    if "current_user" in st.session_state:
        del st.session_state.current_user
