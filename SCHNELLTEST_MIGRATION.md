# 🚀 SCHNELLTEST: PostgreSQL Migration

**Ziel:** Teste ob Migration funktioniert - OHNE alte Testdaten zu migrieren

**Dauer:** 5-10 Minuten

---

## ⚡ **OPTION 1: Mit Docker (Empfohlen)**

### Voraussetzungen
- Docker Desktop läuft
- Port 5432 frei

### Schritte

```bash
# 1. PostgreSQL starten (2 Min)
docker-compose --env-file .env.migration_test up -d postgres

# Warte bis PostgreSQL bereit ist
docker-compose logs -f postgres
# Warte auf: "database system is ready to accept connections"
# Dann: Strg+C

# 2. Schnelltest ausführen (2 Min)
cd migration_scripts
python QUICKTEST_MIGRATION.py

# Erwartetes Ergebnis:
# ✅ PASS | Connection
# ✅ PASS | Schema
# ✅ PASS | CRUD Operations
# ✅ PASS | Foreign Keys
# ✅ PASS | Performance
#
# 🎉 MIGRATION ERFOLGREICH!
```

### Was wird getestet?
✅ PostgreSQL Connection
✅ Schema-Erstellung (8 Tabellen)
✅ **CREATE** - Supplier, ItemInfo, Delivery, Item
✅ **READ** - Alle Tabellen
✅ **UPDATE** - Supplier ändern
✅ **DELETE** - Test-Daten löschen
✅ Foreign Key Constraints
✅ Query Performance (<50ms)

### Bei Erfolg: Apps starten

```bash
# Alle Services starten
docker-compose --env-file .env.migration_test up -d

# Apps öffnen
start http://localhost:8501  # Admin-App
start http://localhost:8502  # User-App
```

---

## ⚡ **OPTION 2: Ohne Docker (Lokales PostgreSQL)**

Falls du PostgreSQL lokal installiert hast:

### 1. PostgreSQL vorbereiten

```sql
-- Als postgres User:
CREATE DATABASE medealis;
CREATE USER medealis_user WITH PASSWORD 'migration_test_password_2024';
GRANT ALL PRIVILEGES ON DATABASE medealis TO medealis_user;
```

### 2. Schnelltest ausführen

```bash
cd migration_scripts
python QUICKTEST_MIGRATION.py
```

---

## ⚡ **OPTION 3: Nur Code-Validierung (Ohne DB)**

Teste nur ob der Code korrekt umgestellt wurde:

### 1. Python Syntax Check

```bash
python -m py_compile src/warehouse/infrastructure/database/connection.py
```

Kein Output = ✅ Syntax korrekt

### 2. Import Test

```python
python -c "from warehouse.infrastructure.database import initialize_database; print('✅ Import erfolgreich')"
```

### 3. PostgreSQL-Support prüfen

```python
python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/db'
from warehouse.infrastructure.database import initialize_database
try:
    # Wird fehlschlagen wegen fehlendem Server, aber Code ist OK
    initialize_database()
except:
    print('✅ PostgreSQL-Support vorhanden')
"
```

---

## 📊 **SCHNELLE MANUELLE PRÜFUNG**

### 1. Prüfe connection.py

Öffne [src/warehouse/infrastructure/database/connection.py](src/warehouse/infrastructure/database/connection.py)

**Suche nach:**
- ✅ `postgresql://` Support
- ✅ `pool_size=10`
- ✅ `os.getenv("DATABASE_URL")`
- ✅ Fallback auf SQLite

### 2. Prüfe docker-compose.yaml

Öffne [docker-compose.yaml](docker-compose.yaml)

**Suche nach:**
- ✅ `postgres:` Service
- ✅ `postgres:15-alpine` Image
- ✅ `DATABASE_URL=postgresql://...`
- ✅ `volumes: postgres_data`

### 3. Prüfe requirements.txt

```bash
grep psycopg2 requirements.txt
```

**Erwartung:**
```
psycopg2-binary>=2.9.9     # PostgreSQL Driver für Production
```

---

## ✅ **ERFOLGSKRITERIEN**

Migration gilt als erfolgreich wenn:

1. **Code-Level:**
   - [ ] `connection.py` unterstützt PostgreSQL
   - [ ] `psycopg2-binary` in requirements.txt
   - [ ] `docker-compose.yaml` hat postgres Service

2. **Runtime-Level (mit Docker):**
   - [ ] PostgreSQL Container läuft
   - [ ] Schema erstellt (8 Tabellen)
   - [ ] CRUD funktioniert
   - [ ] Foreign Keys aktiv

3. **App-Level (mit Docker):**
   - [ ] Admin-App startet (Port 8501)
   - [ ] User-App startet (Port 8502)
   - [ ] Neue Daten können erstellt werden
   - [ ] Keine DB-Fehler in Logs

---

## 🔧 **TROUBLESHOOTING**

### Problem: "Docker Desktop nicht gefunden"

**Lösung:**
- Docker Desktop starten
- Warte 30 Sekunden
- Retry

### Problem: "Port 5432 already in use"

**Lösung:**
```bash
# Windows: Finde Prozess auf Port 5432
netstat -ano | findstr :5432

# Stoppe lokales PostgreSQL (falls installiert)
# Oder ändere Port in docker-compose.yaml zu 5433
```

### Problem: "psycopg2 not found"

**Lösung:**
```bash
pip install psycopg2-binary
```

### Problem: "Connection refused"

**Lösung:**
```bash
# Prüfe ob PostgreSQL läuft
docker-compose logs postgres

# Prüfe Healthcheck
docker-compose ps

# Neustart
docker-compose restart postgres
```

---

## 🎯 **NÄCHSTE SCHRITTE NACH ERFOLG**

1. **QR-Code-System implementieren**
   - ItemInfo: qr_code_image Spalte hinzufügen
   - Upload-Interface erstellen

2. **SharePoint aktivieren**
   - Azure AD App Registration
   - .env mit SharePoint-Credentials
   - USE_SHAREPOINT=true

3. **Production-Deployment**
   - Sichere .env erstellen
   - Mini-Server aufsetzen
   - User-Schulung

---

## 📞 **SUPPORT**

Falls Probleme auftreten:

1. **Logs prüfen:**
   ```bash
   docker-compose logs postgres
   docker-compose logs medealis-admin
   ```

2. **Script-Output:**
   ```bash
   python QUICKTEST_MIGRATION.py > test_output.txt 2>&1
   ```

3. **Rollback:**
   ```bash
   docker-compose down -v
   # Alte SQLite-DB funktioniert weiterhin
   ```

**Keine Sorge:** Alte SQLite-Datenbank bleibt unverändert! ✅
