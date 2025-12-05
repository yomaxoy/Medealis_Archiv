# Detaillierter Umsetzungsplan: ItemInfo-Dialog mit QR-Code Integration

**Datum**: 2025-12-04
**Ziel**: Separater Dialog für fehlende Artikel-Stammdaten zwischen AI-Extraktion und Datenbestätigung
**Features**: ItemInfo-Vervollständigung + QR-Code Upload + Artikel-Überspringen

---

## 📋 Übersicht: Was wird umgesetzt?

### **Hauptkomponenten:**
1. **Datenbank-Erweiterung** (QR-Code Spalte)
2. **Neue Dialog-Komponente** (ItemInfo-Dialog)
3. **Hilfs-Funktionen** (ItemInfo-Check, QR-Verarbeitung)
4. **Workflow-Integration** (Zwischen Extraktion und Bestätigung)
5. **UI-Anpassungen** (Session State Management)

### **Neuer Workflow:**
```
1. Lieferschein PDF hochladen
   ↓
2. Claude AI Extraktion (JSON)
   ↓
3. **NEU: ItemInfo-Existenz-Prüfung**
   ├─ Alle Artikel vorhanden? → Weiter zu Schritt 5
   └─ Fehlende Artikel? → Schritt 4
   ↓
4. **NEU: ItemInfo-Dialog**
   - Fehlende Artikel auflisten
   - Stammdaten vervollständigen
   - QR-Codes hochladen
   - Optional: Artikel überspringen
   - Speichern der ItemInfos
   ↓
5. Bestätigungs-Dialog (bestehend)
   - Lieferungs-Daten bearbeiten
   - Items bearbeiten/löschen
   ↓
6. Speicherung in Datenbank
   ↓
7. **NEU: System-Logging**
```

---

## 🗄️ Phase 1: Datenbank-Erweiterung

### **1.1 QR-Code Spalte zur ItemInfo-Tabelle hinzufügen**

**Betroffene Datei:** `src/warehouse/infrastructure/database/models/item_model.py`

**Änderungen am ItemInfoModel:**
- Neue Spalte `qr_code_image` vom Typ `LargeBinary` (speichert Bild-Bytes)
- Neue Spalte `qr_code_filename` vom Typ `String(255)` (speichert Original-Dateiname)
- Neue Spalte `qr_code_uploaded_at` vom Typ `DateTime` (Timestamp)
- Alle Spalten nullable=True (optional, da nicht immer vorhanden)

**Position:** Nach den bestehenden Feldern, vor den Relationships

**Begründung:**
- `LargeBinary`: PostgreSQL BYTEA-Typ, ideal für Bild-Speicherung
- Filename separat: Zum späteren Download mit korrektem Namen
- Timestamp: Audit-Trail, wann QR-Code hochgeladen wurde

### **1.2 Datenbank-Migration**

**Neue Datei erstellen:** `migration_scripts/02_add_qr_code_column.py`

**Migration durchführen:**
- Prüfen ob PostgreSQL läuft
- ALTER TABLE Statements für alle drei Spalten
- Test-Query ausführen (SELECT mit neuen Spalten)
- Rollback-Strategie dokumentieren

**Wichtig:**
- Migration muss idempotent sein (kann mehrfach ausgeführt werden ohne Fehler)
- Prüfung ob Spalten bereits existieren (IF NOT EXISTS Pattern)
- Logging der Migration (Success/Failure)

---

## 🎨 Phase 2: ItemInfo-Dialog Komponente

### **2.1 Neue Datei erstellen**

**Datei:** `src/warehouse/presentation/user/popups/iteminfo_completion_dialog.py`

**Struktur:**
```
iteminfo_completion_dialog.py
├─ show_iteminfo_completion_dialog()     # Haupt-Dialog Funktion
├─ render_article_form()                 # Formular für einen Artikel
├─ handle_qr_upload()                    # QR-Code Upload-Logik
├─ save_iteminfo_to_db()                 # Speicher-Funktion
├─ validate_iteminfo_fields()            # Validierung
└─ check_missing_iteminfos()             # Prüf-Funktion (Export)
```

### **2.2 Dialog-Funktion: show_iteminfo_completion_dialog()**

**Parameter:**
- `missing_articles`: Liste von Dicts mit {"article_number": "...", "description": "...", ...}

**UI-Struktur:**

