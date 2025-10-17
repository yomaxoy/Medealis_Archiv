"""
Storage Warning Dialog Component

Zeigt Warnungen an wenn Server-Speicherung nicht verfügbar ist.
Listet alle verfügbaren Speicher-Alternativen mit Pfaden.
"""

import streamlit as st
from typing import Dict, Any, Optional


def show_storage_warning_dialog(warning_data: Dict[str, Any]) -> bool:
    """
    Zeigt Storage-Warnung Dialog an.

    Args:
        warning_data: Dictionary mit Warnung-Daten von StorageAvailabilityChecker

    Returns:
        True wenn Benutzer fortfahren möchte, False zum Abbrechen
    """
    if not warning_data:
        return True  # Keine Warnung, weiter

    # Dialog-Container
    with st.container():
        # Header mit Icon
        st.warning(f"### {warning_data['title']}")

        # Haupt-Message
        st.markdown(warning_data['message'])

        st.markdown("---")

        # Speicher-Optionen Tabelle
        st.markdown("#### 📊 Verfügbare Speicher-Optionen:")

        options = warning_data['options']

        for option in options:
            # Status-Symbol
            status_icon = "✅" if option.available else "❌"
            priority_label = {
                1: "🥇 Primär",
                2: "🥈 Fallback 1",
                3: "🥉 Fallback 2"
            }.get(option.priority, "")

            # Expander für jede Option
            with st.expander(
                f"{status_icon} {option.name} - {priority_label}",
                expanded=(option.priority <= 2)
            ):
                # Status
                st.markdown(f"**Status:** {option.status_message}")

                # Pfad
                st.markdown(f"**Speicherort:**")
                st.code(option.path, language=None)

                # Empfehlung
                if option.recommendation:
                    if option.available:
                        st.info(f"💡 {option.recommendation}")
                    else:
                        st.error(f"⚠️ {option.recommendation}")

        st.markdown("---")

        # Empfohlene Aktion
        st.markdown("#### 🎯 Empfohlene Aktion:")

        if warning_data['fallback_available']:
            st.success(warning_data['recommended_action'])
        else:
            st.error(warning_data['recommended_action'])

        st.markdown("---")

        # Aktions-Buttons
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("**Was möchten Sie tun?**")

        with col2:
            if st.button("🔄 Status neu prüfen", use_container_width=True):
                st.rerun()

        with col3:
            continue_anyway = st.button(
                "✅ Fortfahren" if warning_data['fallback_available'] else "❌ Abbrechen",
                type="primary" if warning_data['fallback_available'] else "secondary",
                use_container_width=True
            )

        return continue_anyway


def show_compact_storage_warning(warning_data: Dict[str, Any]) -> Optional[str]:
    """
    Zeigt kompakte Storage-Warnung als st.warning an.

    Args:
        warning_data: Dictionary mit Warnung-Daten

    Returns:
        Gewählte Aktion: "continue", "refresh", "abort" oder None
    """
    if not warning_data:
        return "continue"  # Keine Warnung, weiter

    # Kompakte Warnung
    options = warning_data['options']
    available_options = [opt for opt in options if opt.available]

    if not available_options:
        st.error(
            "❌ **KEINE SPEICHER-OPTION VERFÜGBAR!**\n\n"
            "Bitte kontaktieren Sie sofort den IT-Administrator.\n\n"
            "Dokumente können nicht gespeichert werden!"
        )
        return "abort"

    # Server nicht verfügbar, aber Fallback vorhanden
    primary_fallback = available_options[0]

    warning_msg = (
        f"⚠️ **Server-Speicherung nicht verfügbar**\n\n"
        f"Dokumente werden stattdessen gespeichert auf:\n"
        f"**{primary_fallback.name}**\n\n"
        f"📁 `{primary_fallback.path}`"
    )

    with st.expander("⚠️ Server nicht verfügbar - Details anzeigen", expanded=False):
        st.warning(warning_msg)

        st.markdown("#### Alle Speicher-Optionen:")
        for opt in options:
            status = "✅" if opt.available else "❌"
            st.markdown(f"- {status} **{opt.name}**: {opt.status_message}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Status neu prüfen", key="refresh_compact"):
                return "refresh"
        with col2:
            if st.button("✅ Fortfahren mit Fallback", key="continue_compact", type="primary"):
                return "continue"

    return None


def show_storage_status_indicator(show_details: bool = False):
    """
    Zeigt permanenten Storage-Status-Indikator in Sidebar oder Footer.

    Args:
        show_details: Ob Details angezeigt werden sollen
    """
    from warehouse.application.services.document_storage.storage_availability_checker import (
        storage_availability_checker
    )

    status = storage_availability_checker.check_all_storage_options()

    # Status-Icon und Text
    if status['server_unavailable_warning']:
        icon = "⚠️"
        color = "orange"
        text = "Server nicht verfügbar"
    elif status['primary_option']:
        icon = "✅"
        color = "green"
        text = f"{status['primary_option'].name}"
    else:
        icon = "❌"
        color = "red"
        text = "Keine Speicherung möglich"

    # Anzeige
    if show_details:
        with st.expander(f"{icon} Speicher-Status: {text}", expanded=False):
            st.markdown(f"**Aktueller Modus:** {status['storage_mode']}")

            for opt in status['all_options']:
                status_icon = "✅" if opt.available else "❌"
                st.markdown(f"- {status_icon} {opt.name}: {opt.status_message}")
    else:
        # Nur Status-Badge
        st.markdown(
            f'<div style="padding: 0.5rem; background-color: {color}; '
            f'border-radius: 0.25rem; text-align: center;">'
            f'{icon} {text}'
            f'</div>',
            unsafe_allow_html=True
        )


def check_and_show_storage_warning(
    batch_number: str = None,
    delivery_number: str = None,
    article_number: str = None,
    supplier_name: str = None,
    compact: bool = True
) -> bool:
    """
    Prüft Storage-Verfügbarkeit und zeigt Warnung wenn nötig.

    Args:
        batch_number: Optional - für konkrete Pfad-Beispiele
        delivery_number: Optional
        article_number: Optional
        supplier_name: Optional
        compact: Wenn True, zeigt kompakte Warnung, sonst vollen Dialog

    Returns:
        True wenn fortgefahren werden kann, False zum Abbrechen
    """
    from warehouse.application.services.document_storage.storage_availability_checker import (
        storage_availability_checker
    )

    # Hole Warnung
    warning_data = storage_availability_checker.get_server_unavailable_warning(
        batch_number=batch_number,
        delivery_number=delivery_number,
        article_number=article_number,
        supplier_name=supplier_name
    )

    if not warning_data:
        return True  # Keine Warnung, alles OK

    # Zeige Warnung
    if compact:
        action = show_compact_storage_warning(warning_data)
        if action == "refresh":
            st.rerun()
        elif action == "abort":
            return False
        elif action == "continue":
            return True
        # None = Noch keine Aktion gewählt
        return True
    else:
        return show_storage_warning_dialog(warning_data)
