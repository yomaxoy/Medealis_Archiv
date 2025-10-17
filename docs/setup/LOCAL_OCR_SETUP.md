# 🔐 Lokales OCR Setup - DSGVO-konform

Diese Anleitung erklärt, wie Sie das lokale OCR-System für DSGVO-konforme Lieferschein-Verarbeitung einrichten.

## ⚙️ Vorteile des lokalen OCR

- ✅ **DSGVO-konform**: Keine Daten verlassen Ihr System
- ✅ **Keine API-Kosten**: Komplett lokal ohne externe Services
- ✅ **Offline-fähig**: Funktioniert ohne Internetverbindung
- ✅ **Datenschutz**: Lieferscheine werden nur lokal verarbeitet

## 🛠️ Installation

### 1. Python-Pakete installieren

```bash
pip install -r requirements_local_ocr.txt
```

### 2. Tesseract OCR-Engine installieren

#### Windows
1. Downloaden Sie den Tesseract-Installer von [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Installieren Sie Tesseract (Standard-Pfad: `C:\Program Files\Tesseract-OCR`)
3. Fügen Sie den Tesseract-Pfad zur PATH-Variable hinzu oder setzen Sie:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-deu
```

#### macOS (mit Homebrew)
```bash
brew install tesseract tesseract-lang
```

### 3. Testen der Installation

```python
from src.services.local_ocr_service import local_ocr_service

# Prüfe verfügbare Tools
print("OCR verfügbar:", local_ocr_service.is_available())
print("Tools:", local_ocr_service.available_tools)
```

## 🔍 Funktionsweise

### Pipeline-Ablauf
1. **PDF/Bild Upload** → Benutzer lädt Lieferschein hoch
2. **OCR-Verarbeitung** → pdf2image + pytesseract extrahiert Text
3. **Docling-Analyse** → Strukturiert Dokument-Layout (optional)
4. **Regex-Parsing** → Extrahiert Lieferschein-Daten
5. **DB-Speicherung** → Automatisches Erstellen von Delivery + Items

### Erkannte Datenfelder
- ✅ Lieferscheinnummer (verschiedene Formate)
- ✅ Lieferant/Supplier
- ✅ Lieferdatum
- ✅ Artikel mit Mengen
- ✅ Batch/Charge-Nummern

### Unterstützte Dateiformate
- 📄 **PDF**: Scan-PDFs werden in Bilder konvertiert
- 🖼️ **Bilder**: PNG, JPG, JPEG, TIFF, BMP

## 🎯 Verwendung

### Im AI-Chatbot
1. Öffnen Sie "Deliveries" → "➕ Neu erstellen"
2. Verwenden Sie den KI-Assistenten
3. Laden Sie einen Lieferschein hoch
4. Der Bot erkennt automatisch, ob lokales OCR verfügbar ist
5. Daten werden DSGVO-konform lokal verarbeitet

### Fallback-Verhalten
- Bei verfügbarem lokalen OCR: **🔐 Lokales OCR (DSGVO)**
- Bei nicht verfügbarem lokalen OCR: **🤖 OpenAI** (falls API-Key vorhanden)

## 🐛 Troubleshooting

### "Local OCR not available"
- Prüfen Sie die Tesseract-Installation
- Testen Sie: `tesseract --version` in der Kommandozeile
- Windows: Pfad in PATH-Variable oder direkt setzen

### "No text extracted"
- Bildqualität prüfen (Auflösung, Kontrast)
- Deutsche Sprache: `sudo apt install tesseract-ocr-deu`
- Testen Sie mit verschiedenen Dateiformaten

### Performance-Optimierung
- Große PDFs: Einzelne Seiten verarbeiten
- Bildqualität: 300 DPI optimal für OCR
- Format: Schwarz-weiß-Bilder sind oft besser

## 📊 Vergleich: Lokal vs. Cloud

| Merkmal | Lokales OCR | OpenAI |
|---------|-------------|---------|
| DSGVO | ✅ Vollständig | ⚠️ Extern |
| Kosten | ✅ Kostenlos | 💰 API-Gebühren |
| Setup | ⚙️ Installation nötig | 🔑 Nur API-Key |
| Genauigkeit | 📊 Gut bei klaren Scans | 🎯 Sehr hoch |
| Geschwindigkeit | ⚡ Schnell (lokal) | 🌐 Abhängig von Internet |

## 🔄 Migration

Das System wählt automatisch die beste verfügbare Methode:
1. **Priorität 1**: Lokales OCR (wenn installiert)
2. **Priorität 2**: OpenAI (wenn API-Key vorhanden)
3. **Fallback**: Demo-Modus

Keine Code-Änderungen nötig - das System erkennt automatisch verfügbare Services!