**Header:**
- Titel: "📝 Artikel-Stammdaten vervollständigen"
- Warning-Box: "{Anzahl} Artikel sind noch nicht im System"
- Info-Text: Erklärung, warum Stammdaten benötigt werden

**Artikel-Auswahl:**
- **Falls nur 1 Artikel:** Direkt das Formular anzeigen (kein Tab)
- **Falls 2-5 Artikel:** Tabs verwenden (ein Tab pro Artikel)
- **Falls 6+ Artikel:** Dropdown-Auswahl + Einzelansicht (Performance-Optimierung)

**Session State für Dialog:**
- `iteminfo_form_data`: Dict mit allen eingegebenen Daten
- `articles_to_skip`: Set mit Artikelnummern, die übersprungen werden
- `qr_uploads`: Dict mit {article_number: file_data}
- `iteminfo_dialog_page`: Aktuelle Seite bei Pagination (falls >5 Artikel)

**Action-Buttons (Bottom):**
- **Primär-Button:** "✅ Stammdaten speichern" (type="primary")
  - Validiert alle Felder
  - Speichert ItemInfos in DB
  - Setzt Flag: `iteminfo_completed = True`
  - Schließt Dialog
  - Rerun

- **Sekundär-Button:** "❌ Abbrechen"
  - Schließt Dialog
  - Löscht Session State
  - Kehrt zum Scan-Dialog zurück
  - Rerun

### **2.3 Artikel-Formular: render_article_form()**

**Parameter:**
- `article`: Dict mit extrahierten Artikel-Daten
- `index`: Integer für eindeutige Widget-Keys

**Layout: 2-Spalten Design**

**Spalte 1 (Links):**
1. **Artikelnummer** (nicht editierbar, als st.info Box)
2. **Bezeichnung*** (Pflichtfeld, vorausgefüllt mit AI-Extraktion)
3. **Revisionsnummer** (Number Input, Default: 1)
4. **Zeichnungsnummer** (Text Input, optional)
5. **Lagerort** (Text Input, optional)

**Spalte 2 (Rechts):**
1. **Hersteller** (Text Input, optional)
2. **Material-Spezifikation** (Text Input, optional)
3. **Zusätzliche Beschreibung** (Text Area, optional, 3 Zeilen)

**Pflichtfeld-Validierung:**
- Nur "Bezeichnung" ist Pflicht
- Visuelles Feedback: Rote Border bei leerem Pflichtfeld
- Speichern-Button nur aktiv wenn alle Pflichtfelder gefüllt

**QR-Code Sektion (volle Breite unter den Spalten):**
- Separator-Linie (`st.write("---")`)
- Subheader: "**QR-Code (optional)**"
- File Uploader:
  - Akzeptierte Formate: PNG, JPG, JPEG
  - Max File Size: 5 MB
  - Help-Text: "Laden Sie ein vorhandenes QR-Code Bild hoch (max 5MB)"
  - Key: `iteminfo_qr_{article_number}`

**QR-Code Vorschau (falls hochgeladen):**
- 2-Spalten Layout:
  - Spalte 1 (20%): Thumbnail (100x100px)
  - Spalte 2 (80%):
    - Success-Message: "✅ QR-Code hochgeladen"
    - Dateiname anzeigen
    - Dateigröße anzeigen (KB)
    - "🗑️ QR-Code entfernen" Button

**Artikel-Überspringen Button:**
- Separator-Linie
- Warning-Button (rot): "🗑️ Artikel aus Lieferung entfernen"
- Bestätigungs-Dialog: "Wirklich entfernen? Artikel wird nicht übernommen."
- Bei Bestätigung:
  - Markiere in `articles_to_skip` Set
  - Entferne Tab/Formular
  - Rerun

### **2.4 QR-Upload Handler: handle_qr_upload()**

**Funktionalität:**
- Empfängt UploadedFile Objekt von Streamlit
- Validierung:
  - Dateigröße < 5 MB
  - Format PNG/JPG/JPEG
  - Ist valides Bild? (PIL.Image.open Test)
- Speichert in Session State: `st.session_state.qr_uploads[article_number] = file.getvalue()`
- Speichert Filename: `st.session_state.qr_filenames[article_number] = file.name`
- Return: Success/Error Dict

**Error Handling:**
- Zu große Datei: "Datei zu groß (max 5MB)"
- Ungültiges Format: "Ungültiges Bildformat"
- Korruptes Bild: "Bild kann nicht geladen werden"

