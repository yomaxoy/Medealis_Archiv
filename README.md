# Medealis Archiv Management System

Ein Python-basiertes Verwaltungssystem für den Wareneingang bei Medealis GmbH.

## 🚀 Features

- **📄 Lieferschein-Verarbeitung**: Automatische Texterkennung aus Word-Dokumenten mit KI-Unterstützung
- **📦 Wareneingangskontrolle**: Vollständige Verwaltung von Lieferungen und Artikeln
- **🔍 Sichtprüfung**: Strukturierte Qualitätskontrolle mit Dokumentation
- **📊 Barcode-Generierung**: Automatische Erstellung von Barcodes für Artikel
- **📋 Dokumentenerstellung**: Automatische Generierung von PDB, Begleitscheinen und Sichtkontrollen
- **🗄️ SQLite-Datenbank**: Lokale Datenspeicherung ohne externe Abhängigkeiten

## 🛠️ Systemanforderungen

- **Python**: 3.8 oder höher
- **Betriebssystem**: Windows (für Microsoft Office Integration)
- **OpenAI API Key**: Für KI-gestützte Texterkennung
- **Microsoft Word**: Für Template-Verarbeitung (optional)

## 📥 Installation

1. **Repository klonen**:
   ```bash
   git clone <repository-url>
   cd medealis-archiv
   ```

2. **Virtuelle Umgebung erstellen** (empfohlen):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # oder: source venv/bin/activate  # Linux/Mac
   ```

3. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```

4. **OpenAI API Key konfigurieren**:
   - Beim ersten Start wird nach dem API Key gefragt
   - Dieser wird verschlüsselt in `~/.medealis/config.json` gespeichert

5. **Anwendung starten**:
   ```bash
   python src/main.py
   ```

## 📁 Projektstruktur

```
medealis-archiv/
├── src/
│   ├── config/                 # Konfigurationsdateien
│   │   ├── app_constants.py
│   │   └── app_settings.py
│   ├── controllers/            # MVC Controller
│   │   ├── base_controller.py
│   │   ├── item_controller.py
│   │   ├── delivery_controller.py
│   │   └── document_controller.py
│   ├── database/              # Datenbankschicht
│   │   ├── database.py
│   │   ├── db_connection.py
│   │   └── db_migration.py
│   ├── models/                # Datenmodelle
│   │   ├── base_model.py
│   │   ├── item_model.py
│   │   ├── delivery_model.py
│   │   └── document_model.py
│   ├── services/              # Business Logic
│   │   ├── data_extraction.py
│   │   ├── data_parser.py
│   │   ├── document_service.py
│   │   └── barcode_service.py
│   ├── utils/                 # Hilfsfunktionen
│   │   ├── path_manager.py
│   │   └── path_utils.py
│   ├── views/                 # GUI Views
│   │   ├── base_views/
│   │   ├── dialogs/
│   │   └── windows/
│   └── main.py               # Haupteinstiegspunkt
├── templates/                 # Word-Vorlagen
│   ├── Fo00040_Checklist for incoming goods inspection.docx
│   ├── Fo00057_Begleitschein.docx
│   └── Fo001xx_Sichtkontrolle.docx
├── requirements.txt
├── README.md
└── .gitignore
```

## 🔧 Verwendung

### 1. Neue Lieferung erfassen
1. "Neue Lieferung" im Hauptmenü wählen
2. Mitarbeitername eingeben
3. Lieferschein-Dokument (.docx) auswählen
4. Automatische Texterkennung und Datenextraktion

### 2. Wareneingangskontrolle
1. "Wareneingangskontrolle" öffnen
2. Lieferschein auswählen
3. Artikel-Daten überprüfen und bestätigen
4. Dokumente verwalten (Zeugnisse, etc.)
5. Sichtprüfung durchführen

### 3. Artikel verwalten
- **Artikelansicht**: Detailansicht einzelner Artikel
- **Artikelübersicht**: Tabellarische Übersicht aller Artikel mit Filterfunktionen

## 🗄️ Datenbank

Das System verwendet SQLite mit folgenden Haupttabellen:
- **Items**: Artikel/Produkte
- **Lieferungen**: Lieferscheine
- **Lieferanten**: Supplier-Informationen
- **Bestellungen**: Bestellungen
- **ItemInfo**: Artikel-Metadaten

## 🔐 Sicherheit

- OpenAI API Keys werden verschlüsselt gespeichert (Fernet-Verschlüsselung)
- Lokale Datenbank ohne Netzwerkzugriff
- Konfigurationsdateien werden im Benutzerverzeichnis gespeichert

## 🏗️ Architektur

Das System folgt dem **MVC-Pattern**:
- **Models**: Datenbankzugriff und Business Logic
- **Views**: GUI-Komponenten (Tkinter)
- **Controllers**: Verbindung zwischen Models und Views

**Design Patterns**:
- Singleton Pattern (PathManager, DatabaseConnection)
- Factory Pattern (Document Models)
- Observer Pattern (GUI Event Handling)

## 🚨 Bekannte Einschränkungen

- **Windows-abhängig**: Office-Integration funktioniert nur unter Windows
- **OpenAI API**: Internetverbindung für KI-Features erforderlich
- **Single-User**: Keine Multi-User-Unterstützung
- **Lokale Datenbank**: Keine zentrale Datenhaltung

## 🤝 Entwicklung

### Code-Stil
- PEP 8 konform
- Ausführliche deutsche Kommentare
- Type Hints wo möglich

### Testing
```bash
# Tests ausführen (wenn implementiert)
python -m pytest tests/
```

### Build für Deployment
```bash
# PyInstaller für .exe (Windows)
pip install pyinstaller
pyinstaller --onedir --windowed src/main.py
```

## 📝 Changelog

### Version 1.0.0 (Initial Release)
- Grundlegende Lieferungsverwaltung
- KI-gestützte Dokumentenerkennung
- Barcode-Generierung
- Sichtprüfung und Qualitätskontrolle

## 📞 Support

Bei Fragen oder Problemen:
1. Issues im Repository erstellen
2. Dokumentation prüfen
3. Log-Dateien in `~/.medealis/logs/` überprüfen

## 📄 Lizenz

[Lizenz hier einfügen - z.B. MIT, Apache 2.0, oder Proprietary]

---

**Entwickelt für Medealis GmbH** - Professionelle Verwaltung medizinischer Geräte-Lieferungen