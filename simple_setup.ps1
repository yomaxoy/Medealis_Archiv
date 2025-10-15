# ========================================
# Medealis Warehouse - Einfaches Setup
# ========================================

param(
    [string]$InstallPath = "C:\Medealis",
    [int]$Port = 8501
)

Write-Host "==================================="
Write-Host "Medealis Warehouse Setup"
Write-Host "==================================="
Write-Host ""

# Admin-Rechte prüfen
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "FEHLER: Dieses Script muss als Administrator ausgefuehrt werden!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Administrator-Rechte" -ForegroundColor Green

# Python prüfen
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "[OK] Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Python nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte Python 3.11+ installieren: https://www.python.org/downloads/"
    exit 1
}

# Installation-Pfad erstellen
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    Write-Host "[OK] Installation-Ordner erstellt: $InstallPath" -ForegroundColor Green
}

$ProjectPath = Join-Path $InstallPath "neu_Medealis_Archiv"

# Projekt kopieren
Write-Host ""
Write-Host "Kopiere Projekt..." -ForegroundColor Cyan
$CurrentPath = $PSScriptRoot

if ($CurrentPath -ne $ProjectPath) {
    if (-not (Test-Path $ProjectPath)) {
        New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
    }

    # Robocopy
    $excludeDirs = @('.git', '__pycache__', 'venv', '.pytest_cache')
    robocopy $CurrentPath $ProjectPath /E /XD $excludeDirs /NFL /NDL /NJH /NJS /nc /ns /np
    Write-Host "[OK] Projekt kopiert" -ForegroundColor Green
} else {
    Write-Host "[INFO] Projekt ist bereits am Zielort" -ForegroundColor Yellow
}

# Virtual Environment
Write-Host ""
Write-Host "Richte Virtual Environment ein..." -ForegroundColor Cyan
$VenvPath = Join-Path $ProjectPath "venv"

if (-not (Test-Path $VenvPath)) {
    & python -m venv $VenvPath
    Write-Host "[OK] Virtual Environment erstellt" -ForegroundColor Green
}

$PipExe = Join-Path $VenvPath "Scripts\pip.exe"
$StreamlitExe = Join-Path $VenvPath "Scripts\streamlit.exe"

# Dependencies installieren
Write-Host ""
Write-Host "Installiere Dependencies (kann einige Minuten dauern)..." -ForegroundColor Cyan
& $PipExe install --upgrade pip --quiet
& $PipExe install -r (Join-Path $ProjectPath "requirements.txt") --quiet
Write-Host "[OK] Dependencies installiert" -ForegroundColor Green

# .env Datei
Write-Host ""
Write-Host "Konfiguriere .env Datei..." -ForegroundColor Cyan
$EnvPath = Join-Path $ProjectPath ".env"
if (-not (Test-Path $EnvPath)) {
    $EnvExamplePath = Join-Path $ProjectPath ".env.example"
    if (Test-Path $EnvExamplePath) {
        Copy-Item $EnvExamplePath $EnvPath
    } else {
        # Default .env
        @"
ENVIRONMENT=production
DEBUG=false
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
USE_SHAREPOINT=false
"@ | Out-File -FilePath $EnvPath -Encoding UTF8
    }
    Write-Host "[OK] .env Datei erstellt: $EnvPath" -ForegroundColor Green
    Write-Host "[WICHTIG] Bitte API-Keys in .env eintragen!" -ForegroundColor Yellow
}

# Firewall
Write-Host ""
Write-Host "Konfiguriere Firewall..." -ForegroundColor Cyan
$firewallRule = Get-NetFirewallRule -DisplayName "Medealis Warehouse" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    try {
        New-NetFirewallRule -DisplayName "Medealis Warehouse" `
            -Direction Inbound `
            -LocalPort $Port `
            -Protocol TCP `
            -Action Allow `
            -Profile Domain,Private | Out-Null
        Write-Host "[OK] Firewall-Regel erstellt" -ForegroundColor Green
    } catch {
        Write-Host "[WARNUNG] Firewall-Regel konnte nicht erstellt werden" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Firewall-Regel existiert bereits" -ForegroundColor Yellow
}

# Netzwerk-Info
Write-Host ""
Write-Host "==================================="
Write-Host "Installation abgeschlossen!" -ForegroundColor Green
Write-Host "==================================="
Write-Host ""
Write-Host "Installation-Pfad: $ProjectPath"
Write-Host "Konfiguration: $EnvPath"
Write-Host ""
Write-Host "Naechste Schritte:"
Write-Host "1. .env Datei bearbeiten:"
Write-Host "   notepad $EnvPath"
Write-Host ""
Write-Host "2. App manuell starten:"
Write-Host "   cd $ProjectPath"
Write-Host "   .\venv\Scripts\activate"
Write-Host "   streamlit run src\warehouse\presentation\admin\main_admin_app.py --server.port=$Port"
Write-Host ""
Write-Host "3. Im Browser oeffnen:"
Write-Host "   http://localhost:$Port"
Write-Host ""

# IP-Adressen anzeigen
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -ExpandProperty IPAddress
if ($ipAddresses) {
    Write-Host "Von anderen PCs erreichbar unter:"
    foreach ($ip in $ipAddresses) {
        Write-Host "   http://${ip}:$Port"
    }
}

Write-Host ""
Write-Host "Fuer Windows-Service Installation siehe: docs\guides\DEPLOYMENT_GUIDE.md"
Write-Host ""
