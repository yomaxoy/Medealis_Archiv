# Dokumenten-Speicherung Architektur

## 📋 Übersicht

Komplette Dokumentation der Dokumenten-Speicher-Architektur im Medealis-System.

---

## 🏗️ Architektur-Komponenten

### **1. DocumentStorageService**
**Datei:** [`src/warehouse/application/services/document_storage/document_storage_service.py`](src/warehouse/application/services/document_storage/document_storage_service.py)

**Verantwortlichkeit:** Zentrale API für alle Dokument-Speicher-Operationen

**Hauptmethoden:**
- `save_document()` - Speichert Dokumente (PDB, Begleitschein, etc.)
- `save_delivery_slip_pdf()` - Speichert Lieferscheine
- `get_document_path()` - Holt Dokumenten-Pfad
- `get_documents_for_merge()` - Lädt Dokumente für PDF-Merge

**Speicher-Logik:**
```
1. SharePoint aktiviert (USE_SHAREPOINT=true)?
   → JA: Upload zu SharePoint (primär)
         Bei Fehler: Lokale Speicherung (fallback)
   → NEIN: Nur lokale Speicherung

2. Pfad-Auflösung via PathResolver
3. Validierung via StorageValidator
4. Metadaten via StorageContext
```

---

### **2. PathResolver**
**Datei:** [`src/warehouse/application/services/document_storage/path_resolver.py`](src/warehouse/application/services/document_storage/path_resolver.py)

**Verantwortlichkeit:** EINZIGE Stelle für Pfad-Erstellung im System

**Properties:**
- `base_storage_path` → `C:\Users\{user}\Medealis\Wareneingang\` (lokal)
- `server_storage_path` → `A:\Qualitätsmanagement\...\Produktionsunterlagen\` (Server) **NEU**
- `document_output_path` → `C:\Users\{user}\.medealis\documents\`
- `temp_path` → `C:\Users\{user}\.medealis\temp\`

**Methoden für LOKALE Speicherung:**
- `resolve_storage_path(context)` - Vollständiger Pfad: `{Base}\{Supplier}\{Manufacturer}\{Article}\{Batch}\{Delivery}\`
- `resolve_delivery_slip_path(supplier)` - Lieferschein-Pfad: `{Base}\{Supplier}\Lieferscheine\`
- `resolve_document_output_path(filename)` - Temporärer Output-Pfad
- `resolve_temp_path(filename)` - Temporärer Verarbeitungs-Pfad

**Methoden für SERVER-Speicherung:** ⭐ **NEU**
- `resolve_server_storage_path(context)` - Server-Pfad: `A:\...\{Supplier}\{Manufacturer}\{Article}\{Batch}\{Delivery}\`
- `resolve_server_delivery_slip_path(supplier)` - Server-Lieferschein: `A:\...\{Supplier}\Lieferscheine\`

**Methoden für SHAREPOINT-Pfade:**
- `resolve_sharepoint_path(document_type, context)` - SharePoint-Pfad mit forward slashes

**Hilfsmethoden:**
- `create_folder_structure(path)` - Erstellt Ordnerstruktur
- `move_file(source, target_context, filename)` - Verschiebt Dateien
- `cleanup_temp_files(max_age_hours)` - Räumt Temp-Dateien auf
- `_clean_path_component(component)` - Bereinigt Pfad-Teile (Umlaute, Sonderzeichen)
- `_clean_filename(filename)` - Bereinigt Dateinamen

---

### **3. StorageContext**
**Datei:** [`src/warehouse/application/services/document_storage/storage_context.py`](src/warehouse/application/services/document_storage/storage_context.py)

**Verantwortlichkeit:** Holt und bereitet Metadaten für Storage-Operationen auf

**StorageContextData (Dataclass):**
```python
@dataclass
class StorageContextData:
    # Pflichtfelder
    batch_number: str
    delivery_number: str

    # Artikel
    article_number: str
    article_description: str

    # Lieferant
    supplier_name: str
    supplier_normalized: str

    # Hersteller (abgeleitet aus article_number)
    manufacturer: str

    # Zusätzliche Daten
    quantity: int
    unit: str
    employee_name: str
    delivery_date: str
    order_number: str

    # Metadaten
    context_source: str  # "database", "manual", "fallback"
    completeness_score: float  # 0.0 - 1.0
