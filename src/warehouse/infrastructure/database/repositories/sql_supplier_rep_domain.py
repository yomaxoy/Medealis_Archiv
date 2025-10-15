# src/warehouse/infrastructure/database/repositories/sqlalchemy_supplier_repository_domain.py

"""
SQLAlchemy Supplier Repository mit Domain Objects - Clean Architecture Implementation.

Implementiert das erweiterte SupplierRepository Interface und gibt Domain Objects zurück.
Vollständige Integration der bestehenden Dictionary-basierten Methoden.
"""

from typing import List, Optional

from warehouse.domain.entities.supplier import Supplier
from warehouse.domain.repositories.supplier_repository import SupplierRepository
from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.supplier_model import SupplierModel
from warehouse.infrastructure.database.mappers.supplier_mapper import SupplierMapper

# REMOVED: No longer import legacy repository
# from warehouse.infrastructure.database.repositories.sql_supplier_repository import (
#     SQLSupplierRepository,
# )

import logging

logger = logging.getLogger(__name__)


class SQLAlchemySupplierRepositoryDomain(SupplierRepository):
    """
    Domain Objects Supplier Repository - vollständig unabhängige Implementation.

    Bietet sowohl Domain Object Methoden als auch Legacy Dictionary Methoden.
    Alle Operationen erfolgen direkt ohne Delegation an Legacy Repository.
    """

    def __init__(self):
        self._mapper = SupplierMapper()
        # REMOVED: self._dict_repo = SQLSupplierRepository()  # No longer needed

    # === DOMAIN OBJECT METHODS (NEU) ===

    def save_domain(self, supplier: Supplier) -> str:
        """Speichert Supplier Domain Entity."""
        with get_session() as session:
            # Prüfe ob bereits vorhanden
            existing_model = session.get(SupplierModel, supplier.supplier_id)

            if existing_model:
                # Update existing
                self._mapper.update_model(existing_model, supplier)
            else:
                # Create new
                new_model = self._mapper.to_model(supplier)
                session.add(new_model)

            return supplier.supplier_id

    def find_domain_by_supplier_id(self, supplier_id: str) -> Optional[Supplier]:
        """Sucht Supplier Domain Entity per ID."""
        with get_session() as session:
            model = session.get(SupplierModel, supplier_id)

            if model:
                return self._mapper.to_domain(model)
            return None

    def find_domain_by_name(self, name: str) -> Optional[Supplier]:
        """Sucht Supplier Domain Entity per Namen."""
        with get_session() as session:
            model = (
                session.query(SupplierModel).filter(SupplierModel.name == name).first()
            )

            if model:
                return self._mapper.to_domain(model)
            return None

    def find_domain_all(self) -> List[Supplier]:
        """Gibt alle Suppliers als Domain Entities zurück. ALWAYS returns list."""
        try:
            with get_session() as session:
                models = session.query(SupplierModel).all()

                # Safety check: models should never be None, but check anyway
                if models is None:
                    logger.warning("query().all() returned None, returning empty list")
                    return []

                return [self._mapper.to_domain(model) for model in models]
        except Exception as e:
            logger.error(f"Error in find_domain_all: {e}")
            # Return empty list instead of None on error
            return []

    def delete_domain(self, supplier_id: str) -> bool:
        """Löscht Supplier Domain Entity."""
        with get_session() as session:
            model = session.get(SupplierModel, supplier_id)

            if model:
                session.delete(model)
                return True
            return False

    def exists_domain(self, supplier_id: str) -> bool:
        """Prüft ob Supplier Domain Entity existiert."""
        with get_session() as session:
            return session.get(SupplierModel, supplier_id) is not None

    # === DOMAIN OBJECT CONVENIENCE METHODS ===

    def find_domain_by_name_pattern(self, name_pattern: str) -> List[Supplier]:
        """Sucht Suppliers nach Namens-Pattern als Domain Entities."""
        with get_session() as session:
            models = (
                session.query(SupplierModel)
                .filter(SupplierModel.name.ilike(f"%{name_pattern}%"))
                .all()
            )

            return [self._mapper.to_domain(model) for model in models]

    def search_domain_suppliers(self, search_term: str) -> List[Supplier]:
        """Volltextsuche in Suppliers als Domain Entities."""
        with get_session() as session:
            from sqlalchemy import or_

            models = (
                session.query(SupplierModel)
                .filter(
                    or_(
                        SupplierModel.name.ilike(f"%{search_term}%"),
                        SupplierModel.supplier_id.ilike(f"%{search_term}%"),
                        SupplierModel.notes.ilike(f"%{search_term}%"),
                    )
                )
                .all()
            )

            return [self._mapper.to_domain(model) for model in models]

    # === BASE REPOSITORY INTERFACE (Domain Objects) ===

    def save(self, entity: Supplier) -> Supplier:
        """BaseRepository save method - delegates to save_domain."""
        self.save_domain(entity)
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Supplier]:
        """BaseRepository find_by_id - expects supplier_id."""
        return self.find_domain_by_supplier_id(entity_id)

    def find_all(self) -> List[Supplier]:
        """BaseRepository find_all - delegates to find_domain_all."""
        return self.find_domain_all()

    def delete(self, entity_id: str) -> bool:
        """BaseRepository delete - expects supplier_id."""
        return self.delete_domain(entity_id)

    def exists(self, entity_id: str) -> bool:
        """BaseRepository exists - expects supplier_id."""
        return self.exists_domain(entity_id)

    def count(self) -> int:
        """BaseRepository count."""
        with get_session() as session:
            return session.query(SupplierModel).count()

    def find_by_criteria(self, criteria: dict) -> List[Supplier]:
        """BaseRepository find_by_criteria - basic implementation."""
        with get_session() as session:
            query = session.query(SupplierModel)

            # Basic criteria filtering
            if "name" in criteria:
                query = query.filter(SupplierModel.name.ilike(f"%{criteria['name']}%"))
            if "supplier_id" in criteria:
                query = query.filter(
                    SupplierModel.supplier_id == criteria["supplier_id"]
                )
            if "has_notes" in criteria:
                if criteria["has_notes"]:
                    query = query.filter(
                        SupplierModel.notes.isnot(None), SupplierModel.notes != ""
                    )
                else:
                    query = query.filter(
                        (SupplierModel.notes.is_(None)) | (SupplierModel.notes == "")
                    )

            models = query.all()
            return [self._mapper.to_domain(model) for model in models]

    # === LEGACY INTERFACE DELEGATION (Bestehende Methoden) ===

    def find_by_supplier_id(self, supplier_id: str) -> Optional[Supplier]:
        """Delegates to domain method."""
        return self.find_domain_by_supplier_id(supplier_id)

    def supplier_id_exists(self, supplier_id: str) -> bool:
        """Delegates to exists_domain."""
        return self.exists_domain(supplier_id)

    def find_by_name(self, name: str) -> Optional[Supplier]:
        """Delegates to domain method."""
        return self.find_domain_by_name(name)

    def find_by_name_pattern(self, name_pattern: str) -> List[Supplier]:
        """Delegates to domain method."""
        return self.find_domain_by_name_pattern(name_pattern)

    def find_by_name_starting_with(self, prefix: str) -> List[Supplier]:
        """Find suppliers whose name starts with prefix."""
        with get_session() as session:
            models = (
                session.query(SupplierModel)
                .filter(SupplierModel.name.ilike(f"{prefix}%"))
                .all()
            )

            return [self._mapper.to_domain(model) for model in models]

    # === SEARCH & FILTERING ===

    def search_suppliers(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Supplier]:
        """Delegates to domain method."""
        return self.search_domain_suppliers(search_term)

    def find_suppliers_with_notes(self) -> List[Supplier]:
        """Find suppliers with notes."""
        with get_session() as session:
            models = (
                session.query(SupplierModel)
                .filter(SupplierModel.notes.isnot(None), SupplierModel.notes != "")
                .all()
            )

            return [self._mapper.to_domain(model) for model in models]

    def find_suppliers_without_notes(self) -> List[Supplier]:
        """Find suppliers without notes."""
        with get_session() as session:
            models = (
                session.query(SupplierModel)
                .filter((SupplierModel.notes.is_(None)) | (SupplierModel.notes == ""))
                .all()
            )

            return [self._mapper.to_domain(model) for model in models]

    # === ALPHABETICAL ORDERING ===

    def find_all_ordered_by_name(self, ascending: bool = True) -> List[Supplier]:
        """Find all suppliers ordered by name."""
        with get_session() as session:
            if ascending:
                models = (
                    session.query(SupplierModel)
                    .order_by(SupplierModel.name.asc())
                    .all()
                )
            else:
                models = (
                    session.query(SupplierModel)
                    .order_by(SupplierModel.name.desc())
                    .all()
                )

            return [self._mapper.to_domain(model) for model in models]

    def find_all_ordered_by_id(self, ascending: bool = True) -> List[Supplier]:
        """Find all suppliers ordered by ID."""
        with get_session() as session:
            if ascending:
                models = (
                    session.query(SupplierModel)
                    .order_by(SupplierModel.supplier_id.asc())
                    .all()
                )
            else:
                models = (
                    session.query(SupplierModel)
                    .order_by(SupplierModel.supplier_id.desc())
                    .all()
                )

            return [self._mapper.to_domain(model) for model in models]

    # === VALIDATION HELPERS ===

    def validate_unique_supplier_id(
        self, supplier_id: str, exclude_current: Optional[str] = None
    ) -> bool:
        """Validate that supplier ID is unique."""
        if exclude_current and supplier_id == exclude_current:
            return True

        return not self.exists_domain(supplier_id)

    def validate_unique_name(
        self, name: str, exclude_current: Optional[str] = None
    ) -> bool:
        """Validate that supplier name is unique."""
        existing_supplier = self.find_domain_by_name(name)

        if not existing_supplier:
            return True

        # If excluding current and this is the current supplier
        if exclude_current and existing_supplier.supplier_id == exclude_current:
            return True

        return False

    # === ANALYTICS & STATISTICS ===

    def get_supplier_name_statistics(self) -> dict:
        """Get supplier name statistics."""
        with get_session() as session:
            from sqlalchemy import func

            total_count = session.query(SupplierModel).count()

            # Name length statistics
            name_lengths = [
                len(model.name)
                for model in session.query(SupplierModel).all()
                if model.name
            ]

            avg_name_length = (
                sum(name_lengths) / len(name_lengths) if name_lengths else 0
            )
            min_name_length = min(name_lengths) if name_lengths else 0
            max_name_length = max(name_lengths) if name_lengths else 0

            return {
                "total_suppliers": total_count,
                "average_name_length": round(avg_name_length, 2),
                "min_name_length": min_name_length,
                "max_name_length": max_name_length,
            }

    def get_suppliers_by_first_letter(self) -> dict:
        """Group suppliers by first letter of name."""
        suppliers = self.find_all_ordered_by_name()

        grouped = {}
        for supplier in suppliers:
            if supplier.name:
                first_letter = supplier.name[0].upper()
                if first_letter not in grouped:
                    grouped[first_letter] = []
                grouped[first_letter].append(supplier)
            else:
                # Handle suppliers without names
                if "?" not in grouped:
                    grouped["?"] = []
                grouped["?"].append(supplier)

        return grouped

    # === BULK OPERATIONS ===

    def bulk_update_names(self, name_updates: dict) -> int:
        """Update multiple supplier names in batch."""
        updated_count = 0

        with get_session() as session:
            for supplier_id, new_name in name_updates.items():
                model = session.get(SupplierModel, supplier_id)
                if model:
                    model.name = new_name
                    updated_count += 1

        return updated_count

    def bulk_add_notes(self, note_updates: dict) -> int:
        """Add notes to multiple suppliers."""
        updated_count = 0

        with get_session() as session:
            for supplier_id, note in note_updates.items():
                model = session.get(SupplierModel, supplier_id)
                if model:
                    if model.notes:
                        model.notes += f"\n{note}"
                    else:
                        model.notes = note
                    updated_count += 1

        return updated_count

    # === FUTURE EXTENSIBILITY ===

    def update_validation_rules(self, supplier_id: str, rules: dict) -> bool:
        """Update supplier-specific validation rules (placeholder)."""
        # TODO: Implement in iteration 2
        return True

    # === PRIVATE HELPER METHODS ===

    def validate_entity(self, entity: Supplier) -> List[str]:
        """Validate Supplier Entity before saving."""
        errors = []

        # Basic validation
        if not entity.supplier_id:
            errors.append("Supplier-ID ist erforderlich")
        if not entity.name:
            errors.append("Supplier-Name ist erforderlich")

        # Business validation
        if len(entity.supplier_id) < 2:
            errors.append("Supplier-ID muss mindestens 2 Zeichen haben")
        if len(entity.supplier_id) > 5:
            errors.append("Supplier-ID darf maximal 5 Zeichen haben")

        return errors

    # === BULK OPERATIONS (Enhanced) ===

    def save_domain_batch(self, suppliers: List[Supplier]) -> List[str]:
        """Save multiple suppliers in batch."""
        saved_ids = []

        with get_session() as session:
            for supplier in suppliers:
                existing_model = session.get(SupplierModel, supplier.supplier_id)

                if existing_model:
                    self._mapper.update_model(existing_model, supplier)
                else:
                    new_model = self._mapper.to_model(supplier)
                    session.add(new_model)

                saved_ids.append(supplier.supplier_id)

        return saved_ids

    # === DEBUGGING & MONITORING ===

    def get_repository_statistics(self) -> dict:
        """Get repository statistics for monitoring."""
        with get_session() as session:
            total_suppliers = session.query(SupplierModel).count()
            suppliers_with_notes = (
                session.query(SupplierModel)
                .filter(SupplierModel.notes.isnot(None), SupplierModel.notes != "")
                .count()
            )

            return {
                "total_suppliers": total_suppliers,
                "suppliers_with_notes": suppliers_with_notes,
                "notes_percentage": (
                    (suppliers_with_notes / total_suppliers * 100)
                    if total_suppliers > 0
                    else 0
                ),
            }
