@echo off
REM =============================================================================
REM Medealis Warehouse Service - Installation Script
REM =============================================================================
REM
REM Dieses Script installiert den Medealis Warehouse Service als Windows Service.
REM Der Service startet automatisch beim Windows-Start.
REM
REM Voraussetzungen:
REM   - Python 3.8+ installiert
REM   - pywin32 installiert (pip install pywin32)
REM   - Ausführung als Administrator erforderlich
REM
REM =============================================================================

echo ========================================
echo  Medealis Warehouse Service Installation
echo ========================================
echo.

REM Prüfe Administrator-Rechte
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Dieses Script muss als Administrator ausgefuehrt werden!
    echo Rechtsklick -^> "Als Administrator ausfuehren"
    echo.
    pause
    exit /b 1
)

REM Wechsle zum Service-Verzeichnis
cd /d "%~dp0"

REM Setze Pfad zur virtuellen Umgebung
set VENV_PYTHON=%~dp0..\.venv\Scripts\python.exe

echo [1/5] Pruefe Python-Installation (.venv)...
if not exist "%VENV_PYTHON%" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden!
    echo Erwarteter Pfad: %VENV_PYTHON%
    echo.
    echo Bitte zuerst die virtuelle Umgebung erstellen:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

"%VENV_PYTHON%" --version
if %errorLevel% neq 0 (
    echo FEHLER: Python konnte nicht ausgefuehrt werden!
    pause
    exit /b 1
)

echo [2/5] Pruefe pywin32-Installation...
"%VENV_PYTHON%" -c "import win32serviceutil" 2>nul
if %errorLevel% neq 0 (
    echo FEHLER: pywin32 ist nicht in der virtuellen Umgebung installiert!
    echo.
    echo Bitte installieren mit:
    echo   .venv\Scripts\pip install pywin32
    echo   .venv\Scripts\python .venv\Scripts\pywin32_postinstall.py -install
    pause
    exit /b 1
)

echo [3/5] Stoppe existierenden Service (falls vorhanden)...
"%VENV_PYTHON%" medealis_service.py stop 2>nul
timeout /t 2 /nobreak >nul

echo [4/5] Installiere Medealis Service...
"%VENV_PYTHON%" medealis_service.py install
if %errorLevel% neq 0 (
    echo FEHLER: Service-Installation fehlgeschlagen!
    pause
    exit /b 1
)

echo [5/5] Konfiguriere Autostart...
sc config MedealisWarehouse start= auto
if %errorLevel% neq 0 (
    echo WARNUNG: Autostart-Konfiguration fehlgeschlagen!
)

echo.
echo ========================================
echo  Installation erfolgreich!
echo ========================================
echo.
echo Service-Name: MedealisWarehouse
echo.
echo Zugriff:
echo   Admin App: http://localhost:8501
echo   User App:  http://localhost:8502
echo.
echo   Im Netzwerk:
echo   Admin App: http://%COMPUTERNAME%:8501
echo   User App:  http://%COMPUTERNAME%:8502
echo.
echo Naechste Schritte:
echo   1. Service starten:  start_service.bat
echo   2. Firewall oeffnen: firewall_config.bat
echo   3. Im Browser testen
echo.
pause
