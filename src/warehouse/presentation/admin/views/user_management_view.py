"""
User Management View - Admin Presentation Layer
Benutzerverwaltung: Anlegen, Bearbeiten, Deaktivieren, Passwort zurücksetzen.
"""

import streamlit as st
import logging

from warehouse.application.services.user_service import UserService
from warehouse.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from warehouse.domain.enums.user_role import UserRole

logger = logging.getLogger(__name__)


def _get_user_service() -> UserService:
    """Gibt den UserService zurück (lazy init)."""
    if "user_service" not in st.session_state:
        st.session_state.user_service = UserService(UserRepositoryImpl())
    return st.session_state.user_service


def show_user_management_view():
    """Haupteinstieg: Benutzerverwaltung."""
    st.header("Benutzerverwaltung")

    # Nur Admins dürfen User verwalten
    current_user = st.session_state.get("current_user", {})
    if current_user.get("role") != "admin":
        st.error("Nur Administratoren haben Zugriff auf die Benutzerverwaltung.")
        return

    user_service = _get_user_service()

    tab_list, tab_new = st.tabs(["Benutzer", "Neuer Benutzer"])

    with tab_list:
        _show_user_list(user_service, current_user)

    with tab_new:
        _show_create_user_form(user_service, current_user)


def _show_user_list(user_service: UserService, current_user: dict):
    """Zeigt die Liste aller Benutzer."""
    try:
        users = user_service.get_all_users(include_inactive=True)
    except Exception as e:
        st.error(f"Fehler beim Laden der Benutzer: {e}")
        return

    if not users:
        st.info("Keine Benutzer vorhanden.")
        return

    # Statistik-Zeile
    active_count = sum(1 for u in users if u.is_active)
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamt", len(users))
    col2.metric("Aktiv", active_count)
    col3.metric("Inaktiv", len(users) - active_count)

    st.divider()

    # Benutzer-Tabelle
    for user in users:
        _render_user_row(user, user_service, current_user)


