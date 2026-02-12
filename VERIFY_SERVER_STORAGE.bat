@echo off
REM ========================================
REM  VERIFIZIERUNG: Server-Speicherung
REM ========================================

echo.
echo ========================================
echo  Medealis - Server-Speicherung pruefen
echo ========================================
echo.

REM Wechsel ins richtige Verzeichnis
cd /d "%~dp0"

REM Aktiviere Virtual Environment
call .venv\Scripts\activate.bat

echo.
echo Pruefe Server-Pfad Konfiguration...
echo.

REM Zeige aktuelle .env Einstellungen
echo --- .env Einstellungen ---
findstr "USE_SERVER_STORAGE" .env
findstr "USE_CENTRALIZED_STORAGE" .env
echo.

echo --- Datenbank-Pfad Test ---
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from config.settings import Settings; db_path = Settings.get_database_path(); print(f'[OK] Datenbank: {db_path}'); print(f'[OK] Verzeichnis existiert: {db_path.parent.exists()}')"

echo.
echo --- Dokument-Pfad Test ---
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from warehouse.application.services.document_storage.path_resolver import PathResolver; resolver = PathResolver(); print(f'[OK] Server Storage Path: {resolver.server_storage_path}'); print(f'[OK] Existiert: {resolver.server_storage_path.exists()}')"

echo.
echo ========================================
echo  Verifizierung abgeschlossen!
echo ========================================
echo.

pause
