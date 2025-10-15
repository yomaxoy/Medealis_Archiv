#!/usr/bin/env python3
"""
Automatisches Backup-System für Medealis Warehouse Datenbank.

Features:
- Automatische tägliche Backups
- Komprimierung (ZIP)
- Aufbewahrung der letzten 30 Backups
- Alte Backups werden automatisch gelöscht
- Kann als Windows Task Scheduler Job laufen

Verwendung:
    python backup_database.py              # Einmaliges Backup
    python backup_database.py --install    # Task Scheduler installieren
"""

import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
import argparse


class DatabaseBackup:
    """Automatisches Datenbank-Backup System."""

    def __init__(self):
        """Initialisiert das Backup-System."""
        # Pfade
        self.project_root = Path(__file__).parent.parent

        # Datenbank-Pfad aus Settings oder Standard
        try:
            sys.path.insert(0, str(self.project_root / "config"))
            from settings import settings
            self.db_path = Path(settings.DATABASE_PATH)
        except ImportError:
            # Fallback
            self.db_path = Path.home() / ".medealis" / "warehouse_new.db"

        # Backup-Verzeichnis
        self.backup_dir = self.db_path.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Aufbewahrungsdauer
        self.retention_days = 30

    def create_backup(self) -> Path:
        """
        Erstellt ein Backup der Datenbank.

        Returns:
            Path zum erstellten Backup
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Datenbank nicht gefunden: {self.db_path}")

        # Backup-Dateiname mit Zeitstempel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"warehouse_backup_{timestamp}"
        backup_zip = self.backup_dir / f"{backup_name}.zip"

        print(f"Erstelle Backup: {backup_zip.name}")

        # Temporäres Verzeichnis für Backup-Dateien
        temp_backup_dir = self.backup_dir / backup_name
        temp_backup_dir.mkdir(exist_ok=True)

        try:
            # Kopiere Datenbank-Dateien
            # SQLite mit WAL-Mode hat 3 Dateien: .db, .db-wal, .db-shm
            files_to_backup = [
                self.db_path,
                Path(str(self.db_path) + "-wal"),
                Path(str(self.db_path) + "-shm"),
            ]

            for file_path in files_to_backup:
                if file_path.exists():
                    dest = temp_backup_dir / file_path.name
                    shutil.copy2(file_path, dest)
                    print(f"  ✓ {file_path.name}")

            # Komprimiere zu ZIP
            with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in temp_backup_dir.glob("*"):
                    zipf.write(file, file.name)

            # Lösche temporäres Verzeichnis
            shutil.rmtree(temp_backup_dir)

            # Dateigröße anzeigen
            size_mb = backup_zip.stat().st_size / (1024 * 1024)
            print(f"  ✓ Backup erstellt ({size_mb:.2f} MB)")

            return backup_zip

        except Exception as e:
            # Cleanup bei Fehler
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
            if backup_zip.exists():
                backup_zip.unlink()
            raise RuntimeError(f"Backup fehlgeschlagen: {e}")

    def cleanup_old_backups(self):
        """Löscht alte Backups basierend auf Aufbewahrungsdauer."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        print(f"\nPrüfe alte Backups (älter als {self.retention_days} Tage)...")

        for backup_file in self.backup_dir.glob("warehouse_backup_*.zip"):
            # Extrahiere Datum aus Dateinamen
            try:
                # Format: warehouse_backup_YYYYMMDD_HHMMSS.zip
                date_str = backup_file.stem.split("_")[2]  # YYYYMMDD
                backup_date = datetime.strptime(date_str, "%Y%m%d")

                if backup_date < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    print(f"  🗑 Gelöscht: {backup_file.name}")

            except (ValueError, IndexError):
                # Ungültiger Dateiname - überspringen
                continue

        if deleted_count == 0:
            print("  ✓ Keine alten Backups zum Löschen")
        else:
            print(f"  ✓ {deleted_count} alte Backups gelöscht")

    def list_backups(self):
        """Listet alle vorhandenen Backups auf."""
        backups = sorted(
            self.backup_dir.glob("warehouse_backup_*.zip"), reverse=True
        )

        if not backups:
            print("Keine Backups gefunden.")
            return

        print(f"\n{'Backup':<40} {'Größe':<12} {'Datum'}")
        print("-" * 70)

        for backup_file in backups:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            print(f"{backup_file.name:<40} {size_mb:>8.2f} MB   {mtime:%Y-%m-%d %H:%M}")

        print(f"\nGesamt: {len(backups)} Backups")

    def restore_backup(self, backup_file: Path):
        """
        Stellt ein Backup wieder her.

        Args:
            backup_file: Path zum Backup-ZIP

        WARNUNG: Überschreibt die aktuelle Datenbank!
        """
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup nicht gefunden: {backup_file}")

        print(f"\nWARNUNG: Die aktuelle Datenbank wird überschrieben!")
        print(f"Backup: {backup_file.name}")

        response = input("Fortfahren? (ja/nein): ").strip().lower()
        if response not in ("ja", "j", "yes", "y"):
            print("Abgebrochen.")
            return

        # Erstelle Sicherheits-Backup der aktuellen DB
        safety_backup = self.db_path.parent / f"warehouse_before_restore_{datetime.now():%Y%m%d_%H%M%S}.db"
        if self.db_path.exists():
            shutil.copy2(self.db_path, safety_backup)
            print(f"  ✓ Sicherheits-Backup erstellt: {safety_backup.name}")

        try:
            # Entpacke Backup
            with zipfile.ZipFile(backup_file, "r") as zipf:
                zipf.extractall(self.db_path.parent)

            print("  ✓ Backup erfolgreich wiederhergestellt")

        except Exception as e:
            # Stelle Original wieder her bei Fehler
            if safety_backup.exists():
                shutil.copy2(safety_backup, self.db_path)
                print(f"  ✗ Fehler! Original wiederhergestellt: {e}")
            raise

    def install_scheduled_task(self):
        """Installiert einen Windows Task Scheduler Job für tägliche Backups."""
        print("\n=== Windows Task Scheduler Installation ===\n")

        task_name = "MedealisWarehouseBackup"
        script_path = Path(__file__).resolve()
        python_exe = sys.executable

        # Task-XML generieren
        task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Tägliches Backup der Medealis Warehouse Datenbank</Description>
    <Author>Medealis</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{script_path}"</Arguments>
    </Exec>
  </Actions>
