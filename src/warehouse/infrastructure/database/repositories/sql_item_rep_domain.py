# src/warehouse/infrastructure/database/repositories/sql_item_rep_domain.py

"""
SQLAlchemy Item Repository mit Workflow-Steps System.

Verwendet zwei Tabellen:
- items: Stammdaten (Mengen, Zertifikate, etc.)
- item_workflow_steps: Workflow/Status-Tracking
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from warehouse.domain.entities.item import Item
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber
from warehouse.domain.repositories.item_repository import ItemRepository, ItemId
from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.item_model import ItemModel, ItemInfoModel
from warehouse.infrastructure.database.models.item_workflow_steps_model import (
    ItemWorkflowStepsModel,
)
from warehouse.infrastructure.database.mappers.item_mapper import ItemMapper

logger = logging.getLogger(__name__)


class SQLAlchemyItemRepositoryDomain(ItemRepository):
    """
    Item Repository mit Workflow-Steps System.

    Arbeitet mit zwei Tabellen:
    1. items - Stammdaten
    2. item_workflow_steps - Workflow/Status
    """

    def __init__(self):
        self._mapper = ItemMapper()

    # === CORE CRUD OPERATIONS ===

    def save_domain(self, item: Item) -> ItemId:
        """
        Speichert Item Domain Entity in beide Tabellen.

        Args:
            item: Item Domain Entity

        Returns:
            Composite Key des Items
        """
        with get_session() as session:
            composite_key = (
                str(item.article_number),
                str(item.batch_number),
                item.delivery_number,
            )

            # Prüfe ob Item bereits existiert
            existing_item = session.get(ItemModel, composite_key)
            existing_workflow = session.get(ItemWorkflowStepsModel, composite_key)

            if existing_item:
                # Update existing
                item_model, workflow_model = self._mapper.to_models(item)

                # Update ItemModel
                self._copy_item_fields(item_model, existing_item)

                # Update oder Create WorkflowStepsModel
                if existing_workflow:
                    self._copy_workflow_fields(workflow_model, existing_workflow)
                else:
                    session.add(workflow_model)

            else:
                # Create new
                # Stelle sicher dass ItemInfo existiert
                self._ensure_item_info_exists(session, str(item.article_number))

                # Erstelle beide Models
                item_model, workflow_model = self._mapper.to_models(item)
                session.add(item_model)
                session.add(workflow_model)

            return composite_key

    def find_domain_by_composite_key(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
    ) -> Optional[Item]:
        """
        Lädt Item aus beiden Tabellen (items + item_workflow_steps).

        Args:
            article_number: ArticleNumber Value Object
            batch_number: BatchNumber Value Object
            delivery_number: Lieferscheinnummer

        Returns:
            Item Domain Entity oder None
        """
        with get_session() as session:
            composite_key = (str(article_number), str(batch_number), delivery_number)

            # Lade ItemModel
            item_model = session.get(ItemModel, composite_key)
            if not item_model:
                return None

            # Lade WorkflowStepsModel
            workflow_model = session.get(ItemWorkflowStepsModel, composite_key)

            # Konvertiere zu Domain Entity
            return self._mapper.to_domain(item_model, workflow_model)

    def find_domain_by_delivery(self, delivery_number: str) -> List[Item]:
        """Sucht alle Items einer Lieferung."""
        with get_session() as session:
            # Lade alle ItemModels
            item_models = (
                session.query(ItemModel)
                .filter(ItemModel.delivery_number == delivery_number)
                .all()
            )

            if not item_models:
                return []

            # Lade alle WorkflowSteps in einem Query (Performance!)
            composite_keys = [
                (m.article_number, m.batch_number, m.delivery_number)
                for m in item_models
            ]

            workflow_models = (
                session.query(ItemWorkflowStepsModel)
                .filter(ItemWorkflowStepsModel.delivery_number == delivery_number)
                .all()
            )

            # Erstelle Lookup-Dict für schnellen Zugriff
            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }

            # Konvertiere zu Domain Entities
            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                items.append(self._mapper.to_domain(item_model, workflow_model))

            return items

    def find_domain_all(self) -> List[Item]:
        """Lädt alle Items (mit Workflow-Steps)."""
        try:
            with get_session() as session:
                # Lade alle ItemModels
                item_models = session.query(ItemModel).all()

                if not item_models:
                    return []

                # Lade alle WorkflowSteps
                workflow_models = session.query(ItemWorkflowStepsModel).all()

                # Erstelle Lookup-Dict
                workflow_dict = {
                    (w.article_number, w.batch_number, w.delivery_number): w
                    for w in workflow_models
                }

                # Konvertiere zu Domain Entities
                items = []
                for item_model in item_models:
                    key = (
                        item_model.article_number,
                        item_model.batch_number,
                        item_model.delivery_number,
                    )
                    workflow_model = workflow_dict.get(key)
                    items.append(self._mapper.to_domain(item_model, workflow_model))

                return items

        except Exception as e:
            logger.error(f"Error in find_domain_all: {e}")
            return []

    def find_all_with_info(self) -> List[Tuple[Item, Optional[dict]]]:
        """
        Lädt alle Items mit ItemInfo (optimiert mit JOIN).

        Returns:
            List of tuples (Item, ItemInfo_dict or None)
        """
        try:
            with get_session() as session:
                # Query mit LEFT JOIN für ItemInfo
                query = session.query(ItemModel, ItemInfoModel).outerjoin(
                    ItemInfoModel,
                    ItemModel.article_number == ItemInfoModel.article_number,
                )

                results = query.all()

                if not results:
                    return []

                # Lade alle WorkflowSteps in einem Query
                workflow_models = session.query(ItemWorkflowStepsModel).all()
                workflow_dict = {
                    (w.article_number, w.batch_number, w.delivery_number): w
                    for w in workflow_models
                }

                # Konvertiere zu Domain mit Info
                items_with_info = []
                for item_model, info_model in results:
                    key = (
                        item_model.article_number,
                        item_model.batch_number,
                        item_model.delivery_number,
                    )
                    workflow_model = workflow_dict.get(key)

                    item = self._mapper.to_domain(item_model, workflow_model)
                    info_dict = (
                        self._item_info_to_dict(info_model) if info_model else None
                    )

                    items_with_info.append((item, info_dict))

                return items_with_info

        except Exception as e:
            logger.error(f"Error in find_all_with_info: {e}")
            return []

    def delete_domain(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
    ) -> bool:
        """Löscht Item (beide Tabellen via CASCADE)."""
        with get_session() as session:
            composite_key = (str(article_number), str(batch_number), delivery_number)
            item_model = session.get(ItemModel, composite_key)

            if item_model:
                session.delete(item_model)
                # WorkflowSteps wird automatisch via CASCADE gelöscht
                return True
            return False

    def exists_domain(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
    ) -> bool:
        """Prüft ob Item existiert."""
        return (
            self.find_domain_by_composite_key(
                article_number, batch_number, delivery_number
            )
            is not None
        )

    # === ITEM INFO OPERATIONS ===

    def save_item_info(
        self,
        article_number: str,
        designation: str = "",
        revision_number: int = None,
        drawing_reference: str = "",
        storage_location: str = "",
        manufacturer: str = "",
        material_specification: str = "",
        description: str = "",
    ) -> str:
        """Speichert oder aktualisiert ItemInfo (Artikel-Stammdaten)."""
        with get_session() as session:
            item_info = session.get(ItemInfoModel, article_number)

            if item_info:
                # Update existing
                if designation:
                    item_info.designation = designation
                if revision_number:
                    item_info.revision_number = revision_number
                if drawing_reference:
                    item_info.drawing_reference = drawing_reference
                if storage_location is not None:
                    item_info.storage_location = storage_location
                if manufacturer:
                    item_info.manufacturer = manufacturer
                if material_specification:
                    item_info.material_specification = material_specification
                if description:
                    item_info.description = description
            else:
                # Create new
                item_info = ItemInfoModel(
                    article_number=article_number,
                    designation=designation,
                    revision_number=revision_number,
                    drawing_reference=drawing_reference,
                    storage_location=storage_location,
                    manufacturer=manufacturer,
                    material_specification=material_specification,
                    description=description,
                )
                session.add(item_info)

            return article_number

    def find_item_info_by_article_number(self, article_number: str) -> Optional[dict]:
        """Sucht ItemInfo per Artikelnummer."""
        with get_session() as session:
            item_info = session.get(ItemInfoModel, article_number)
            if item_info:
                return self._item_info_to_dict(item_info)
            return None

    def _item_info_to_dict(self, item_info: ItemInfoModel) -> dict:
        """Konvertiert ItemInfoModel zu Dictionary."""
        return {
            "article_number": item_info.article_number,
            "designation": item_info.designation,
            "revision_number": item_info.revision_number,
            "drawing_reference": item_info.drawing_reference,
            "storage_location": item_info.storage_location,
            "manufacturer": item_info.manufacturer,
            "material_specification": item_info.material_specification,
            "description": item_info.description,
            "created_at": item_info.created_at,
            "updated_at": item_info.updated_at,
        }

    # === LEGACY INTERFACE (für Kompatibilität) ===

    def find_by_composite_key(
        self, article_number: str, batch_number: str, delivery_number: str
    ) -> Optional[dict]:
        """Legacy-Methode - gibt Dictionary zurück."""
        try:
            article_num = (
                ArticleNumber(article_number)
                if isinstance(article_number, str)
                else article_number
            )
            batch_num = (
                BatchNumber(batch_number)
                if isinstance(batch_number, str)
                else batch_number
            )

            item = self.find_domain_by_composite_key(
                article_num, batch_num, delivery_number
            )

            if item:
                return item.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error in find_by_composite_key: {e}")
            return None

    # === BASE REPOSITORY INTERFACE ===

    def save(self, entity: Item) -> Item:
        """BaseRepository save method."""
        self.save_domain(entity)
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Item]:
        """BaseRepository find_by_id - erwartet 'ArticleNumber#BatchNumber#DeliveryNumber'."""
        parts = entity_id.split("#")
        if len(parts) == 3:
            try:
                article_number = ArticleNumber(parts[0])
                batch_number = BatchNumber(parts[1])
                delivery_number = parts[2]
                return self.find_domain_by_composite_key(
                    article_number, batch_number, delivery_number
                )
            except ValueError:
                return None
        return None

    def find_all(self) -> List[Item]:
        """BaseRepository find_all."""
        return self.find_domain_all()

    def delete(self, entity_id: str) -> bool:
        """BaseRepository delete."""
        parts = entity_id.split("#")
        if len(parts) == 3:
            try:
                article_number = ArticleNumber(parts[0])
                batch_number = BatchNumber(parts[1])
                delivery_number = parts[2]
                return self.delete_domain(article_number, batch_number, delivery_number)
            except ValueError:
                return False
        return False

    def exists(self, entity_id: str) -> bool:
        """BaseRepository exists."""
        return self.find_by_id(entity_id) is not None

    def count(self) -> int:
        """BaseRepository count."""
        with get_session() as session:
            return session.query(ItemModel).count()

    # === QUERY METHODS ===

    def find_by_article_number(self, article_number: str) -> List[Item]:
        """Sucht alle Items eines Artikels."""
        with get_session() as session:
            item_models = (
                session.query(ItemModel)
                .filter(ItemModel.article_number == article_number)
                .all()
            )

            if not item_models:
                return []

            # Lade WorkflowSteps
            workflow_models = (
                session.query(ItemWorkflowStepsModel)
                .filter(ItemWorkflowStepsModel.article_number == article_number)
                .all()
            )

            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }

            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                items.append(self._mapper.to_domain(item_model, workflow_model))

            return items

    def find_by_status(self, status: str) -> List[Item]:
        """
        Sucht Items nach Status.

        HINWEIS: Da Status jetzt berechnet wird, müssen wir alle Items laden
        und dann filtern. Für große Datenmengen sollte ein Index auf
        workflow_steps Felder gesetzt werden.
        """
        all_items = self.find_domain_all()
        return [item for item in all_items if item.get_current_status() == status]

    def find_ready_for_completion(self) -> List[Item]:
        """Sucht Items die bereit zum Abschluss sind (alle Steps done)."""
        all_items = self.find_domain_all()
        return [item for item in all_items if item.is_ready_for_completion()]

    # === HELPER METHODS ===

    def _ensure_item_info_exists(self, session, article_number: str) -> None:
        """Stellt sicher dass ItemInfo existiert (FK Constraint)."""
        item_info = session.get(ItemInfoModel, article_number)
        if not item_info:
            item_info = ItemInfoModel(
                article_number=article_number, designation=f"Artikel {article_number}"
            )
            session.add(item_info)
            session.flush()

    def _copy_item_fields(self, source: ItemModel, target: ItemModel) -> None:
        """Kopiert Felder von source zu target ItemModel."""
        target.delivered_quantity = source.delivered_quantity
        target.delivery_slip_quantity = source.delivery_slip_quantity
        target.ordered_quantity = source.ordered_quantity
        target.waste_quantity = source.waste_quantity
        target.employee = source.employee
        target.notes = source.notes
        target.order_number = source.order_number

        # Zertifikate
        target.material_certificate = source.material_certificate
        target.measurement_protocol = source.measurement_protocol
        target.coating_certificate = source.coating_certificate
        target.hardness_certificate = source.hardness_certificate
        target.additional_certificates = source.additional_certificates
        target.label_present = source.label_present
        target.accompanying_document = source.accompanying_document

        target.updated_at = datetime.now()

    def _copy_workflow_fields(
        self, source: ItemWorkflowStepsModel, target: ItemWorkflowStepsModel
    ) -> None:
        """Kopiert Felder von source zu target WorkflowStepsModel."""
        target.iteminfo_complete_by = source.iteminfo_complete_by
        target.iteminfo_complete_at = source.iteminfo_complete_at

        target.data_checked_by = source.data_checked_by
        target.data_checked_at = source.data_checked_at

        target.documents_checked_by = source.documents_checked_by
        target.documents_checked_at = source.documents_checked_at

        target.measured_by = source.measured_by
        target.measured_at = source.measured_at

        target.visually_inspected_by = source.visually_inspected_by
        target.visually_inspected_at = source.visually_inspected_at

        target.documents_merged_by = source.documents_merged_by
        target.documents_merged_at = source.documents_merged_at

        target.completed_by = source.completed_by
        target.completed_at = source.completed_at

        target.rejected_by = source.rejected_by
        target.rejected_at = source.rejected_at
        target.rejection_reason = source.rejection_reason

        target.updated_at = datetime.now()

    # === STUB IMPLEMENTATIONS (TODO: Implement these methods) ===

    def find_domain_by_article_number(self, article_number) -> List[Item]:
        """TODO: Implement"""
        return self.find_by_article_number(str(article_number))

    def find_domain_by_status(self, status) -> List[Item]:
        """TODO: Implement - Status ist jetzt String nicht ItemStatus"""
        return self.find_by_status(
            status.value if hasattr(status, "value") else str(status)
        )

    def find_domain_by_order_number(self, order_number: str) -> List[Item]:
        """TODO: Implement"""
        with get_session() as session:
            item_models = (
                session.query(ItemModel)
                .filter(ItemModel.order_number == order_number)
                .all()
            )
            if not item_models:
                return []

            workflow_models = (
                session.query(ItemWorkflowStepsModel)
                .filter(
                    ItemWorkflowStepsModel.article_number.in_(
                        [m.article_number for m in item_models]
                    )
                )
                .all()
            )
            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }

            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                items.append(self._mapper.to_domain(item_model, workflow_model))
            return items

    def find_by_article_and_batch(self, article_number, batch_number) -> Optional[Item]:
        """TODO: Implement - returns first match"""
        with get_session() as session:
            item_model = (
                session.query(ItemModel)
                .filter(
                    ItemModel.article_number == str(article_number),
                    ItemModel.batch_number == str(batch_number),
                )
                .first()
            )
            if not item_model:
                return None
            workflow_model = session.get(
                ItemWorkflowStepsModel,
                (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                ),
            )
            return self._mapper.to_domain(item_model, workflow_model)

    def find_by_unique_identifier(self, unique_id: str) -> Optional[Item]:
        """Format: ArticleNumber#BatchNumber#DeliveryNumber"""
        return self.find_by_id(unique_id)

    def find_by_barcode(self, barcode: str) -> Optional[Item]:
        """TODO: Implement barcode lookup"""
        raise NotImplementedError("Barcode lookup not yet implemented")

    def find_by_delivery_number(self, delivery_number: str) -> List[Item]:
        """Already implemented as find_domain_by_delivery"""
        return self.find_domain_by_delivery(delivery_number)

    def find_by_supplier(self, supplier_id: str) -> List[Item]:
        """TODO: Implement - requires JOIN with deliveries"""
        raise NotImplementedError("Supplier lookup not yet implemented")

    def find_by_current_status(self, status) -> List[Item]:
        """Already implemented as find_by_status"""
        return self.find_by_status(str(status))

    def find_items_needing_attention(self) -> List[Item]:
        """TODO: Implement"""
        all_items = self.find_domain_all()
        return [
            item for item in all_items if not item.completed_by and not item.rejected_by
        ]

    def find_by_completed_step(self, step) -> List[Item]:
        """TODO: Implement step-based queries"""
        raise NotImplementedError("Step-based queries not yet implemented")

    def find_by_missing_step(self, step) -> List[Item]:
        """TODO: Implement step-based queries"""
        raise NotImplementedError("Step-based queries not yet implemented")

    def find_by_certificate_status(self, certificate_type, present: bool) -> List[Item]:
        """TODO: Implement certificate queries"""
        raise NotImplementedError("Certificate queries not yet implemented")

    def find_with_missing_certificates(self) -> List[Item]:
        """TODO: Implement"""
        raise NotImplementedError("Certificate queries not yet implemented")

    def find_with_complete_certificates(self) -> List[Item]:
        """TODO: Implement"""
        raise NotImplementedError("Certificate queries not yet implemented")

    def find_with_inspection_results(self) -> List[Item]:
        """TODO: Implement"""
        all_items = self.find_domain_all()
        return [item for item in all_items if item.inspection_result is not None]

    def find_with_waste(self) -> List[Item]:
        """TODO: Implement"""
        with get_session() as session:
            item_models = (
                session.query(ItemModel).filter(ItemModel.waste_quantity > 0).all()
            )
            workflow_models = session.query(ItemWorkflowStepsModel).all()
            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }
            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                items.append(self._mapper.to_domain(item_model, workflow_model))
            return items

    def find_by_quality_status(self, passed: bool) -> List[Item]:
        """TODO: Implement"""
        raise NotImplementedError("Quality status queries not yet implemented")

    def find_created_between(
        self, start_date: datetime, end_date: datetime
    ) -> List[Item]:
        """TODO: Implement"""
        with get_session() as session:
            item_models = (
                session.query(ItemModel)
                .filter(
                    ItemModel.created_at >= start_date, ItemModel.created_at <= end_date
                )
                .all()
            )
            workflow_models = session.query(ItemWorkflowStepsModel).all()
            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }
            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                items.append(self._mapper.to_domain(item_model, workflow_model))
            return items

    def find_updated_since(self, since_date: datetime) -> List[Item]:
        """TODO: Implement"""
        with get_session() as session:
            item_models = (
                session.query(ItemModel)
                .filter(ItemModel.updated_at >= since_date)
                .all()
            )
            workflow_models = session.query(ItemWorkflowStepsModel).all()
            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }
            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                items.append(self._mapper.to_domain(item_model, workflow_model))
            return items

    def find_by_step_completion_date(self, step, completion_date) -> List[Item]:
        """TODO: Implement"""
        raise NotImplementedError("Step completion date queries not yet implemented")

    def find_by_employee(self, employee_name: str) -> List[Item]:
        """TODO: Implement - search all workflow step fields"""
        with get_session() as session:
            workflow_models = (
                session.query(ItemWorkflowStepsModel)
                .filter(
                    (ItemWorkflowStepsModel.data_checked_by == employee_name)
                    | (ItemWorkflowStepsModel.documents_checked_by == employee_name)
                    | (ItemWorkflowStepsModel.measured_by == employee_name)
                    | (ItemWorkflowStepsModel.visually_inspected_by == employee_name)
                    | (ItemWorkflowStepsModel.documents_merged_by == employee_name)
                    | (ItemWorkflowStepsModel.completed_by == employee_name)
                )
                .all()
            )

            if not workflow_models:
                return []

            composite_keys = [
                (w.article_number, w.batch_number, w.delivery_number)
                for w in workflow_models
            ]

            item_models = (
                session.query(ItemModel)
                .filter(ItemModel.article_number.in_([k[0] for k in composite_keys]))
                .all()
            )

            workflow_dict = {
                (w.article_number, w.batch_number, w.delivery_number): w
                for w in workflow_models
            }

            items = []
            for item_model in item_models:
                key = (
                    item_model.article_number,
                    item_model.batch_number,
                    item_model.delivery_number,
                )
                workflow_model = workflow_dict.get(key)
                if workflow_model:
                    items.append(self._mapper.to_domain(item_model, workflow_model))
            return items

    def find_by_step_employee(self, step, employee_name: str) -> List[Item]:
        """TODO: Implement"""
        raise NotImplementedError("Step employee queries not yet implemented")

    def get_status_distribution(self) -> dict:
        """TODO: Implement"""
        all_items = self.find_domain_all()
        distribution = {}
        for item in all_items:
            status = item.get_current_status()
            distribution[status] = distribution.get(status, 0) + 1
        return distribution

    def get_completion_statistics(self) -> dict:
        """TODO: Implement"""
        all_items = self.find_domain_all()
        total = len(all_items)
        completed = sum(1 for item in all_items if item.completed_by)
        rejected = sum(1 for item in all_items if item.rejected_by)
        in_progress = total - completed - rejected
        return {
            "total": total,
            "completed": completed,
            "rejected": rejected,
            "in_progress": in_progress,
        }

    def get_waste_statistics(self) -> dict:
        """TODO: Implement"""
        raise NotImplementedError("Waste statistics not yet implemented")

    def get_employee_workload(self) -> dict:
        """TODO: Implement"""
        raise NotImplementedError("Employee workload not yet implemented")

    def search_items(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Item]:
        """TODO: Implement full-text search"""
        raise NotImplementedError("Full-text search not yet implemented")

    def find_by_advanced_criteria(self, criteria: dict) -> List[Item]:
        """TODO: Implement advanced search"""
        raise NotImplementedError("Advanced search not yet implemented")

    def find_by_criteria(self, **kwargs) -> List[Item]:
        """TODO: Implement generic criteria search"""
        raise NotImplementedError("Criteria search not yet implemented")

    def update_item_info_order_quantity(
        self, article_number: str, order_quantity: int, order_number: str
    ) -> bool:
        """
        Aktualisiert die Bestellmenge in der ItemInfo Tabelle.

        Diese Methode wird vom DocumentProcessingService aufgerufen,
        wenn ein Bestelldokument verarbeitet wird.

        Args:
            article_number: Artikelnummer
            order_quantity: Bestellte Menge
            order_number: Bestellnummer

        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            with get_session() as session:
                from warehouse.infrastructure.database.models.item_model import (
                    ItemInfoModel,
                )

                # Finde oder erstelle ItemInfo
                item_info = session.get(ItemInfoModel, article_number)

                if not item_info:
                    # Erstelle neue ItemInfo wenn nicht vorhanden
                    item_info = ItemInfoModel(
                        article_number=article_number,
                        designation=f"Artikel {article_number}",  # Placeholder
                    )
                    session.add(item_info)

                # TODO: ItemInfo hat kein order_quantity Feld
                # Entweder Feld hinzufügen oder in separater Tabelle speichern
                # Für jetzt nur loggen
                logger.info(
                    f"Order quantity update requested for {article_number}: "
                    f"{order_quantity} units (order: {order_number})"
                )

                return True

        except Exception as e:
            logger.error(f"Error updating item info order quantity: {e}")
            return False

    def get_repository_statistics(self) -> dict:
        """Gibt Repository-Statistiken zurück."""
        all_items = self.find_domain_all()
        status_dist = self.get_status_distribution()
        completion_stats = self.get_completion_statistics()

        # NEU: waste_quantity ist nicht mehr direkt im Item, sondern in inspection_result
        total_waste = sum(
            item.inspection_result.waste_quantity
            for item in all_items
            if item.inspection_result is not None
        )

        return {
            "total_items": len(all_items),
            "status_distribution": status_dist,
            "completion_statistics": completion_stats,
            "total_quantity": sum(item.delivered_quantity for item in all_items),
            "waste_quantity": total_waste,
        }
