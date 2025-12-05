@echo off
setlocal enabledelayedexpansion
REM ========================================
REM Medealis Warehouse - Automatischer Start
REM ========================================
REM Dieses Skript startet beide Apps automatisch

cd /d "%~dp0"

REM Tesseract-OCR zum PATH hinzufuegen
set PATH=%PATH%;C:\Program Files\Tesseract-OCR

REM Umgebungsvariablen aus .env laden
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "line=%%a"
    REM Skip comments and empty lines
    if not "!line:~0,1!"=="#" if not "%%a"=="" (
        set "%%a=%%b"
    )
)

echo.
echo ========================================
echo  Starte Medealis Warehouse Apps
echo ========================================
echo.

REM Admin App starten (Port 8501)
echo [1/2] Starte Admin App auf Port 8501...
start "Medealis Admin" /MIN cmd /c ".venv\Scripts\streamlit.exe run src\warehouse\presentation\admin\main_admin_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"

REM Kurz warten
timeout /t 3 /nobreak >nul

REM User App starten (Port 8502)
echo [2/2] Starte User App auf Port 8502...
start "Medealis User" /MIN cmd /c ".venv\Scripts\streamlit.exe run src\warehouse\presentation\user\main_user_app.py --server.port=8502 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"

echo.
echo ========================================
echo  Apps erfolgreich gestartet!
echo ========================================
echo.
echo Zugriff:
echo   Admin App: http://localhost:8501
echo   User App:  http://localhost:8502
echo.
echo   Im Netzwerk:
echo   Admin App: http://%COMPUTERNAME%:8501
echo   User App:  http://%COMPUTERNAME%:8502
echo.
echo Die Apps laufen jetzt im Hintergrund.
echo Zum Beenden: stop_medealis_apps.bat
echo.
pause
