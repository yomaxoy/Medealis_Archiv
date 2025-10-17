# 🖥️ Medealis Warehouse - Server Deployment Guide

## Komplette Anleitung zur Installation als Windows Service

Dieses Dokument beschreibt die Installation des Medealis Warehouse Management Systems als Windows Service auf einem Firmen-Server.

---

## 📋 Voraussetzungen

### Hardware (Server)
- **CPU**: 2+ Kerne
- **RAM**: 4 GB (8 GB empfohlen)
- **Festplatte**: 10 GB freier Speicher
- **Netzwerk**: Ethernet-Verbindung (LAN)

### Software (Server)
- **Betriebssystem**: Windows 10/11 oder Windows Server 2016+
- **Python**: Version 3.8 oder höher ([python.org](https://python.org))
- **Administrator-Rechte**: Erforderlich für Installation

### Netzwerk (Client-PCs)
- **Browser**: Chrome, Firefox, Edge (aktuell)
- **Netzwerk**: Zugriff auf Server im LAN
- **Port**: 8501 muss erreichbar sein

---

## 🚀 Installation (Schritt für Schritt)

### Schritt 1: Python installieren

1. **Python herunterladen**: https://www.python.org/downloads/
2. Bei Installation **wichtig**: ☑️ "Add Python to PATH" aktivieren
3. Installation bestätigen:
   ```cmd
   python --version
   ```
   Erwartete Ausgabe: `Python 3.8.x` oder höher

### Schritt 2: Projekt auf Server kopieren

1. Projekt-Ordner auf Server kopieren nach:
   ```
   C:\Medealis\warehouse\
   ```

2. In Projekt-Verzeichnis wechseln:
   ```cmd
   cd C:\Medealis\warehouse
   ```

### Schritt 3: Dependencies installieren

1. **Virtuelle Umgebung erstellen** (empfohlen):
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Requirements installieren**:
   ```cmd
   pip install -r requirements.txt
   pip install -r requirements_service.txt
   ```

3. **Test**: Prüfe ob alle Module geladen werden können:
   ```cmd
   python -c "import streamlit; import pywin32"
   ```

### Schritt 4: Windows Service installieren

1. **Als Administrator** Eingabeaufforderung öffnen:
   - Windows-Taste drücken
   - "cmd" eingeben
   - Rechtsklick → "Als Administrator ausführen"

2. In Service-Verzeichnis wechseln:
   ```cmd
   cd C:\Medealis\warehouse\service
   ```

3. **Service installieren**:
   ```cmd
   install_service.bat
   ```

   Das Script führt automatisch aus:
   - ✅ Prüft Python-Installation
   - ✅ Installiert pywin32 (falls nötig)
   - ✅ Installiert Windows Service
   - ✅ Konfiguriert Autostart

4. **Erfolg**: Sie sehen:
   ```
   ========================================
    Installation erfolgreich!
   ========================================
   ```

### Schritt 5: Firewall konfigurieren

1. **Firewall-Regel erstellen** (als Administrator):
   ```cmd
   firewall_config.bat
   ```

   Dies öffnet Port 8501 für das Netzwerk.

2. **Alternative (manuell)**:
   - Windows Firewall öffnen
   - "Erweiterte Einstellungen"
   - "Eingehende Regeln" → "Neue Regel"
   - Port: TCP 8501
   - Profil: Domain + Privat

### Schritt 6: Service starten

1. **Service starten**:
   ```cmd
   start_service.bat
   ```

2. **Status prüfen**:
   ```cmd
   status_service.bat
   ```

3. **Testen im Browser**:
   - Auf dem Server: http://localhost:8501
   - Von anderem PC: http://SERVER-IP:8501

---

## 🌐 Zugriff von Client-PCs

### Option A: IP-Adresse verwenden

1. **Server-IP ermitteln** (auf Server):
   ```cmd
   ipconfig
   ```
   Suche nach "IPv4-Adresse", z.B. `192.168.1.100`

2. **Von Client-PC aus zugreifen**:
   ```
   http://192.168.1.100:8501
   ```

### Option B: Computer-Name verwenden

```
http://SERVER-NAME:8501
```

Ersetze `SERVER-NAME` mit dem Computernamen des Servers.

### Bookmark erstellen

Erstellen Sie ein Lesezeichen im Browser für einfachen Zugriff:
- **Name**: Medealis Wareneingang
- **URL**: http://192.168.1.100:8501

---

## 🔧 Verwaltung

### Service-Befehle (als Administrator)

```cmd
# Service starten
start_service.bat

# Service stoppen
stop_service.bat

# Status anzeigen
status_service.bat

# Service neu starten
stop_service.bat
start_service.bat
```

### Backup-System

#### Automatisches Backup

Das System erstellt **täglich um 02:00 Uhr** automatisch ein Backup.

**Backup-Task installieren**:
```cmd
install_backup_task.bat
```

**Aufbewahrung**: 30 Tage (ältere Backups werden automatisch gelöscht)

**Backup-Speicherort**:
```
C:\Users\<USERNAME>\.medealis\backups\
```

#### Manuelles Backup

```cmd
# Sofortiges Backup erstellen
backup_now.bat

# Alle Backups anzeigen
python backup_database.py --list

# Backup wiederherstellen
python backup_database.py --restore "C:\Users\...\backups\warehouse_backup_20250113_020000.zip"
```

---

## 📊 Monitoring & Troubleshooting

### Service läuft nicht?

1. **Event Viewer prüfen**:
   - Windows-Taste + R → `eventvwr`
   - Windows-Protokolle → Anwendung
   - Nach "MedealisWarehouse" filtern

2. **Port bereits belegt?**:
   ```cmd
   netstat -ano | findstr :8501
   ```

3. **Manueller Start zum Debuggen**:
   ```cmd
   cd C:\Medealis\warehouse
   venv\Scripts\activate
   streamlit run src\warehouse\presentation\admin\main_admin_app.py --server.port=8501
   ```

### Verbindung vom Client funktioniert nicht?

1. **Ping-Test**:
   ```cmd
   ping SERVER-IP
   ```

2. **Port-Test**:
   ```cmd
   telnet SERVER-IP 8501
   ```

3. **Firewall prüfen** (auf Server):
   ```cmd
   netsh advfirewall firewall show rule name="Medealis Warehouse - Streamlit"
   ```

### Performance-Probleme?

1. **Task Manager öffnen** → Prozess "python.exe" prüfen
2. **Zu viele Backups?** Alte Backups manuell löschen
3. **Datenbank-Größe prüfen**:
   ```cmd
   dir %USERPROFILE%\.medealis\warehouse_new.db*
   ```

---

## 🔄 Updates

### Software-Update durchführen

1. **Service stoppen**:
   ```cmd
   stop_service.bat
   ```

2. **Backup erstellen**:
   ```cmd
   backup_now.bat
   ```

3. **Code aktualisieren**:
   - Neue Version in Projekt-Ordner kopieren
   - ODER: Git Pull (falls Git verwendet wird)

4. **Dependencies aktualisieren**:
   ```cmd
   venv\Scripts\activate
   pip install -r requirements.txt --upgrade
   ```

5. **Service neu starten**:
   ```cmd
   start_service.bat
   ```

---

## 🗑️ Deinstallation

```cmd
# Als Administrator
uninstall_service.bat
```

Dies entfernt:
- ✅ Windows Service
- ✅ Firewall-Regel

**Nicht gelöscht** (manuell entfernen falls gewünscht):
- Datenbank: `C:\Users\<USERNAME>\.medealis\`
- Projekt-Dateien: `C:\Medealis\warehouse\`
- Python-Installation

---

## 📱 Mobile Zugriff (optional)

Falls der Server auch von außerhalb des LANs erreichbar sein soll:

### ⚠️ SICHERHEITSHINWEIS
**Nicht empfohlen** ohne zusätzliche Sicherheitsmaßnahmen!

### Sichere Optionen:

#### Option 1: VPN
- Mitarbeiter verbinden sich per VPN ins Firmennetzwerk
- Dann normaler Zugriff über LAN-IP

#### Option 2: Reverse Proxy mit Authentifizierung
- Nginx oder Caddy als Reverse Proxy
- HTTPS + Passwort-Schutz
- Komplexere Konfiguration erforderlich

---

## 📞 Support & Hilfe

### Log-Dateien

**Service-Logs** (Windows Event Viewer):
- Windows-Taste + R → `eventvwr`
- Windows-Protokolle → Anwendung

**Application-Logs**:
```
C:\Users\<USERNAME>\.medealis\logs\
```

### Häufige Probleme

| Problem | Lösung |
|---------|--------|
| "Database locked" | WAL-Mode prüfen (bereits konfiguriert) |
| "Port 8501 in use" | Anderen Prozess beenden oder Port ändern |
| "Service starts but crashes" | Event Viewer prüfen, Python-Path prüfen |
| "Can't connect from client" | Firewall-Regel prüfen, IP-Adresse prüfen |

---

## ✅ Checkliste Post-Installation

Nach erfolgreicher Installation prüfen:

- [ ] Service läuft (`status_service.bat`)
- [ ] Lokaler Zugriff funktioniert (`http://localhost:8501`)
- [ ] Netzwerk-Zugriff von Client-PC funktioniert
- [ ] Backup-Task installiert (`install_backup_task.bat`)
- [ ] Firewall-Regel aktiv
- [ ] Mitarbeiter wurden eingewiesen
- [ ] Browser-Lesezeichen erstellt
- [ ] Test-Lieferung erfasst

---

## 📚 Weiterführende Dokumentation

- **Benutzerhandbuch**: `USER_GUIDE.md` (für Mitarbeiter)
- **Entwickler-Dokumentation**: `DEVELOPMENT_NOTES.md`
- **Architektur-Übersicht**: `ARCHITECTURE_EXPLANATION.md`
- **Lokales Deployment**: `LOCAL_PC_DEPLOYMENT.md`

---

**Version**: 2.0.0
**Stand**: Januar 2025
**Entwickelt für**: Medealis GmbH
