"""
Form Components
Reusable form building components for popup dialogs.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from datetime import date, datetime


class FormBuilder:
    """
    Builder-Pattern für standardisierte Formulare.

    Ermöglicht einfaches Erstellen von Formularen mit automatischem
    Layout in Spalten.

    Beispiel:
        ```python
        form = FormBuilder(columns=2)

        form.add_section("Grunddaten")
        form.add_text_input("Name", "name_field", value="")
        form.add_number_input("Alter", "age_field", value=0, min_value=0)

        form.add_section("Zusatzinfo")
        form.add_text_area("Notizen", "notes_field")

        # Render und hole Daten
        data = form.render()
        print(data['name_field'], data['age_field'])
        ```
    """

    def __init__(self, columns: int = 2):
        """
        Initialisiert den FormBuilder.

        Args:
            columns: Anzahl Spalten für das Layout (default: 2)
        """
        self.columns = columns
        self.sections = []
        self.current_section = None

    def add_section(
        self,
        title: str,
        expanded: bool = True,
        use_expander: bool = False
    ) -> 'FormBuilder':
        """
        Fügt eine neue Formular-Sektion hinzu.

        Args:
            title: Titel der Sektion
            expanded: Bei Expander: initial expanded (default: True)
            use_expander: Nutzt st.expander statt direkter Anzeige

        Returns:
            Self für Method-Chaining
        """
        self.current_section = {
            'title': title,
            'expanded': expanded,
            'use_expander': use_expander,
            'fields': []
        }
        self.sections.append(self.current_section)
        return self

    def add_text_input(
        self,
        label: str,
        key: str,
        value: str = "",
        disabled: bool = False,
        help: str = None,
        placeholder: str = None
    ) -> 'FormBuilder':
        """Fügt Text-Input hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'text_input',
            'label': label,
            'key': key,
            'value': value,
            'disabled': disabled,
            'help': help,
            'placeholder': placeholder
        })
        return self

    def add_number_input(
        self,
        label: str,
        key: str,
        value: int = 0,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: int = 1,
        help: str = None,
        format: str = "%d"
    ) -> 'FormBuilder':
        """Fügt Number-Input hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'number_input',
            'label': label,
            'key': key,
            'value': value,
            'min_value': min_value,
            'max_value': max_value,
            'step': step,
            'help': help,
            'format': format
        })
        return self

    def add_date_input(
        self,
        label: str,
        key: str,
        value: Optional[date] = None,
        min_value: Optional[date] = None,
        max_value: Optional[date] = None,
        help: str = None
    ) -> 'FormBuilder':
        """Fügt Date-Input hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'date_input',
            'label': label,
            'key': key,
            'value': value or date.today(),
            'min_value': min_value,
            'max_value': max_value,
            'help': help
        })
        return self

    def add_checkbox(
        self,
        label: str,
        key: str,
        value: bool = False,
        help: str = None
    ) -> 'FormBuilder':
        """Fügt Checkbox hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'checkbox',
            'label': label,
            'key': key,
            'value': value,
            'help': help
        })
        return self

    def add_selectbox(
        self,
        label: str,
        key: str,
        options: List[str],
        index: int = 0,
        help: str = None
    ) -> 'FormBuilder':
        """Fügt Selectbox hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'selectbox',
            'label': label,
            'key': key,
            'options': options,
            'index': index,
            'help': help
        })
        return self

    def add_text_area(
        self,
        label: str,
        key: str,
        value: str = "",
        height: int = 100,
        placeholder: str = None,
        help: str = None
    ) -> 'FormBuilder':
        """Fügt Textarea hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'text_area',
            'label': label,
            'key': key,
            'value': value,
            'height': height,
            'placeholder': placeholder,
            'help': help
        })
        return self

    def add_slider(
        self,
        label: str,
        key: str,
        min_value: float = 0.0,
        max_value: float = 100.0,
        value: float = 50.0,
        step: float = 1.0,
        help: str = None
    ) -> 'FormBuilder':
        """Fügt Slider hinzu."""
        self._ensure_section()
        self.current_section['fields'].append({
            'type': 'slider',
            'label': label,
            'key': key,
            'min_value': min_value,
            'max_value': max_value,
            'value': value,
            'step': step,
            'help': help
        })
        return self

    def render(self) -> Dict[str, Any]:
        """
        Rendert alle Sektionen und gibt die Formulardaten zurück.

        Returns:
            Dict mit allen Formular-Werten: {field_key: field_value}
        """
        results = {}

        for section in self.sections:
            # Section Header oder Expander
            if section['use_expander']:
                with st.expander(f"**{section['title']}**", expanded=section['expanded']):
                    section_results = self._render_section_fields(section['fields'])
                    results.update(section_results)
            else:
                if section['title']:
                    st.markdown(f"#### {section['title']}")

                section_results = self._render_section_fields(section['fields'])
                results.update(section_results)

                st.divider()

        return results

    def _render_section_fields(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rendert die Felder einer Sektion."""
        results = {}

        # Teile Felder in Rows auf (basierend auf columns)
        rows = []
        current_row = []

        for field in fields:
            current_row.append(field)
            if len(current_row) >= self.columns:
                rows.append(current_row)
                current_row = []

        # Füge letzte unvollständige Row hinzu
        if current_row:
            rows.append(current_row)

        # Render jede Row
        for row in rows:
            cols = st.columns(self.columns)

            for i, field in enumerate(row):
                with cols[i]:
                    field_value = self._render_field(field)
                    results[field['key']] = field_value

        return results

    def _render_field(self, field: Dict[str, Any]) -> Any:
        """Rendert ein einzelnes Feld."""
        field_type = field['type']

        if field_type == 'text_input':
            return st.text_input(
                field['label'],
                value=field['value'],
                key=field['key'],
                disabled=field.get('disabled', False),
                help=field.get('help'),
                placeholder=field.get('placeholder')
            )

        elif field_type == 'number_input':
            kwargs = {
                'label': field['label'],
                'value': field['value'],
                'key': field['key'],
                'step': field['step'],
                'help': field.get('help'),
                'format': field.get('format', '%d')
            }
            if field['min_value'] is not None:
                kwargs['min_value'] = field['min_value']
            if field['max_value'] is not None:
                kwargs['max_value'] = field['max_value']

            return st.number_input(**kwargs)

        elif field_type == 'date_input':
            kwargs = {
                'label': field['label'],
                'value': field['value'],
                'key': field['key'],
                'help': field.get('help')
            }
            if field.get('min_value'):
                kwargs['min_value'] = field['min_value']
            if field.get('max_value'):
                kwargs['max_value'] = field['max_value']

            return st.date_input(**kwargs)

        elif field_type == 'checkbox':
            return st.checkbox(
                field['label'],
                value=field['value'],
                key=field['key'],
                help=field.get('help')
            )

        elif field_type == 'selectbox':
            return st.selectbox(
                field['label'],
                options=field['options'],
                index=field['index'],
                key=field['key'],
                help=field.get('help')
            )

        elif field_type == 'text_area':
            return st.text_area(
                field['label'],
                value=field['value'],
                height=field.get('height', 100),
                key=field['key'],
                placeholder=field.get('placeholder'),
                help=field.get('help')
            )

        elif field_type == 'slider':
            return st.slider(
                field['label'],
                min_value=field['min_value'],
                max_value=field['max_value'],
                value=field['value'],
                step=field.get('step', 1.0),
                key=field['key'],
                help=field.get('help')
            )

        return None

    def _ensure_section(self):
        """Stellt sicher, dass eine aktuelle Sektion existiert."""
        if self.current_section is None:
            self.add_section("", expanded=True, use_expander=False)


