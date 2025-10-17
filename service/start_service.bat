@echo off
REM =============================================================================
REM Medealis Warehouse Service - Start Script
REM =============================================================================

echo Starte Medealis Warehouse Service...

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

"%VENV_PYTHON%" medealis_service.py start

if %errorLevel% equ 0 (
    echo.
    echo Service erfolgreich gestartet!
    echo.
    echo Zugriff ueber:
    echo   Admin App: http://localhost:8501
    echo   User App:  http://localhost:8502
    echo.
    echo   Im Netzwerk: http://%COMPUTERNAME%:8501 (Admin)
    echo                http://%COMPUTERNAME%:8502 (User)
    echo.
    echo Status pruefen: status_service.bat
    echo.
) else (
    echo.
    echo FEHLER: Service konnte nicht gestartet werden!
    echo.
    echo Pruefe:
    echo   1. Service installiert? (install_service.bat)
    echo   2. Event Viewer fuer Details
    echo.
)

pause
