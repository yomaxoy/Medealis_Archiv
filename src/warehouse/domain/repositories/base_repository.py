# src/warehouse/domain/repositories/base_repository.py

"""
Base Repository Interface für das Warehouse Management System.

Definiert die grundlegenden CRUD-Operationen, die alle Repository-Implementierungen
bereitstellen müssen. Folgt dem Repository Pattern für saubere Trennung zwischen
Domain Logic und Datenpersistierung.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

# Type Variable für generische Repository-Operationen
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstrakte Basis-Klasse für alle Repository-Implementierungen.

    Definiert die Standard-CRUD-Operationen und gemeinsame Patterns
    für Datenzugriff im Warehouse Management System.
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Speichert eine Entity (INSERT oder UPDATE).

        Args:
            entity: Die zu speichernde Entity

        Returns:
            Die gespeicherte Entity (möglicherweise mit generierter ID)

        Raises:
            RepositoryException: Bei Speicherungsfehlern
        """

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Sucht eine Entity anhand ihrer ID.

        Args:
            entity_id: Eindeutige ID der Entity

        Returns:
            Die gefundene Entity oder None
        """

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        Gibt alle Entities dieses Typs zurück.

        Returns:
            Liste aller Entities (kann leer sein)
        """

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Löscht eine Entity anhand ihrer ID.

        Args:
            entity_id: ID der zu löschenden Entity

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Prüft, ob eine Entity mit der gegebenen ID existiert.

        Args:
            entity_id: ID der zu prüfenden Entity

        Returns:
            True wenn Entity existiert, False sonst
        """

    @abstractmethod
    def count(self) -> int:
        """
        Zählt die Anzahl aller Entities dieses Typs.

        Returns:
            Anzahl der Entities
        """

    @abstractmethod
    def find_by_criteria(self, criteria: dict) -> List[T]:
        """
        Sucht Entities basierend auf flexiblen Kriterien.

        Args:
            criteria: Dictionary mit Suchkriterien

        Returns:
            Liste der gefundenen Entities
        """

    # === BATCH OPERATIONS ===

    def save_all(self, entities: List[T]) -> List[T]:
        """
        Speichert mehrere Entities in einem Batch.

        Standard-Implementierung ruft save() für jede Entity auf.
        Kann in konkreten Implementierungen optimiert werden.

        Args:
            entities: Liste der zu speichernden Entities

        Returns:
            Liste der gespeicherten Entities
        """
        return [self.save(entity) for entity in entities]

    def delete_all(self, entity_ids: List[str]) -> int:
        """
        Löscht mehrere Entities in einem Batch.

        Standard-Implementierung ruft delete() für jede ID auf.
        Kann in konkreten Implementierungen optimiert werden.

        Args:
            entity_ids: Liste der zu löschenden Entity-IDs

        Returns:
            Anzahl der tatsächlich gelöschten Entities
        """
        deleted_count = 0
        for entity_id in entity_ids:
            if self.delete(entity_id):
                deleted_count += 1
        return deleted_count

    def find_first_by_criteria(self, criteria: dict) -> Optional[T]:
        """
        Sucht die erste Entity, die den Kriterien entspricht.

        Args:
            criteria: Dictionary mit Suchkriterien

        Returns:
            Erste gefundene Entity oder None
        """
        results = self.find_by_criteria(criteria)
        return results[0] if results else None

    # === VALIDATION HELPERS ===

    def validate_entity(self, _entity: T) -> List[str]:
        """
        Validiert eine Entity vor dem Speichern.

        Standard-Implementierung führt keine Validierung durch.
        Kann in konkreten Implementierungen überschrieben werden.

        Args:
            entity: Zu validierende Entity

        Returns:
            Liste von Validierungsfehlern (leer = gültig)
        """
        return []

    def ensure_valid(self, entity: T) -> None:
        """
        Stellt sicher, dass eine Entity gültig ist.

        Args:
            entity: Zu validierende Entity

        Raises:
            ValueError: Wenn Entity ungültig ist
        """
        errors = self.validate_entity(entity)
        if errors:
            raise ValueError(f"Validierungsfehler: {'; '.join(errors)}")


class ReadOnlyRepository(ABC, Generic[T]):
    """
    Read-Only Repository Interface für schreibgeschützte Zugriffe.

    Nützlich für Reporting, Analytics oder cached Data.
    """

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Sucht Entity anhand ID."""

    @abstractmethod
    def find_all(self) -> List[T]:
        """Gibt alle Entities zurück."""

    @abstractmethod
    def find_by_criteria(self, criteria: dict) -> List[T]:
        """Sucht basierend auf Kriterien."""

    @abstractmethod
    def count(self) -> int:
        """Zählt Entities."""

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Prüft Existenz."""
