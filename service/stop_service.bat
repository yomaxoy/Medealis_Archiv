@echo off
REM =============================================================================
REM Medealis Warehouse Service - Stop Script
REM =============================================================================

echo Stoppe Medealis Warehouse Service...

REM Prüfe Administrator-Rechte
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Dieses Script muss als Administrator ausgefuehrt werden!
    pause
    exit /b 1
)

REM Wechsle zum Service-Verzeichnis
cd /d "%~dp0"

REM Setze Pfad zur virtuellen Umgebung
set VENV_PYTHON=%~dp0..\.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden!
    echo Erwarteter Pfad: %VENV_PYTHON%
    pause
    exit /b 1
)

"%VENV_PYTHON%" medealis_service.py stop

if %errorLevel% equ 0 (
    echo.
    echo Service erfolgreich gestoppt!
    echo.
) else (
    echo.
    echo FEHLER: Service konnte nicht gestoppt werden!
    echo.
)

pause
