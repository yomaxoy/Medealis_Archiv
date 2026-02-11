# UML Aktivitätsdiagramm: Lieferschein-Scan Prozess

## Prozessbeschreibung
Dieser Ablauf zeigt, wie ein Lieferschein gescannt, mit AI ausgewertet und in die Datenbank gespeichert wird.

---

## PlantUML Code

```plantuml
@startuml Lieferschein_Scan_Prozess
title Lieferschein-Scan Prozess (AI-gestützt)

|User|
start
:Öffnet "Lieferschein scannen" Dialog;
:Lädt PDF/Bild hoch;

|System|
:Prüft System-Status;
note right
  - Claude API verfügbar?
  - OCR (Tesseract) verfügbar?
  - Speicher verfügbar?
end note

if (Storage verfügbar?) then (ja)
  |User|
  :Klickt "OCR + Claude Analyse";

  |Document Processing Service|
  :**Schritt 1/4:** Datei verarbeiten;
  :Liest PDF/Bild-Daten;
  :Erstellt temporäre Datei;

  :**Schritt 2/4:** AI-Datenextraktion;
  if (OCR verfügbar?) then (ja)
    :OCR-Vorverarbeitung (Tesseract);
    note right: Extrahiert Text aus Bild
  else (nein)
    :Direkter Claude-Upload;
  endif

  :Sendet an Claude API;
  note right
    Model: claude-sonnet-4-20250514
    Prompt: Strukturierte Datenextraktion
  end note

  :Empfängt JSON-Response;
  note right
    {
      "delivery_number": "LS24-077",
      "supplier_name": "Primec",
      "delivery_date": "11.06.2024",
      "items": [...]
    }
  end note

  |Storage Service|
  :Speichert PDF;
  :Pfad: /Wareneingang/[Supplier]/Lieferscheine/;

  |Document Processing Service|
  :**Schritt 3/4:** Daten validieren;
  :Normalisiert Lieferantennamen;
  note right: "Primec" → "PRIMEC"

  :**Schritt 4/4:** Extraktion erfolgreich;
  :Speichert Daten in Session State;

  |User|
  :Sieht Bestätigungs-Dialog;
  :Prüft extrahierte Daten;

  partition "Datenbearbeitung" {
    repeat
      :Bearbeitet Felder (optional);
      note right
        - Lieferscheinnummer
        - Lieferant
        - Lieferdatum
        - Items (Menge, Artikel, Charge)
      end note
      :Löscht fehlerhafte Items (optional);
    repeat while (Weitere Änderungen?) is (ja) not (nein)
  }

  :Klickt "Speichern";

  |Delivery Service|
  :Erstellt/Prüft Supplier;
  if (Supplier existiert?) then (nein)
    :Erstellt neuen Supplier;
    note right: supplier_id = "PRIMEC"
  else (ja)
  endif

  :Erstellt Delivery-Record;
  note right
    - delivery_number
    - supplier_id
    - delivery_date
    - status = "Empfangen"
  end note

  |Item Service|
  repeat :Verarbeitet Item;
    if (ItemInfo existiert?) then (nein)
      :Erstellt ItemInfo;
      note right: Artikel-Stammdaten
    else (ja)
    endif

    if (Order existiert?) then (nein)
      :Erstellt Auto-Order;
      note right
        - order_number (aus PDF)
        - supplier_id = "AUTO_SUPP"
      end note
    else (ja)
    endif

    :Erstellt Item-Record;
    note right
      Composite Key:
      - article_number
      - batch_number
      - delivery_number
    end note

  repeat while (Weitere Items?) is (ja) not (nein)

  |System|
  :Commit Transaction;

  |User|
  :Sieht Erfolgs-Meldung;
  :Artikel erscheinen im Hauptmenü;
  stop

else (nein)
  :Zeigt Fehler-Dialog;
  :Speicherung nicht möglich;
  stop
endif

@enduml
```

---

## Beteiligte Komponenten

### **Presentation Layer**
- `delivery_scan.py::show_delivery_scan_popup()` - Upload-Dialog
- `delivery_scan.py::process_uploaded_delivery_file()` - Dateiverarbeitung
- `delivery_scan.py::show_extraction_confirmation_popup()` - Bestätigung

### **Application Layer**
- `document_processing_service.py::process_document()` - Dokumenten-Verarbeitung
- `claude_api_client.py::extract_delivery_data()` - AI-Extraktion
- `delivery_service.py::create_delivery_from_extraction()` - Delivery-Erstellung
- `item_service.py::create_item()` - Item-Erstellung
- `supplier_service.py::create_supplier()` - Supplier-Erstellung

### **Infrastructure Layer**
- `document_storage_service.py::save_delivery_slip()` - PDF-Speicherung
- `path_resolver.py::resolve_delivery_slip_path()` - Pfad-Auflösung
- PostgreSQL Datenbank

---

## Wichtige Entscheidungspunkte

1. **Storage Check**: Verhindert Upload, wenn kein Speicher verfügbar
2. **OCR Verfügbarkeit**: Nutzt Tesseract wenn verfügbar, sonst direkter Claude-Upload
3. **Supplier-Existenz**: Erstellt automatisch neuen Supplier wenn nicht vorhanden
4. **Order-Existenz**: Erstellt Auto-Order mit "AUTO_SUPP" Supplier
5. **ItemInfo-Existenz**: Erstellt Stammdaten nur für neue Artikel

---

## Fehlerbehandlung

- **API-Key fehlt**: Prozess kann nicht starten
- **Storage nicht verfügbar**: Upload wird abgebrochen
- **Claude API Fehler**: Fehlermeldung mit Details
- **Datenbank-Fehler**: Rollback, Items werden einzeln verarbeitet (Fehler isoliert)

---

## Performance

- **Typische Dauer**: 3-10 Sekunden (abhängig von Claude API)
- **Parallel-Verarbeitung**: Nein (sequenziell)
- **Caching**: Ja (Document Cache für wiederholte Requests)
