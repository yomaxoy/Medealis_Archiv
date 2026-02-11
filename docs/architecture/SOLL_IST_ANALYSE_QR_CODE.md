# SOLL-IST Analyse: QR-Code Integration & Lieferschein-Prozess

**Datum**: 2025-12-04
**Fokus**: Prozess 1 (Lieferschein-Scan) und QR-Code Feature

---

## 📊 SOLL-Szenario (Gewünscht)

### **Prozess 1: Lieferschein scannen (NEU)**

1. **Lieferschein-Scan & AI-Auswertung** ✓ (wie aktuell)
   - PDF hochladen
   - Claude AI/OCR Extraktion
   - JSON-Response erhalten

2. **ItemInfo-Prüfung** ❌ (NEU - fehlt aktuell)
   - System prüft: Sind Artikelnummern bereits in `item_info` Tabelle vorhanden?
   - **Falls NICHT vorhanden**:
     - Dialog öffnet sich mit Liste aller fehlenden Artikelnummern
     - Für jeden fehlenden Artikel:
       - ItemInfo-Felder vervollständigen (Designation, Hersteller, etc.)
       - **QR-Code hochladen/erstellen** (NEU)
       - Speichern oder
       - Artikel aus Lieferung löschen (wenn nicht übernehmen)

3. **Datenbestätigung** ✓ (vorhanden, evtl. erweitern)
   - Übersicht mit allen extrahierten Daten
   - Bearbeiten/Löschen/Speichern möglich

4. **Speicher-Feedback** ⚠️ (teilweise vorhanden)
   - **Falls Erfolg**: Messagebox mit Erfolgsmeldung
   - **Falls Fehler**: Fehlermeldung mit Details

5. **System-Logging** ❌ (NEU - fehlt komplett)
   - Log-Datei: `Systemlogs.txt`
   - Format: `Date - Time - "Lieferschein Scan" - {Delivery Info}{Artikel Info 1, ..., Artikel Info n}`

---

## 🔍 IST-Zustand (Aktuelle Implementierung)

### **Was funktioniert bereits:**

#### ✅ **1. Lieferschein-Scan & AI-Auswertung**
**Datei**: `delivery_scan.py::process_uploaded_delivery_file()`
- PDF-Upload ✓
- Claude API Integration ✓
- JSON-Extraktion ✓
- Storage-Check vor Upload ✓

#### ✅ **2. Bestätigungs-Dialog**
**Datei**: `delivery_scan.py::show_extraction_confirmation_popup()`
- Zeigt extrahierte Daten (Lieferung + Items) ✓
- Bearbeiten von Feldern:
  - Lieferscheinnummer ✓
  - Lieferant ✓
  - Lieferdatum ✓
  - Bearbeiter ✓
  - Items (Artikelnummer, Charge, Menge, Bestellnr.) ✓
- Artikel löschen (🗑️ Button) ✓
- Neue Artikel hinzufügen (➕ Button) ✓

#### ✅ **3. Speicher-Logik**
**Datei**: `main_user_view.py::handle_extraction_confirmation()`
- Ruft `delivery_service.create_delivery_from_extraction()` auf ✓
- Zeigt Erfolgs-/Fehlermeldung ✓
- Session State Cleanup ✓

#### ⚠️ **4. DB-Speicherung**
**Datei**: `delivery_service.py::create_delivery_from_extraction()`
- Supplier-Mapping/Erstellung ✓
- Delivery-Erstellung ✓
- Item-Erstellung über `item_service.create_item()` ✓
- **ABER**: Keine ItemInfo-Prüfung vorher!

---

### **Was fehlt:**

#### ❌ **1. ItemInfo-Prüfung vor Speicherung**
**Problem**:
- System erstellt Items sofort nach Bestätigung
- Keine Prüfung, ob `item_info` bereits existiert
- Keine Möglichkeit, ItemInfo-Stammdaten **vor** der Item-Erstellung zu vervollständigen

**Aktueller Ablauf**:
```
User bestätigt → create_delivery_from_extraction()
  → create_item()
    → Prüft ItemInfo
      → Falls nicht vorhanden: Erstellt ItemInfo MIT Minimal-Daten (nur designation)
```

