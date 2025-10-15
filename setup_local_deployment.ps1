# ========================================
# Medealis Warehouse - Automatisches Setup
# Lokales Deployment auf Windows-PC/Server
# ========================================
# Version: 1.0
# Datum: 2025
# Autor: Medealis Team

param(
    [string]$InstallPath = "C:\Medealis",
    [string]$ServiceName = "MedealisWarehouse",
    [int]$Port = 8501,
    [switch]$SkipService,
    [switch]$SkipFirewall,
    [switch]$Help
)

# Farben für Output
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Step { Write-Host "`n📌 $args" -ForegroundColor Magenta }

# Help anzeigen
if ($Help) {
    Write-Host @"
Medealis Warehouse - Automatisches Setup
========================================

Verwendung:
  .\setup_local_deployment.ps1 [Optionen]

Optionen:
  -InstallPath <Pfad>    Installation-Pfad (Standard: C:\Medealis)
  -ServiceName <Name>    Windows-Service Name (Standard: MedealisWarehouse)
  -Port <Port>          Port für Streamlit (Standard: 8501)
  -SkipService          Überspringt Service-Installation
  -SkipFirewall         Überspringt Firewall-Konfiguration
  -Help                 Zeigt diese Hilfe

Beispiele:
  .\setup_local_deployment.ps1
  .\setup_local_deployment.ps1 -InstallPath "D:\Apps\Medealis"
  .\setup_local_deployment.ps1 -Port 8502 -SkipService

WICHTIG: Als Administrator ausführen!
"@
    exit 0
}

# ========================================
# Pre-Flight Checks
# ========================================

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║   Medealis Warehouse Management System - Setup            ║
║   Lokales Deployment auf Windows                          ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Step "Pre-Flight Checks"

# Admin-Rechte prüfen
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "Dieses Script muss als Administrator ausgeführt werden!"
    Write-Info "Rechtsklick auf PowerShell → 'Als Administrator ausführen'"
    exit 1
}
Write-Success "Administrator-Rechte: OK"

# Python prüfen
$pythonVersion = $null
try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 10) {
            Write-Success "Python gefunden: $pythonVersion"
        } else {
            Write-Warning "Python $pythonVersion ist zu alt (benötigt: 3.10+)"
            $install = Read-Host "Python 3.11 jetzt installieren? (y/n)"
            if ($install -eq 'y') {
                Write-Info "Öffne Python Download-Seite..."
                Start-Process "https://www.python.org/downloads/"
                Write-Info "Bitte installieren Sie Python und führen Sie das Script erneut aus."
                exit 1
            } else {
                exit 1
            }
        }
    }
} catch {
    Write-Error "Python nicht gefunden!"
    $install = Read-Host "Python 3.11 jetzt installieren? (y/n)"
    if ($install -eq 'y') {
        Write-Info "Öffne Python Download-Seite..."
        Start-Process "https://www.python.org/downloads/"
        Write-Info "WICHTIG: Bei Installation 'Add Python to PATH' aktivieren!"
        Write-Info "Nach Installation PowerShell NEU starten und Script erneut ausführen."
        exit 1
    } else {
        exit 1
    }
}

# Git prüfen (optional)
try {
    $gitVersion = & git --version 2>&1
    Write-Success "Git gefunden: $gitVersion"
} catch {
    Write-Warning "Git nicht gefunden (optional, für Updates nützlich)"
}

# ========================================
# Installation
# ========================================

Write-Step "Installation vorbereiten"

# Installation-Pfad erstellen
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    Write-Success "Installation-Ordner erstellt: $InstallPath"
} else {
    Write-Info "Installation-Ordner existiert bereits: $InstallPath"
}

# Projekt-Pfad
$ProjectPath = Join-Path $InstallPath "neu_Medealis_Archiv"

# Prüfen ob Projekt bereits existiert
if (Test-Path $ProjectPath) {
    Write-Warning "Projekt existiert bereits: $ProjectPath"
    $overwrite = Read-Host "Fortfahren und aktualisieren? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Info "Installation abgebrochen."
        exit 0
    }
}

