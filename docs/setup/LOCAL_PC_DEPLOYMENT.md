# Dauerhaftes Hosting auf lokalem Windows-PC

## Übersicht

Diese Anleitung zeigt, wie Sie das Medealis Warehouse System **dauerhaft auf einem normalen Windows-PC** hosten können - ohne Server, ohne Cloud.

---

## Voraussetzungen

- Windows 10/11 PC (oder Workstation)
- Admin-Rechte auf dem PC
- PC läuft 24/7 (oder zu Geschäftszeiten)
- Feste IP im Netzwerk oder Hostname

---

## Schnellstart (10 Minuten)

### Schritt 1: Python installieren

```powershell
# Python 3.11 herunterladen
# https://www.python.org/downloads/
# WICHTIG: "Add Python to PATH" aktivieren!

# Überprüfen
python --version
# Sollte: Python 3.11.x zeigen
```

### Schritt 2: Projekt einrichten

```powershell
# Projekt-Ordner erstellen
mkdir C:\Medealis
cd C:\Medealis

# Ihr Projekt hierhin kopieren
# z.B. via Git oder USB-Stick

# Virtual Environment erstellen
python -m venv venv

# Aktivieren
.\venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

### Schritt 3: .env konfigurieren

```powershell
# .env Datei erstellen
copy .env.example .env

# Bearbeiten
notepad .env
```

**.env Inhalt:**
```ini
ENVIRONMENT=production
DEBUG=false

# API Keys (falls benötigt)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-proj-xxx

# SharePoint
USE_SHAREPOINT=true
SHAREPOINT_SITE_URL=https://ihrefirma.sharepoint.com/sites/Medealis
SHAREPOINT_CLIENT_ID=xxx
SHAREPOINT_CLIENT_SECRET=xxx
SHAREPOINT_TENANT_ID=xxx
```

### Schritt 4: Test-Start

```powershell
# App testen
cd C:\Medealis\neu_Medealis_Archiv
.\venv\Scripts\activate
streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port=8501

# Im Browser öffnen:
http://localhost:8501
```

✅ **Wenn das funktioniert, weitermachen!**

---

## Automatischer Start (Windows-Dienst)

### Variante A: Mit NSSM (Empfohlen)

#### 1. NSSM herunterladen

```powershell
# Download: https://nssm.cc/download
# Entpacken nach: C:\Tools\nssm

# Oder via Chocolatey:
choco install nssm
```

#### 2. Service erstellen

```powershell
# Als Administrator ausführen!
cd C:\Tools\nssm\win64

# Service installieren
.\nssm.exe install MedealisWarehouse

# Im Dialog eingeben:
# Path: C:\Medealis\neu_Medealis_Archiv\venv\Scripts\python.exe
# Startup directory: C:\Medealis\neu_Medealis_Archiv
# Arguments: -m streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

# Alternativ per CLI:
.\nssm.exe install MedealisWarehouse "C:\Medealis\neu_Medealis_Archiv\venv\Scripts\python.exe"
.\nssm.exe set MedealisWarehouse AppDirectory "C:\Medealis\neu_Medealis_Archiv"
.\nssm.exe set MedealisWarehouse AppParameters "-m streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"
.\nssm.exe set MedealisWarehouse DisplayName "Medealis Warehouse System"
.\nssm.exe set MedealisWarehouse Description "Warehouse Management System für Medealis"
.\nssm.exe set MedealisWarehouse Start SERVICE_AUTO_START

# Service starten
.\nssm.exe start MedealisWarehouse

# Status prüfen
.\nssm.exe status MedealisWarehouse
```

#### 3. Im Task-Manager überprüfen

```
Task-Manager → Dienste → "MedealisWarehouse" sollte "Wird ausgeführt" zeigen
```

### Variante B: Mit Windows Task Scheduler (Einfacher, weniger robust)

#### 1. Batch-Script erstellen

**Erstellen:** `C:\Medealis\start_warehouse.bat`

```batch
@echo off
cd /d C:\Medealis\neu_Medealis_Archiv
call venv\Scripts\activate
streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
```

#### 2. Task Scheduler konfigurieren

```powershell
# PowerShell als Admin

