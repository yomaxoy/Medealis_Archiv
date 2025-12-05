"""
Repository für Audit Logging.

Speichert Audit Events in:
1. PostgreSQL Datenbank (strukturiert, queryable)
2. Backup-Textdatei (menschenlesbar, langfristige Archivierung)
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc

from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.audit_log_model import AuditLogModel
from warehouse.domain.events.audit_events import AuditEvent

logger = logging.getLogger(__name__)


class AuditRepository:
    """
    Repository für Audit Log Operationen.

    Speichert Audit Events dual:
    - PostgreSQL: Strukturiert, queryable, mit Indices
    - Textdatei: Backup, menschenlesbar, compliance-konform

    Thread-safe durch PostgreSQL ACID und append-only File Operations.
    """

    def __init__(self, backup_file_path: str = "data/logs/audit_log.txt"):
        """
        Initialisiert Repository.

        Args:
            backup_file_path: Pfad zur Backup-Textdatei
        """
        self.backup_file_path = Path(backup_file_path)
        self._ensure_backup_file_exists()

    def _ensure_backup_file_exists(self):
        """Erstellt Backup-Datei und Verzeichnis falls nicht vorhanden."""
        try:
            self.backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.backup_file_path.exists():
                self.backup_file_path.touch()
                logger.info(f"Audit log backup file created: {self.backup_file_path}")
        except Exception as e:
            logger.error(f"Failed to create backup file: {e}")
            # Nicht kritisch - System funktioniert auch ohne Textdatei

    def log_event(self, event: AuditEvent) -> bool:
        """
        Loggt ein Audit-Event in DB und Datei.

        Args:
            event: AuditEvent zu loggen

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Format log line
            log_line = event.format_log_line()

            # 1. In Datenbank speichern (primär)
            with get_session() as session:
                audit_entry = AuditLogModel(
                    timestamp=event.timestamp,
                    user=event.user,
                    action=event.action.value,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    data=event.data,
                    notes=event.notes,
                    log_line=log_line,
                )
                session.add(audit_entry)
                session.commit()

            # 2. In Textdatei schreiben (Backup)
            try:
                with open(self.backup_file_path, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
            except Exception as file_error:
                # Textdatei-Fehler ist nicht kritisch
                logger.warning(f"Failed to write to backup file: {file_error}")
                # Aber Event ist in DB, also Success

            logger.debug(f"Audit event logged: {event.action.value} by {event.user}")
            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            logger.exception("Full traceback:")
            return False

    def get_recent_logs(self, limit: int = 100) -> List[AuditLogModel]:
        """
        Lädt die neuesten Audit-Logs.

        Args:
            limit: Maximale Anzahl Einträge

        Returns:
            Liste von AuditLogModel (neueste zuerst)
        """
        try:
            with get_session() as session:
                logs = (
                    session.query(AuditLogModel)
                    .order_by(desc(AuditLogModel.timestamp))
                    .limit(limit)
                    .all()
                )

                # Detach from session for usage outside
                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []

    def get_logs_by_user(self, user: str, days: int = 30) -> List[AuditLogModel]:
        """
        Lädt Logs für einen bestimmten Benutzer.

        Args:
            user: Benutzername
            days: Anzahl Tage zurück (default: 30)

        Returns:
            Liste von AuditLogModel für diesen User
        """
        try:
            since = datetime.now() - timedelta(days=days)

            with get_session() as session:
                logs = (
                    session.query(AuditLogModel)
                    .filter(AuditLogModel.user == user)
                    .filter(AuditLogModel.timestamp >= since)
                    .order_by(desc(AuditLogModel.timestamp))
                    .all()
                )

                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get logs by user: {e}")
            return []

    def get_logs_by_entity(
        self, entity_type: str, entity_id: str
    ) -> List[AuditLogModel]:
        """
        Lädt alle Logs für eine bestimmte Entity (vollständige Historie).

        Nützlich um nachzuvollziehen was mit einem bestimmten Item/Delivery passiert ist.

        Args:
            entity_type: Typ der Entity ("Delivery", "Item", "Order", etc.)
            entity_id: ID der Entity

        Returns:
            Liste von AuditLogModel für diese Entity (chronologisch)
        """
        try:
            with get_session() as session:
                logs = (
                    session.query(AuditLogModel)
                    .filter(AuditLogModel.entity_type == entity_type)
                    .filter(AuditLogModel.entity_id == entity_id)
                    .order_by(AuditLogModel.timestamp)
                    .all()
                )

                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get logs by entity: {e}")
            return []

    def get_logs_by_action(self, action: str, days: int = 7) -> List[AuditLogModel]:
        """
        Lädt Logs für eine bestimmte Aktion.

        Nützlich für Statistiken (z.B. wie oft wurde "Lieferschein gescannt").

        Args:
            action: Aktionsname (aus AuditAction.value)
            days: Anzahl Tage zurück (default: 7)

        Returns:
            Liste von AuditLogModel für diese Aktion
        """
        try:
            since = datetime.now() - timedelta(days=days)

            with get_session() as session:
                logs = (
                    session.query(AuditLogModel)
                    .filter(AuditLogModel.action == action)
                    .filter(AuditLogModel.timestamp >= since)
                    .order_by(desc(AuditLogModel.timestamp))
                    .all()
                )

                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get logs by action: {e}")
            return []

    def get_logs_by_date_range(
        self, start_date: datetime, end_date: datetime, user: Optional[str] = None
    ) -> List[AuditLogModel]:
        """
        Lädt Logs für einen Zeitraum (optional gefiltert nach User).

        Args:
            start_date: Start-Zeitpunkt
            end_date: End-Zeitpunkt
            user: Optional: Nur Logs dieses Users

        Returns:
            Liste von AuditLogModel im Zeitraum
        """
        try:
            with get_session() as session:
                query = (
                    session.query(AuditLogModel)
                    .filter(AuditLogModel.timestamp >= start_date)
                    .filter(AuditLogModel.timestamp <= end_date)
                )

                if user:
                    query = query.filter(AuditLogModel.user == user)

                logs = query.order_by(AuditLogModel.timestamp).all()

                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get logs by date range: {e}")
            return []


# Global instance (Singleton pattern)
audit_repository = AuditRepository()
