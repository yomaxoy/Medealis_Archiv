# 🔧 Medealis Service Management

Dieses Verzeichnis enthält alle Dateien für den Windows Service-Betrieb.

## 📁 Dateien-Übersicht

### Installation & Verwaltung

| Datei | Beschreibung |
|-------|-------------|
| `install_service.bat` | Installiert den Windows Service |
| `start_service.bat` | Startet den Service |
| `stop_service.bat` | Stoppt den Service |
| `status_service.bat` | Zeigt Service-Status an |
| `uninstall_service.bat` | Deinstalliert den Service |
| `firewall_config.bat` | Konfiguriert Windows Firewall |

### Backup-System

| Datei | Beschreibung |
|-------|-------------|
| `backup_database.py` | Backup-Script (Python) |
| `backup_now.bat` | Erstellt sofortiges Backup |
| `install_backup_task.bat` | Installiert automatisches tägliches Backup |

### Service-Komponenten

| Datei | Beschreibung |
|-------|-------------|
| `medealis_service.py` | Windows Service Wrapper |
| `backup_task.xml` | Task Scheduler Definition (auto-generiert) |

---

## 🚀 Quick Start

### Erstinstallation

```cmd
# 1. Als Administrator öffnen
# 2. Service installieren
install_service.bat

# 3. Firewall konfigurieren
firewall_config.bat

# 4. Service starten
start_service.bat

# 5. Backup-Task installieren
install_backup_task.bat
```

### Täglicher Betrieb

```cmd
# Service-Status prüfen
status_service.bat

# Manuelles Backup
backup_now.bat
```

---

## 🔍 Service-Details

**Service-Name**: `MedealisWarehouse`
**Display-Name**: Medealis Warehouse Management System
**Startup-Type**: Automatic
**Port**: 8501

---

## 📝 Wichtige Hinweise

- Alle `.bat`-Dateien müssen **als Administrator** ausgeführt werden
- Der Service startet automatisch beim Windows-Start
- Backups werden täglich um 02:00 Uhr erstellt
- Alte Backups (>30 Tage) werden automatisch gelöscht

---

## 🆘 Hilfe

Bei Problemen siehe: `../SERVER_DEPLOYMENT_GUIDE.md`
