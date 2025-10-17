# src/warehouse/domain/entities/order.py

"""
Order Entity für das Warehouse Management System.

Repräsentiert Bestellungen, die bei Lieferanten aufgegeben wurden.
Wichtig für die Verknüpfung zwischen erwarteten und tatsächlich
gelieferten Artikeln.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict, Any, List

# from warehouse.domain.enums.item_status import ItemStatus


@dataclass
class OrderItem:
    """Value Object für einen bestellten Artikel."""

    article_number: str
    ordered_quantity: int
    expected_delivery_date: Optional[date] = None
    unit_description: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if self.ordered_quantity <= 0:
            raise ValueError("Bestellmenge muss größer als 0 sein")


class Order:
    """
    Entity für Bestellungen im Warehouse Management System.

    Verwaltet Bestellungen bei Lieferanten und ermöglicht den Abgleich
    zwischen bestellten und gelieferten Artikeln für bessere Kontrolle
    und Rückverfolgbarkeit.
    """

    def __init__(
        self,
        order_number: str,
        supplier_id: str,
        order_date: date,
        employee_name: str,
        expected_delivery_date: Optional[date] = None,
    ):
        # === KERN-IDENTIFIKATOREN ===
        self.order_number = order_number
        self.supplier_id = supplier_id
        self.order_date = order_date

        # === BESTELLINFORMATIONEN ===
        self.employee_name = employee_name
        self.expected_delivery_date = expected_delivery_date

        # === LIFECYCLE ===
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # === BESTELLPOSITIONEN ===
        self.order_items: List[OrderItem] = []

        # === STATUS UND METADATEN ===
        self.is_completed = False
        self.completed_at: Optional[datetime] = None
        self.notes: str = ""

    # === ORDER ITEM MANAGEMENT ===

    def add_order_item(
        self,
        article_number: str,
        ordered_quantity: int,
        expected_delivery_date: Optional[date] = None,
        unit_description: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> OrderItem:
        """
        Fügt einen Artikel zur Bestellung hinzu.

        Args:
            article_number: Artikelnummer
            ordered_quantity: Bestellte Menge
            expected_delivery_date: Erwartetes Lieferdatum
            unit_description: Einheitenbeschreibung
            notes: Notizen zum Artikel

        Returns:
            Erstelltes OrderItem

        Raises:
            ValueError: Wenn Artikel bereits in Bestellung vorhanden
        """
        if self.is_completed:
            raise ValueError("Abgeschlossene Bestellung kann nicht geändert werden")

        # Prüfe auf Duplikate
        existing_item = self.find_order_item(article_number)
        if existing_item:
            raise ValueError(f"Artikel {article_number} ist bereits in der Bestellung")

        order_item = OrderItem(
            article_number=article_number,
            ordered_quantity=ordered_quantity,
            expected_delivery_date=expected_delivery_date
            or self.expected_delivery_date,
            unit_description=unit_description,
            notes=notes,
        )

        self.order_items.append(order_item)
        self._update_timestamp()

        return order_item

    def find_order_item(self, article_number: str) -> Optional[OrderItem]:
        """
        Sucht ein OrderItem anhand der Artikelnummer.

        Args:
            article_number: Zu suchende Artikelnummer

        Returns:
            Gefundenes OrderItem oder None
        """
        for item in self.order_items:
            if item.article_number == article_number:
                return item
        return None

    def update_order_item_quantity(
        self, article_number: str, new_quantity: int
    ) -> bool:
        """
        Aktualisiert die bestellte Menge eines Artikels.

        Args:
            article_number: Artikelnummer
            new_quantity: Neue Bestellmenge

        Returns:
            True wenn erfolgreich aktualisiert

        Raises:
            ValueError: Bei ungültiger Menge oder abgeschlossener Bestellung
        """
        if self.is_completed:
            raise ValueError("Abgeschlossene Bestellung kann nicht geändert werden")

        if new_quantity <= 0:
            raise ValueError("Bestellmenge muss größer als 0 sein")

        order_item = self.find_order_item(article_number)
        if order_item:
            order_item.ordered_quantity = new_quantity
            self._update_timestamp()
            return True
        return False

    def remove_order_item(self, article_number: str) -> bool:
        """
        Entfernt einen Artikel aus der Bestellung.

        Args:
            article_number: Zu entfernende Artikelnummer

        Returns:
            True wenn erfolgreich entfernt

        Raises:
            ValueError: Bei abgeschlossener Bestellung
        """
        if self.is_completed:
            raise ValueError("Abgeschlossene Bestellung kann nicht geändert werden")

        order_item = self.find_order_item(article_number)
        if order_item:
            self.order_items.remove(order_item)
            self._update_timestamp()
            return True
        return False

    # === ORDER STATUS MANAGEMENT ===

    def complete_order(self, completed_by: str) -> None:
        """
        Schließt die Bestellung ab.

        Args:
            completed_by: Name des Mitarbeiters, der die Bestellung abschließt

        Raises:
            ValueError: Wenn Bestellung bereits abgeschlossen oder leer
        """
        if self.is_completed:
            raise ValueError("Bestellung ist bereits abgeschlossen")

        if not self.order_items:
            raise ValueError("Leere Bestellung kann nicht abgeschlossen werden")

        self.is_completed = True
        self.completed_at = datetime.now()
        self.employee_name = completed_by
        self._update_timestamp()

    def reopen_order(self, reopened_by: str) -> None:
        """
        Öffnet eine abgeschlossene Bestellung wieder.

        Args:
            reopened_by: Name des Mitarbeiters, der die Bestellung wieder öffnet
        """
        if not self.is_completed:
            raise ValueError("Bestellung ist nicht abgeschlossen")

        self.is_completed = False
        self.completed_at = None
        self.employee_name = reopened_by
        self._update_timestamp()

    # === BUSINESS LOGIC ===

    def get_total_items_count(self) -> int:
        """
        Gibt die Anzahl verschiedener Artikel in der Bestellung zurück.

        Returns:
            Anzahl der OrderItems
        """
        return len(self.order_items)

    def get_total_quantity(self) -> int:
        """
        Gibt die Gesamtmenge aller bestellten Artikel zurück.

        Returns:
            Summe aller bestellten Mengen
        """
        return sum(item.ordered_quantity for item in self.order_items)

    def is_overdue(self) -> bool:
        """
        Prüft, ob die Bestellung überfällig ist.

        Returns:
            True wenn erwartetes Lieferdatum überschritten und nicht abgeschlossen
        """
        if self.is_completed or not self.expected_delivery_date:
            return False

        today = date.today()
        return today > self.expected_delivery_date

    def days_until_expected_delivery(self) -> Optional[int]:
        """
        Berechnet Tage bis zum erwarteten Lieferdatum.

        Returns:
            Anzahl Tage (negativ = überfällig) oder None wenn kein Datum gesetzt
        """
        if not self.expected_delivery_date:
            return None

        today = date.today()
        delta = self.expected_delivery_date - today
        return delta.days

    def has_article(self, article_number: str) -> bool:
        """
        Prüft, ob ein bestimmter Artikel bestellt wurde.

        Args:
            article_number: Zu prüfende Artikelnummer

        Returns:
            True wenn Artikel in Bestellung enthalten
        """
        return self.find_order_item(article_number) is not None

    def get_ordered_quantity_for_article(self, article_number: str) -> int:
        """
        Gibt die bestellte Menge für einen Artikel zurück.

        Args:
            article_number: Artikelnummer

        Returns:
            Bestellte Menge oder 0 wenn Artikel nicht bestellt
        """
        order_item = self.find_order_item(article_number)
        return order_item.ordered_quantity if order_item else 0

    # === DELIVERY COMPARISON ===

    def compare_with_delivery(
        self, delivery_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Vergleicht Bestellung mit gelieferten Artikeln.

        Args:
            delivery_items: Liste von Delivery Items (dict mit article_number, quantity)

        Returns:
            Dictionary mit Vergleichsstatistiken
        """
        comparison: Dict[str, List[Any]] = {
            "matched_items": [],
            "missing_items": [],
            "unexpected_items": [],
            "quantity_mismatches": [],
        }

        # Erstelle Sets für Vergleich
        ordered_articles = {item.article_number for item in self.order_items}
        delivered_articles = {item["article_number"] for item in delivery_items}

        # Finde fehlende und unerwartete Artikel
        comparison["missing_items"] = list(ordered_articles - delivered_articles)
        comparison["unexpected_items"] = list(delivered_articles - ordered_articles)

        # Vergleiche Mengen für gemeinsame Artikel
        common_articles = ordered_articles & delivered_articles

        for article_number in common_articles:
            ordered_qty = self.get_ordered_quantity_for_article(article_number)
            delivered_qty = next(
                item["quantity"]
                for item in delivery_items
                if item["article_number"] == article_number
            )

            if ordered_qty == delivered_qty:
                comparison["matched_items"].append(
                    {"article_number": article_number, "quantity": ordered_qty}
                )
            else:
                comparison["quantity_mismatches"].append(
                    {
                        "article_number": article_number,
                        "ordered_quantity": ordered_qty,
                        "delivered_quantity": delivered_qty,
                        "difference": delivered_qty - ordered_qty,
                    }
                )

        return comparison

    # === UTILITY METHODS ===

    def _update_timestamp(self):
        """Aktualisiert den Timestamp bei Änderungen."""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für Persistierung."""
        return {
            "order_number": self.order_number,
            "supplier_id": self.supplier_id,
            "order_date": self.order_date.isoformat(),
            "employee_name": self.employee_name,
            "expected_delivery_date": (
                self.expected_delivery_date.isoformat()
                if self.expected_delivery_date
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_completed": self.is_completed,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "notes": self.notes,
            "order_items": [
                {
                    "article_number": item.article_number,
                    "ordered_quantity": item.ordered_quantity,
                    "expected_delivery_date": (
                        item.expected_delivery_date.isoformat()
                        if item.expected_delivery_date
                        else None
                    ),
                    "unit_description": item.unit_description,
                    "notes": item.notes,
                }
                for item in self.order_items
            ],
        }

    def get_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Bestellung zurück."""
        return {
            "order_number": self.order_number,
            "supplier_id": self.supplier_id,
            "order_date": self.order_date,
            "expected_delivery_date": self.expected_delivery_date,
            "is_completed": self.is_completed,
            "total_items": self.get_total_items_count(),
            "total_quantity": self.get_total_quantity(),
            "is_overdue": self.is_overdue(),
            "days_until_delivery": self.days_until_expected_delivery(),
        }

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        status = "Abgeschlossen" if self.is_completed else "Offen"
        return f"Order({self.order_number}, {self.supplier_id}, {status})"

    def __repr__(self) -> str:
        """Debug-Repräsentation."""
        return (
            f"Order(order_number='{self.order_number}', "
            f"supplier_id='{self.supplier_id}', "
            f"is_completed={self.is_completed}, "
            f"items_count={len(self.order_items)})"
        )
