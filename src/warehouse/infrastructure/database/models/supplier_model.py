# src/warehouse/infrastructure/database/models/supplier_model.py

"""
Supplier Model für Lieferanten-Stammdaten.
ERWEITERT um Orders-Beziehung.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship

from warehouse.infrastructure.database.connection import Base


class SupplierModel(Base):
    """
    Supplier Model - Lieferanten-Stammdaten.
    Primary Key: supplier_id (Business Key)
    ERWEITERT um Orders-Beziehung.
    """

    __tablename__ = "suppliers"
    __table_args__ = {"extend_existing": True}

    # === PRIMÄRSCHLÜSSEL (Business Key) ===
    # Frei wählbare 5-stellige numerische Lieferantennummer, z.B. "10006" (Primec), "10031" (Terrats)
    # Nur echte physische Lieferanten! Implantatmarken (BEGO, CAMLOG, DENTSPLY etc.) gehören
    # NICHT hier rein - sie sind Kompatibilitäten und stehen in item_info.kompatibilitaet.
    supplier_id = Column(String(20), primary_key=True)

    # === AUDIT FIELDS ===
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # === GRUNDDATEN ===
    name = Column(Text, nullable=False)  # Lieferanten-Name
    address = Column(Text, nullable=True)  # Vollständige Adresse

    # === KONTAKTDATEN ===
    contact_person = Column(String(100), nullable=True)  # Ansprechpartner
    phone = Column(String(50), nullable=True)  # Telefonnummer
    email = Column(String(100), nullable=True)  # E-Mail Adresse
    website = Column(String(200), nullable=True)  # Website URL

    # === QUALITÄTS-INFO ===
    iso_certification = Column(String(100), nullable=True)  # ISO-Zertifizierung
    quality_rating = Column(String(20), nullable=True)  # A, B, C Rating
    preferred_supplier = Column(String(10), default="No", nullable=False)  # "Yes"/"No"

    # === ZUSÄTZLICHE INFOS ===
    notes = Column(Text, nullable=True)  # Allgemeine Notizen

    # === BEZIEHUNGEN ===
    # Temporarily disabled due to SQLAlchemy registry conflicts
    # deliveries = relationship("DeliveryModel", back_populates="supplier", lazy="select")
    # orders = relationship("OrderModel", back_populates="supplier", lazy="select")  # ← NEU: Orders-Beziehung

    def __repr__(self):
        return f"SupplierModel({self.supplier_id}: {self.name})"

    def get_display_name(self) -> str:
        """Gibt Anzeigename für UI zurück."""
        return f"{self.name} ({self.supplier_id})"

    def is_preferred_supplier(self) -> bool:
        """Prüft ob dies ein bevorzugter Lieferant ist."""
        return self.preferred_supplier.lower() == "yes"

    def get_contact_summary(self) -> dict:
        """Gibt Kontakt-Zusammenfassung zurück."""
        return {
            "name": self.name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
        }

    def get_quality_info(self) -> dict:
        """Gibt Qualitäts-Informationen zurück."""
        return {
            "quality_rating": self.quality_rating,
            "iso_certification": self.iso_certification,
            "preferred_supplier": self.is_preferred_supplier(),
        }

    def has_complete_contact_info(self) -> bool:
        """Prüft ob vollständige Kontaktdaten vorhanden sind."""
        return all(
            [
                self.name,
                self.address,
                (self.phone or self.email),  # Mindestens Telefon ODER E-Mail
            ]
        )

    # === NEU: BUSINESS LOGIC FÜR ORDERS ===

    def get_order_summary(self) -> dict:
        """Gibt Übersicht über Orders zurück."""
        if not self.orders:
            return {"total_orders": 0, "open_orders": 0, "completed_orders": 0}

        total = len(self.orders)
        open_orders = len([o for o in self.orders if o.status == "Offen"])
        completed = len([o for o in self.orders if o.status == "Abgeschlossen"])

        return {
            "total_orders": total,
            "open_orders": open_orders,
            "completed_orders": completed,
            "completion_rate": round((completed / total * 100), 1) if total > 0 else 0,
        }

    def get_delivery_summary(self) -> dict:
        """Gibt Übersicht über Deliveries zurück."""
        if not self.deliveries:
            return {"total_deliveries": 0}

        return {
            "total_deliveries": len(self.deliveries),
            "recent_deliveries": len([d for d in self.deliveries if d.created_at]),
        }
