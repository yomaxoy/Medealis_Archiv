# src/warehouse/infrastructure/database/mappers/delivery_mapper.py

"""
Delivery Mapper - Domain Objects Implementation.
Schlanke Implementierung für Delivery Entity ↔ DeliveryModel Mapping.
"""

from datetime import datetime, date
from typing import Optional

from warehouse.domain.entities.delivery import Delivery
from warehouse.domain.enums.delivery_status import DeliveryStatus
from warehouse.infrastructure.database.models.delivery_model import DeliveryModel
from .base_mapper import BaseMapper


class DeliveryMapper(BaseMapper):
    """Mapper zwischen Delivery Domain Entity und DeliveryModel."""

    def to_domain(self, model: DeliveryModel) -> Delivery:
        """Konvertiert DeliveryModel zu Delivery Domain Entity."""
        try:
            # Delivery Entity erstellen
            delivery = Delivery(
                delivery_number=model.delivery_number,
                supplier_id=model.supplier_id,
                delivery_date=model.delivery_date,
                employee_name=model.employee_name,
                document_path=model.document_path,
            )

            # Status setzen - robust
            if model.status:
                try:
                    delivery.status = DeliveryStatus(model.status)
                except ValueError:
                    # Fallback für unbekannte Status
                    delivery.status = DeliveryStatus.EMPFANGEN

            # Metadaten
            delivery.notes = model.notes or ""
            delivery.created_at = model.created_at or datetime.now()
            delivery.updated_at = model.updated_at or datetime.now()

            # Items werden separat geladen - nicht hier (Performance)
            # delivery.items bleibt leer, wird bei Bedarf vom Repository gefüllt

            return delivery

        except Exception as e:
            print(f"Warning: Error in delivery to_domain mapping: {e}")
            # Fallback
            return self._create_fallback_delivery(model)

    def to_model(self, entity: Delivery) -> DeliveryModel:
        """Konvertiert Delivery Entity zu DeliveryModel."""
        model = DeliveryModel(
            delivery_number=entity.delivery_number,
            supplier_id=entity.supplier_id,
            delivery_date=entity.delivery_date,
            employee_name=entity.employee_name,
            document_path=entity.document_path,
            status=entity.status.value,
            notes=entity.notes or "",
        )

        return model

    def update_model(self, model: DeliveryModel, entity: Delivery) -> None:
        """Aktualisiert DeliveryModel mit Entity-Daten."""
        model.supplier_id = entity.supplier_id
        model.delivery_date = entity.delivery_date
        model.employee_name = entity.employee_name
        model.document_path = entity.document_path
        model.status = entity.status.value
        model.notes = entity.notes or ""
        # updated_at wird automatisch von SQLAlchemy gesetzt

    def _create_fallback_delivery(self, model: DeliveryModel) -> Delivery:
        """Erstellt Fallback-Delivery bei Mapping-Fehlern."""
        try:
            return Delivery(
                delivery_number=model.delivery_number or "LS000",
                supplier_id=model.supplier_id or "UNKNOWN",
                delivery_date=model.delivery_date or date.today(),
                employee_name=model.employee_name or "Unknown",
                document_path=model.document_path,
            )
        except Exception:
            raise ValueError(f"Kritischer Delivery-Mapping-Fehler für Model: {model}")
