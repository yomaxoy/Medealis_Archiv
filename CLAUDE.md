# Medealis QMS - Projektkontext

## Projekt
Intelligentes Qualitaetsmanagementsystem fuer Medizinprodukte-Hersteller.
Produktbereich: Dental Locator Abutments (Klasse IIa nach MDR 2017/745).

## Tech-Stack
- **Backend:** Python 3.11+
- **UI:** Streamlit (Admin-App Port 8501, User-App Port 8502)
- **ORM:** SQLAlchemy 2.0
- **Datenbank:** SQLite (data/medealis_db/warehouse_new.db), PostgreSQL-ready
- **AI:** Anthropic Claude API via `src/ai_service/` (provider-agnostisch)
- **MCP-Server:** `mcp-servers/qms_database/` (Read-Only DB-Zugriff)
- **Architektur:** Clean Architecture + Domain-Driven Design

## Verzeichnisstruktur
```
src/
  ai_service/              # Zentrale KI-Abstraktion (Multi-Provider)
    providers/             # Provider-Implementierungen (Claude, ...)
    ai_client.py           # Unified AI Client
    config.py              # KI-Konfiguration
    prompts.py             # QMS System-Prompt Repository
  warehouse/
    domain/                # Entities, Value Objects, Enums, Repository-Interfaces
    application/           # Services, Workflows, Processors
    infrastructure/        # DB-Models, Repositories, External Services
    presentation/          # Streamlit UI (admin/, user/, auth/)
    shared/                # Caching, Config, Utils
config/settings.py         # Zentrale Konfiguration
mcp-servers/qms_database/  # MCP-Server fuer Claude Code
```

## Datenbank-Tabellen
- `suppliers` - Lieferanten-Stammdaten (PK: supplier_id)
- `deliveries` - Lieferungen/Wareneingang (PK: id, UK: delivery_number)
- `items` - Chargen-Items (Composite PK: article_number + batch_number + delivery_number)
- `item_info` - Artikel-Stammdaten (PK: article_number)
- `orders` - Bestellungen (PK: order_number)
- `order_items` - Bestellpositionen (PK: id)
- `users` - Benutzer mit RBAC (PK: user_id)
- `audit_log` - Audit-Trail (PK: id)
- `item_workflow_steps` - Workflow-Status pro Item

## Konventionen
- Type Hints durchgehend
- Docstrings deutsch/englisch gemischt
- Globale Singleton-Instanzen (z.B. `audit_service = AuditService()`)
- ServiceRegistry Pattern fuer Lazy-Loading
- Domain-Enums in `domain/enums/`
- Repository-Interfaces als ABCs in `domain/repositories/`

## Starten
```bash
# User-App
streamlit run src/warehouse/presentation/user/main_user_app.py --server.port 8502
# Admin-App
streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port 8501
```

## Umgebungsvariablen
- `ANTHROPIC_API_KEY` - Claude API Key (erforderlich fuer KI-Features)
- `AI_PROVIDER` - Aktiver Provider (default: claude)
- `USE_SERVER_STORAGE` - Server-Speicher nutzen (true/false)
- `ENVIRONMENT` - development/production
