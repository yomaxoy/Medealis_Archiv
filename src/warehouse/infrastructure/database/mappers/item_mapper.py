# src/warehouse/infrastructure/database/mappers/item_mapper.py

"""
Item Mapper - Workflow-Steps Version.

Mappt zwischen Item Domain Entity und Database Models:
- ItemModel (Stammdaten)
- ItemWorkflowStepsModel (Status/Workflow)
"""

from typing import Optional
from datetime import datetime

from warehouse.domain.entities.item import Item, InspectionResult
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber
from warehouse.domain.enums.priority_level import PriorityLevel
from warehouse.domain.enums.certificate_type import CertificateType
from warehouse.infrastructure.database.models.item_model import ItemModel
from warehouse.infrastructure.database.models.item_workflow_steps_model import (
    ItemWorkflowStepsModel,
)
from .base_mapper import BaseMapper


class ItemMapper(BaseMapper):
    """
    Mapper zwischen Item Domain Entity und Database Models.

    Verwendet zwei Tabellen:
    1. ItemModel - Stammdaten (Mengen, Zertifikate, etc.)
    2. ItemWorkflowStepsModel - Workflow/Status
    """

    def to_domain(
        self,
        item_model: ItemModel,
        workflow_model: Optional[ItemWorkflowStepsModel] = None,
    ) -> Item:
        """
        Konvertiert Database Models zu Item Domain Entity.

        Args:
            item_model: ItemModel mit Stammdaten
            workflow_model: ItemWorkflowStepsModel mit Workflow-Steps (optional)

        Returns:
            Item Domain Entity
        """
        # Value Objects erstellen
        article_number = ArticleNumber(item_model.article_number)
        batch_number = BatchNumber(item_model.batch_number)

        # Supplier ID direkt aus ItemModel (wurde hinzugefügt zur Denormalisierung)
        supplier_id = item_model.supplier_id or "UNKNOWN"

        # Priority Level
        priority_level = PriorityLevel.MEDIUM  # Default
        # Falls in ItemModel gespeichert, würde hier geladen

        # Item Entity erstellen
        item = Item(
            article_number=article_number,
            batch_number=batch_number,
            delivery_number=item_model.delivery_number,
            supplier_id=supplier_id,
            delivered_quantity=item_model.delivered_quantity or 0,
            employee_name=item_model.employee or "Unknown",
            priority_level=priority_level,
            order_number=item_model.order_number,
            delivery_slip_quantity=item_model.delivery_slip_quantity,
            ordered_quantity=item_model.ordered_quantity,
        )

        # Workflow Steps übertragen (falls vorhanden)
        if workflow_model:
            item.iteminfo_complete_by = workflow_model.iteminfo_complete_by
            item.iteminfo_complete_at = workflow_model.iteminfo_complete_at

            item.data_checked_by = workflow_model.data_checked_by
            item.data_checked_at = workflow_model.data_checked_at

            item.documents_checked_by = workflow_model.documents_checked_by
            item.documents_checked_at = workflow_model.documents_checked_at

            item.measured_by = workflow_model.measured_by
            item.measured_at = workflow_model.measured_at

            item.visually_inspected_by = workflow_model.visually_inspected_by
            item.visually_inspected_at = workflow_model.visually_inspected_at

            item.documents_merged_by = workflow_model.documents_merged_by
            item.documents_merged_at = workflow_model.documents_merged_at

            item.completed_by = workflow_model.completed_by
            item.completed_at = workflow_model.completed_at

            item.rejected_by = workflow_model.rejected_by
            item.rejected_at = workflow_model.rejected_at
            item.rejection_reason = workflow_model.rejection_reason

        # Zertifikate übertragen
        item.certificates[CertificateType.MATERIALZEUGNIS] = (
            item_model.material_certificate or False
        )
        item.certificates[CertificateType.MESSPROTOKOLL] = (
            item_model.measurement_protocol or False
        )
        item.certificates[CertificateType.BESCHICHTUNGSZEUGNIS] = (
            item_model.coating_certificate or False
        )
        item.certificates[CertificateType.HAERTEZEUGNIS] = (
            item_model.hardness_certificate or False
        )
        item.certificates[CertificateType.WEITERE_ZEUGNISSE] = (
            item_model.additional_certificates or False
        )

        # Inspection Result rekonstruieren (falls Sichtkontrolle done)
        if item.visually_inspected_by and item.visually_inspected_at:
            item.inspection_result = InspectionResult(
                performed_at=item.visually_inspected_at,
                performed_by=item.visually_inspected_by,
                waste_quantity=item_model.waste_quantity or 0,
                passed=(item.rejected_by is None),  # Passed wenn nicht rejected
            )

        # Metadaten
        item.notes = item_model.notes or ""
        item.created_at = item_model.created_at
        item.updated_at = item_model.updated_at

        return item

    def to_models(self, entity: Item) -> tuple[ItemModel, ItemWorkflowStepsModel]:
        """
        Konvertiert Item Entity zu Database Models.

        Args:
            entity: Item Domain Entity

        Returns:
            Tuple von (ItemModel, ItemWorkflowStepsModel)
        """
        # ItemModel (Stammdaten)
        item_model = ItemModel(
            article_number=str(entity.article_number),
            batch_number=str(entity.batch_number),
            delivery_number=entity.delivery_number,
            delivered_quantity=entity.delivered_quantity,
            delivery_slip_quantity=entity.delivery_slip_quantity,
            ordered_quantity=entity.ordered_quantity,
            supplier_id=entity.supplier_id or None,  # Denormalisierung für schnellere Abfragen
            employee=entity.created_by or "Unknown",
            notes=entity.notes or "",
            order_number=entity.order_number,
        )

        # Zertifikate
        item_model.material_certificate = entity.certificates.get(
            CertificateType.MATERIALZEUGNIS, False
        )
        item_model.measurement_protocol = entity.certificates.get(
            CertificateType.MESSPROTOKOLL, False
        )
        item_model.coating_certificate = entity.certificates.get(
            CertificateType.BESCHICHTUNGSZEUGNIS, False
        )
        item_model.hardness_certificate = entity.certificates.get(
            CertificateType.HAERTEZEUGNIS, False
        )
        item_model.additional_certificates = entity.certificates.get(
            CertificateType.WEITERE_ZEUGNISSE, False
        )
        item_model.label_present = entity.certificates.get(
            CertificateType.ETIKETT, False
        )
        item_model.accompanying_document = entity.certificates.get(
            CertificateType.BEGLEITSCHEIN, False
        )

        # Waste Quantity (aus InspectionResult)
        if entity.inspection_result:
            item_model.waste_quantity = entity.inspection_result.waste_quantity
        else:
            item_model.waste_quantity = 0

        # ItemWorkflowStepsModel (Status/Workflow)
        workflow_model = ItemWorkflowStepsModel(
            article_number=str(entity.article_number),
            batch_number=str(entity.batch_number),
            delivery_number=entity.delivery_number,
            iteminfo_complete_by=entity.iteminfo_complete_by,
            iteminfo_complete_at=entity.iteminfo_complete_at,
            data_checked_by=entity.data_checked_by,
            data_checked_at=entity.data_checked_at,
            documents_checked_by=entity.documents_checked_by,
            documents_checked_at=entity.documents_checked_at,
            measured_by=entity.measured_by,
            measured_at=entity.measured_at,
            visually_inspected_by=entity.visually_inspected_by,
            visually_inspected_at=entity.visually_inspected_at,
            documents_merged_by=entity.documents_merged_by,
            documents_merged_at=entity.documents_merged_at,
            completed_by=entity.completed_by,
            completed_at=entity.completed_at,
            rejected_by=entity.rejected_by,
            rejected_at=entity.rejected_at,
            rejection_reason=entity.rejection_reason,
        )

        return item_model, workflow_model

    def to_model(self, entity: Item) -> ItemModel:
        """
        BaseMapper Interface - gibt nur ItemModel zurück.

        Für beide Models verwende to_models().
        """
        item_model, _ = self.to_models(entity)
        return item_model

    def update_models(
        self,
        item_model: ItemModel,
        workflow_model: ItemWorkflowStepsModel,
        entity: Item,
    ) -> None:
        """
        Aktualisiert bestehende Models mit Daten aus Entity.

        Args:
            item_model: Bestehendes ItemModel
            workflow_model: Bestehendes ItemWorkflowStepsModel
            entity: Item Entity mit neuen Daten
        """
        # Update ItemModel
        item_model.delivered_quantity = entity.delivered_quantity
        item_model.delivery_slip_quantity = entity.delivery_slip_quantity
        item_model.ordered_quantity = entity.ordered_quantity
        item_model.notes = entity.notes or ""
        item_model.order_number = entity.order_number

        # Zertifikate
        item_model.material_certificate = entity.certificates.get(
            CertificateType.MATERIALZEUGNIS, False
        )
        item_model.measurement_protocol = entity.certificates.get(
            CertificateType.MESSPROTOKOLL, False
        )
        item_model.coating_certificate = entity.certificates.get(
            CertificateType.BESCHICHTUNGSZEUGNIS, False
        )
        item_model.hardness_certificate = entity.certificates.get(
            CertificateType.HAERTEZEUGNIS, False
        )
        item_model.additional_certificates = entity.certificates.get(
            CertificateType.WEITERE_ZEUGNISSE, False
        )
        item_model.label_present = entity.certificates.get(
            CertificateType.ETIKETT, False
        )
        item_model.accompanying_document = entity.certificates.get(
            CertificateType.BEGLEITSCHEIN, False
        )

        # Waste Quantity
        if entity.inspection_result:
            item_model.waste_quantity = entity.inspection_result.waste_quantity
        else:
            item_model.waste_quantity = 0

        item_model.updated_at = datetime.now()

        # Update WorkflowStepsModel
        workflow_model.iteminfo_complete_by = entity.iteminfo_complete_by
        workflow_model.iteminfo_complete_at = entity.iteminfo_complete_at

        workflow_model.data_checked_by = entity.data_checked_by
        workflow_model.data_checked_at = entity.data_checked_at

        workflow_model.documents_checked_by = entity.documents_checked_by
        workflow_model.documents_checked_at = entity.documents_checked_at

        workflow_model.measured_by = entity.measured_by
        workflow_model.measured_at = entity.measured_at

        workflow_model.visually_inspected_by = entity.visually_inspected_by
        workflow_model.visually_inspected_at = entity.visually_inspected_at

        workflow_model.documents_merged_by = entity.documents_merged_by
        workflow_model.documents_merged_at = entity.documents_merged_at

        workflow_model.completed_by = entity.completed_by
        workflow_model.completed_at = entity.completed_at

        workflow_model.rejected_by = entity.rejected_by
        workflow_model.rejected_at = entity.rejected_at
        workflow_model.rejection_reason = entity.rejection_reason

        workflow_model.updated_at = datetime.now()