# Task erstellen
$action = New-ScheduledTaskAction -Execute "C:\Medealis\start_warehouse.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "MedealisWarehouse" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Startet Medealis Warehouse bei PC-Start"
```

**Oder manuell:**
```
1. Task Scheduler öffnen (taskschd.msc)
2. "Einfache Aufgabe erstellen"
3. Name: "MedealisWarehouse"
4. Trigger: "Beim Start des Computers"
5. Aktion: "Programm starten"
6. Programm: C:\Medealis\start_warehouse.bat
7. Fertigstellen
```

---

## Netzwerk-Zugriff einrichten

### 1. Firewall-Regel erstellen

```powershell
# Als Administrator
New-NetFirewallRule -DisplayName "Medealis Warehouse" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow -Profile Domain,Private
```

### 2. Lokale IP-Adresse ermitteln

```powershell
ipconfig | findstr IPv4

# Notieren Sie die IP, z.B.: 192.168.1.100
```

### 3. Feste IP vergeben (Optional, aber empfohlen)

```
Windows-Einstellungen → Netzwerk → Eigenschaften
→ IP-Einstellungen bearbeiten → Manuell
→ IP: 192.168.1.100 (Beispiel)
→ Subnetz: 255.255.255.0
→ Gateway: 192.168.1.1 (Ihr Router)
→ DNS: 192.168.1.1
```

### 4. Zugriff testen

```powershell
# Vom Host-PC selbst
http://localhost:8501

# Von anderem PC im Netzwerk
http://192.168.1.100:8501
```

---

## Energieverwaltung anpassen

Damit der PC nicht in den Ruhezustand geht:

```powershell
# Ruhezustand deaktivieren
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0

# Oder in Windows-Einstellungen:
# System → Netzbetrieb und Energie → Bildschirm und Energie → Nie
```

---

## Benutzerfreundliche URL (Optional)

### Hostname im Netzwerk verwenden

**Auf dem Host-PC:**

```powershell
# Computernamen festlegen
Rename-Computer -NewName "MEDEALIS-SERVER"
Restart-Computer

# Zugriff dann über:
http://medealis-server:8501
# oder
http://medealis-server.firma.local:8501
```

**Oder: DNS-Eintrag im Router/AD erstellen**
```
medealis.firma.local → 192.168.1.100
```

Dann zugreifen via: `http://medealis.firma.local:8501`

---

## Monitoring & Wartung

### 1. Health-Check Script

**Erstellen:** `C:\Medealis\scripts\health_check.ps1`

```powershell
# Health Check für lokalen PC-Server
$AppUrl = "http://localhost:8501"
$LogFile = "C:\Medealis\logs\health_check.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Add-Content $LogFile
    Write-Host $Message
}

# App-Status prüfen
try {
    $response = Invoke-WebRequest -Uri $AppUrl -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "✅ OK: App läuft normal"
    }
} catch {
    Write-Log "❌ ERROR: App antwortet nicht!"

    # Versuch neu zu starten
    Write-Log "Versuche App neu zu starten..."
    Restart-Service MedealisWarehouse -ErrorAction SilentlyContinue

    Start-Sleep -Seconds 15

    try {
        $response = Invoke-WebRequest -Uri $AppUrl -TimeoutSec 10 -UseBasicParsing
        Write-Log "✅ App erfolgreich neu gestartet"
    } catch {
        Write-Log "❌ CRITICAL: Neustart fehlgeschlagen! Manuelle Intervention nötig."

        # Optional: Email-Benachrichtigung senden
        # Send-MailMessage ...
    }
}

# Disk Space prüfen
$drive = Get-PSDrive C
$freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
if ($freeSpaceGB -lt 10) {
    Write-Log "⚠️ WARNING: Nur noch $freeSpaceGB GB frei auf C:"
}

# Datenbank-Größe
$dbPath = "C:\Users\$env:USERNAME\.medealis\warehouse_new.db"
if (Test-Path $dbPath) {
    $dbSizeMB = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
    Write-Log "📊 Datenbank-Größe: $dbSizeMB MB"
}

Write-Log "Health Check abgeschlossen"
```

**Task Scheduler für Health-Check (alle 15 Minuten):**

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Medealis\scripts\health_check.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName "MedealisHealthCheck" -Action $action -Trigger $trigger -User "SYSTEM" -RunLevel Highest
```

### 2. Automatische Backups

**Script:** `C:\Medealis\scripts\backup.ps1`

```powershell
# Automatisches Backup
$SourceDB = "C:\Users\$env:USERNAME\.medealis\warehouse_new.db"
$BackupDir = "C:\Medealis\backups"
$RetentionDays = 30

# Backup-Ordner erstellen
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Backup mit Timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "warehouse_backup_$timestamp.db"

# Kopieren
Copy-Item $SourceDB $backupFile -Force
Write-Host "✅ Backup erstellt: $backupFile"

