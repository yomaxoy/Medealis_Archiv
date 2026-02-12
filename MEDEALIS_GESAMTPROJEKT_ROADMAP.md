# Medealis QMS-System: Gesamtprojekt & Roadmap

**Projekt:** Intelligentes Qualitätsmanagementsystem für Medizinprodukte-Hersteller
**Produktbereich:** Dental Locator Abutments (Klasse IIa nach MDR 2017/745)
**Letzte Aktualisierung:** 2025-02-11
**Status:** Phase 1 abgeschlossen, Phase 2 in Planung

---

## Inhaltsverzeichnis

1. [Executive Summary](#executive-summary)
2. [Aktueller Stand (Was ist implementiert)](#aktueller-stand)
3. [Technologie-Stack Überblick](#technologie-stack)
4. [Detaillierter Migrationsplan](#migrationsplan)
5. [Zeitplan & Meilensteine](#zeitplan)
6. [Risiken & Mitigation](#risiken)
7. [Ressourcenplanung](#ressourcen)

---

## Executive Summary {#executive-summary}

### Vision

Ein **vollständig KI-gestütztes QMS**, das:
- ✅ Wareneingang automatisiert (OCR, Barcode, QR-Code)
- ✅ QM-Berichte automatisch erstellt (PMS, CAPA, Lieferantenbewertungen)
- ✅ Human-in-the-Loop für Compliance (Genehmigungsworkflow)
- ✅ Audit-Trail für ISO 13485 & MDR konform
- ✅ Flexible KI-Provider-Wahl (Claude, GPT-4, Gemini, Ollama)

### Projektphasen

| Phase | Zeitraum | Status | Beschreibung |
|-------|----------|--------|--------------|
| **Phase 0** | Q4 2024 | ✅ Abgeschlossen | Warehouse-App mit Wareneingang |
| **Phase 1** | Jan-Feb 2025 | ✅ Abgeschlossen | KI-Abstraktion + MCP-Server |
| **Phase 2** | Feb-Mär 2025 | 🔄 In Planung | NAS/SharePoint MCP + Approval-System |
| **Phase 3** | Mär-Apr 2025 | 📋 Geplant | FastAPI Migration + Agents |
| **Phase 4** | Apr-Mai 2025 | 📋 Geplant | Validierung + Audit-Vorbereitung |
| **Phase 5** | Jun 2025 | 📋 Geplant | Produktiv-Rollout |

---

## Aktueller Stand (Was ist implementiert) {#aktueller-stand}

### ✅ Phase 0: Warehouse-App (Wareneingang) - ABGESCHLOSSEN

**Implementiert:** Q4 2024

#### Architektur

```
src/warehouse/
├── domain/                  # Clean Architecture
│   ├── entities/           # Customer, ItemInfo, Delivery, etc.
│   ├── value_objects/      # ArticleNumber, Barcode, etc.
│   └── exceptions/         # Domain-spezifische Fehler
│
├── application/
│   └── services/           # Business-Logik
│       ├── customer_service.py
│       ├── item_info_service.py
│       ├── delivery_service.py
│       └── document_generation/
│           ├── barcode_generator.py
│           ├── delivery_note_generator.py
│           └── receipt_generator.py
│
├── infrastructure/
│   ├── database/
│   │   ├── models/         # SQLAlchemy Models
│   │   ├── repositories/   # Repository Pattern
│   │   └── connection.py   # DB Connection
│   └── ocr/                # Tesseract OCR
│
└── presentation/
    └── user/
        └── views/
            └── main_user_view.py  # Streamlit UI
```

#### Features

1. **Lieferschein-Scan (OCR)**
   - Tesseract OCR-Integration
   - Automatische Texterkennung
   - Manuelle Korrekturmöglichkeit

2. **Wareneingang-Erfassung**
   - Artikel-Zuordnung
   - Chargen-Verwaltung
   - Menge, Lagerort

3. **Dokumenten-Generierung**
   - Barcode-Generierung (Code128)
   - Begleitschein (DOCX)
   - Wareneingangsprotokoll (DOCX)
   - QR-Code für ItemInfo (geplant fertiggestellt)

4. **Datenbank**
   - PostgreSQL (Docker)
   - SQLAlchemy ORM
   - Clean Architecture Pattern

5. **User-Management**
   - Login/Logout
   - Rollen: Admin, Manager, Operator, Viewer
   - Berechtigungen (Permission-System)
   - Session-Management

#### Technologie

- **Backend:** Python 3.11+
- **Framework:** Streamlit
- **ORM:** SQLAlchemy 2.0
- **Datenbank:** PostgreSQL 15 (Docker)
- **OCR:** Tesseract 5.0
- **Dokumenten:** python-docx, qrcode, python-barcode

#### Deployment

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: medealis_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: medealis_warehouse
```

```bash
# Start
docker-compose up -d
streamlit run src/warehouse/presentation/user/views/main_user_view.py
```

**Status:** ✅ Produktiv im Einsatz (lokale Entwicklungsumgebung)

---

### ✅ Phase 1: KI-Abstraktion + MCP-Server - ABGESCHLOSSEN

**Implementiert:** Jan-Feb 2025

#### 1.1 Zentrale KI-Service-Schicht

**Verzeichnis:** `src/ai_service/`

**Dateien:**
```
src/ai_service/
├── __init__.py
├── ai_client.py        # Multi-Provider Client (305 Zeilen)
├── config.py           # Model-Konfiguration (120 Zeilen)
└── prompts.py          # System-Prompt Repository (450 Zeilen)
```

**Features:**

✅ **Multi-Provider-Unterstützung:**
- Anthropic Claude (claude-3-5-sonnet, claude-3-5-haiku)
- OpenAI (gpt-4-turbo, gpt-4o)
- Azure OpenAI
- Google Gemini (gemini-1.5-pro)
- Ollama (lokale Modelle: llama3)

✅ **Einheitliche API:**
```python
from src.ai_service import AIClient, PromptType

# Modell aus .env oder explizit
client = AIClient()  # oder: AIClient(model_name="gpt-4o")

response = client.generate(
    prompt="Erstelle Lieferantenbewertung für SUP-001",
    prompt_type=PromptType.SUPPLIER_EVALUATION
)
```

✅ **Vorgefertigte System-Prompts:**

| Prompt-Typ | Verwendung | Status |
|------------|------------|--------|
| `PMS_RESEARCH` | Post-Market Surveillance Recherche | ✅ |
| `CAPA_ANALYSIS` | CAPA-Berichte (8D-Methodik) | ✅ |
| `SUPPLIER_EVALUATION` | Lieferantenbewertung nach ISO 13485 | ✅ |
| `DOCUMENT_CONTROL` | Dokumentenlenkung & -überwachung | ✅ |
| `DATA_EXTRACTION` | Datenextraktion aus Rohdaten | ✅ |
| `REPORT_GENERATION` | Allgemeine QM-Berichte | ✅ |
| `RISK_ASSESSMENT` | Risikobewertung nach ISO 14971 | ✅ |

**Vorteil:** Modellwechsel über `.env` ohne Code-Änderung!

#### 1.2 MCP-Server: QMS-Datenbank

**Verzeichnis:** `mcp-servers/qms_database/`

**Dateien:**
```
mcp-servers/qms_database/
├── server.py           # MCP-Server mit 7 Tools (620 Zeilen)
├── audit.py            # Audit-Logging-System (280 Zeilen)
├── config.py           # DB-Konfiguration (110 Zeilen)
└── pyproject.toml      # Dependencies
```

**MCP-Tools (für Claude Code):**

| Tool | Beschreibung | Parameter |
|------|-------------|-----------|
| `get_supplier_data` | Lieferant-Stammdaten + Lieferungen + Reklamationen | `supplier_id` |
| `get_open_capas` | Offene CAPA-Vorgänge | `priority` (optional) |
| `get_expiring_documents` | QM-Dokumente mit ablaufendem Review | `days` (default: 30) |
| `get_inspection_data` | Wareneingangsprüfungen | Filter, Limit |
| `query_database` | Freie SELECT-Queries (validiert) | `sql`, `timeout` |
| `list_available_tables` | Alle Tabellen mit Spalten | - |
| `get_database_statistics` | Anzahl Einträge pro Tabelle | - |

**Sicherheit:**

✅ **Read-Only Zugriff:**
- PostgreSQL: Separater User `qms_readonly`
- SQLite: `?mode=ro` Parameter
- Nur SELECT-Queries erlaubt

✅ **SQL-Injection-Schutz:**
```python
def validate_sql_query(sql: str) -> tuple[bool, str]:
    if not sql.strip().upper().startswith("SELECT"):
        return False, "Nur SELECT erlaubt"

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", ...]
    if any(kw in sql.upper() for kw in forbidden):
        return False, "Verbotene Operation"

    return True, ""
```

✅ **Audit-Logging:**
- Jede Operation wird protokolliert
- SQLite-Datenbank: `data/audit_logs.db`
- Felder: Timestamp, Server, Tool, User, Params, Result, Error, Duration

**Tabellen-Whitelist:**
```python
ALLOWED_TABLES = {
    "suppliers", "deliveries", "inspections",
    "capas", "documents", "articles", "complaints"
}
```

**Claude Code Integration:**

`.claude/settings.json`:
```json
{
  "mcpServers": {
    "qms-database": {
      "command": "uv",
      "args": ["run", "--directory", "mcp-servers/qms_database", "server.py"]
    }
  }
}
```

**Usage:**
```bash
claude

Du: Liste alle verfügbaren Tabellen auf.
Du: Zeige mir Lieferantendaten für SUP-001.
Du: Wie viele offene CAPAs gibt es?
```

**Status:** ✅ Funktionsfähig, getestet im MCP Inspector

---

## Technologie-Stack Überblick {#technologie-stack}

### Aktuell (Phase 0 + 1)

```
┌─────────────────────────────────────────────────┐
│         Presentation Layer                      │
│  Streamlit (Warehouse) | Claude Code (QMS)     │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         Application Layer                       │
│  src/warehouse/application/services/            │
│  src/ai_service/ai_client.py                    │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         Infrastructure Layer                    │
│  SQLAlchemy ORM | MCP-Server | OCR              │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         Data Layer                              │
│  PostgreSQL (Docker) | Audit-Log (SQLite)       │
└─────────────────────────────────────────────────┘
```

### Zukünftig (Phase 3+)

```
┌─────────────────────────────────────────────────┐
│         Frontend                                │
│  HTMX + Alpine.js + TailwindCSS                 │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         API Layer                               │
│  FastAPI (REST API mit OpenAPI)                 │
│  • JWT Auth | RBAC | Middleware                 │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         Application Layer                       │
│  Services + Domain Logic (Clean Architecture)   │
│  • AI Service | MCP Clients | Agents            │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         Infrastructure                          │
│  SQLAlchemy | MCP-Server | Event Bus            │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│         Data Sources                            │
│  PostgreSQL | NAS (SMB) | SharePoint | Files    │
└─────────────────────────────────────────────────┘
```

---

## Detaillierter Migrationsplan {#migrationsplan}

### Phase 2: Datenquellen-Erweiterung + Approval-System

**Zeitraum:** Feb-Mär 2025 (6 Wochen)
**Ziel:** Vollständiger Read-Only Zugriff + Human-in-the-Loop

---

#### Woche 1-2: NAS-Filesystem MCP-Server

**Aufgaben:**

1. **NAS Read-Only User erstellen**
   ```bash
   # Auf NAS (Synology/QNAP Admin-Interface):
   # User: qms_readonly_nas
   # Berechtigung: Nur Lesen auf Share "QMS_Dokumente"
   # Kein Schreibzugriff!
   ```

2. **MCP-Server implementieren**

   **Dateien:**
   ```
   mcp-servers/nas_filesystem/
   ├── server.py           # MCP-Server
   ├── smb_client.py       # SMB-Wrapper
   ├── config.py           # NAS-Konfiguration
   └── pyproject.toml
   ```

   **Dependencies:**
   ```toml
   [project.dependencies]
   mcp = ">=1.1.2"
   smbprotocol = ">=1.10.0"  # Windows SMB
   ```

   **Tools:**
   - `list_nas_directory(path)` – Verzeichnisinhalt
   - `read_nas_file(filepath, max_size_mb)` – Datei lesen (Text/JSON/CSV)
   - `search_nas_files(pattern, base_path)` – Dateisuche (rekursiv)

3. **Sicherheit**
   ```python
   # config.py
   NAS_CONFIG = {
       "server_ip": "192.168.1.100",
       "share_name": "QMS_Dokumente",
       "username": "qms_readonly_nas",
       "password": os.getenv("NAS_PASSWORD"),  # Nie im Code!
   }

   # Read-Only Verbindung
   conn = SMBConnection(..., use_ntlm_v2=True)
   # Nur listPath() und retrieveFile()
   # KEIN storeFile() oder deleteFiles()
   ```

4. **Testing**
   ```bash
   cd mcp-servers/nas_filesystem
   uv run mcp dev server.py

   # Im Inspector testen:
   list_nas_directory("/Lieferanten")
   read_nas_file("/Lieferanten/SUP-001/Audit_2024.txt")
   search_nas_files("Lieferantenbewertung*.docx", "/Lieferanten")
   ```

5. **Claude Code Integration**
   ```json
   // .claude/settings.json
   {
     "mcpServers": {
       "qms-database": { ... },
       "nas-filesystem": {
         "command": "uv",
         "args": ["run", "--directory", "mcp-servers/nas_filesystem", "server.py"],
         "env": {
           "NAS_PASSWORD": "${NAS_PASSWORD}"
         }
       }
     }
   }
   ```

**Deliverables:**
- ✅ Funktionierender NAS MCP-Server
- ✅ 3 Tools getestet
- ✅ Audit-Logging integriert
- ✅ Dokumentation

**Zeitaufwand:** 40 Stunden (2 Wochen)

---

#### Woche 3-4: SharePoint-Connector MCP-Server

**Aufgaben:**

1. **Azure AD App Registration**

   **In Azure Portal:**
   ```
   1. App Registrations → New Registration
      Name: "Medealis QMS Read-Only"

   2. API Permissions:
      - SharePoint → Application Permissions → Sites.Read.All
      - Admin Consent erteilen

   3. Certificates & Secrets:
      - New Client Secret → kopieren

   4. Overview:
      - Application (client) ID → kopieren
   ```

   **Umgebungsvariablen:**
   ```bash
   # .env
   SP_SITE_URL=https://deinefirma.sharepoint.com/sites/QMS
   SP_CLIENT_ID=12345678-1234-1234-1234-123456789abc
   SP_CLIENT_SECRET=dein~geheimer~wert
   ```

2. **MCP-Server implementieren**

   **Dateien:**
   ```
   mcp-servers/sharepoint_connector/
   ├── server.py           # MCP-Server
   ├── sp_auth.py          # OAuth2 Authentication
   ├── config.py
   └── pyproject.toml
   ```

   **Dependencies:**
   ```toml
   [project.dependencies]
   mcp = ">=1.1.2"
   Office365-REST-Python-Client = ">=2.5.0"
   ```

   **Tools:**
   - `list_sharepoint_folder(folder_path)` – Ordnerinhalt
   - `read_sharepoint_file(file_path)` – Datei herunterladen
   - `search_sharepoint(query, max_results)` – Volltextsuche

3. **Implementierung**
   ```python
   # server.py
   from office365.sharepoint.client_context import ClientContext
   from office365.runtime.auth.client_credential import ClientCredential

   def get_sp_context():
       credentials = ClientCredential(
           SP_CONFIG["client_id"],
           SP_CONFIG["client_secret"]
       )
       ctx = ClientContext(SP_CONFIG["site_url"]).with_credentials(credentials)
       return ctx

   @mcp.tool()
   def search_sharepoint(query: str, max_results: int = 50):
       ctx = get_sp_context()
       search = SearchQuery(query_text=query, row_limit=max_results)
       result = ctx.search.post_query(search)
       ctx.execute_query()
       return json.dumps(result.value.PrimaryQueryResult.RelevantResults)
   ```

4. **Berechtigungen prüfen**
   ```bash
   # Test: Kann App auf SharePoint zugreifen?
   python -c "
   from sharepoint_connector.sp_auth import get_sp_context
   ctx = get_sp_context()
   web = ctx.web.get().execute_query()
   print(f'Connected to: {web.title}')
   "
   ```

5. **Testing**
   ```bash
   cd mcp-servers/sharepoint_connector
   uv run mcp dev server.py
   ```

**Deliverables:**
- ✅ SharePoint MCP-Server
- ✅ OAuth2 funktioniert
- ✅ 3 Tools getestet
- ✅ Dokumentation

**Zeitaufwand:** 40 Stunden (2 Wochen)

---

#### Woche 5-6: Approval-Queue + Streamlit Dashboard

**Aufgaben:**

1. **Approval-Queue MCP-Server**

   **Dateien:**
   ```
   mcp-servers/approval_queue/
   ├── server.py           # Queue Handler
   ├── queue_db.py         # SQLite Queue
   ├── executor.py         # Write-Operationen ausführen
   └── pyproject.toml
   ```

   **Datenbank:**
   ```sql
   CREATE TABLE approval_requests (
       request_id TEXT PRIMARY KEY,
       timestamp TEXT NOT NULL,
       agent TEXT NOT NULL,
       operation_type TEXT NOT NULL,
       target_system TEXT NOT NULL,  -- 'nas', 'sharepoint', 'database'
       target_path TEXT,
       data TEXT NOT NULL,           -- JSON
       status TEXT DEFAULT 'pending',
       requester TEXT DEFAULT 'claude-agent',
       approver TEXT,
       approval_timestamp TEXT,
       rejection_reason TEXT,
       metadata TEXT
   );
   ```

   **Tools:**
   - `submit_for_approval(operation_type, target_system, target_path, data)`
   - `check_approval_status(request_id)`
   - `list_pending_approvals()`

   **Workflow:**
   ```
   1. Claude erstellt Dokument → submit_for_approval()
   2. Request landet in Queue (Status: pending)
   3. QMB sieht Request im Dashboard
   4. QMB prüft und genehmigt → Status: approved
   5. System führt Schreiboperation aus
   6. Audit-Log: Vollständiger Trail
   ```

2. **Streamlit Approval-Dashboard**

   **Dateien:**
   ```
   approval-dashboard/
   ├── app.py              # Hauptapp
   ├── auth.py             # User-Authentifizierung
   ├── components/
   │   ├── pending_requests.py
   │   ├── approval_history.py
   │   └── audit_viewer.py
   └── requirements.txt
   ```

   **Features:**
   - Login (nutzt bestehendes User-System)
   - Pending Approvals Liste
   - Vorschau des Dokuments/Daten
   - Approve/Reject Buttons
   - Kommentar-Funktion
   - Audit-Log Viewer

   **UI-Mockup:**
   ```
   ┌─────────────────────────────────────────────────┐
   │ 🔐 QMS Approval Dashboard                       │
   │ Eingeloggt als: max.mustermann@medealis.de     │
   ├─────────────────────────────────────────────────┤
   │                                                 │
   │ 📋 Offene Genehmigungsanfragen (3)             │
   │                                                 │
   │ ┌──────────────────────────────────────────┐   │
   │ │ 🔔 Lieferantenbewertung SUP-001          │   │
   │ │ Von: pms-researcher Agent                │   │
   │ │ Zeitpunkt: 2025-02-11 14:30             │   │
   │ │ Ziel: NAS /Lieferanten/SUP-001/         │   │
   │ │                                          │   │
   │ │ [Vorschau anzeigen]                      │   │
   │ │                                          │   │
   │ │ ✅ Genehmigen   ❌ Ablehnen              │   │
   │ └──────────────────────────────────────────┘   │
   │                                                 │
   │ ┌──────────────────────────────────────────┐   │
   │ │ 🔔 CAPA-Bericht CAPA-2025-003            │   │
   │ │ ...                                      │   │
   │ └──────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────┘
   ```

3. **Executor implementieren**

   Nach Genehmigung werden Operationen ausgeführt:
   ```python
   # executor.py
   def execute_approved_operation(request: ApprovalRequest):
       if request.target_system == "nas":
           from nas_filesystem.smb_client import write_nas_file
           write_nas_file(request.target_path, request.data["content"])

       elif request.target_system == "sharepoint":
           from sharepoint_connector.sp_auth import upload_file
           upload_file(request.target_path, request.data["content"])

       elif request.target_system == "database":
           # Nur für spezifische, sichere Updates!
           conn = get_db_write_connection()  # Separater Write-User
           conn.execute(request.data["sql"], request.data["params"])

       # Audit-Log
       audit_log(
           "approval-executor",
           "execute_operation",
           {"request_id": request.request_id, "target": request.target_system}
       )
   ```

4. **Testing**
   ```bash
   # Dashboard starten
   cd approval-dashboard
   streamlit run app.py --server.port 8502

   # Test-Workflow:
   # 1. Claude erstellt Dokument (submit_for_approval)
   # 2. Dashboard zeigt Request
   # 3. QMB genehmigt
   # 4. Datei wird auf NAS geschrieben
   # 5. Audit-Log prüfen
   ```

**Deliverables:**
- ✅ Approval-Queue MCP-Server
- ✅ Streamlit Dashboard
- ✅ Write-Executor
- ✅ End-to-End getestet
- ✅ Dokumentation

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

### Phase 3: FastAPI Migration + Spezialisierte Agents

**Zeitraum:** Mär-Apr 2025 (8 Wochen)
**Ziel:** Moderne Web-App + KI-Agents

---

#### Woche 1-2: FastAPI Projekt-Setup

**Aufgaben:**

1. **Projekt-Struktur anlegen**
   ```
   medealis_qms/
   ├── backend/
   │   ├── main.py                 # FastAPI Entry Point
   │   ├── api/                    # API Routes
   │   │   ├── __init__.py
   │   │   ├── auth.py            # Login, JWT
   │   │   ├── suppliers.py       # Lieferanten-Endpoints
   │   │   ├── capas.py           # CAPA-Endpoints
   │   │   ├── documents.py       # Dokumentenlenkung
   │   │   └── deliveries.py      # Wareneingang
   │   ├── services/              # Business Logic
   │   │   ├── supplier_service.py
   │   │   ├── capa_service.py
   │   │   ├── document_service.py
   │   │   └── ai_service_wrapper.py
   │   ├── models/                # SQLAlchemy Models (aus warehouse übernehmen)
   │   ├── schemas/               # Pydantic Request/Response Schemas
   │   │   ├── supplier.py
   │   │   ├── capa.py
   │   │   └── auth.py
   │   ├── dependencies/          # FastAPI Dependencies
   │   │   ├── auth.py            # get_current_user, require_permission
   │   │   └── database.py        # get_db
   │   ├── middleware/            # Middleware
   │   │   ├── audit.py           # Audit-Logging für alle Requests
   │   │   └── error_handler.py   # Globale Error-Handler
   │   ├── templates/             # Jinja2 Templates (HTMX)
   │   │   ├── base.html
   │   │   ├── suppliers/
   │   │   │   ├── index.html
   │   │   │   └── evaluation.html
   │   │   ├── capas/
   │   │   └── partials/          # HTMX Fragments
   │   └── config.py              # Konfiguration (Settings)
   │
   ├── static/                    # CSS, JS
   │   ├── css/
   │   │   └── styles.css         # TailwindCSS
   │   └── js/
   │       ├── htmx.min.js
   │       └── alpine.min.js
   │
   ├── shared/                    # Shared mit Warehouse
   │   ├── ai_service/            # Bereits vorhanden
   │   ├── database/
   │   └── models/                # Gemeinsame Models
   │
   ├── tests/
   │   ├── test_api/
   │   ├── test_services/
   │   └── test_integration/
   │
   ├── alembic/                   # DB Migrations
   │   ├── versions/
   │   └── env.py
   │
   ├── docker/
   │   ├── Dockerfile
   │   ├── docker-compose.yml
   │   └── nginx.conf
   │
   ├── .env.example
   ├── pyproject.toml
   └── README.md
   ```

2. **Dependencies installieren**
   ```toml
   # pyproject.toml
   [project]
   name = "medealis-qms"
   version = "2.0.0"
   requires-python = ">=3.11"
   dependencies = [
       "fastapi>=0.109.0",
       "uvicorn[standard]>=0.27.0",
       "sqlalchemy>=2.0.0",
       "alembic>=1.13.0",
       "pydantic>=2.5.0",
       "pydantic-settings>=2.1.0",
       "python-jose[cryptography]>=3.3.0",  # JWT
       "passlib[bcrypt]>=1.7.4",
       "python-multipart>=0.0.6",
       "jinja2>=3.1.0",
       "aiofiles>=23.2.0",
       "httpx>=0.26.0",
   ]
   ```

3. **Basis-Setup implementieren**

   **main.py:**
   ```python
   from fastapi import FastAPI
   from fastapi.staticfiles import StaticFiles
   from fastapi.templating import Jinja2Templates
   from backend.middleware.audit import audit_middleware
   from backend.api import auth, suppliers, capas, documents

   app = FastAPI(
       title="Medealis QMS",
       version="2.0.0",
       description="Qualitätsmanagementsystem für Medizinprodukte"
   )

   # Middleware
   app.middleware("http")(audit_middleware)

   # Static Files
   app.mount("/static", StaticFiles(directory="static"), name="static")

   # Templates
   templates = Jinja2Templates(directory="backend/templates")

   # API Routes
   app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
   app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"])
   app.include_router(capas.router, prefix="/api/capas", tags=["capas"])
   app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

   # Health Check
   @app.get("/health")
   async def health():
       return {"status": "ok"}

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000)
   ```

   **config.py:**
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       # Database
       database_url: str = "postgresql://user:pass@localhost/medealis_qms"

       # Security
       secret_key: str
       algorithm: str = "HS256"
       access_token_expire_minutes: int = 480  # 8 Stunden

       # CORS
       allowed_origins: list[str] = ["http://localhost:8000"]

       class Config:
           env_file = ".env"

   settings = Settings()
   ```

4. **Auth-System implementieren**

   **dependencies/auth.py:**
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import OAuth2PasswordBearer
   from jose import JWTError, jwt
   from datetime import datetime, timedelta

   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

   def create_access_token(data: dict):
       to_encode = data.copy()
       expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
       to_encode.update({"exp": expire})
       return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

   async def get_current_user(token: str = Depends(oauth2_scheme)):
       try:
           payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
           username: str = payload.get("sub")
           if username is None:
               raise HTTPException(status_code=401, detail="Invalid token")
       except JWTError:
           raise HTTPException(status_code=401, detail="Invalid token")

       # User aus DB holen (nutzt bestehendes User-Model)
       user = user_repository.get_by_username(username)
       if user is None:
           raise HTTPException(status_code=401, detail="User not found")
       return user

   def require_permission(permission: str):
       def dependency(user = Depends(get_current_user)):
           if not user.has_permission(permission):
               raise HTTPException(status_code=403, detail="No permission")
           return user
       return dependency
   ```

   **api/auth.py:**
   ```python
   from fastapi import APIRouter, Depends, HTTPException
   from fastapi.security import OAuth2PasswordRequestForm

   router = APIRouter()

   @router.post("/login")
   async def login(form_data: OAuth2PasswordRequestForm = Depends()):
       # Nutzt bestehendes User-Service
       user = user_service.authenticate(form_data.username, form_data.password)
       if not user:
           raise HTTPException(status_code=401, detail="Invalid credentials")

       access_token = create_access_token(data={"sub": user.username})
       return {"access_token": access_token, "token_type": "bearer"}
   ```

5. **Erste API-Route: Suppliers**

   **api/suppliers.py:**
   ```python
   from fastapi import APIRouter, Depends, Request
   from fastapi.templating import Jinja2Templates
   from backend.schemas.supplier import SupplierEvaluation
   from backend.services.supplier_service import SupplierService

   router = APIRouter()
   templates = Jinja2Templates(directory="backend/templates")

   @router.get("/")
   async def list_suppliers(
       request: Request,
       user = Depends(require_permission("read:suppliers"))
   ):
       suppliers = supplier_service.get_all()
       return templates.TemplateResponse(
           "suppliers/index.html",
           {"request": request, "suppliers": suppliers, "user": user}
       )

   @router.get("/{supplier_id}/evaluate")
   async def evaluate_supplier(
       request: Request,
       supplier_id: str,
       user = Depends(require_permission("read:suppliers"))
   ):
       # KI-Bewertung generieren
       evaluation = supplier_service.generate_evaluation(supplier_id)

       return templates.TemplateResponse(
           "partials/supplier_evaluation.html",
           {"request": request, "evaluation": evaluation, "user": user}
       )
   ```

6. **HTMX Template erstellen**

   **templates/suppliers/index.html:**
   ```html
   {% extends "base.html" %}

   {% block content %}
   <div class="container mx-auto px-4 py-8">
       <h1 class="text-3xl font-bold mb-6">Lieferantenbewertung</h1>

       <select id="supplier-select"
               hx-get="/api/suppliers/{value}/evaluate"
               hx-target="#evaluation-result"
               hx-trigger="change"
               class="w-full p-2 border rounded">
           <option value="">Lieferant wählen...</option>
           {% for supplier in suppliers %}
           <option value="{{ supplier.id }}">
               {{ supplier.name }} ({{ supplier.supplier_id }})
           </option>
           {% endfor %}
       </select>

       <div id="evaluation-result" class="mt-8"></div>
   </div>
   {% endblock %}
   ```

7. **Testing**
   ```bash
   # Development Server
   uvicorn backend.main:app --reload

   # Browser: http://localhost:8000
   # API Docs: http://localhost:8000/docs (automatisch generiert!)
   ```

**Deliverables:**
- ✅ FastAPI Projekt läuft
- ✅ Auth-System (JWT)
- ✅ Erste API-Route (Suppliers)
- ✅ HTMX-Template funktioniert
- ✅ OpenAPI-Docs generiert

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

#### Woche 3-4: Wareneingang auf FastAPI migrieren

**Aufgaben:**

1. **API-Routen für Wareneingang**

   **api/deliveries.py:**
   ```python
   @router.post("/scan")
   async def scan_delivery_note(
       file: UploadFile,
       user = Depends(get_current_user)
   ):
       # OCR-Service wiederverwenden
       from warehouse_app.application.services import ocr_service

       text = await ocr_service.extract_text(file)
       delivery_data = ocr_service.parse_delivery_note(text)

       return {
           "status": "success",
           "data": delivery_data
       }

   @router.post("/create")
   async def create_delivery(
       delivery: DeliveryCreate,
       user = Depends(get_current_user)
   ):
       # Delivery-Service wiederverwenden
       delivery_entity = delivery_service.create(delivery, user)

       # Event publishen (für QMS)
       event_bus.publish(DeliveryCreatedEvent(delivery_entity))

       return {"id": delivery_entity.id, "status": "created"}
   ```

2. **Frontend mit HTMX**

   **templates/deliveries/scan.html:**
   ```html
   <form hx-post="/api/deliveries/scan"
         hx-encoding="multipart/form-data"
         hx-target="#scan-result">

       <input type="file" name="file" accept="image/*,application/pdf">
       <button type="submit">Scannen</button>
   </form>

   <div id="scan-result"></div>
   ```

3. **Barcode/QR-Code Generation API**
   ```python
   @router.post("/items/{item_id}/barcode")
   async def generate_barcode(item_id: str):
       # Barcode-Service wiederverwenden
       barcode_path = barcode_service.generate(item_id)
       return FileResponse(barcode_path)
   ```

4. **Migration abschließen**
   - Alle Streamlit-Views nach FastAPI portieren
   - Side-by-Side Testing
   - Streamlit deprecated markieren

**Deliverables:**
- ✅ Wareneingang-API vollständig
- ✅ HTMX-Frontend funktional
- ✅ Feature-Parität mit Streamlit

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

#### Woche 5-6: Spezialisierte Agents implementieren

**Aufgaben:**

1. **Agent-Framework aufbauen**

   **Dateien:**
   ```
   .claude/agents/
   ├── pms_researcher.md       # PMS-Recherche Agent
   ├── capa_agent.md           # CAPA-Analyse Agent
   ├── supplier_evaluator.md   # Lieferantenbewertung Agent
   └── doc_controller.md       # Dokumentenlenkung Agent
   ```

2. **PMS-Researcher Agent**

   **.claude/agents/pms_researcher.md:**
   ```markdown
   ---
   name: pms-researcher
   description: >
     Post-Market Surveillance Recherche für Medizinprodukte.
     Aktiviert bei: PMS, Literaturrecherche, Vigilanzdaten, MAUDE, BfArM
   tools: Read, Bash, WebSearch, WebFetch
   model: sonnet
   ---

   Du bist PMS-Spezialist für Dental Locator Abutments.

   ## Datenquellen
   1. PubMed (search_pubmed via MCP)
   2. FDA MAUDE (search_fda_maude via MCP)
   3. BfArM (search_bfarm_safety via MCP)
   4. Interne Daten (get_inspection_data via MCP)

   ## Arbeitsweise
   1. Suchstrategie definieren
   2. Systematisch alle Quellen durchsuchen
   3. Relevanz bewerten
   4. Strukturierte Zusammenfassung
   5. PMS-Bericht erstellen (create_pms_report)

   ## Output
   - Suchstrategie
   - Literaturübersicht (PMID-Referenzen)
   - Vigilanzdaten
   - Trendanalyse
   - Risikobewertung
   - Empfohlene Maßnahmen
   ```

3. **CAPA-Agent**

   **.claude/agents/capa_agent.md:**
   ```markdown
   ---
   name: capa-agent
   description: >
     CAPA-Analyse und -Berichtserstellung nach ISO 13485.
     Aktiviert bei: CAPA, Korrekturmaßnahme, Abweichung, 8D, Root Cause
   tools: Read, Write, Edit, Bash
   model: sonnet
   ---

   Du bist QM-Experte für CAPA-Prozesse.

   ## 8D-Methodik
   1. Problembeschreibung (messbar)
   2. Sofortmaßnahme
   3. Ursachenanalyse (Ishikawa + 5-Why)
   4. Korrekturmaßnahme (SMART)
   5. Vorbeugemaßnahme (systemisch)
   6. Wirksamkeitsprüfung (Kriterien)

   ## Priorisierung
   - Hoch: Patientensicherheit betroffen
   - Mittel: Qualitätsabweichung
   - Niedrig: Prozessverbesserung

   ## Output
   - CAPA-Bericht (create_capa_report)
   - Verknüpfung mit ähnlichen CAPAs prüfen
   - Lieferant-Auffälligkeiten identifizieren
   ```

4. **Supplier-Evaluator Agent**

   **.claude/agents/supplier_evaluator.md:**
   ```markdown
   ---
   name: supplier-evaluator
   description: >
     Lieferantenbewertung nach ISO 13485 Kap. 7.4.
     Aktiviert bei: Lieferantenbewertung, Supplier Rating, Audit
   tools: Read, Bash, Write
   model: sonnet
   ---

   Du bewertest Lieferanten objektiv nach QM-Kriterien.

   ## Bewertungskriterien
   1. Liefertreue (30%)
   2. Qualität (35%)
   3. Dokumentation (20%)
   4. Kommunikation (15%)

   ## Skala 1-5
   - 5 = Hervorragend (>98% Liefertreue, <0.5% Reklamationen)
   - 4 = Gut (95-98%, 0.5-1%)
   - 3 = Befriedigend (90-95%, 1-2%)
   - 2 = Mangelhaft (80-90%, 2-5%)
   - 1 = Ungenügend (<80%, >5%)

   ## Klassifizierung
   - A-Lieferant (≥4.0): Bevorzugt
   - B-Lieferant (3.0-3.9): Zugelassen
   - C-Lieferant (2.0-2.9): Bedingt
   - Gesperrt (<2.0): Keine Beschaffung

   ## Arbeitsweise
   1. Daten über get_supplier_data abrufen
   2. Kennzahlen berechnen
   3. Bewertung mit Begründung
   4. Dokument erstellen (create_supplier_evaluation)
   5. Bei C: CAPA-Vorschlag
   ```

5. **Testing der Agents**
   ```bash
   # Claude Code starten
   claude

   # Agent-Aktivierung testen:
   Du: Erstelle einen PMS-Bericht für Dental Locator Abutments für 2024.

   # → pms-researcher Agent sollte aktiviert werden
   # → Führt Recherche durch
   # → Erstellt strukturierten Bericht
   ```

**Deliverables:**
- ✅ 4 spezialisierte Agents
- ✅ Agent-Aktivierung funktioniert
- ✅ Integration mit MCP-Tools
- ✅ Dokumentation

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

#### Woche 7-8: Headless Automation + Event Bus

**Aufgaben:**

1. **Event-Bus implementieren**

   **shared/events/event_bus.py:**
   ```python
   from dataclasses import dataclass
   from typing import Callable, List
   from datetime import datetime

   @dataclass
   class Event:
       event_type: str
       timestamp: datetime
       data: dict
       source: str

   class EventBus:
       def __init__(self):
           self._subscribers: dict[str, List[Callable]] = {}

       def subscribe(self, event_type: str, handler: Callable):
           if event_type not in self._subscribers:
               self._subscribers[event_type] = []
           self._subscribers[event_type].append(handler)

       def publish(self, event: Event):
           handlers = self._subscribers.get(event.event_type, [])
           for handler in handlers:
               handler(event)

   # Singleton
   event_bus = EventBus()
   ```

2. **Event-Handlers für QMS**

   **qms_app/event_handlers.py:**
   ```python
   from shared.events import event_bus, Event

   # Wenn Wareneingang erfasst → QMS benachrichtigen
   def on_delivery_created(event: Event):
       delivery_data = event.data

       # Prüfe ob Lieferant neu bewertet werden muss
       if should_reevaluate_supplier(delivery_data["supplier_id"]):
           # Trigger Supplier Evaluation
           supplier_service.schedule_evaluation(delivery_data["supplier_id"])

   event_bus.subscribe("delivery.created", on_delivery_created)

   # Wenn Reklamation → CAPA prüfen
   def on_complaint_created(event: Event):
       complaint = event.data

       if complaint["severity"] == "high":
           # Auto-CAPA erstellen
           capa_service.create_from_complaint(complaint)

   event_bus.subscribe("complaint.created", on_complaint_created)
   ```

3. **Headless Scripts für Automation**

   **scripts/weekly_qms_report.sh:**
   ```bash
   #!/bin/bash
   # Wöchentlicher QMS-Statusbericht

   LOG_DIR="$HOME/medealis_qms/logs"
   OUTPUT_DIR="$HOME/medealis_qms/data/output"

   cd "$HOME/medealis_qms" || exit 1

   echo "=== QMS Statusbericht $(date) ===" >> "$LOG_DIR/weekly.log"

   # Claude Code Headless
   claude -p "
   Du bist der doc-controller Agent.

   Erstelle den wöchentlichen QMS-Statusbericht:
   1. Ablaufende Dokumente (nächste 30 Tage)
   2. Offene CAPAs mit Fristüberschreitung
   3. QMS-Gesundheitsstatus
   4. Speichere als DOCX in $OUTPUT_DIR

   Nutze die MCP-Tools für Datenzugriff.
   " --allowedTools Read,Write,Bash >> "$LOG_DIR/weekly.log" 2>&1

   # Approval-Request erstellen
   REQUEST_ID=$(cat "$LOG_DIR/weekly.log" | grep "request_id" | tail -1 | cut -d'"' -f4)

   echo "Bericht erstellt. Approval-Request: $REQUEST_ID"

   # Email an QMB
   echo "Neuer QMS-Statusbericht wartet auf Genehmigung: $REQUEST_ID" | \
       mail -s "QMS-Bericht Review erforderlich" qmb@medealis.de
   ```

4. **Cron-Jobs einrichten**
   ```bash
   # crontab -e

   # Wöchentlicher QMS-Statusbericht: Montag 8:00
   0 8 * * 1 /home/medealis/scripts/weekly_qms_report.sh

   # Monatliche Lieferantenbewertung: 1. des Monats 9:00
   0 9 1 * * /home/medealis/scripts/monthly_supplier_eval.sh

   # Quartalsweise PMS-Recherche: 1. Jan/Apr/Jul/Okt 10:00
   0 10 1 1,4,7,10 * /home/medealis/scripts/quarterly_pms.sh
   ```

5. **FastAPI Background Tasks**
   ```python
   from fastapi import BackgroundTasks

   @router.post("/suppliers/{supplier_id}/evaluate/schedule")
   async def schedule_evaluation(
       supplier_id: str,
       background_tasks: BackgroundTasks,
       user = Depends(get_current_user)
   ):
       # Im Hintergrund ausführen
       background_tasks.add_task(
           supplier_service.generate_evaluation_async,
           supplier_id
       )
       return {"status": "scheduled"}
   ```

**Deliverables:**
- ✅ Event-Bus funktioniert
- ✅ Event-Handlers für QMS
- ✅ Headless Scripts getestet
- ✅ Cron-Jobs konfiguriert
- ✅ Background Tasks

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

### Phase 4: Validierung + Audit-Vorbereitung

**Zeitraum:** Apr-Mai 2025 (6 Wochen)
**Ziel:** Audit-Ready System

---

#### Woche 1-2: Validierungsbericht erstellen

**Aufgaben:**

1. **Validierungsplan erstellen**

   **Struktur nach GAMP 5:**
   ```
   1. Einleitung
      - Zweck der Validierung
      - Scope (Wareneingang + QMS-Modul)
      - Regulatorischer Rahmen (ISO 13485, MDR)

   2. System-Beschreibung
      - Architektur-Diagramme
      - Technologie-Stack
      - Datenflüsse

   3. Risikoanalyse
      - Kritikalität der Module (GAMP Kategorie 4)
      - Risiken identifizieren
      - Mitigation-Maßnahmen

   4. Validierungsstrategie
      - Unit Tests (pytest)
      - Integration Tests
      - User Acceptance Tests

   5. Testdokumentation
      - Test Cases (Excel/CSV)
      - Test Execution Records
      - Defect Tracking

   6. Traceability Matrix
      - Anforderungen ↔ Tests ↔ Code

   7. Schlussfolgerung
      - Validierungsstatus
      - Offene Punkte
      - Freigabe-Empfehlung
   ```

2. **Test Cases definieren**

   **Beispiel: Lieferantenbewertung**

   | Test-ID | Beschreibung | Eingabe | Erwartetes Ergebnis | Status |
   |---------|-------------|---------|---------------------|--------|
   | VAL-SUP-001 | Bewertung mit gültigen Daten | Supplier-ID, Zeitraum | Bewertung erstellt | ✅ Pass |
   | VAL-SUP-002 | Bewertung mit ungültiger ID | "INVALID" | Fehlermeldung | ✅ Pass |
   | VAL-SUP-003 | Klassifizierung A-Lieferant | Score ≥4.0 | Klassifizierung = A | ✅ Pass |
   | VAL-SUP-004 | CAPA-Vorschlag bei C | Score 2.5 | CAPA-Empfehlung | ✅ Pass |
   | VAL-SUP-005 | Audit-Log-Eintrag | Jede Bewertung | Log vorhanden | ✅ Pass |

3. **Automated Tests implementieren**

   **tests/test_supplier_service.py:**
   ```python
   import pytest
   from backend.services.supplier_service import SupplierService

   @pytest.fixture
   def supplier_service():
       return SupplierService()

   def test_evaluate_supplier_valid(supplier_service):
       """VAL-SUP-001: Bewertung mit gültigen Daten."""
       evaluation = supplier_service.evaluate("SUP-001", "Q4 2024")

       assert evaluation is not None
       assert "total_score" in evaluation
       assert evaluation["total_score"] >= 1.0
       assert evaluation["total_score"] <= 5.0

   def test_evaluate_supplier_invalid_id(supplier_service):
       """VAL-SUP-002: Ungültige Supplier-ID."""
       with pytest.raises(SupplierNotFoundException):
           supplier_service.evaluate("INVALID", "Q4 2024")

   def test_classification_a_supplier(supplier_service):
       """VAL-SUP-003: A-Lieferant Klassifizierung."""
       # Mock mit Score 4.5
       evaluation = supplier_service.evaluate("SUP-EXCELLENT", "Q4 2024")

       assert evaluation["classification"] == "A-Lieferant"
       assert evaluation["total_score"] >= 4.0
   ```

4. **Test-Execution durchführen**
   ```bash
   # Alle Tests ausführen
   pytest tests/ -v --html=reports/test_report.html

   # Coverage-Report
   pytest --cov=backend --cov-report=html
   ```

5. **Validierungsbericht schreiben**

   **VALIDATION_REPORT.md:**
   ```markdown
   # Validierungsbericht: Medealis QMS v2.0

   ## 1. Einleitung

   Dieser Bericht dokumentiert die Validierung des QMS-Systems
   gemäß ISO 13485:2016 Kap. 4.1.6 und 7.5.6 (Validierung).

   ## 2. System-Beschreibung

   [Architektur-Diagramme einfügen]

   ## 3. Risikoanalyse

   | Risiko | Wahrscheinlichkeit | Schweregrad | RPZ | Mitigation |
   |--------|-------------------|-------------|-----|------------|
   | KI generiert falsche Bewertung | Mittel | Hoch | 12 | Human-in-the-Loop |
   | SQL-Injection | Niedrig | Kritisch | 9 | Query-Validierung |
   | Daten-Verlust | Niedrig | Hoch | 6 | Tägliches Backup |

   ## 4. Testdokumentation

   Gesamt: 87 Tests
   - Passed: 85
   - Failed: 2 (bekannte Bugs, nicht kritisch)

   Coverage: 92%

   [Detaillierte Test-Matrix anhängen]

   ## 5. Traceability

   | Anforderung | Test-ID | Code-Modul |
   |------------|---------|------------|
   | REQ-001: Lieferantenbewertung | VAL-SUP-001-005 | supplier_service.py |

   ## 6. Schlussfolgerung

   Das System ist validiert und für den Produktiveinsatz freigegeben.

   Offene Punkte: [Liste]

   ---
   Erstellt: [Datum]
   Geprüft: [QMB]
   Freigegeben: [GF]
   ```

**Deliverables:**
- ✅ Validierungsplan
- ✅ 80+ Test Cases
- ✅ Automated Tests (>90% Coverage)
- ✅ Validierungsbericht

**Zeitaufwand:** 60 Stunden (2 Wochen)

---

#### Woche 3-4: Verfahrensanweisung "Einsatz von KI"

**Aufgaben:**

1. **VA erstellen nach ISO 13485 Format**

   **VA-QM-017: Einsatz von KI-Hilfsmitteln im QMS**

   ```markdown
   # VA-QM-017: Einsatz von KI-Hilfsmitteln im QMS

   Version: 1.0
   Datum: 2025-04-01
   Gültig ab: 2025-05-01
   Nächste Review: 2026-05-01
   Verantwortlich: QM-Beauftragter

   ## 1. Zweck und Geltungsbereich

   Diese VA regelt den Einsatz von künstlicher Intelligenz (KI)
   bei der Erstellung von QM-Dokumenten.

   Geltungsbereich:
   - Lieferantenbewertungen
   - CAPA-Berichte
   - PMS-Berichte
   - Dokumentenlenkung

   ## 2. Verantwortlichkeiten

   - KI-System: Erstellt Entwürfe
   - QM-Beauftragter: Prüft und genehmigt alle Entwürfe
   - Geschäftsführung: Freigabe kritischer Dokumente

   ## 3. Verfahrensbeschreibung

   ### 3.1 KI-gestützte Dokumentenerstellung

   1. Anforderung durch autorisierten Benutzer
   2. KI-System generiert Entwurf
   3. Entwurf wird in Approval-Queue eingereiht
   4. QMB prüft Entwurf auf:
      - Fakten-Richtigkeit
      - Regulatorische Konformität
      - Vollständigkeit
   5. QMB genehmigt oder lehnt ab
   6. Bei Genehmigung: Dokument wird finalisiert

   ### 3.2 Human-in-the-Loop Prinzip

   KEIN KI-generiertes Dokument darf ohne menschliche Prüfung
   in das QMS aufgenommen werden.

   ### 3.3 Audit-Trail

   Für jedes Dokument wird protokolliert:
   - Wer hat Erstellung angefordert?
   - Welches KI-Modell wurde verwendet?
   - Wer hat geprüft und genehmigt?
   - Datum/Uhrzeit aller Schritte

   ## 4. Verwendete KI-Modelle

   | Modell | Provider | Version | Zweck |
   |--------|----------|---------|-------|
   | Claude 3.5 Sonnet | Anthropic | 20241022 | Standard |
   | GPT-4o | OpenAI | 2024-11 | Fallback |

   ## 5. Risikobewertung

   [Risikomanagement-Akte Verweis: RMA-001]

   Hauptrisiko: KI halluziniert Daten
   Mitigation: Human-in-the-Loop (obligatorisch)

   ## 6. Validierung

   Das KI-System wurde validiert gemäß VALIDATION_REPORT.md.

   ## 7. Schulung

   Alle QMB und autorisierten Benutzer müssen geschult werden:
   - Funktionsweise des Systems
   - Prüf-Kriterien für KI-Entwürfe
   - Umgang mit Approval-Dashboard

   ## 8. Änderungshistorie

   | Version | Datum | Änderung | Autor |
   |---------|-------|----------|-------|
   | 1.0 | 2025-04-01 | Erstausgabe | M. Mustermann |

   ---
   Geprüft: [QMB]
   Freigegeben: [GF]
   ```

2. **Schulungsunterlagen erstellen**

   **Schulung: KI-gestütztes QMS**

   - PowerPoint-Präsentation (30 Folien)
   - Hands-on Demo (Approval-Dashboard)
   - Quiz (10 Fragen)
   - Schulungsnachweis

3. **Risikoanalyse nach ISO 14971**

   **RMA-001: KI-System im QMS**

   | Gefährdung | Gefährdungssituation | Schaden | S | P | RPZ | Maßnahme |
   |------------|---------------------|---------|---|---|-----|----------|
   | Falsche Bewertung | KI bewertet Lieferant falsch | Schlechter Lieferant wird nicht erkannt | 3 | 2 | 6 | Human Review |
   | Daten-Leak | KI-Provider speichert Daten | Vertraulichkeit verletzt | 4 | 1 | 4 | AVV, Anonymisierung |
   | Halluzination | KI erfindet Fakten | Falsche regulatorische Aussagen | 4 | 2 | 8 | Faktencheck durch QMB |

**Deliverables:**
- ✅ VA-QM-017 erstellt und freigegeben
- ✅ Schulungsunterlagen
- ✅ Risikoanalyse RMA-001
- ✅ Schulung durchgeführt

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

#### Woche 5-6: Audit-Vorbereitung

**Aufgaben:**

1. **Audit-Checkliste erstellen**

   **Interne Audit-Checkliste (ISO 13485 Kap. 8.2.2):**

   ```markdown
   # Interne Audit-Checkliste: QMS-Software

   Datum: [TT.MM.JJJJ]
   Auditor: [Name]
   Auditee: IT/QM

   ## 4.1.6 Validierung von Anwendungssoftware

   - [ ] Validierungsbericht vorhanden? (VALIDATION_REPORT.md)
   - [ ] Testdokumentation vollständig?
   - [ ] Traceability Matrix vorhanden?
   - [ ] Validierungsstatus: ☐ Validiert ☐ In Arbeit

   ## 4.2.4 Lenkung von Dokumenten

   - [ ] VA für KI-Einsatz vorhanden? (VA-QM-017)
   - [ ] Freigabe-Prozess dokumentiert?
   - [ ] Versionskontrolle funktioniert?

   ## 4.2.5 Lenkung von Aufzeichnungen

   - [ ] Audit-Log vollständig?
   - [ ] Alle Aktionen nachvollziehbar?
   - [ ] Backup-Strategie dokumentiert?
   - [ ] Aufbewahrungsfristen definiert? (90 Tage)

   ## 7.4 Beschaffung (Lieferantenbewertung)

   - [ ] Bewertungskriterien definiert?
   - [ ] Bewertungsrhythmus eingehalten? (jährlich)
   - [ ] Klassifizierung nachvollziehbar?
   - [ ] Bei C-Lieferant: CAPA vorhanden?

   ## 8.5.2/8.5.3 Korrektur- und Vorbeugemaßnahmen

   - [ ] CAPA-Prozess dokumentiert?
   - [ ] 8D-Methodik angewendet?
   - [ ] Wirksamkeitsprüfung definiert?
   - [ ] Ursachenanalyse nachvollziehbar?

   ## Datenschutz (DSGVO)

   - [ ] AVV mit KI-Provider vorhanden?
   - [ ] Datenschutz-Folgenabschätzung durchgeführt?
   - [ ] Anonymisierung sensibler Daten?

   ## IT-Sicherheit

   - [ ] Zugriffskontrolle implementiert? (RBAC)
   - [ ] Passwörter sicher gespeichert? (BCrypt)
   - [ ] SQL-Injection-Schutz vorhanden?
   - [ ] Audit-Log manipulationssicher?

   ## Schulung

   - [ ] Schulungsplan vorhanden?
   - [ ] Mitarbeiter geschult? (Nachweise)
   - [ ] Wirksamkeit der Schulung geprüft?

   ---

   ## Feststellungen

   Positiv:
   - [Liste der positiven Befunde]

   Abweichungen:
   - [Liste der Abweichungen mit Schweregrad]

   Empfehlungen:
   - [Verbesserungsvorschläge]

   ---
   Auditor: [Unterschrift]
   Datum: [TT.MM.JJJJ]
   ```

2. **Mock-Audit durchführen**

   - Interne Auditoren schulen
   - Mock-Audit mit externer Perspektive
   - Befunde dokumentieren
   - CAPAs für Abweichungen erstellen

3. **Dokumentation vervollständigen**

   **Dokumente für Benannte Stelle:**
   - QM-Handbuch (aktualisiert mit Software-Modul)
   - VA-QM-017 (KI-Einsatz)
   - Validierungsbericht
   - Risikoanalyse RMA-001
   - Schulungsnachweise
   - Backup-Strategie
   - Incident-Response-Plan

4. **Technische Dokumentation**

   **Tech-Doku für Audit:**
   - Architektur-Diagramme
   - Datenfluss-Diagramme
   - API-Dokumentation (OpenAPI)
   - Datenbank-Schema
   - Deployment-Anleitung
   - Disaster-Recovery-Plan

**Deliverables:**
- ✅ Audit-Checkliste
- ✅ Mock-Audit durchgeführt
- ✅ Dokumentation vollständig
- ✅ Tech-Doku erstellt
- ✅ Audit-Ready

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

### Phase 5: Produktiv-Rollout

**Zeitraum:** Jun 2025 (4 Wochen)
**Ziel:** Produktiv-System im Einsatz

---

#### Woche 1: Production-Deployment

**Aufgaben:**

1. **Docker-Setup finalisieren**

   **docker-compose.production.yml:**
   ```yaml
   version: '3.8'

   services:
     fastapi-app:
       build:
         context: .
         dockerfile: docker/Dockerfile.production
       environment:
         - DATABASE_URL=postgresql://medealis:${DB_PASSWORD}@postgres/medealis_qms
         - SECRET_KEY=${SECRET_KEY}
         - ALLOWED_ORIGINS=https://qms.medealis.de
       ports:
         - "8000:8000"
       depends_on:
         - postgres
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3

     postgres:
       image: postgres:15-alpine
       environment:
         POSTGRES_DB: medealis_qms
         POSTGRES_USER: medealis
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - pgdata:/var/lib/postgresql/data
         - ./backups:/backups
       restart: unless-stopped

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
         - ./static:/usr/share/nginx/html/static:ro
       depends_on:
         - fastapi-app
       restart: unless-stopped

     backup:
       image: postgres:15-alpine
       volumes:
         - ./backups:/backups
       environment:
         PGHOST: postgres
         PGDATABASE: medealis_qms
         PGUSER: medealis
         PGPASSWORD: ${DB_PASSWORD}
       command: >
         sh -c "while true; do
           pg_dump -Fc > /backups/backup_$(date +%Y%m%d_%H%M%S).dump
           find /backups -name '*.dump' -mtime +30 -delete
           sleep 86400
         done"
       depends_on:
         - postgres

   volumes:
     pgdata:
   ```

2. **SSL-Zertifikat einrichten**
   ```bash
   # Let's Encrypt
   certbot certonly --standalone -d qms.medealis.de

   # Zertifikate kopieren
   cp /etc/letsencrypt/live/qms.medealis.de/fullchain.pem ssl/
   cp /etc/letsencrypt/live/qms.medealis.de/privkey.pem ssl/
   ```

3. **Deployment-Script**
   ```bash
   #!/bin/bash
   # deploy.sh

   set -e

   echo "=== Medealis QMS Deployment ==="

   # 1. Backup erstellen
   echo "Erstelle Backup..."
   docker-compose -f docker-compose.production.yml exec postgres \
       pg_dump -Fc medealis_qms > backups/pre_deploy_$(date +%Y%m%d).dump

   # 2. Git Pull
   echo "Hole neueste Version..."
   git pull origin main

   # 3. Build
   echo "Baue Container..."
   docker-compose -f docker-compose.production.yml build

   # 4. DB-Migrations
   echo "Führe DB-Migrations aus..."
   docker-compose -f docker-compose.production.yml run --rm fastapi-app \
       alembic upgrade head

   # 5. Deploy
   echo "Starte Services..."
   docker-compose -f docker-compose.production.yml up -d

   # 6. Health Check
   echo "Warte auf Health Check..."
   sleep 10
   curl -f http://localhost:8000/health || exit 1

   echo "✅ Deployment erfolgreich!"
   ```

4. **Monitoring einrichten**
   ```bash
   # Prometheus + Grafana (optional)
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

**Deliverables:**
- ✅ Production-Docker-Setup
- ✅ SSL-Zertifikat
- ✅ Deployment-Script
- ✅ Monitoring (optional)

**Zeitaufwand:** 30 Stunden (1 Woche)

---

#### Woche 2-3: User-Training & Go-Live

**Aufgaben:**

1. **End-User Training**

   **Zielgruppen:**
   - Lageristen (Wareneingang)
   - QM-Beauftragte (QMS-Modul)
   - Geschäftsführung (Dashboards)

   **Inhalte:**
   - System-Überblick (30 Min)
   - Hands-on Wareneingang (60 Min)
   - Hands-on QMS (60 Min)
   - Approval-Workflow (30 Min)
   - Q&A (30 Min)

2. **Pilot-Phase**
   ```
   Woche 1: 2 Power-User
   Woche 2: 5 Benutzer
   Woche 3: Alle Benutzer

   Feedback sammeln täglich!
   ```

3. **Go-Live Checkliste**
   ```markdown
   - [ ] Alle Benutzer geschult
   - [ ] Production-System läuft stabil (7 Tage)
   - [ ] Backup-Strategie funktioniert
   - [ ] Monitoring aktiv
   - [ ] Support-Prozess definiert
   - [ ] Incident-Response-Plan kommuniziert
   - [ ] Audit-Dokumentation vollständig
   - [ ] Benannte Stelle informiert (falls erforderlich)
   ```

4. **Go-Live**
   ```
   Datum: [Festlegen nach Pilot]

   Go-Live-Tag:
   08:00 - System-Check
   09:00 - Go-Live Announcement
   09:30 - Erste Produktiv-Nutzung
   12:00 - Mittagspause (Support vor Ort)
   17:00 - Review-Meeting
   ```

**Deliverables:**
- ✅ Alle Benutzer geschult
- ✅ Pilot erfolgreich
- ✅ Go-Live durchgeführt
- ✅ Support etabliert

**Zeitaufwand:** 50 Stunden (2 Wochen)

---

#### Woche 4: Post-Go-Live Support & Optimierung

**Aufgaben:**

1. **Intensive Support-Phase (4 Wochen)**
   - Tägliche Check-ins
   - Bug-Fixes priorisiert
   - User-Feedback sammeln

2. **Performance-Monitoring**
   ```python
   # Metriken erfassen
   - Response-Zeiten API
   - Datenbank-Query-Performance
   - KI-Generierungs-Dauer
   - Fehlerrate
   ```

3. **Optimierungen**
   - Langsame Queries optimieren
   - Caching einführen (Redis)
   - UI/UX Tweaks

4. **Lessons Learned**
   ```markdown
   ## Post-Go-Live Review

   ### Was lief gut?
   - [Liste]

   ### Was lief schlecht?
   - [Liste]

   ### Optimierungen umgesetzt:
   - [Liste]

   ### Nächste Schritte:
   - [Roadmap für v2.1]
   ```

**Deliverables:**
- ✅ Support erfolgreich
- ✅ Performance optimiert
- ✅ Lessons Learned dokumentiert

**Zeitaufwand:** 30 Stunden (1 Woche)

---

## Zeitplan & Meilensteine {#zeitplan}

### Gesamtübersicht

```
2024          2025
Q4   │ Jan  Feb  Mär  Apr  Mai  Jun  Jul  Aug  Sep  Okt  Nov  Dez
─────┼────────────────────────────────────────────────────────────
  ✅  │  ✅   ✅   🔄   📋   📋   📋   📋   📋   📋   📋   📋   📋
Ph0  │ Ph1  Ph1  Ph2  Ph3  Ph4  Ph5  Opt  Opt  V3?  V3?  V3?  V3?
```

**Legende:**
- ✅ Abgeschlossen
- 🔄 In Arbeit
- 📋 Geplant

### Detaillierter Zeitplan

| Meilenstein | Datum | Status | Notizen |
|-------------|-------|--------|---------|
| **M0:** Warehouse-App Live | 2024-12-15 | ✅ | Wareneingang läuft |
| **M1:** KI-Abstraktion fertig | 2025-02-11 | ✅ | Multi-Provider |
| **M2:** MCP-Server QMS-DB | 2025-02-11 | ✅ | 7 Tools verfügbar |
| **M3:** NAS MCP-Server | 2025-02-25 | 🔄 | In Arbeit |
| **M4:** SharePoint MCP-Server | 2025-03-11 | 📋 | Geplant |
| **M5:** Approval-System | 2025-03-25 | 📋 | Geplant |
| **M6:** FastAPI Basis | 2025-04-08 | 📋 | Geplant |
| **M7:** Wareneingang migriert | 2025-04-22 | 📋 | Geplant |
| **M8:** Agents fertig | 2025-05-06 | 📋 | Geplant |
| **M9:** Validierung | 2025-05-20 | 📋 | Geplant |
| **M10:** Audit-Ready | 2025-06-03 | 📋 | Geplant |
| **M11:** Production Go-Live | 2025-06-17 | 📋 | Geplant |

### Kritischer Pfad

```
M1 (KI) → M2 (DB-MCP) → M3 (NAS) → M4 (SP) → M5 (Approval)
   ↓
M6 (FastAPI) → M7 (Migration) → M8 (Agents)
   ↓
M9 (Validierung) → M10 (Audit) → M11 (Go-Live)
```

**Abhängigkeiten:**
- M5 benötigt M3 + M4 (NAS + SharePoint für Writes)
- M8 benötigt M5 (Agents nutzen Approval-Queue)
- M10 benötigt M9 (Audit setzt Validierung voraus)

---

## Risiken & Mitigation {#risiken}

### Top-Risiken

| ID | Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|----|--------|-------------------|--------|------------|
| R1 | **Zeitverzug bei FastAPI-Migration** | Hoch (50%) | Hoch | Parallel-Betrieb Streamlit, schrittweise Migration |
| R2 | **KI-Kosten explodieren** | Mittel (30%) | Mittel | Budgetlimit, Ollama-Fallback |
| R3 | **Audit-Probleme** | Niedrig (10%) | Kritisch | Mock-Audit, frühzeitige Abstimmung mit Benannter Stelle |
| R4 | **Performance-Probleme** | Mittel (40%) | Mittel | Load-Tests, Caching, Skalierung |
| R5 | **User-Akzeptanz niedrig** | Mittel (30%) | Hoch | Intensive Schulung, Pilot-Phase, Feedback-Loops |
| R6 | **Daten-Leak** | Niedrig (5%) | Kritisch | AVV, Anonymisierung, Penetration-Tests |

### Mitigation-Strategien im Detail

#### R1: Zeitverzug

**Plan B:**
- Streamlit NICHT migrieren, nur QMS auf FastAPI
- Reduzierter Scope: Nur kritische Features
- Externe Entwickler hinzuziehen

#### R2: KI-Kosten

**Budgetplanung:**
```
Max. Budget: 500 EUR/Monat
- Claude API: ~200 EUR (für komplexe Aufgaben)
- Ollama (lokal): 0 EUR (für einfache Aufgaben)
- Reserve: 300 EUR

Monitoring: Tägliches Kosten-Tracking
Fallback: Bei >400 EUR → Ollama für alle
```

#### R3: Audit-Probleme

**Proaktive Maßnahmen:**
1. Mock-Audit mit externem Berater (Monat vor echtem Audit)
2. Lückenanalyse
3. CAPAs für alle Befunde
4. Nachdokumentation

#### R5: User-Akzeptanz

**Change-Management:**
```
1. Stakeholder früh einbinden
2. Champions identifizieren (Power-User)
3. Quick Wins kommunizieren
4. Feedback ernst nehmen
5. Iterative Verbesserungen
```

---

## Ressourcenplanung {#ressourcen}

### Team

| Rolle | Person | Aufwand | Phasen |
|-------|--------|---------|--------|
| **Projekt-Lead** | [Name] | 50% | Alle |
| **Backend-Entwickler** | [Name] | 100% | 2-5 |
| **Frontend-Entwickler** | [Name] | 50% | 3-5 |
| **QM-Beauftragter** | [Name] | 20% | 4-5 |
| **Test-Manager** | [Name] | 50% | 4 |
| **Ext. Berater (Audit)** | [Firma] | Ad-hoc | 4 |

### Zeitaufwand (Personentage)

| Phase | Backend | Frontend | QM | Test | Gesamt |
|-------|---------|----------|----|----|--------|
| Phase 2 | 25 PT | 5 PT | 3 PT | 0 PT | 33 PT |
| Phase 3 | 35 PT | 20 PT | 5 PT | 0 PT | 60 PT |
| Phase 4 | 10 PT | 5 PT | 15 PT | 10 PT | 40 PT |
| Phase 5 | 10 PT | 5 PT | 10 PT | 5 PT | 30 PT |
| **Gesamt** | **80 PT** | **35 PT** | **33 PT** | **15 PT** | **163 PT** |

**1 Personentag (PT) = 8 Stunden**

### Budget

```
Personal (intern):         163 PT × 800 EUR/PT = 130.400 EUR
Software-Lizenzen:         Claude Max Abo: 12 × 200 EUR = 2.400 EUR
Externe Berater (Audit):   5.000 EUR
Server/Hosting (1 Jahr):   3.000 EUR
Schulung:                  2.000 EUR
Puffer (15%):              21.270 EUR
─────────────────────────────────────────────────────
GESAMT:                    164.070 EUR
```

---

## Anhang

### A. Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **MCP** | Model Context Protocol – Standard für KI-Tool-Integration |
| **HTMX** | HTML Extension – Partial-Updates ohne JavaScript-Framework |
| **CAPA** | Corrective and Preventive Action – Korrektur-/Vorbeugemaßnahme |
| **PMS** | Post-Market Surveillance – Marktüberwachung nach Inverkehrbringen |
| **MDR** | Medical Device Regulation (EU 2017/745) |
| **GAMP** | Good Automated Manufacturing Practice – Validierungsstandard |

### B. Referenzen

- ISO 13485:2016 – QMS für Medizinprodukte
- ISO 14971:2019 – Risikomanagement
- EU MDR 2017/745 – Medical Device Regulation
- GAMP 5 – Software-Validierung
- MEDDEV 2.12/2 rev2 – PMS-Leitfaden

### C. Kontakte

| Rolle | Name | Email | Telefon |
|-------|------|-------|---------|
| Projekt-Lead | [Name] | [email] | [tel] |
| QM-Beauftragter | [Name] | [email] | [tel] |
| Benannte Stelle | [Firma] | [email] | [tel] |

---

**Dokument-Ende**

**Erstellt:** 2025-02-11
**Version:** 1.0
**Nächste Review:** 2025-03-11
**Freigabe:** [Geschäftsführung]
