"""
Base Popup Class for Inspection Popups
Provides standardized 3-part structure: Header, Body, Footer
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import streamlit as st
import logging

logger = logging.getLogger(__name__)


class InspectionPopup(ABC):
    """
    Basis-Klasse für alle Inspection Popups.

    Definiert eine standardisierte 3-Teile-Struktur:
    1. Header: Artikelinformationen und Status
    2. Body: Formular-Felder und Eingaben
    3. Footer: Action-Buttons

    Beispiel:
        ```python
        class MyCustomPopup(InspectionPopup):
            def __init__(self, item_data):
                super().__init__(
                    title="Mein Custom Popup",
                    item_data=item_data
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
        info_text: Optional[str] = None
    ):
        """
        Initialisiert das Popup.

        Args:
            title: Popup-Titel (erscheint im @st.dialog Dekorator)
            item_data: Dict mit allen Item-Informationen
            width: Popup-Breite ("small", "large")
            show_info_box: Zeigt Info-Box im Header
            info_text: Text für Info-Box
        """
        self.title = title
        self.item_data = item_data
        self.width = width
        self.show_info_box = show_info_box
        self.info_text = info_text

        # Zentrale Daten-Extraktion für einfachen Zugriff
        self.article_number = item_data.get('article_number', '')
        self.batch_number = item_data.get('batch_number', '')
        self.delivery_number = item_data.get('delivery_number', '')
        self.quantity = item_data.get('quantity', 0)
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
                from ..components.header_components import render_article_header
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
                from ..components.form_components import FormBuilder

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
        from ..components.footer_components import render_action_buttons

        return render_action_buttons(
            primary_label=self.get_primary_action_label(),
            secondary_actions=self.get_secondary_actions()
        )

    def handle_secondary_action(self, action: str) -> None:
        """
        Verarbeitet Sekundäraktionen (z.B. Abbrechen, Zurück).

        Kann überschrieben werden für Custom-Actions.
        Standard: Setzt popup_action='cancel' und macht st.rerun()

        Args:
            action: Name der Aktion (z.B. 'abbrechen', 'zurück')
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
        1. render_header()
        2. render_body()
        3. render_footer()
        4. handle_*_action()
        """
        try:
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

    # ========== Utility Methods ==========

    def get_current_user(self) -> str:
        """Gibt den aktuellen Username aus Session-State zurück."""
        user = st.session_state.get('current_user')
        if user is None:
            return 'System'
        if isinstance(user, dict):
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