### **2.5 Speicher-Funktion: save_iteminfo_to_db()**

**Prozess:**
1. **Sammle alle Daten** aus Session State (`iteminfo_form_data`)
2. **Iteriere über jeden Artikel** (außer die in `articles_to_skip`)
3. **Für jeden Artikel:**
   - Prüfe erneut ob ItemInfo bereits existiert (Race Condition vermeiden)
   - Falls existiert: Überspringen mit Warning-Log
   - Falls nicht existiert:
     - Erstelle ItemInfoModel Instanz
     - Setze alle Felder aus Form-Daten
     - Falls QR-Code in Session State:
       - Hole Binary-Daten aus `qr_uploads`
       - Setze `qr_code_image`, `qr_code_filename`, `qr_code_uploaded_at`
     - session.add(item_info)
4. **Commit Transaction**
5. **Bei Erfolg:**
   - Return: `{"success": True, "created_count": X, "skipped_count": Y}`
6. **Bei Fehler:**
   - Rollback
   - Log Exception
   - Return: `{"success": False, "error": str(e)}`

**Error Scenarios:**
- DB Connection Error → User-freundliche Meldung
- Constraint Violation (z.B. doppelte Artikelnummer) → Spezifische Meldung
- Timeout → "Bitte erneut versuchen"

### **2.6 Validierungs-Funktion: validate_iteminfo_fields()**

**Prüfungen pro Artikel:**
1. **Artikelnummer:** Nicht leer, max 7 Zeichen
2. **Bezeichnung:** Nicht leer (Pflichtfeld)
3. **Revisionsnummer:** >= 0 (falls angegeben)
4. **Zeichnungsnummer:** Max 100 Zeichen (falls angegeben)
5. **QR-Code:** Falls hochgeladen, valides Bild?

**Return:**
- Dict mit `{"valid": True/False, "errors": ["Fehler 1", "Fehler 2", ...]}`

**UI-Feedback:**
- Bei Fehler: Rote st.error Box mit allen Fehlern
- Bei Success: Grüne st.success Box

---

## 🔍 Phase 3: Hilfs-Funktionen

### **3.1 ItemInfo-Check Funktion**

**Funktion:** `check_missing_iteminfos(items_data: List[Dict]) -> List[Dict]`

**Datei:** `iteminfo_completion_dialog.py` (als exportierte Funktion)

**Logik:**
1. Öffne DB-Session
2. Für jeden Artikel in items_data:
   - Extrahiere `article_number`
   - Query: `session.get(ItemInfoModel, article_number)`
   - Falls None: Artikel zu missing_articles Liste hinzufügen
3. Return Liste aller fehlenden Artikel

**Performance-Optimierung:**
- Bei vielen Artikeln (>20): Bulk-Query statt einzelne Gets
- SQL: `SELECT article_number FROM item_info WHERE article_number IN (...)`
- Set-Differenz für fehlende Artikel

### **3.2 QR-Code Verarbeitungs-Funktionen**

**Funktion:** `process_qr_image(uploaded_file) -> bytes`

**Schritte:**
1. Lese File-Bytes
2. Öffne mit PIL.Image (Validierung)
3. Optional: Resize falls zu groß (>1000x1000px)
4. Optional: Konvertiere zu PNG (einheitliches Format)
5. Return: Prozessierte Bytes

**Funktion:** `get_qr_image_from_db(article_number: str) -> Optional[bytes]`

**Logik:**
- Query ItemInfo mit article_number
- Return qr_code_image Feld (oder None)

**Funktion:** `display_qr_code(qr_bytes: bytes)`

**Streamlit UI:**
- Konvertiere bytes zu PIL.Image
- Zeige mit st.image()
- Download-Button: "⬇️ QR-Code herunterladen"

---

## 🔗 Phase 4: Workflow-Integration

### **4.1 Änderungen in delivery_scan.py**

**Funktion:** `process_uploaded_delivery_file()`

**Position:** Nach Zeile 170 (Nach erfolgreicher AI-Extraktion)

**Neue Logik einfügen:**

1. **Extrahiere Items aus Result:**
   - Hole structured_data aus result
   - Extrahiere items Array

2. **Prüfe fehlende ItemInfos:**
   - Import: `from .iteminfo_completion_dialog import check_missing_iteminfos`
   - Call: `missing_articles = check_missing_iteminfos(items_data)`

