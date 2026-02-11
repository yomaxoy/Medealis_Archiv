# UML Aktivitätsdiagramm: Kompletter Wareneingang-Prozess

## Prozessbeschreibung
Dieser Ablauf zeigt den kompletten Wareneingang-Workflow für einen Artikel - von der Lieferschein-Erfassung bis zur finalen Freigabe oder Ausschuss.

---

## PlantUML Code

```plantuml
@startuml Wareneingang_Prozess
title Kompletter Wareneingang-Prozess für einen Artikel

|Wareneingang|
start

partition "Phase 1: Lieferschein-Erfassung" {
  :Lieferschein-PDF scannen;
  note right
    Claude AI extrahiert:
    - Lieferant
    - Lieferscheinnummer
    - Artikel-Liste
    - Chargen
  end note

  :Bestätigt extrahierte Daten;

  |System|
  :Erstellt Delivery-Record;
  :Erstellt Items (je Artikel/Charge);
  :Erstellt ItemWorkflowSteps (alle NULL);
  note right
    Status: "Daten prüfen"
    (erster offener Schritt)
  end note
}

partition "Phase 2: Datenprüfung" {
  |Sachbearbeiter|
  :Öffnet Artikel-Details;
  :Prüft Artikelstammdaten;

  while (Daten korrekt?) is (nein)
    :Korrigiert Daten;
    note right
      - Artikelnummer
      - Bezeichnung
      - Chargennummer
      - Mengen
    end note
  endwhile (ja)

  :Klickt "Daten geprüft ✓";

  |System|
  :Setzt data_checked_by = "Mitarbeitername";
  :Setzt data_checked_at = NOW();
  :Berechnet neuen Status;
  note right: Status → "Dokumente prüfen"
}

partition "Phase 3: Dokumentenprüfung" {
  |Sachbearbeiter|
  :Prüft Zertifikate/Dokumente;

  fork
    :Prüft Lieferschein ✓;
  fork again
    if (Messprotokolle erforderlich?) then (ja)
      :Prüft Messprotokolle ✓;
    else (nein)
    endif
  fork again
    if (Materialkennzeichen erforderlich?) then (ja)
      :Prüft Materialkennzeichen ✓;
    else (nein)
    endif
  fork again
    if (Härtezertifikate erforderlich?) then (ja)
      :Prüft Härtezertifikate ✓;
    else (nein)
    endif
  fork again
    if (Beschichtungszertifikate erforderlich?) then (ja)
      :Prüft Beschichtungszertifikate ✓;
    else (nein)
    endif
  end fork

  if (Alle Dokumente vorhanden?) then (ja)
    :Markiert Dokumente als vollständig;
    :Klickt "Dokumente geprüft ✓";

    |System|
    :Setzt documents_checked_by = "Mitarbeitername";
    :Setzt documents_checked_at = NOW();
    note right: Status → "Vermessen"

  else (nein)
    :Markiert fehlende Dokumente;
    :Kontaktiert Lieferanten;
    note right: Prozess pausiert
    stop
  endif
}

partition "Phase 4: Vermessung" {
  |Qualitätsprüfer|
  :Nimmt Artikel aus Lager;
  :Vermisst Artikel;

  fork
    :Misst Maße;
    :Dokumentiert Messwerte;
  fork again
    if (Härteprüfung erforderlich?) then (ja)
      :Führt Härteprüfung durch;
      :Dokumentiert Härtewerte;
    else (nein)
    endif
  end fork

  if (Maße innerhalb Toleranz?) then (ja)
    :Klickt "Vermessen ✓";

    |System|
    :Setzt measured_by = "Mitarbeitername";
    :Setzt measured_at = NOW();
    note right: Status → "Sichtkontrolle"

  else (nein)
    :Artikel markieren für Ausschuss;
    :Klickt "Als Ausschuss markieren";

    |System|
    :Setzt rejected_by = "Mitarbeitername";
    :Setzt rejected_at = NOW();
    :Setzt rejection_reason = "Maße außerhalb Toleranz";
    note right: Status → "Ausschuss (rejected)"

    |Qualitätsprüfer|
    :Legt Artikel in Ausschuss;
    stop
  endif
}

partition "Phase 5: Sichtkontrolle" {
  |Qualitätsprüfer|
  :Führt visuelle Inspektion durch;

  fork
    :Prüft Oberfläche;
  fork again
    :Prüft Beschichtung;
  fork again
    :Prüft Kennzeichnung/Label;
  fork again
    :Prüft Verpackung;
  end fork

  if (Sichtprüfung bestanden?) then (ja)
    :Klickt "Sichtkontrolle ✓";

    |System|
    :Setzt visually_inspected_by = "Mitarbeitername";
    :Setzt visually_inspected_at = NOW();
    note right: Status → "Dokumente zusammenführen"

  else (nein)
    :Artikel markieren für Ausschuss;
    :Klickt "Als Ausschuss markieren";

    |System|
    :Setzt rejected_by = "Mitarbeitername";
    :Setzt rejected_at = NOW();
    :Setzt rejection_reason = "Visuelle Mängel";
    note right: Status → "Ausschuss (rejected)"

    |Qualitätsprüfer|
    :Legt Artikel in Ausschuss;
    stop
  endif
}

partition "Phase 6: Dokumenten-Zusammenführung" {
  |Sachbearbeiter|
  :Öffnet Artikel-Details;
  :Klickt "Dokumente generieren";

  |Document Generation Service|
  :Sammelt alle Daten;
  note right
    - Artikel-Stammdaten
    - Lieferanten-Info
    - Messwerte
    - Zertifikate
  end note

  fork
    :Generiert QM-Protokoll (Word);
  fork again
    :Generiert Prüfbericht (Word);
  fork again
    :Generiert Artikel-Labels (PDF);
    note right: Mit QR-Code
  fork again
    :Kopiert Zertifikate;
  end fork

  :Erstellt Sammel-PDF;
  note right: Alle Dokumente in einem PDF

  :Speichert in Produktionsunterlagen;
  note right
    Pfad: /Wareneingang/[Supplier]/
    Produktionsunterlagen/[Charge]/
  end note

  |Sachbearbeiter|
  :Prüft generierte Dokumente;

  if (Dokumente korrekt?) then (ja)
    :Klickt "Dokumente zusammengeführt ✓";

    |System|
    :Setzt documents_merged_by = "Mitarbeitername";
    :Setzt documents_merged_at = NOW();
    note right: Alle Workflow-Schritte erledigt!

  else (nein)
    :Korrigiert Daten;
    :Generiert Dokumente erneut;
    backward :Zurück zu "Dokumente generieren";
  endif
}

partition "Phase 7: Finale Freigabe" {
  |Qualitätsmanager|
  :Prüft vollständigen Prozess;

  fork
    :Prüft alle Workflow-Schritte ✓;
  fork again
    :Prüft Dokumenten-Vollständigkeit;
  fork again
    :Prüft Zertifikate;
  end fork

  if (Finale Freigabe?) then (ja)
    :Klickt "Artikel freigeben";

    |System|
    :Setzt completed_by = "Mitarbeitername";
    :Setzt completed_at = NOW();
    note right: Status → "Abgeschlossen (completed)"

    :Artikel ist freigegeben;
    :Kann in Produktion verwendet werden;

    |Lager|
    :Lagert Artikel ein;
    :Artikel verfügbar für Entnahme;
    stop

  else (nein)
    :Artikel markieren für Ausschuss;
    :Gibt Ausschuss-Grund ein;
    :Klickt "Als Ausschuss markieren";

    |System|
    :Setzt rejected_by = "Mitarbeitername";
    :Setzt rejected_at = NOW();
    :Setzt rejection_reason = [Eingabe];
    note right: Status → "Ausschuss (rejected)"

    |Lager|
    :Legt Artikel in Ausschuss;
    stop
  endif
}

@enduml
```

