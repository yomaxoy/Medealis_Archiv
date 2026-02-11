"""
SQLAlchemy Model für Audit Log.

Speichert alle Benutzeraktionen und Statusänderungen für vollständige Nachvollziehbarkeit.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Index, JSON
from datetime import datetime
from warehouse.infrastructure.database.connection import Base


class AuditLogModel(Base):
    """
    Audit Log Tabelle.

    Speichert alle Benutzeraktionen und Statusänderungen im System.
    Wichtig für Compliance (Medizinprodukte) und Fehlersuche.

    Columns:
        id: Auto-increment Primary Key
        timestamp: Zeitpunkt der Aktion (mit Index für schnelle Zeit-Queries)
        user: Benutzername (mit Index für User-spezifische Queries)
        action: Art der Aktion (mit Index für Action-Filter)
        entity_type: Typ der Entity ("Delivery", "Item", etc.) (mit Index)
        entity_id: ID der Entity (mit Index für Entity-History)
        data: Strukturierte Zusatzdaten als JSONB (queryable)
        notes: Optionale Freitext-Notizen
        log_line: Formatierte Log-Zeile (menschenlesbar)
    """

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    user = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(200), nullable=False, index=True)
    data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    log_line = Column(Text, nullable=False)  # Formatierte Zeile für Textdatei

    # Composite Index für häufige Queries (Entity-History)
    __table_args__ = (
        Index("idx_audit_entity_history", "entity_type", "entity_id", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user='{self.user}', action='{self.action}', timestamp='{self.timestamp}')>"