# Aktuelles Projekt kopieren
Write-Step "Projekt kopieren"
$CurrentPath = $PSScriptRoot
if ($CurrentPath -ne $ProjectPath) {
    Write-Info "Kopiere Projekt von: $CurrentPath"
    Write-Info "Nach: $ProjectPath"

    # Kopieren (ohne .git, __pycache__, etc.)
    $excludeDirs = @('.git', '__pycache__', 'venv', '.pytest_cache', '.mypy_cache', 'node_modules')
    $excludeFiles = @('*.pyc', '*.pyo', '*.pyd', '.DS_Store', 'Thumbs.db')

    if (-not (Test-Path $ProjectPath)) {
        New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
    }

    # Robocopy für effizientes Kopieren
    $robocopyArgs = @(
        $CurrentPath,
        $ProjectPath,
        '/E',  # Subdirectories
        '/XD', ($excludeDirs -join ' '),  # Exclude dirs
        '/XF', ($excludeFiles -join ' '),  # Exclude files
        '/NFL', '/NDL', '/NJH', '/NJS', '/nc', '/ns', '/np'  # Minimal output
    )

    $result = & robocopy @robocopyArgs 2>&1
    if ($LASTEXITCODE -le 7) {  # Robocopy exit codes 0-7 are success
        Write-Success "Projekt kopiert"
    } else {
        Write-Error "Fehler beim Kopieren: $result"
        exit 1
    }
} else {
    Write-Success "Projekt ist bereits am Zielort"
}

# ========================================
# Virtual Environment
# ========================================

Write-Step "Virtual Environment einrichten"

$VenvPath = Join-Path $ProjectPath "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$PipExe = Join-Path $VenvPath "Scripts\pip.exe"
$StreamlitExe = Join-Path $VenvPath "Scripts\streamlit.exe"

if (-not (Test-Path $VenvPath)) {
    Write-Info "Erstelle Virtual Environment..."
    & python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Virtual Environment konnte nicht erstellt werden"
        exit 1
    }
    Write-Success "Virtual Environment erstellt"
} else {
    Write-Info "Virtual Environment existiert bereits"
}

# Pip upgraden
Write-Info "Aktualisiere pip..."
& $PipExe install --upgrade pip --quiet
Write-Success "Pip aktualisiert"

# Dependencies installieren
Write-Step "Dependencies installieren (kann einige Minuten dauern)"
$RequirementsPath = Join-Path $ProjectPath "requirements.txt"
if (Test-Path $RequirementsPath) {
    Write-Info "Installiere Pakete aus requirements.txt..."
    & $PipExe install -r $RequirementsPath --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Fehler bei Installation der Dependencies"
        exit 1
    }
    Write-Success "Alle Dependencies installiert"
} else {
    Write-Warning "requirements.txt nicht gefunden: $RequirementsPath"
}

# ========================================
# Konfiguration
# ========================================

Write-Step "Konfiguration erstellen"

$EnvExamplePath = Join-Path $ProjectPath ".env.example"
$EnvPath = Join-Path $ProjectPath ".env"

if (-not (Test-Path $EnvPath)) {
    if (Test-Path $EnvExamplePath) {
        Copy-Item $EnvExamplePath $EnvPath
        Write-Success ".env Datei erstellt"
        Write-Warning "WICHTIG: Bitte .env Datei bearbeiten und API-Keys eintragen!"
        Write-Info "Pfad: $EnvPath"
    } else {
        # Default .env erstellen
        $defaultEnv = @"
# Environment
ENVIRONMENT=production
DEBUG=false

# API Keys (optional)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# SharePoint (optional)
USE_SHAREPOINT=false
SHAREPOINT_SITE_URL=
SHAREPOINT_CLIENT_ID=
SHAREPOINT_CLIENT_SECRET=
SHAREPOINT_TENANT_ID=
"@
        $defaultEnv | Out-File -FilePath $EnvPath -Encoding UTF8
        Write-Success ".env Datei erstellt (mit Defaults)"
    }
} else {
    Write-Info ".env Datei existiert bereits"
}

# Verzeichnisse erstellen
Write-Info "Erstelle Verzeichnisse..."
$Directories = @(
    (Join-Path $InstallPath "logs"),
    (Join-Path $InstallPath "backups"),
    (Join-Path $InstallPath "scripts")
)

