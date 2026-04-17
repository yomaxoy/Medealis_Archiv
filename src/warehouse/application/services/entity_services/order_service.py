# src/warehouse/application/services/order_service.py

"""
Order Service - Application Layer für das Warehouse Management System.

Orchestriert Order-bezogene Use Cases und verbindet Domain Logic
mit Infrastructure. Angepasst an deine exakte Projektstruktur.
"""

# Standard library imports
import logging
from datetime import date
from typing import Dict, Any, List, Optional

# Domain imports
from warehouse.domain.entities.order import Order  # , OrderItem
from warehouse.domain.entities.supplier import Supplier
from warehouse.domain.exceptions.order_exceptions import (
    OrderAlreadyExistsException,
    OrderNotFoundException,
    OrderAlreadyCompletedException,
    OrderNotCompletedException,
    EmptyOrderException,
    #  OrderItemAlreadyExistsException,
    OrderItemNotFoundException,
)

# Infrastructure imports
from warehouse.infrastructure.database.repositories.sql_order_rep_domain import (
    SQLAlchemyOrderRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.sql_supplier_rep_domain import (
    SQLAlchemySupplierRepositoryDomain,
)

logger = logging.getLogger(__name__)


class OrderService:
    """
    Application Service für Order-Management.

    Verwaltet den kompletten Lebenszyklus von Bestellungen:
    - Erstellung neuer Orders
    - Hinzufügen/Entfernen von OrderItems
    - Status-Management (offen/abgeschlossen)
    - Delivery-Vergleich und Tracking
    """

    def __init__(self):
        try:
            self.order_repo = SQLAlchemyOrderRepositoryDomain()
            self.supplier_repo = SQLAlchemySupplierRepositoryDomain()
            logger.info("OrderService erfolgreich initialisiert")
        except (ImportError, AttributeError, ConnectionError) as e:
            logger.error("Fehler bei OrderService Initialisierung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei OrderService Initialisierung: %s", e)
            raise

    # === ORDER CREATION & MANAGEMENT ===

    def create_order(
        self,
        order_number: str,
        supplier_id: str,
        order_date: date,
        employee_name: str,
        expected_delivery_date: Optional[date] = None,
    ) -> str:
        """
        Erstellt eine neue Order.

        Args:
            order_number: Eindeutige Bestellnummer
            supplier_id: Lieferanten-ID
            order_date: Bestelldatum
            employee_name: Bearbeitender Mitarbeiter
            expected_delivery_date: Erwartetes Lieferdatum (optional)

        Returns:
            Bestellnummer der erstellten Order
        """
        try:
            logger.info("Erstelle neue Order: %s", order_number)

            # Prüfe, ob Order bereits existiert
            if self.order_repo.exists_domain(order_number):
                raise OrderAlreadyExistsException(order_number)

            # Prüfe, ob Supplier existiert
            supplier = self.supplier_repo.find_domain_by_supplier_id(supplier_id)
            if not supplier:
                logger.warning(
                    "Supplier %s nicht gefunden - erstelle automatisch", supplier_id
                )
                # Erstelle Basic Supplier falls nicht vorhanden
                new_supplier = Supplier(
                    supplier_id=supplier_id, name=f"Supplier {supplier_id}"
                )
                self.supplier_repo.save_domain(new_supplier)

            # Erstelle Order Domain Entity
            order = Order(
                order_number=order_number,
                supplier_id=supplier_id,
                order_date=order_date,
                employee_name=employee_name,
                expected_delivery_date=expected_delivery_date,
            )

            # Persistiere in Database
            saved_order_number = self.order_repo.save_domain(order)

            logger.info("Order %s erfolgreich erstellt", order_number)
            return saved_order_number

        except (OrderAlreadyExistsException, ValueError) as e:
            logger.error(
                "Geschäftslogik-Fehler beim Erstellen der Order %s: %s", order_number, e
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Erstellen der Order %s: %s", order_number, e
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Erstellen der Order %s: %s", order_number, e
            )
            raise

    def get_order(self, order_number: str) -> Optional[Dict[str, Any]]:
        """
        Holt eine Order mit allen Details.

        Args:
            order_number: Bestellnummer

        Returns:
            Dictionary mit Order-Daten oder None
        """
        try:
            order = self.order_repo.find_domain_by_order_number(order_number)
            if not order:
                return None

            return {
                "order_number": order.order_number,
                "supplier_id": order.supplier_id,
                "order_date": order.order_date.isoformat(),
                "employee_name": order.employee_name,
                "expected_delivery_date": (
                    order.expected_delivery_date.isoformat()
                    if order.expected_delivery_date
                    else None
                ),
                "is_completed": order.is_completed,
                "completed_at": (
                    order.completed_at.isoformat() if order.completed_at else None
                ),
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "notes": order.notes,
                "total_items": order.get_total_items_count(),
                "total_quantity": order.get_total_quantity(),
                "is_overdue": order.is_overdue(),
                "days_until_delivery": order.days_until_expected_delivery(),
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
                    for item in order.order_items
                ],
            }

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Order %s: %s", order_number, e
            )
            return None
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der Order %s: %s", order_number, e
            )
            return None

    # === ORDER ITEM MANAGEMENT ===

    def add_item_to_order(
        self,
        order_number: str,
        article_number: str,
        ordered_quantity: int,
        expected_delivery_date: Optional[date] = None,
        unit_description: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Fügt ein OrderItem zu einer Order hinzu.

        Args:
            order_number: Bestellnummer
            article_number: Artikelnummer
            ordered_quantity: Bestellmenge
            expected_delivery_date: Erwartetes Lieferdatum (optional)
            unit_description: Einheitenbeschreibung (optional)
            notes: Notizen (optional)

        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            logger.info(
                "Füge Artikel %s zu Order %s hinzu", article_number, order_number
            )

            # Lade Order
            order = self.order_repo.find_domain_by_order_number(order_number)
            if not order:
                raise OrderNotFoundException(order_number)

            # Prüfe ob Order abgeschlossen
            if order.is_completed:
                raise OrderAlreadyCompletedException(order_number)

            # Füge Item über Domain Logic hinzu
            order.add_order_item(
                article_number=article_number,
                ordered_quantity=ordered_quantity,
                expected_delivery_date=expected_delivery_date,
                unit_description=unit_description,
                notes=notes,
            )

            # Persistiere Order (mit Items)
            self.order_repo.save_domain(order)

            logger.info(
                "Artikel %s erfolgreich zu Order %s hinzugefügt",
                article_number,
                order_number,
            )
            return True

        except (
            OrderNotFoundException,
            OrderAlreadyCompletedException,
            ValueError,
        ) as e:
            logger.error("Geschäftslogik-Fehler beim Hinzufügen des OrderItems: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Hinzufügen des OrderItems: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Hinzufügen des OrderItems: %s", e)
            raise

    def remove_item_from_order(self, order_number: str, article_number: str) -> bool:
        """
        Entfernt ein OrderItem aus einer Order.

        Args:
            order_number: Bestellnummer
            article_number: Artikelnummer

        Returns:
            True wenn erfolgreich entfernt
        """
        try:
            logger.info(
                "Entferne Artikel %s aus Order %s", article_number, order_number
            )

            # Lade Order
            order = self.order_repo.find_domain_by_order_number(order_number)
            if not order:
                raise OrderNotFoundException(order_number)

            # Prüfe ob Order abgeschlossen
            if order.is_completed:
                raise OrderAlreadyCompletedException(order_number)

            # Prüfe ob Artikel existiert
            if not order.has_article(article_number):
                raise OrderItemNotFoundException(order_number, article_number)

            # Entferne Item über Domain Logic
            success = order.remove_order_item(article_number)

            if success:
                # Persistiere Order
                self.order_repo.save_domain(order)
                logger.info(
                    "Artikel %s erfolgreich aus Order %s entfernt",
                    article_number,
                    order_number,
                )

            return success

        except (
            OrderNotFoundException,
            OrderAlreadyCompletedException,
            OrderItemNotFoundException,
            ValueError,
        ) as e:
            logger.error("Geschäftslogik-Fehler beim Entfernen des OrderItems: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Entfernen des OrderItems: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Entfernen des OrderItems: %s", e)
            raise

    def update_item_quantity(
        self, order_number: str, article_number: str, new_quantity: int
    ) -> bool:
        """
        Aktualisiert die Menge eines OrderItems.

        Args:
            order_number: Bestellnummer
            article_number: Artikelnummer
            new_quantity: Neue Bestellmenge

        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            logger.info(
                "Aktualisiere Menge für Artikel %s in Order %s auf %d",
                article_number,
                order_number,
                new_quantity,
            )

            # Lade Order
            order = self.order_repo.find_domain_by_order_number(order_number)
            if not order:
                raise OrderNotFoundException(order_number)

            # Prüfe ob Order abgeschlossen
            if order.is_completed:
                raise OrderAlreadyCompletedException(order_number)

            # Prüfe ob Artikel existiert
            if not order.has_article(article_number):
                raise OrderItemNotFoundException(order_number, article_number)

            # Update über Domain Logic
            success = order.update_order_item_quantity(article_number, new_quantity)

            if success:
                # Persistiere Order
                self.order_repo.save_domain(order)
                logger.info(
                    "Menge für Artikel %s in Order %s erfolgreich aktualisiert",
                    article_number,
                    order_number,
                )

            return success

        except (
            OrderNotFoundException,
            OrderAlreadyCompletedException,
            OrderItemNotFoundException,
            ValueError,
        ) as e:
            logger.error(
                "Geschäftslogik-Fehler beim Aktualisieren der OrderItem-Menge: %s", e
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Aktualisieren der OrderItem-Menge: %s", e
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Aktualisieren der OrderItem-Menge: %s", e
            )
            raise

    # === ORDER STATUS MANAGEMENT ===

    def complete_order(self, order_number: str, completed_by: str) -> bool:
        """
        Schließt eine Order ab.

        Args:
            order_number: Bestellnummer
            completed_by: Mitarbeiter der abschließt

        Returns:
            True wenn erfolgreich abgeschlossen
        """
        try:
            logger.info("Schließe Order %s ab", order_number)

            # Lade Order
            order = self.order_repo.find_domain_by_order_number(order_number)
            if not order:
                raise OrderNotFoundException(order_number)

            # Prüfe ob bereits abgeschlossen
            if order.is_completed:
                raise OrderAlreadyCompletedException(order_number)

            # Prüfe ob Order leer
            if not order.order_items:
                raise EmptyOrderException(order_number)

            # Complete über Domain Logic
            order.complete_order(completed_by)

            # Persistiere Order
            self.order_repo.save_domain(order)

            logger.info("Order %s erfolgreich abgeschlossen", order_number)
            return True

        except (
            OrderNotFoundException,
            OrderAlreadyCompletedException,
            EmptyOrderException,
            ValueError,
        ) as e:
            logger.error("Geschäftslogik-Fehler beim Abschließen der Order: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Abschließen der Order: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Abschließen der Order: %s", e)
            raise

    def reopen_order(self, order_number: str, reopened_by: str) -> bool:
        """
        Öffnet eine abgeschlossene Order wieder.

        Args:
            order_number: Bestellnummer
            reopened_by: Mitarbeiter der wieder öffnet

        Returns:
            True wenn erfolgreich wieder geöffnet
        """
        try:
            logger.info("Öffne Order %s wieder", order_number)

            # Lade Order
            order = self.order_repo.find_domain_by_order_number(order_number)
            if not order:
                raise OrderNotFoundException(order_number)

            # Prüfe ob nicht abgeschlossen
            if not order.is_completed:
                raise OrderNotCompletedException(order_number)

            # Reopen über Domain Logic
            order.reopen_order(reopened_by)

            # Persistiere Order
            self.order_repo.save_domain(order)

            logger.info("Order %s erfolgreich wieder geöffnet", order_number)
            return True

        except (OrderNotFoundException, OrderNotCompletedException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler beim Wiederöffnen der Order: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Wiederöffnen der Order: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Wiederöffnen der Order: %s", e)
            raise

    # === ORDER SEARCH & FILTERING ===

    def get_all_orders(
        self, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Holt alle Orders mit optionalem Status-Filter.

        Args:
            status_filter: "open", "completed", oder None für alle

        Returns:
            Liste von Order-Dictionaries
        """
        try:
            if status_filter == "open":
                orders = self.order_repo.find_domain_by_status(False)
            elif status_filter == "completed":
                orders = self.order_repo.find_domain_by_status(True)
            else:
                orders = self.order_repo.find_domain_all()

            return [order.get_summary() for order in orders]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden aller Orders: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden aller Orders: %s", e)
            return []

    def get_orders_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """
        Holt alle Orders eines Lieferanten.

        Args:
            supplier_id: Lieferanten-ID

        Returns:
            Liste von Order-Dictionaries
        """
        try:
            orders = self.order_repo.find_domain_by_supplier(supplier_id)
            return [order.get_summary() for order in orders]

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Orders für Supplier %s: %s",
                supplier_id,
                e,
            )
            return []
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der Orders für Supplier %s: %s",
                supplier_id,
                e,
            )
            return []

    def get_orders_by_employee(self, employee_name: str) -> List[Dict[str, Any]]:
        """
        Holt alle Orders eines Mitarbeiters.

        Args:
            employee_name: Mitarbeiter-Name

        Returns:
            Liste von Order-Dictionaries
        """
        try:
            orders = self.order_repo.find_domain_by_employee(employee_name)
            return [order.get_summary() for order in orders]

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Orders für Employee %s: %s",
                employee_name,
                e,
            )
            return []
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der Orders für Employee %s: %s",
                employee_name,
                e,
            )
            return []

    def get_overdue_orders(self) -> List[Dict[str, Any]]:
        """
        Holt alle überfälligen Orders.

        Returns:
            Liste von überfälligen Order-Dictionaries
        """
        try:
            orders = self.order_repo.find_domain_overdue()
            return [order.get_summary() for order in orders]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden überfälliger Orders: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden überfälliger Orders: %s", e)
            return []

    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Holt die neuesten Orders."""
        try:
            orders = self.order_repo.find_domain_recent(limit)
            return [order.get_summary() for order in orders]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden aktueller Orders: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden aktueller Orders: %s", e)
            return []

    def search_orders(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Volltext-Suche in Orders.

        Args:
            search_term: Suchbegriff

        Returns:
            Liste von gefundenen Order-Dictionaries
        """
        try:
            orders = self.order_repo.search_orders(search_term)
            return [order.get_summary() for order in orders]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Order-Suche: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Order-Suche: %s", e)
            return []

    # === ORDER UTILITIES ===

    def order_exists(self, order_number: str) -> bool:
        """Prüft, ob eine Order existiert."""
        return self.order_repo.exists_domain(order_number)

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Holt alle Orders für die GUI-Liste.
        
        Returns:
            Liste von Order-Dictionaries
        """
        try:
            orders = self.order_repo.find_domain_all()
            order_list = []
            
            for order in orders:
                order_dict = {
                    'order_number': order.order_number,
                    'supplier_id': order.supplier_id,
                    'order_date': order.order_date.isoformat() if order.order_date else None,
                    'expected_delivery_date': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                    'status': 'Abgeschlossen' if order.is_completed else 'Offen',
                    'employee_name': order.employee_name,
                    'notes': order.notes,
                    'created_at': order.created_at.isoformat() if order.created_at else None
                }
                order_list.append(order_dict)
            
            return order_list
            
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden aller Orders: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden aller Orders: %s", e)
            return []

    def get_order_statistics(self) -> Dict[str, Any]:
        """Holt Order-Statistiken für Dashboard."""
        try:
            stats = self.order_repo.get_order_statistics()
            return stats

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Order-Statistiken: %s", e
            )
            return {}
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden der Order-Statistiken: %s", e)
            return {}

    # === DELIVERY COMPARISON ===

    def compare_order_with_deliveries(
        self, order_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Vergleicht eine Order mit tatsächlichen Deliveries.

        Args:
            order_number: Bestellnummer

        Returns:
            Dictionary mit Vergleichsdaten oder None
        """
        try:
            comparison = self.order_repo.compare_order_with_deliveries(order_number)
            return comparison

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Order-Delivery Vergleich für %s: %s",
                order_number,
                e,
            )
            return None
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Order-Delivery Vergleich für %s: %s",
                order_number,
                e,
            )
            return None

    def update_order(
        self,
        order_number: str,
        supplier_id: Optional[str] = None,
        order_date: Optional[date] = None,
        expected_delivery_date: Optional[date] = None,
        employee_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Aktualisiert Order-Grunddaten.

        Args:
            order_number: Bestellnummer (unveränderlich)
            supplier_id: Neue Lieferanten-ID (optional)
            order_date: Neues Bestelldatum (optional)
            expected_delivery_date: Neues erwartetes Lieferdatum (optional)
            employee_name: Neuer Mitarbeiter (optional)
            notes: Neue Notizen (optional)

        Returns:
            True wenn erfolgreich aktualisiert

        Raises:
            OrderNotFoundException: Wenn Order nicht existiert
            OrderAlreadyCompletedException: Wenn Order abgeschlossen ist
        """
        try:
            logger.info("Aktualisiere Order: %s", order_number)

            # Prüfe, ob Order existiert
            if not self.order_repo.exists_domain(order_number):
                raise OrderNotFoundException(order_number)

            # Lade existierende Order
            order = self.order_repo.get_domain(order_number)
            if not order:
                raise OrderNotFoundException(order_number)

            # Prüfe, ob Order bereits abgeschlossen ist
            if order.is_completed:
                raise OrderAlreadyCompletedException(order_number)

            # Aktualisiere nur die übergebenen Felder
            if supplier_id is not None:
                order.supplier_id = supplier_id
            if order_date is not None:
                order.order_date = order_date
            if expected_delivery_date is not None:
                order.expected_delivery_date = expected_delivery_date
            if employee_name is not None:
                order.employee_name = employee_name
            if notes is not None:
                order.notes = notes

            # Speichere aktualisierte Order
            success = self.order_repo.update_domain(order)

            if success:
                logger.info("Order %s erfolgreich aktualisiert", order_number)
            else:
                logger.warning("Order %s konnte nicht aktualisiert werden", order_number)

            return success

        except (OrderNotFoundException, OrderAlreadyCompletedException) as e:
            logger.error("Geschäftslogik-Fehler beim Aktualisieren der Order: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Aktualisieren der Order %s: %s", order_number, e)
            return False
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Aktualisieren der Order %s: %s", order_number, e)
            return False

    def delete_order(self, order_number: str) -> bool:
        """
        Löscht eine Order.

        Args:
            order_number: Bestellnummer

        Returns:
            True wenn erfolgreich gelöscht
        """
        try:
            logger.info("Lösche Order: %s", order_number)

            # Prüfe, ob Order existiert
            if not self.order_repo.exists_domain(order_number):
                raise OrderNotFoundException(order_number)

            # Lösche über Repository
            success = self.order_repo.delete_domain(order_number)

            if success:
                logger.info("Order %s erfolgreich gelöscht", order_number)
            else:
                logger.warning("Order %s konnte nicht gelöscht werden", order_number)

            return success

        except OrderNotFoundException as e:
            logger.error("Geschäftslogik-Fehler beim Löschen der Order: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Löschen der Order: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Löschen der Order: %s", e)
            raise


# Test-Funktion
if __name__ == "__main__":
    print("Testing OrderService...")
    try:
        service = OrderService()
        print("OrderService erfolgreich erstellt!")
    except Exception as e:
        print("Fehler: %s" % e)
        import traceback

        traceback.print_exc()