**Problem**: ItemInfo wird **automatisch** mit unvollständigen Daten erstellt!

#### ❌ **2. QR-Code Spalte & Upload**
**Problem**:
- `item_info` Tabelle hat **keine** `qr_code_image` Spalte
- Kein Dialog zum Hochladen von QR-Codes
- Keine QR-Code-Anzeige in der UI

#### ❌ **3. System-Logging**
**Problem**:
- Keine Log-Datei `Systemlogs.txt`
- Nur Application-Logs (Python logging), aber nicht als strukturierte TXT-Datei
- Kein Format: `Date - Time - "Lieferschein Scan" - {...}`

#### ❌ **4. Fehlende ItemInfo-Vervollständigungs-Dialog**
**Problem**:
- Kein separater Dialog für:
  - Fehlende Artikelnummern auflisten
  - ItemInfo-Felder editieren (Designation, Hersteller, Zeichnung, Lagerort, etc.)
  - QR-Code hochladen

---

## 🔄 Unterschiede SOLL vs. IST

| Feature | SOLL | IST | Status |
|---------|------|-----|--------|
| **1. Lieferschein-Scan** | ✓ | ✓ | ✅ Vorhanden |
| **2. ItemInfo-Prüfung** | ✓ Vor Speicherung | ❌ Keine Prüfung | ❌ Fehlt |
| **3. ItemInfo-Dialog** | ✓ Für fehlende Artikel | ❌ Kein Dialog | ❌ Fehlt |
| **4. QR-Code Upload** | ✓ Im ItemInfo-Dialog | ❌ Keine Spalte/UI | ❌ Fehlt |
| **5. Datenbestätigung** | ✓ | ✓ | ✅ Vorhanden |
| **6. Artikel löschen** | ✓ | ✓ | ✅ Vorhanden |
| **7. Erfolgs-Messagebox** | ✓ | ✓ | ✅ Vorhanden |
| **8. Fehler-Messagebox** | ✓ | ⚠️ Teilweise | ⚠️ Verbesserbar |
| **9. System-Logging (TXT)** | ✓ | ❌ Keine TXT-Datei | ❌ Fehlt |

---

## 💡 Umsetzungsvorschläge

### **Vorschlag 1: Minimale Integration (Quick Win)**

**Idee**: ItemInfo-Prüfung direkt im bestehenden Bestätigungs-Dialog integrieren

**Änderungen**:
1. **Erweitere `show_extraction_confirmation_popup()`**:
   ```python
   # Nach Zeile 208 (items_data = delivery_data.get("items", []))

   # Prüfe ItemInfo-Existenz
   missing_item_infos = check_missing_item_infos(items_data)

   if missing_item_infos:
       st.warning(f"⚠️ {len(missing_item_infos)} Artikel noch nicht im System!")

       # Expandable Section für fehlende Artikel
       with st.expander("📝 Fehlende Artikel-Stammdaten vervollständigen", expanded=True):
           for article_number in missing_item_infos:
               st.write(f"### {article_number}")
               # Input-Felder für ItemInfo
               designation = st.text_input("Bezeichnung", key=f"des_{article_number}")
               manufacturer = st.text_input("Hersteller", key=f"man_{article_number}")
               # QR-Code Upload
               qr_file = st.file_uploader("QR-Code", type=["png","jpg"], key=f"qr_{article_number}")

               if st.button("Artikel überspringen", key=f"skip_{article_number}"):
                   # Entferne aus items_data
                   items_data = [i for i in items_data if i['article_number'] != article_number]
   ```

**Vorteil**:
- ✅ Schnell umsetzbar
- ✅ Keine neue Dialog-Komponente
- ✅ Nutzt bestehenden Flow

**Nachteil**:
- ❌ UI wird sehr lang bei vielen fehlenden Artikeln
- ❌ Weniger übersichtlich

---

### **Vorschlag 2: Separater ItemInfo-Dialog (Empfohlen)**

**Idee**: Neuer Dialog zwischen AI-Extraktion und Datenbestätigung

