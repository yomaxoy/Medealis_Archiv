# Medealis Archiv Management System

Ein Python-basiertes Verwaltungssystem für den Wareneingang bei Medealis GmbH.

## 🚀 Features

- **📄 Lieferschein-Verarbeitung**: Automatische Texterkennung aus PDF-Dokumenten mit KI-Unterstützung
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

   # Optional: Für DSGVO-konforme lokale OCR-Funktionalität:
   pip install -r requirements_local_ocr.txt
   ```

4. **API Keys konfigurieren** (optional):
   - **Claude AI**: Setze `ANTHROPIC_API_KEY` in `.env` für KI-gestützte Extraktion
   - **OpenAI**: Setze `OPENAI_API_KEY` in `.env` für alternative KI-Features
   - **Lokal**: Nutze OCR ohne API-Keys für DSGVO-Konformität

5. **Anwendung starten**:
   ```bash
   # Streamlit Web-Interface (Hauptanwendung):
   streamlit run src/warehouse/presentation/admin/main_admin_app.py

   # Oder CLI-Interface:
   python src/main.py
   ```

## 📁 Projektstruktur

```
medealis-archiv/
├── src/                            # Source Code
│   ├── warehouse/                  # Clean Architecture Implementation
│   │   ├── domain/                # Domain Layer (Business Logic)
│   │   │   ├── entities/          # Business Entities (Item, Delivery, Supplier, Order)
│   │   │   ├── value_objects/     # Value Objects (ArticleNumber, BatchNumber)
│   │   │   ├── enums/            # Domain Enums (ItemStatus, DeliveryStatus)
│   │   │   ├── repositories/     # Repository Interfaces
│   │   │   ├── services/         # Domain Services (BarcodeService, InspectionService)
│   │   │   ├── events/          # Domain Events
│   │   │   └── exceptions/      # Domain Exceptions
│   │   ├── application/          # Application Layer (Use Cases)
│   │   │   └── services/        # Application Services (DeliveryService, ItemService)
│   │   ├── infrastructure/      # Infrastructure Layer (Technical Details)
│   │   │   ├── database/        # SQLAlchemy Implementation
│   │   │   │   ├── models/      # Database Models
│   │   │   │   ├── repositories/ # Repository Implementations
│   │   │   │   └── connection.py # Database Connection
│   │   │   ├── external_services/ # API Integrations (Claude, OpenAI)
│   │   │   └── file_system/     # File Operations
│   │   ├── presentation/        # Presentation Layer (UI)
│   │   │   └── admin/          # Admin Interface (Streamlit-based)
│   │   │       ├── views/      # UI Views
│   │   │       ├── popups/     # Modal Dialogs
│   │   │       ├── utils/      # UI Utilities
│   │   │       └── main_admin_app.py # Main Streamlit Application
│   │   └── shared/             # Shared Utilities
│   │       └── utils/          # Common Utilities (date_parser.py)
│   ├── reset_DB.py             # Database Reset Utility (Domain-based)
│   ├── simple_reset_db.py      # Simple Database Reset Utility
│   └── main.py                 # CLI Entry Point
├── resources/                   # Application Resources
│   └── templates/              # Document Templates
│       ├── Begleitschein.txt
│       ├── Sichtkontrolle.txt
│       ├── Fo00040_PDB_Template.docx
│       ├── Fo00141_Sichtkontrolle.docx
│       └── Fo0113_Wareneingangskontrolle.docx
├── tests/                      # Test Files
│   └── test_clean_architecture.py # Architecture Integration Tests
├── config/                     # Configuration Files
│   └── settings.py             # Application Settings
├── requirements.txt            # Python Dependencies
├── requirements_local_ocr.txt  # OCR Dependencies (DSGVO-compliant)
├── pyproject.toml             # Modern Python Package Configuration
├── DEVELOPMENT_NOTES.md        # Development Documentation
├── README.md                  # This file
└── .gitignore                 # Git ignore patterns
```

## 🔧 Verwendung

### 1. Neue Lieferung erfassen
1. "Neue Lieferung" im Hauptmenü wählen
2. Mitarbeitername eingeben
3. Lieferschein-Dokument (.pdf) hochladen
4. OCR-Texterkennung und strukturierte Datenextraktion

### 2. Wareneingangskontrolle
1. "Wareneingangskontrolle" öffnen
2. Lieferschein auswählen
3. Artikel-Daten überprüfen und bestätigen (Artikelnummer, Chargennummer, Anzahl)
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

- API Keys werden verschlüsselt gespeichert (Fernet-Verschlüsselung)
- Lokale SQLite-Datenbank ohne Netzwerkzugriff
- DSGVO-konforme OCR-Verarbeitung (keine Datenübertragung an externe APIs)
- Konfigurationsdateien werden im Benutzerverzeichnis gespeichert

## 🏗️ Architektur

Das System folgt der **Clean Architecture** mit **Domain-Driven Design (DDD)**:

### 🎯 Architektur-Ebenen

#### **1. Domain Layer (Geschäftslogik)**
- **Entities**: Kern-Geschäftsobjekte (Item, Delivery, Supplier, Order)
  - `Item`: Artikel mit flexiblem Status-System und Rückverfolgbarkeit
  - `Delivery`: Lieferungs-Aggregat mit automatischem Status-Management
- **Value Objects**: Unveränderliche Objekte (ArticleNumber, BatchNumber)
- **Enums**: Geschäftswerte (ItemStatus, DeliveryStatus, PriorityLevel)
- **Domain Services**: Geschäftslogik (BarcodeService, InspectionService)
- **Repository Interfaces**: Abstraktionen für Datenzugriff
- **Domain Events**: Geschäftsereignisse für Entkopplung
- **Exceptions**: Domänen-spezifische Fehlerbehandlung

#### **2. Application Layer (Use Cases)**
- **Application Services**: Orchestrierung von Use Cases
  - `DeliveryService`: Koordiniert Lieferungs-Workflows
  - `ItemService`: Artikel-Management und Sichtprüfung
  - `SupplierService`: Lieferanten-Verwaltung mit find-or-create Pattern
  - `DocumentService`: Template-basierte Dokumentenerstellung

#### **3. Infrastructure Layer (Technische Details)**
- **Database**: SQLAlchemy mit SQLite
  - **Models**: ORM-Entitäten für Persistierung
  - **Repositories**: Konkrete Repository-Implementierungen
  - **Mappers**: Domain ↔ Infrastructure Mapping
- **External Services**: Claude AI-Integration (optional)
- **File System**: Dokumentenverwaltung

#### **4. Presentation Layer (Benutzeroberfläche)**
- **Admin Interface**: Streamlit-basierte Web-Anwendung
- **Views**: Delivery Management, Item Management, Document Generation
- **Popups**: Modal Dialoge für komplexe Operationen
- **Utils**: UI-spezifische Hilfsfunktionen

### 🔧 Design Patterns

#### **Domain-Driven Design**
- **Aggregate Pattern**: Delivery als Aggregat Root mit Items
- **Repository Pattern**: Abstrakte Datenzugriff-Schnittstellen
- **Value Object Pattern**: ArticleNumber, BatchNumber mit Validierung
- **Domain Events**: Entkoppelte Kommunikation zwischen Kontexten

#### **Clean Architecture Patterns**
- **Dependency Inversion**: Domain abhängt nicht von Infrastructure
- **Interface Segregation**: Kleine, spezifische Repository-Interfaces
- **Single Responsibility**: Jede Schicht hat eine klare Verantwortung

#### **Weitere Patterns**
- **Factory Pattern**: Entity-Erstellung mit Validierung
- **Strategy Pattern**: Verschiedene Status-Implementierungen
- **Observer Pattern**: Event-Handling in der GUI
- **Unit of Work**: Transaktionale Konsistenz in Repositories

### 📊 Status-Management-System

#### **Artikel-Workflow (Item)**
```
ARTIKEL_ANGELEGT → DATEN_GEPRUEFT → SICHT_GEPRUEFT → DOKUMENTE_GEPRUEFT → VERMESSEN → ABGESCHLOSSEN
                                                                           ↓
                                                                      AUSSCHUSS
