# src/warehouse/presentation/auth/user_management_view.py

import streamlit as st
import logging
from typing import Optional

from warehouse.application.services.user_service import UserService
from warehouse.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from warehouse.domain.enums.user_role import UserRole
from warehouse.domain.exceptions.user_exceptions import UserAlreadyExistsError
from warehouse.presentation.auth.login_view import (
    require_authentication,
    require_permission,
    get_current_user,
)

logger = logging.getLogger(__name__)


class UserManagementView:
    """User-Management-View für Admins und Manager."""

    def __init__(self, user_service: Optional[UserService] = None):
        self._user_service = user_service or UserService(UserRepositoryImpl())

    @require_permission("user.read")
    def show(self):
        """Zeigt User-Management-Oberfläche."""
        st.title("👥 Benutzerverwaltung")
        st.markdown("---")

        # Tabs
        tab1, tab2 = st.tabs(["📋 Benutzer-Liste", "➕ Neuer Benutzer"])

        with tab1:
            self._show_user_list()

        with tab2:
            self._show_create_user_form()

    def _show_user_list(self):
        """Zeigt Liste aller Benutzer."""
        try:
            users = self._user_service.get_all_users(include_inactive=True)

            if not users:
                st.info("Noch keine Benutzer vorhanden")
                return

            # Filter-Optionen
            col1, col2 = st.columns([2, 1])
            with col1:
                show_inactive = st.checkbox("Inaktive Benutzer anzeigen", value=True)
            with col2:
                role_filter = st.selectbox(
                    "Rolle filtern",
                    options=["Alle"] + [role.display_name for role in UserRole],
                )

            # Filtere Users
            filtered_users = users
            if not show_inactive:
                filtered_users = [u for u in filtered_users if u.is_active]

            if role_filter != "Alle":
                role_value = next(r for r in UserRole if r.display_name == role_filter)
                filtered_users = [u for u in filtered_users if u.role == role_value]

            st.markdown(f"**{len(filtered_users)} Benutzer**")

            # Tabelle
            for user in filtered_users:
                status = "✅" if user.is_active else "❌"
                name = user.full_name or user.username
                with st.expander(f"{status} {name} ({user.role.display_name})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Benutzername:** {user.username}")
                        st.write(f"**E-Mail:** {user.email}")
                        st.write(f"**Rolle:** {user.role.display_name}")
                        st.write(
                            f"**Status:** {'Aktiv' if user.is_active else 'Inaktiv'}"
                        )

                    with col2:
                        if user.last_login:
                            login_str = user.last_login.strftime("%d.%m.%Y %H:%M")
                            st.write(f"**Letzter Login:** {login_str}")
                        st.write(
                            f"**Erstellt:** {user.created_at.strftime('%d.%m.%Y')}"
                            if user.created_at
                            else ""
                        )

                    # Aktionen
                    self._show_user_actions(user)

        except Exception as e:
            st.error(f"Fehler beim Laden der Benutzer: {str(e)}")
            logger.error(f"Error loading users: {str(e)}")

    def _show_user_actions(self, user):
        """Zeigt Aktions-Buttons für einen User."""
        current_user = get_current_user()
        can_modify = UserRole(current_user["role"]).has_permission("user.update")

        if not can_modify:
            return

        col1, col2, col3 = st.columns(3)

        with col1:
            # Aktivieren/Deaktivieren
            if user.is_active:
                if st.button("Deaktivieren", key=f"deactivate_{user.user_id}"):
                    try:
                        self._user_service.deactivate_user(
                            user.user_id, current_user["user_id"]
                        )
                        st.success("Benutzer deaktiviert")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {str(e)}")
            else:
                if st.button("Aktivieren", key=f"activate_{user.user_id}"):
                    try:
                        self._user_service.activate_user(
                            user.user_id, current_user["user_id"]
                        )
                        st.success("Benutzer aktiviert")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {str(e)}")

        with col2:
            # Rolle ändern
            if st.button("Rolle ändern", key=f"change_role_{user.user_id}"):
                st.session_state[f"edit_role_{user.user_id}"] = True

        if st.session_state.get(f"edit_role_{user.user_id}"):
            new_role = st.selectbox(
                "Neue Rolle",
                options=[role for role in UserRole],
                format_func=lambda r: r.display_name,
                index=list(UserRole).index(user.role),
                key=f"role_select_{user.user_id}",
            )

            if st.button("Speichern", key=f"save_role_{user.user_id}"):
                try:
                    self._user_service.update_user_role(
                        user.user_id, new_role, current_user["user_id"]
                    )
                    st.success("Rolle aktualisiert")
                    del st.session_state[f"edit_role_{user.user_id}"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {str(e)}")

    @require_permission("user.create")
    def _show_create_user_form(self):
        """Zeigt Formular zum Erstellen eines neuen Users."""
        with st.form("create_user_form"):
            st.subheader("Neuen Benutzer anlegen")

            username = st.text_input(
                "Benutzername *", placeholder="z.B. max.mustermann"
            )
            email = st.text_input("E-Mail *", placeholder="z.B. max@example.com")
            full_name = st.text_input(
                "Vollständiger Name", placeholder="Max Mustermann"
            )

            role = st.selectbox(
                "Rolle *",
                options=[r for r in UserRole],
                format_func=lambda r: r.display_name,
            )

            password = st.text_input("Passwort *", type="password")
            password_confirm = st.text_input("Passwort bestätigen *", type="password")

            st.markdown("**Passwort-Anforderungen:**")
            st.markdown(
                "- Mindestens 8 Zeichen\n"
                "- Groß- und Kleinbuchstaben\n"
                "- Mindestens eine Zahl"
            )

            submit = st.form_submit_button("Benutzer erstellen", type="primary")

            if submit:
                # Validierung
                if not username or not email or not password:
                    st.error("Bitte alle Pflichtfelder ausfüllen")
                    return

                if password != password_confirm:
                    st.error("Passwörter stimmen nicht überein")
                    return

                try:
                    current_user = get_current_user()
                    user = self._user_service.create_user(
                        username=username,
                        email=email,
                        password=password,
                        role=role,
                        full_name=full_name if full_name else None,
                        created_by=current_user["user_id"],
                    )

                    st.success(
                        f"Benutzer '{user.username}' erfolgreich erstellt! "
                        f"(Rolle: {role.display_name})"
                    )
                    logger.info(
                        f"User created: {username} by {current_user['username']}"
                    )

                except UserAlreadyExistsError as e:
                    st.error(str(e))

                except ValueError as e:
                    st.error(f"Validierungsfehler: {str(e)}")

                except Exception as e:
                    st.error(f"Fehler beim Erstellen des Benutzers: {str(e)}")
                    logger.error(f"Error creating user: {str(e)}")


@require_authentication
def show_user_management_view():
    """Helper-Funktion für direkten View-Aufruf."""
    view = UserManagementView()
    view.show()
