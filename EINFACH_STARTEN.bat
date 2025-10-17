@echo off
REM ========================================
REM  EINFACHER START - Wie in VSCode
REM ========================================

echo.
echo ========================================
echo  Medealis Warehouse - Einfacher Start
echo ========================================
echo.

REM Wechsel ins richtige Verzeichnis
cd /d "%~dp0"

REM Aktiviere Virtual Environment
call .venv\Scripts\activate.bat

echo.
echo Welche App moechtest du starten?
echo.
echo [1] Admin App (Port 8501)
echo [2] User App (Port 8502)
echo [3] Beide Apps gleichzeitig
echo.
set /p choice="Bitte waehle (1/2/3): "

if "%choice%"=="1" goto admin
if "%choice%"=="2" goto user
if "%choice%"=="3" goto both
echo Ungueltige Auswahl!
pause
exit

:admin
echo.
echo Starte Admin App auf Port 8501...
echo Erreichbar unter: http://10.190.140.121:8501
echo.
streamlit run src\warehouse\presentation\admin\main_admin_app.py --server.port=8501 --server.address=0.0.0.0
pause
exit

:user
echo.
echo Starte User App auf Port 8502...
echo Erreichbar unter: http://10.190.140.121:8502
echo.
streamlit run src\warehouse\presentation\user\main_user_app.py --server.port=8502 --server.address=0.0.0.0
pause
exit

:both
echo.
echo Starte beide Apps...
echo Admin: http://10.190.140.121:8501
echo User:  http://10.190.140.121:8502
echo.
start "Medealis Admin" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && streamlit run src\warehouse\presentation\admin\main_admin_app.py --server.port=8501 --server.address=0.0.0.0"
timeout /t 2 >nul
start "Medealis User" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && streamlit run src\warehouse\presentation\user\main_user_app.py --server.port=8502 --server.address=0.0.0.0"
echo.
echo Beide Apps wurden gestartet!
echo Fenster bleiben offen - CTRL+C zum Beenden
pause
exit
