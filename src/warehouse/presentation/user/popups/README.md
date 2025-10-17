# User Popups - Standardisierte Inspection Popups

Dieses Modul enthält **standardisierte, wiederverwendbare Komponenten** für Inspection-Popups in der User-View.

## 📁 Struktur

```
user/popups/
├── core/                          # Basis-Klassen und Utilities
│   ├── base_popup.py              # InspectionPopup Basis-Klasse
│   ├── popup_session_manager.py   # Session-State Management
│   └── popup_validators.py        # Validierungs-Funktionen
├── components/                    # Wiederverwendbare UI-Komponenten
│   ├── header_components.py       # Artikel-Header, Status-Badges
│   ├── form_components.py         # FormBuilder, Input-Felder
│   ├── document_components.py     # Dokument-Upload, Ordner-Management
│   └── footer_components.py       # Button-Leisten
├── visual_inspection.py           # Beispiel: Sichtkontrolle-Popup
├── measurement.py                 # Beispiel: Vermessungs-Popup
└── data_confirmation.py           # Beispiel: Datenbestätigungs-Popup
```

---

## 🚀 Quick Start

### **1. Einfaches Popup erstellen**

```python
from user.popups.core.base_popup import InspectionPopup
from user.popups.components import (
    render_article_header,
    FormBuilder,
    render_action_buttons
)
import streamlit as st

class MyCustomPopup(InspectionPopup):
    def __init__(self, item_data):
        super().__init__(
            title="Mein Custom Popup",
            item_data=item_data
        )

    def render_header(self):
        render_article_header(
            article_number=self.article_number,
            batch_number=self.batch_number,
            delivery_number=self.delivery_number,
            show_info_box=True,
            info_text="Bitte prüfen Sie alle Felder"
        )

    def render_body(self):
        form = FormBuilder(columns=2)

        form.add_section("Eingaben")
        form.add_text_input("Name", "name", value="")
        form.add_number_input("Menge", "quantity", value=0)

        return form.render()

    def handle_primary_action(self, form_data):
        # Validierung
        if not form_data['name']:
            st.error("Name ist erforderlich!")
            return

        # Speichern
        st.success(f"Gespeichert: {form_data['name']}")
        st.rerun()

# Verwendung
@st.dialog("Mein Custom Popup")
def show_my_popup(item_data):
    popup = MyCustomPopup(item_data)
    popup.render()
```

---

## 📚 Komponenten-Dokumentation

### **1. Base Popup (`InspectionPopup`)**

Die Basis-Klasse für alle Inspection-Popups mit 3-Teile-Struktur.

**Muss überschrieben werden:**
- `render_header()` - Rendert Popup-Kopfteil
- `render_body()` - Rendert Formular-Bereich
- `handle_primary_action(form_data)` - Verarbeitet Hauptaktion

**Optional überschreiben:**
- `render_footer()` - Custom Button-Leiste
- `validate_form(form_data)` - Custom Validierung
- `get_primary_action_label()` - Button-Label
- `get_secondary_actions()` - Sekundär-Aktionen

**Utility-Methoden:**
- `get_current_user()` - Aktueller User
- `log_action(action, details)` - Logging
- `show_success(message)` - Erfolgsmeldung
- `cleanup_session_state()` - Session-Cleanup

---

### **2. Header Components**

#### **`render_article_header()`**

Rendert standardisierten Artikel-Header.

```python
from user.popups.components import render_article_header

render_article_header(
    article_number="MG0001",
    batch_number="BATCH-123",
    delivery_number="LS-001",
    quantity=100,
    status="In Bearbeitung",
    show_info_box=True,
    info_text="Wichtige Info hier"
)
```

#### **`render_status_badge()`**

Rendert farbiges Status-Badge.

```python
from user.popups.components import render_status_badge

render_status_badge("COMPLETED")  # Grün
render_status_badge("IN_PROGRESS")  # Blau
render_status_badge("FAILED")  # Rot
```

#### **`render_progress_indicator()`**

Fortschrittsanzeige für mehrstufige Popups.

```python
from user.popups.components.header_components import render_progress_indicator

render_progress_indicator(
    current_step=2,
    total_steps=3,
    step_labels=["Daten", "Dokumente", "Abschluss"]
)
```

---

### **3. Form Components**

#### **`FormBuilder`**

Builder-Pattern für Formulare mit automatischem Layout.

