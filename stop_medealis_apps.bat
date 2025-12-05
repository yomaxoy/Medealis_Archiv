@echo off
REM ========================================
REM Medealis Warehouse - Apps beenden
REM ========================================

echo.
echo ========================================
echo  Beende Medealis Warehouse Apps
echo ========================================
echo.

REM Alle Streamlit-Prozesse beenden
echo Beende laufende Streamlit-Prozesse...
taskkill /F /FI "WINDOWTITLE eq Medealis Admin*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Medealis User*" >nul 2>&1

echo.
echo Apps wurden beendet!
echo.
pause