**Neuer Workflow**:
```
1. Lieferschein scannen
   ↓
2. AI-Extraktion (JSON)
   ↓
3. **NEU: ItemInfo-Check & Dialog** ← Wenn fehlende Artikel
   ↓
4. Datenbestätigung (bestehender Dialog)
   ↓
5. Speichern
```

**Implementation**:

**Neue Datei**: `delivery_scan_iteminfo_dialog.py`

```python
@st.dialog("📝 Artikel-Stammdaten vervollständigen", width="large")
def show_missing_iteminfo_dialog(missing_articles: List[Dict]):
    """
    Zeigt Dialog für fehlende ItemInfo-Stammdaten.

    Args:
        missing_articles: Liste von Artikeln ohne ItemInfo
        Format: [{"article_number": "CT0003", "description": "..."}, ...]
    """
    st.write("### ⚠️ Folgende Artikel sind noch nicht im System:")
    st.info(f"Bitte vervollständigen Sie die Stammdaten für {len(missing_articles)} Artikel")

    # Tabs für jeden Artikel
    if len(missing_articles) > 1:
        tabs = st.tabs([art["article_number"] for art in missing_articles])

        for i, (tab, article) in enumerate(zip(tabs, missing_articles)):
            with tab:
                show_iteminfo_form(article, i)
    else:
        show_iteminfo_form(missing_articles[0], 0)

    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Stammdaten speichern", type="primary", use_container_width=True):
            # Speichere alle ItemInfos
            save_all_iteminfos()
            st.session_state.iteminfo_completed = True
            st.session_state.show_iteminfo_dialog = False
            st.rerun()

    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.show_iteminfo_dialog = False
            st.rerun()


def show_iteminfo_form(article: Dict, index: int):
    """Zeigt Formular für einen Artikel."""
    st.write(f"**Artikelnummer:** {article['article_number']}")

    # Extrahierte Beschreibung als Vorausfüllung
    default_desc = article.get("description", "")

    # ItemInfo Felder
    col1, col2 = st.columns(2)
    with col1:
        designation = st.text_input(
            "Bezeichnung *",
            value=default_desc,
            key=f"iteminfo_designation_{index}"
        )
        revision = st.number_input(
            "Revisionsnummer",
            min_value=0,
            value=1,
            key=f"iteminfo_revision_{index}"
        )
        storage_location = st.text_input(
            "Lagerort",
            key=f"iteminfo_storage_{index}"
        )

    with col2:
        manufacturer = st.text_input(
            "Hersteller",
            key=f"iteminfo_manufacturer_{index}"
        )
        drawing_ref = st.text_input(
            "Zeichnungsnummer",
            key=f"iteminfo_drawing_{index}"
        )
        material = st.text_input(
            "Material-Spezifikation",
            key=f"iteminfo_material_{index}"
        )

    # QR-Code Upload (NEU)
    st.write("---")
    st.write("**QR-Code (optional)**")
    qr_file = st.file_uploader(
        "QR-Code Bild hochladen",
        type=["png", "jpg", "jpeg"],
        key=f"iteminfo_qr_{index}",
        help="Laden Sie ein vorhandenes QR-Code Bild hoch"
    )

    if qr_file:
        # Vorschau
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(qr_file, width=100)
        with col2:
            st.success(f"✅ QR-Code hochgeladen: {qr_file.name}")

    # Option: Artikel überspringen
    st.write("---")
    if st.button(
        "🗑️ Artikel aus Lieferung entfernen",
        key=f"iteminfo_skip_{index}",
        help="Artikel wird nicht in die Lieferung übernommen"
    ):
        # Markiere zum Entfernen
        if "articles_to_skip" not in st.session_state:
            st.session_state.articles_to_skip = set()
        st.session_state.articles_to_skip.add(article["article_number"])
        st.rerun()
```

**Integration in `process_uploaded_delivery_file()`**:

```python
# Nach Zeile 150 (if result:)
# Füge hinzu:

# Check for missing ItemInfos
items_data = result.get("structured_data", {}).get("items", [])
missing_articles = check_missing_iteminfos(items_data)

if missing_articles:
    # Store for ItemInfo dialog
    st.session_state.missing_iteminfo_articles = missing_articles
    st.session_state.show_iteminfo_dialog = True
    st.session_state.show_scan_popup = False
    st.rerun()
else:
    # Proceed to confirmation as before
    st.session_state.show_extraction_popup = True
```