```python
from user.popups.components import FormBuilder

form = FormBuilder(columns=2)

# Sektion hinzufügen
form.add_section("Grunddaten")

# Felder hinzufügen
form.add_text_input("Name", "name", value="", help="Vollständiger Name")
form.add_number_input("Alter", "age", value=0, min_value=0)
form.add_date_input("Datum", "date", value=date.today())
form.add_checkbox("Aktiv", "active", value=True)
form.add_text_area("Notizen", "notes", height=100)

# Render und hole Daten
data = form.render()
# data = {'name': '...', 'age': 25, 'date': ..., 'active': True, 'notes': '...'}
```

**Verfügbare Feld-Typen:**
- `add_text_input()` - Text-Eingabe
- `add_number_input()` - Zahlen-Eingabe
- `add_date_input()` - Datums-Auswahl
- `add_checkbox()` - Checkbox
- `add_selectbox()` - Dropdown
- `add_text_area()` - Mehrzeilige Text-Eingabe
- `add_slider()` - Schieberegler

#### **`render_quantity_inputs()`**

Spezial-Komponente für 3-Mengen-Erfassung.

```python
from user.popups.components import render_quantity_inputs

quantities = render_quantity_inputs(
    ordered_quantity=100,
    delivery_slip_quantity=98,
    delivered_quantity=None,  # User muss zählen
    key_prefix="qty"
)

# quantities = {
#     'ordered': 100,
#     'delivery_slip': 98,
#     'delivered': 95  # User-Input
# }
```

---

### **4. Document Components**

#### **`render_document_uploader()`**

Standardisierter Dokumenten-Uploader mit optionaler KI-Analyse.

```python
from user.popups.components import render_document_uploader

def analyze_doc(file, idx):
    st.info(f"Analysiere {file.name}...")
    # KI-Analyse hier

files = render_document_uploader(
    label="Vermessungsprotokoll hochladen",
    key="measurement_upload",
    file_types=['pdf', 'png', 'jpg'],
    accept_multiple=True,
    show_ai_analysis=True,
    ai_analysis_callback=analyze_doc
)
```

#### **`render_folder_path()`**

Zeigt Ordner-Pfad mit "Ordner öffnen"-Button.

```python
from user.popups.components import render_folder_path

folder = render_folder_path(
    article_number="MG0001",
    batch_number="BATCH-123",
    delivery_number="LS-001"
)
```

#### **`save_uploaded_document()`**

Speichert hochgeladenes Dokument.

```python
from user.popups.components.document_components import save_uploaded_document

result = save_uploaded_document(
    uploaded_file=file,
    article_number="MG0001",
    batch_number="BATCH-123",
    delivery_number="LS-001",
    document_type="vermessungsprotokoll",
    filename_prefix="Vermessungsprotokoll"
)

if result['success']:
    st.success(f"Gespeichert: {result['file_path']}")
```

---

### **5. Footer Components**

#### **`render_action_buttons()`**

Flexible Button-Leiste.

```python
from user.popups.components import render_action_buttons

action = render_action_buttons(
    primary_label="💾 Speichern",
    secondary_actions=["❌ Abbrechen", "🔙 Zurück"]
)

if action == 'primary':
    # Speichern
    pass
elif action == 'abbrechen':
    # Abbrechen
    pass
```

#### **`render_two_button_footer()`**

Einfache 2-Button-Leiste.

```python
action = render_two_button_footer(
    confirm_label="✅ Bestätigen",
    cancel_label="❌ Abbrechen"
)
```

#### **`render_three_button_footer()`**

3-Button-Leiste.

```python
action = render_three_button_footer(
    primary_label="✅ Bestätigen",
    secondary_label="❌ Zurückweisen",
    cancel_label="🚫 Abbrechen"
)
```

---

## 🛡️ Validierung

### **PopupValidator**

Sammlung von Validierungs-Funktionen.

```python
from user.popups.core.popup_validators import PopupValidator

# Einzelne Validierungen
is_valid, error = PopupValidator.required("", "Name")
is_valid, error = PopupValidator.min_length("AB", 3, "Name")
is_valid, error = PopupValidator.is_email("test@example.com")
is_valid, error = PopupValidator.is_article_number("MG0001")

# Kombinierte Validierung
validator = PopupValidator.combine_validators(
    lambda v: PopupValidator.required(v, "Name"),
    lambda v: PopupValidator.min_length(v, 2, "Name")
)

is_valid, error = validator("John")
```