3. **Entscheidung:**
   - **Falls missing_articles leer:**
     - Weiter wie bisher (Bestätigungs-Dialog zeigen)

   - **Falls missing_articles nicht leer:**
     - Speichere in Session State:
       - `st.session_state.missing_iteminfo_articles = missing_articles`
       - `st.session_state.extracted_delivery_data = result` (für später)
       - `st.session_state.show_iteminfo_dialog = True`
       - `st.session_state.show_scan_popup = False` (aktuellen Dialog schließen)
     - Rerun

### **4.2 Änderungen in main_user_view.py**

**Funktion:** `show_user_view()`

**Nach Zeile 58 (Nach Extraction Confirmation Popup Handler)**

**Neuer Handler einfügen:**

1. **ItemInfo-Dialog Handler:**
   - Prüfe: `if st.session_state.get("show_iteminfo_dialog")`
   - Falls True:
     - Import: `from warehouse.presentation.user.popups.iteminfo_completion_dialog import show_iteminfo_completion_dialog`
     - Call: `show_iteminfo_completion_dialog(st.session_state.missing_iteminfo_articles)`

2. **ItemInfo-Completion Handler:**
   - Prüfe: `if st.session_state.get("iteminfo_completed")`
   - Falls True:
     - Setze Flags:
       - `st.session_state.show_extraction_popup = True`
       - `st.session_state.show_iteminfo_dialog = False`
       - `st.session_state.iteminfo_completed = False`
     - Cleanup: Lösche `missing_iteminfo_articles` aus Session State
     - Rerun

**Fluss:**
```
ItemInfo-Dialog → User klickt "Speichern"
  → iteminfo_completed = True
    → Handler erkennt Flag
      → Öffnet Bestätigungs-Dialog
        → User bestätigt
          → Normale Speicherung
```

### **4.3 Session State Management**

**Neue Session State Keys:**

| Key | Typ | Zweck |
|-----|-----|-------|
| `show_iteminfo_dialog` | bool | Steuert ItemInfo-Dialog Anzeige |
| `missing_iteminfo_articles` | List[Dict] | Fehlende Artikel-Daten |
| `iteminfo_completed` | bool | Flag: ItemInfos wurden gespeichert |
| `iteminfo_form_data` | Dict | Formulardaten pro Artikel |
| `articles_to_skip` | Set | Artikelnummern zum Überspringen |
| `qr_uploads` | Dict | QR-Code Binary-Daten pro Artikel |
| `qr_filenames` | Dict | QR-Code Dateinamen |

**Cleanup-Strategie:**
- Bei Abbruch: Alle Keys löschen
- Bei Erfolg: Alle Keys außer `extracted_delivery_data` löschen
- Bei Dialog-Wechsel: Nur relevante Keys behalten

---

## 🎨 Phase 5: UI/UX Details

### **5.1 Design-Konsistenz**

**Farben:**
- Primary Button: Streamlit Standard (Blau)
- Warning Button: Rot (für Löschen/Überspringen)
- Success Messages: Grün
- Info Messages: Blau
- Error Messages: Rot

**Icons:**
- ✅ Erfolg
- ❌ Fehler/Abbrechen
- 📝 Bearbeiten
- 🗑️ Löschen
- ⬆️ Upload
- ⬇️ Download
- 📋 Liste
- 🔍 Prüfung

### **5.2 Responsives Layout**

**Desktop (>1200px):**
- 2-Spalten Formular
- Tabs nebeneinander
- QR-Vorschau 150x150px

**Tablet (768-1200px):**
- 2-Spalten Formular (schmaler)
- Tabs gestapelt
- QR-Vorschau 120x120px

**Mobile (<768px):**
- 1-Spalte Formular
- Dropdowns statt Tabs
- QR-Vorschau 100x100px

**Streamlit-Lösung:**
- Verwende `st.columns()` mit relativen Breiten
- Dynamische Anpassung durch Streamlit

### **5.3 Benutzerführung**

**Tooltips (help-Parameter):**
- Bezeichnung: "Name des Artikels wie in Katalog/Zeichnung"
- Revisionsnummer: "Aktuelle Revisionsstand der Zeichnung"
- QR-Code Upload: "Laden Sie ein vorhandenes QR-Code Bild hoch (max 5MB)"

