"""
Audit Log View - Admin Presentation Layer
Anzeige und Durchsuchen des Audit-Trails.
"""

import streamlit as st
import logging
from datetime import datetime, timedelta

from warehouse.application.services.audit_service import audit_service

logger = logging.getLogger(__name__)


def show_audit_log_view():
    """Haupteinstieg: Audit-Log-Ansicht."""
    st.header("Aktivitätsprotokoll")

    # Nur Admins dürfen Logs einsehen
    current_user = st.session_state.get("current_user", {})
    if current_user.get("role") != "admin":
        st.error("Nur Administratoren haben Zugriff auf das Aktivitätsprotokoll.")
        return

    # Filter-Leiste
    col_search, col_filter, col_days = st.columns([3, 2, 1])

    with col_search:
        search_term = st.text_input(
            "Suche",
            placeholder="Benutzername, Aktion, Artikel...",
            key="audit_search",
        )

    with col_filter:
        filter_options = [
            "Alle",
            "Login/Logout",
            "Benutzerverwaltung",
            "Lieferschein",
            "Workflow",
            "Bestellungen",
        ]
        action_filter = st.selectbox("Kategorie", filter_options, key="audit_filter")

    with col_days:
        days = st.number_input("Tage", min_value=1, max_value=365, value=30, key="audit_days")

    st.divider()

    # Logs laden
    try:
        if search_term:
            logs = audit_service.search_logs(search_term, limit=500)
            st.caption(f"Suchergebnisse für \"{search_term}\"")
        else:
            logs = audit_service.get_recent_logs(limit=500)

        # Nach Zeitraum filtern
        cutoff = datetime.now() - timedelta(days=days)
        logs = [log for log in logs if log.timestamp and log.timestamp >= cutoff]

        # Nach Kategorie filtern
        logs = _filter_by_category(logs, action_filter)

        if not logs:
            st.info("Keine Einträge gefunden.")
            return

        st.caption(f"{len(logs)} Einträge")

        # Log-Einträge anzeigen
        for log in logs:
            _render_log_entry(log)

    except Exception as e:
        logger.error(f"Fehler beim Laden der Audit-Logs: {e}")
        st.error(f"Fehler beim Laden: {e}")


def _filter_by_category(logs, category: str):
    """Filtert Logs nach Aktions-Kategorie."""
    if category == "Alle":
        return logs

    category_actions = {
        "Login/Logout": [
            "Benutzer angemeldet", "Benutzer abgemeldet",
        ],
        "Benutzerverwaltung": [
            "Benutzer erstellt", "Benutzerrolle geändert",
            "Passwort zurückgesetzt", "Benutzer aktiviert",
            "Benutzer deaktiviert", "Passwort geändert",
        ],
        "Lieferschein": [
            "Lieferschein gescannt", "Lieferschein bestätigt",
            "Lieferschein gelöscht",
        ],
        "Workflow": [
            "Daten bestätigt", "Dokumente geprüft", "Vermessen",
            "Sichtkontrolle durchgeführt", "Dokumente zusammengeführt",
            "Artikel abgeschlossen", "Artikel ausgeschossen",
            "ItemInfo erstellt", "ItemInfo aktualisiert",
        ],
        "Bestellungen": [
            "Bestellung erstellt", "Bestellung aktualisiert",
            "Bestellung gelöscht",
        ],
    }

    allowed = category_actions.get(category, [])
    if not allowed:
        return logs

    return [log for log in logs if log.action in allowed]


def _render_log_entry(log):
    """Rendert einen einzelnen Log-Eintrag."""
    timestamp = log.timestamp.strftime("%d.%m.%Y %H:%M:%S") if log.timestamp else "?"
    action = log.action or "?"
    user = log.user or "?"
    entity = f"{log.entity_type}: {log.entity_id}" if log.entity_type else ""

    # Farbcodierung nach Aktionstyp
    icon = _get_action_icon(action)

    col_time, col_action, col_detail = st.columns([2, 3, 4])

    with col_time:
        st.caption(timestamp)
        st.caption(f"von **{user}**")

    with col_action:
        st.markdown(f"{icon} **{action}**")

    with col_detail:
        if entity:
            st.caption(entity)
        if log.notes:
            st.caption(f"_{log.notes}_")


def _get_action_icon(action: str) -> str:
    """Gibt ein passendes Icon für die Aktion zurück."""
    icon_map = {
        "Benutzer angemeldet": "🔓",
        "Benutzer abgemeldet": "🔒",
        "Benutzer erstellt": "👤",
        "Benutzerrolle geändert": "🔄",
        "Passwort zurückgesetzt": "🔑",
        "Passwort geändert": "🔑",
        "Benutzer aktiviert": "✅",
        "Benutzer deaktiviert": "⛔",
        "Lieferschein gescannt": "📄",
        "Lieferschein bestätigt": "✅",
        "Lieferschein gelöscht": "🗑️",
        "Daten bestätigt": "📋",
        "Dokumente geprüft": "📑",
        "Vermessen": "📏",
        "Sichtkontrolle durchgeführt": "👁️",
        "Dokumente zusammengeführt": "📎",
        "Artikel abgeschlossen": "✅",
        "Artikel ausgeschossen": "❌",
        "Bestellung erstellt": "🛒",
    }
    return icon_map.get(action, "📝")