```

#### **Lieferungs-Workflow (Delivery)**
```
EMPFANGEN → ERFASST → IN_BEARBEITUNG → ABGESCHLOSSEN
```

- **Automatische Status-Updates**: Lieferungsstatus wird automatisch basierend auf Artikel-Status aktualisiert
- **Dictionary-basiertes Tracking**: Jeder Arbeitsschritt wird mit Zeitstempel und Mitarbeiter protokolliert
- **Validation Logic**: Geschäftsregeln verhindern ungültige Zustandsübergänge

### 🗄️ Datenmodell

#### **Kern-Entitäten**
- **Item**: Artikel mit Rückverfolgbarkeit (ArticleNumber + BatchNumber + DeliveryNumber)
- **Delivery**: Lieferungs-Aggregat mit automatischem Status-Management
- **Supplier**: Lieferanten-Stammdaten
- **Order**: Bestellungs-Kontext (geplante Erweiterung)

#### **Rückverfolgbarkeit**
- **Unique Identifier**: `{ArticleNumber}#{BatchNumber}#{DeliveryNumber}`
- **Audit Trail**: Vollständige Nachverfolgung aller Änderungen
- **Compliance**: Medizinprodukte-konforme Dokumentation

## 🚨 Bekannte Einschränkungen

- **Windows-abhängig**: Office-Integration funktioniert nur unter Windows
- **Claude API**: Internetverbindung für KI-Features erforderlich (optional)
- **Single-User**: Keine Multi-User-Unterstützung
- **Lokale Datenbank**: Keine zentrale Datenhaltung

## 🤝 Entwicklung

### Code-Stil
- PEP 8 konform
- Ausführliche deutsche Kommentare
- Type Hints wo möglich

### Testing
```bash
# Architektur-Tests ausführen
python tests/test_clean_architecture.py
```

### Build für Deployment
```bash
# PyInstaller für .exe (Windows)
pip install pyinstaller
pyinstaller --onedir --windowed src/warehouse/presentation/admin/main_admin_app.py
```

## 📝 Changelog

### Version 1.0.0 (Clean Architecture Implementation)
- **Clean Architecture**: Domain-Driven Design mit klarer Schichtentrennung
- **OCR-basierte Dokumentenerkennung**: DSGVO-konforme Lieferschein-Verarbeitung
- **Lieferungsverwaltung**: Vollständiger Workflow mit Status-Tracking
- **Artikel-Management**: Sichtprüfung und Qualitätskontrolle
- **Template-System**: Automatische Dokumentenerstellung (PDB, Begleitschein, Sichtkontrolle)
- **Barcode-Generierung**: Code 128 für Artikel-Identifikation

## 📞 Support

Bei Fragen oder Problemen:
1. Issues im Repository erstellen
2. Dokumentation prüfen
3. Log-Dateien in `~/.medealis/logs/` überprüfen

## 📄 Lizenz

[Lizenz hier einfügen - z.B. MIT, Apache 2.0, oder Proprietary]

---

**Entwickelt für Medealis GmbH** - Professionelle Verwaltung medizinischer Geräte-Lieferungen