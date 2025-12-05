# src/warehouse/domain/validation/validation_result.py

"""
Validation Result - Domain Value Object.

Represents the result of a validation operation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ValidationError:
    """Single validation error."""

    field_name: str
    error_message: str
    error_code: str  # z.B. "REQUIRED", "INVALID_FORMAT", "TOO_LONG"


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: True wenn keine Fehler
        errors: Liste von ValidationError
        warnings: Liste von Warnings (nicht blockierend)
    """

    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(
        self, field_name: str, error_message: str, error_code: str = "VALIDATION_ERROR"
    ) -> None:
        """Fügt einen Fehler hinzu und setzt is_valid auf False."""
        self.errors.append(ValidationError(field_name, error_message, error_code))
        self.is_valid = False

    def add_warning(self, warning_message: str) -> None:
        """Fügt eine Warnung hinzu (nicht blockierend)."""
        self.warnings.append(warning_message)

    def get_errors_by_field(self, field_name: str) -> List[ValidationError]:
        """Gibt alle Fehler für ein bestimmtes Feld zurück."""
        return [error for error in self.errors if error.field_name == field_name]

    def get_error_messages(self) -> List[str]:
        """Gibt alle Fehlermeldungen als Liste zurück."""
        return [f"{error.field_name}: {error.error_message}" for error in self.errors]

    def get_formatted_errors(self) -> str:
        """
        Gibt alle Fehler als formatierten String zurück.
        Format: "- Feldname: Fehlermeldung\n"
        """
        if not self.errors:
            return ""

        error_lines = [
            f"- {error.field_name}: {error.error_message}" for error in self.errors
        ]
        return "\n".join(error_lines)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merged zwei ValidationResults zusammen."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
        return self

    @staticmethod
    def success() -> "ValidationResult":
        """Factory method für erfolgreiche Validierung."""
        return ValidationResult(is_valid=True)

    @staticmethod
    def failure(
        field_name: str, error_message: str, error_code: str = "VALIDATION_ERROR"
    ) -> "ValidationResult":
        """Factory method für fehlgeschlagene Validierung."""
        result = ValidationResult(is_valid=False)
        result.add_error(field_name, error_message, error_code)
        return result
