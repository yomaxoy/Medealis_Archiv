# 🔑 API Keys Setup für Claude und OCR

## Übersicht

Damit **Claude AI** und **OCR** dauerhaft im Windows Service verfügbar sind, müssen die API-Keys korrekt konfiguriert werden.

---

## ✅ Schritt-für-Schritt Anleitung

### 1. Claude API Key besorgen

1. Gehe zu https://console.anthropic.com/
2. Erstelle einen Account oder melde dich an
3. Navigiere zu "API Keys"
4. Erstelle einen neuen API Key
5. **Kopiere den Key sofort** (er wird nur einmal angezeigt!)

**Kosten**: Claude API verwendet Pay-per-Use Pricing
- Claude Sonnet 4: ~$3 pro Million Input-Tokens
- Typischer Dokumenten-Scan: ~$0.01-0.05 pro Dokument

### 2. .env Datei erstellen

**WICHTIG**: Die `.env` Datei muss im **Hauptverzeichnis** des Projekts liegen!

```plaintext
C:\Users\KlausKrüger\Desktop\neu_Medealis_Archiv\.env
```

#### Option A: Kopiere .env.example

```powershell
# Im Projektverzeichnis
copy .env.example .env
```

#### Option B: Erstelle neue .env Datei

Erstelle eine neue Datei namens `.env` mit folgendem Inhalt:

```env
# ==========================================
# API KEYS
# ==========================================

# Anthropic Claude API Key (ERFORDERLICH)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==========================================
# STORAGE CONFIGURATION
# ==========================================
USE_SERVER_STORAGE=true
USE_SHAREPOINT=false

# ==========================================
# OTHER SETTINGS
# ==========================================
DEBUG=false
```

**Ersetze `sk-ant-api03-xxx...`** mit deinem echten API Key!

### 3. .env Datei in .gitignore eintragen

**WICHTIG**: Die `.env` Datei darf **NIEMALS** ins Git-Repository!

Prüfe, ob `.env` in der `.gitignore` steht:

```bash
# In .gitignore sollte stehen:
.env
.env.local
```

### 4. Service neu installieren

Nach dem Erstellen der `.env` Datei:

```powershell
# Als Administrator ausführen
cd service

# Falls Service bereits installiert ist, neu installieren
.\uninstall_service.bat
.\install_service.bat
.\start_service.bat
```

---

## 🔍 OCR Setup (Tesseract)

### OCR Installation prüfen

Der Service benötigt **Tesseract OCR** für die Dokumentenerkennung.

#### Tesseract installieren (falls noch nicht vorhanden)

1. **Download**: https://github.com/UB-Mannheim/tesseract/wiki
2. Installiere Tesseract nach: `C:\Program Files\Tesseract-OCR\`
3. Wähle bei der Installation: **Deutsch (deu)** als zusätzliche Sprache

#### Tesseract testen

```powershell
# In PowerShell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

Sollte die Version anzeigen (z.B. `tesseract 5.3.0`)

---

## ✅ Verfügbarkeit prüfen

### Im Service Event Log prüfen

Nach dem Service-Start:

```powershell
# Event Viewer öffnen
eventvwr

# Navigiere zu:
# Windows Logs → Application
# Filtere nach: "MedealisWarehouse"
```

Erfolgsmeldungen:
- ✅ `ANTHROPIC_API_KEY is set - Claude features enabled`
- ✅ `Admin App erfolgreich gestartet`
- ✅ `User App erfolgreich gestartet`

Warnungen:
- ⚠️ `ANTHROPIC_API_KEY not set - Claude features will be unavailable`
  → API Key fehlt oder .env nicht geladen

### In der Anwendung testen

1. Öffne Admin App: http://localhost:8501
2. Gehe zu: **Wareneingang** → **Lieferschein scannen**
3. Lade ein Test-PDF hoch
4. Wenn Claude verfügbar ist: ✅ Automatische Datenextraktion startet
5. Wenn Claude nicht verfügbar: ⚠️ Fehlermeldung erscheint

---

## 🔧 Troubleshooting

### Problem: Claude API nicht verfügbar

