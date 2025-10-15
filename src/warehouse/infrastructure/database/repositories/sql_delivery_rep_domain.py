# src/warehouse/infrastructure/database/repositories/sqlalchemy_delivery_repository_domain.py

"""
SQLAlchemy Delivery Repository mit Domain Objects - Clean Architecture Implementation.

Implementiert das erweiterte DeliveryRepository Interface und gibt Domain Objects zurück.
Vollständige Integration der bestehenden Dictionary-basierten Methoden.
"""

from typing import List, Optional
from datetime import datetime, date

from warehouse.domain.entities.delivery import Delivery
from warehouse.domain.enums.delivery_status import DeliveryStatus
from warehouse.domain.repositories.delivery_repository import DeliveryRepository
from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.delivery_model import DeliveryModel
from warehouse.infrastructure.database.mappers.delivery_mapper import DeliveryMapper

# REMOVED: No longer import legacy repository
# from warehouse.infrastructure.database.repositories.sql_delivery_repository import (
#     SQLDeliveryRepository,
# )

import logging

logger = logging.getLogger(__name__)


class SQLAlchemyDeliveryRepositoryDomain(DeliveryRepository):
    """
    Domain Objects Delivery Repository - vollständig unabhängige Implementation.

    Bietet sowohl Domain Object Methoden als auch Legacy Dictionary Methoden.
    Alle Operationen erfolgen direkt ohne Delegation an Legacy Repository.
    """

    def __init__(self):
        self._mapper = DeliveryMapper()
        # REMOVED: self._dict_repo = SQLDeliveryRepository()  # No longer needed

    # === DOMAIN OBJECT METHODS (NEU) ===

    def save_domain(self, delivery: Delivery) -> str:
        """Speichert Delivery Domain Entity."""
        with get_session() as session:
            # Prüfe ob bereits vorhanden
            existing_model = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.delivery_number == delivery.delivery_number)
                .first()
            )

            if existing_model:
                # Update existing
                self._mapper.update_model(existing_model, delivery)
            else:
                # Create new
                new_model = self._mapper.to_model(delivery)
                session.add(new_model)

            return delivery.delivery_number

    def find_domain_by_delivery_number(
        self, delivery_number: str
    ) -> Optional[Delivery]:
        """Sucht Delivery Domain Entity per Lieferscheinnummer."""
        with get_session() as session:
            model = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.delivery_number == delivery_number)
                .first()
            )

            if model:
                delivery = self._mapper.to_domain(model)
                # Items separat laden für Performance
                self._load_items_for_delivery(delivery)
                return delivery
            return None

    def find_domain_by_supplier(self, supplier_id: str) -> List[Delivery]:
        """Sucht alle Delivery Domain Entities eines Lieferanten."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.supplier_id == supplier_id)
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            # Items für alle Deliveries laden
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_domain_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        """Sucht Delivery Domain Entities nach Status."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.status == status.value)
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_domain_all(self) -> List[Delivery]:
        """Gibt alle Deliveries als Domain Entities zurück. ALWAYS returns list."""
        try:
            with get_session() as session:
                models = session.query(DeliveryModel).all()

                # Safety check: models should never be None, but check anyway
                if models is None:
                    logger.warning("query().all() returned None, returning empty list")
                    return []

                deliveries = [self._mapper.to_domain(model) for model in models]

                # Items für alle Deliveries laden (könnte Performance-Issue werden bei vielen)
                for delivery in deliveries:
                    try:
                        self._load_items_for_delivery(delivery)
                    except Exception as e:
                        logger.warning(f"Could not load items for delivery {delivery.delivery_number}: {e}")

                return deliveries
        except Exception as e:
            logger.error(f"Error in find_domain_all: {e}")
            # Return empty list instead of None on error
            return []

    def delete_domain(self, delivery_number: str) -> bool:
        """Löscht Delivery Domain Entity."""
        with get_session() as session:
            model = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.delivery_number == delivery_number)
                .first()
            )

            if model:
                session.delete(model)
                return True
            return False

    def exists_domain(self, delivery_number: str) -> bool:
        """Prüft ob Delivery Domain Entity existiert."""
        with get_session() as session:
            return (
                session.query(DeliveryModel)
                .filter(DeliveryModel.delivery_number == delivery_number)
                .first()
            ) is not None

    # === DOMAIN OBJECT CONVENIENCE METHODS ===

    def find_domain_by_employee(self, employee_name: str) -> List[Delivery]:
        """Sucht Deliveries eines Mitarbeiters als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.employee_name == employee_name)
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_domain_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Delivery]:
        """Sucht Deliveries in Datumsbereich als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.delivery_date >= start_date,
                    DeliveryModel.delivery_date <= end_date,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_domain_pending(self) -> List[Delivery]:
        """Sucht alle noch nicht abgeschlossenen Deliveries als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.status != DeliveryStatus.ABGESCHLOSSEN.value)
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === BASE REPOSITORY INTERFACE (Domain Objects) ===

    def save(self, entity: Delivery) -> Delivery:
        """BaseRepository save method - delegates to save_domain."""
        self.save_domain(entity)
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Delivery]:
        """BaseRepository find_by_id - expects delivery_number."""
        return self.find_domain_by_delivery_number(entity_id)

    def find_all(self) -> List[Delivery]:
        """BaseRepository find_all - delegates to find_domain_all."""
        return self.find_domain_all()

    def delete(self, entity_id: str) -> bool:
        """BaseRepository delete - expects delivery_number."""
        return self.delete_domain(entity_id)

    def exists(self, entity_id: str) -> bool:
        """BaseRepository exists - expects delivery_number."""
        return self.exists_domain(entity_id)

    def count(self) -> int:
        """BaseRepository count."""
        with get_session() as session:
            return session.query(DeliveryModel).count()

    def find_by_criteria(self, criteria: dict) -> List[Delivery]:
        """BaseRepository find_by_criteria - basic implementation."""
        with get_session() as session:
            query = session.query(DeliveryModel)

            # Basic criteria filtering
            if "status" in criteria:
                query = query.filter(DeliveryModel.status == criteria["status"])
            if "supplier_id" in criteria:
                query = query.filter(
                    DeliveryModel.supplier_id == criteria["supplier_id"]
                )
            if "employee_name" in criteria:
                query = query.filter(
                    DeliveryModel.employee_name == criteria["employee_name"]
                )

            models = query.all()
            deliveries = [self._mapper.to_domain(model) for model in models]

            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === LEGACY INTERFACE DELEGATION (Bestehende Methoden) ===

    def find_by_delivery_number(self, delivery_number: str) -> Optional[Delivery]:
        """Delegates to domain method."""
        return self.find_domain_by_delivery_number(delivery_number)

    def delivery_number_exists(self, delivery_number: str) -> bool:
        """Delegates to exists_domain."""
        return self.exists_domain(delivery_number)

    def find_by_supplier(self, supplier_id: str) -> List[Delivery]:
        """Delegates to domain method."""
        return self.find_domain_by_supplier(supplier_id)

    def find_by_supplier_and_status(
        self, supplier_id: str, status: DeliveryStatus
    ) -> List[Delivery]:
        """Find by supplier and status."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.supplier_id == supplier_id,
                    DeliveryModel.status == status.value,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def get_supplier_delivery_count(self, supplier_id: str) -> int:
        """Count deliveries for supplier."""
        with get_session() as session:
            return (
                session.query(DeliveryModel)
                .filter(DeliveryModel.supplier_id == supplier_id)
                .count()
            )

    def find_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        """Delegates to domain method."""
        return self.find_domain_by_status(status)

    def find_pending_deliveries(self) -> List[Delivery]:
        """Delegates to domain method."""
        return self.find_domain_pending()

    def find_completed_deliveries(self) -> List[Delivery]:
        """Find completed deliveries."""
        return self.find_domain_by_status(DeliveryStatus.ABGESCHLOSSEN)

    def find_deliveries_needing_data_check(self) -> List[Delivery]:
        """Find deliveries needing data check."""
        # Deliveries mit Status EMPFANGEN die Items mit ARTIKEL_ANGELEGT haben
        with get_session() as session:
            from warehouse.infrastructure.database.models.item_model import ItemModel

            # Subquery für Deliveries mit Items die noch ARTIKEL_ANGELEGT sind
            subquery = (
                session.query(ItemModel.delivery_number)
                .filter(ItemModel.status == "Artikel angelegt")
                .distinct()
                .subquery()
            )

            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.status == DeliveryStatus.EMPFANGEN.value,
                    DeliveryModel.delivery_number.in_(subquery),
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_deliveries_in_processing(self) -> List[Delivery]:
        """Find deliveries in processing."""
        processing_statuses = [
            DeliveryStatus.ERFASST.value,
            DeliveryStatus.IN_BEARBEITUNG.value,
        ]

        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.status.in_(processing_statuses))
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === DATE-BASED QUERIES ===

    def find_by_delivery_date(self, delivery_date: date) -> List[Delivery]:
        """Find deliveries by delivery date."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.delivery_date == delivery_date)
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_by_delivery_date_range(
        self, start_date: date, end_date: date
    ) -> List[Delivery]:
        """Delegates to domain method."""
        return self.find_domain_by_date_range(start_date, end_date)

    def find_created_between(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> List[Delivery]:
        """Find deliveries created between datetimes."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.created_at >= start_datetime,
                    DeliveryModel.created_at <= end_datetime,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_completed_between(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> List[Delivery]:
        """Find deliveries completed between datetimes."""
        with get_session() as session:
            # Annahme: completed_at Field existiert oder nutze updated_at
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.status == DeliveryStatus.ABGESCHLOSSEN.value,
                    DeliveryModel.updated_at >= start_datetime,
                    DeliveryModel.updated_at <= end_datetime,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_overdue_deliveries(self, days_threshold: int = 7) -> List[Delivery]:
        """Find overdue deliveries."""
        cutoff_date = datetime.now() - datetime.timedelta(days=days_threshold)

        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.status != DeliveryStatus.ABGESCHLOSSEN.value,
                    DeliveryModel.created_at <= cutoff_date,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === EMPLOYEE-BASED QUERIES ===

    def find_by_employee(self, employee_name: str) -> List[Delivery]:
        """Delegates to domain method."""
        return self.find_domain_by_employee(employee_name)

    def find_by_employee_and_status(
        self, employee_name: str, status: DeliveryStatus
    ) -> List[Delivery]:
        """Find deliveries by employee and status."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.employee_name == employee_name,
                    DeliveryModel.status == status.value,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === DOCUMENT-BASED QUERIES ===

    def find_with_document_path(self) -> List[Delivery]:
        """Find deliveries with document path."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.document_path.isnot(None),
                    DeliveryModel.document_path != "",
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_without_document_path(self) -> List[Delivery]:
        """Find deliveries without document path."""
        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    (DeliveryModel.document_path.is_(None))
                    | (DeliveryModel.document_path == "")
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === ANALYTICS & STATISTICS ===

    def get_status_distribution(self) -> dict:
        """Get status distribution."""
        with get_session() as session:
            from sqlalchemy import func

            results = (
                session.query(DeliveryModel.status, func.count(DeliveryModel.status))
                .group_by(DeliveryModel.status)
                .all()
            )

            return {status: count for status, count in results}

    def get_supplier_statistics(self) -> dict:
        """Get supplier statistics."""
        with get_session() as session:
            from sqlalchemy import func

            results = (
                session.query(
                    DeliveryModel.supplier_id,
                    func.count(DeliveryModel.id).label("delivery_count"),
                    func.count(
                        func.case(
                            [
                                (
                                    DeliveryModel.status
                                    == DeliveryStatus.ABGESCHLOSSEN.value,
                                    1,
                                )
                            ]
                        )
                    ).label("completed_count"),
                )
                .group_by(DeliveryModel.supplier_id)
                .all()
            )

            return {
                supplier_id: {
                    "total_deliveries": delivery_count,
                    "completed_deliveries": completed_count,
                    "completion_rate": (
                        (completed_count / delivery_count * 100)
                        if delivery_count > 0
                        else 0
                    ),
                }
                for supplier_id, delivery_count, completed_count in results
            }

    def get_delivery_volume_by_month(self, year: int) -> dict:
        """Get delivery volume by month."""
        with get_session() as session:
            from sqlalchemy import func, extract

            results = (
                session.query(
                    extract("month", DeliveryModel.delivery_date).label("month"),
                    func.count(DeliveryModel.id),
                )
                .filter(extract("year", DeliveryModel.delivery_date) == year)
                .group_by(extract("month", DeliveryModel.delivery_date))
                .all()
            )

            # Initialize all months with 0
            monthly_volume = {i: 0 for i in range(1, 13)}

            # Fill with actual data
            for month, count in results:
                monthly_volume[int(month)] = count

            return monthly_volume

    def get_completion_rate_statistics(self) -> dict:
        """Get completion rate statistics."""
        with get_session() as session:
            from sqlalchemy import func

            total_count = session.query(DeliveryModel).count()
            completed_count = (
                session.query(DeliveryModel)
                .filter(DeliveryModel.status == DeliveryStatus.ABGESCHLOSSEN.value)
                .count()
            )

            # Average processing time
            avg_processing_time = (
                session.query(
                    func.avg(
                        func.julianday(DeliveryModel.updated_at)
                        - func.julianday(DeliveryModel.created_at)
                    )
                )
                .filter(DeliveryModel.status == DeliveryStatus.ABGESCHLOSSEN.value)
                .scalar()
            ) or 0.0

            return {
                "total_deliveries": total_count,
                "completed_deliveries": completed_count,
                "completion_rate": (
                    (completed_count / total_count * 100) if total_count > 0 else 0
                ),
                "average_processing_days": round(avg_processing_time, 2),
            }

    def get_employee_workload_statistics(self) -> dict:
        """Get employee workload statistics."""
        with get_session() as session:
            from sqlalchemy import func

            results = (
                session.query(
                    DeliveryModel.employee_name,
                    func.count(DeliveryModel.id).label("total_deliveries"),
                    func.count(
                        func.case(
                            [
                                (
                                    DeliveryModel.status
                                    == DeliveryStatus.ABGESCHLOSSEN.value,
                                    1,
                                )
                            ]
                        )
                    ).label("completed_deliveries"),
                )
                .group_by(DeliveryModel.employee_name)
                .all()
            )

            return {
                employee: {
                    "total_deliveries": total,
                    "completed_deliveries": completed,
                    "completion_rate": (completed / total * 100) if total > 0 else 0,
                }
                for employee, total, completed in results
            }

    def get_average_processing_time(self) -> float:
        """Get average processing time."""
        with get_session() as session:
            from sqlalchemy import func

            avg_time = (
                session.query(
                    func.avg(
                        func.julianday(DeliveryModel.updated_at)
                        - func.julianday(DeliveryModel.created_at)
                    )
                )
                .filter(DeliveryModel.status == DeliveryStatus.ABGESCHLOSSEN.value)
                .scalar()
            )

            return float(avg_time) if avg_time else 0.0

    # === SEARCH & FILTERING ===

    def search_deliveries(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Delivery]:
        """Search deliveries with term."""
        with get_session() as session:
            query = session.query(DeliveryModel)

            # Default search fields
            if not search_fields:
                search_fields = [
                    "delivery_number",
                    "supplier_id",
                    "employee_name",
                    "notes",
                ]

            # Build search conditions
            conditions = []
            for field in search_fields:
                if hasattr(DeliveryModel, field):
                    field_attr = getattr(DeliveryModel, field)
                    conditions.append(field_attr.contains(search_term))

            if conditions:
                from sqlalchemy import or_

                query = query.filter(or_(*conditions))

            models = query.all()
            deliveries = [self._mapper.to_domain(model) for model in models]

            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_by_advanced_criteria(self, criteria: dict) -> List[Delivery]:
        """Advanced search with complex criteria."""
        # Enhanced version of find_by_criteria
        with get_session() as session:
            query = session.query(DeliveryModel)

            # Extended criteria filtering
            if "status" in criteria:
                query = query.filter(DeliveryModel.status == criteria["status"])
            if "supplier_id" in criteria:
                query = query.filter(
                    DeliveryModel.supplier_id == criteria["supplier_id"]
                )
            if "employee_name" in criteria:
                query = query.filter(
                    DeliveryModel.employee_name == criteria["employee_name"]
                )
            if "delivery_date_from" in criteria:
                query = query.filter(
                    DeliveryModel.delivery_date >= criteria["delivery_date_from"]
                )
            if "delivery_date_to" in criteria:
                query = query.filter(
                    DeliveryModel.delivery_date <= criteria["delivery_date_to"]
                )
            if "has_document" in criteria:
                if criteria["has_document"]:
                    query = query.filter(
                        DeliveryModel.document_path.isnot(None),
                        DeliveryModel.document_path != "",
                    )
                else:
                    query = query.filter(
                        (DeliveryModel.document_path.is_(None))
                        | (DeliveryModel.document_path == "")
                    )

            models = query.all()
            deliveries = [self._mapper.to_domain(model) for model in models]

            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === WORKFLOW SUPPORT ===

    def find_deliveries_requiring_attention(self) -> List[Delivery]:
        """Find deliveries requiring attention."""
        # Kombination aus überfälligen und stagnierenden Deliveries
        overdue = self.find_overdue_deliveries(7)
        stalled = self.find_stalled_deliveries(48)  # 48 Stunden

        # Unique deliveries (avoid duplicates)
        attention_deliveries = {}
        for delivery in overdue + stalled:
            attention_deliveries[delivery.delivery_number] = delivery

        return list(attention_deliveries.values())

    def find_deliveries_ready_for_next_step(self) -> List[Delivery]:
        """Find deliveries ready for next step."""
        # Deliveries die alle Items in einem "ready" Status haben
        with get_session() as session:
            from warehouse.infrastructure.database.models.item_model import ItemModel

            # Subquery für Deliveries wo alle Items mindestens "Daten geprüft" sind
            subquery = (
                session.query(ItemModel.delivery_number)
                .filter(
                    ItemModel.status.in_(
                        [
                            "Daten geprüft",
                            "Sichtgeprüft",
                            "Dokumente geprüft",
                            "Vermessen",
                        ]
                    )
                )
                .distinct()
                .subquery()
            )

            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.status.in_(
                        [
                            DeliveryStatus.ERFASST.value,
                            DeliveryStatus.IN_BEARBEITUNG.value,
                        ]
                    ),
                    DeliveryModel.delivery_number.in_(subquery),
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    def find_stalled_deliveries(self, hours_threshold: int = 24) -> List[Delivery]:
        """Find stalled deliveries."""
        cutoff_datetime = datetime.now() - datetime.timedelta(hours=hours_threshold)

        with get_session() as session:
            models = (
                session.query(DeliveryModel)
                .filter(
                    DeliveryModel.status != DeliveryStatus.ABGESCHLOSSEN.value,
                    DeliveryModel.updated_at <= cutoff_datetime,
                )
                .all()
            )

            deliveries = [self._mapper.to_domain(model) for model in models]
            for delivery in deliveries:
                self._load_items_for_delivery(delivery)

            return deliveries

    # === PRIVATE HELPER METHODS ===

    def _load_items_for_delivery(self, delivery: Delivery) -> None:
        """
        Lädt Items für eine Delivery (Performance-optimiert).
        Verwendet lazy loading um N+1 Probleme zu vermeiden.
        """
        try:
            # Import hier um Circular Import zu vermeiden
            from warehouse.infrastructure.database.repositories.sql_item_rep_domain import (
                SQLAlchemyItemRepositoryDomain,
            )

            item_repo = SQLAlchemyItemRepositoryDomain()
            items = item_repo.find_domain_by_delivery(delivery.delivery_number)
            delivery.items = items

            # Update Delivery Status basierend auf Items
            delivery._update_delivery_status()

        except Exception as e:
            print(
                f"Warning: Could not load items for delivery {delivery.delivery_number}: {e}"
            )
            # Fallback: lasse Items leer
            delivery.items = []

    def validate_entity(self, entity: Delivery) -> List[str]:
        """Validiert Delivery Entity vor dem Speichern."""
        errors = []

        # Basic validation
        if not entity.delivery_number:
            errors.append("Lieferscheinnummer ist erforderlich")
        if not entity.supplier_id:
            errors.append("Lieferanten-ID ist erforderlich")
        if not entity.employee_name:
            errors.append("Mitarbeitername ist erforderlich")
        if not entity.delivery_date:
            errors.append("Lieferdatum ist erforderlich")

        return errors

    # === BULK OPERATIONS ===

    def save_domain_batch(self, deliveries: List[Delivery]) -> List[str]:
        """Speichert mehrere Deliveries in einem Batch."""
        saved_numbers = []

        with get_session() as session:
            for delivery in deliveries:
                existing_model = (
                    session.query(DeliveryModel)
                    .filter(DeliveryModel.delivery_number == delivery.delivery_number)
                    .first()
                )

                if existing_model:
                    self._mapper.update_model(existing_model, delivery)
                else:
                    new_model = self._mapper.to_model(delivery)
                    session.add(new_model)

                saved_numbers.append(delivery.delivery_number)

        return saved_numbers

    # === DEBUGGING & MONITORING ===

    def get_repository_statistics(self) -> dict:
        """Get repository statistics for monitoring."""
        with get_session() as session:
            from sqlalchemy import func

            total_deliveries = session.query(DeliveryModel).count()
            status_dist = self.get_status_distribution()
            supplier_count = session.query(
                func.count(func.distinct(DeliveryModel.supplier_id))
            ).scalar()

            return {
                "total_deliveries": total_deliveries,
                "unique_suppliers": supplier_count,
                "status_distribution": status_dist,
                "completion_rate": self.get_completion_rate_statistics()[
                    "completion_rate"
                ],
            }
