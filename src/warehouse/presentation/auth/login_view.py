# src/warehouse/presentation/auth/login_view.py

import streamlit as st
import logging
from typing import Optional

from warehouse.application.services.user_service import UserService
from warehouse.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from warehouse.infrastructure.security.session_manager import SessionManager
from warehouse.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    UserInactiveError,
)

logger = logging.getLogger(__name__)


class LoginView:
    """Login-View für die Anwendung."""

    def __init__(
        self,
        user_service: Optional[UserService] = None,
        session_manager: Optional[SessionManager] = None,
    ):
        self._user_service = user_service or UserService(UserRepositoryImpl())
        self._session_manager = session_manager or SessionManager()

    def show(self) -> bool:
        """
        Zeigt Login-Formular an.

        Returns:
            True wenn erfolgreich eingeloggt
        """
        st.markdown("### 🔐 Anmeldung")
        st.markdown("---")

        # Login-Formular
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Benutzername", placeholder="z.B. max.mustermann")
            password = st.text_input("Passwort", type="password")

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submit = st.form_submit_button(
                    "Anmelden", type="primary", use_container_width=True
                )

            if submit:
                if not username or not password:
                    st.error("Bitte Benutzername und Passwort eingeben")
                    return False

                try:
                    # Authentifiziere User
                    user = self._user_service.authenticate(username, password)

                    # Erstelle Session
                    token = self._session_manager.create_session(
                        user_id=user.user_id,
                        username=str(user.username),
                        role=user.role.value,
                    )

                    # Speichere in Session State
                    st.session_state.auth_token = token
                    st.session_state.current_user = {
                        "user_id": user.user_id,
                        "username": str(user.username),
                        "email": str(user.email),
                        "role": user.role.value,
                        "full_name": user.full_name,
                    }

                    st.success(f"Willkommen, {user.full_name or user.username}!")
                    logger.info(f"User login successful: {username}")
                    st.rerun()
                    return True

                except InvalidCredentialsError:
                    st.error("Benutzername oder Passwort ungültig")
                    logger.warning(f"Failed login attempt for: {username}")
                    return False

                except UserInactiveError:
                    st.error(
                        "Ihr Benutzerkonto ist deaktiviert. "
                        "Bitte kontaktieren Sie einen Administrator."
                    )
                    logger.warning(f"Login attempt for inactive user: {username}")
                    return False

                except Exception as e:
                    st.error(
                        "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut."
                    )
                    logger.error(f"Login error for {username}: {str(e)}")
                    return False

        return False

    def logout(self):
        """Loggt den aktuellen User aus."""
        if "auth_token" in st.session_state:
            self._session_manager.invalidate_session(st.session_state.auth_token)

        # Clear session state
        for key in ["auth_token", "current_user"]:
            if key in st.session_state:
                del st.session_state[key]

        logger.info("User logged out")
        st.rerun()


def show_login_view():
    """Helper-Funktion für direkten View-Aufruf."""
    login_view = LoginView()
    return login_view.show()


def is_authenticated() -> bool:
    """Prüft ob User eingeloggt ist."""
    return "auth_token" in st.session_state and "current_user" in st.session_state


def get_current_user() -> Optional[dict]:
    """Gibt aktuell eingeloggten User zurück."""
    return st.session_state.get("current_user")


def require_authentication(view_func):
    """Decorator für Views die Authentifizierung erfordern."""

    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_view()
            return None
        return view_func(*args, **kwargs)

    return wrapper


def require_permission(permission: str):
    """Decorator für Views die bestimmte Berechtigung erfordern."""

    def decorator(view_func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                show_login_view()
                return None

            user = get_current_user()
            from warehouse.domain.enums.user_role import UserRole

            role = UserRole(user["role"])
            if not role.has_permission(permission):
                st.error("Sie haben keine Berechtigung für diese Aktion")
                logger.warning(
                    f"Permission denied for user {user['username']}: {permission}"
                )
                return None

            return view_func(*args, **kwargs)

        return wrapper

    return decorator
