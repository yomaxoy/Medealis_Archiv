@echo off
REM =============================================================================
REM Medealis Warehouse Service - Uninstallation Script
REM =============================================================================

echo ========================================
echo  Medealis Warehouse Service Deinstallation
echo ========================================
echo.

REM Prüfe Administrator-Rechte
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Dieses Script muss als Administrator ausgefuehrt werden!
    pause
    exit /b 1
)

REM Wechsle zum Service-Verzeichnis
cd /d "%~dp0"

echo WARNUNG: Der Medealis Service wird deinstalliert!
echo.
set /p confirm="Fortfahren? (J/N): "

if /i not "%confirm%"=="J" (
    echo Abgebrochen.
    pause
    exit /b 0
)

REM Setze Pfad zur virtuellen Umgebung
set VENV_PYTHON=%~dp0..\.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden!
    echo Erwarteter Pfad: %VENV_PYTHON%
    pause
    exit /b 1
)

echo.
echo [1/3] Stoppe Service...
"%VENV_PYTHON%" medealis_service.py stop 2>nul
timeout /t 3 /nobreak >nul

echo [2/3] Deinstalliere Service...
"%VENV_PYTHON%" medealis_service.py remove

echo [3/3] Entferne Firewall-Regel...
netsh advfirewall firewall delete rule name="Medealis Warehouse - Streamlit" >nul 2>&1

echo.
echo ========================================
echo  Deinstallation abgeschlossen!
echo ========================================
echo.
echo Der Service wurde entfernt.
echo Die Datenbank und Konfiguration bleiben erhalten.
echo.
pause
