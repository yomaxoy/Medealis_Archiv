# Medealis Archiv - Startanleitung

## 🚀 Schnellstart

### Option 1: Startskript verwenden (EMPFOHLEN)

Doppelklicken Sie auf eine dieser Dateien:
- **`start_app.bat`** - Für Windows CMD
- **`start_app.ps1`** - Für PowerShell (Rechtsklick → "Mit PowerShell ausführen")

### Option 2: Manuell starten

In PowerShell im Projektverzeichnis:

```powershell
.\.venv\Scripts\streamlit.exe run src\warehouse\presentation\admin\main_admin_app.py --server.port=8502
```

## 🌐 URL

Nach dem Start öffnen Sie im Browser:

**http://localhost:8502**

## ⚠️ Wichtige Hinweise

1. **NICHT `venv` aktivieren** - Das Startskript verwendet direkt `.venv\Scripts\streamlit.exe`
2. **Port 8502** wird verwendet (nicht 8501, da dieser oft blockiert ist)
3. Das alte kaputte `venv` Verzeichnis wurde entfernt - nur `.venv` wird verwendet

## 🛠️ Bei Problemen

### Port bereits belegt

Wenn Port 8502 belegt ist, verwenden Sie einen anderen:

```powershell
.\.venv\Scripts\streamlit.exe run src\warehouse\presentation\admin\main_admin_app.py --server.port=8503
```

### Prozess läuft noch

Um laufende Streamlit-Prozesse zu finden und zu beenden:

```powershell
# Prozess finden
netstat -ano | findstr :8502

# Prozess beenden (ersetzen Sie PID mit der Prozess-ID)
taskkill /F /PID <PID>
```

## 📦 Abhängigkeiten installieren

Falls neue Pakete benötigt werden:

```powershell
.\.venv\Scripts\python.exe -m pip install <paketname>
```

## ✅ Ihre App läuft bereits!

Die App wurde erfolgreich gestartet und läuft auf:
**http://localhost:8502**
