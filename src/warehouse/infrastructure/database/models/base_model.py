# src/warehouse/infrastructure/database/models/base_model.py

"""
Base Model für alle SQLAlchemy Models.
Enthält gemeinsame Felder und Funktionalität.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String
from warehouse.infrastructure.database.connection import Base


class BaseModel(Base):
    """
    Abstrakte Basis für alle Database Models.

    Enthält Standard-Felder, die jede Tabelle benötigt:
    - Primärschlüssel
    - Audit-Felder (created_at, updated_at)
    """

    __abstract__ = True  # Wird nicht als eigene Tabelle erstellt

    # Primärschlüssel
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Audit-Felder
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    def to_dict(self):
        """
        Konvertiert Model zu Dictionary.
        Hilfsmethode für Serialisierung.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self):
        """Debug-Repräsentation."""
        return f"{self.__class__.__name__}(id={getattr(self, 'id', 'new')})"
