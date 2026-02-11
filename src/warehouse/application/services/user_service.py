# src/warehouse/application/services/user_service.py

import logging
import uuid
from typing import Optional, List

from warehouse.domain.entities.user import User
from warehouse.domain.repositories.user_repository import UserRepository
from warehouse.domain.value_objects.username import Username
from warehouse.domain.value_objects.email import Email
from warehouse.domain.enums.user_role import UserRole
from warehouse.domain.exceptions.user_exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InsufficientPermissionsError,
    UserInactiveError,
)
from warehouse.infrastructure.security.password_hasher import PasswordHasher

logger = logging.getLogger(__name__)


class UserService:
    """
    Application Service für User-Management.

    Koordiniert Domain-Logik und Infrastructure-Services.
    """

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository
        self._password_hasher = PasswordHasher()

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole,
        full_name: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> User:
        """
        Erstellt einen neuen User.

        Args:
            username: Benutzername
            email: E-Mail-Adresse
            password: Klartext-Passwort
            role: Benutzerrolle
            full_name: Vollständiger Name (optional)
            created_by: User-ID des Erstellers (optional)

        Returns:
            Erstellter User

        Raises:
            UserAlreadyExistsError: Wenn Username oder Email bereits existiert
            ValueError: Bei ungültigen Eingaben
        """
        # Validiere Passwort-Stärke
        is_valid, error_msg = self._password_hasher.validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)

        # Erstelle Value Objects (validiert Format)
        username_vo = Username(username)
        email_vo = Email(email)

        # Prüfe ob bereits vorhanden
        if self._user_repository.exists_by_username(username_vo):
            raise UserAlreadyExistsError(username)

        if self._user_repository.exists_by_email(email_vo):
            raise ValueError(f"E-Mail-Adresse bereits registriert: {email}")

        # Hash Passwort
        password_hash = self._password_hasher.hash_password(password)

        # Erstelle User Entity
        user = User(
            user_id=str(uuid.uuid4()),
            username=username_vo,
            email=email_vo,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
            created_by=created_by,
        )

        # Persistiere
        saved_user = self._user_repository.save(user)
        logger.info(
            f"User erstellt: {saved_user.username} ({saved_user.role.display_name})"
        )

        return saved_user

    def authenticate(self, username: str, password: str) -> User:
        """
        Authentifiziert einen User.

        Args:
            username: Benutzername
            password: Klartext-Passwort

        Returns:
            Authentifizierter User

        Raises:
            InvalidCredentialsError: Bei ungültigen Anmeldedaten
            UserInactiveError: Wenn User inaktiv ist
        """
        try:
            username_vo = Username(username)
        except ValueError:
            raise InvalidCredentialsError()

        user = self._user_repository.find_by_username(username_vo)

        if not user:
            # Timing-Attack-Schutz: Hash trotzdem berechnen
            self._password_hasher.verify_password(password, "dummy")
            raise InvalidCredentialsError()

        # Verifiziere Passwort
        if not self._password_hasher.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        # Prüfe ob aktiv
        if not user.is_active:
            raise UserInactiveError(username)

        # Login erfassen
        user.record_login()
        self._user_repository.save(user)

        logger.info(f"User authentifiziert: {user.username}")
        return user

    def get_user_by_id(self, user_id: str) -> User:
        """
        Lädt User anhand ID.

        Raises:
            UserNotFoundError: Wenn User nicht existiert
        """
        user = self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_user_by_username(self, username: str) -> User:
        """
        Lädt User anhand Benutzername.

        Raises:
            UserNotFoundError: Wenn User nicht existiert
        """
        username_vo = Username(username)
        user = self._user_repository.find_by_username(username_vo)
        if not user:
            raise UserNotFoundError(username)
        return user

    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        """Gibt alle User zurück."""
        return self._user_repository.find_all(include_inactive=include_inactive)

    def update_user_role(
        self, user_id: str, new_role: UserRole, actor_user_id: str
    ) -> User:
        """
        Aktualisiert die Rolle eines Users.

        Args:
            user_id: ID des zu aktualisierenden Users
            new_role: Neue Rolle
            actor_user_id: ID des ausführenden Users

        Returns:
            Aktualisierter User

        Raises:
            UserNotFoundError: Wenn User nicht existiert
            InsufficientPermissionsError: Wenn Actor keine Berechtigung hat
        """
        # Prüfe Berechtigung des Actors
        actor = self.get_user_by_id(actor_user_id)
        if not actor.has_permission("user.update"):
            raise InsufficientPermissionsError("user.update")

        # Lade und aktualisiere User
        user = self.get_user_by_id(user_id)
        user.update_role(new_role)

        saved_user = self._user_repository.save(user)
        logger.info(
            f"User-Rolle aktualisiert: {user.username} -> {new_role.display_name}"
        )

        return saved_user

    def activate_user(self, user_id: str, actor_user_id: str) -> User:
        """Aktiviert einen User."""
        actor = self.get_user_by_id(actor_user_id)
        if not actor.has_permission("user.update"):
            raise InsufficientPermissionsError("user.update")

        user = self.get_user_by_id(user_id)
        user.activate()

        return self._user_repository.save(user)

    def deactivate_user(self, user_id: str, actor_user_id: str) -> User:
        """Deaktiviert einen User."""
        actor = self.get_user_by_id(actor_user_id)
        if not actor.has_permission("user.update"):
            raise InsufficientPermissionsError("user.update")

        user = self.get_user_by_id(user_id)
        user.deactivate()

        return self._user_repository.save(user)

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> None:
        """
        Ändert das Passwort eines Users.

        Args:
            user_id: User ID
            old_password: Altes Passwort
            new_password: Neues Passwort

        Raises:
            InvalidCredentialsError: Wenn altes Passwort falsch
            ValueError: Bei ungültigem neuen Passwort
        """
        user = self.get_user_by_id(user_id)

        # Verifiziere altes Passwort
        if not self._password_hasher.verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError()

        # Validiere neues Passwort
        is_valid, error_msg = self._password_hasher.validate_password_strength(
            new_password
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Hash und speichere neues Passwort
        user.password_hash = self._password_hasher.hash_password(new_password)
        user.must_change_password = False
        self._user_repository.save(user)

        logger.info(f"Passwort geändert für User: {user.username}")

    def force_change_password(self, user_id: str, new_password: str) -> None:
        """
        Erzwungener Passwortwechsel (ohne altes Passwort).

        Wird beim ersten Login mit Default-Passwort verwendet.

        Args:
            user_id: User ID
            new_password: Neues Passwort

        Raises:
            UserNotFoundError: Wenn User nicht existiert
            ValueError: Bei ungültigem neuen Passwort
        """
        user = self.get_user_by_id(user_id)

        # Validiere neues Passwort
        is_valid, error_msg = self._password_hasher.validate_password_strength(
            new_password
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Hash und speichere
        user.password_hash = self._password_hasher.hash_password(new_password)
        user.must_change_password = False
        self._user_repository.save(user)

        logger.info(f"Erzwungener Passwortwechsel für User: {user.username}")

    def reset_password(
        self, user_id: str, new_password: str, actor_user_id: str
    ) -> None:
        """
        Setzt das Passwort eines Users zurück (Admin-Funktion).

        Args:
            user_id: ID des Users
            new_password: Neues Passwort
            actor_user_id: ID des ausführenden Admins

        Raises:
            InsufficientPermissionsError: Wenn Actor kein Admin ist
        """
        actor = self.get_user_by_id(actor_user_id)
        if actor.role != UserRole.ADMIN:
            raise InsufficientPermissionsError("admin required")

        user = self.get_user_by_id(user_id)

        # Validiere neues Passwort
        is_valid, error_msg = self._password_hasher.validate_password_strength(
            new_password
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Hash und speichere — User muss beim nächsten Login Passwort ändern
        user.password_hash = self._password_hasher.hash_password(new_password)
        user.must_change_password = True
        self._user_repository.save(user)

        logger.info(
            f"Passwort zurückgesetzt für User: {user.username} (durch {actor.username})"
        )
