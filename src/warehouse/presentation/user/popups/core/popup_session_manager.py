"""
Popup Session Manager
Centralized management of session state for popups.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PopupSessionManager:
    """
    Verwaltet Session-State für Popups zentral.

    Verhindert Session-State-Chaos durch strukturierte Namensgebung
    und automatisches Cleanup.
    """

    def __init__(self, popup_id: str):
        """
        Initialisiert den Session Manager.

        Args:
            popup_id: Eindeutige ID für das Popup (z.B. 'visual_inspection_ARTICLE_BATCH')
        """
        self.popup_id = popup_id
        self.prefix = f"popup_{popup_id}_"

    def set(self, key: str, value: Any) -> None:
        """
        Setzt einen Wert im Session-State mit Popup-Prefix.

        Args:
            key: Key ohne Prefix
            value: Wert
        """
        full_key = f"{self.prefix}{key}"
        st.session_state[full_key] = value
        logger.debug(f"Session set: {full_key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Wert aus Session-State.

        Args:
            key: Key ohne Prefix
            default: Default-Wert wenn nicht gefunden

        Returns:
            Wert oder default
        """
        full_key = f"{self.prefix}{key}"
        return st.session_state.get(full_key, default)

    def has(self, key: str) -> bool:
        """
        Prüft ob Key existiert.

        Args:
            key: Key ohne Prefix

        Returns:
            True wenn existiert
        """
        full_key = f"{self.prefix}{key}"
        return full_key in st.session_state

    def delete(self, key: str) -> None:
        """
        Löscht einen Key aus Session-State.

        Args:
            key: Key ohne Prefix
        """
        full_key = f"{self.prefix}{key}"
        if full_key in st.session_state:
            del st.session_state[full_key]
            logger.debug(f"Session deleted: {full_key}")

    def cleanup(self) -> None:
        """
        Räumt alle Keys dieses Popups auf.
        """
        keys_to_delete = [
            key for key in st.session_state.keys()
            if key.startswith(self.prefix)
        ]

        for key in keys_to_delete:
            del st.session_state[key]

        logger.debug(f"Session cleanup: Removed {len(keys_to_delete)} keys for {self.popup_id}")

    def get_all(self) -> Dict[str, Any]:
        """
        Gibt alle Keys dieses Popups zurück.

        Returns:
            Dict mit allen Keys (ohne Prefix) und Werten
        """
        result = {}
        prefix_len = len(self.prefix)

        for key, value in st.session_state.items():
            if key.startswith(self.prefix):
                clean_key = key[prefix_len:]
                result[clean_key] = value

        return result

    def set_action(self, action: str) -> None:
        """
        Setzt die Popup-Action (Standard-Key für Action-Handling).

        Args:
            action: Action-Name (z.B. 'confirm', 'cancel')
        """
        st.session_state['popup_action'] = action

    def get_action(self) -> Optional[str]:
        """
        Holt die Popup-Action.

        Returns:
            Action-Name oder None
        """
        return st.session_state.get('popup_action')

    def clear_action(self) -> None:
        """Löscht die Popup-Action."""
        if 'popup_action' in st.session_state:
            del st.session_state['popup_action']

    @staticmethod
    def cleanup_all_popups() -> None:
        """
        Räumt alle Popup-bezogenen Keys auf (global cleanup).
        """
        keys_to_delete = [
            key for key in st.session_state.keys()
            if key.startswith('popup_')
        ]

        for key in keys_to_delete:
            del st.session_state[key]

        logger.debug(f"Global popup cleanup: Removed {len(keys_to_delete)} keys")


def create_popup_session_manager(
    article_number: str,
    batch_number: str,
    popup_type: str
) -> PopupSessionManager:
    """
    Factory-Funktion für Popup Session Manager.

    Args:
        article_number: Artikelnummer
        batch_number: Chargennummer
        popup_type: Typ des Popups (z.B. 'visual_inspection', 'measurement')

    Returns:
        PopupSessionManager Instanz

    Beispiel:
        ```python
        manager = create_popup_session_manager(
            'MG0001',
            'BATCH123',
            'visual_inspection'
        )

        manager.set('waste_quantity', 5)
        waste = manager.get('waste_quantity')
        ```
    """
    popup_id = f"{popup_type}_{article_number}_{batch_number}".replace('-', '_').replace('.', '_')
    return PopupSessionManager(popup_id)
