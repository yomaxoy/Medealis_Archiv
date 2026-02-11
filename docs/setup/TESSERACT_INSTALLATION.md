# Tesseract OCR Installation für Medealis Warehouse

## Was ist Tesseract OCR?

Tesseract OCR ist eine Open-Source-Software zur optischen Texterkennung (OCR). Sie ermöglicht es, Text aus Bildern und PDF-Dokumenten zu extrahieren.

## Warum wird Tesseract benötigt?

In der Medealis Warehouse App wird Tesseract verwendet für:
- **Fallback-Lösung**: Wenn Claude API nicht verfügbar ist
- **Backup-Texterkennung**: Zusätzliche OCR-Funktionalität neben Claude
- **Offline-Betrieb**: OCR ohne Internet-Verbindung

**WICHTIG**: Mit Claude API (bereits konfiguriert) funktioniert die App vollständig. Tesseract ist **optional** für zusätzliche Features.

## Installation auf Windows

### Schritt 1: Tesseract Software herunterladen

1. Öffnen Sie: https://github.com/UB-Mannheim/tesseract/wiki
2. Laden Sie den **neuesten Windows Installer** herunter (z.B. `tesseract-ocr-w64-setup-5.x.x.exe`)
3. Führen Sie den Installer aus

### Schritt 2: Installation durchführen

1. **Installationspfad wählen**:
   - Standard: `C:\Program Files\Tesseract-OCR`
   - Merken Sie sich den Pfad!

2. **Sprachpakete auswählen**:
   - ✅ **Deutsch** (deu) - WICHTIG für deutsche Dokumente
   - ✅ **Englisch** (eng) - Standard
   - Optional: Weitere Sprachen nach Bedarf

3. **Installation abschließen**
   - Klicken Sie auf "Install"
   - Warten Sie bis die Installation fertig ist

### Schritt 3: Umgebungsvariable setzen (WICHTIG!)

Damit Python Tesseract findet, müssen Sie den Pfad zur PATH-Variable hinzufügen:

#### Option A: Automatisch über PowerShell (als Administrator)
```powershell
# PowerShell als Administrator öffnen
$tesseractPath = "C:\Program Files\Tesseract-OCR"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$tesseractPath", "Machine")
```

#### Option B: Manuell über Windows-Einstellungen
1. Drücken Sie `Windows + Pause` (oder Rechtsklick auf "Dieser PC" → Eigenschaften)
2. Klicken Sie auf "Erweiterte Systemeinstellungen"
3. Klicken Sie auf "Umgebungsvariablen"
4. Unter "Systemvariablen" suchen Sie "Path"
5. Klicken Sie auf "Bearbeiten"
6. Klicken Sie auf "Neu"
7. Fügen Sie hinzu: `C:\Program Files\Tesseract-OCR`
8. Klicken Sie auf "OK" (alle Fenster)

### Schritt 4: Installation überprüfen

Öffnen Sie eine **neue** Eingabeaufforderung (wichtig: neu öffnen!) und testen Sie:

```bash
tesseract --version
```

Sie sollten die Versionsnummer sehen, z.B.:
```
tesseract 5.3.0
```

### Schritt 5: Python-Bibliothek installieren

Wechseln Sie zum Projekt-Verzeichnis und aktivieren Sie das Virtual Environment:

```bash
cd C:\Users\KlausKrüger\Desktop\neu_Medealis_Archiv
.venv\Scripts\activate
pip install pytesseract pillow opencv-python
```

**Benötigte Python-Pakete:**
- `pytesseract` - Python-Wrapper für Tesseract
- `pillow` - Bildverarbeitung
- `opencv-python` - Computer Vision (für OCR-Preprocessing)

### Schritt 6: Konfiguration in der App

Die App erkennt Tesseract automatisch, wenn:
1. Tesseract im PATH ist (siehe Schritt 3)
2. `pytesseract` installiert ist (siehe Schritt 5)

## Alternative: Manuelle Pfad-Konfiguration

Falls Tesseract nicht automatisch gefunden wird, können Sie den Pfad direkt in der `.env` Datei angeben:

Fügen Sie in `.env` hinzu:
```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Testen

Nach der Installation starten Sie die App neu:

```bash
start_admin.bat
```

In den Logs sollte erscheinen:
```
INFO:warehouse.application.processors.ocr_processor:OCR available: Tesseract
```

Statt der bisherigen Warnung:
```
WARNING:warehouse.application.processors.ocr_processor:OCR not available: No module named 'pytesseract'
```

## Troubleshooting

### Problem: "Tesseract nicht gefunden"
**Lösung**:
- Stellen Sie sicher, dass Tesseract im PATH ist
- Öffnen Sie eine NEUE Eingabeaufforderung nach PATH-Änderung
- Oder setzen Sie `TESSERACT_CMD` in `.env`

### Problem: "Error opening data file"
**Lösung**:
- Deutsche Sprachdaten fehlen
- Installieren Sie Tesseract neu und wählen Sie "deu" Sprachpaket

### Problem: "pytesseract not found"
**Lösung**:
```bash
.venv\Scripts\activate
pip install pytesseract pillow
```

## Zusammenfassung

**Was Sie brauchen:**
1. ✅ Tesseract-OCR Software (von GitHub herunterladen)
2. ✅ Tesseract im Windows PATH
3. ✅ Python-Bibliothek `pytesseract` installiert
4. ✅ Sprachpaket Deutsch (deu) installiert

**Nach erfolgreicher Installation:**
- OCR-Funktionalität verfügbar
- Backup neben Claude API
- Offline-Texterkennung möglich

---

**Hinweis**: Die App funktioniert bereits mit Claude API vollständig. Tesseract ist eine optionale Ergänzung für zusätzliche Features und Offline-Betrieb.