**Symptome:**
- Fehlermeldung: "Claude API nicht verfügbar"
- Keine automatische Dokumentenanalyse

**Lösungen:**

1. **Prüfe .env Datei:**
   ```powershell
   # Datei muss existieren
   Test-Path C:\Users\KlausKrüger\Desktop\neu_Medealis_Archiv\.env
   # Sollte: True
   ```

2. **Prüfe API Key Format:**
   - Muss beginnen mit: `sk-ant-api03-`
   - Keine Leerzeichen vor/nach dem Key
   - Keine Anführungszeichen um den Key

3. **Prüfe python-dotenv Installation:**
   ```powershell
   .\.venv\Scripts\python.exe -c "import dotenv; print(dotenv.__version__)"
   ```

   Falls Fehler:
   ```powershell
   .\.venv\Scripts\pip.exe install python-dotenv
   ```

4. **Service neu starten:**
   ```powershell
   cd service
   .\stop_service.bat
   .\start_service.bat
   ```

### Problem: OCR nicht verfügbar

**Symptome:**
- Fehlermeldung: "OCR not available"
- Keine Texterkennung in Dokumenten

**Lösungen:**

1. **Tesseract installieren** (siehe oben)

2. **Tesseract-Pfad prüfen:**
   ```powershell
   Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe"
   # Sollte: True
   ```

3. **Deutsche Sprachdaten prüfen:**
   ```powershell
   Test-Path "C:\Program Files\Tesseract-OCR\tessdata\deu.traineddata"
   # Sollte: True
   ```

### Problem: Environment-Variablen werden nicht geladen

**Symptome:**
- API Key ist in .env aber Service meldet "not set"

**Lösungen:**

1. **Prüfe Datei-Encoding:**
   - .env Datei muss UTF-8 sein (OHNE BOM)
   - Mit Notepad++ prüfen: Encoding → "UTF-8"

2. **Prüfe Zeilenumbrüche:**
   - Windows: CRLF (`\r\n`)
   - Unix: LF (`\n`)
   - Beide funktionieren, aber **nicht mischen**!

3. **Service als Administrator installieren:**
   - Rechtsklick auf `install_service.bat`
   - "Als Administrator ausführen"

---

## 📊 Best Practices

### Sicherheit

1. **API Key niemals ins Git**
   - Immer in `.env` speichern
   - `.env` in `.gitignore` eintragen

2. **API Key Rotation**
   - Regelmäßig neue Keys erstellen
   - Alte Keys in Anthropic Console widerrufen

3. **Zugriffskontrolle**
   - `.env` Datei-Berechtigungen beschränken
   - Nur Administratoren Zugriff geben

### Kostenoptimierung

1. **API Usage überwachen**
   - Console: https://console.anthropic.com/usage
   - Budget-Limits setzen

2. **Caching nutzen**
   - Die App cached bereits verarbeitete Dokumente
   - Vermeide doppelte Scans

3. **Kleineres Modell für einfache Tasks**
   - Standardmäßig: Claude Sonnet 4 (balanced)
   - Für simple Extraktion: Claude Haiku (günstig)

---

## 📞 Support

Bei Problemen:

1. **Event Viewer** prüfen (siehe oben)
2. **Log-Dateien** prüfen: `data/logs/`
3. **Service Status** prüfen: `status_service.bat`
4. **API Status** prüfen: https://status.anthropic.com/

---

## ✅ Checkliste

Nach Setup sollten alle diese Punkte ✅ sein:

- [ ] `.env` Datei erstellt im Hauptverzeichnis
- [ ] `ANTHROPIC_API_KEY` eingetragen
- [ ] Tesseract OCR installiert
- [ ] Deutsche Sprachdaten (deu) installiert
- [ ] Service neu installiert
- [ ] Service gestartet
- [ ] Event Log zeigt "Claude features enabled"
- [ ] Test-Scan in der App erfolgreich
- [ ] Beide Apps erreichbar (8501 + 8502)

**Wenn alle Punkte ✅ sind: Claude und OCR sind dauerhaft verfügbar!** 🎉