**Verfügbare Validatoren:**
- `required()` - Pflichtfeld
- `min_length()` / `max_length()` - String-Länge
- `min_value()` / `max_value()` - Zahlen-Bereich
- `in_range()` - Wertebereich
- `is_email()` - E-Mail-Validierung
- `is_date_in_past()` / `is_date_in_future()` - Datums-Validierung
- `matches_pattern()` - Regex-Pattern
- `is_article_number()` - Artikelnummer-Format
- `is_batch_number()` - Chargennummer-Format
- `one_of()` - Erlaubte Werte

---

## 📦 Session-State Management

### **PopupSessionManager**

Verhindert Session-State-Chaos durch strukturierte Keys.

```python
from user.popups.core.popup_session_manager import create_popup_session_manager

# Manager erstellen
manager = create_popup_session_manager(
    article_number="MG0001",
    batch_number="BATCH-123",
    popup_type="visual_inspection"
)

# Werte setzen/holen
manager.set('waste_quantity', 5)
waste = manager.get('waste_quantity')  # 5

# Prüfen
if manager.has('waste_quantity'):
    print("Existiert!")

# Cleanup
manager.cleanup()  # Entfernt alle Keys dieses Popups
```

---

## 🎨 Best Practices

### **1. Konsistente Namensgebung**

```python
# ✅ Gut
form.add_text_input("Mitarbeitername", "employee_name")
form.add_number_input("Ausschussmenge", "waste_quantity")

# ❌ Schlecht
form.add_text_input("Name", "n")
form.add_number_input("Menge", "qty")
```

### **2. Session-State Keys**

```python
# ✅ Gut - Nutze PopupSessionManager
manager = create_popup_session_manager(article, batch, "visual_inspection")
manager.set('waste_quantity', 5)

# ❌ Schlecht - Direkt in st.session_state
st.session_state['waste_qty'] = 5  # Kollisionsgefahr!
```

### **3. Validierung**

```python
# ✅ Gut - Frühe Validierung
def handle_primary_action(self, form_data):
    if not self.validate_form(form_data):
        return  # Stop bei Fehler

    # Speichern...

# ❌ Schlecht - Keine Validierung
def handle_primary_action(self, form_data):
    # Direkt speichern ohne Prüfung
    save_to_db(form_data)  # Kann fehlschlagen!
```

### **4. Error Handling**

```python
# ✅ Gut - Try-Catch mit User-Feedback
try:
    result = service.save_item(data)
    st.success("✅ Gespeichert!")
except Exception as e:
    st.error(f"❌ Fehler: {e}")
    logger.error(f"Save failed: {e}", exc_info=True)

# ❌ Schlecht - Keine Fehlerbehandlung
result = service.save_item(data)  # Crasht bei Fehler!
```

---

## 📖 Beispiele

Siehe Beispiel-Implementierungen:
- [visual_inspection.py](./visual_inspection.py) - Sichtkontrolle
- [measurement.py](./measurement.py) - Vermessung
- [data_confirmation.py](./data_confirmation.py) - Datenbestätigung

---

## 🔧 Development

### **Neues Popup erstellen**

1. Erbe von `InspectionPopup`
2. Implementiere `render_header()`, `render_body()`, `handle_primary_action()`
3. Optional: Override `render_footer()` für Custom-Buttons
4. Nutze Components aus `components/`
5. Teste mit verschiedenen Daten

### **Neue Component hinzufügen**

1. Erstelle Funktion in passendem `*_components.py`
2. Exportiere in `components/__init__.py`
3. Dokumentiere in diesem README
4. Schreibe Unit-Test

---

## ✅ Testing

```python
# Test mit Mock-Daten
test_item_data = {
    'article_number': 'MG0001',
    'batch_number': 'TEST-BATCH',
    'delivery_number': 'LS-001',
    'quantity': 100,
    'status': 'IN_PROGRESS'
}

@st.dialog("Test Popup")
def show_test_popup():
    popup = MyCustomPopup(test_item_data)
    popup.render()

show_test_popup()
```

---

## 📝 Changelog

**v1.0.0** (2025-01-09)
- Initial Release
- Base Popup Class
- 5 Component-Module
- Session-Management
- Validation Framework

---

**Fragen? Probleme?**
Siehe [INSPECTION_POPUP_REFACTORING_PLAN.md](../../../../INSPECTION_POPUP_REFACTORING_PLAN.md)
