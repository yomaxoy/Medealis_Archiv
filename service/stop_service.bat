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

python medealis_service.py stop

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
