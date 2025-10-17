@echo off
REM =============================================================================
REM Medealis Warehouse Service - Firewall Configuration
REM =============================================================================
REM
REM Dieses Script konfiguriert die Windows Firewall, damit andere PCs
REM im Netzwerk auf den Streamlit-Server zugreifen können.
REM
REM =============================================================================

echo ========================================
echo  Medealis - Firewall Konfiguration
echo ========================================
echo.

REM Prüfe Administrator-Rechte
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Dieses Script muss als Administrator ausgefuehrt werden!
    echo Rechtsklick -^> "Als Administrator ausfuehren"
    echo.
    pause
    exit /b 1
)

echo Loesche alte Firewall-Regeln (falls vorhanden)...
netsh advfirewall firewall delete rule name="Medealis Warehouse - HTTP" >nul 2>&1
netsh advfirewall firewall delete rule name="Medealis Warehouse - Admin" >nul 2>&1
netsh advfirewall firewall delete rule name="Medealis Warehouse - User" >nul 2>&1
netsh advfirewall firewall delete rule name="Medealis Warehouse - Streamlit" >nul 2>&1

echo.
echo Erstelle Firewall-Regel fuer Port 8501 (Admin App)...

netsh advfirewall firewall add rule ^
    name="Medealis Warehouse - Admin" ^
    description="Erlaubt Zugriff auf Medealis Warehouse Admin App (Port 8501)" ^
    dir=in ^
    action=allow ^
    protocol=TCP ^
    localport=8501 ^
    profile=any ^
    enable=yes

if %errorLevel% neq 0 (
    echo FEHLER: Port 8501 konnte nicht geoeffnet werden!
    goto error
)

echo Erstelle Firewall-Regel fuer Port 8502 (User App)...

netsh advfirewall firewall add rule ^
    name="Medealis Warehouse - User" ^
    description="Erlaubt Zugriff auf Medealis Warehouse User App (Port 8502)" ^
    dir=in ^
    action=allow ^
    protocol=TCP ^
    localport=8502 ^
    profile=any ^
    enable=yes

if %errorLevel% neq 0 (
    echo FEHLER: Port 8502 konnte nicht geoeffnet werden!
    goto error
)

echo.
echo ========================================
echo  Firewall erfolgreich konfiguriert!
echo ========================================
echo.
echo Beide Ports sind jetzt im Netzwerk erreichbar:
echo   Port 8501 - Admin App
echo   Port 8502 - User App
echo.
echo Andere PCs koennen zugreifen via:
echo   Admin: http://%COMPUTERNAME%:8501
echo   User:  http://%COMPUTERNAME%:8502
echo.
echo HINWEIS: Die Regeln gelten fuer ALLE Netzwerk-Profile.
echo (Domain, Privat UND Oeffentlich)
echo.

echo.
echo Aktuelle Firewall-Regeln fuer Medealis:
netsh advfirewall firewall show rule name="Medealis Warehouse - Admin"
echo.
netsh advfirewall firewall show rule name="Medealis Warehouse - User"
goto end

:error
echo.
echo FEHLER: Firewall-Regeln konnten nicht erstellt werden!
echo.

:end

echo.
pause
