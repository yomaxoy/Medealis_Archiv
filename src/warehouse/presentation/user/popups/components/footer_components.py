"""
Footer Components
Reusable button layouts for popup footers.
"""

import streamlit as st
from typing import List, Optional


def render_action_buttons(
    primary_label: str = "✅ Bestätigen",
    secondary_actions: Optional[List[str]] = None,
    primary_type: str = "primary",
    primary_disabled: bool = False
) -> Optional[str]:
    """
    Rendert eine standardisierte Button-Leiste.

    Args:
        primary_label: Label für den Haupt-Button
        secondary_actions: Liste von Sekundär-Aktionen (z.B. ["Abbrechen", "Zurück"])
        primary_type: Streamlit Button-Typ (default: "primary")
        primary_disabled: Deaktiviert Primary-Button

    Returns:
        'primary' wenn Hauptbutton geklickt, sonst Name der Sekundär-Aktion (lowercase)

    Beispiel:
        ```python
        action = render_action_buttons(
            primary_label="💾 Speichern",
            secondary_actions=["❌ Abbrechen", "🔙 Zurück"]
        )

        if action == 'primary':
            # Speichern-Logik
            pass
        elif action == 'abbrechen':
            # Abbrechen-Logik
            pass
        elif action == 'zurück':
            # Zurück-Logik
            pass
        ```
    """
    if secondary_actions is None:
        secondary_actions = ["❌ Abbrechen"]

    st.divider()

    num_buttons = 1 + len(secondary_actions)
    cols = st.columns(num_buttons)

    # Primary Button (links)
    with cols[0]:
        if st.button(
            primary_label,
            type=primary_type,
            use_container_width=True,
            disabled=primary_disabled,
            key=f"btn_primary_{_sanitize_key(primary_label)}"
        ):
            return 'primary'

    # Secondary Buttons
    for i, action in enumerate(secondary_actions):
        with cols[i + 1]:
            if st.button(
                action,
                use_container_width=True,
                key=f"btn_secondary_{_sanitize_key(action)}"
            ):
                # Extract action name (remove emoji and lowercase)
                action_name = _extract_action_name(action)
                return action_name

    return None


def render_two_button_footer(
    confirm_label: str = "✅ Bestätigen",
    cancel_label: str = "❌ Abbrechen",
    confirm_disabled: bool = False
) -> Optional[str]:
    """
    Rendert zwei Buttons: Bestätigen + Abbrechen.

    Args:
        confirm_label: Label für Bestätigen-Button
        cancel_label: Label für Abbrechen-Button
        confirm_disabled: Deaktiviert Bestätigen-Button

    Returns:
        'confirm' oder 'cancel'

    Beispiel:
        ```python
        action = render_two_button_footer(
            confirm_label="✅ Prüfung bestätigen"
        )

        if action == 'confirm':
            # Bestätigen-Logik
            pass
        elif action == 'cancel':
            # Abbrechen-Logik
            pass
        ```
    """
    st.divider()

    # Zentrierte Buttons mit 50% Breite
    col_left, col1, col2, col_right = st.columns([1, 2, 2, 1])

    with col1:
        if st.button(
            confirm_label,
            type="primary",
            use_container_width=True,
            disabled=confirm_disabled,
            key=f"btn_confirm_{_sanitize_key(confirm_label)}"
        ):
            return 'confirm'

    with col2:
        if st.button(
            cancel_label,
            use_container_width=True,
            key=f"btn_cancel_{_sanitize_key(cancel_label)}"
        ):
            return 'cancel'

    return None


