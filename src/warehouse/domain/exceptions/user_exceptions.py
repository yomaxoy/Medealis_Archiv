# src/warehouse/domain/exceptions/user_exceptions.py

from warehouse.domain.exceptions.base_exceptions import BaseDomainException


class UserException(BaseDomainException):
    """Basis-Exception für User-bezogene Fehler."""

    pass


class UserNotFoundError(UserException):
    """User wurde nicht gefunden."""

    def __init__(self, identifier: str):
        super().__init__(f"Benutzer nicht gefunden: {identifier}")
        self.identifier = identifier


class UserAlreadyExistsError(UserException):
    """User existiert bereits."""

    def __init__(self, username: str):
        super().__init__(f"Benutzer existiert bereits: {username}")
        self.username = username


class InvalidCredentialsError(UserException):
    """Ungültige Anmeldedaten."""

    def __init__(self):
        super().__init__("Benutzername oder Passwort ungültig")


class InsufficientPermissionsError(UserException):
    """Unzureichende Berechtigungen."""

    def __init__(self, required_permission: str):
        super().__init__(f"Fehlende Berechtigung: {required_permission}")
        self.required_permission = required_permission


class UserInactiveError(UserException):
    """User ist inaktiv."""

    def __init__(self, username: str):
        super().__init__(f"Benutzer ist inaktiv: {username}")
        self.username = username
