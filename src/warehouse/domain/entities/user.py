# src/warehouse/domain/entities/user.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from warehouse.domain.enums.user_role import UserRole
from warehouse.domain.value_objects.username import Username
from warehouse.domain.value_objects.email import Email


@dataclass
class User:
    """
    User Entity für das Warehouse Management System.

    Verwaltet Authentifizierung und Autorisierung.
    """

    user_id: str
    username: Username
    email: Email
    password_hash: str
    role: UserRole
    is_active: bool = True
    must_change_password: bool = False
    full_name: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

        # Validierung
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID ist erforderlich")

        if not self.password_hash or not self.password_hash.strip():
            raise ValueError("Password Hash ist erforderlich")

        # Typ-Konvertierung falls nötig
        if isinstance(self.username, str):
            object.__setattr__(self, "username", Username(self.username))

        if isinstance(self.email, str):
            object.__setattr__(self, "email", Email(self.email))

        if isinstance(self.role, str):
            object.__setattr__(self, "role", UserRole(self.role))

    def has_permission(self, permission: str) -> bool:
        """Prüft ob der User eine bestimmte Berechtigung hat."""
        if not self.is_active:
            return False
        return self.role.has_permission(permission)

    def activate(self) -> None:
        """Aktiviert den Benutzer."""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deaktiviert den Benutzer."""
        self.is_active = False
        self.updated_at = datetime.now()

    def update_role(self, new_role: UserRole) -> None:
        """Aktualisiert die Benutzerrolle."""
        self.role = new_role
        self.updated_at = datetime.now()

    def update_profile(
        self, full_name: Optional[str] = None, email: Optional[Email] = None
    ) -> None:
        """Aktualisiert Profil-Informationen."""
        if full_name is not None:
            self.full_name = full_name.strip() if full_name.strip() else None

        if email is not None:
            self.email = email

        self.updated_at = datetime.now()

    def record_login(self) -> None:
        """Erfasst erfolgreichen Login."""
        self.last_login = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für Persistierung."""
        return {
            "user_id": self.user_id,
            "username": str(self.username),
            "email": str(self.email),
            "password_hash": self.password_hash,
            "role": self.role.value,
            "is_active": self.is_active,
            "must_change_password": self.must_change_password,
            "full_name": self.full_name,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Deserialisierung aus Dict."""
        return cls(
            user_id=data["user_id"],
            username=Username(data["username"]),
            email=Email(data["email"]),
            password_hash=data["password_hash"],
            role=UserRole(data["role"]),
            is_active=data.get("is_active", True),
            must_change_password=data.get("must_change_password", False),
            full_name=data.get("full_name"),
            last_login=datetime.fromisoformat(data["last_login"])
            if data.get("last_login")
            else None,
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
            created_by=data.get("created_by"),
        )

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        name = self.full_name or str(self.username)
        return f"{name} ({self.role.display_name})"

    def __repr__(self) -> str:
        """Debug-Repräsentation."""
        return (
            f"User(user_id='{self.user_id}', "
            f"username='{self.username}', role={self.role})"
        )
