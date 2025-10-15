# src/warehouse/infrastructure/database/models/item_workflow_steps_model.py

"""
Item Workflow Steps Model - Status-Tracking System.

Diese Tabelle trackt den Workflow-Fortschritt jedes Items.
Jeder Schritt speichert: Wer hat ihn durchgeführt + Wann.

Workflow-Reihenfolge:
1. Daten prüfen
2. Dokumente prüfen
3. Vermessen
4. Sichtkontrolle
5. Dokumente zusammenführen
6. Abschließen (completed) oder Ausschuss (rejected)
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKeyConstraint
from datetime import datetime
from warehouse.infrastructure.database.connection import Base


class ItemWorkflowStepsModel(Base):
    """
    Workflow Steps für Items - Status-Tracking.

    Design:
    - Ein Eintrag pro Item (1:1 Beziehung mit items Tabelle)
    - NULL = Schritt nicht erledigt
    - String (Mitarbeitername) = Schritt erledigt von diesem Mitarbeiter
    - Status wird berechnet als "Erster nicht-erledigter Schritt"
    """

    __tablename__ = "item_workflow_steps"

    # === COMPOSITE PRIMARY KEY (Item-Identifikation) ===
    article_number = Column(String(7), primary_key=True)
    batch_number = Column(String(50), primary_key=True)
    delivery_number = Column(String(50), primary_key=True)

    # === WORKFLOW STEPS (in Reihenfolge) ===

    # Step 1: Daten prüfen
    data_checked_by = Column(String(100), nullable=True)
    data_checked_at = Column(DateTime, nullable=True)

    # Step 2: Dokumente prüfen
    documents_checked_by = Column(String(100), nullable=True)
    documents_checked_at = Column(DateTime, nullable=True)

    # Step 3: Vermessen
    measured_by = Column(String(100), nullable=True)
    measured_at = Column(DateTime, nullable=True)

    # Step 4: Sichtkontrolle
    visually_inspected_by = Column(String(100), nullable=True)
    visually_inspected_at = Column(DateTime, nullable=True)

    # Step 5: Dokumente zusammenführen
    documents_merged_by = Column(String(100), nullable=True)
    documents_merged_at = Column(DateTime, nullable=True)

    # === FINALE STATUS ===

    # Abgeschlossen (Success)
    completed_by = Column(String(100), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Ausschuss (Rejected)
    rejected_by = Column(String(100), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # === AUDIT-TIMESTAMPS ===
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # === FOREIGN KEY CONSTRAINT ===
    __table_args__ = (
        ForeignKeyConstraint(
            ['article_number', 'batch_number', 'delivery_number'],
            ['items.article_number', 'items.batch_number', 'items.delivery_number'],
            name='fk_workflow_steps_item',
            ondelete='CASCADE'
        ),
    )

    def __repr__(self):
        return (
            f"<ItemWorkflowStepsModel("
            f"article={self.article_number}, "
            f"batch={self.batch_number}, "
            f"delivery={self.delivery_number})>"
        )
