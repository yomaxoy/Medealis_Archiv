# PostgreSQL Migration Guide
## Medealis Warehouse Management System

**Status:** Migration vorbereitet - Bereit zur Ausführung
**Datum:** 2025-12-01
**Dauer:** ~2-3 Stunden

---

## ✅ **BEREITS ERLEDIGT**

### Phase 2.1: Vorbereitung ✅
- [x] Datenbank-Integrität geprüft → **PERFEKT**
- [x] Backup erstellt: `warehouse_new_MIGRATION_BACKUP_20251201_201217.db`
- [x] Schema exportiert: `schema_dump_20251201_201217.sql`
- [x] **90 Datensätze** bereit zur Migration
- [x] **8 Tabellen** ohne FK-Verletzungen

### Phase 2.2: Code-Anpassungen ✅
- [x] `connection.py` → PostgreSQL-Support hinzugefügt
- [x] `requirements.txt` → psycopg2-binary hinzugefügt
- [x] Fallback auf SQLite weiterhin möglich

### Phase 2.3: Docker-Konfiguration ✅
- [x] `docker-compose.yaml` → PostgreSQL Service hinzugefügt
- [x] `.env.example` → PostgreSQL Variablen hinzugefügt
- [x] Volume `postgres_data` konfiguriert
- [x] Healthcheck implementiert

---

## 🚀 **NÄCHSTE SCHRITTE**

### Phase 2.4: PostgreSQL starten (15 Min)

```bash
# 1. PostgreSQL Container starten
docker-compose --env-file .env.migration_test up -d postgres

# 2. Warten bis PostgreSQL bereit
docker-compose logs -f postgres
# Warte auf: "database system is ready to accept connections"

# 3. Connection testen
docker-compose exec postgres psql -U medealis_user -d medealis -c "SELECT version();"
```

### Phase 2.5: Schema erstellen (10 Min)

```bash
# Python Script ausführen
cd migration_scripts
python 02_create_postgres_schema.py
```

**Was passiert:**
- SQLAlchemy erstellt alle Tabellen in PostgreSQL
- Foreign Keys werden automatisch angelegt
- Indexes werden erstellt
- Schema-Validierung

### Phase 2.6: Daten migrieren (30-60 Min)

```bash
# Migrations-Script ausführen
python 03_migrate_data_sqlite_to_postgres.py
```

**Migrations-Reihenfolge:**
1. `suppliers` (6 Datensätze)
2. `item_info` (23 Datensätze)
3. `orders` (12 Datensätze)
4. `order_items` (0 Datensätze)
5. `deliveries` (5 Datensätze)
6. `items` (24 Datensätze)
7. `item_workflow_steps` (20 Datensätze)
8. `item_status_steps` (0 Datensätze)

**Features:**
- Batch-Processing (1000 Rows/Batch)
- Progress Bar
- Error Handling & Rollback
- Validierung nach jeder Tabelle

### Phase 2.7: Validierung (15 Min)

```bash
# Validierungs-Script
python 04_validate_migration.py
```

**Prüfungen:**
- Row Counts: SQLite vs PostgreSQL
- Foreign Key Integrity
- Sample Data Verification
- Query Performance Test

---

## 🔧 **MANUELLE SCHRITTE**

### 1. .env Datei anpassen

Kopiere `.env.migration_test` zu `.env` und passe an:

```bash
cp .env.migration_test .env
nano .env  # oder notepad .env
```

**Ändere:**
```env
POSTGRES_PASSWORD=DEIN_SICHERES_PASSWORT_HIER

# Falls du SharePoint nutzen willst:
USE_SHAREPOINT=true
SHAREPOINT_SITE_URL=https://...
SHAREPOINT_CLIENT_ID=...
SHAREPOINT_CLIENT_SECRET=...
SHAREPOINT_TENANT_ID=...
```

### 2. Dependencies installieren

```bash
pip install psycopg2-binary
# oder
pip install -r requirements.txt
```

### 3. Apps neu starten

Nach erfolgreicher Migration:

```bash
# Stoppe alte Container
docker-compose down

# Starte mit PostgreSQL
docker-compose --env-file .env up -d

# Prüfe Logs
docker-compose logs -f medealis-admin
docker-compose logs -f medealis-user
```

---

## ⚠️ **TROUBLESHOOTING**

### Problem: PostgreSQL startet nicht
```bash
docker-compose logs postgres
# Prüfe Fehler

# Neustart
docker-compose restart postgres
```

### Problem: Connection refused
```bash
# Prüfe ob Port 5432 frei ist
netstat -an | findstr 5432

# Prüfe Healthcheck
docker-compose ps
```

### Problem: Migration fehlgeschlagen
```bash
# Rollback: Alte SQLite-Datenbank wiederherstellen
cp ~/.medealis/warehouse_new_MIGRATION_BACKUP_*.db ~/.medealis/warehouse_new.db

# PostgreSQL Daten löschen
docker-compose down -v
docker volume rm neu_medealis_archiv_postgres_data

# Von vorne beginnen
docker-compose up -d postgres
```

---

## 📊 **ERFOLGS-KRITERIEN**

Migration gilt als erfolgreich wenn:

- [  ] PostgreSQL Container läuft (docker ps)
- [  ] Schema erstellt (8 Tabellen)
- [  ] 90 Datensätze migriert
- [  ] Foreign Keys validiert
- [  ] Admin-App startet ohne Fehler
- [  ] User-App startet ohne Fehler
- [  ] CRUD-Operationen funktionieren
- [  ] Performance: Queries < 100ms

---

## 🎯 **NACH DER MIGRATION**

### Optional: QR-Code-System implementieren

Siehe `PHASE3_QR_CODES.md` für:
- QR-Code-Spalte in ItemInfo
- Upload-Interface
- Integration in Barcode-Generator

### Optional: SharePoint aktivieren

Siehe `PHASE4_SHAREPOINT.md` für:
- Azure AD App Registration
- SharePoint Permissions
- Document Upload Test

---

## 📞 **SUPPORT**

Bei Problemen:
1. Prüfe Logs: `docker-compose logs`
2. Prüfe Scripts: `migration_scripts/`
3. Backup vorhanden: `~/.medealis/warehouse_new_MIGRATION_BACKUP_*.db`

**Rollback jederzeit möglich!**