```

**Hauptmethoden:**
- `get_complete_storage_context()` - SINGLE SOURCE OF TRUTH für Storage-Daten
- `determine_manufacturer(article_number)` - Bestimmt Hersteller aus Artikelnummer
- `_resolve_supplier_data()` - Normalisiert Lieferanten-Namen
- `_calculate_completeness_score()` - Berechnet Daten-Vollständigkeit

**Hersteller-Bestimmung (Prefix-Mapping):**
```python
"MG" → "MegaGen"
"M"  → "Medentis"
"S"  → "Straumann"
"N"  → "Nobel Biocare"
"O"  → "Osstem"
# ... etc.
```

**Lieferanten-Normalisierung:**
```python
"primec" → "Primec GmbH"
"megagen" → "MEGAGEN"
"ctech" → "C-Tech"
# ... etc.
```

---

### **4. SharePointGraphClient**
**Datei:** [`src/warehouse/application/services/document_storage/sharepoint_graph_client.py`](src/warehouse/application/services/document_storage/sharepoint_graph_client.py)

**Verantwortlichkeit:** Upload/Download von SharePoint via Microsoft Graph API

**Konfiguration:**
- Nutzt Azure AD OAuth
- Credentials aus `.env` oder Streamlit Secrets
- Graph API Endpoint: `https://graph.microsoft.com/v1.0`

**Hauptmethoden:**
- `upload_document(document_data, sharepoint_path, filename)` - Upload zu SharePoint
- `download_document(sharepoint_path, filename)` - Download von SharePoint
- `list_files(sharepoint_path)` - Listet Dateien in Ordner
- `test_connection()` - Testet SharePoint-Verbindung
- `is_available()` - Prüft ob konfiguriert

**Authentifizierung:**
```python
# Azure AD Token Request:
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
scope = "https://graph.microsoft.com/.default"
```

---

### **5. StorageValidator**
**Datei:** [`src/warehouse/application/services/document_storage/storage_validator.py`](src/warehouse/application/services/document_storage/storage_validator.py)

**Verantwortlichkeit:** Validiert Dokumente und Pfade vor Speicherung

**Validation Levels:**
- `STRICT` - Maximale Sicherheit
- `STANDARD` - Balance zwischen Sicherheit und Usability (default)
- `PERMISSIVE` - Minimale Validierung

**Hauptmethoden:**
- `validate_document_data(document_data, filename)` - Validiert Dokument-Inhalte
- `validate_storage_context(context)` - Validiert Storage-Kontext
- `validate_storage_permissions(path)` - Prüft Schreibrechte
- `sanitize_filename(filename)` - Bereinigt Dateinamen (Sicherheit)

---

### **6. EnvironmentConfig**
**Datei:** [`src/warehouse/shared/config/environment_config.py`](src/warehouse/shared/config/environment_config.py)

**Verantwortlichkeit:** Zentrale Konfigurations-Verwaltung

**Konfigurationsquellen (Priorität):**
1. System-Umgebungsvariablen (höchste Priorität)
2. Streamlit Secrets (`.streamlit/secrets.toml`)
3. .env Datei
4. Default-Werte (niedrigste Priorität)

**Wichtige Konfigurationen:**
```bash
# SharePoint
SHAREPOINT_SITE_URL=https://medealis.sharepoint.com
SHAREPOINT_CLIENT_ID=...
SHAREPOINT_CLIENT_SECRET=...
SHAREPOINT_TENANT_ID=...

# Storage-Modus
USE_SHAREPOINT=false  # true = SharePoint, false = nur lokal/Server
```

**Hauptmethoden:**
- `get_sharepoint_config()` - Holt SharePoint-Konfiguration
- `is_sharepoint_enabled()` - Prüft ob SharePoint aktiviert ist
- `get_config_status()` - Gibt Config-Status zurück

---

## 📁 Pfad-Strukturen

