# 🚀 Phase 1 Deployment: Konfigurierbare Pfade

**Status:** ✅ Abgeschlossen
**Version:** 2.0.1
**Datum:** 2025-10-15

---

## 📋 Übersicht

Phase 1 macht **kritische Pfade** konfigurierbar über `.env` Umgebungsvariablen:

- ✅ **QR_CODE_BASE_PATH**: QR-Code Verzeichnis für Label-Generierung
- ✅ **SERVER_STORAGE_PATH**: Server/Netzlaufwerk Basis-Pfad

### Warum diese Änderung?

**Problem vorher:**
```python
# ❌ Hardcodiert im Code
qr_path = "C:/Users/krueg/Medealis/..."
server_path = "A:\"
```

**Lösung jetzt:**
```bash
# ✅ Konfigurierbar in .env
QR_CODE_BASE_PATH=A:\QR-Codes Messprogramme
SERVER_STORAGE_PATH=A:\
```

**Vorteile:**
- ✅ Kein Code-Change für unterschiedliche Server
- ✅ Einfaches Testing (Lokal vs. Server)
- ✅ Flexibles Deployment (Dev/Test/Prod)
- ✅ Best Practice (12-Factor App)

---

## 🔧 Geänderte Dateien

### 1. [.env.example](.env.example)
**Neue Konfigurationsoptionen:**
```bash
# QR-Code Configuration
QR_CODE_BASE_PATH=A:\QR-Codes Messprogramme

# Server Storage Configuration
SERVER_STORAGE_PATH=A:\
```

### 2. [src/warehouse/application/services/document_generation/barcode_generator.py](src/warehouse/application/services/document_generation/barcode_generator.py#L640)
**Methode:** `_get_qr_code_for_article()`

**Änderung:**
```python
# VORHER: Hardcodiert
qr_base_path = Path("C:/Users/krueg/Medealis/...")

# NACHHER: Konfigurierbar mit Fallback
qr_base_path_str = os.getenv("QR_CODE_BASE_PATH")
if qr_base_path_str:
    qr_base_path = Path(qr_base_path_str)
else:
    # Fallback 1: Server
    qr_base_path = Path("A:/QR-Codes Messprogramme")
    if not qr_base_path.exists():
        # Fallback 2: Lokal (Development)
        qr_base_path = Path.home() / "Medealis" / "..."
```

**Fallback-Strategie:**
1. **Primär**: `QR_CODE_BASE_PATH` aus `.env`
2. **Fallback 1**: Server-Pfad `A:\QR-Codes Messprogramme`
3. **Fallback 2**: Lokaler Pfad `~/Medealis/Wareneingang/QR-Codes Messprogramme`

### 3. [src/warehouse/application/services/document_storage/path_resolver.py](src/warehouse/application/services/document_storage/path_resolver.py#L110)
**Property:** `server_storage_path`

**Änderung:**
```python
# VORHER: Hardcodiert
self._server_storage_path = Path(r"A:\Qualitätsmanagement\...")

# NACHHER: Konfigurierbar
server_path_env = os.getenv("SERVER_STORAGE_PATH")
if server_path_env:
    base_path = Path(server_path_env)
    self._server_storage_path = base_path / "Qualitätsmanagement\..."
else:
    # Fallback: Standard A:\
    self._server_storage_path = Path(r"A:\Qualitätsmanagement\...")
```

---

## 📦 Installation & Migration

### Für **NEUE** Installationen:

#### 1. `.env` Datei erstellen
```bash
# Kopiere Vorlage
cp .env.example .env

# Editiere für deinen Server
nano .env  # oder notepad .env
```

#### 2. Pfade konfigurieren
```bash
# ========================================
# PRODUKTION (Server-Deployment)
# ========================================
QR_CODE_BASE_PATH=A:\QR-Codes Messprogramme
SERVER_STORAGE_PATH=A:\

# ========================================
# DEVELOPMENT (Lokale Entwicklung)
# ========================================
QR_CODE_BASE_PATH=C:\Users\IhrName\Medealis\Wareneingang\QR-Codes Messprogramme
SERVER_STORAGE_PATH=C:\Medealis\Server
```

#### 3. QR-Codes kopieren (falls auf Server)
```powershell
# Von lokal zum Server
robocopy "C:\Users\krueg\Medealis\Wareneingang\QR-Codes Messprogramme" `
         "A:\QR-Codes Messprogramme" /E /Z

# Verifizieren
dir "A:\QR-Codes Messprogramme\*.png"
```

### Für **BESTEHENDE** Installationen:

#### Option A: Mit .env (Empfohlen)
```bash
# 1. .env.example als Basis kopieren
cp .env.example .env

# 2. Pfade anpassen
# (Falls du bereits QR-Codes lokal hast, behalte lokalen Pfad)
QR_CODE_BASE_PATH=C:\Users\krueg\Medealis\Wareneingang\QR-Codes Messprogramme

# 3. Anwendung neu starten
# → Lädt .env automatisch beim Start
```

#### Option B: Ohne .env (Fallback)
```bash
# Nichts tun!
# → Anwendung verwendet automatisch Fallback-Pfade
# → Funktioniert wie vorher
```

**Wichtig:** Bestehende Installationen funktionieren **ohne Änderungen** weiter!

---

## ✅ Testing

### Test 1: QR-Code Suche
```bash
# Test mit gesetzter .env Variable
QR_CODE_BASE_PATH=A:\QR-Codes Messprogramme
→ Suche in A:\QR-Codes Messprogramme

