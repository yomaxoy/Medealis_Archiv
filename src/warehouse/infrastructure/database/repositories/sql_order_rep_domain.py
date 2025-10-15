# src/warehouse/infrastructure/database/repositories/sqlalchemy_order_repository_domain.py

"""
SQLAlchemy Order Repository mit Domain Objects - Clean Architecture Implementation.

Implementiert das OrderRepository Interface und gibt Domain Objects zurück.
Vollständige Implementation für Order und OrderItem Management.
"""

from typing import List, Optional
from datetime import datetime, date

from warehouse.domain.entities.order import Order, OrderItem
from warehouse.domain.repositories.order_repository import OrderRepository
from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.order_model import (
    OrderModel,
    OrderItemModel,
)
from warehouse.infrastructure.database.mappers.order_mapper import (
    OrderMapper,
    OrderItemMapper,
)

import logging

logger = logging.getLogger(__name__)


class SQLAlchemyOrderRepositoryDomain(OrderRepository):
    """
    Domain Objects Order Repository - vollständige Implementation.

    Bietet Domain Object Methoden für Order und OrderItem Management.
    """

    def __init__(self):
        self._order_mapper = OrderMapper()
        self._order_item_mapper = OrderItemMapper()

    # === DOMAIN OBJECT METHODS ===

    def save_domain(self, order: Order) -> str:
        """Speichert Order Domain Entity."""
        with get_session() as session:
            # Prüfe ob bereits vorhanden
            existing_model = (
                session.query(OrderModel)
                .filter(OrderModel.order_number == order.order_number)
                .first()
            )

            if existing_model:
                # Update existing
                self._order_mapper.update_model(existing_model, order)
            else:
                # Create new
                new_model = self._order_mapper.to_model(order)
                session.add(new_model)
                session.flush()  # Für OrderItems

            # Handle OrderItems separately
            self._save_order_items(session, order)

            return order.order_number

    def find_domain_by_order_number(self, order_number: str) -> Optional[Order]:
        """Sucht Order Domain Entity per Bestellnummer."""
        with get_session() as session:
            model = (
                session.query(OrderModel)
                .filter(OrderModel.order_number == order_number)
                .first()
            )

            if model:
                order = self._order_mapper.to_domain(model)
                # Load OrderItems
                self._load_order_items_for_order(session, order)
                return order
            return None

    def find_domain_by_supplier(self, supplier_id: str) -> List[Order]:
        """Sucht alle Order Domain Entities eines Lieferanten."""
        with get_session() as session:
            models = (
                session.query(OrderModel)
                .filter(OrderModel.supplier_id == supplier_id)
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            # Load OrderItems für alle Orders
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_domain_by_status(self, is_completed: bool) -> List[Order]:
        """Sucht Order Domain Entities nach Completion-Status."""
        with get_session() as session:
            status_value = "Abgeschlossen" if is_completed else "Offen"
            models = (
                session.query(OrderModel)
                .filter(OrderModel.status == status_value)
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_domain_all(self) -> List[Order]:
        """Gibt alle Orders als Domain Entities zurück. ALWAYS returns list."""
        try:
            with get_session() as session:
                models = session.query(OrderModel).all()

                # Safety check: models should never be None, but check anyway
                if models is None:
                    logger.warning("query().all() returned None, returning empty list")
                    return []

                orders = [self._order_mapper.to_domain(model) for model in models]

                # Load OrderItems für alle Orders
                for order in orders:
                    try:
                        self._load_order_items_for_order(session, order)
                    except Exception as e:
                        logger.warning(f"Could not load items for order {order.order_number}: {e}")

                return orders
        except Exception as e:
            logger.error(f"Error in find_domain_all: {e}")
            # Return empty list instead of None on error
            return []

    def delete_domain(self, order_number: str) -> bool:
        """Löscht Order Domain Entity."""
        with get_session() as session:
            model = (
                session.query(OrderModel)
                .filter(OrderModel.order_number == order_number)
                .first()
            )

            if model:
                # OrderItems werden durch CASCADE gelöscht
                session.delete(model)
                return True
            return False

    def exists_domain(self, order_number: str) -> bool:
        """Prüft ob Order Domain Entity existiert."""
        with get_session() as session:
            return (
                session.query(OrderModel)
                .filter(OrderModel.order_number == order_number)
                .first()
            ) is not None

    # === CONVENIENCE METHODS ===

    def find_domain_by_employee(self, employee_name: str) -> List[Order]:
        """Sucht Orders eines Mitarbeiters als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(OrderModel)
                .filter(OrderModel.employee_name == employee_name)
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_domain_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Order]:
        """Sucht Orders in Datumsbereich als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(OrderModel)
                .filter(
                    OrderModel.order_date >= start_date,
                    OrderModel.order_date <= end_date,
                )
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_domain_overdue(self) -> List[Order]:
        """Sucht überfällige Orders als Domain Entities."""
        today = date.today()

        with get_session() as session:
            models = (
                session.query(OrderModel)
                .filter(
                    OrderModel.status == "Offen",
                    OrderModel.expected_delivery_date.isnot(None),
                    OrderModel.expected_delivery_date < today,
                )
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_domain_recent(self, limit: int = 10) -> List[Order]:
        """Sucht die neuesten Orders als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(OrderModel)
                .order_by(OrderModel.created_at.desc())
                .limit(limit)
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    # === BASE REPOSITORY INTERFACE ===

    def save(self, entity: Order) -> Order:
        """BaseRepository save method."""
        self.save_domain(entity)
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Order]:
        """BaseRepository find_by_id."""
        return self.find_domain_by_order_number(entity_id)

    def find_all(self) -> List[Order]:
        """BaseRepository find_all."""
        return self.find_domain_all()

    def delete(self, entity_id: str) -> bool:
        """BaseRepository delete."""
        return self.delete_domain(entity_id)

    def exists(self, entity_id: str) -> bool:
        """BaseRepository exists."""
        return self.exists_domain(entity_id)

    def count(self) -> int:
        """BaseRepository count."""
        with get_session() as session:
            return session.query(OrderModel).count()

    def find_by_criteria(self, criteria: dict) -> List[Order]:
        """BaseRepository find_by_criteria."""
        with get_session() as session:
            query = session.query(OrderModel)

            if "supplier_id" in criteria:
                query = query.filter(OrderModel.supplier_id == criteria["supplier_id"])
            if "employee_name" in criteria:
                query = query.filter(
                    OrderModel.employee_name == criteria["employee_name"]
                )
            if "is_completed" in criteria:
                status = "Abgeschlossen" if criteria["is_completed"] else "Offen"
                query = query.filter(OrderModel.status == status)

            models = query.all()
            orders = [self._order_mapper.to_domain(model) for model in models]

            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    # === ORDER ITEM MANAGEMENT ===

    def add_order_item_to_order(
        self,
        order_number: str,
        article_number: str,
        ordered_quantity: int,
        unit_description: str = None,
        notes: str = None,
    ) -> bool:
        """Fügt OrderItem zu einer Order hinzu."""
        try:
            # Load Order
            order = self.find_domain_by_order_number(order_number)
            if not order:
                return False

            # Add OrderItem using Domain Logic
            order.add_order_item(
                article_number=article_number,
                ordered_quantity=ordered_quantity,
                unit_description=unit_description,
                notes=notes,
            )

            # Save Order (will save OrderItems too)
            self.save_domain(order)
            return True

        except Exception as e:
            print(f"Error adding OrderItem: {e}")
            return False

    def remove_order_item_from_order(
        self, order_number: str, article_number: str
    ) -> bool:
        """Entfernt OrderItem aus einer Order."""
        try:
            order = self.find_domain_by_order_number(order_number)
            if not order:
                return False

            # Remove using Domain Logic
            success = order.remove_item(article_number)

            if success:
                self.save_domain(order)

            return success

        except Exception as e:
            print(f"Error removing OrderItem: {e}")
            return False

    def update_order_item_quantity(
        self, order_number: str, article_number: str, new_quantity: int
    ) -> bool:
        """Aktualisiert Menge eines OrderItems."""
        try:
            order = self.find_domain_by_order_number(order_number)
            if not order:
                return False

            # Update using Domain Logic
            success = order.update_order_item_quantity(article_number, new_quantity)

            if success:
                self.save_domain(order)

            return success

        except Exception as e:
            print(f"Error updating OrderItem quantity: {e}")
            return False

    def find_order_items_by_order(self, order_number: str) -> List[OrderItem]:
        """Sucht alle OrderItems einer Order."""
        order = self.find_domain_by_order_number(order_number)
        if order:
            return order.order_items
        return []

    # === SEARCH & FILTERING ===

    def search_orders(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Order]:
        """Volltextsuche in Orders."""
        with get_session() as session:
            from sqlalchemy import or_

            # Default search fields
            if not search_fields:
                search_fields = [
                    "order_number",
                    "supplier_id",
                    "employee_name",
                    "notes",
                ]

            conditions = []
            for field in search_fields:
                if hasattr(OrderModel, field):
                    field_attr = getattr(OrderModel, field)
                    conditions.append(field_attr.contains(search_term))

            if conditions:
                models = session.query(OrderModel).filter(or_(*conditions)).all()
            else:
                models = []

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_by_advanced_criteria(self, criteria: dict) -> List[Order]:
        """Erweiterte Suche mit komplexen Kriterien."""
        with get_session() as session:
            query = session.query(OrderModel)

            # Extended filtering
            if "supplier_id" in criteria:
                query = query.filter(OrderModel.supplier_id == criteria["supplier_id"])
            if "employee_name" in criteria:
                query = query.filter(
                    OrderModel.employee_name == criteria["employee_name"]
                )
            if "order_date_from" in criteria:
                query = query.filter(
                    OrderModel.order_date >= criteria["order_date_from"]
                )
            if "order_date_to" in criteria:
                query = query.filter(OrderModel.order_date <= criteria["order_date_to"])
            if "is_completed" in criteria:
                status = "Abgeschlossen" if criteria["is_completed"] else "Offen"
                query = query.filter(OrderModel.status == status)
            if "is_overdue" in criteria and criteria["is_overdue"]:
                today = date.today()
                query = query.filter(
                    OrderModel.status == "Offen",
                    OrderModel.expected_delivery_date.isnot(None),
                    OrderModel.expected_delivery_date < today,
                )

            models = query.all()
            orders = [self._order_mapper.to_domain(model) for model in models]

            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    def find_orders_containing_article(self, article_number: str) -> List[Order]:
        """Sucht Orders die einen bestimmten Artikel enthalten."""
        with get_session() as session:
            # Subquery für Orders mit dem Artikel
            subquery = (
                session.query(OrderItemModel.order_number)
                .filter(OrderItemModel.article_number == article_number)
                .distinct()
                .subquery()
            )

            models = (
                session.query(OrderModel)
                .filter(OrderModel.order_number.in_(subquery))
                .all()
            )

            orders = [self._order_mapper.to_domain(model) for model in models]
            for order in orders:
                self._load_order_items_for_order(session, order)

            return orders

    # === STATUS & LIFECYCLE MANAGEMENT ===

    def complete_order(self, order_number: str, completed_by: str) -> bool:
        """Schließt eine Order ab."""
        try:
            order = self.find_domain_by_order_number(order_number)
            if not order:
                return False

            # Use Domain Logic
            order.complete_order(completed_by)
            self.save_domain(order)
            return True

        except Exception as e:
            print(f"Error completing order: {e}")
            return False

    def reopen_order(self, order_number: str, reopened_by: str) -> bool:
        """Öffnet eine abgeschlossene Order wieder."""
        try:
            order = self.find_domain_by_order_number(order_number)
            if not order:
                return False

            # Use Domain Logic
            order.reopen_order(reopened_by)
            self.save_domain(order)
            return True

        except Exception as e:
            print(f"Error reopening order: {e}")
            return False

    # === ANALYTICS & STATISTICS ===

    def get_order_statistics(self) -> dict:
        """Gibt Order-Statistiken zurück."""
        with get_session() as session:
            from sqlalchemy import func

            total_orders = session.query(OrderModel).count()
            completed_orders = (
                session.query(OrderModel)
                .filter(OrderModel.status == "Abgeschlossen")
                .count()
            )
            open_orders = (
                session.query(OrderModel).filter(OrderModel.status == "Offen").count()
            )

            # Overdue orders
            today = date.today()
            overdue_orders = (
                session.query(OrderModel)
                .filter(
                    OrderModel.status == "Offen",
                    OrderModel.expected_delivery_date.isnot(None),
                    OrderModel.expected_delivery_date < today,
                )
                .count()
            )

            return {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "open_orders": open_orders,
                "overdue_orders": overdue_orders,
                "completion_rate": (
                    (completed_orders / total_orders * 100) if total_orders > 0 else 0
                ),
            }

    def get_supplier_order_statistics(self) -> dict:
        """Gibt Order-Statistiken pro Lieferant zurück."""
        with get_session() as session:
            from sqlalchemy import func

            results = (
                session.query(
                    OrderModel.supplier_id,
                    func.count(OrderModel.order_number).label("total_orders"),
                    func.count(
                        func.case([(OrderModel.status == "Abgeschlossen", 1)])
                    ).label("completed_orders"),
                )
                .group_by(OrderModel.supplier_id)
                .all()
            )

            return {
                supplier_id: {
                    "total_orders": total,
                    "completed_orders": completed,
                    "completion_rate": (completed / total * 100) if total > 0 else 0,
                }
                for supplier_id, total, completed in results
            }

    def get_order_volume_by_month(self, year: int) -> dict:
        """Gibt monatliche Order-Volumina für ein Jahr zurück."""
        with get_session() as session:
            from sqlalchemy import func, extract

            results = (
                session.query(
                    extract("month", OrderModel.order_date).label("month"),
                    func.count(OrderModel.order_number),
                )
                .filter(extract("year", OrderModel.order_date) == year)
                .group_by(extract("month", OrderModel.order_date))
                .all()
            )

            # Initialize all months with 0
            monthly_volume = {i: 0 for i in range(1, 13)}

            # Fill with actual data
            for month, count in results:
                monthly_volume[int(month)] = count

            return monthly_volume

    def get_employee_order_statistics(self) -> dict:
        """Gibt Order-Statistiken pro Mitarbeiter zurück."""
        with get_session() as session:
            from sqlalchemy import func

            results = (
                session.query(
                    OrderModel.employee_name,
                    func.count(OrderModel.order_number).label("total_orders"),
                    func.count(
                        func.case([(OrderModel.status == "Abgeschlossen", 1)])
                    ).label("completed_orders"),
                )
                .group_by(OrderModel.employee_name)
                .all()
            )

            return {
                employee: {
                    "total_orders": total,
                    "completed_orders": completed,
                    "completion_rate": (completed / total * 100) if total > 0 else 0,
                }
                for employee, total, completed in results
            }

    def get_completion_rate_statistics(self) -> dict:
        """Gibt Abschlussraten-Statistiken zurück."""
        with get_session() as session:
            from sqlalchemy import func

            # Overall completion rate
            overall_stats = self.get_order_statistics()

            # Average completion time
            avg_completion_time = (
                session.query(
                    func.avg(
                        func.julianday(OrderModel.updated_at)
                        - func.julianday(OrderModel.created_at)
                    )
                )
                .filter(OrderModel.status == "Abgeschlossen")
                .scalar()
            ) or 0.0

            return {
                **overall_stats,
                "average_completion_days": round(avg_completion_time, 2),
            }

    # === DELIVERY COMPARISON ===

    def compare_order_with_deliveries(self, order_number: str) -> dict:
        """Vergleicht Order mit tatsächlichen Deliveries."""
        order = self.find_domain_by_order_number(order_number)
        if not order:
            return {"error": "Order not found"}

        try:
            # Get delivered items via ItemRepository
            from warehouse.infrastructure.database.repositories.sql_item_rep_domain import (
                SQLAlchemyItemRepositoryDomain,
            )

            item_repo = SQLAlchemyItemRepositoryDomain()
            delivered_items = item_repo.find_domain_by_order_number(order_number)

            # Use Domain Logic for comparison
            delivery_items_dict = [
                {"article_number": str(item.article_number), "quantity": item.quantity}
                for item in delivered_items
            ]

            return order.compare_with_delivery(delivery_items_dict)

        except Exception as e:
            return {"error": f"Comparison failed: {e}"}

    def find_orders_with_delivery_discrepancies(self) -> List[Order]:
        """Sucht Orders mit Liefer-Abweichungen."""
        orders_with_discrepancies = []

        # Get all completed orders
        completed_orders = self.find_domain_by_status(False)  # Open orders

        for order in completed_orders:
            try:
                comparison = self.compare_order_with_deliveries(order.order_number)

                # Check for discrepancies
                if (
                    comparison.get("missing_items")
                    or comparison.get("unexpected_items")
                    or comparison.get("quantity_mismatches")
                ):
                    orders_with_discrepancies.append(order)

            except Exception:
                continue  # Skip orders with comparison errors

        return orders_with_discrepancies

    def find_orders_fully_delivered(self) -> List[Order]:
        """Sucht Orders die vollständig geliefert wurden."""
        fully_delivered = []

        orders = self.find_domain_by_status(False)  # Open orders

        for order in orders:
            try:
                comparison = self.compare_order_with_deliveries(order.order_number)

                # Check if fully delivered
                if (
                    not comparison.get("missing_items")
                    and not comparison.get("quantity_mismatches")
                    and comparison.get("matched_items")
                ):
                    fully_delivered.append(order)

            except Exception:
                continue

        return fully_delivered

    def find_orders_partially_delivered(self) -> List[Order]:
        """Sucht Orders die nur teilweise geliefert wurden."""
        partially_delivered = []

        orders = self.find_domain_by_status(False)  # Open orders

        for order in orders:
            try:
                comparison = self.compare_order_with_deliveries(order.order_number)

                # Check if partially delivered
                if comparison.get("matched_items") and (
                    comparison.get("missing_items")
                    or comparison.get("quantity_mismatches")
                ):
                    partially_delivered.append(order)

            except Exception:
                continue

        return partially_delivered

    # === VALIDATION ===

    def validate_order_for_completion(self, order_number: str) -> List[str]:
        """Validiert Order für Abschluss."""
        order = self.find_domain_by_order_number(order_number)
        if not order:
            return ["Order nicht gefunden"]

        # Use Domain Logic
        return order.validate_for_completion()

    def order_number_exists(self, order_number: str) -> bool:
        """Prüft ob Bestellnummer bereits existiert."""
        return self.exists_domain(order_number)

    # === PRIVATE HELPER METHODS ===

    def _save_order_items(self, session, order: Order) -> None:
        """Speichert OrderItems für eine Order."""
        try:
            # Delete existing OrderItems
            session.query(OrderItemModel).filter(
                OrderItemModel.order_number == order.order_number
            ).delete()

            # Add current OrderItems
            for order_item in order.order_items:
                item_model = self._order_item_mapper.to_model(
                    order_item, order.order_number
                )
                session.add(item_model)

        except Exception as e:
            print(
                f"Warning: Could not save OrderItems for order {order.order_number}: {e}"
            )

    def _load_order_items_for_order(self, session, order: Order) -> None:
        """Lädt OrderItems für eine Order."""
        try:
            item_models = (
                session.query(OrderItemModel)
                .filter(OrderItemModel.order_number == order.order_number)
                .all()
            )

            order.order_items = [
                self._order_item_mapper.to_domain(item_model)
                for item_model in item_models
            ]

        except Exception as e:
            print(
                f"Warning: Could not load OrderItems for order {order.order_number}: {e}"
            )
            order.order_items = []

    def validate_entity(self, entity: Order) -> List[str]:
        """Validiert Order Entity vor dem Speichern."""
        errors = []

        # Basic validation
        if not entity.order_number:
            errors.append("Bestellnummer ist erforderlich")
        if not entity.supplier_id:
            errors.append("Lieferanten-ID ist erforderlich")
        if not entity.employee_name:
            errors.append("Mitarbeitername ist erforderlich")
        if not entity.order_date:
            errors.append("Bestelldatum ist erforderlich")

        return errors

    # === BULK OPERATIONS ===

    def save_domain_batch(self, orders: List[Order]) -> List[str]:
        """Speichert mehrere Orders in einem Batch."""
        saved_numbers = []

        with get_session() as session:
            for order in orders:
                existing_model = (
                    session.query(OrderModel)
                    .filter(OrderModel.order_number == order.order_number)
                    .first()
                )

                if existing_model:
                    self._order_mapper.update_model(existing_model, order)
                else:
                    new_model = self._order_mapper.to_model(order)
                    session.add(new_model)
                    session.flush()

                # Save OrderItems
                self._save_order_items(session, order)
                saved_numbers.append(order.order_number)

        return saved_numbers

    # === LEGACY COMPATIBILITY METHODS (Dictionary-based) ===

    def create_order(
        self,
        order_number: str,
        order_date,
        supplier_name: str = "",
        customer_name: str = "Medealis",
        employee_name: str = "System",
        items: List[dict] = None
    ) -> bool:
        """
        Erstellt eine neue Bestellung (Legacy-kompatibel).

        Args:
            order_number: Bestellnummer
            order_date: Bestelldatum (date oder string)
            supplier_name: Lieferantenname (nicht verwendet)
            customer_name: Kundenname (nicht verwendet)
            employee_name: Mitarbeitername
            items: Liste von Item-Dicts (optional)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            from datetime import datetime

            # Parse date if string
            if isinstance(order_date, str):
                date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']
                parsed_date = None

                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(order_date.strip(), fmt).date()
                        break
                    except ValueError:
                        continue

                if not parsed_date:
                    parsed_date = date.today()
            else:
                parsed_date = order_date if order_date else date.today()

            # Create Order entity
            order = Order(
                order_number=order_number,
                supplier_id=None,  # Will be set later if needed
                order_date=parsed_date,
                employee_name=employee_name,
                notes=f"Erstellt ueber KI-Analyse fuer {customer_name}"
            )

            # Add items if provided
            if items:
                for item_data in items:
                    order.add_order_item(
                        article_number=item_data.get('article_number', ''),
                        ordered_quantity=item_data.get('quantity', 0),
                        unit_description=item_data.get('unit_description', ''),
                        notes=item_data.get('description', '')
                    )

            # Save
            self.save_domain(order)
            return True

        except Exception as e:
            logger.error(f"Error creating order {order_number}: {e}")
            return False

    def update_order_date(self, order_number: str, order_date: str) -> bool:
        """
        Aktualisiert das Bestelldatum (Legacy-kompatibel).

        Args:
            order_number: Bestellnummer
            order_date: Neues Bestelldatum (String)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            from datetime import datetime

            # Parse date string
            date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']
            parsed_date = None

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(order_date.strip(), fmt).date()
                    break
                except ValueError:
                    continue

            if not parsed_date:
                logger.warning(f"Could not parse date: {order_date}")
                return False

            # Load order
            order = self.find_domain_by_order_number(order_number)
            if not order:
                logger.warning(f"Order not found: {order_number}")
                return False

            # Update date
            order.order_date = parsed_date

            # Save
            self.save_domain(order)
            return True

        except Exception as e:
            logger.error(f"Error updating order date for {order_number}: {e}")
            return False

    def find_by_order_number(self, order_number: str):
        """Legacy-kompatible Methode - gibt Domain Object zurück."""
        return self.find_domain_by_order_number(order_number)

    # === DEBUGGING & MONITORING ===

    def get_repository_statistics(self) -> dict:
        """Get repository statistics for monitoring."""
        with get_session() as session:
            from sqlalchemy import func

            total_orders = session.query(OrderModel).count()
            total_order_items = session.query(OrderItemModel).count()

            # Average items per order
            avg_items_per_order = (
                (total_order_items / total_orders) if total_orders > 0 else 0
            )

            # Supplier distribution
            supplier_count = session.query(
                func.count(func.distinct(OrderModel.supplier_id))
            ).scalar()

            return {
                "total_orders": total_orders,
                "total_order_items": total_order_items,
                "average_items_per_order": round(avg_items_per_order, 2),
                "unique_suppliers": supplier_count,
                **self.get_order_statistics(),
            }
