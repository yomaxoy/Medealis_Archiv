"""
Header Components
Reusable header components for popup dialogs.
"""

import streamlit as st
from typing import Dict, Any, Optional


def render_article_header(
    article_number: str,
    batch_number: str,
    delivery_number: Optional[str] = None,
    quantity: Optional[int] = None,
    status: Optional[str] = None,
    show_info_box: bool = False,
    info_text: Optional[str] = None,
    additional_info: Optional[Dict[str, str]] = None
) -> None:
    """
    Rendert einen standardisierten Artikel-Header für Popups.

    Args:
        article_number: Artikelnummer
        batch_number: Chargennummer
        delivery_number: Lieferscheinnummer (optional)
        quantity: Menge (optional)
        status: Status (optional)
        show_info_box: Zeigt Info-Box unter dem Header
        info_text: Text für die Info-Box
        additional_info: Dict mit zusätzlichen Infos {label: wert}

    Beispiel:
        ```python
        render_article_header(
            article_number="MG0001",
            batch_number="BATCH-123",
            delivery_number="LS-2024-001",
            quantity=100,
            status="In Bearbeitung",
            show_info_box=True,
            info_text="Bitte prüfen Sie alle Felder sorgfältig",
            additional_info={"Lieferant": "ACME Corp"}
        )
        ```
    """
    # Kompakte Header-Zeile: Alle Informationen in einer Zeile
    info_parts = [f"**Artikelnummer:** {article_number}", f"**Chargennummer:** {batch_number}"]

    if delivery_number:
        info_parts.append(f"**Lieferscheinnummer:** {delivery_number}")

    if quantity is not None:
        info_parts.append(f"**Menge:** {quantity}")

    st.markdown(" | ".join(info_parts))

    # Status-Badge
    if status:
        render_status_badge(status)

    # Zusätzliche Informationen als Key-Value
    if additional_info:
        cols = st.columns(len(additional_info))
        for i, (label, value) in enumerate(additional_info.items()):
            with cols[i]:
                st.caption(f"**{label}:** {value}")

    # Info-Box (optional)
    if show_info_box and info_text:
        st.info(f"💡 {info_text}")

    # Divider nach Header
    st.divider()


def render_status_badge(status: str, use_html: bool = True) -> None:
    """
    Rendert ein Status-Badge mit entsprechender Farbe.

    Args:
        status: Status-Text
        use_html: Nutzt HTML für farbiges Badge (default: True)

    Unterstützte Status-Werte:
        - PENDING, IN_PROGRESS, COMPLETED, FAILED
        - Daten geprüft, Dokumente geprüft, Vermessen, Sichtgeprüft
        - Custom Status werden mit grauer Farbe angezeigt
    """
    # Status-Mapping: (icon, color, background_color)
    status_map = {
        # Workflow-Status
        'PENDING': ('⏳', 'white', '#ff9800'),
        'IN_PROGRESS': ('🔄', 'white', '#2196f3'),
        'COMPLETED': ('✅', 'white', '#4caf50'),
        'FAILED': ('❌', 'white', '#f44336'),

        # Prüfungs-Status
        'Daten geprüft': ('📋', 'white', '#2196f3'),
        'Dokumente geprüft': ('📄', 'white', '#2196f3'),
        'Vermessen': ('📏', 'white', '#2196f3'),
        'Sichtgeprüft': ('👁️', 'white', '#2196f3'),
        'Ausgeschleust': ('❌', 'white', '#f44336'),

        # Zusätzliche Status
        'Wartet': ('⏸️', 'white', '#ff9800'),
        'Gesperrt': ('🔒', 'white', '#f44336'),
        'Freigegeben': ('✅', 'white', '#4caf50'),
    }

    icon, text_color, bg_color = status_map.get(status, ('ℹ️', 'white', '#9e9e9e'))

    if use_html:
        # HTML-Badge mit abgerundeten Ecken
        st.markdown(
            f'<span style="'
            f'background-color: {bg_color}; '
            f'color: {text_color}; '
            f'padding: 4px 12px; '
            f'border-radius: 12px; '
            f'font-size: 0.85em; '
            f'font-weight: 500; '
            f'display: inline-block; '
            f'margin: 4px 0;'
            f'">{icon} {status}</span>',
            unsafe_allow_html=True
        )
    else:
        # Fallback: Streamlit native (ohne Farbe)
        st.caption(f"{icon} **{status}**")


def render_compact_info_row(info_dict: Dict[str, str], columns: int = 3) -> None:
    """
    Rendert eine kompakte Info-Zeile mit mehreren Key-Value-Paaren.

    Args:
        info_dict: Dict mit Label: Wert Paaren
        columns: Anzahl Spalten (default: 3)

    Beispiel:
        ```python
        render_compact_info_row({
            "Lieferant": "ACME Corp",
            "Bestellung": "PO-123",
            "Datum": "2024-01-15"
        })
        ```
    """
    if not info_dict:
        return

    cols = st.columns(columns)

    for i, (label, value) in enumerate(info_dict.items()):
        col_idx = i % columns
        with cols[col_idx]:
            st.caption(f"**{label}:** {value}")


def render_progress_indicator(
    current_step: int,
    total_steps: int,
    step_labels: Optional[list] = None
) -> None:
    """
    Rendert einen Fortschritts-Indikator für mehrstufige Popups.

    Args:
        current_step: Aktueller Schritt (1-basiert)
        total_steps: Gesamtzahl Schritte
        step_labels: Optional - Labels für jeden Schritt

    Beispiel:
        ```python
        render_progress_indicator(
            current_step=2,
            total_steps=3,
            step_labels=["Daten", "Dokumente", "Abschluss"]
        )
        ```
    """
    # Progress Bar
    progress = current_step / total_steps
    st.progress(progress)

    # Step Labels
    if step_labels:
        cols = st.columns(total_steps)
        for i, label in enumerate(step_labels):
            with cols[i]:
                step_num = i + 1
                if step_num < current_step:
                    st.caption(f"✅ {label}")
                elif step_num == current_step:
                    st.caption(f"🔵 **{label}**")
                else:
                    st.caption(f"⚪ {label}")
    else:
        st.caption(f"Schritt {current_step} von {total_steps}")

    st.divider()


def render_warning_box(message: str, icon: str = "⚠️") -> None:
    """
    Rendert eine auffällige Warn-Box.

    Args:
        message: Warnungs-Text
        icon: Icon (default: ⚠️)
    """
    st.warning(f"{icon} **{message}**")


def render_success_box(message: str, icon: str = "✅") -> None:
    """
    Rendert eine Erfolgs-Box.

    Args:
        message: Erfolgs-Text
        icon: Icon (default: ✅)
    """
    st.success(f"{icon} **{message}**")


def render_error_box(message: str, icon: str = "❌") -> None:
    """
    Rendert eine Fehler-Box.

    Args:
        message: Fehler-Text
        icon: Icon (default: ❌)
    """
    st.error(f"{icon} **{message}**")


def render_info_box(message: str, icon: str = "💡") -> None:
    """
    Rendert eine Info-Box.

    Args:
        message: Info-Text
        icon: Icon (default: 💡)
    """
    st.info(f"{icon} {message}")