def _render_user_row(user, user_service: UserService, current_user: dict):
    """Rendert eine Benutzer-Zeile mit Aktionen."""
    user_id = user.user_id
    username = str(user.username)
    is_self = current_user.get("user_id") == user_id

    # Status-Indikator
    status = "Aktiv" if user.is_active else "Inaktiv"
    status_color = "green" if user.is_active else "red"

    with st.container(border=True):
        col_info, col_role, col_status, col_actions = st.columns([3, 2, 1, 3])

        with col_info:
            name_display = user.full_name or username
            st.markdown(f"**{name_display}**")
            st.caption(f"@{username} | {str(user.email)}")
            if user.last_login:
                st.caption(f"Letzter Login: {user.last_login.strftime('%d.%m.%Y %H:%M')}")

        with col_role:
            st.markdown(f"**{user.role.display_name}**")
            if user.must_change_password:
                st.caption("Passwortwechsel ausstehend")

        with col_status:
            st.markdown(f":{status_color}[{status}]")

        with col_actions:
            action_cols = st.columns(3)

            # Rolle ändern
            with action_cols[0]:
                if st.button("Rolle", key=f"role_{user_id}", use_container_width=True):
                    st.session_state[f"edit_role_{user_id}"] = True

            # Passwort zurücksetzen
            with action_cols[1]:
                if st.button("Passwort", key=f"pw_{user_id}", use_container_width=True):
                    st.session_state[f"reset_pw_{user_id}"] = True

            # Aktivieren/Deaktivieren (nicht für sich selbst)
            with action_cols[2]:
                if is_self:
                    st.button(
                        "Eigener Account",
                        key=f"toggle_{user_id}",
                        disabled=True,
                        use_container_width=True,
                    )
                elif user.is_active:
                    if st.button(
                        "Deaktivieren",
                        key=f"toggle_{user_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"confirm_deactivate_{user_id}"] = True
                else:
                    if st.button(
                        "Aktivieren",
                        key=f"toggle_{user_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        _activate_user(user_service, user_id, current_user)

        # Inline: Rolle ändern
        if st.session_state.get(f"edit_role_{user_id}"):
            _show_role_edit(user, user_service, current_user)

        # Inline: Passwort zurücksetzen
        if st.session_state.get(f"reset_pw_{user_id}"):
            _show_password_reset(user, user_service, current_user)

        # Inline: Deaktivierung bestätigen
        if st.session_state.get(f"confirm_deactivate_{user_id}"):
            _show_deactivate_confirm(user, user_service, current_user)


def _show_role_edit(user, user_service: UserService, current_user: dict):
    """Inline-Formular zur Rollenänderung."""
    user_id = user.user_id
    roles = [r for r in UserRole]
    current_index = roles.index(user.role)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_role = st.selectbox(
            "Neue Rolle",
            options=roles,
            index=current_index,
            format_func=lambda r: r.display_name,
            key=f"select_role_{user_id}",
        )
    with col2:
        st.write("")  # Spacing
        if st.button("Speichern", key=f"save_role_{user_id}", type="primary"):
            try:
                user_service.update_user_role(user_id, new_role, current_user["user_id"])
                st.session_state[f"edit_role_{user_id}"] = False
                st.success(f"Rolle geändert: {new_role.display_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler: {e}")
    with col3:
        st.write("")
        if st.button("Abbrechen", key=f"cancel_role_{user_id}"):
            st.session_state[f"edit_role_{user_id}"] = False
            st.rerun()


def _show_password_reset(user, user_service: UserService, current_user: dict):
    """Inline-Formular zum Passwort-Reset."""
    user_id = user.user_id

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_pw = st.text_input(
            "Neues Passwort",
            type="password",
            key=f"new_pw_{user_id}",
            placeholder="Min. 8 Zeichen, Gross/Klein, Zahl",
        )
    with col2:
        st.write("")
        if st.button("Zurücksetzen", key=f"save_pw_{user_id}", type="primary"):
            if not new_pw:
                st.error("Bitte Passwort eingeben")
            else:
                try:
                    user_service.reset_password(
                        user_id, new_pw, current_user["user_id"]
                    )
                    st.session_state[f"reset_pw_{user_id}"] = False
                    st.success(
                        f"Passwort zurückgesetzt. "
                        f"Benutzer muss beim nächsten Login ein neues Passwort wählen."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")
    with col3:
        st.write("")
        if st.button("Abbrechen", key=f"cancel_pw_{user_id}"):
            st.session_state[f"reset_pw_{user_id}"] = False
            st.rerun()


def _show_deactivate_confirm(user, user_service: UserService, current_user: dict):
    """Bestätigung für Deaktivierung."""
    user_id = user.user_id
    username = str(user.username)

    st.warning(f"Benutzer **{username}** wirklich deaktivieren?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ja, deaktivieren", key=f"do_deactivate_{user_id}", type="primary"):
            try:
                user_service.deactivate_user(user_id, current_user["user_id"])
                st.session_state[f"confirm_deactivate_{user_id}"] = False
                st.success(f"Benutzer {username} deaktiviert.")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler: {e}")
    with col2:
        if st.button("Abbrechen", key=f"cancel_deactivate_{user_id}"):
            st.session_state[f"confirm_deactivate_{user_id}"] = False
            st.rerun()


def _activate_user(user_service: UserService, user_id: str, current_user: dict):
    """Aktiviert einen Benutzer."""
    try:
        user_service.activate_user(user_id, current_user["user_id"])
        st.success("Benutzer aktiviert.")
        st.rerun()
    except Exception as e:
        st.error(f"Fehler: {e}")


def _show_create_user_form(user_service: UserService, current_user: dict):
    """Formular zum Erstellen eines neuen Benutzers."""
    st.subheader("Neuen Benutzer anlegen")

    with st.form("create_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Vollständiger Name", placeholder="Max Mustermann")
            username = st.text_input(
                "Benutzername",
                placeholder="max.mustermann",
                help="Erlaubt: Buchstaben, Zahlen, Punkte, Unterstriche, Bindestriche",
            )
            email = st.text_input(
                "E-Mail",
                placeholder="max@medealis.local",
            )

        with col2:
            role = st.selectbox(
                "Rolle",
                options=list(UserRole),
                index=2,  # Default: Operator
                format_func=lambda r: r.display_name,
            )
            password = st.text_input(
                "Initiales Passwort",
                type="password",
                help="Min. 8 Zeichen, Gross-/Kleinbuchstaben, Zahl",
            )
            password_confirm = st.text_input(
                "Passwort bestätigen",
                type="password",
            )

        st.divider()

        # Rollen-Info
        st.caption(
            "**Rollen:** Admin = Vollzugriff | "
            "Manager = Lieferungen, Bestellungen, Lieferanten | "
            "Sachbearbeiter = Wareneingangskontrolle | "
            "Betrachter = Nur Lesen"
        )

        submitted = st.form_submit_button("Benutzer anlegen", type="primary")

        if submitted:
            # Validierung
            if not username or not email or not password:
                st.error("Bitte alle Pflichtfelder ausfüllen.")
                return

            if password != password_confirm:
                st.error("Die Passwörter stimmen nicht überein.")
                return

            try:
                user_service.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    full_name=full_name or None,
                    created_by=current_user.get("user_id"),
                )
                st.success(f"Benutzer **{username}** erfolgreich angelegt!")
                logger.info(f"User created by admin: {username} ({role.display_name})")
            except Exception as e:
                st.error(f"Fehler beim Anlegen: {e}")
                logger.error(f"User creation failed: {e}")