**Fortschritts-Anzeige:**
- Bei vielen Artikeln (>5): "Artikel 1 von 10 vervollständigt"
- Progress Bar: `st.progress(completed / total)`

**Warnungen:**
- "⚠️ Pflichtfelder müssen ausgefüllt werden"
- "⚠️ Artikel ohne Stammdaten werden nicht übernommen"
- "⚠️ QR-Code ist optional, aber empfohlen"

---

## 🧪 Phase 6: Testing & Validierung

### **6.1 Unit-Tests**

**Test-Datei:** `tests/test_iteminfo_completion_dialog.py`

**Test-Cases:**
1. **test_check_missing_iteminfos_all_exist:** Alle Artikel vorhanden → Leere Liste
2. **test_check_missing_iteminfos_none_exist:** Keine Artikel vorhanden → Alle in Liste
3. **test_check_missing_iteminfos_partial:** Mix → Nur fehlende in Liste
4. **test_validate_iteminfo_fields_valid:** Alle Felder korrekt → valid=True
5. **test_validate_iteminfo_fields_invalid:** Leere Bezeichnung → valid=False
6. **test_save_iteminfo_to_db_success:** Erfolgreiche Speicherung
7. **test_save_iteminfo_to_db_duplicate:** Artikelnummer bereits vorhanden → Skip
8. **test_qr_upload_valid:** Valides Bild → Success
9. **test_qr_upload_too_large:** >5MB → Error
10. **test_qr_upload_invalid_format:** .txt File → Error

### **6.2 Integrations-Tests**

**Test-Szenarien:**
1. **Happy Path:**
   - Scan → 3 neue Artikel → ItemInfo-Dialog → Ausfüllen → Speichern → Bestätigung → DB-Check
2. **Skip Artikel:**
   - Scan → 2 neue Artikel → 1 überspringen → Nur 1 in DB
3. **QR-Code Upload:**
   - Scan → 1 neuer Artikel → QR hochladen → In DB gespeichert → Wieder abrufbar
4. **Abbruch:**
   - Scan → ItemInfo-Dialog → Abbrechen → Keine DB-Änderungen
5. **Validierungs-Fehler:**
   - Scan → ItemInfo-Dialog → Leere Bezeichnung → Error → Korrektur → Success

### **6.3 Manuelle Test-Checkliste**

**Vor Go-Live prüfen:**
- [ ] QR-Code Spalte in DB vorhanden
- [ ] Migration erfolgreich durchgeführt
- [ ] ItemInfo-Dialog öffnet bei fehlenden Artikeln
- [ ] Dialog überspringt wenn alle Artikel vorhanden
- [ ] Alle Formular-Felder speichern korrekt
- [ ] QR-Code Upload funktioniert (PNG, JPG)
- [ ] QR-Code Vorschau wird angezeigt
- [ ] QR-Code wird in DB gespeichert
- [ ] QR-Code kann wieder abgerufen werden
- [ ] Artikel überspringen funktioniert
- [ ] Validierung zeigt Fehler korrekt an
- [ ] Success-Message erscheint nach Speicherung
- [ ] Workflow führt zu Bestätigungs-Dialog
- [ ] Finale Speicherung in DB erfolgreich
- [ ] Session State wird korrekt aufgeräumt
- [ ] Performance bei 10+ Artikeln okay
- [ ] UI responsive auf verschiedenen Bildschirmgrößen

---

## 📦 Phase 7: Deployment & Rollout

### **7.1 Deployment-Schritte**

**Reihenfolge (wichtig!):**

1. **Datenbank-Migration** (ZUERST!)
   - Stoppe Container: `docker-compose down`
   - Migration ausführen: `python migration_scripts/02_add_qr_code_column.py`
   - Prüfe Migration: `SELECT column_name FROM information_schema.columns WHERE table_name = 'item_info';`
   - Erwartung: `qr_code_image`, `qr_code_filename`, `qr_code_uploaded_at` vorhanden

2. **Code-Deployment:**
   - Git commit aller neuen/geänderten Dateien
   - Docker Images neu bauen: `docker-compose build --no-cache`
   - Container starten: `docker-compose up -d`

3. **Funktionstests:**
   - Testuser einloggen
   - Test-Lieferschein mit neuen Artikeln scannen
   - ItemInfo-Dialog sollte erscheinen
   - Testdaten eingeben + QR hochladen
   - Erfolg prüfen in DB