foreach ($dir in $Directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Success "Verzeichnisse erstellt"

# ========================================
# Test-Start
# ========================================

Write-Step "Funktionstest"

Write-Info "Teste Streamlit Installation..."
$testResult = & $StreamlitExe --version 2>&1
if ($testResult -match "Streamlit") {
    Write-Success "Streamlit funktioniert: $testResult"
} else {
    Write-Error "Streamlit Test fehlgeschlagen"
    exit 1
}

# App-Pfad finden
$AppPath = Join-Path $ProjectPath "src\warehouse\presentation\admin\main_admin_app.py"
if (-not (Test-Path $AppPath)) {
    # Fallback: nach streamlit_app.py suchen
    $AppPath = Join-Path $ProjectPath "src\streamlit_app.py"
    if (-not (Test-Path $AppPath)) {
        Write-Error "Streamlit App nicht gefunden!"
        Write-Info "Erwartet: src/warehouse/presentation/admin/main_admin_app.py"
        Write-Info "Oder: src/streamlit_app.py"
        exit 1
    }
}
Write-Success "App gefunden: $AppPath"

# ========================================
# Firewall
# ========================================

if (-not $SkipFirewall) {
    Write-Step "Firewall konfigurieren"

    $firewallRule = Get-NetFirewallRule -DisplayName "Medealis Warehouse" -ErrorAction SilentlyContinue
    if ($firewallRule) {
        Write-Info "Firewall-Regel existiert bereits"
    } else {
        Write-Info "Erstelle Firewall-Regel für Port $Port..."
        try {
            New-NetFirewallRule -DisplayName "Medealis Warehouse" `
                -Direction Inbound `
                -LocalPort $Port `
                -Protocol TCP `
                -Action Allow `
                -Profile Domain,Private `
                -ErrorAction Stop | Out-Null
            Write-Success "Firewall-Regel erstellt"
        } catch {
            Write-Warning "Firewall-Regel konnte nicht erstellt werden: $_"
        }
    }
} else {
    Write-Info "Firewall-Konfiguration übersprungen"
}

# ========================================
# Windows Service (NSSM)
# ========================================

if (-not $SkipService) {
    Write-Step "Windows-Service einrichten"

    # NSSM prüfen/installieren
    $nssmPath = $null
    $nssmLocations = @(
        "C:\Tools\nssm\win64\nssm.exe",
        "C:\nssm\win64\nssm.exe",
        "$env:ProgramFiles\nssm\win64\nssm.exe",
        (Join-Path $InstallPath "nssm\win64\nssm.exe")
    )

    foreach ($location in $nssmLocations) {
        if (Test-Path $location) {
            $nssmPath = $location
            break
        }
    }

    if (-not $nssmPath) {
        Write-Warning "NSSM nicht gefunden"
        Write-Info "NSSM wird für Windows-Service benötigt"
        $download = Read-Host "NSSM jetzt herunterladen und installieren? (y/n)"

        if ($download -eq 'y') {
            Write-Info "Öffne NSSM Download-Seite..."
            Start-Process "https://nssm.cc/download"
            Write-Info "Bitte NSSM herunterladen, entpacken nach C:\Tools\nssm"
            Write-Info "Dann Script erneut ausführen"
            exit 0
        } else {
            Write-Warning "Service-Installation übersprungen"
            Write-Info "App kann manuell gestartet werden mit:"
            Write-Info "  cd $ProjectPath"
            Write-Info "  .\venv\Scripts\activate"
            Write-Info "  streamlit run $AppPath --server.port=$Port"
        }
    } else {
        Write-Success "NSSM gefunden: $nssmPath"

        # Prüfen ob Service bereits existiert
        $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-Warning "Service '$ServiceName' existiert bereits"
            $reinstall = Read-Host "Service neu installieren? (y/n)"
            if ($reinstall -eq 'y') {
                Write-Info "Stoppe und entferne existierenden Service..."
                & $nssmPath stop $ServiceName
                Start-Sleep -Seconds 2
                & $nssmPath remove $ServiceName confirm
                Write-Success "Service entfernt"
            } else {
                Write-Info "Service-Installation übersprungen"
                $nssmPath = $null  # Skip installation
            }
        }

        if ($nssmPath -and -not $existingService) {
            Write-Info "Installiere Windows-Service..."

            # Service installieren
            & $nssmPath install $ServiceName $StreamlitExe
            & $nssmPath set $ServiceName AppDirectory $ProjectPath
            & $nssmPath set $ServiceName AppParameters "run `"$AppPath`" --server.port=$Port --server.address=0.0.0.0 --server.headless=true"
            & $nssmPath set $ServiceName DisplayName "Medealis Warehouse System"
            & $nssmPath set $ServiceName Description "Warehouse Management System für Medealis"
            & $nssmPath set $ServiceName Start SERVICE_AUTO_START

            # Service starten
            Write-Info "Starte Service..."
            & $nssmPath start $ServiceName
            Start-Sleep -Seconds 5

            $status = & $nssmPath status $ServiceName
            if ($status -match "SERVICE_RUNNING") {
                Write-Success "Service erfolgreich gestartet!"
            } else {
                Write-Warning "Service Status: $status"
            }
        }
    }
} else {
    Write-Info "Service-Installation übersprungen"
}

# ========================================
# Backup & Health Check Scripts
# ========================================

Write-Step "Wartungs-Scripts erstellen"

# Backup Script
$BackupScript = Join-Path $InstallPath "scripts\backup.ps1"
$BackupContent = @"
# Automatisches Datenbank-Backup
`$SourceDB = "`$env:USERPROFILE\.medealis\warehouse_new.db"
`$BackupDir = "$InstallPath\backups"
`$RetentionDays = 30

if (-not (Test-Path `$BackupDir)) {
    New-Item -ItemType Directory -Path `$BackupDir -Force | Out-Null
}

`$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
`$backupFile = Join-Path `$BackupDir "warehouse_backup_`$timestamp.db"

if (Test-Path `$SourceDB) {
    Copy-Item `$SourceDB `$backupFile -Force
    Write-Host "✅ Backup erstellt: `$backupFile"

    # Alte Backups löschen
    `$cutoffDate = (Get-Date).AddDays(-`$RetentionDays)
    Get-ChildItem `$BackupDir -Filter "warehouse_backup_*.db" |
        Where-Object { `$_.LastWriteTime -lt `$cutoffDate } |
        Remove-Item -Force
} else {
    Write-Host "⚠️ Datenbank nicht gefunden: `$SourceDB"
}
"@
$BackupContent | Out-File -FilePath $BackupScript -Encoding UTF8
Write-Success "Backup-Script erstellt: $BackupScript"

# Health Check Script
$HealthCheckScript = Join-Path $InstallPath "scripts\health_check.ps1"
$HealthCheckContent = @"
# Health Check für Medealis Warehouse
`$AppUrl = "http://localhost:$Port"
`$LogFile = "$InstallPath\logs\health_check.log"

function Write-Log {
    param([string]`$Message)
    `$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "`$timestamp - `$Message" | Add-Content `$LogFile
}

try {
    `$response = Invoke-WebRequest -Uri `$AppUrl -TimeoutSec 10 -UseBasicParsing
    if (`$response.StatusCode -eq 200) {
        Write-Log "OK: App läuft"
    }
} catch {
    Write-Log "ERROR: App antwortet nicht - `$_"

    # Versuche Service neu zu starten
    Restart-Service $ServiceName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 15

    try {
        `$response = Invoke-WebRequest -Uri `$AppUrl -TimeoutSec 10 -UseBasicParsing
        Write-Log "INFO: Service erfolgreich neu gestartet"
    } catch {
        Write-Log "CRITICAL: Neustart fehlgeschlagen!"
    }
}
"@
$HealthCheckContent | Out-File -FilePath $HealthCheckScript -Encoding UTF8
Write-Success "Health-Check-Script erstellt: $HealthCheckScript"

# ========================================
# Netzwerk-Info
# ========================================

Write-Step "Netzwerk-Information"

# IP-Adresse ermitteln
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -ne 'WellKnown' } |
    Select-Object -ExpandProperty IPAddress

if ($ipAddresses) {
    Write-Success "IP-Adressen dieses PCs:"
    foreach ($ip in $ipAddresses) {
        Write-Host "  http://${ip}:$Port" -ForegroundColor Green
    }
} else {
    Write-Warning "Keine Netzwerk-IP gefunden"
}

$computerName = $env:COMPUTERNAME
Write-Info "Hostname: http://${computerName}:$Port"

# ========================================
# Abschluss
# ========================================

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║   Installation abgeschlossen! ✅                           ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Host "📍 Installation-Pfad: $ProjectPath" -ForegroundColor Cyan
Write-Host "📍 Konfiguration: $EnvPath" -ForegroundColor Cyan
Write-Host "📍 Logs: $InstallPath\logs" -ForegroundColor Cyan
Write-Host "📍 Backups: $InstallPath\backups" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 App-URLs:" -ForegroundColor Yellow
Write-Host "   Lokal:    http://localhost:$Port" -ForegroundColor Green
Write-Host "   Hostname: http://${computerName}:$Port" -ForegroundColor Green
foreach ($ip in $ipAddresses) {
    Write-Host "   Netzwerk: http://${ip}:$Port" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Nächste Schritte:" -ForegroundColor Yellow
Write-Host "   1. .env Datei bearbeiten (API-Keys eintragen):" -ForegroundColor White
Write-Host "      notepad $EnvPath" -ForegroundColor Gray
Write-Host "   2. Im Browser öffnen: http://localhost:$Port" -ForegroundColor White
Write-Host "   3. Von anderem PC testen: http://${computerName}:$Port" -ForegroundColor White
Write-Host ""

if (-not $SkipService) {
    Write-Host "🔧 Service-Befehle:" -ForegroundColor Yellow
    Write-Host "   Status:    nssm status $ServiceName" -ForegroundColor Gray
    Write-Host "   Stoppen:   nssm stop $ServiceName" -ForegroundColor Gray
    Write-Host "   Starten:   nssm start $ServiceName" -ForegroundColor Gray
    Write-Host "   Neustart:  nssm restart $ServiceName" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "📚 Dokumentation: $ProjectPath\LOCAL_PC_DEPLOYMENT.md" -ForegroundColor Cyan
Write-Host ""

# Browser öffnen?
$openBrowser = Read-Host "Browser öffnen und App testen? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:$Port"
}

Write-Host ""
Write-Host "Setup abgeschlossen! 🎉" -ForegroundColor Green
