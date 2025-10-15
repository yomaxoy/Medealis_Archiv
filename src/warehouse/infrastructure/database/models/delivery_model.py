# src/warehouse/infrastructure/database/models/delivery_model.py

"""
SQLAlchemy Model für Deliveries (Lieferungen).
Fokus auf Rückverfolgbarkeit und Workflow-Status.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Date
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class DeliveryModel(BaseModel):
    """
    Database Model für Deliveries.

    Verwaltet Lieferungen mit Rückverfolgbarkeit:
    - Lieferscheinnummer (eindeutig)
    - Lieferant
    - Lieferdatum
    - Status
    """

    __tablename__ = "deliveries"
    __table_args__ = {'extend_existing': True}

    # === KERN-IDENTIFIKATOREN ===
    delivery_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(
        String(5), ForeignKey("suppliers.supplier_id"), nullable=False, index=True
    )
    delivery_date = Column(Date, nullable=False, index=True)

    # === VERARBEITUNG ===
    employee_name = Column(String(100), nullable=False)
    document_path = Column(
        String(500), nullable=True
    )  # Pfad zum gescannten Lieferschein

    # === STATUS ===
    status = Column(String(50), nullable=False, default="Empfangen")

    # === METADATEN ===
    notes = Column(Text, nullable=True)

    # === BEZIEHUNGEN === 
    # Temporarily disabled due to SQLAlchemy registry conflicts
    # items = relationship("ItemModel", back_populates="delivery", lazy="select")
    # supplier = relationship("SupplierModel", back_populates="deliveries", lazy="select")

    def __repr__(self):
        """Debug-Repräsentation."""
        return (
            f"DeliveryModel("
            f"delivery_number={self.delivery_number}, "
            f"supplier_id={self.supplier_id}, "
            f"status={self.status})"
        )

    def get_summary(self) -> str:
        """Kurze Zusammenfassung für UI."""
        return f"{self.delivery_number} ({self.supplier_id}) - {self.status}"