### **Lokale Speicherung:**
```
C:\Users\{user}\Medealis\Wareneingang\
├── Primec_GmbH\
│   ├── MegaGen\
│   │   └── MG0001\
│   │       └── 20240415-1234\
│   │           └── LS24-077\
│   │               ├── PDB_MG0001.pdf
│   │               ├── Begleitschein.pdf
│   │               └── Sichtkontrolle.pdf
│   └── Lieferscheine\
│       ├── Lieferschein_LS24-077_2024-04-15.pdf
│       └── ...
└── ...
```

### **Server-Speicherung:** ⭐ **NEU**
```
A:\Qualitätsmanagement\QM_Medealis\03. Produkte\Chargenverwaltung\Produktionsunterlagen\
├── Primec_GmbH\
│   ├── MegaGen\
│   │   └── MG0001\
│   │       └── 20240415-1234\
│   │           └── LS24-077\
│   │               ├── PDB_MG0001.pdf
│   │               ├── Begleitschein.pdf
│   │               └── Sichtkontrolle.pdf
│   └── Lieferscheine\
│       ├── Lieferschein_LS24-077_2024-04-15.pdf
│       └── ...
└── ...
```

**Hinweis:** Struktur ist **identisch**, nur unterschiedlicher Basis-Pfad!

### **SharePoint-Speicherung:**
```
QM_System_Neu/08_Messung_Analyse/06_Überwachung_Produkte/Produktionsunterlagen/
├── Primec_GmbH/
│   ├── MegaGen/
│   │   └── MG0001/
│   │       └── 20240415-1234/
│   │           └── LS24-077/
│   │               ├── PDB_MG0001.pdf
│   │               └── ...
│   └── Lieferscheine/
│       └── ...
└── ...
```

**Unterschied:** Forward slashes `/` statt Backslashes `\`

---

## 🔄 Speicher-Workflow

### **Ablauf beim Dokument-Speichern:**

```
1. DocumentStorageService.save_document() aufgerufen
   ↓
2. StorageContext.get_complete_storage_context()
   → Holt Metadaten aus Datenbank
   → Normalisiert Lieferant
   → Bestimmt Hersteller
   ↓
3. StorageValidator.validate_storage_context()
   → Prüft Vollständigkeit
   ↓
4. StorageValidator.validate_document_data()
   → Prüft Dokument-Inhalte
   ↓
5. StorageValidator.sanitize_filename()
   → Bereinigt Dateiname
   ↓
6. PathResolver.resolve_storage_path() ODER
   PathResolver.resolve_server_storage_path() ⭐ NEU
   → Erstellt Pfad-Struktur
   ↓
7. StorageValidator.validate_storage_permissions()
   → Prüft Schreibrechte
   ↓
8. [OPTIONAL] SharePointGraphClient.upload_document()
   → Upload zu SharePoint (falls aktiviert)
   ↓
9. Lokale/Server Speicherung (mit open/write)
   → Fallback wenn SharePoint fehlschlägt
   ↓
10. StorageResult zurückgeben
    → Enthält Pfad, URL, Metadaten, Warnungen
```

---

## 🎯 Verwendung der Services

### **Standard-Pattern für Dokument-Speicherung:**

```python
from warehouse.application.services.document_storage import document_storage_service

# Dokument speichern
result = document_storage_service.save_document(
    document_data=pdf_bytes,
    document_name="PDB_MG0001_20240415-1234.pdf",
    document_type="PDB",
    batch_number="20240415-1234",
    delivery_number="LS24-077",
    article_number="MG0001",
    supplier_name="Primec GmbH"
)

if result.success:
    print(f"✅ Dokument gespeichert!")
    print(f"   Lokal: {result.file_path}")
    print(f"   SharePoint: {result.sharepoint_url}")
    print(f"   Modus: {result.metadata['storage_mode']}")
else:
    print(f"❌ Fehler: {result.error}")
```

### **Server-Storage nutzen (NEU):**

```python
from warehouse.application.services.document_storage.path_resolver import path_resolver
from warehouse.application.services.document_storage.storage_context import storage_context
from pathlib import Path