def render_three_button_footer(
    primary_label: str = "✅ Bestätigen",
    secondary_label: str = "📝 Bearbeiten",
    cancel_label: str = "❌ Abbrechen",
    primary_disabled: bool = False,
    secondary_disabled: bool = False
) -> Optional[str]:
    """
    Rendert drei Buttons: Primary + Secondary + Cancel.

    Args:
        primary_label: Label für Primary-Button
        secondary_label: Label für Secondary-Button
        cancel_label: Label für Cancel-Button
        primary_disabled: Deaktiviert Primary-Button
        secondary_disabled: Deaktiviert Secondary-Button

    Returns:
        'primary', 'secondary' oder 'cancel'

    Beispiel:
        ```python
        action = render_three_button_footer(
            primary_label="✅ Prüfung bestätigen",
            secondary_label="❌ Artikel zurückweisen",
            cancel_label="🚫 Abbrechen"
        )

        if action == 'primary':
            # Bestätigen-Logik
            pass
        elif action == 'secondary':
            # Zurückweisen-Logik
            pass
        elif action == 'cancel':
            # Abbrechen-Logik
            pass
        ```
    """
    st.divider()

    # Zentrierte Buttons mit 50% Breite
    col_left, col1, col2, col3, col_right = st.columns([1, 2, 2, 2, 1])

    with col1:
        if st.button(
            primary_label,
            type="primary",
            use_container_width=True,
            disabled=primary_disabled,
            key=f"btn_primary_{_sanitize_key(primary_label)}"
        ):
            return 'primary'

    with col2:
        if st.button(
            secondary_label,
            use_container_width=True,
            disabled=secondary_disabled,
            key=f"btn_secondary_{_sanitize_key(secondary_label)}"
        ):
            return 'secondary'

    with col3:
        if st.button(
            cancel_label,
            use_container_width=True,
            key=f"btn_cancel_{_sanitize_key(cancel_label)}"
        ):
            return 'cancel'

    return None


def render_quality_footer(
    confirm_label: str = "✅ Prüfung bestätigen",
    reject_label: str = "🗑️ Als Ausschuss markieren",
    cancel_label: str = "🚫 Abbrechen",
    confirm_disabled: bool = False,
    reject_disabled: bool = False
) -> Optional[str]:
    """
    Rendert Quality-Footer mit Ausschuss-Option.

    Für Popups mit Qualitätsprüfung: Visual Inspection, Measurement.

    Args:
        confirm_label: Label für Bestätigen-Button
        reject_label: Label für Ausschuss-Button
        cancel_label: Label für Abbrechen-Button
        confirm_disabled: Deaktiviert Bestätigen-Button
        reject_disabled: Deaktiviert Ausschuss-Button

    Returns:
        'confirm', 'reject' oder 'cancel'

    Beispiel:
        ```python
        action = render_quality_footer(
            confirm_label="✅ Prüfung bestätigen",
            reject_label="🗑️ Als Ausschuss markieren"
        )

        if action == 'confirm':
            # Bestätigen mit evtl. Teilausschuss
            pass
        elif action == 'reject':
            # Gesamten Artikel als Ausschuss markieren
            pass
        elif action == 'cancel':
            # Abbrechen
            pass
        ```
    """
    st.divider()

    # Zentrierte Buttons mit 50% Breite
    col_left, col1, col2, col3, col_right = st.columns([1, 2, 2, 2, 1])

    with col1:
        if st.button(
            confirm_label,
            type="primary",
            use_container_width=True,
            disabled=confirm_disabled,
            key=f"btn_quality_confirm_{_sanitize_key(confirm_label)}"
        ):
            return 'confirm'

    with col2:
        if st.button(
            reject_label,
            use_container_width=True,
            disabled=reject_disabled,
            key=f"btn_quality_reject_{_sanitize_key(reject_label)}",
            help="Markiert den gesamten Artikel als Ausschuss"
        ):
            return 'reject'

    with col3:
        if st.button(
            cancel_label,
            use_container_width=True,
            key=f"btn_quality_cancel_{_sanitize_key(cancel_label)}"
        ):
            return 'cancel'

    return None


def render_standard_footer(
    save_label: str = "💾 Speichern",
    cancel_label: str = "❌ Abbrechen",
    save_disabled: bool = False
) -> Optional[str]:
    """
    Rendert Standard-Footer (2 Buttons).

    Für einfache Popups ohne Qualitätsprüfung: Data Confirmation, Document Check.

    Args:
        save_label: Label für Speichern-Button
        cancel_label: Label für Abbrechen-Button
        save_disabled: Deaktiviert Speichern-Button

    Returns:
        'save' oder 'cancel'

    Beispiel:
        ```python
        action = render_standard_footer()

        if action == 'save':
            # Speichern
            pass
        elif action == 'cancel':
            # Abbrechen
            pass
        ```
    """
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            save_label,
            type="primary",
            use_container_width=True,
            disabled=save_disabled,
            key=f"btn_save_{_sanitize_key(save_label)}"
        ):
            return 'save'

    with col2:
        if st.button(
            cancel_label,
            use_container_width=True,
            key=f"btn_cancel_{_sanitize_key(cancel_label)}"
        ):
            return 'cancel'

    return None


