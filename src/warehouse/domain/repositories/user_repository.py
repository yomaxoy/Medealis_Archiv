# src/warehouse/domain/repositories/user_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List

from warehouse.domain.entities.user import User
from warehouse.domain.value_objects.username import Username
from warehouse.domain.value_objects.email import Email


class UserRepository(ABC):
    """Repository Interface für User-Persistierung."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Speichert oder aktualisiert einen User."""
        pass

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """Findet User anhand der ID."""
        pass

    @abstractmethod
    def find_by_username(self, username: Username) -> Optional[User]:
        """Findet User anhand des Benutzernamens."""
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """Findet User anhand der E-Mail."""
        pass

    @abstractmethod
    def exists_by_username(self, username: Username) -> bool:
        """Prüft ob ein User mit diesem Benutzernamen existiert."""
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """Prüft ob ein User mit dieser E-Mail existiert."""
        pass

    @abstractmethod
    def find_all(self, include_inactive: bool = False) -> List[User]:
        """Gibt alle User zurück."""
        pass

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Löscht einen User (hart oder soft delete je nach Implementierung)."""
        pass
