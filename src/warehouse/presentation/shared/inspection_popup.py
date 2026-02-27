"""
Base Popup Class for Inspection Popups.

Provides standardized 3-part structure: Header, Body, Footer
Used by both User-View and Admin-View.

Features:
- Automatic CSS application
- Validation framework
- Audit logging hooks
- Permission-ready architecture (for future implementation)

Author: Medealis
Version: 2.0.0 - Shared across User & Admin
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import streamlit as st
import logging
from warehouse.presentation.shared.popup_styles import get_popup_css

logger = logging.getLogger(__name__)


class InspectionPopup(ABC):
    """
    Basis-Klasse für alle Inspection Popups (User & Admin).

    Definiert eine standardisierte 3-Teile-Struktur:
    1. Header: Artikelinformationen und Status
    2. Body: Formular-Felder und Eingaben
    3. Footer: Action-Buttons

    Permission-Ready:
    - required_permission Parameter vorbereitet
    - _check_permissions() Hook-Point
    - Aktuell: Alle Permissions erlaubt
    - Später: Einfach aktivierbar

    Beispiel:
        ```python
        from warehouse.presentation.shared.inspection_popup import InspectionPopup

        class MyCustomPopup(InspectionPopup):
            def __init__(self, item_data):
                super().__init__(
                    title="Mein Custom Popup",
                    item_data=item_data,
                    required_permission="my_custom_action"  # Optional
                )

            def render_header(self):
                # Custom header implementation
                pass

            def render_body(self):
                # Custom body with form fields
                return {"field1": value1, "field2": value2}

            def handle_primary_action(self, form_data):
                # Process the form data
                pass
        ```
    """

    def __init__(
        self,
        title: str,
        item_data: Dict[str, Any],
        width: str = "large",
        show_info_box: bool = False,
        info_text: Optional[str] = None,
        css_style: str = "compact",
        required_permission: Optional[str] = None  # ← Permission-Ready
    ):
        """
        Initialisiert das Popup.

        Args:
            title: Popup-Titel (erscheint im @st.dialog Dekorator)
            item_data: Dict mit allen Item-Informationen
            width: Popup-Breite ("small", "large")
            show_info_box: Zeigt Info-Box im Header
            info_text: Text für Info-Box
            css_style: CSS-Style für Popup ("compact", "standard", "wide")
            required_permission: Permission-Name (z.B. "perform_measurement")
                                Aktuell nur Dokumentation, später für Permission-System
        """
        self.title = title
        self.item_data = item_data
        self.width = width
        self.show_info_box = show_info_box
        self.info_text = info_text
        self.css_style = css_style
        self.required_permission = required_permission  # ← Für später

        # Zentrale Daten-Extraktion für einfachen Zugriff
        self.article_number = item_data.get('article_number', '')
        self.batch_number = item_data.get('batch_number', '')
        self.delivery_number = item_data.get('delivery_number', '')
        # Ensure quantity is always int (could come as string from DB)
        raw_quantity = item_data.get('quantity', 0)
        self.quantity = int(raw_quantity) if raw_quantity else 0
        self.status = item_data.get('status', '')
        self.supplier_name = item_data.get('supplier_name', '')

        # Validation flag
        self._validated = False

    # ========== Abstract Methods (müssen implementiert werden) ==========

    @abstractmethod
    def render_header(self) -> None:
        """
        Rendert den Popup-Kopfteil mit Artikelinformationen.

        Diese Methode muss in der Unterklasse implementiert werden.
        Üblicherweise nutzt man hier die render_article_header() Funktion
        aus header_components.py

        Beispiel:
            ```python
            def render_header(self):
                from warehouse.presentation.shared.components import render_article_header
                render_article_header(
                    article_number=self.article_number,
                    batch_number=self.batch_number,
                    delivery_number=self.delivery_number
                )
            ```
        """
        pass

    @abstractmethod
    def render_body(self) -> Dict[str, Any]:
        """
        Rendert den Hauptbereich mit Formular-Feldern.

        Diese Methode muss in der Unterklasse implementiert werden.
        Sie sollte ein Dict mit allen Formular-Werten zurückgeben.

        Returns:
            Dict mit Formular-Daten, z.B.:
            {
                'field1': 'value1',
                'field2': 123,
                'checkbox1': True
            }

        Beispiel:
            ```python
            def render_body(self):
                from warehouse.presentation.shared.components import FormBuilder

                form = FormBuilder(columns=2)
                form.add_section("Eingaben")
                form.add_text_input("Name", "name_field", value="")

                return form.render()
            ```
        """
        pass

    @abstractmethod
    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """
        Verarbeitet die Hauptaktion (z.B. Bestätigen, Speichern).

        Diese Methode wird aufgerufen, wenn der Primary-Button geklickt wird.
        Hier sollte die Geschäftslogik implementiert werden (DB-Speicherung,
        Dokument-Generierung, etc.)

        Args:
            form_data: Dict mit allen Formular-Werten aus render_body()

        Beispiel:
            ```python
            def handle_primary_action(self, form_data):
                # Validierung
                if not self.validate_form(form_data):
                    return

                # Speichere in DB
                item_service.update_item(
                    article_number=self.article_number,
                    **form_data
                )

                # Erfolg
                st.success("✅ Erfolgreich gespeichert!")
                st.rerun()
            ```
        """
        pass

    # ========== Optional Override Methods ==========

    def render_footer(self) -> Optional[str]:
        """
        Rendert die Button-Leiste am unteren Ende.

        Kann überschrieben werden für Custom-Buttons.
        Standard: Primary-Button + Abbrechen-Button

        Returns:
            'primary' wenn Primary-Button geklickt, sonst Action-Name
        """
        # Hinweis: footer_components wird später verschoben
        # Für jetzt: Einfache Standard-Implementation
        col1, col2 = st.columns(2)

        with col1:
            if st.button(self.get_primary_action_label(), type="primary", use_container_width=True):
                return "primary"

        with col2:
            if st.button("❌ Abbrechen", use_container_width=True):
                return "cancel"

        return None

    def handle_secondary_action(self, action: str) -> None:
        """
        Verarbeitet Sekundäraktionen (z.B. Abbrechen, Zurück).

        Kann überschrieben werden für Custom-Actions.
        Standard: Setzt popup_action='cancel' und macht st.rerun()

        Args:
            action: Name der Aktion (z.B. 'abbrechen', 'cancel')
        """
        if action == 'abbrechen' or action == 'cancel':
            st.session_state['popup_action'] = 'cancel'
            self.cleanup_session_state()
            st.rerun()

    def validate_form(self, form_data: Dict[str, Any]) -> bool:
        """
        Validiert die Formulardaten.

        Kann überschrieben werden für Custom-Validierung.
        Standard: Ruft get_validation_rules() auf und validiert.

        Args:
            form_data: Dict mit allen Formular-Werten

        Returns:
            True wenn Validierung erfolgreich, sonst False
        """
        validation_rules = self.get_validation_rules()

        for field, rules in validation_rules.items():
            value = form_data.get(field)

            # Required Check
            if rules.get('required', False):
                if not value or (isinstance(value, str) and not value.strip()):
                    error_msg = rules.get('error_message', f"❌ Feld '{field}' ist erforderlich!")
                    st.error(error_msg)
                    return False

            # Min Length Check
            if 'min_length' in rules and isinstance(value, str):
                if len(value.strip()) < rules['min_length']:
                    error_msg = rules.get('error_message', f"❌ '{field}' muss mindestens {rules['min_length']} Zeichen haben!")
                    st.error(error_msg)
                    return False

            # Min Value Check
            if 'min_value' in rules and isinstance(value, (int, float)):
                if value < rules['min_value']:
                    error_msg = rules.get('error_message', f"❌ '{field}' muss mindestens {rules['min_value']} sein!")
                    st.error(error_msg)
                    return False

            # Custom Validator
            if 'custom_validator' in rules:
                is_valid, error_msg = rules['custom_validator'](value)
                if not is_valid:
                    st.error(error_msg)
                    return False

        return True

    def get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Gibt Validierungsregeln zurück.

        Kann überschrieben werden für Custom-Validierung.

        Returns:
            Dict mit Validierungsregeln pro Feld, z.B.:
            {
                'field_name': {
                    'required': True,
                    'min_length': 2,
                    'error_message': 'Custom error'
                }
            }
        """
        return {}

    def get_primary_action_label(self) -> str:
        """
        Gibt das Label für den Primary-Button zurück.

        Kann überschrieben werden.
        """
        return "✅ Bestätigen"

    def get_secondary_actions(self) -> List[str]:
        """
        Gibt Liste von Sekundär-Aktionen zurück.

        Kann überschrieben werden.
        """
        return ["❌ Abbrechen"]

    def cleanup_session_state(self) -> None:
        """
        Räumt Session-State auf.

        Kann überschrieben werden für Custom-Cleanup.
        Standard: Entfernt popup-spezifische Keys.
        """
        cleanup_keys = [
            'popup_action',
            'confirmed_data',
            f'popup_{self.article_number}_{self.batch_number}'
        ]

        for key in cleanup_keys:
            if key in st.session_state:
                del st.session_state[key]

    # ========== Main Render Method ==========

    def render(self):
        """
        Haupt-Render-Methode - orchestriert die Popup-Darstellung.

        Diese Methode sollte nicht überschrieben werden, außer für
        sehr spezielle Fälle. Die Standardimplementierung ruft in
        der richtigen Reihenfolge auf:
        1. Permission-Check (Hook-Point)
        2. CSS anwenden (automatisch)
        3. render_header()
        4. render_body()
        5. render_footer()
        6. handle_*_action()
        """
        try:
            # ↓ Hook-Point: Permission-Check (aktuell immer erlaubt)
            if not self._check_permissions():
                return

            # CSS automatisch anwenden
            self._apply_css()

            # Header
            self.render_header()

            # Body (Datenbereich)
            form_data = self.render_body()

            # Footer (Buttons)
            action = self.render_footer()

            # Action Handler
            if action == 'primary':
                # Validierung
                if not self.validate_form(form_data):
                    st.stop()

                # Primary Action
                self.handle_primary_action(form_data)

            elif action:
                # Secondary Actions
                self.handle_secondary_action(action)

        except Exception as e:
            logger.error(f"Error in popup render: {e}", exc_info=True)
            st.error(f"❌ Fehler im Popup: {e}")

    def _check_permissions(self) -> bool:
        """
        Hook-Point für Permission-Checks.

        AKTUELL: Immer True (alle dürfen alles)
        SPÄTER: Echter Permission-Check aktivierbar

        Returns:
            True wenn erlaubt, False sonst

        IMPLEMENTATION GUIDE (für später):
        ---------------------------------
        Um Permissions zu aktivieren:

        1. Erstelle src/warehouse/domain/enums/permission.py mit Permission-Enum
        2. Erstelle src/warehouse/application/services/authorization_service.py
        3. Aktiviere den auskommentierten Code unten
        4. Fertig! Alle Popups nutzen automatisch ihre required_permission

        Beispiel-Code für später:
        ```python
        if self.required_permission is None:
            return True

        from warehouse.application.services.authorization_service import authorization_service

        if not authorization_service.has_permission(self.required_permission):
            st.error("⛔ **Keine Berechtigung!**")
            st.info(f"Erforderliche Berechtigung: `{self.required_permission}`")
            logger.warning(
                f"Permission denied: user={st.session_state.get('current_user')}, "
                f"required={self.required_permission}"
            )
            return False

        return True
        ```
        """
        # AKTUELL: Einfach immer erlauben
        return True

    def _apply_css(self) -> None:
        """
        Wendet CSS-Style an (intern, wird automatisch von render() aufgerufen).

        Diese Methode sollte nicht manuell aufgerufen werden.
        """
        css = get_popup_css(self.css_style)
        st.markdown(css, unsafe_allow_html=True)

    # ========== Utility Methods ==========

    def get_current_user(self) -> str:
        """Gibt den aktuellen vollständigen Namen aus Session-State zurück."""
        user = st.session_state.get('current_user')
        if user is None:
            return 'System'
        if isinstance(user, dict):
            # Priorisiere full_name, fallback auf username
            full_name = user.get('full_name')
            if full_name and full_name.strip():
                return full_name
            return user.get('username', 'System')
        return str(user)

    def log_action(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Loggt eine Aktion.

        Args:
            action: Name der Aktion
            details: Zusätzliche Details
        """
        log_data = {
            'popup': self.__class__.__name__,
            'action': action,
            'article': self.article_number,
            'batch': self.batch_number,
            'user': self.get_current_user()
        }

        if details:
            log_data.update(details)

        logger.info(f"Popup Action: {log_data}")

    def show_success(self, message: str, with_balloons: bool = False) -> None:
        """
        Zeigt Erfolgsmeldung.

        Args:
            message: Erfolgsmeldung
            with_balloons: Zeigt Ballons-Animation
        """
        st.success(message)

        if with_balloons:
            st.balloons()

    def show_error(self, message: str) -> None:
        """Zeigt Fehlermeldung."""
        st.error(message)

    def show_warning(self, message: str) -> None:
        """Zeigt Warnmeldung."""
        st.warning(message)

    def show_info(self, message: str) -> None:
        """Zeigt Info-Meldung."""
        st.info(message)
