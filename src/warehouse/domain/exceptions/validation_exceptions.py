# src/warehouse/domain/exceptions/validation_exceptions.py

from warehouse.domain.exceptions.base_exceptions import BaseDomainException
from typing import List


class ValidationException(BaseDomainException):
    """Allgemeine Validierungsfehler."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validierungsfehler bei '{field}': {message}")


class MultipleValidationException(BaseDomainException):
    """Mehrere Validierungsfehler gleichzeitig."""

    def __init__(self, errors: List[ValidationException]):
        self.errors = errors
        error_messages = [error.message for error in errors]
        message = "Mehrere Validierungsfehler:\n" + "\n".join(error_messages)
        super().__init__(message)


class RequiredFieldException(ValidationException):
    """Pflichtfeld ist leer."""

    def __init__(self, field: str):
        super().__init__(field, "Feld ist erforderlich")


class InvalidFormatException(ValidationException):
    """Ungültiges Format."""

    def __init__(self, field: str, expected_format: str):
        super().__init__(field, f"Erwartetes Format: {expected_format}")
