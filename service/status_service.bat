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

REM Prüfe ob Ports offen sind
echo Admin App (Port 8501):
netstat -an | findstr "8501"
echo.
echo User App (Port 8502):
netstat -an | findstr "8502"

echo.
echo ----------------------------------------
echo  Zugriffs-URLs
echo ----------------------------------------
echo.
echo Lokal:
echo   Admin App: http://localhost:8501
echo   User App:  http://localhost:8502
echo.
echo Computer:
echo   Admin App: http://%COMPUTERNAME%:8501
echo   User App:  http://%COMPUTERNAME%:8502
echo.

REM IP-Adressen anzeigen
echo IP-Adressen dieses Rechners:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo   Admin: http://%%a:8501
    echo   User:  http://%%a:8502
    echo.
)

echo.
pause
