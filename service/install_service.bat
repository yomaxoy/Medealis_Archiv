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

echo [1/5] Pruefe Python-Installation...
python --version
if %errorLevel% neq 0 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH!
    pause
    exit /b 1
)

echo [2/5] Pruefe pywin32-Installation...
python -c "import win32serviceutil" 2>nul
if %errorLevel% neq 0 (
    echo pywin32 nicht gefunden - installiere...
    pip install pywin32
    if %errorLevel% neq 0 (
        echo FEHLER: pywin32-Installation fehlgeschlagen!
        pause
        exit /b 1
    )

    REM Registriere pywin32-DLLs
    python -c "import win32api; print(win32api.__file__)" >temp_path.txt
    set /p PYWIN32_PATH=<temp_path.txt
    for %%i in ("%PYWIN32_PATH%") do set PYWIN32_DIR=%%~dpi

    echo Registriere pywin32-DLLs...
    python "%PYWIN32_DIR%..\scripts\pywin32_postinstall.py" -install
    del temp_path.txt
)

echo [3/5] Stoppe existierenden Service (falls vorhanden)...
python medealis_service.py stop 2>nul
timeout /t 2 /nobreak >nul

echo [4/5] Installiere Medealis Service...
python medealis_service.py install
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
echo Zugriff:      http://localhost:8501
echo              http://%COMPUTERNAME%:8501
echo              http://IP-ADRESSE:8501
echo.
echo Naechste Schritte:
echo   1. Service starten:  start_service.bat
echo   2. Firewall oeffnen: firewall_config.bat
echo   3. Im Browser testen
echo.
pause