**Hilfsfunktion**:

```python
def check_missing_iteminfos(items_data: List[Dict]) -> List[Dict]:
    """
    Prüft, welche Artikel noch keine ItemInfo haben.

    Returns:
        Liste von Artikeln ohne ItemInfo
    """
    from warehouse.infrastructure.database.models import ItemInfoModel
    from warehouse.infrastructure.database.connection import get_session

    missing = []
    with get_session() as session:
        for item in items_data:
            article_number = item.get("article_number")
            if not article_number:
                continue

            # Prüfe ob ItemInfo existiert
            item_info = session.get(ItemInfoModel, article_number)
            if not item_info:
                missing.append(item)

    return missing
```

**Vorteil**:
- ✅ Übersichtliche UI (Tabs pro Artikel)
- ✅ Klare Trennung der Prozess-Schritte
- ✅ Skalierbar für viele Artikel
- ✅ QR-Code Upload integriert

**Nachteil**:
- ⚠️ Mehr Implementierungsaufwand
- ⚠️ Zusätzlicher Dialog-Schritt

---

### **Vorschlag 3: QR-Code Spalte in Datenbank**

**DB-Migration erforderlich**:

```python
# Migration Script
from sqlalchemy import Column, LargeBinary
from warehouse.infrastructure.database.models import ItemInfoModel

# Füge Spalte hinzu
ALTER TABLE item_info ADD COLUMN qr_code_image BYTEA;
```

**Oder in SQLAlchemy Model** (`item_model.py`):

```python
class ItemInfoModel(Base):
    __tablename__ = "item_info"

    article_number = Column(String(7), primary_key=True)
    designation = Column(Text, nullable=True)
    # ... existing fields ...

    # NEU: QR-Code Spalte
    qr_code_image = Column(LargeBinary, nullable=True)  # Speichert Bild als BLOB
    qr_code_filename = Column(String(255), nullable=True)  # Original-Dateiname
```

**Speicher-Logik**:

```python
def save_iteminfo_with_qr(article_number, designation, qr_file):
    """Speichert ItemInfo mit QR-Code."""
    from warehouse.infrastructure.database.connection import get_session
    from warehouse.infrastructure.database.models import ItemInfoModel

    with get_session() as session:
        # QR-Code als Binary lesen
        qr_data = qr_file.read() if qr_file else None

        item_info = ItemInfoModel(
            article_number=article_number,
            designation=designation,
            qr_code_image=qr_data,
            qr_code_filename=qr_file.name if qr_file else None
        )

        session.add(item_info)
        session.commit()
```

**Anzeige in UI**:

```python
# In Artikel-Details-View
if item_info.qr_code_image:
    import io
    from PIL import Image

    qr_image = Image.open(io.BytesIO(item_info.qr_code_image))
    st.image(qr_image, width=200, caption="QR-Code")
else:
    st.info("Kein QR-Code vorhanden")
```

---

### **Vorschlag 4: System-Logging (TXT-Datei)**

**Neue Datei**: `system_logger.py`

```python
# src/warehouse/shared/logging/system_logger.py

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class SystemLogger:
    """
    System-Logger für strukturierte TXT-Log-Datei.

    Format: Date - Time - "Event" - {Data}
    """

    def __init__(self, log_file: str = "Systemlogs.txt"):
        """
        Initialize logger.

        Args:
            log_file: Pfad zur Log-Datei
        """
        # Standard: Logs im data/ Verzeichnis
        self.log_dir = Path("data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_file

    def log_event(self, event_name: str, data: Dict[str, Any]):
        """
        Loggt ein Event mit Daten.

        Args:
            event_name: Name des Events (z.B. "Lieferschein Scan")
            data: Daten als Dictionary
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")

        # Konvertiere Data zu JSON
        data_json = json.dumps(data, ensure_ascii=False, default=str)

        # Format: Date - Time - "Event" - {Data}
        log_entry = f'{date_str} - {time_str} - "{event_name}" - {data_json}\n'

        # Append to file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def log_delivery_scan(self, delivery_data: Dict, items_data: List[Dict]):
        """
        Spezielle Methode für Lieferschein-Scan.

        Args:
            delivery_data: Lieferungs-Daten
            items_data: Liste von Artikel-Daten
        """
        log_data = {
            "Delivery": {
                "number": delivery_data.get("delivery_number"),
                "supplier": delivery_data.get("supplier_name"),
                "date": delivery_data.get("delivery_date"),
                "employee": delivery_data.get("employee_name")
            },
            "Items": [
                {
                    "article_number": item.get("article_number"),
                    "batch_number": item.get("batch_number"),
                    "quantity": item.get("quantity"),
                    "order_number": item.get("order_number")
                }
                for item in items_data
            ]
        }

        self.log_event("Lieferschein Scan", log_data)

# Global instance
system_logger = SystemLogger()
```

