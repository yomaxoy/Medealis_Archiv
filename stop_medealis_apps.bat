@echo off
REM ========================================
REM Medealis Warehouse - Apps beenden
REM ========================================

echo.
echo ========================================
echo  Beende Medealis Warehouse Apps
echo ========================================
echo.

REM Apps ueber Port-Belegung finden und beenden
REM Suche nach LISTENING-Prozessen (0.0.0.0:0 = lauschend)

set "found=0"

echo Suche Prozesse auf Port 8501 (Admin App)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "0.0.0.0:8501" 2^>nul') do (
    echo   Beende PID %%a ...
    taskkill /F /PID %%a >nul 2>&1
    set "found=1"
)

echo Suche Prozesse auf Port 8502 (User App)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "0.0.0.0:8502" 2^>nul') do (
    echo   Beende PID %%a ...
    taskkill /F /PID %%a >nul 2>&1
    set "found=1"
)

REM Fallback: Auch cmd-Fenster mit Medealis-Titel beenden
taskkill /F /FI "WINDOWTITLE eq Medealis Admin*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Medealis User*" >nul 2>&1

echo.
if "%found%"=="1" (
    echo Apps wurden beendet!
) else (
    echo Keine laufenden Apps gefunden.
)
echo.
pause
