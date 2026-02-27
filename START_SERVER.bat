@echo off
echo ================================================================================
echo MEDEALIS ARCHIV - SERVER STARTEN
echo ================================================================================
echo.

cd /d "%~dp0"

echo Starte Streamlit Server...
echo.
echo Die App wird verfuegbar sein unter:
echo   - Lokal:    http://localhost:8502
echo   - Netzwerk: http://%COMPUTERNAME%:8502
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo   - IP:       http://%%a:8502
)
echo.
echo Druecken Sie STRG+C zum Beenden
echo ================================================================================
echo.

streamlit run src\warehouse\presentation\admin\main_admin_app.py --server.port 8502 --server.address 0.0.0.0