# Test ohne .env (Fallback)
# (keine QR_CODE_BASE_PATH gesetzt)
→ Suche in A:\QR-Codes Messprogramme (Fallback 1)
→ Falls nicht gefunden: ~/Medealis/Wareneingang/... (Fallback 2)
```

### Test 2: Label-Generierung
```python
# Test-Artikel mit QR-Code
article_number = "CT0001"
→ ✓ QR-Code gefunden und im Label eingebunden

# Test-Artikel ohne QR-Code
article_number = "UNKNOWN"
→ ⚠️ Kein QR-Code gefunden, Label wird ohne QR-Code erstellt
```

### Test 3: Server Storage
```bash
# Test mit Server-Pfad
SERVER_STORAGE_PATH=A:\
→ Vollständiger Pfad: A:\Qualitätsmanagement\QM_Medealis\...

# Test mit UNC-Pfad
SERVER_STORAGE_PATH=\\server\share\Medealis
→ Vollständiger Pfad: \\server\share\Medealis\Qualitätsmanagement\...
```

---

## 🔍 Logging & Troubleshooting

### Wichtige Log-Meldungen:

#### QR-Code Suche
```log
# Erfolg
✓ QR-Code gefunden: CT0001.png

# Warnung (nicht gefunden)
⚠️  QR-Code Verzeichnis nicht gefunden: A:\QR-Codes Messprogramme
    Tipp: Setze QR_CODE_BASE_PATH in .env
    Labels werden trotzdem generiert (ohne QR-Code)

# Info (Artikel ohne QR)
ℹ️  Kein QR-Code gefunden für Artikel: B0123
    Gesucht in: A:\QR-Codes Messprogramme
    Label wird ohne QR-Code generiert
```

#### Server Storage
```log
# Erfolg
✓ Server Storage Path aus .env: A:\

# Warnung (Laufwerk nicht verfügbar)
⚠️  Server-Laufwerk A:\ nicht verfügbar!
    Bitte Netzlaufwerk verbinden.
    Tipp: Setze SERVER_STORAGE_PATH in .env für alternativen Pfad
```

### Häufige Probleme:

#### Problem 1: QR-Codes werden nicht gefunden
```bash
# Lösung 1: Pfad in .env setzen
QR_CODE_BASE_PATH=C:\Korrekter\Pfad\QR-Codes Messprogramme

# Lösung 2: QR-Codes kopieren
robocopy "Quelle" "A:\QR-Codes Messprogramme" /E

# Lösung 3: Labels funktionieren auch OHNE QR-Code
# → Kein kritischer Fehler!
```

#### Problem 2: Server-Laufwerk nicht erreichbar
```bash
# Lösung 1: Netzlaufwerk verbinden
net use A: \\server\share /persistent:yes

# Lösung 2: UNC-Pfad verwenden
SERVER_STORAGE_PATH=\\server\share\Medealis

# Lösung 3: Lokaler Fallback wird automatisch verwendet
```

---

## 🎯 Deployment-Checkliste

### Vor dem Deployment:
- [ ] `.env.example` nach `.env` kopieren
- [ ] `QR_CODE_BASE_PATH` konfigurieren
- [ ] `SERVER_STORAGE_PATH` konfigurieren (optional)
- [ ] QR-Codes auf Server kopieren (falls Server-Deployment)
- [ ] Service-Account hat Lesezugriff auf QR-Code Ordner

### Nach dem Deployment:
- [ ] Label-Generierung testen (mit QR-Code)
- [ ] Label-Generierung testen (ohne QR-Code)
- [ ] Logs prüfen: Werden korrekte Pfade verwendet?
- [ ] Server-Storage funktioniert (falls aktiviert)

### Rollback (falls Probleme):
```bash
# Einfach .env löschen oder umbenennen
mv .env .env.backup

# → System verwendet automatisch Fallback-Pfade
# → Funktioniert wie vor dem Update
```

---

## 📊 Backward Compatibility

✅ **100% Abwärtskompatibel!**

- **Ohne `.env`**: System verwendet Fallback-Pfade (wie vorher)
- **Mit `.env`**: System verwendet konfigurierte Pfade (neu)
- **Bestehende Installationen**: Funktionieren ohne Änderungen weiter

**Keine Breaking Changes!**

---

## 📞 Support

Bei Problemen:

1. **Logs prüfen**: `~/.medealis/logs/`
2. **Fallback nutzen**: `.env` löschen → automatischer Fallback
3. **Issue erstellen**: Mit Log-Auszug und `.env` Inhalt

---

## 🔮 Nächste Schritte (Phase 2)

Weitere Pfade konfigurierbar machen:
- `USER_DATA_DIR` - Hauptverzeichnis für Dokumente
- `DATABASE_PATH` - Datenbank-Speicherort
- `TEMPLATE_DIR` - Word-Template Verzeichnis
- `LOG_DIR` - Log-Dateien

**Phase 2 Aufwand:** ~2-3 Stunden
**Phase 2 Nutzen:** Vollständig deployment-freundliche Konfiguration

---

**Ende Phase 1 Dokumentation** ✅