def render_confirm_cancel_footer(
    on_confirm_message: str = "Möchten Sie wirklich fortfahren?",
    confirm_label: str = "✅ Ja, fortfahren",
    cancel_label: str = "❌ Nein, abbrechen"
) -> Optional[str]:
    """
    Rendert eine Bestätigungs-Abfrage mit Warnung.

    Args:
        on_confirm_message: Bestätigungs-Nachricht
        confirm_label: Label für Bestätigen-Button
        cancel_label: Label für Abbrechen-Button

    Returns:
        'confirm' oder 'cancel'

    Beispiel:
        ```python
        action = render_confirm_cancel_footer(
            on_confirm_message="⚠️ Diese Aktion kann nicht rückgängig gemacht werden!",
            confirm_label="🗑️ Endgültig löschen"
        )
        ```
    """
    st.warning(on_confirm_message)

    return render_two_button_footer(
        confirm_label=confirm_label,
        cancel_label=cancel_label
    )


def render_save_cancel_footer(
    save_disabled: bool = False
) -> Optional[str]:
    """
    Rendert Speichern + Abbrechen Buttons.

    Args:
        save_disabled: Deaktiviert Speichern-Button

    Returns:
        'save' oder 'cancel'
    """
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💾 Speichern",
            type="primary",
            use_container_width=True,
            disabled=save_disabled,
            key="btn_save"
        ):
            return 'save'

    with col2:
        if st.button(
            "❌ Abbrechen",
            use_container_width=True,
            key="btn_cancel_save"
        ):
            return 'cancel'

    return None


def render_multi_action_footer(
    actions: List[dict],
    layout: Optional[List[int]] = None
) -> Optional[str]:
    """
    Rendert flexible Multi-Button-Leiste.

    Args:
        actions: Liste von Button-Definitionen:
            [
                {"label": "✅ Action1", "type": "primary", "key": "action1"},
                {"label": "📝 Action2", "key": "action2"},
                ...
            ]
        layout: Optional - Spaltenbreiten (z.B. [2, 1, 1])

    Returns:
        Key der geklickten Action oder None

    Beispiel:
        ```python
        action = render_multi_action_footer(
            actions=[
                {"label": "✅ Bestätigen", "type": "primary", "key": "confirm"},
                {"label": "📝 Bearbeiten", "key": "edit"},
                {"label": "🗑️ Löschen", "key": "delete"},
                {"label": "❌ Abbrechen", "key": "cancel"}
            ],
            layout=[2, 1, 1, 1]
        )
        ```
    """
    st.divider()

    num_actions = len(actions)

    if layout:
        cols = st.columns(layout)
    else:
        cols = st.columns(num_actions)

    for i, action in enumerate(actions):
        with cols[i]:
            button_type = action.get('type', 'secondary')
            disabled = action.get('disabled', False)

            if st.button(
                action['label'],
                type=button_type,
                use_container_width=True,
                disabled=disabled,
                key=f"btn_multi_{action['key']}"
            ):
                return action['key']

    return None


# ============== Helper Functions ==============

def _sanitize_key(text: str) -> str:
    """
    Macht Text Key-sicher (keine Leerzeichen, Sonderzeichen).

    Args:
        text: Text zum Sanitizen

    Returns:
        Sanitized Text
    """
    import re
    # Entferne Emojis und Sonderzeichen, ersetze Leerzeichen mit Underscore
    sanitized = re.sub(r'[^\w\s-]', '', text)
    sanitized = re.sub(r'[\s-]+', '_', sanitized)
    return sanitized.lower()


def _extract_action_name(action_text: str) -> str:
    """
    Extrahiert Action-Namen aus Button-Label (entfernt Emojis).

    Args:
        action_text: Button-Label (z.B. "❌ Abbrechen")

    Returns:
        Action-Name (lowercase, z.B. "abbrechen")
    """
    # Entferne alles bis zum ersten Buchstaben (Emojis, Leerzeichen)
    import re
    name = re.sub(r'^[^\w]+', '', action_text)
    return name.strip().lower()