</Task>"""

        # Speichere Task-XML
        task_xml_path = Path(__file__).parent / "backup_task.xml"
        task_xml_path.write_text(task_xml, encoding="utf-16")

        print(f"Task-Name: {task_name}")
        print(f"Zeitplan:  Täglich um 02:00 Uhr")
        print(f"Script:    {script_path}")
        print()
        print("Führe folgenden Befehl als Administrator aus:")
        print()
        print(f'schtasks /Create /XML "{task_xml_path}" /TN "{task_name}"')
        print()
        print("Oder verwende: install_backup_task.bat")


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description="Medealis Warehouse Datenbank-Backup"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Installiere Task Scheduler Job",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste alle Backups auf",
    )
    parser.add_argument(
        "--restore",
        type=str,
        metavar="BACKUP_FILE",
        help="Stelle Backup wieder her",
    )

    args = parser.parse_args()

    backup = DatabaseBackup()

    try:
        if args.install:
            backup.install_scheduled_task()

        elif args.list:
            backup.list_backups()

        elif args.restore:
            backup_file = Path(args.restore)
            backup.restore_backup(backup_file)

        else:
            # Standard: Backup erstellen
            print("=" * 60)
            print(" Medealis Warehouse - Datenbank Backup")
            print("=" * 60)
            print()

            backup.create_backup()
            backup.cleanup_old_backups()
            backup.list_backups()

            print()
            print("=" * 60)
            print(" Backup erfolgreich abgeschlossen!")
            print("=" * 60)

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
