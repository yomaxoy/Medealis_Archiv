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

python medealis_service.py start

if %errorLevel% equ 0 (
    echo.
    echo Service erfolgreich gestartet!
    echo.
    echo Zugriff ueber:
    echo   http://localhost:8501
    echo   http://%COMPUTERNAME%:8501
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
