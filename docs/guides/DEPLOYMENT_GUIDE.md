# Deployment-Leitfaden: Medealis Warehouse System auf Firmenserver

## Inhaltsverzeichnis
1. [Überblick & Voraussetzungen](#1-überblick--voraussetzungen)
2. [Empfohlene Deployment-Architektur](#2-empfohlene-deployment-architektur)
3. [Detaillierte Setup-Anleitung](#3-detaillierte-setup-anleitung)
4. [Security & Best Practices](#4-security--best-practices)
5. [Wartung & Monitoring](#5-wartung--monitoring)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Überblick & Voraussetzungen

### Was wird deployed?
- **Streamlit Web-Anwendung** (Port 8501)
- **SQLite Datenbank** (lokale Datei)
- **SharePoint Integration** (optional)
- **Python 3.10+ Backend**

### Server-Anforderungen (Minimum)
- **OS**: Windows Server 2016+ oder Linux Server
- **CPU**: 2 Cores
- **RAM**: 4 GB
- **Speicher**: 20 GB (für Anwendung + Datenbank)
- **Netzwerk**: Statische IP oder interner DNS-Eintrag

### Wichtige Entscheidungen vor dem Deployment

| Entscheidung | Option A | Option B |
|--------------|----------|----------|
| **Server-OS** | Windows Server (einfacher für Sie) | Linux Server (performanter) |
| **Zugriff** | Nur intern (VPN/LAN) | Extern mit Reverse Proxy |
| **Authentifizierung** | Windows AD Integration | Eigenes Login-System |
| **Datenbank** | SQLite (aktuell) | PostgreSQL (für >50 User) |

---

## 2. Empfohlene Deployment-Architektur

### Option A: Einfaches Windows Server Deployment (EMPFOHLEN für Einstieg)

```
┌─────────────────────────────────────────┐
│     Windows Server 2019/2022            │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Python 3.11 Virtual Environment │ │
│  │                                   │ │
│  │   Streamlit App (Port 8501)      │ │
│  │   ├─ main.py                     │ │
│  │   ├─ warehouse/                  │ │
│  │   └─ SQLite DB                   │ │
│  └───────────────────────────────────┘ │
│            ↕                            │
│  ┌───────────────────────────────────┐ │
│  │   NSSM (Windows Service)         │ │
│  │   Auto-Start bei Server-Boot     │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
           ↕
  Firmen-LAN (192.168.x.x)
           ↕
  User-Browser: http://server-ip:8501
```

**Vorteile:**
✅ Einfach einzurichten
✅ Windows AD Integration möglich
✅ Keine zusätzliche Software nötig
✅ Läuft als Windows-Dienst

**Nachteile:**
❌ Kein HTTPS (nur intern sicher)
❌ Keine Lastverteilung
❌ Port-Zugriff muss freigeschaltet werden

---

### Option B: Professionelles Deployment mit Reverse Proxy

```
┌────────────────────────────────────────────┐
│         Windows Server / Linux             │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  Nginx Reverse Proxy (Port 443)     │ │
│  │  SSL/TLS Zertifikat                  │ │
│  │  https://warehouse.firma.de          │ │
│  └──────────────────────────────────────┘ │
│            ↓                               │
│  ┌──────────────────────────────────────┐ │
│  │  Streamlit App (localhost:8501)     │ │
│  │  + Authentifizierung                 │ │
│  └──────────────────────────────────────┘ │
│            ↓                               │
│  ┌──────────────────────────────────────┐ │
│  │  SQLite / PostgreSQL Datenbank      │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

**Vorteile:**
✅ HTTPS verschlüsselt
✅ Professionelle URL (warehouse.firma.de)
✅ Bessere Security
✅ Load Balancing möglich

**Nachteile:**
❌ Komplexere Einrichtung
❌ Nginx-Kenntnisse erforderlich
❌ SSL-Zertifikat notwendig

---

## 3. Detaillierte Setup-Anleitung

### Setup A: Einfaches Windows Server Deployment

#### Schritt 1: Server vorbereiten

```powershell
# 1. Windows Updates installieren
# Windows Update durchführen

# 2. Python installieren
# Download: https://www.python.org/downloads/
# Version 3.11+ empfohlen
# WICHTIG: "Add Python to PATH" aktivieren!

# 3. Python überprüfen
python --version
# Sollte: Python 3.11.x anzeigen
```

#### Schritt 2: Anwendung auf Server kopieren

```powershell
# Ordner erstellen
mkdir C:\Medealis
cd C:\Medealis

# Ihre Anwendung hierhin kopieren (z.B. via Git oder Netzlaufwerk)
# Kompletter Ordner: neu_Medealis_Archiv

# Oder via Git:
git clone <ihr-repository-url> C:\Medealis\warehouse
cd C:\Medealis\warehouse
```

#### Schritt 3: Virtual Environment einrichten

```powershell
cd C:\Medealis\warehouse

# Virtual Environment erstellen
python -m venv venv

# Aktivieren
.\venv\Scripts\activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# Test: Anwendung starten
python src/main.py
# Sollte ohne Fehler starten
```

#### Schritt 4: Umgebungsvariablen konfigurieren

```powershell
# .env Datei erstellen
copy .env.example .env

# .env bearbeiten (mit Notepad)
notepad .env
```

**Wichtige .env Einstellungen:**
```ini
# Environment
ENVIRONMENT=production
DEBUG=false

# API Keys (falls benötigt)
ANTHROPIC_API_KEY=sk-ant-xxxx...
OPENAI_API_KEY=sk-proj-xxxx...

# SharePoint (optional)
USE_SHAREPOINT=true
SHAREPOINT_SITE_URL=https://ihrefirma.sharepoint.com/sites/MedealisWareneingang
SHAREPOINT_CLIENT_ID=xxx
SHAREPOINT_CLIENT_SECRET=xxx
SHAREPOINT_TENANT_ID=xxx

# Datenbank
DATABASE_PATH=C:\Medealis\data\warehouse_new.db
```

#### Schritt 5: Als Windows Service einrichten (mit NSSM)

```powershell
# NSSM herunterladen
# https://nssm.cc/download
# nssm-2.24.zip herunterladen und entpacken

# NSSM zu System Path hinzufügen oder direkt verwenden
cd C:\Tools\nssm\win64

# Service installieren
.\nssm.exe install MedealisWarehouse

# Im GUI-Dialog eingeben:
# Path: C:\Medealis\warehouse\venv\Scripts\python.exe
# Startup directory: C:\Medealis\warehouse
# Arguments: -m streamlit run src/warehouse/presentation/admin/main_admin_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

# Service-Details konfigurieren
.\nssm.exe set MedealisWarehouse Description "Medealis Warehouse Management System"
.\nssm.exe set MedealisWarehouse Start SERVICE_AUTO_START

# Umgebungsvariablen für Service setzen
.\nssm.exe set MedealisWarehouse AppEnvironmentExtra ENVIRONMENT=production DEBUG=false

# Service starten
.\nssm.exe start MedealisWarehouse

# Status prüfen
.\nssm.exe status MedealisWarehouse
```

#### Schritt 6: Firewall-Regel erstellen

```powershell
# Windows Firewall Regel für Port 8501
New-NetFirewallRule -DisplayName "Medealis Warehouse" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow

# Oder manuell:
# Windows Firewall -> Erweiterte Einstellungen -> Eingehende Regeln -> Neue Regel
# Port: 8501, TCP, Zulassen
```

#### Schritt 7: Zugriff testen

```powershell
# Auf dem Server selbst
http://localhost:8501

# Von anderem PC im Netzwerk
http://<server-ip>:8501
# z.B. http://192.168.1.100:8501
```

---

### Setup B: Mit Nginx Reverse Proxy (Optional, für HTTPS)

#### Zusätzliche Schritte nach Setup A:

#### 1. Nginx installieren (Windows)

```powershell
# Nginx für Windows herunterladen
# http://nginx.org/en/download.html
# nginx-1.24.0 (stable)

# Entpacken nach C:\nginx

cd C:\nginx

# nginx.conf bearbeiten
notepad conf\nginx.conf
```

#### 2. Nginx Konfiguration

```nginx
# conf/nginx.conf

worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    upstream streamlit {
        server 127.0.0.1:8501;
    }

    server {
        listen       80;
        server_name  warehouse.firma.local;  # Ihre interne Domain

        # Optional: Redirect zu HTTPS
        # return 301 https://$server_name$request_uri;

        location / {
            proxy_pass http://streamlit;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Wichtig für Streamlit WebSocket
            proxy_read_timeout 86400;
        }

        # Health Check Endpoint
        location /health {
            access_log off;
            return 200 "OK";
            add_header Content-Type text/plain;
        }
    }

    # HTTPS Server (optional, benötigt SSL-Zertifikat)
    # server {
    #     listen       443 ssl;
    #     server_name  warehouse.firma.local;
    #
    #     ssl_certificate      C:/nginx/ssl/cert.pem;
    #     ssl_certificate_key  C:/nginx/ssl/key.pem;
    #
    #     location / {
    #         proxy_pass http://streamlit;
    #         # ... gleiche Proxy-Einstellungen wie oben
    #     }
    # }
}
```

#### 3. Nginx als Service starten

```powershell
# Nginx testen
C:\nginx\nginx.exe -t

# Nginx starten
C:\nginx\nginx.exe

# Nginx als Service mit NSSM
nssm install NginxProxy C:\nginx\nginx.exe
nssm start NginxProxy

# Zugriff jetzt über:
http://warehouse.firma.local
```

---

## 4. Security & Best Practices

### 4.1 Netzwerk-Security

```yaml
Empfehlungen:
  ✅ Nur im Firmen-LAN erreichbar
  ✅ VPN erforderlich für Remote-Zugriff
  ✅ Firewall-Regeln nur für benötigte Ports
  ✅ Kein direkter Internet-Zugriff

Wenn Internet-Zugriff nötig:
  ✅ HTTPS mit gültigem Zertifikat
  ✅ Reverse Proxy (Nginx)
  ✅ Rate Limiting
  ✅ Web Application Firewall (WAF)
```

### 4.2 Authentifizierung hinzufügen

**Erstellen Sie:** `src/warehouse/presentation/admin/auth.py`

```python
"""
Einfache Authentifizierung für Streamlit App
"""
import streamlit as st
import hashlib
import os

def hash_password(password: str) -> str:
    """Hash password mit SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_authentication():
    """Prüft ob User eingeloggt ist"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        show_login_page()
        return False

    return True

def show_login_page():
    """Zeigt Login-Formular"""
    st.title("🔐 Medealis Warehouse - Login")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")

        if st.button("Login", use_container_width=True):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Ungültige Anmeldedaten")

def authenticate(username: str, password: str) -> bool:
    """
    Authentifiziert User gegen Umgebungsvariablen oder Datenbank

    TODO: Für Production - gegen Active Directory oder Datenbank prüfen
    """
    # Einfache Version: Aus Umgebungsvariablen
    valid_users = {
        os.getenv("ADMIN_USER", "admin"): hash_password(
            os.getenv("ADMIN_PASSWORD", "medealis2024")
        ),
        # Weitere User hier hinzufügen
    }

    return valid_users.get(username) == hash_password(password)

def logout():
    """Loggt User aus"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()
```

**In Ihrer main_admin_app.py einbinden:**

```python
import streamlit as st
from auth import check_authentication, logout

# Ganz am Anfang
if not check_authentication():
    st.stop()

# Ihre normale App hier
st.title("Warehouse Management")

# Logout-Button in Sidebar
with st.sidebar:
    if st.button("🚪 Logout"):
        logout()
```

### 4.3 Datenbank-Backups

**Erstellen Sie:** `scripts/backup_database.ps1`

```powershell
# Automatisches Datenbank-Backup Script
param(
    [string]$DatabasePath = "C:\Medealis\data\warehouse_new.db",
    [string]$BackupDir = "C:\Medealis\backups",
    [int]$RetentionDays = 30
)

# Backup-Ordner erstellen
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Backup mit Timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "warehouse_backup_$timestamp.db"

# Kopieren
Copy-Item $DatabasePath $backupFile -Force

# Alte Backups löschen (älter als RetentionDays)
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem $BackupDir -Filter "warehouse_backup_*.db" |
    Where-Object { $_.LastWriteTime -lt $cutoffDate } |
    Remove-Item -Force

Write-Host "✅ Backup erstellt: $backupFile"
```

**Windows Task Scheduler für tägliches Backup:**

```powershell
# Task erstellen (täglich um 2:00 Uhr)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Medealis\scripts\backup_database.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName "MedealisBackup" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

### 4.4 Logging & Monitoring

**Erweitern Sie config/logging_config.py:**

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_production_logging():
    """Production-ready Logging mit Rotation"""
    log_dir = Path("C:/Medealis/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Rotating File Handler (max 10MB, 5 Backups)
    file_handler = RotatingFileHandler(
        log_dir / "warehouse.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    return root_logger
```

---

## 5. Wartung & Monitoring

### 5.1 System-Monitoring

**PowerShell Monitoring Script:** `scripts/health_check.ps1`

```powershell
# Health Check für Medealis Warehouse
$ServiceName = "MedealisWarehouse"
$AppUrl = "http://localhost:8501"
$LogFile = "C:\Medealis\logs\health_check.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Add-Content $LogFile
}

# 1. Service Status prüfen
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service.Status -ne "Running") {
    Write-Log "ERROR: Service $ServiceName ist nicht aktiv!"

    # Versuch neu zu starten
    Start-Service $ServiceName
    Start-Sleep -Seconds 10

    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Running") {
        Write-Log "INFO: Service erfolgreich neu gestartet"
    } else {
        Write-Log "CRITICAL: Service konnte nicht gestartet werden!"
        # Optional: Email-Benachrichtigung senden
    }
}

# 2. HTTP Health Check
try {
    $response = Invoke-WebRequest -Uri $AppUrl -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "OK: App antwortet erfolgreich"
    }
} catch {
    Write-Log "ERROR: App antwortet nicht! $($_.Exception.Message)"
}

# 3. Disk Space prüfen
$drive = Get-PSDrive C
$freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
if ($freeSpaceGB -lt 5) {
    Write-Log "WARNING: Nur noch $freeSpaceGB GB frei auf Laufwerk C:"
}

# 4. Datenbank-Größe prüfen
$dbPath = "C:\Medealis\data\warehouse_new.db"
if (Test-Path $dbPath) {
    $dbSizeMB = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
    Write-Log "INFO: Datenbank-Größe: $dbSizeMB MB"
}

Write-Log "Health Check abgeschlossen"
```

**Als Scheduled Task einrichten (alle 15 Minuten):**

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Medealis\scripts\health_check.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName "MedealisHealthCheck" -Action $action -Trigger $trigger
```

### 5.2 Update-Prozess

**Update Script:** `scripts/update_app.ps1`

```powershell
# Anwendungs-Update Script
param(
    [string]$BackupBeforeUpdate = $true
)

$appDir = "C:\Medealis\warehouse"
$serviceName = "MedealisWarehouse"

Write-Host "🔄 Starte Update-Prozess..."

# 1. Backup erstellen
if ($BackupBeforeUpdate) {
    Write-Host "📦 Erstelle Backup..."
    & "C:\Medealis\scripts\backup_database.ps1"
}

# 2. Service stoppen
Write-Host "⏸️  Stoppe Service..."
Stop-Service $serviceName
Start-Sleep -Seconds 5

# 3. Git Pull (oder manuelle Code-Aktualisierung)
Write-Host "⬇️  Lade Updates..."
cd $appDir
git pull origin main

# 4. Dependencies aktualisieren
Write-Host "📚 Aktualisiere Dependencies..."
& "$appDir\venv\Scripts\pip.exe" install -r requirements.txt --upgrade

# 5. Datenbank-Migrationen (falls vorhanden)
# python src/migrations/migrate.py

# 6. Service starten
Write-Host "▶️  Starte Service..."
Start-Service $serviceName
Start-Sleep -Seconds 10

# 7. Health Check
$response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 30 -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Update erfolgreich! App läuft wieder."
} else {
    Write-Host "❌ Update fehlgeschlagen! Bitte manuell prüfen."
}
```

---

## 6. Troubleshooting

### Häufige Probleme und Lösungen

#### Problem: Service startet nicht

```powershell
# Logs prüfen
Get-EventLog -LogName Application -Source MedealisWarehouse -Newest 10

# Service-Status detailliert
nssm status MedealisWarehouse

# Manuell starten zum Testen
cd C:\Medealis\warehouse
.\venv\Scripts\activate
python -m streamlit run src/warehouse/presentation/admin/main_admin_app.py
```

#### Problem: Keine Verbindung möglich

```powershell
# 1. Firewall prüfen
Get-NetFirewallRule -DisplayName "Medealis Warehouse"

# 2. Port prüfen
netstat -ano | findstr :8501

# 3. Von anderem PC testen
Test-NetConnection -ComputerName <server-ip> -Port 8501
```

#### Problem: SharePoint Connection fehlgeschlagen

```powershell
# .env Variablen prüfen
Get-Content C:\Medealis\warehouse\.env | Select-String "SHAREPOINT"

# Test-Script ausführen
cd C:\Medealis\warehouse
.\venv\Scripts\python.exe test_sharepoint_connection.py
```

#### Problem: Datenbank gesperrt

```powershell
# SQLite Locks prüfen
# Alle Verbindungen schließen
Stop-Service MedealisWarehouse

# Datenbank-Integrität prüfen
sqlite3 C:\Medealis\data\warehouse_new.db "PRAGMA integrity_check;"
```

---

## Checkliste: Production Readiness

### Vor Go-Live:

- [ ] Server mit ausreichend Ressourcen bereitgestellt
- [ ] Python 3.11+ installiert
- [ ] Anwendung deployed und getestet
- [ ] Windows Service konfiguriert und Auto-Start aktiviert
- [ ] Firewall-Regeln erstellt
- [ ] .env Datei mit Production-Werten konfiguriert
- [ ] Authentifizierung aktiviert (falls erforderlich)
- [ ] HTTPS eingerichtet (falls Internet-Zugriff)
- [ ] Automatische Backups konfiguriert
- [ ] Health Checks eingerichtet
- [ ] Logging konfiguriert
- [ ] Update-Prozess dokumentiert
- [ ] Team geschult (Admin-Zugang, Troubleshooting)
- [ ] Dokumentation erstellt
- [ ] Notfall-Kontakte definiert

### Nach Go-Live:

- [ ] Monitoring aktiv
- [ ] Erste Backups erfolgreich
- [ ] User-Feedback sammeln
- [ ] Performance-Metriken tracken
- [ ] Regelmäßige Updates planen

---

## Kontakt & Support

Bei Fragen zur Deployment:
1. Dokumentation prüfen
2. Logs analysieren (C:\Medealis\logs)
3. GitHub Issues erstellen
4. IT-Administrator kontaktieren

---

**Erstellt für:** Medealis Warehouse Management System v2.0
**Datum:** 2025
**Status:** Production Ready
