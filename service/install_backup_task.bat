@echo off
REM =============================================================================
REM Medealis Warehouse - Backup Task Installation
REM =============================================================================

echo ========================================
echo  Medealis - Backup Task Installation
echo ========================================
echo.

REM Prüfe Administrator-Rechte
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Dieses Script muss als Administrator ausgefuehrt werden!
    pause
    exit /b 1
)

echo Generiere Task-Definition...
python backup_database.py --install

echo.
echo Erstelle Backup-Task im Task Scheduler...

REM Lösche existierenden Task falls vorhanden
schtasks /Delete /TN "MedealisWarehouseBackup" /F >nul 2>&1

REM Erstelle neuen Task
schtasks /Create /XML "backup_task.xml" /TN "MedealisWarehouseBackup"

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo  Backup-Task erfolgreich installiert!
    echo ========================================
    echo.
    echo Task-Name:     MedealisWarehouseBackup
    echo Zeitplan:      Taeglich um 02:00 Uhr
    echo Aufbewahrung:  30 Tage
    echo.
    echo Manuelles Backup: backup_now.bat
    echo Backups anzeigen: python backup_database.py --list
    echo.
) else (
    echo.
    echo FEHLER: Task-Installation fehlgeschlagen!
    echo.
)

pause
