@echo off
echo ========================================
echo  Medealis Admin App
echo ========================================
echo.
echo Starte Admin App auf Port 8501...
echo.

REM Stelle sicher, dass wir im richtigen Verzeichnis sind
cd /d "%~dp0"

echo.
echo Erreichbar unter: http://localhost:8501
echo.
echo Zum Beenden: CTRL+C druecken
echo.
echo ========================================
echo.

REM Aktiviere Virtual Environment und starte Streamlit mit .env loading
call .venv\Scripts\activate.bat
python start_app_with_env.py src\warehouse\presentation\admin\main_admin_app.py --server.port=8501 --server.address=0.0.0.0

pause