4. **Rollback-Plan** (falls Probleme):
   - Container stoppen
   - Alte Docker Images verwenden
   - DB-Rollback: `ALTER TABLE item_info DROP COLUMN qr_code_image;` (etc.)
   - Alte Container starten

### **7.2 Monitoring nach Deployment**

**Zu überwachen:**
- Logs auf Fehler prüfen: `docker-compose logs -f medealis-user | grep ERROR`
- Performance: Sind Dialoge schnell genug? (<2s Ladezeit)
- DB-Größe: Wächst DB durch QR-Codes stark? (Monitoring)
- User-Feedback: Gibt es Usability-Probleme?

### **7.3 Dokumentation aktualisieren**

**Dateien zu updaten:**
- `PROZESSBESCHREIBUNG_WARENEINGANG.md` (neuer Workflow-Schritt einfügen)
- `UML_ABLAUF_LIEFERSCHEIN_SCAN.md` (ItemInfo-Dialog hinzufügen)
- README.md (Features-Liste erweitern)
- CHANGELOG.md (neues Feature dokumentieren)

---

## 📊 Zusammenfassung: Änderungsliste

### **Neue Dateien:**
1. `src/warehouse/presentation/user/popups/iteminfo_completion_dialog.py` (Haupt-Dialog)
2. `migration_scripts/02_add_qr_code_column.py` (DB-Migration)
3. `tests/test_iteminfo_completion_dialog.py` (Tests - optional)

### **Geänderte Dateien:**
1. `src/warehouse/infrastructure/database/models/item_model.py` (QR-Spalten)
2. `src/warehouse/presentation/user/popups/delivery_scan.py` (ItemInfo-Check)
3. `src/warehouse/presentation/user/views/main_user_view.py` (Dialog-Handler)

### **Geschätzter Aufwand:**

| Phase | Aufgabe | Zeit |
|-------|---------|------|
| 1 | DB-Migration | 30 Min |
| 2 | Dialog-Komponente | 3 Std |
| 3 | Hilfs-Funktionen | 1 Std |
| 4 | Workflow-Integration | 1 Std |
| 5 | UI/UX Feinschliff | 1 Std |
| 6 | Testing | 1 Std |
| 7 | Deployment | 30 Min |
| **Gesamt** | | **~8 Stunden** |

---

## ✅ Definition of Done

**Feature gilt als fertig wenn:**
- [ ] QR-Code Spalten in Datenbank vorhanden
- [ ] Migration erfolgreich durchgeführt und dokumentiert
- [ ] ItemInfo-Dialog funktioniert für 1, 5, und 10+ Artikel
- [ ] QR-Code Upload, Speicherung und Anzeige funktioniert
- [ ] Artikel können übersprungen werden
- [ ] Validierung funktioniert (Pflichtfelder, Dateigrößen)
- [ ] Workflow-Integration nahtlos (Scan → ItemInfo → Bestätigung → Speichern)
- [ ] Session State wird korrekt verwaltet (keine Memory Leaks)
- [ ] Error Handling für alle bekannten Fehler-Szenarien
- [ ] UI ist responsive und benutzerfreundlich
- [ ] Manuelle Tests alle erfolgreich
- [ ] Docker Container mit neuem Code laufen stabil
- [ ] Dokumentation aktualisiert
- [ ] User-Acceptance Test bestanden

---

## 🚀 Bereit für Go?

**Wenn Sie "Go" geben, werde ich:**

1. **Zuerst:** DB-Migration durchführen (QR-Spalten)
2. **Dann:** ItemInfo-Dialog Komponente erstellen
3. **Danach:** Hilfs-Funktionen implementieren
4. **Anschließend:** Workflow integrieren
5. **Zum Schluss:** Docker neu bauen & testen

**Geschätzte Reihenfolge der Commits:**
1. "feat: Add QR-Code columns to item_info table (DB migration)"
2. "feat: Add ItemInfo completion dialog component"
3. "feat: Integrate ItemInfo dialog into delivery scan workflow"
4. "test: Add manual test checklist for ItemInfo dialog"
5. "docs: Update process documentation with ItemInfo dialog"

**Bereit für Umsetzung?** 🎯

---

**Erstellt**: 2025-12-04
**Autor**: Claude (AI-Assistent)
**Status**: Warte auf Go für Implementierung
