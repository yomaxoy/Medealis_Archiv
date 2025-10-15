# src/warehouse/infrastructure/database/mappers/supplier_mapper.py

"""
Supplier Mapper - Domain Objects Implementation.
Schlanke Implementierung für Supplier Entity ↔ SupplierModel Mapping.
"""

from datetime import datetime
from typing import Optional

from warehouse.domain.entities.supplier import Supplier
from warehouse.infrastructure.database.models.supplier_model import SupplierModel
from .base_mapper import BaseMapper


class SupplierMapper(BaseMapper):
    """Mapper zwischen Supplier Domain Entity und SupplierModel."""

    def to_domain(self, model: SupplierModel) -> Supplier:
        """Konvertiert SupplierModel zu Supplier Domain Entity."""
        try:
            # Supplier Entity erstellen (dataclass)
            supplier = Supplier(
                supplier_id=model.supplier_id,
                name=model.name,
                created_at=model.created_at,
                updated_at=model.updated_at,
                notes=model.notes,
            )

            return supplier

        except Exception as e:
            print(f"Warning: Error in supplier to_domain mapping: {e}")
            # Fallback
            return self._create_fallback_supplier(model)

    def to_model(self, entity: Supplier) -> SupplierModel:
        """Konvertiert Supplier Entity zu SupplierModel."""
        model = SupplierModel(
            supplier_id=entity.supplier_id, name=entity.name, notes=entity.notes
        )

        # Timestamps werden in __post_init__ gesetzt falls None
        if entity.created_at:
            model.created_at = entity.created_at
        if entity.updated_at:
            model.updated_at = entity.updated_at

        return model

    def update_model(self, model: SupplierModel, entity: Supplier) -> None:
        """Aktualisiert SupplierModel mit Entity-Daten."""
        model.name = entity.name
        model.notes = entity.notes
        # updated_at wird automatisch von SQLAlchemy/Entity gesetzt

    def _create_fallback_supplier(self, model: SupplierModel) -> Supplier:
        """Erstellt Fallback-Supplier bei Mapping-Fehlern."""
        try:
            return Supplier(
                supplier_id=model.supplier_id or "UNKNOWN",
                name=model.name or "Unknown Supplier",
                created_at=model.created_at or datetime.now(),
                updated_at=model.updated_at or datetime.now(),
                notes=model.notes,
            )
        except Exception:
            raise ValueError(f"Kritischer Supplier-Mapping-Fehler für Model: {model}")