# 1. Context holen
context = storage_context.get_complete_storage_context(
    batch_number="20240415-1234",
    delivery_number="LS24-077",
    article_number="MG0001"
)

# 2. Server-Pfad auflösen
if Path("A:\\").exists():
    # Server verfügbar
    path_result = path_resolver.resolve_server_storage_path(context, create_folders=True)
    storage_location = "server"
else:
    # Fallback: Lokal
    path_result = path_resolver.resolve_storage_path(context, create_folders=True)
    storage_location = "local"

# 3. Speichern
if path_result.success:
    file_path = path_result.path / "dokument.pdf"
    with open(file_path, 'wb') as f:
        f.write(document_data)
    print(f"✅ Gespeichert auf {storage_location}: {file_path}")
```

---

## 🔧 Konfiguration

### **.env Datei:**

```bash
# SharePoint Configuration (optional)
SHAREPOINT_SITE_URL=https://medealis.sharepoint.com
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_TENANT_ID=your-tenant-id

# Storage Mode
USE_SHAREPOINT=false  # false = nur lokal/Server, true = SharePoint + Fallback

# Debug
DEBUG=false
```

### **Streamlit Secrets (`.streamlit/secrets.toml`):**

```toml
[sharepoint]
site_url = "https://medealis.sharepoint.com"
client_id = "your-client-id"
client_secret = "your-client-secret"
tenant_id = "your-tenant-id"

[storage]
use_sharepoint = false
```

---

## 📊 Storage-Modi Vergleich

| Modus | Speicherort | Verfügbarkeit | Performance | Backup | Use Case |
|-------|-------------|---------------|-------------|--------|----------|
| **Lokal** | `C:\Users\...` | Immer | Sehr schnell | Manuell | Entwicklung, Offline |
| **Server** ⭐ | `A:\...` | Im Netzwerk | Schnell | Automatisch | **Produktion (empfohlen)** |
| **SharePoint** | Cloud | Mit Internet | Langsam | Cloud-Backup | Cloud-First, Remote |
| **Hybrid** | SharePoint + Lokal | Immer | Mittel | Beide | Maximale Ausfallsicherheit |

---

## 🚀 Migration SharePoint → Server

### **Schritt 1: .env anpassen**
```bash
USE_SHAREPOINT=false
```

### **Schritt 2: Code anpassen**

**In allen Services die `document_storage_service` nutzen:**

Keine Änderung nötig, da `DocumentStorageService` intern `PathResolver` nutzt!

**Für direkte PathResolver-Nutzung:**

```python
# ALT (lokal):
path_result = path_resolver.resolve_storage_path(context, create_folders=True)

# NEU (Server):
path_result = path_resolver.resolve_server_storage_path(context, create_folders=True)
```

### **Schritt 3: Testen**
```bash
python test_server_storage.py
```

---

## 📚 Weitere Dokumentation

- [`SERVER_STORAGE_ANLEITUNG.md`](SERVER_STORAGE_ANLEITUNG.md) - Detaillierte Anleitung für Server-Storage
- [`test_server_storage.py`](test_server_storage.py) - Test-Script für Server-Funktionalität
- [`.env.example`](.env.example) - Beispiel-Konfiguration

---

## 🔍 Wichtige Dateien

```
src/warehouse/application/services/document_storage/
├── document_storage_service.py    # Haupt-Service
├── path_resolver.py                # Pfad-Erstellung (inkl. Server ⭐)
├── storage_context.py              # Metadaten-Verwaltung
├── storage_validator.py            # Validierung
├── sharepoint_graph_client.py      # SharePoint-Integration
└── __init__.py

src/warehouse/shared/config/
└── environment_config.py           # Konfiguration

test_server_storage.py              # Server-Tests ⭐
SERVER_STORAGE_ANLEITUNG.md         # Server-Anleitung ⭐
DOKUMENTEN_SPEICHERUNG_ARCHITEKTUR.md  # Diese Datei
```

---

**Stand:** 2025-01-13
**Version:** 2.0 (mit Server-Storage)
**Status:** Produktionsreif ✅
