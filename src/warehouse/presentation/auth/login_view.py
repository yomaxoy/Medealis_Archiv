# src/warehouse/presentation/auth/login_view.py

import streamlit as st
import logging
from typing import Optional

from warehouse.application.services.user_service import UserService
from warehouse.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from warehouse.infrastructure.security.session_manager import SessionManager
from warehouse.infrastructure.security.login_rate_limiter import get_login_rate_limiter
from warehouse.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    UserInactiveError,
    UserNotFoundError,
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
        Zeigt Login-Formular oder Passwortwechsel-Formular an.

        Returns:
            True wenn erfolgreich eingeloggt
        """
        # Erzwungener Passwortwechsel aktiv?
        if st.session_state.get("force_password_change"):
            return self._show_force_password_change()

        return self._show_login_form()

    def _show_login_form(self) -> bool:
        """Zeigt Login-Formular an."""
        st.markdown("### Anmeldung")
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

                # Rate-Limiting prüfen
                rate_limiter = get_login_rate_limiter()
                if rate_limiter.is_locked(username):
                    remaining = rate_limiter.get_remaining_lockout_seconds(username)
                    minutes = remaining // 60
                    seconds = remaining % 60
                    st.error(
                        f"Zu viele fehlgeschlagene Anmeldeversuche. "
                        f"Bitte warten Sie noch {minutes}:{seconds:02d} Minuten."
                    )
                    logger.warning(f"Login blocked by rate limiter for: {username}")
                    return False

                try:
                    # Authentifiziere User
                    user = self._user_service.authenticate(username, password)

                    # Erfolgreicher Login — Zähler zurücksetzen
                    rate_limiter.record_successful_login(username)

                    # Prüfe ob Passwortwechsel erzwungen wird
                    if user.must_change_password:
                        st.session_state.force_password_change = True
                        st.session_state.force_pw_user_id = user.user_id
                        st.session_state.force_pw_username = str(user.username)
                        st.warning(
                            "Ihr Passwort muss geändert werden. "
                            "Bitte wählen Sie ein neues Passwort."
                        )
                        st.rerun()
                        return False

                    # Erstelle Session
                    self._complete_login(user)
                    st.success(f"Willkommen, {user.full_name or user.username}!")
                    logger.info(f"User login successful: {username}")

                    # Audit-Trail: Login loggen
                    try:
                        from warehouse.application.services.audit_service import audit_service
                        audit_service.log_login(user=str(user.username))
                    except Exception:
                        pass  # Audit-Fehler darf Login nicht blockieren

                    st.rerun()
                    return True

                except InvalidCredentialsError:
                    locked = rate_limiter.record_failed_attempt(username)
                    if locked:
                        remaining = rate_limiter.get_remaining_lockout_seconds(username)
                        minutes = remaining // 60
                        st.error(
                            f"Zu viele fehlgeschlagene Anmeldeversuche. "
                            f"Konto für {minutes} Minuten gesperrt."
                        )
                    else:
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

    def _show_force_password_change(self) -> bool:
        """Zeigt Formular für erzwungenen Passwortwechsel."""
        username = st.session_state.get("force_pw_username", "")
        user_id = st.session_state.get("force_pw_user_id", "")

        st.markdown("### Passwort ändern")
        st.warning(
            f"**{username}**: Ihr Passwort muss vor der ersten Nutzung geändert werden."
        )
        st.markdown("---")

        with st.form("force_password_change_form"):
            new_password = st.text_input("Neues Passwort", type="password")
            confirm_password = st.text_input("Neues Passwort bestätigen", type="password")

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submit = st.form_submit_button(
                    "Passwort ändern", type="primary", use_container_width=True
                )

            if submit:
                if not new_password or not confirm_password:
                    st.error("Bitte beide Passwortfelder ausfüllen")
                    return False

                if new_password != confirm_password:
                    st.error("Die Passwörter stimmen nicht überein")
                    return False

                try:
                    self._user_service.force_change_password(user_id, new_password)

                    # Clear force-change state
                    for key in ["force_password_change", "force_pw_user_id", "force_pw_username"]:
                        if key in st.session_state:
                            del st.session_state[key]

                    st.success("Passwort erfolgreich geändert! Bitte melden Sie sich erneut an.")
                    logger.info(f"Forced password change completed for: {username}")

                    # Audit-Trail: Passwortwechsel loggen (NICHT das Passwort!)
                    try:
                        from warehouse.application.services.audit_service import audit_service
                        audit_service.log_user_password_changed(user=username)
                    except Exception:
                        pass
                    st.rerun()
                    return False

                except UserNotFoundError:
                    st.error("Benutzer nicht gefunden. Bitte melden Sie sich erneut an.")
                    self._clear_force_change_state()
                    return False

                except ValueError as e:
                    st.error(f"Passwort ungültig: {str(e)}")
                    return False

                except Exception as e:
                    st.error("Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.")
                    logger.error(f"Force password change error for {username}: {str(e)}")
                    return False

        # Abbrechen-Button außerhalb des Formulars
        if st.button("Zurück zur Anmeldung"):
            self._clear_force_change_state()
            st.rerun()

        return False

    def _complete_login(self, user) -> None:
        """Erstellt Session und speichert User in Session State."""
        token = self._session_manager.create_session(
            user_id=user.user_id,
            username=str(user.username),
            role=user.role.value,
        )

        st.session_state.auth_token = token
        st.session_state.current_user = {
            "user_id": user.user_id,
            "username": str(user.username),
            "email": str(user.email),
            "role": user.role.value,
            "full_name": user.full_name,
        }

    def _clear_force_change_state(self) -> None:
        """Entfernt Force-Password-Change State."""
        for key in ["force_password_change", "force_pw_user_id", "force_pw_username"]:
            if key in st.session_state:
                del st.session_state[key]

    def logout(self):
        """Loggt den aktuellen User aus."""
        # Audit-Trail: Logout loggen (vor Session-Clear!)
        username = st.session_state.get("current_user", {}).get("username", "?")
        try:
            from warehouse.application.services.audit_service import audit_service
            audit_service.log_logout(user=username)
        except Exception:
            pass  # Audit-Fehler darf Logout nicht blockieren

        if "auth_token" in st.session_state:
            self._session_manager.invalidate_session(st.session_state.auth_token)

        # Clear session state
        for key in ["auth_token", "current_user"]:
            if key in st.session_state:
                del st.session_state[key]

        self._clear_force_change_state()

        logger.info(f"User logged out: {username}")
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
