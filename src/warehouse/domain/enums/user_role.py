# src/warehouse/domain/enums/user_role.py

from enum import Enum


class UserRole(str, Enum):
    """Benutzerrollen für das Warehouse Management System."""

    ADMIN = "admin"  # Volle Systemberechtigungen
    MANAGER = "manager"  # Verwaltung von Beständen, Bestellungen
    OPERATOR = "operator"  # Wareneingänge erfassen, Lieferungen bearbeiten
    VIEWER = "viewer"  # Nur Lesezugriff

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Deutscher Anzeigename."""
        names = {
            UserRole.ADMIN: "Administrator",
            UserRole.MANAGER: "Manager",
            UserRole.OPERATOR: "Sachbearbeiter",
            UserRole.VIEWER: "Betrachter",
        }
        return names[self]

    @property
    def permissions(self) -> set[str]:
        """Berechtigungen pro Rolle."""
        perms = {
            UserRole.ADMIN: {
                "user.create",
                "user.read",
                "user.update",
                "user.delete",
                "delivery.create",
                "delivery.read",
                "delivery.update",
                "delivery.delete",
                "order.create",
                "order.read",
                "order.update",
                "order.delete",
                "supplier.create",
                "supplier.read",
                "supplier.update",
                "supplier.delete",
                "item.create",
                "item.read",
                "item.update",
                "item.delete",
                "settings.manage",
            },
            UserRole.MANAGER: {
                "delivery.create",
                "delivery.read",
                "delivery.update",
                "order.create",
                "order.read",
                "order.update",
                "supplier.read",
                "supplier.update",
                "item.create",
                "item.read",
                "item.update",
            },
            UserRole.OPERATOR: {
                "delivery.create",
                "delivery.read",
                "delivery.update",
                "item.create",
                "item.read",
                "item.update",
                "order.read",
                "supplier.read",
            },
            UserRole.VIEWER: {
                "delivery.read",
                "order.read",
                "supplier.read",
                "item.read",
            },
        }
        return perms[self]

    def has_permission(self, permission: str) -> bool:
        """Prüft ob die Rolle eine bestimmte Berechtigung hat."""
        return permission in self.permissions
