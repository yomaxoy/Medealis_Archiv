# src/warehouse/domain/repositories/supplier_repository.py

"""
Supplier Repository Interface für das Warehouse Management System.

ERWEITERT um Domain Object Methoden für Clean Architecture Migration.
Bestehende Methoden bleiben unverändert erhalten.

Definiert spezifische Datenzugriffs-Methoden für Supplier-Entities.
Fokus auf Lieferantenverwaltung und Supplier-bezogene Abfragen.
"""

from abc import abstractmethod
from typing import List, Optional

from warehouse.domain.entities.supplier import Supplier
from warehouse.domain.repositories.base_repository import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    """
    Repository Interface für Supplier-Entities.

    Erweitert BaseRepository um Supplier-spezifische Abfrage-Methoden
    für Lieferantenverwaltung und Supplier-bezogene Analysen.

    ERWEITERT um Domain Object Methoden für Clean Architecture.
    """

    # === DOMAIN OBJECT METHODS (NEU) ===

    @abstractmethod
    def save_domain(self, supplier: Supplier) -> str:
        """
        Speichert Supplier Domain Entity.

        Args:
            supplier: Supplier Domain Entity

        Returns:
            supplier_id des gespeicherten Suppliers
        """

    @abstractmethod
    def find_domain_by_supplier_id(self, supplier_id: str) -> Optional[Supplier]:
        """
        Sucht Supplier Domain Entity per ID.

        Args:
            supplier_id: Supplier-ID

        Returns:
            Supplier Domain Entity oder None
        """

    @abstractmethod
    def find_domain_by_name(self, name: str) -> Optional[Supplier]:
        """
        Sucht Supplier Domain Entity per Namen.

        Args:
            name: Supplier-Name

        Returns:
            Supplier Domain Entity oder None
        """

    @abstractmethod
    def find_domain_all(self) -> List[Supplier]:
        """
        Gibt alle Suppliers als Domain Entities zurück.


        Volltextsuche in Suppliers.

        Args:
            search_term: Suchbegriff
            search_fields: Felder für Suche (None = alle durchsuchbaren Felder)

        Returns:
            Liste der gefundenen Suppliers
        """

    @abstractmethod
    def find_suppliers_with_notes(self) -> List[Supplier]:
        """
        Sucht Suppliers mit hinterlegten Notizen.

        Returns:
            Liste der Suppliers mit Notizen
        """

    @abstractmethod
    def find_suppliers_without_notes(self) -> List[Supplier]:
        """
        Sucht Suppliers ohne Notizen.

        Returns:
            Liste der Suppliers ohne Notizen
        """

    # === BESTEHENDE ALPHABETICAL ORDERING (UNVERÄNDERT) ===

    @abstractmethod
    def find_all_ordered_by_name(self, ascending: bool = True) -> List[Supplier]:
        """
        Gibt alle Suppliers alphabetisch sortiert zurück.

        Args:
            ascending: True für aufsteigend, False für absteigend

        Returns:
            Alphabetisch sortierte Liste aller Suppliers
        """

    @abstractmethod
    def find_all_ordered_by_id(self, ascending: bool = True) -> List[Supplier]:
        """
        Gibt alle Suppliers nach ID sortiert zurück.

        Args:
            ascending: True für aufsteigend, False für absteigend

        Returns:
            Nach ID sortierte Liste aller Suppliers
        """

    # === BESTEHENDE VALIDATION HELPERS (UNVERÄNDERT) ===

    @abstractmethod
    def validate_unique_supplier_id(
        self, supplier_id: str, exclude_current: Optional[str] = None
    ) -> bool:
        """
        Validiert, dass eine Supplier-ID einzigartig ist.

        Args:
            supplier_id: Zu prüfende Supplier-ID
            exclude_current: Aktuelle ID ausschließen (für Updates)

        Returns:
            True wenn einzigartig, False wenn bereits vorhanden
        """

    @abstractmethod
    def validate_unique_name(
        self, name: str, exclude_current: Optional[str] = None
    ) -> bool:
        """
        Validiert, dass ein Supplier-Name einzigartig ist.

        Args:
            name: Zu prüfender Name
            exclude_current: Aktuelle ID ausschließen (für Updates)

        Returns:
            True wenn einzigartig, False wenn bereits vorhanden
        """

    # === BESTEHENDE ANALYTICS & STATISTICS (UNVERÄNDERT) ===

    @abstractmethod
    def get_supplier_name_statistics(self) -> dict:
        """
        Gibt Statistiken zu Supplier-Namen zurück.

        Returns:
            Dictionary mit Namens-Statistiken (Länge, Häufigkeiten, etc.)
        """

    @abstractmethod
    def get_suppliers_by_first_letter(self) -> dict:
        """
        Gruppiert Suppliers nach dem ersten Buchstaben des Namens.

        Returns:
            Dictionary mit Buchstabe -> Liste von Suppliers
        """

    # === BESTEHENDE BULK OPERATIONS (UNVERÄNDERT) ===

    @abstractmethod
    def bulk_update_names(self, name_updates: dict) -> int:
        """
        Aktualisiert mehrere Supplier-Namen in einem Batch.

        Args:
            name_updates: Dictionary mit supplier_id -> neuer_name

        Returns:
            Anzahl der aktualisierten Suppliers
        """

    @abstractmethod
    def bulk_add_notes(self, note_updates: dict) -> int:
        """
        Fügt mehreren Suppliers Notizen hinzu.

        Args:
            note_updates: Dictionary mit supplier_id -> notiz

        Returns:
            Anzahl der aktualisierten Suppliers
        """

    # === BESTEHENDE FUTURE EXTENSIBILITY (UNVERÄNDERT) ===
    # Diese Methoden sind für zukünftige Erweiterungen vorgesehen
    # (Iteration 2): Implementierung supplier-spezifischer Features

    def find_suppliers_requiring_validation_updates(self) -> List[Supplier]:
        """
        Sucht Suppliers, die Validierungsregel-Updates benötigen.

        TODO: Für Iteration 2 - supplier-spezifische Validierung

        Returns:
            Liste der Suppliers mit veralteten Validierungsregeln
        """
        return []

    def get_validation_rules_for_supplier(self, _supplier_id: str) -> dict:
        """
        Gibt supplier-spezifische Validierungsregeln zurück.

        TODO: Für Iteration 2 - ArticleNumber/BatchNumber Validierung

        Args:
            supplier_id: Supplier-ID

        Returns:
            Dictionary mit Validierungsregeln
        """
        return {}

    @abstractmethod
    def update_validation_rules(self, _supplier_id: str, _rules: dict) -> bool:
        """
        Aktualisiert supplier-spezifische Validierungsregeln.

        TODO: Für Iteration 2

        Args:
            supplier_id: Supplier-ID
            rules: Neue Validierungsregeln

        Returns:
            True wenn erfolgreich aktualisiert
        """

    # return True aller Supplier Domain Entities

    @abstractmethod
    def delete_domain(self, supplier_id: str) -> bool:
        """
        Löscht Supplier Domain Entity.

        Args:
            supplier_id: Supplier-ID

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """

    @abstractmethod
    def exists_domain(self, supplier_id: str) -> bool:
        """
        Prüft ob Supplier Domain Entity existiert.

        Args:
            supplier_id: Supplier-ID

        Returns:
            True wenn existiert
        """

    # === DOMAIN OBJECT CONVENIENCE METHODS ===

    @abstractmethod
    def find_domain_by_name_pattern(self, name_pattern: str) -> List[Supplier]:
        """
        Sucht Suppliers nach Namens-Pattern als Domain Entities.

        Args:
            name_pattern: Namens-Pattern

        Returns:
            Liste von Supplier Domain Entities
        """

    @abstractmethod
    def search_domain_suppliers(self, search_term: str) -> List[Supplier]:
        """
        Volltextsuche in Suppliers als Domain Entities.

        Args:
            search_term: Suchbegriff

        Returns:
            Liste von gefundenen Supplier Domain Entities
        """

    # === BESTEHENDE CORE IDENTIFIER QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_supplier_id(self, supplier_id: str) -> Optional[Supplier]:
        """
        Sucht Supplier anhand der Supplier-ID.

        Args:
            supplier_id: Eindeutige Supplier-ID

        Returns:
            Gefundener Supplier oder None
        """

    @abstractmethod
    def supplier_id_exists(self, supplier_id: str) -> bool:
        """
        Prüft, ob eine Supplier-ID bereits existiert.

        Args:
            supplier_id: Zu prüfende Supplier-ID

        Returns:
            True wenn bereits vorhanden, False sonst
        """

    # === BESTEHENDE NAME-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Supplier]:
        """
        Sucht Supplier anhand des exakten Namens.

        Args:
            name: Exakter Supplier-Name

        Returns:
            Gefundener Supplier oder None
        """

    @abstractmethod
    def find_by_name_pattern(self, name_pattern: str) -> List[Supplier]:
        """
        Sucht Suppliers anhand eines Namensmusters.

        Unterstützt Wildcards und Teilstring-Suche.

        Args:
            name_pattern: Namensmuster (z.B. "Bego*", "*Medical*")

        Returns:
            Liste der gefundenen Suppliers
        """

    @abstractmethod
    def find_by_name_starting_with(self, prefix: str) -> List[Supplier]:
        """
        Sucht Suppliers, deren Name mit einem Präfix beginnt.

        Args:
            prefix: Namens-Präfix

        Returns:
            Liste der Suppliers mit passendem Namens-Präfix
        """

    # === BESTEHENDE SEARCH & FILTERING (UNVERÄNDERT) ===

    @abstractmethod
    def search_suppliers(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Supplier]:
        """
        Volltextsuche in Suppliers.

        Args:
            search_term: Suchbegriff
            search_fields: Felder für Suche (None = alle durchsuchbaren Felder)

        Returns:
            Liste
        """
