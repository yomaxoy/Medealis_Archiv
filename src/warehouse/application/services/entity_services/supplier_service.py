# src/warehouse/application/services/supplier_service.py

"""
Supplier Service - Application Layer für das Warehouse Management System.

Orchestriert Supplier-bezogene Use Cases und verbindet Domain Logic
mit Infrastructure. Angepasst an deine exakte Projektstruktur.
"""

# Standard library imports
import logging
from typing import Dict, Any, List, Optional

# Domain imports
from warehouse.domain.entities.supplier import Supplier
from warehouse.domain.exceptions.supplier_exceptions import (
    SupplierAlreadyExistsException,
    SupplierNotFoundException,
)

# Infrastructure imports
from warehouse.infrastructure.database.repositories.sql_supplier_rep_domain import (
    SQLAlchemySupplierRepositoryDomain,
)

logger = logging.getLogger(__name__)


class SupplierService:
    """
    Application Service für Supplier-Management.

    Verwaltet den kompletten Lebenszyklus von Lieferanten:
    - Erstellung neuer Suppliers
    - Aktualisierung von Supplier-Daten
    - Suche und Filterung
    - Validierung und Geschäftslogik
    """

    def __init__(self):
        try:
            # Database should already be initialized by Infrastructure Layer
            self.supplier_repo = SQLAlchemySupplierRepositoryDomain()
            logger.info("SupplierService erfolgreich initialisiert")
        except (ImportError, AttributeError, ConnectionError) as e:
            logger.error("Fehler bei SupplierService Initialisierung: %s", e)
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler bei SupplierService Initialisierung: %s", e
            )
            raise

    # === SUPPLIER CREATION & MANAGEMENT ===

    def create_supplier(
        self,
        supplier_id: str,
        name: str,
        notes: Optional[str] = None,
    ) -> str:
        """
        Erstellt einen neuen Supplier.

        Args:
            supplier_id: Eindeutige Supplier-ID
            name: Supplier-Name
            notes: Optionale Notizen

        Returns:
            Supplier-ID des erstellten Suppliers
        """
        try:
            logger.info("Erstelle neuen Supplier: %s", supplier_id)

            # Prüfe, ob Supplier bereits existiert
            if self.supplier_repo.exists_domain(supplier_id):
                raise SupplierAlreadyExistsException(supplier_id)

            # Validiere unique name
            if not self.supplier_repo.validate_unique_name(name):
                raise ValueError("Supplier-Name bereits vergeben: %s" % name)

            # Erstelle Supplier Domain Entity
            supplier = Supplier(
                supplier_id=supplier_id,
                name=name,
                notes=notes,
            )

            # Persistiere in Database
            saved_supplier_id = self.supplier_repo.save_domain(supplier)

            logger.info("Supplier %s erfolgreich erstellt", supplier_id)
            return saved_supplier_id

        except (SupplierAlreadyExistsException, ValueError) as e:
            logger.error(
                "Geschäftslogik-Fehler beim Erstellen des Suppliers %s: %s", supplier_id, e
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Erstellen des Suppliers %s: %s", supplier_id, e
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Erstellen des Suppliers %s: %s", supplier_id, e
            )
            raise

    def get_supplier(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt einen Supplier mit allen Details.

        Args:
            supplier_id: Supplier-ID

        Returns:
            Dictionary mit Supplier-Daten oder None
        """
        try:
            supplier = self.supplier_repo.find_domain_by_supplier_id(supplier_id)
            if not supplier:
                return None

            return {
                "supplier_id": supplier.supplier_id,
                "name": supplier.name,
                "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                "notes": supplier.notes,
            }

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden des Suppliers %s: %s", supplier_id, e
            )
            return None
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden des Suppliers %s: %s", supplier_id, e
            )
            return None

    def update_supplier_name(
        self,
        supplier_id: str,
        new_name: str,
    ) -> bool:
        """
        Aktualisiert den Namen eines Suppliers.

        Args:
            supplier_id: Supplier-ID
            new_name: Neuer Name

        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            logger.info("Aktualisiere Supplier-Name für %s: %s", supplier_id, new_name)

            # Lade Supplier
            supplier = self.supplier_repo.find_domain_by_supplier_id(supplier_id)
            if not supplier:
                raise SupplierNotFoundException(supplier_id)

            # Validiere unique name (exkludiere aktuellen Supplier)
            if not self.supplier_repo.validate_unique_name(new_name, exclude_current=supplier_id):
                raise ValueError("Supplier-Name bereits vergeben: %s" % new_name)

            # Update über Domain Logic
            supplier.update_name(new_name)

            # Persistiere
            self.supplier_repo.save_domain(supplier)

            logger.info("Supplier-Name für %s erfolgreich aktualisiert", supplier_id)
            return True

        except (SupplierNotFoundException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler beim Aktualisieren des Supplier-Namens: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Aktualisieren des Supplier-Namens: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Aktualisieren des Supplier-Namens: %s", e)
            raise

    def add_supplier_notes(
        self,
        supplier_id: str,
        notes: str,
    ) -> bool:
        """
        Fügt Notizen zu einem Supplier hinzu.

        Args:
            supplier_id: Supplier-ID
            notes: Notizen

        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            logger.info("Füge Notizen zu Supplier %s hinzu", supplier_id)

            # Lade Supplier
            supplier = self.supplier_repo.find_domain_by_supplier_id(supplier_id)
            if not supplier:
                raise SupplierNotFoundException(supplier_id)

            # Update über Domain Logic
            supplier.add_notes(notes)

            # Persistiere
            self.supplier_repo.save_domain(supplier)

            logger.info("Notizen für Supplier %s erfolgreich hinzugefügt", supplier_id)
            return True

        except SupplierNotFoundException as e:
            logger.error("Geschäftslogik-Fehler beim Hinzufügen der Notizen: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Hinzufügen der Notizen: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Hinzufügen der Notizen: %s", e)
            raise

    # === SUPPLIER SEARCH & LOOKUP ===

    def get_all_suppliers(self, ordered_by: str = "name") -> List[Dict[str, Any]]:
        """
        Holt alle Suppliers.

        Args:
            ordered_by: Sortierung ("name", "id", "created")

        Returns:
            Liste von Supplier-Dictionaries
        """
        try:
            if ordered_by == "name":
                suppliers = self.supplier_repo.find_all_ordered_by_name()
            elif ordered_by == "id":
                suppliers = self.supplier_repo.find_all_ordered_by_id()
            else:
                suppliers = self.supplier_repo.find_domain_all()

            return [
                {
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                    "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                    "notes": supplier.notes,
                }
                for supplier in suppliers
            ]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden aller Suppliers: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden aller Suppliers: %s", e)
            return []

    def find_suppliers_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Sucht Supplier nach exaktem Namen.

        Args:
            name: Supplier-Name

        Returns:
            Dictionary mit Supplier-Daten oder None
        """
        try:
            supplier = self.supplier_repo.find_domain_by_name(name)
            if not supplier:
                return None

            return {
                "supplier_id": supplier.supplier_id,
                "name": supplier.name,
                "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                "notes": supplier.notes,
            }

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Suchen des Suppliers: %s", e)
            return None
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Suchen des Suppliers: %s", e)
            return None

    def find_suppliers_by_pattern(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Sucht Suppliers nach Namens-Pattern.

        Args:
            name_pattern: Namens-Pattern (z.B. "Bego*")

        Returns:
            Liste von Supplier-Dictionaries
        """
        try:
            suppliers = self.supplier_repo.find_domain_by_name_pattern(name_pattern)

            return [
                {
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                    "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                    "notes": supplier.notes,
                }
                for supplier in suppliers
            ]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Pattern-Suche: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Pattern-Suche: %s", e)
            return []

    def search_suppliers(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Volltext-Suche in Suppliers.

        Args:
            search_term: Suchbegriff

        Returns:
            Liste von gefundenen Supplier-Dictionaries
        """
        try:
            suppliers = self.supplier_repo.search_domain_suppliers(search_term)

            return [
                {
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                    "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                    "notes": supplier.notes,
                }
                for supplier in suppliers
            ]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Volltext-Suche: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Volltext-Suche: %s", e)
            return []

    # === SUPPLIER VALIDATION & UTILITIES ===

    def supplier_exists(self, supplier_id: str) -> bool:
        """Prüft, ob ein Supplier existiert."""
        return self.supplier_repo.exists_domain(supplier_id)

    def validate_supplier_id_unique(self, supplier_id: str) -> bool:
        """Validiert, dass eine Supplier-ID einzigartig ist."""
        return self.supplier_repo.validate_unique_supplier_id(supplier_id)

    def validate_supplier_name_unique(self, name: str, exclude_supplier_id: Optional[str] = None) -> bool:
        """Validiert, dass ein Supplier-Name einzigartig ist."""
        return self.supplier_repo.validate_unique_name(name, exclude_current=exclude_supplier_id)

    # === SUPPLIER STATISTICS & ANALYTICS ===

    def get_supplier_statistics(self) -> Dict[str, Any]:
        """Holt Supplier-Statistiken für Dashboard."""
        try:
            stats = {
                "total_suppliers": len(self.supplier_repo.find_domain_all()),
                "suppliers_with_notes": len(self.supplier_repo.find_suppliers_with_notes()),
                "suppliers_without_notes": len(self.supplier_repo.find_suppliers_without_notes()),
            }

            # Zusätzliche Statistiken
            name_stats = self.supplier_repo.get_supplier_name_statistics()
            stats.update(name_stats)

            suppliers_by_letter = self.supplier_repo.get_suppliers_by_first_letter()
            stats["suppliers_by_first_letter"] = suppliers_by_letter

            return stats

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden der Supplier-Statistiken: %s", e)
            return {}
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden der Supplier-Statistiken: %s", e)
            return {}

    def get_suppliers_with_notes(self) -> List[Dict[str, Any]]:
        """Holt alle Suppliers mit Notizen."""
        try:
            suppliers = self.supplier_repo.find_suppliers_with_notes()

            return [
                {
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "notes": supplier.notes,
                    "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                    "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                }
                for supplier in suppliers
            ]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden der Suppliers mit Notizen: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden der Suppliers mit Notizen: %s", e)
            return []

    def get_suppliers_without_notes(self) -> List[Dict[str, Any]]:
        """Holt alle Suppliers ohne Notizen."""
        try:
            suppliers = self.supplier_repo.find_suppliers_without_notes()

            return [
                {
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                    "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
                }
                for supplier in suppliers
            ]

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden der Suppliers ohne Notizen: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden der Suppliers ohne Notizen: %s", e)
            return []

    def find_or_create_supplier_by_name(self, name: str, notes: str = None) -> str:
        """
        Findet einen Supplier nach Namen oder erstellt einen neuen.

        Args:
            name: Supplier-Name (case-insensitive)
            notes: Optionale Notizen für neuen Supplier

        Returns:
            supplier_id des gefundenen oder erstellten Suppliers

        Raises:
            Exception: Bei Fehlern während der Erstellung
        """
        try:
            name = name.strip()
            logger.info("Suche oder erstelle Supplier: %s", name)

            # Versuche Supplier nach Namen zu finden (case-insensitive)
            suppliers = self.get_all_suppliers()

            for supplier in suppliers:
                if supplier['name'].lower() == name.lower():
                    logger.info("Existierender Supplier gefunden: %s", supplier['supplier_id'])
                    return supplier['supplier_id']

            # Neuen Supplier erstellen
            import uuid
            supplier_id = f"SUP-{str(uuid.uuid4())[:8].upper()}"

            # Standard-Notizen wenn keine angegeben
            if not notes:
                notes = f'Automatisch erstellt beim Import von Lieferschein'

            success = self.create_supplier(
                supplier_id=supplier_id,
                name=name,
                notes=notes
            )

            if success:
                logger.info("Neuer Supplier erstellt: %s", supplier_id)
                return supplier_id
            else:
                raise Exception(f"Supplier-Erstellung fehlgeschlagen für: {name}")

        except Exception as e:
            logger.error("Fehler beim Find-or-Create für Supplier '%s': %s", name, e)
            raise Exception(f"Supplier konnte nicht gefunden oder erstellt werden: {e}")

    # === SUPPLIER DELETION ===

    def delete_supplier(self, supplier_id: str) -> bool:
        """
        Löscht einen Supplier.

        Args:
            supplier_id: Supplier-ID

        Returns:
            True wenn erfolgreich gelöscht
        """
        try:
            logger.info("Lösche Supplier: %s", supplier_id)

            # Prüfe, ob Supplier existiert
            if not self.supplier_repo.exists_domain(supplier_id):
                raise SupplierNotFoundException(supplier_id)

            # Lösche über Repository
            success = self.supplier_repo.delete_domain(supplier_id)

            if success:
                logger.info("Supplier %s erfolgreich gelöscht", supplier_id)
            else:
                logger.warning("Supplier %s konnte nicht gelöscht werden", supplier_id)

            return success

        except SupplierNotFoundException as e:
            logger.error("Geschäftslogik-Fehler beim Löschen des Suppliers: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Löschen des Suppliers: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Löschen des Suppliers: %s", e)
            raise


# Test-Funktion
if __name__ == "__main__":
    print("Testing SupplierService...")
    try:
        service = SupplierService()
        print("✅ SupplierService erfolgreich erstellt!")
    except Exception as e:
        print("❌ Fehler: %s" % e)
        import traceback
        traceback.print_exc()