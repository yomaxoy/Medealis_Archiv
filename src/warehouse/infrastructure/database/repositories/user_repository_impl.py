# src/warehouse/infrastructure/database/repositories/user_repository_impl.py

import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from warehouse.domain.entities.user import User
from warehouse.domain.repositories.user_repository import UserRepository
from warehouse.domain.value_objects.username import Username
from warehouse.domain.value_objects.email import Email
from warehouse.domain.enums.user_role import UserRole
from warehouse.domain.exceptions.user_exceptions import UserAlreadyExistsError
from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.user_model import UserModel

logger = logging.getLogger(__name__)


class UserRepositoryImpl(UserRepository):
    """SQLAlchemy-Implementation des UserRepository."""

    def save(self, user: User) -> User:
        """Speichert oder aktualisiert einen User."""
        try:
            with get_session() as session:
                # Prüfe ob User existiert
                existing = (
                    session.query(UserModel)
                    .filter(UserModel.user_id == user.user_id)
                    .first()
                )

                if existing:
                    # Update
                    existing.username = str(user.username)
                    existing.email = str(user.email)
                    existing.password_hash = user.password_hash
                    existing.role = user.role.value
                    existing.is_active = user.is_active
                    existing.must_change_password = user.must_change_password
                    existing.full_name = user.full_name
                    existing.last_login = user.last_login
                    existing.updated_at = datetime.now()
                    existing.created_by = user.created_by
                else:
                    # Create
                    user_model = UserModel(
                        user_id=user.user_id,
                        username=str(user.username),
                        email=str(user.email),
                        password_hash=user.password_hash,
                        role=user.role.value,
                        is_active=user.is_active,
                        must_change_password=user.must_change_password,
                        full_name=user.full_name,
                        last_login=user.last_login,
                        created_at=user.created_at or datetime.now(),
                        updated_at=user.updated_at or datetime.now(),
                        created_by=user.created_by,
                    )
                    session.add(user_model)

                session.commit()
                logger.info(f"User gespeichert: {user.username}")
                return user

        except IntegrityError as e:
            logger.error(
                f"Integrity error beim Speichern von User {user.username}: {str(e)}"
            )
            raise UserAlreadyExistsError(str(user.username))
        except Exception as e:
            logger.error(f"Fehler beim Speichern von User {user.username}: {str(e)}")
            raise

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Findet User anhand der ID."""
        try:
            with get_session() as session:
                user_model = (
                    session.query(UserModel)
                    .filter(UserModel.user_id == user_id)
                    .first()
                )

                if not user_model:
                    return None

                return self._to_entity(user_model)

        except Exception as e:
            logger.error(f"Fehler beim Laden von User {user_id}: {str(e)}")
            return None

    def find_by_username(self, username: Username) -> Optional[User]:
        """Findet User anhand des Benutzernamens."""
        try:
            with get_session() as session:
                user_model = (
                    session.query(UserModel)
                    .filter(UserModel.username == str(username))
                    .first()
                )

                if not user_model:
                    return None

                return self._to_entity(user_model)

        except Exception as e:
            logger.error(f"Fehler beim Laden von User {username}: {str(e)}")
            return None

    def find_by_email(self, email: Email) -> Optional[User]:
        """Findet User anhand der E-Mail."""
        try:
            with get_session() as session:
                user_model = (
                    session.query(UserModel)
                    .filter(UserModel.email == str(email))
                    .first()
                )

                if not user_model:
                    return None

                return self._to_entity(user_model)

        except Exception as e:
            logger.error(f"Fehler beim Laden von User mit Email {email}: {str(e)}")
            return None

    def exists_by_username(self, username: Username) -> bool:
        """Prüft ob ein User mit diesem Benutzernamen existiert."""
        try:
            with get_session() as session:
                count = (
                    session.query(UserModel)
                    .filter(UserModel.username == str(username))
                    .count()
                )
                return count > 0

        except Exception as e:
            logger.error(f"Fehler beim Prüfen von Username {username}: {str(e)}")
            return False

    def exists_by_email(self, email: Email) -> bool:
        """Prüft ob ein User mit dieser E-Mail existiert."""
        try:
            with get_session() as session:
                count = (
                    session.query(UserModel)
                    .filter(UserModel.email == str(email))
                    .count()
                )
                return count > 0

        except Exception as e:
            logger.error(f"Fehler beim Prüfen von Email {email}: {str(e)}")
            return False

    def find_all(self, include_inactive: bool = False) -> List[User]:
        """Gibt alle User zurück."""
        try:
            with get_session() as session:
                query = session.query(UserModel)

                if not include_inactive:
                    query = query.filter(UserModel.is_active.is_(True))

                user_models = query.order_by(UserModel.username).all()
                return [self._to_entity(model) for model in user_models]

        except Exception as e:
            logger.error(f"Fehler beim Laden aller User: {str(e)}")
            return []

    def delete(self, user_id: str) -> bool:
        """Soft-Delete: Deaktiviert den User."""
        try:
            with get_session() as session:
                user_model = (
                    session.query(UserModel)
                    .filter(UserModel.user_id == user_id)
                    .first()
                )

                if not user_model:
                    return False

                user_model.is_active = False
                user_model.updated_at = datetime.now()
                session.commit()

                logger.info(f"User deaktiviert: {user_model.username}")
                return True

        except Exception as e:
            logger.error(f"Fehler beim Löschen von User {user_id}: {str(e)}")
            return False

    def _to_entity(self, model: UserModel) -> User:
        """Konvertiert UserModel zu User Entity."""
        return User(
            user_id=model.user_id,
            username=Username(model.username),
            email=Email(model.email),
            password_hash=model.password_hash,
            role=UserRole(model.role),
            is_active=model.is_active,
            must_change_password=model.must_change_password,
            full_name=model.full_name,
            last_login=model.last_login,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
        )