**Integration**:

```python
# In handle_extraction_confirmation() (main_user_view.py)
# Nach Zeile 497 (result = delivery_service.create_delivery_from_extraction...)

if result.get("success"):
    # System-Log schreiben
    from warehouse.shared.logging.system_logger import system_logger

    system_logger.log_delivery_scan(
        delivery_data=extraction_data,
        items_data=extraction_data.get("items", [])
    )

    # Erfolgs-Meldung (wie bisher)
    st.success(...)
```

**Beispiel-Log-Eintrag**:

```
2025-12-04 - 14:32:15 - "Lieferschein Scan" - {"Delivery": {"number": "LS24-077", "supplier": "Primec", "date": "2024-06-11", "employee": "Max Mustermann"}, "Items": [{"article_number": "CT0003", "batch_number": "P-153520240417", "quantity": 107, "order_number": "10170"}, {"article_number": "CT0004", "batch_number": "P-153620240418", "quantity": 54, "order_number": "10170"}]}
```

---

## 🎯 Empfohlene Umsetzungsreihenfolge

### **Phase 1: Basis-Features (Priorität HOCH)**

1. **QR-Code Spalte zu Datenbank hinzufügen** (30 Min)
   - Migration Script erstellen
   - ItemInfoModel erweitern
   - DB migrieren

2. **ItemInfo-Check Funktion** (1 Std)
   - `check_missing_iteminfos()` implementieren
   - In `process_uploaded_delivery_file()` integrieren

3. **System-Logger implementieren** (1 Std)
   - `system_logger.py` erstellen
   - In `handle_extraction_confirmation()` integrieren
   - Testen

### **Phase 2: ItemInfo-Dialog (Priorität MITTEL)**

4. **ItemInfo-Dialog erstellen** (3-4 Std)
   - `delivery_scan_iteminfo_dialog.py` erstellen
   - Formular für ItemInfo-Felder
   - QR-Code Upload-Funktion
   - Artikel-Überspringen-Funktion

5. **Dialog-Integration** (1 Std)
   - In Workflow zwischen Extraktion und Bestätigung integrieren
   - Session State Management

### **Phase 3: UI-Verbesserungen (Priorität NIEDRIG)**

6. **QR-Code Anzeige** (1 Std)
   - In Artikel-Details-View QR-Code anzeigen
   - Download-Funktion

7. **Fehlermeldungen verbessern** (30 Min)
   - Detailliertere Fehlermeldungen
   - Error-Logging

---

## 📝 Zusammenfassung

**IST-Zustand**:
- ✅ Lieferschein-Scan funktioniert
- ✅ Bestätigungs-Dialog vorhanden
- ✅ Artikel löschen möglich
- ❌ **Keine ItemInfo-Prüfung vor Speicherung**
- ❌ **Keine QR-Code Spalte/Upload**
- ❌ **Kein System-Logging (TXT)**

**SOLL-Zustand**:
- ItemInfo-Prüfung mit separatem Dialog
- QR-Code Upload & Speicherung
- System-Logging in TXT-Datei

**Empfehlung**: **Vorschlag 2** (Separater ItemInfo-Dialog) + **Vorschlag 3** (QR-Code Spalte) + **Vorschlag 4** (System-Logging)

**Geschätzter Aufwand**: ~8-10 Stunden

---

**Erstellt**: 2025-12-04
**Autor**: Claude (AI-Assistent)
