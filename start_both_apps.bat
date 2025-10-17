@echo off
REM ==========================================
REM Medealis Warehouse - Beide Apps starten
REM ==========================================
echo.
echo ========================================
echo  Medealis Warehouse Management System
echo ========================================
echo.
echo Starte beide Anwendungen:
echo   - Admin App: http://localhost:8501
echo   - User App:  http://localhost:8502
echo.

REM Admin App auf Port 8501 im Hintergrund starten
echo [1/2] Starte Admin App (Port 8501)...
start "Medealis Admin" /MIN cmd /c ".venv\Scripts\activate.bat && .venv\Scripts\python.exe start_app_with_env.py src\warehouse\presentation\admin\main_admin_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"

REM Kurz warten
timeout /t 3 /nobreak >nul

REM User App auf Port 8502 im Hintergrund starten
echo [2/2] Starte User App (Port 8502)...
start "Medealis User" /MIN cmd /c ".venv\Scripts\activate.bat && .venv\Scripts\python.exe start_app_with_env.py src\warehouse\presentation\user\main_user_app.py --server.port=8502 --server.address=0.0.0.0 --server.headless=true"

echo.
echo ========================================
echo  Beide Apps erfolgreich gestartet!
echo ========================================
echo.
echo Zugriff ueber:
echo   Admin App: http://localhost:8501
echo   User App:  http://localhost:8502
echo.
echo Im Netzwerk erreichbar:
echo   Admin: http://10.190.140.121:8501
echo   User:  http://10.190.140.121:8502
echo.
echo Zum Beenden: Beide Fenster schliessen
echo              oder CTRL+C in jedem Fenster
echo.

pause