def render_quantity_inputs(
    ordered_quantity: int = 0,
    delivery_slip_quantity: int = 0,
    delivered_quantity: Optional[int] = None,
    key_prefix: str = "qty"
) -> Dict[str, int]:
    """
    Rendert die 3 Mengen-Eingabefelder für Inspection-Popups.

    Args:
        ordered_quantity: Bestellmenge (aus Bestellung)
        delivery_slip_quantity: Lieferscheinmenge (OCR-extrahiert)
        delivered_quantity: Gezählte Liefermenge
        key_prefix: Prefix für Session-State Keys

    Returns:
        Dict mit {'ordered': int, 'delivery_slip': int, 'delivered': int}
    """
    st.markdown("#### 📊 Mengen-Erfassung")

    col1, col2 = st.columns(2)

    with col1:
        # 1. Bestellmenge
        ordered = st.number_input(
            "1️⃣ Bestellmenge (aus Bestellung):",
            value=ordered_quantity,
            min_value=0,
            key=f"{key_prefix}_ordered",
            help="Ursprünglich bestellte Menge beim Lieferanten"
        )

        # 2. Lieferscheinmenge
        delivery_slip = st.number_input(
            "2️⃣ Lieferscheinmenge (vom OCR):",
            value=delivery_slip_quantity,
            min_value=0,
            key=f"{key_prefix}_delivery_slip",
            help="Auf dem Lieferschein angegebene Menge"
        )

    with col2:
        # 3. Liefermenge (gezählt)
        st.markdown("**3️⃣ Liefermenge (gezählt) ⚠️:**")
        st.caption("*Bitte zählen Sie die Ware manuell!*")

        default_delivered = str(delivered_quantity) if delivered_quantity not in [None, 0] else ""

        delivered_str = st.text_input(
            "Gezählte Menge:",
            value=default_delivered,
            key=f"{key_prefix}_delivered",
            placeholder="Bitte Ware zählen...",
            help="Tatsächlich physisch gelieferte Menge",
            label_visibility="collapsed"
        )

        # Parse delivered quantity
        delivered = None
        if delivered_str.strip():
            try:
                delivered = int(delivered_str)
                if delivered < 0:
                    st.error("❌ Menge kann nicht negativ sein!")
                    delivered = None
            except ValueError:
                st.error("❌ Bitte geben Sie eine gültige Zahl ein!")

    # Abweichungs-Warnungen
    if delivered is not None:
        if delivery_slip != delivered:
            diff = delivered - delivery_slip
            st.warning(f"⚠️ **Abweichung Lieferschein:** {diff:+d} (Geliefert: {delivered}, Lieferschein: {delivery_slip})")

        if ordered > 0 and ordered != delivered:
            diff = delivered - ordered
            st.warning(f"⚠️ **Abweichung Bestellung:** {diff:+d} (Geliefert: {delivered}, Bestellt: {ordered})")
    else:
        st.info("💡 Bitte zählen Sie die Ware und geben Sie die tatsächliche Liefermenge ein.")

    return {
        'ordered': ordered,
        'delivery_slip': delivery_slip,
        'delivered': delivered
    }
