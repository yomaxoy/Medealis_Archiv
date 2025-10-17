# src/warehouse/infrastructure/database/models/item_model.py

"""
Item Models mit korrekten Primary Keys und Beziehungen.
ERWEITERT um Order-Beziehung.

ItemInfoModel: article_number als PK
ItemModel: (article_number, batch_number, delivery_number) als Composite PK
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from warehouse.infrastructure.database.connection import Base


class ItemInfoModel(Base):
    """
    Item Info Model - Artikel-Stammdaten.

    Primary Key: article_number
    Entspricht deiner 'ItemInfo' Tabelle.
    """

    __tablename__ = "item_info"
    __table_args__ = {'extend_existing': True}

    # === PRIMÄRSCHLÜSSEL ===
    article_number = Column(String(7), primary_key=True)  # A0001, B0002, CT003, SI00154, etc.

    # === AUDIT FIELDS ===
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # === ARTIKEL-STAMMDATEN ===
    designation = Column(Text, nullable=True)  # Artikelbezeichnung
    revision_number = Column(Integer, nullable=True)  # Revisionsnummer
    drawing_reference = Column(Text, nullable=True)  # Zeichnung
    storage_location = Column(Text, nullable=True)  # Lagernummer

    # === ZUSÄTZLICHE INFOS ===
    manufacturer = Column(String(100), nullable=True)  # Implantathersteller für Docklocs Schema
    material_specification = Column(Text, nullable=True)  # Material-Spezifikation
    description = Column(Text, nullable=True)  # Zusätzliche Beschreibung

    # === BEZIEHUNGEN ===
    # Temporarily disabled due to SQLAlchemy registry conflicts  
    # items = relationship("ItemModel", back_populates="item_info", lazy="select")

    def __repr__(self):
        return f"ItemInfoModel({self.article_number}: {self.designation})"


class ItemModel(Base):
    """
    Item Model - Chargen-spezifische Item-Instanzen.

    Primary Key: (article_number, batch_number, delivery_number)
    ERWEITERT um Order-Beziehung für vollständige Rückverfolgbarkeit.
    """

    __tablename__ = "items"
    __table_args__ = {'extend_existing': True}

    # === COMPOSITE PRIMARY KEY (wie in deinem Original) ===
    article_number = Column(
        String(7), ForeignKey("item_info.article_number"), primary_key=True
    )  # Teil des Composite PK
    batch_number = Column(String(19), primary_key=True)  # Chargennummer (Teil des PK)
    delivery_number = Column(
        String(10), ForeignKey("deliveries.delivery_number"), primary_key=True
    )  # Lieferscheinnummer (Teil des PK)

    # === AUDIT FIELDS ===
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # === ZUSÄTZLICHE RÜCKVERFOLGBARKEIT ===
    order_number = Column(
        String(10), ForeignKey("orders.order_number"), nullable=True, index=True
    )  # ← NEU: Beziehung zur ursprünglichen Bestellung

    # === MENGEN-TRACKING ===
    # Drei Mengentypen für vollständige Rückverfolgbarkeit:
    # 1. ordered_quantity: Bestellte Menge (aus Bestellung beim Lieferanten)
    # 2. delivery_slip_quantity: Lieferscheinmenge (vom OCR extrahiert)
    # 3. delivered_quantity: Tatsächlich gelieferte Menge (manuell gezählt)
    delivered_quantity = Column(Integer, nullable=False)  # Tatsächlich gelieferte Menge
    ordered_quantity = Column(Integer, nullable=True)  # Bestellmenge
    delivery_slip_quantity = Column(Integer, nullable=True)  # Lieferscheinmenge (OCR)
    waste_quantity = Column(Integer, nullable=True, default=0)  # Ausschuss

    # === WORKFLOW-STATUS ===
    # REMOVED: status wird jetzt über item_workflow_steps Tabelle verwaltet
    # Status wird dynamisch berechnet basierend auf erledigten Workflow-Steps

    # === ZERTIFIKATE (Boolean Flags wie in deinem Original) ===
    measurement_protocol = Column(
        Boolean, nullable=False, default=False
    )  # Messprotokoll
    coating_certificate = Column(Boolean, nullable=False, default=False)  # Beschichtung
    material_certificate = Column(
        Boolean, nullable=False, default=False
    )  # Materialzeugnis
    hardness_certificate = Column(
        Boolean, nullable=False, default=False
    )  # Härtezeugnis
    additional_certificates = Column(
        Boolean, nullable=False, default=False
    )  # Weitere_Zeugnisse
    label_present = Column(Boolean, nullable=True, default=False)  # Etikett
    accompanying_document = Column(
        Boolean, nullable=True, default=False
    )  # Begleitschein

    # === VERANTWORTLICHKEITEN ===
    employee = Column(Text, nullable=True)  # Mitarbeiter
    visual_inspector = Column(Text, nullable=True)  # Sichtprüfer

    # === NOTIZEN ===
    notes = Column(Text, nullable=True)  # Notiz

    # === BEZIEHUNGEN ===
    # Temporarily disabled due to SQLAlchemy registry conflicts
    # item_info = relationship("ItemInfoModel", back_populates="items", lazy="select")
    # delivery = relationship("DeliveryModel", back_populates="items", lazy="select")
    # order = relationship("OrderModel", back_populates="items", lazy="select")  # ← NEU: Order-Beziehung

    def __repr__(self):
        return (
            f"ItemModel({self.article_number}, "
            f"batch={self.batch_number}, "
            f"delivery={self.delivery_number}, "
            f"order={self.order_number})"
        )

    # === BUSINESS LOGIC METHODS ===

    def get_good_quantity(self) -> int:
        """Berechnet verwertbare Menge (Geliefert - Ausschuss)."""
        return self.delivered_quantity - self.waste_quantity

    def get_waste_percentage(self) -> float:
        """Berechnet Ausschussquote in Prozent."""
        if self.delivered_quantity == 0:
            return 0.0
        return (self.waste_quantity / self.delivered_quantity) * 100.0

    def has_quantity_discrepancy(self) -> bool:
        """Prüft ob Mengen-Abweichungen vorliegen (Bestellung vs. Lieferung)."""
        if self.ordered_quantity is None:
            return False
        return self.delivered_quantity != self.ordered_quantity

    def has_delivery_slip_discrepancy(self) -> bool:
        """Prüft ob Lieferschein und tatsächliche Lieferung abweichen."""
        if self.delivery_slip_quantity is None:
            return False
        return self.delivered_quantity != self.delivery_slip_quantity

    def get_quantity_difference(self) -> int:
        """Gibt Mengen-Differenz zurück (Geliefert - Bestellt)."""
        if self.ordered_quantity is None:
            return 0
        return self.delivered_quantity - self.ordered_quantity

    def get_slip_difference(self) -> int:
        """Gibt Mengen-Differenz zurück (Geliefert - Lieferschein)."""
        if self.delivery_slip_quantity is None:
            return 0
        return self.delivered_quantity - self.delivery_slip_quantity

    def has_all_required_certificates(self) -> bool:
        """Prüft ob alle erforderlichen Zertifikate vorhanden sind."""
        return self.material_certificate

    def get_missing_certificates(self) -> list:
        """Gibt Liste fehlender Zertifikate zurück."""
        missing = []

        if not self.material_certificate:
            missing.append("Materialzeugnis")
        if not self.measurement_protocol:
            missing.append("Messprotokoll")
        if not self.coating_certificate:
            missing.append("Beschichtung")
        if not self.hardness_certificate:
            missing.append("Härtezeugnis")

        return missing

    def get_certificate_summary(self) -> dict:
        """Gibt Übersicht über alle Zertifikate zurück."""
        return {
            "Materialzeugnis": self.material_certificate,
            "Messprotokoll": self.measurement_protocol,
            "Beschichtung": self.coating_certificate,
            "Härtezeugnis": self.hardness_certificate,
            "Weitere Zeugnisse": self.additional_certificates,
            "Etikett": self.label_present,
            "Begleitschein": self.accompanying_document,
        }

    def can_be_completed(self) -> bool:
        """Prüft ob Item abgeschlossen werden kann."""
        return (
            self.has_all_required_certificates()
            and self.status not in ["Abgeschlossen", "Ausschuss"]
            and self.visual_inspector is not None
        )

    def get_unique_identifier(self) -> str:
        """Gibt eindeutigen Identifier für Rückverfolgbarkeit zurück."""
        return f"{self.article_number}#{self.batch_number}#{self.delivery_number}"

    def get_composite_key(self) -> tuple:
        """Gibt den Composite Primary Key als Tuple zurück."""
        return (self.article_number, self.batch_number, self.delivery_number)

    def get_traceability_info(self) -> dict:
        """Gibt vollständige Rückverfolgbarkeits-Informationen zurück."""
        return {
            "article_number": self.article_number,
            "batch_number": self.batch_number,
            "delivery_number": self.delivery_number,
            "order_number": self.order_number,
            "unique_identifier": self.get_unique_identifier(),
            "quantity_info": {
                "ordered": self.ordered_quantity,
                "delivery_slip": self.delivery_slip_quantity,
                "delivered": self.delivered_quantity,
                "good": self.get_good_quantity(),
                "waste": self.waste_quantity,
                "order_discrepancy": self.get_quantity_difference(),
                "slip_discrepancy": self.get_slip_difference(),
            },
        }
