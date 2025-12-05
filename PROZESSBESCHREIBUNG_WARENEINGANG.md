# Prozessbeschreibung: Medealis Wareneingang-System

**Version**: 1.0
**Datum**: 2025-12-04
**System**: Medealis Warehouse Management
**Technologie**: Python, PostgreSQL, Claude AI, Docker

---

## 📋 Inhaltsverzeichnis

1. [Prozess 1: Lieferschein-Scan](#prozess-1-lieferschein-scan)
2. [Prozess 2: Kompletter Wareneingang](#prozess-2-kompletter-wareneingang)
3. [Systemarchitektur](#systemarchitektur)
4. [Datenfluss](#datenfluss)
5. [Qualitätssicherung](#qualitätssicherung)

---

## Prozess 1: Lieferschein-Scan

### **Ziel**
Automatisierte Erfassung von Lieferschein-Daten mittels künstlicher Intelligenz (Claude AI) zur Vermeidung manueller Eingabefehler und Zeitersparnis.

### **Ablauf im Detail**

#### **Phase 1: Upload und Vorbereitung**
Der Mitarbeiter öffnet in der User-Anwendung (Port 8502) den Dialog "Lieferschein scannen" und lädt eine PDF-Datei oder ein Bild (PNG, JPG, JPEG, TIFF) hoch. Das System prüft automatisch:
- Ist der Claude API-Key verfügbar?
- Ist OCR (Tesseract) installiert?
- Ist mindestens eine Speicheroption verfügbar (Server 10.190.140.10, lokaler Speicher, oder SharePoint)?

Falls keine Speicheroption verfügbar ist, wird der Upload mit einer Fehlermeldung abgebrochen, um Datenverlust zu vermeiden.

#### **Phase 2: AI-Datenextraktion**
Nach Klick auf "OCR + Claude Analyse" startet ein mehrstufiger Verarbeitungsprozess:

**Schritt 1 (25%)**: Das System liest die hochgeladene Datei und erstellt eine temporäre Arbeitskopie im `/tmp` Verzeichnis.

**Schritt 2 (50%)**: Die Datei wird an die Claude AI (Model: claude-sonnet-4-20250514) gesendet. Falls Tesseract OCR verfügbar ist, wird zuerst eine Textextraktion durchgeführt, um die Qualität der AI-Analyse zu verbessern. Claude analysiert das Dokument und extrahiert strukturiert folgende Informationen:
- Lieferscheinnummer (z.B. "LS24-077")
- Lieferantenname (z.B. "Primec")
- Lieferdatum (Format: DD.MM.YYYY)
- Liste aller Artikel mit:
  - Artikelnummer
  - Chargennummer
  - Menge
  - Beschreibung/Bezeichnung
  - Bestellnummer (falls vorhanden)

Die Antwort kommt als strukturiertes JSON zurück, was eine automatische Weiterverarbeitung ermöglicht.

**Schritt 3 (75%)**: Das System speichert das Original-PDF im Dokumentenverzeichnis unter folgendem Pfad:
```
/Wareneingang/[Lieferant]/Lieferscheine/Lieferschein_[Lieferant]_[LS-Nr]_[Datum].pdf
```

Parallel normalisiert das System den Lieferantennamen (z.B. "Primec" → "PRIMEC") für konsistente Datenbankeinträge.

**Schritt 4 (100%)**: Die extrahierten Daten werden in der Session gespeichert und dem Benutzer in einem Bestätigungsdialog angezeigt.

#### **Phase 3: Datenbestätigung und Bearbeitung**
Der Mitarbeiter sieht nun alle extrahierten Informationen in einem bearbeitbaren Formular:

**Kopfzeile-Daten**:
- Lieferscheinnummer (editierbar)
- Lieferant (editierbar)
- Lieferdatum (editierbar)
- Bearbeiter (vorausgefüllt mit Benutzername)
- Notizen (optional)

**Artikel-Tabelle**:
Jeder extrahierte Artikel erscheint als Zeile mit:
- Artikelnummer
- Chargennummer
- Menge
- Beschreibung
- Bestellnummer

Der Mitarbeiter kann:
- Einzelne Felder korrigieren (bei AI-Fehlern)
- Fehlerhafte Artikel aus der Liste löschen
- Fehlende Artikel manuell hinzufügen

Diese Kontrollmöglichkeit ist wichtig, da AI-Systeme nicht 100% fehlerfrei arbeiten, insbesondere bei handgeschriebenen Lieferscheinen oder schlechter Scan-Qualität.

#### **Phase 4: Datenbankintegration**
Nach Klick auf "Speichern" startet die Datenbank-Transaktion:

**Schritt 1 - Supplier-Check**:
Das System prüft, ob der Lieferant bereits in der `suppliers` Tabelle existiert (Suche nach `supplier_id`). Falls nein, wird automatisch ein neuer Supplier-Eintrag erstellt mit:
- `supplier_id`: Normalisierter Name (z.B. "PRIMEC")
- `name`: Vollständiger Name (z.B. "Primec")
- `contact_person`: "System" (da automatisch erstellt)
- Timestamp: Erstellungsdatum

**Schritt 2 - Delivery-Erstellung**:
Ein neuer Eintrag wird in der `deliveries` Tabelle angelegt:
- `delivery_number`: Eindeutige Lieferscheinnummer (Primary Key)
- `supplier_id`: Referenz zum Lieferanten (Foreign Key)
- `delivery_date`: Lieferdatum
- `employee_name`: Name des Mitarbeiters
- `document_path`: Pfad zum gespeicherten PDF
- `status`: "Empfangen" (Initial-Status)
- `notes`: Optionale Notizen

**Schritt 3 - Items-Verarbeitung**:
Für jeden Artikel in der Liste wird sequenziell verarbeitet:

a) **ItemInfo-Check**: Prüfung, ob Artikel-Stammdaten existieren
   - Falls NEIN: Erstelle `item_info` Eintrag mit:
     - `article_number`: Primary Key
     - `designation`: Beschreibung aus Lieferschein
     - `manufacturer`: Leer (wird später ergänzt)
     - Weitere Felder: NULL (werden im Workflow ergänzt)

b) **Order-Check**: Prüfung, ob Bestellnummer existiert
   - Falls im Lieferschein eine Bestellnummer vorhanden ist:
     - Prüfe in `orders` Tabelle
     - Falls NEIN: Erstelle automatisch neue Order mit:
       - `order_number`: Aus Lieferschein
       - `supplier_id`: "AUTO_SUPP" (Auto-created Supplier)
       - `order_date`: Aktuelles Datum
       - `status`: "open"
       - `employee_name`: "System"
       - `notes`: "Auto-created from delivery import"

c) **Item-Erstellung**: Haupteintrag in `items` Tabelle
   - Composite Primary Key (3 Felder):
     - `article_number`: Referenz zu ItemInfo
     - `batch_number`: Chargennummer (z.B. "P-153520240417")
     - `delivery_number`: Referenz zu Delivery
   - Mengen-Daten:
     - `delivered_quantity`: Tatsächlich gelieferte Menge
     - `ordered_quantity`: NULL (wird aus Order übernommen)
     - `delivery_slip_quantity`: Menge laut Lieferschein
     - `waste_quantity`: 0 (Initial)
   - Zertifikate (alle False, da noch nicht geprüft):
     - `measurement_protocol`: False
     - `material_certificate`: False
     - `hardness_certificate`: False
     - `coating_certificate`: False
     - `label_present`: False
   - `employee`: Name des Mitarbeiters
   - Timestamps: `created_at`, `updated_at`

d) **Workflow-Initialisierung**: Automatische Erstellung eines `item_workflow_steps` Eintrags
   - Alle Workflow-Felder auf NULL:
     - `data_checked_by`: NULL
     - `documents_checked_by`: NULL
     - `measured_by`: NULL
     - `visually_inspected_by`: NULL
     - `documents_merged_by`: NULL
     - `completed_by`: NULL
     - `rejected_by`: NULL
   - Status wird berechnet als: "Daten prüfen" (erster offener Schritt)

**Schritt 4 - Transaction Commit**:
Alle Änderungen werden als atomare Transaktion committed. Bei einem Fehler erfolgt ein Rollback, und bereits erstellte Items bleiben isoliert (kein Komplett-Rollback der Delivery).

**Schritt 5 - UI-Update**:
Die Hauptansicht wird aktualisiert, und die neuen Artikel erscheinen sofort in der Artikel-Liste mit Status "Daten prüfen".

### **Ergebnis**
- ✅ Delivery-Record erstellt und dokumentiert
- ✅ PDF gespeichert für Audit-Trail
- ✅ Artikel-Stammdaten angelegt (falls neu)
- ✅ Items mit Workflow-Status initialisiert
- ✅ Artikel erscheinen zur Weiterbearbeitung im System

### **Zeitbedarf**
- Upload: ~5 Sekunden
- AI-Analyse: ~3-8 Sekunden (abhängig von Claude API)
- Bearbeitung: ~1-3 Minuten (manuell)
- DB-Speicherung: ~1-2 Sekunden

**Gesamt: ~2-6 Minuten** (gegenüber 10-15 Minuten manueller Eingabe)

---

## Prozess 2: Kompletter Wareneingang

### **Ziel**
Strukturierter Qualitätssicherungs-Workflow von der Warenannahme bis zur Freigabe für die Produktion mit lückenloser Dokumentation aller Prüfschritte.

### **Ablauf im Detail**

#### **Phase 1: Lieferschein-Erfassung**
Siehe "Prozess 1: Lieferschein-Scan" oben. Nach dieser Phase existiert:
- Ein Delivery-Record in der Datenbank
- Mehrere Item-Records (je Artikel/Charge)
- Alle Items im Status "Daten prüfen"

#### **Phase 2: Datenprüfung** (Sachbearbeiter)

**Verantwortung**: Sachbearbeiter im Büro

Der Sachbearbeiter öffnet die Artikel-Liste in der User-Anwendung und wählt einen Artikel aus. Die Detailansicht zeigt:
- Artikelnummer und Bezeichnung
- Chargennummer und Lieferant
- Lieferdatum und Bestellnummer
- Alle Mengen-Informationen

**Prüfschritte**:
1. **Artikelstammdaten validieren**:
   - Ist die Artikelnummer korrekt formatiert? (z.B. "CT0003")
   - Stimmt die Bezeichnung mit dem Katalog überein?
   - Ist der Hersteller korrekt? (falls angegeben)

2. **Lieferinformationen prüfen**:
   - Stimmt die Chargennummer mit dem Lieferschein überein?
   - Ist die Menge plausibel?
   - Passt das Lieferdatum zur Bestellung?

3. **Bestelldaten abgleichen**:
   - Existiert die Bestellnummer im System?
   - Wurde diese Charge bereits geliefert? (Duplikat-Check)
   - Stimmt die Menge mit der Bestellung überein?

Falls Korrekturen nötig sind, kann der Sachbearbeiter alle Felder direkt bearbeiten. Nach erfolgreicher Prüfung klickt er auf **"Daten geprüft ✓"**.

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET data_checked_by = 'Max Mustermann',
    data_checked_at = NOW(),
    updated_at = NOW()
WHERE article_number = 'CT0003'
  AND batch_number = 'P-153520240417'
  AND delivery_number = 'LS24-077';
```

Der Artikel-Status wechselt automatisch zu: **"Dokumente prüfen"**

#### **Phase 3: Dokumentenprüfung** (Sachbearbeiter)

**Verantwortung**: Sachbearbeiter im Büro

Der Sachbearbeiter öffnet den Artikel erneut und navigiert zur Dokumenten-Sektion. Das System zeigt eine Checkliste aller erforderlichen Dokumente:

**Basis-Dokumente** (immer erforderlich):
- ✓ Lieferschein (bereits vorhanden aus Phase 1)
- ☐ Begleitdokument (falls vorhanden)

**Qualitäts-Zertifikate** (artikelabhängig):
- ☐ Messprotokolle (für Präzisionsteile)
- ☐ Materialkennzeichen (für Implantate)
- ☐ Härtezertifikat (für gehärtete Teile)
- ☐ Beschichtungszertifikat (für beschichtete Teile)
- ☐ Zusätzliche Zertifikate (z.B. CE, FDA)

**Prüfvorgang**:
1. Der Sachbearbeiter öffnet die physischen Dokumente (Papier oder eingescannte PDFs)
2. Für jedes Dokument:
   - Prüft er die Vollständigkeit (alle Seiten vorhanden?)
   - Prüft er die Lesbarkeit (ist alles lesbar?)
   - Prüft er die Gültigkeit (ist das Zertifikat aktuell?)
   - Scannt er fehlende Dokumente ein (optional)
   - Lädt er das Dokument ins System hoch (Upload-Button)

3. Das System speichert hochgeladene Dokumente unter:
   ```
   /Wareneingang/[Lieferant]/Zertifikate/[Charge]/[Dokumentname].pdf
   ```

4. Für jedes hochgeladene Dokument wird das entsprechende Boolean-Flag gesetzt:
   ```sql
   UPDATE items
   SET measurement_protocol = TRUE,
       material_certificate = TRUE,
       updated_at = NOW()
   WHERE article_number = 'CT0003'
     AND batch_number = 'P-153520240417';
   ```

**Fehlende Dokumente**:
Falls Dokumente fehlen, hat der Sachbearbeiter folgende Optionen:
- **Lieferant kontaktieren**: Automatische E-Mail-Vorlage mit Liste fehlender Dokumente
- **Dokumenten-Anforderung tracken**: System merkt sich die Anfrage mit Datum
- **Prozess pausieren**: Artikel bleibt in Phase 3 bis Dokumente nachgeliefert werden

Nach Vollständigkeitsprüfung klickt der Sachbearbeiter auf **"Dokumente geprüft ✓"**.

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET documents_checked_by = 'Max Mustermann',
    documents_checked_at = NOW()
WHERE ...;
```

Status wechselt zu: **"Vermessen"**

#### **Phase 4: Vermessung** (Qualitätsprüfer)

**Verantwortung**: Qualitätsprüfer im Messlabor

Der Qualitätsprüfer erhält eine Arbeitsliste aller Artikel mit Status "Vermessen". Er entnimmt den physischen Artikel aus dem Wareneingangslager und bringt ihn zum Messplatz.

**Prüfplan-Abruf**:
Das System zeigt automatisch den artikelspezifischen Prüfplan an, z.B.:
```
Artikel: CT0003 - DL Abutment GH 3,0mm
Toleranzen:
- Durchmesser: Ø 3,0mm ±0,05mm
- Länge: 8,5mm ±0,1mm
- Gewindemaß: M2,5 ±0,02mm
- Härte: 58-62 HRC (falls gehärtet)
```

**Mess-Durchführung**:
1. **Vorbereitung**:
   - Messgerät kalibrieren (falls nötig)
   - Artikel reinigen
   - Raumtemperatur prüfen (20°C ±2°C für Präzisionsmessung)

2. **Messungen**:
   - Für jedes Maß in der Spezifikation:
     - 3 Messungen durchführen (Redundanz)
     - Mittelwert berechnen
     - In System eingeben: `Durchmesser: 3,02mm ✓`
   - Visuelle Markierung: Grün (✓) wenn innerhalb Toleranz, Rot (✗) wenn außerhalb

3. **Härteprüfung** (falls erforderlich):
   - Rockwell-Härteprüfung durchführen
   - Ergebnis dokumentieren
   - Prüfpunkt auf Artikel markieren (mit Mikrostempel)

**Toleranz-Prüfung**:
Das System berechnet automatisch:
```python
# Beispiel: Durchmesser
gemessen = 3.02  # mm
soll = 3.00      # mm
toleranz = 0.05  # mm

if abs(gemessen - soll) <= toleranz:
    status = "PASS ✓"
else:
    status = "FAIL ✗"
```

**Bei Erfolg** (alle Maße innerhalb Toleranz):
Der Qualitätsprüfer klickt **"Vermessen ✓"**.

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET measured_by = 'Peter Prüfer',
    measured_at = NOW()
WHERE ...;
```
Status: **"Sichtkontrolle"**

**Bei Fehler** (Maße außerhalb Toleranz):
Der Qualitätsprüfer klickt **"Als Ausschuss markieren"** und gibt den Grund ein:
```
Ausschuss-Grund: "Durchmesser 3,08mm (Toleranz: 3,0±0,05mm überschritten)"
```

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET rejected_by = 'Peter Prüfer',
    rejected_at = NOW(),
    rejection_reason = 'Durchmesser außerhalb Toleranz'
WHERE ...;
```
Status: **"Ausschuss (rejected)"** → Prozess endet hier.

Der Artikel wird physisch in den Ausschuss-Bereich verbracht und bleibt zur Dokumentation in der Datenbank.

#### **Phase 5: Sichtkontrolle** (Qualitätsprüfer)

**Verantwortung**: Qualitätsprüfer (oft gleiche Person wie Vermessung)

**Prüfumfang**:
Die visuelle Inspektion umfasst vier Hauptbereiche:

1. **Oberflächenprüfung**:
   - Kratzer prüfen: Mit bloßem Auge und bei Bedarf mit Lupe (10x)
   - Dellen/Beulen: Oberflächenebene prüfen
   - Verfärbungen: Oxidation, Flecken
   - Rauheit: Fühlen mit behandschuhter Hand
   - Kriterium: Keine sichtbaren Mängel, die Funktionalität beeinträchtigen

2. **Beschichtungs-Prüfung** (falls beschichtet):
   - Gleichmäßigkeit: Farbton-Vergleich mit Referenzmuster
   - Dicke: Visuell (bei Bedarf mit Schichtdickenmessgerät)
   - Haftung: Klebeband-Test (nach ISO 2409)
   - Blasen/Abplatzungen: Visuelle Inspektion
   - Kriterium: Beschichtung lückenlos und gleichmäßig

3. **Kennzeichnungs-Prüfung**:
   - Label-Präsenz: Ist das Label vorhanden?
   - Lesbarkeit: Sind alle Angaben lesbar?
   - Korrektheit: Stimmen Artikel-Nr. und Charge?
   - Haftung: Sitzt das Label fest?
   - Kriterium: Label korrekt, lesbar und fest angebracht

4. **Verpackungs-Prüfung**:
   - Unversehrtheit: Ist die Verpackung intakt?
   - Sauberkeit: Keine Verschmutzungen
   - Vollständigkeit: Alle Komponenten vorhanden?
   - Schutz: Schützt die Verpackung ausreichend?
   - Kriterium: Verpackung schützt Artikel für Transport/Lagerung

**Durchführung**:
Der Prüfer arbeitet die Checkliste in der System-UI ab:
```
☐ Oberfläche    → Prüfen → ✓ OK / ✗ Mangel
☐ Beschichtung  → Prüfen → ✓ OK / ✗ Mangel
☐ Kennzeichnung → Prüfen → ✓ OK / ✗ Mangel
☐ Verpackung    → Prüfen → ✓ OK / ✗ Mangel
```

Bei jedem Mangel kann der Prüfer:
- Foto hochladen (Dokumentation)
- Mangeldetails beschreiben
- Schweregrad einstufen (Leicht/Mittel/Schwer)

**Bei Erfolg** (keine wesentlichen Mängel):
Klick auf **"Sichtkontrolle ✓"**.

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET visually_inspected_by = 'Peter Prüfer',
    visually_inspected_at = NOW()
WHERE ...;
```
Status: **"Dokumente zusammenführen"**

**Bei Fehler** (wesentliche Mängel):
Klick auf **"Als Ausschuss markieren"** mit Begründung:
```
Ausschuss-Grund: "Tiefe Kratzer in Oberfläche (>0,1mm Tiefe),
                  Beschichtung teilweise abgeplatzt"
```

Status: **"Ausschuss (rejected)"** → Prozess endet.

#### **Phase 6: Dokumenten-Zusammenführung** (Sachbearbeiter)

**Verantwortung**: Sachbearbeiter im Büro

**Ziel**: Alle Dokumente für den Artikel zusammenführen und ein vollständiges Produktionsdossier erstellen.

**Vorbereitung**:
Der Sachbearbeiter öffnet die Artikel-Details und sieht eine Übersicht:
```
Artikel: CT0003 - DL Abutment GH 3,0mm
Charge: P-153520240417
Status: Alle Prüfungen bestanden ✓

Verfügbare Dokumente:
✓ Lieferschein (LS24-077)
✓ Messprotokolle (3 Seiten)
✓ Materialkennzeichen (1 Seite)
✓ Härtezertifikat (2 Seiten)

Messwerte:
✓ Durchmesser: 3,02mm (Soll: 3,0±0,05mm)
✓ Länge: 8,48mm (Soll: 8,5±0,1mm)
✓ Härte: 60 HRC (Soll: 58-62 HRC)

Visuelle Prüfung:
✓ Oberfläche: OK
✓ Beschichtung: OK
✓ Kennzeichnung: OK
✓ Verpackung: OK
```

**Dokument-Generierung**:
Der Sachbearbeiter klickt auf **"Dokumente generieren"**. Das System startet den Document Generation Service:

**Schritt 1: Datensammlung** (~2 Sekunden)
```python
context = {
    "article": item_info,          # Artikelstammdaten
    "batch": batch_number,         # Charge
    "supplier": supplier,          # Lieferant
    "delivery": delivery,          # Lieferung
    "measurements": measurements,  # Messwerte
    "inspection": inspection,      # Prüfergebnisse
    "certificates": certificates,  # Zertifikate
    "workflow": workflow_steps     # Workflow-Historie
}
```

**Schritt 2: Template-Verarbeitung** (~3 Sekunden pro Dokument)

a) **QM-Protokoll** (Word → PDF):
```
Template: qm_protokoll_template.docx
Platzhalter ersetzen:
- {{artikel_nummer}} → "CT0003"
- {{bezeichnung}} → "DL Abutment GH 3,0mm"
- {{charge}} → "P-153520240417"
- {{lieferant}} → "Primec"
- {{datum}} → "2025-12-04"
- {{pruefer}} → "Peter Prüfer"
- {{messwerte_tabelle}} → [Dynamisch generierte Tabelle]
- {{unterschrift}} → [Digitale Signatur]

Output: QM_Protokoll_CT0003_P-153520240417.pdf
```

b) **Prüfbericht** (Word → PDF):
```
Template: pruefbericht_template.docx
Enthält:
- Prüfplan-Referenz
- Durchgeführte Messungen (Tabelle)
- Prüfergebnisse (OK/NOK)
- Abweichungen (falls vorhanden)
- Freigabe-Unterschriften

Output: Pruefbericht_CT0003_P-153520240417.pdf
```

c) **Artikel-Label** (PDF mit QR-Code):
```python
# QR-Code Generierung
qr_data = {
    "article_number": "CT0003",
    "batch_number": "P-153520240417",
    "delivery_number": "LS24-077",
    "supplier": "PRIMEC",
    "date": "2025-12-04"
}
qr_code = barcode_generator.generate_qr(json.dumps(qr_data))

# Label-Layout (70x30mm)
label = create_label(
    qr_code=qr_code,
    article_number="CT0003",
    designation="DL Abutment GH 3,0mm",
    batch="P-153520240417",
    supplier="Primec",
    date="04.12.2025"
)

Output: Label_CT0003_P-153520240417.pdf
```

d) **Zertifikate kopieren**:
Alle hochgeladenen Zertifikate werden in den Produktionsunterlagen-Ordner kopiert:
```
Messprotokolle.pdf
Materialkennzeichen.pdf
Haertezertifikat.pdf
```

**Schritt 3: PDF-Zusammenführung** (~2 Sekunden)
Alle generierten PDFs werden in ein Sammel-PDF zusammengeführt:
```
Sammel_CT0003_P-153520240417.pdf (35 Seiten)
├── Seite 1-3: QM-Protokoll
├── Seite 4-7: Prüfbericht
├── Seite 8: Artikel-Label
├── Seite 9-11: Messprotokolle
├── Seite 12: Materialkennzeichen
└── Seite 13-14: Härtezertifikat
```

**Schritt 4: Dateisystem-Ablage**
Alle Dokumente werden strukturiert gespeichert:
```
/Wareneingang/PRIMEC/Produktionsunterlagen/P-153520240417/
├── QM_Protokoll_CT0003_P-153520240417.pdf
├── Pruefbericht_CT0003_P-153520240417.pdf
├── Label_CT0003_P-153520240417.pdf
├── Sammel_CT0003_P-153520240417.pdf  ← Komplett-Dossier
├── Zertifikate/
│   ├── Messprotokolle.pdf
│   ├── Materialkennzeichen.pdf
│   └── Haertezertifikat.pdf
└── Lieferschein/
    └── Lieferschein_PRIMEC_LS24-077_2025-12-04.pdf
```

**Schritt 5: Dokumenten-Prüfung**
Der Sachbearbeiter öffnet das Sammel-PDF und prüft:
- Sind alle Seiten vorhanden?
- Sind alle Platzhalter korrekt ersetzt?
- Ist die Formatierung korrekt?
- Sind alle QR-Codes lesbar?

**Bei Erfolg**:
Klick auf **"Dokumente zusammengeführt ✓"**.

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET documents_merged_by = 'Max Mustermann',
    documents_merged_at = NOW()
WHERE ...;
```

Der Workflow zeigt nun an: **"Alle Schritte abgeschlossen ✓"** - Der Artikel ist bereit für die finale Freigabe.

**Bei Fehler** (z.B. Formatierungsproblem):
Der Sachbearbeiter korrigiert die Daten und klickt erneut auf "Dokumente generieren". Das System überschreibt die fehlerhaften Dokumente.

#### **Phase 7: Finale Freigabe** (Qualitätsmanager)

**Verantwortung**: Qualitätsmanager oder autorisierte Person

**Ablauf**:
Der Qualitätsmanager öffnet eine Liste aller Artikel mit Status "Bereit für Freigabe" (alle Workflow-Schritte erledigt, aber noch nicht freigegeben).

**Finale Prüfung**:
1. **Workflow-Vollständigkeit**:
   ```
   ✓ Daten geprüft: Max Mustermann (04.12.2025 09:15)
   ✓ Dokumente geprüft: Max Mustermann (04.12.2025 09:30)
   ✓ Vermessen: Peter Prüfer (04.12.2025 10:45)
   ✓ Sichtkontrolle: Peter Prüfer (04.12.2025 11:00)
   ✓ Dokumente zusammengeführt: Max Mustermann (04.12.2025 14:20)
   ```

2. **Dokumenten-Vollständigkeit**:
   - Sammel-PDF vorhanden und vollständig?
   - Alle Unterschriften vorhanden?
   - QR-Code-Labels gedruckt?

3. **Kritische Prüfung**:
   - Gibt es Auffälligkeiten in den Messwerten? (Trend zur Toleranzgrenze?)
   - Gibt es Anmerkungen von Prüfern?
   - Gibt es Lieferanten-Historie-Probleme?

**Freigabe-Entscheidung**:

**Szenario A: Freigabe erteilen**
Der Qualitätsmanager klickt **"Artikel freigeben"**.

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET completed_by = 'Dr. Müller',
    completed_at = NOW()
WHERE ...;

UPDATE items
SET status = 'Freigegeben'  -- (wird aus workflow berechnet)
WHERE ...;
```

Status: **"Abgeschlossen (completed)"** ✅

Der Artikel wird:
- Für die Produktion freigegeben
- Im Lager als "verfügbar" markiert
- Kann für Projekte/Aufträge verwendet werden
- Erscheint in der Entnahme-Verwaltung

**Szenario B: Nacharbeit erforderlich**
Falls der Qualitätsmanager Bedenken hat, aber keine Ausschuss-Entscheidung treffen will:
- Kann er den Artikel an vorherige Phase zurückschicken
- Workflow-Step wird auf NULL gesetzt
- Verantwortlicher wird benachrichtigt
- Artikel durchläuft Phase erneut

**Szenario C: Ausschuss**
Falls gravierende Mängel nachträglich festgestellt werden:
Klick auf **"Als Ausschuss markieren"** mit detaillierter Begründung:
```
Ausschuss-Grund: "Nachträgliche Feststellung: Materialkennzeichen
                  entspricht nicht Spezifikation (falscher Werkstoff).
                  Artikel darf nicht in Produktion verwendet werden."
```

**System-Reaktion**:
```sql
UPDATE item_workflow_steps
SET rejected_by = 'Dr. Müller',
    rejected_at = NOW(),
    rejection_reason = '[Begründung]'
WHERE ...;
```

Status: **"Ausschuss (rejected)"** ❌

### **Ergebnis des kompletten Prozesses**

**Bei erfolgreicher Freigabe**:
- ✅ Artikel vollständig dokumentiert (PDF-Dossier)
- ✅ Alle Prüfschritte mit Timestamps und Verantwortlichen
- ✅ Lückenloser Audit-Trail
- ✅ Artikel für Produktion freigegeben
- ✅ QR-Code-Label für Rückverfolgbarkeit
- ✅ Zertifikate archiviert
- ✅ Bereit für ISO/QM-Audit

**Bei Ausschuss**:
- ❌ Artikel gesperrt für Produktion
- ❌ Ausschuss-Grund dokumentiert
- ❌ Artikel physisch in Ausschuss-Bereich
- ✅ Dokumentation bleibt in DB (für Statistiken/Analysen)
- ✅ Lieferanten-Feedback automatisch generierbar

### **Zeitbedarf**
- Phase 1 (Scan): ~2-6 Min
- Phase 2 (Daten): ~3-5 Min
- Phase 3 (Dokumente): ~5-10 Min
- Phase 4 (Vermessung): ~10-20 Min
- Phase 5 (Sichtkontrolle): ~5-10 Min
- Phase 6 (Zusammenführung): ~5-10 Min
- Phase 7 (Freigabe): ~2-5 Min

**Gesamt: 32-66 Minuten pro Artikel**

---

## Systemarchitektur

### **Layer-Struktur (Clean Architecture)**

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer (UI)                        │
│  - Streamlit Views (Admin: 8501, User: 8502)   │
│  - Popups & Dialogs                             │
│  - User Input Validation                        │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│  Application Layer (Business Logic)            │
│  - Services (Delivery, Item, Supplier, Order)  │
│  - Document Processing (Claude AI Integration) │
│  - Document Generation (Word/PDF)              │
│  - Storage Management (Path Resolution)        │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│  Infrastructure Layer (Data Access)            │
│  - PostgreSQL Database (Repositories)          │
│  - File System (Document Storage)              │
│  - External APIs (Claude, OCR)                 │
│  - Docker Container Environment                │
└─────────────────────────────────────────────────┘
```

### **Technologie-Stack**

**Backend**:
- Python 3.11
- SQLAlchemy 2.0 (ORM)
- PostgreSQL 15 (Datenbank)
- psycopg2 (PostgreSQL Adapter)

**Frontend**:
- Streamlit 1.52 (Web UI Framework)
- pandas (Daten-Manipulation)
- Pillow (Bildverarbeitung)

**AI/ML**:
- Anthropic Claude API (claude-sonnet-4-20250514)
- pytesseract (OCR - optional)

**Dokumenten-Verarbeitung**:
- python-docx (Word-Generierung)
- PyPDF2 / PyMuPDF (PDF-Manipulation)
- python-barcode (QR-Code-Generierung)

**Deployment**:
- Docker + Docker Compose
- Multi-Container Setup (App + PostgreSQL)
- Volume Mounting (Persistente Daten)

---

## Datenfluss

### **Lieferschein-Scan Datenfluss**

```
User Upload (PDF)
  → Temporary File (/tmp)
    → Claude API (JSON Response)
      → Session State (Python Dict)
        → User Confirmation & Edits
          → PostgreSQL Transaction:
            ├─→ INSERT suppliers (if new)
            ├─→ INSERT deliveries
            ├─→ INSERT item_info (if new)
            ├─→ INSERT orders (if new)
            ├─→ INSERT items (multiple)
            └─→ INSERT item_workflow_steps (multiple)
          → File System:
            └─→ PDF Storage (/Wareneingang/.../Lieferscheine/)
```

### **Workflow-Status Datenfluss**

```
item_workflow_steps Table (NULL = pending, String = done)
  → Status Calculation (Python):
    if rejected_by IS NOT NULL → "Ausschuss"
    elif completed_by IS NOT NULL → "Abgeschlossen"
    elif documents_merged_by IS NULL → "Dokumente zusammenführen"
    elif visually_inspected_by IS NULL → "Sichtkontrolle"
    elif measured_by IS NULL → "Vermessen"
    elif documents_checked_by IS NULL → "Dokumente prüfen"
    elif data_checked_by IS NULL → "Daten prüfen"
  → UI Display (Colored Badges)
  → Filtering & Sorting
```

### **Dokumenten-Generierung Datenfluss**

```
User Click "Dokumente generieren"
  → Context Builder:
    ├─→ Query items (SQLAlchemy)
    ├─→ Query item_info (JOIN)
    ├─→ Query delivery (JOIN)
    ├─→ Query supplier (JOIN)
    └─→ Query workflow_steps (JOIN)
  → Template Manager:
    ├─→ Load Word Templates (/resources/templates/)
    ├─→ Replace Placeholders (Jinja2-style)
    └─→ Save as .docx
  → Word Converter:
    ├─→ Convert .docx → .pdf (python-docx)
    └─→ Handle Errors (fallback options)
  → Barcode Generator:
    ├─→ Create QR Code (python-barcode)
    └─→ Embed in Label PDF
  → PDF Merger:
    ├─→ Combine all PDFs (PyPDF2)
    └─→ Add Bookmarks (navigation)
  → Storage Service:
    └─→ Save to /Wareneingang/.../Produktionsunterlagen/
  → UI Feedback:
    └─→ "Dokumente erfolgreich generiert" + Download Links
```

---

## Qualitätssicherung

### **System-Qualität**

**Datenbank-Integrität**:
- Foreign Key Constraints (Referentielle Integrität)
- Composite Primary Keys (Eindeutigkeit)
- NOT NULL Constraints (Datenvollständigkeit)
- CHECK Constraints (Datenvalidierung)
- Transaction Isolation (ACID-Eigenschaften)

**Fehlerbehandlung**:
- Try-Except Blöcke (Python)
- Rollback bei DB-Fehlern
- Logging auf 3 Levels (INFO, WARNING, ERROR)
- User-freundliche Fehlermeldungen

**Performance**:
- Connection Pooling (10 Connections, max 20)
- Lazy Loading (SQLAlchemy)
- Indexed Columns (delivery_number, article_number, etc.)
- Query Optimization (JOIN statt N+1)

### **Prozess-Qualität**

**Workflow-Kontrolle**:
- Sequenzieller Workflow (Schritt 2 erst nach Schritt 1)
- Verantwortlichkeits-Tracking (wer, wann)
- Status-Berechnung (transparent, nachvollziehbar)
- Ausschuss-Sperre (rejected Items können nicht freigegeben werden)

**Dokumentation**:
- Lückenloser Audit-Trail (alle Änderungen mit Timestamp)
- Dokument-Versionierung (bei Regenerierung)
- QR-Code-Rückverfolgbarkeit (vom Label zur kompletten Historie)
- Zertifikats-Archivierung (langfristige Aufbewahrung)

**Benutzer-Führung**:
- Klare Status-Anzeigen (farbige Badges)
- Checklisten (keine Schritte vergessen)
- Validierung (Pflichtfelder, Formate)
- Warnungen (fehlende Dokumente, Toleranzüberschreitungen)

### **Compliance**

**ISO 9001**:
- ✅ Dokumentierte Prozesse (UML-Diagramme)
- ✅ Verantwortlichkeiten definiert (in Workflow)
- ✅ Nachvollziehbarkeit (Audit-Trail)
- ✅ Kontinuierliche Verbesserung (Ausschuss-Analysen)

**ISO 13485 (Medizinprodukte)**:
- ✅ Rückverfolgbarkeit (Charge → Lieferant → Zertifikate)
- ✅ Prüfprotokolle (Mess- und Prüfberichte)
- ✅ Dokumentenmanagement (strukturierte Ablage)
- ✅ Risikomanagement (Ausschuss-Tracking)

**FDA 21 CFR Part 820**:
- ✅ Device History Record (komplette Artikel-Historie)
- ✅ Device Master Record (Artikel-Stammdaten)
- ✅ Quality System Records (QM-Protokolle)
- ✅ Traceability (QR-Codes, Chargen-Tracking)

---

**Dokumenten-Version**: 1.0
**Letzte Aktualisierung**: 2025-12-04
**Gültig ab**: Sofort
**Gültig bis**: Bis zur nächsten Revision
**Verantwortlich**: Qualitätsmanagement
