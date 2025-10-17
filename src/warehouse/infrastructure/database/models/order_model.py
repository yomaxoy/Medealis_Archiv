# src/warehouse/infrastructure/database/models/order_model.py

"""
Order Model für Bestellungen.
ERWEITERT um Items-Beziehung für vollständige Rückverfolgbarkeit.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship

from warehouse.infrastructure.database.connection import Base


class OrderModel(Base):
    """
    Order Model - Bestellungen bei Lieferanten.
    Primary Key: order_number (Business Key)
    ERWEITERT um Items-Beziehung.
    """

    __tablename__ = "orders"
    __table_args__ = {'extend_existing': True}

    # === PRIMÄRSCHLÜSSEL (Business Key) ===
    order_number = Column(String(10), primary_key=True)  # "ORD001", "B24001"

    # === AUDIT FIELDS ===
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # === BESTELLDATEN ===
    supplier_id = Column(String(5), nullable=True, index=True)
    order_date = Column(Date, nullable=False, index=True)
    expected_delivery_date = Column(Date, nullable=True)

    # === VERARBEITUNG ===
    employee_name = Column(String(100), nullable=False)

    # === STATUS ===
    status = Column(String(50), nullable=False, default="Offen")  # Offen, Abgeschlossen

    # === METADATEN ===
    notes = Column(Text, nullable=True)

    # === BEZIEHUNGEN ===
    # Temporarily disabled due to SQLAlchemy registry conflicts
    # supplier = relationship("SupplierModel", back_populates="orders", lazy="select")
    # order_items = relationship("OrderItemModel", back_populates="order", cascade="all, delete-orphan", lazy="select")
    # items = relationship("ItemModel", back_populates="order", lazy="select")  # ← NEU: Beziehung zu tatsächlich gelieferten Items

    def __repr__(self):
        return f"OrderModel({self.order_number}, {self.supplier_id}, {self.status})"

    def get_summary(self) -> str:
        """Kurze Zusammenfassung für UI."""
        return f"{self.order_number} ({self.supplier_id}) - {self.status}"

    # === NEU: BUSINESS LOGIC FÜR ORDER-ITEM MATCHING ===

    def get_delivered_items(self) -> list:
        """Gibt alle tatsächlich gelieferten Items dieser Bestellung zurück."""
        return self.items or []

    def get_delivery_status_summary(self) -> dict:
        """Vergleicht bestellte vs. gelieferte Items."""
        ordered_items = {
            item.article_number: item.ordered_quantity for item in self.order_items
        }
        delivered_items = {}

        # Summiere gelieferte Mengen nach Artikel
        for item in self.get_delivered_items():
            article = item.article_number
            delivered_items[article] = (
                delivered_items.get(article, 0) + item.delivery_quantity
            )

        # Vergleiche
        summary = {
            "ordered_articles": len(ordered_items),
            "delivered_articles": len(delivered_items),
            "fully_delivered": [],
            "partially_delivered": [],
            "missing": [],
            "unexpected": [],
        }

        # Analyse
        for article, ordered_qty in ordered_items.items():
            delivered_qty = delivered_items.get(article, 0)

            if delivered_qty == 0:
                summary["missing"].append({"article": article, "ordered": ordered_qty})
            elif delivered_qty == ordered_qty:
                summary["fully_delivered"].append(
                    {"article": article, "quantity": delivered_qty}
                )
            else:
                summary["partially_delivered"].append(
                    {
                        "article": article,
                        "ordered": ordered_qty,
                        "delivered": delivered_qty,
                        "difference": delivered_qty - ordered_qty,
                    }
                )

        # Unerwartete Lieferungen
        for article, delivered_qty in delivered_items.items():
            if article not in ordered_items:
                summary["unexpected"].append(
                    {"article": article, "delivered": delivered_qty}
                )

        return summary


class OrderItemModel(Base):
    """
    Order Item Model - Einzelne Artikel in einer Bestellung.
    """

    __tablename__ = "order_items"
    __table_args__ = {'extend_existing': True}

    # === PRIMÄRSCHLÜSSEL ===
    id = Column(Integer, primary_key=True, autoincrement=True)

    # === AUDIT FIELDS ===
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # === BEZIEHUNGEN ===
    order_number = Column(
        String(10), ForeignKey("orders.order_number"), nullable=False, index=True
    )
    article_number = Column(String(7), nullable=False)  # Keine FK zu ItemInfo

    # === BESTELLDATEN ===
    ordered_quantity = Column(Integer, nullable=False)
    unit_description = Column(String(100), nullable=True)  # "Stück", "Karton"

    # === METADATEN ===
    notes = Column(Text, nullable=True)

    # === BEZIEHUNGEN ===
    # Temporarily disabled due to SQLAlchemy registry conflicts
    # order = relationship("OrderModel", back_populates="order_items", lazy="select")

    def __repr__(self):
        return f"OrderItemModel({self.order_number}, {self.article_number}, {self.ordered_quantity})"