---

## Workflow-Schritte Übersicht

| # | Schritt | Verantwortlich | Datenbank-Feld | Status-Anzeige |
|---|---------|----------------|----------------|----------------|
| 1 | Daten prüfen | Sachbearbeiter | `data_checked_by` | "Daten prüfen" |
| 2 | Dokumente prüfen | Sachbearbeiter | `documents_checked_by` | "Dokumente prüfen" |
| 3 | Vermessen | Qualitätsprüfer | `measured_by` | "Vermessen" |
| 4 | Sichtkontrolle | Qualitätsprüfer | `visually_inspected_by` | "Sichtkontrolle" |
| 5 | Dokumente zusammenführen | Sachbearbeiter | `documents_merged_by` | "Dokumente zusammenführen" |
| 6a | Freigabe (Erfolg) | Qualitätsmanager | `completed_by` | "Abgeschlossen" ✅ |
| 6b | Ausschuss (Ablehnung) | Qualitätsprüfer | `rejected_by` | "Ausschuss" ❌ |

---

## Status-Berechnung

Der Status wird **dynamisch** aus der `item_workflow_steps` Tabelle berechnet:

```python
def get_current_status():
    if rejected_by is not None:
        return "Ausschuss (rejected)"
    if completed_by is not None:
        return "Abgeschlossen (completed)"
    if documents_merged_by is None:
        return "Dokumente zusammenführen"
    if visually_inspected_by is None:
        return "Sichtkontrolle"
    if measured_by is None:
        return "Vermessen"
    if documents_checked_by is None:
        return "Dokumente prüfen"
    if data_checked_by is None:
        return "Daten prüfen"
    return "Bereit für Freigabe"
```

