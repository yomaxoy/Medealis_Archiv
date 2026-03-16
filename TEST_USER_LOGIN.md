# Test-Anleitung: User-Login zwischen Admin/User-App

## Ziel
Prüfen ob das User-Login-Problem gelöst ist (Admin erstellt User → User kann sich in User-App anmelden).

## Voraussetzungen
- Admin-App läuft auf Port 8501
- User-App läuft auf Port 8502
- Beide Apps nutzen gleiche Datenbank (SQLite oder PostgreSQL)

## Test-Schritte

### 1. Admin-App: Neuen User anlegen

```bash
# Terminal 1: Admin-App starten
streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port=8501
```

1. Browser öffnen: `http://localhost:8501`
2. Als Admin einloggen
3. Navigation → **"Benutzer"** (nur für Admins sichtbar)
4. Neuen Benutzer erstellen:
   - Username: `testuser`
   - Email: `test@example.com`
   - Rolle: `user`
   - Passwort: `Test1234!`
5. User speichern

**Erwartung:** ✅ User wurde erfolgreich angelegt

---

### 2. User-App: Mit neuem User einloggen

```bash
# Terminal 2: User-App starten (parallel zu Admin-App)
streamlit run src/warehouse/presentation/user/main_user_app.py --server.port=8502
```

1. Browser öffnen: `http://localhost:8502`
2. Anmeldung mit:
   - Username: `testuser`
   - Passwort: `Test1234!`

**Erwartung:** ✅ Login funktioniert, User wird eingeloggt!

**VORHER (Bug):** ❌ Fehlermeldung "Benutzername oder Passwort ungültig" (User nicht gefunden)

---

### 3. Cookie-Trennung prüfen

1. In Admin-App eingeloggt bleiben
2. Neuen Browser-Tab öffnen
3. User-App öffnen: `http://localhost:8502`

**Erwartung:**
- ✅ User-App zeigt Login-Screen (nicht automatisch eingeloggt als Admin)
- ✅ Separate Sessions (Admin-Cookie ≠ User-Cookie)

---

### 4. ServiceContainer-Singleton prüfen

**Logs überprüfen:**

```bash
# In Terminal 1 (Admin-App) sollte erscheinen:
🚀 Initializing ServiceContainer (Singleton)...
📦 Creating service instances...
✅ ServiceContainer initialized successfully
🍪 Cookie Manager initialized for ADMIN app (prefix: medealis_admin_)

# In Terminal 2 (User-App) sollte NICHT nochmal erscheinen:
# "Initializing ServiceContainer" (nutzt gleiche Instanz!)
Initializing services via ServiceContainer...
🍪 Cookie Manager initialized for USER app (prefix: medealis_user_)
```

**WICHTIG:** ServiceContainer sollte nur **EINMAL** initialisiert werden (Singleton!)

---

## Erfolgs-Kriterien

| Test | Status | Notizen |
|------|--------|---------|
| 1. Admin: User anlegen | ☐ | User erfolgreich erstellt? |
| 2. User: Login funktioniert | ☐ | Kein "User nicht gefunden" Fehler? |
| 3. Cookie-Trennung | ☐ | Admin-Session ≠ User-Session? |
| 4. ServiceContainer Singleton | ☐ | Nur 1x "Initializing ServiceContainer"? |
| 5. Passwort-Wechsel-Flow | ☐ | Wenn must_change_password=True gesetzt? |

---

## Fehlersuche

### Problem: User-Login schlägt fehl

**Mögliche Ursachen:**

1. **Verschiedene Datenbanken**
   ```python
   # In beiden Apps ausführen:
   from warehouse.infrastructure.database.connection import get_session
   with get_session() as session:
       print(session.bind.url)

   # Sollte identisch sein!
   ```

2. **ServiceContainer nicht korrekt importiert**
   ```bash
   # Logs prüfen - sollte "via ServiceContainer" zeigen
   grep "ServiceContainer" logs/*
   ```

3. **Cache-Problem**
   ```bash
   # Streamlit Cache löschen
   # In Browser: Settings → Clear Cache
   # Oder: Apps neu starten
   ```

### Problem: Cookie-Kollision

**Symptom:** User-App zeigt Admin-Session (oder umgekehrt)

**Lösung prüfen:**
```python
# In login_view.py Zeile 30:
app_type = "admin" if "main_admin_app" in " ".join(sys.argv) else "user"
print(f"App Type: {app_type}")  # Sollte korrekt erkannt werden
```

---

## Nächste Schritte nach erfolgreichem Test

✅ Phase 1 erfolgreich → Weiter mit Phase 3: PostgreSQL Migration
- Docker Postgres starten
- Daten migrieren
- Multi-Client-Setup

---

## Rollback (falls Probleme)

```bash
# Änderungen rückgängig machen:
git checkout src/warehouse/presentation/auth/login_view.py
git checkout src/warehouse/presentation/admin/main_admin_app.py
git checkout src/warehouse/presentation/user/main_user_app.py
git checkout .env

# Neue Dateien löschen:
rm src/warehouse/shared/service_container.py
rm src/warehouse/presentation/shared/document_viewer.py

# Apps neu starten
```
