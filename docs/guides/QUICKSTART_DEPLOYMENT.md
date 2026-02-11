# ⚡ Quick Start: Server Deployment

**Ziel:** Medealis Warehouse System auf Firmen-Server deployen

**Zeit:** ~15 Minuten

---

## 🚀 Schritt-für-Schritt Anleitung

### **1️⃣ .env Datei erstellen** (2 Min)

```powershell
# Im Projektverzeichnis
cd C:\Path\To\neu_Medealis_Archiv

# .env erstellen
copy .env.example .env

# .env editieren
notepad .env
```

### **2️⃣ .env Konfigurieren** (3 Min)

Trage folgende Werte ein:

```bash
# ==========================================
# STORAGE CONFIGURATION
# ==========================================
USE_SERVER_STORAGE=true
SERVER_STORAGE_PATH=A:\

# ==========================================
# QR-CODE CONFIGURATION
# ==========================================
QR_CODE_BASE_PATH=A:\QR-Codes Messprogramme

# ==========================================
# SHAREPOINT (optional - erstmal deaktiviert)
# ==========================================
USE_SHAREPOINT=false

# ==========================================
# OTHER SETTINGS
# ==========================================
DEBUG=false
```

**Speichern & Schließen!**

### **3️⃣ QR-Codes zum Server kopieren** (5 Min)

```powershell
# Prüfe ob A:\ verfügbar ist
dir A:\

# Falls nicht, Netzlaufwerk verbinden:
net use A: \\firmenserver\medealis /persistent:yes

# QR-Codes kopieren
robocopy "C:\Users\krueg\Medealis\Wareneingang\QR-Codes Messprogramme" `
         "A:\QR-Codes Messprogramme" /E /Z /R:3

# Verifizieren
dir "A:\QR-Codes Messprogramme\*.png"
```

### **4️⃣ Testen** (5 Min)

```powershell
# Anwendung starten
python src\main.py

# Oder direkt Streamlit GUI:
streamlit run src\warehouse\presentation\admin\main_admin_app.py
```

**Tests:**
1. ✅ Label für Artikel mit QR-Code generieren (z.B. CT0001)
2. ✅ Label für Artikel ohne QR-Code generieren
3. ✅ Dokument speichern (prüfe ob auf A:\ landet)

---

## 🔍 Quick-Check

### Alles OK wenn:

```powershell
# 1. .env existiert
dir .env
# → Sollte Datei zeigen

# 2. A:\ erreichbar
dir A:\
# → Sollte Ordner listen

# 3. QR-Codes vorhanden
dir "A:\QR-Codes Messprogramme\*.png"
# → Sollte PNG-Dateien zeigen

# 4. Logs zeigen korrekte Pfade
type "%USERPROFILE%\.medealis\logs\warehouse.log" | findstr "QR-Code"
# → Sollte "✓ QR-Code gefunden" oder "Kein QR-Code gefunden" zeigen
```

---

## ⚠️ Troubleshooting

### Problem: A:\ nicht verfügbar
```powershell
# Lösung: Netzlaufwerk verbinden
net use A: \\firmenserver\medealis /persistent:yes

# Prüfen
net use
```

### Problem: QR-Codes nicht gefunden
```powershell
# Pfad in .env prüfen
type .env | findstr "QR_CODE"

# Existiert der Ordner?
dir "A:\QR-Codes Messprogramme"

# Falls nein, erstellen
mkdir "A:\QR-Codes Messprogramme"
```

### Problem: Berechtigungen
```powershell
# Service-Account benötigt:
# - Lesezugriff: A:\QR-Codes Messprogramme
# - Schreibzugriff: A:\Qualitätsmanagement\...

# Testen als Service-Account
runas /user:SERVICE_ACCOUNT cmd
# Dann: dir A:\
```

---

## 📋 Deployment-Checkliste

### Vor Go-Live:
- [ ] .env konfiguriert
- [ ] A:\ Netzlaufwerk verbunden
- [ ] QR-Codes nach A:\ kopiert
- [ ] Berechtigungen für Service-Account gesetzt
- [ ] Test: Label-Generierung funktioniert
- [ ] Test: Dokument-Speicherung auf A:\ funktioniert

### Nach Go-Live:
- [ ] Logs monitoren: `~/.medealis/logs/`
- [ ] Backup-Script für Datenbank eingerichtet
- [ ] Firewall-Regel für Port 8501

---

## 🎯 Fertig!

Deine Anwendung läuft jetzt auf dem Server mit:
- ✅ Konfigurierbaren Pfaden
- ✅ QR-Code Integration
- ✅ Server-Storage auf A:\
- ✅ Fallback für Development

**Support:** Siehe [DEPLOYMENT_PHASE1.md](DEPLOYMENT_PHASE1.md) für Details

---

**Viel Erfolg! 🚀**
