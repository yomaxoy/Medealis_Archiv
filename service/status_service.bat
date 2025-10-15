@echo off
REM =============================================================================
REM Medealis Warehouse Service - Status Check
REM =============================================================================

echo ========================================
echo  Medealis Warehouse Service - Status
echo ========================================
echo.

REM Service-Status prüfen
sc query MedealisWarehouse

echo.
echo ----------------------------------------
echo  Netzwerk-Status
echo ----------------------------------------
echo.

REM Prüfe ob Port 8501 offen ist
netstat -an | findstr "8501"

echo.
echo ----------------------------------------
echo  Zugriffs-URLs
echo ----------------------------------------
echo.
echo Lokal:    http://localhost:8501
echo Computer: http://%COMPUTERNAME%:8501
echo.

REM IP-Adressen anzeigen
echo IP-Adressen dieses Rechners:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo   http://%%a:8501

echo.
pause