---

## Beteiligte Komponenten

### **Datenbank-Tabellen**
- `deliveries` - Lieferung
- `items` - Artikel-Instanzen (Charge-spezifisch)
- `item_info` - Artikel-Stammdaten
- `item_workflow_steps` - Workflow-Status-Tracking
- `suppliers` - Lieferanten
- `orders` - Bestellungen

### **Services**
- `delivery_service.py` - Lieferungs-Management
- `item_service.py` - Artikel-Management
- `document_generation_service.py` - Dokument-Generierung
- `document_storage_service.py` - Dokumenten-Speicherung
- `barcode_generator.py` - QR-Code-Generierung

### **Presentation Layer**
- `delivery_scan.py` - Lieferschein-Scan
- `item_details_view.py` - Artikel-Details und Workflow-Buttons
- `main_user_app.py` - Haupt-Interface

---

## Ausschuss-Szenarien

Artikel kann in **3 Phasen** als Ausschuss markiert werden:

1. **Nach Vermessung**: Maße außerhalb Toleranz
2. **Nach Sichtkontrolle**: Visuelle Mängel (Kratzer, Beschädigungen)
3. **Nach Finaler Prüfung**: Andere Qualitätsmängel

Bei Ausschuss:
- `rejected_by` = Mitarbeitername
- `rejected_at` = Timestamp
- `rejection_reason` = Grund (Freitext)
- Artikel kann **nicht mehr** freigegeben werden
- Artikel bleibt zur Dokumentation in der DB

---

## Parallele Verarbeitung

**Mehrere Artikel gleichzeitig:**
- Verschiedene Mitarbeiter können an verschiedenen Artikeln arbeiten
- Jeder Artikel hat eigenen Workflow-Status
- Workflow-Steps sind **unabhängig** pro Artikel

**Bulk-Operationen:**
- Mehrere Artikel aus gleicher Lieferung können gemeinsam geprüft werden
- Status-Updates können per Batch erfolgen (zukünftige Erweiterung)

---

## Dokument-Generierung Details

**Phase 6** generiert folgende Dokumente:

1. **QM-Protokoll** (Word/PDF)
   - Artikel-Details
   - Lieferanten-Info
   - Messwerte
   - Zertifikate-Referenzen

2. **Prüfbericht** (Word/PDF)
   - Prüfergebnisse
   - Unterschriften
   - Freigabe-Status

3. **Artikel-Labels** (PDF)
   - QR-Code (Artikel-ID)
   - Artikelnummer + Charge
   - Lieferant
   - Prüfdatum

4. **Sammel-PDF**
   - Alle obigen Dokumente
   - Lieferschein
   - Zertifikate

**Speicherort:**
```
/Wareneingang/[Supplier]/Produktionsunterlagen/[Batch_Number]/
├── QM_Protokoll_[Article]_[Batch].pdf
├── Pruefbericht_[Article]_[Batch].pdf
├── Label_[Article]_[Batch].pdf
└── Sammel_[Article]_[Batch].pdf
```

---

## Zeitschätzung

**Durchschnittliche Dauer pro Artikel:**
- Phase 1 (Scan): 2-5 Min
- Phase 2 (Datenprüfung): 3-5 Min
- Phase 3 (Dokumente): 5-10 Min
- Phase 4 (Vermessung): 10-20 Min
- Phase 5 (Sichtkontrolle): 5-10 Min
- Phase 6 (Dokumente): 5-10 Min
- Phase 7 (Freigabe): 2-5 Min

**Gesamt: 32-65 Minuten pro Artikel** (abhängig von Komplexität)

---

## Qualitäts-Metriken

Das System trackt automatisch:
- ⏱️ Durchlaufzeit pro Workflow-Schritt
- 👤 Mitarbeiter-Performance
- ❌ Ausschuss-Rate pro Lieferant
- ✅ First-Time-Right Rate
- 📊 Bearbeitungs-Bottlenecks
