# src/warehouse/domain/repositories/order_repository.py

"""
Order Repository Interface für das Warehouse Management System.

ERWEITERT um Domain Object Methoden für Clean Architecture Migration.
Neu erstellt da Order Repository vorher nicht vorhanden war.

Definiert spezifische Datenzugriffs-Methoden für Order-Entities.
Fokus auf Bestellungsmanagement und Order-Item Tracking.
"""

from abc import abstractmethod
from typing import List, Optional
from datetime import datetime, date

from warehouse.domain.repositories.base_repository import BaseRepository
from warehouse.domain.entities.order import Order, OrderItem


class OrderRepository(BaseRepository[Order]):
    """
    Repository Interface für Order-Entities.

    Erweitert BaseRepository um Order-spezifische Abfrage-Methoden
    für Bestellungsmanagement und Order-Item Tracking.

    Domain Object Methoden für Clean Architecture.
    """

    # === DOMAIN OBJECT METHODS ===

    @abstractmethod
    def save_domain(self, order: Order) -> str:
        """
        Speichert Order Domain Entity.

        Args:
            order: Order Domain Entity

        Returns:
            order_number der gespeicherten Order
        """

    @abstractmethod
    def find_domain_by_order_number(self, order_number: str) -> Optional[Order]:
        """
        Sucht Order Domain Entity per Bestellnummer.

        Args:
            order_number: Bestellnummer

        Returns:
            Order Domain Entity oder None
        """

    @abstractmethod
    def find_domain_by_supplier(self, supplier_id: str) -> List[Order]:
        """
        Sucht alle Order Domain Entities eines Lieferanten.

        Args:
            supplier_id: Lieferanten-ID

        Returns:
            Liste von Order Domain Entities
        """

    @abstractmethod
    def find_domain_by_status(self, is_completed: bool) -> List[Order]:
        """
        Sucht Order Domain Entities nach Completion-Status.

        Args:
            is_completed: True für abgeschlossene, False für offene Orders

        Returns:
            Liste von Order Domain Entities
        """

    @abstractmethod
    def find_domain_all(self) -> List[Order]:
        """
        Gibt alle Orders als Domain Entities zurück.

        Returns:
            Liste aller Order Domain Entities
        """

    @abstractmethod
    def delete_domain(self, order_number: str) -> bool:
        """
        Löscht Order Domain Entity.

        Args:
            order_number: Bestellnummer

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """

    @abstractmethod
    def exists_domain(self, order_number: str) -> bool:
        """
        Prüft ob Order Domain Entity existiert.

        Args:
            order_number: Bestellnummer

        Returns:
            True wenn existiert
        """

    # === CONVENIENCE METHODS ===

    @abstractmethod
    def find_domain_by_employee(self, employee_name: str) -> List[Order]:
        """
        Sucht Orders eines Mitarbeiters als Domain Entities.

        Args:
            employee_name: Name des Mitarbeiters

        Returns:
            Liste von Order Domain Entities
        """

    @abstractmethod
    def find_domain_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Order]:
        """
        Sucht Orders in Datumsbereich als Domain Entities.

        Args:
            start_date: Startdatum
            end_date: Enddatum

        Returns:
            Liste von Order Domain Entities
        """

    @abstractmethod
    def find_domain_overdue(self) -> List[Order]:
        """
        Sucht überfällige Orders als Domain Entities.

        Returns:
            Liste von überfälligen Order Domain Entities
        """

    @abstractmethod
    def find_domain_recent(self, limit: int = 10) -> List[Order]:
        """
        Sucht die neuesten Orders als Domain Entities.

        Args:
            limit: Maximale Anzahl

        Returns:
            Liste der neuesten Order Domain Entities
        """

    # === ORDER ITEM MANAGEMENT ===

    @abstractmethod
    def add_order_item_to_order(
        self,
        order_number: str,
        article_number: str,
        ordered_quantity: int,
        unit_description: str = "",
        notes: str = "",
    ) -> bool:
        """
        Fügt OrderItem zu einer Order hinzu.

        Args:
            order_number: Bestellnummer
            article_number: Artikelnummer
            ordered_quantity: Bestellmenge
            unit_description: Einheitenbeschreibung
            notes: Notizen

        Returns:
            True wenn erfolgreich hinzugefügt
        """

    @abstractmethod
    def remove_order_item_from_order(
        self, order_number: str, article_number: str
    ) -> bool:
        """
        Entfernt OrderItem aus einer Order.

        Args:
            order_number: Bestellnummer
            article_number: Artikelnummer

        Returns:
            True wenn erfolgreich entfernt
        """

    @abstractmethod
    def update_order_item_quantity(
        self, order_number: str, article_number: str, new_quantity: int
    ) -> bool:
        """
        Aktualisiert Menge eines OrderItems.

        Args:
            order_number: Bestellnummer
            article_number: Artikelnummer
            new_quantity: Neue Menge

        Returns:
            True wenn erfolgreich aktualisiert
        """

    @abstractmethod
    def find_order_items_by_order(self, order_number: str) -> List[OrderItem]:
        """
        Sucht alle OrderItems einer Order.

        Args:
            order_number: Bestellnummer

        Returns:
            Liste von OrderItem Domain Objects
        """

    # === SEARCH & FILTERING ===

    @abstractmethod
    def search_orders(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Order]:
        """
        Volltextsuche in Orders.

        Args:
            search_term: Suchbegriff
            search_fields: Felder für Suche (None = alle durchsuchbaren Felder)

        Returns:
            Liste der gefundenen Orders
        """

    @abstractmethod
    def find_by_advanced_criteria(self, criteria: dict) -> List[Order]:
        """
        Erweiterte Suche mit komplexen Kriterien.

        Args:
            criteria: Erweiterte Suchkriterien

        Returns:
            Liste der gefundenen Orders
        """

    @abstractmethod
    def find_orders_containing_article(self, article_number: str) -> List[Order]:
        """
        Sucht Orders die einen bestimmten Artikel enthalten.

        Args:
            article_number: Artikelnummer

        Returns:
            Liste von Orders die den Artikel enthalten
        """

    # === STATUS & LIFECYCLE MANAGEMENT ===

    @abstractmethod
    def complete_order(self, order_number: str, completed_by: str) -> bool:
        """
        Schließt eine Order ab.

        Args:
            order_number: Bestellnummer
            completed_by: Mitarbeiter der abschließt

        Returns:
            True wenn erfolgreich abgeschlossen
        """

    @abstractmethod
    def reopen_order(self, order_number: str, reopened_by: str) -> bool:
        """
        Öffnet eine abgeschlossene Order wieder.

        Args:
            order_number: Bestellnummer
            reopened_by: Mitarbeiter der wieder öffnet

        Returns:
            True wenn erfolgreich wieder geöffnet
        """

    # === ANALYTICS & STATISTICS ===

    @abstractmethod
    def get_order_statistics(self) -> dict:
        """
        Gibt Order-Statistiken zurück.

        Returns:
            Dictionary mit Order-Statistiken
        """

    @abstractmethod
    def get_supplier_order_statistics(self) -> dict:
        """
        Gibt Order-Statistiken pro Lieferant zurück.

        Returns:
            Dictionary mit Lieferant -> Order-Statistiken
        """

    @abstractmethod
    def get_order_volume_by_month(self, year: int) -> dict:
        """
        Gibt monatliche Order-Volumina für ein Jahr zurück.

        Args:
            year: Jahr für Statistik

        Returns:
            Dictionary mit Monat -> Anzahl Orders
        """

    @abstractmethod
    def get_employee_order_statistics(self) -> dict:
        """
        Gibt Order-Statistiken pro Mitarbeiter zurück.

        Returns:
            Dictionary mit Mitarbeiter -> Order-Statistiken
        """

    @abstractmethod
    def get_completion_rate_statistics(self) -> dict:
        """
        Gibt Abschlussraten-Statistiken zurück.

        Returns:
            Dictionary mit Completion-Metriken
        """

    # === DELIVERY COMPARISON ===

    @abstractmethod
    def compare_order_with_deliveries(self, order_number: str) -> dict:
        """
        Vergleicht Order mit tatsächlichen Deliveries.

        Args:
            order_number: Bestellnummer

        Returns:
            Dictionary mit Vergleichsdaten (bestellt vs. geliefert)
        """

    @abstractmethod
    def find_orders_with_delivery_discrepancies(self) -> List[Order]:
        """
        Sucht Orders mit Liefer-Abweichungen.

        Returns:
            Liste von Orders mit Mengen-/Artikel-Abweichungen
        """

    @abstractmethod
    def find_orders_fully_delivered(self) -> List[Order]:
        """
        Sucht Orders die vollständig geliefert wurden.

        Returns:
            Liste von vollständig gelieferten Orders
        """

    @abstractmethod
    def find_orders_partially_delivered(self) -> List[Order]:
        """
        Sucht Orders die nur teilweise geliefert wurden.

        Returns:
            Liste von teilweise gelieferten Orders
        """

    # === VALIDATION ===

    @abstractmethod
    def validate_order_for_completion(self, order_number: str) -> List[str]:
        """
        Validiert Order für Abschluss.

        Args:
            order_number: Bestellnummer

        Returns:
            Liste von Validierungsfehlern (leer = OK)
        """

    @abstractmethod
    def order_number_exists(self, order_number: str) -> bool:
        """
        Prüft ob Bestellnummer bereits existiert.

        Args:
            order_number: Bestellnummer

        Returns:
            True wenn bereits vorhanden
        """
