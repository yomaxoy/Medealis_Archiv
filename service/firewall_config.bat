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
netsh advfirewall firewall delete rule name="Medealis Warehouse - Streamlit" >nul 2>&1

echo.
echo Erstelle neue Firewall-Regel fuer Port 8501...

netsh advfirewall firewall add rule ^
    name="Medealis Warehouse - Streamlit" ^
    description="Erlaubt Zugriff auf Medealis Warehouse Management System (Streamlit Port 8501)" ^
    dir=in ^
    action=allow ^
    protocol=TCP ^
    localport=8501 ^
    profile=domain,private ^
    enable=yes

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo  Firewall erfolgreich konfiguriert!
    echo ========================================
    echo.
    echo Port 8501 ist jetzt im Netzwerk erreichbar.
    echo.
    echo Andere PCs koennen zugreifen via:
    echo   http://IP-ADRESSE:8501
    echo   http://%COMPUTERNAME%:8501
    echo.
    echo HINWEIS: Die Regel gilt nur fuer Domain/Private Netzwerke.
    echo Oeffentliche Netzwerke sind aus Sicherheitsgruenden blockiert.
    echo.
) else (
    echo.
    echo FEHLER: Firewall-Regel konnte nicht erstellt werden!
    echo.
)

echo.
echo Aktuelle Firewall-Regeln fuer Medealis:
netsh advfirewall firewall show rule name="Medealis Warehouse - Streamlit"

echo.
pause