# Alte Backups löschen
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem $BackupDir -Filter "warehouse_backup_*.db" |
    Where-Object { $_.LastWriteTime -lt $cutoffDate } |
    Remove-Item -Force

Write-Host "✅ Alte Backups bereinigt (älter als $RetentionDays Tage)"
```

**Task Scheduler (täglich um 2:00 Uhr):**

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Medealis\scripts\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

Register-ScheduledTask -TaskName "MedealisBackup" -Action $action -Trigger $trigger -User "SYSTEM" -RunLevel Highest
```

---

## Vor- und Nachteile: PC vs. Server vs. Cloud

| Kriterium | Lokaler PC | Firmenserver | Cloud |
|-----------|------------|--------------|-------|
| **Kosten** | 0€ (nur Strom) | 0€ (bereits vorhanden) | 30-100€/Monat |
| **Setup-Zeit** | 1 Stunde | 3 Stunden | 30 Minuten |
| **Wartung** | Mittel | Mittel | Minimal |
| **Verfügbarkeit** | 99% (wenn PC läuft) | 99.9% | 99.9% |
| **Performance** | Begrenzt | Gut | Sehr gut |
| **Skalierung** | Keine | Begrenzt | Unbegrenzt |
| **DSGVO** | ✅ Perfekt | ✅ Perfekt | ⚠️ Prüfen |
| **Backup** | Manuell | Semi-Auto | Automatisch |
| **Monitoring** | Basic | Mittel | Professionell |

---

## Empfehlung für Ihr Projekt

### ✅ **Lokaler PC ist perfekt, wenn:**
- Budget sehr begrenzt
- Wenige User (<10 gleichzeitig)
- Nur Bürozeiten genutzt (8-18 Uhr)
- Prototyp/Testing-Phase
- Sie einen ungenutzten PC haben

### ⚠️ **Besser Firmenserver, wenn:**
- 24/7 Verfügbarkeit wichtig
- >10 gleichzeitige User
- Produktiv-System
- IT-Abteilung vorhanden
- Professionelles Backup wichtig

### ☁️ **Cloud nur, wenn:**
- Keine eigene Hardware
- Remote-Teams weltweit
- Keine IT-Abteilung
- DSGVO kein Problem (nicht-medizinische Daten)

---

## Troubleshooting

### Problem: Service startet nicht

```powershell
# Logs prüfen (NSSM)
nssm status MedealisWarehouse

# Manuell starten zum Testen
cd C:\Medealis\neu_Medealis_Archiv
.\venv\Scripts\activate
streamlit run src/warehouse/presentation/admin/main_admin_app.py

# Fehler anzeigen lassen
```

### Problem: Kein Netzwerk-Zugriff

```powershell
# Firewall prüfen
Get-NetFirewallRule -DisplayName "Medealis Warehouse"

# Port testen
netstat -ano | findstr :8501

# Von anderem PC
Test-NetConnection -ComputerName <pc-ip> -Port 8501
```

### Problem: App schläft nach Inaktivität

Das passiert bei Streamlit Community Cloud, **nicht bei lokalem Hosting**! ✅

### Problem: PC geht in Ruhezustand

```powershell
# Energieeinstellungen prüfen
powercfg /query

# Ruhezustand deaktivieren
powercfg -change -standby-timeout-ac 0
```

---

## Checkliste: Lokaler PC-Setup

- [ ] Python 3.11+ installiert
- [ ] Virtual Environment erstellt
- [ ] Dependencies installiert
- [ ] .env konfiguriert
- [ ] App manuell getestet (funktioniert!)
- [ ] Windows-Dienst eingerichtet (NSSM oder Task Scheduler)
- [ ] Firewall-Regel erstellt
- [ ] Feste IP vergeben
- [ ] Ruhezustand deaktiviert
- [ ] Health-Check Script aktiviert
- [ ] Backup-Script aktiviert
- [ ] Von anderem PC getestet
- [ ] Dokumentation erstellt
- [ ] Team informiert

---

## Fazit

**Lokales PC-Hosting ist eine völlig legitime Lösung** für Ihr Projekt, besonders in der Anfangsphase. Es kostet nichts, ist schnell eingerichtet, und Sie behalten volle Kontrolle.

**Später upgraden:** Wenn Ihr System wächst, können Sie jederzeit auf einen dedizierten Server oder Cloud umziehen - die Anwendung ist identisch!

---

**Erstellt für:** Medealis Warehouse Management System
**Version:** 2.0
**Datum:** 2025
