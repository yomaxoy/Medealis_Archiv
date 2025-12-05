# src/warehouse/domain/validation/field_validators.py

"""
Field Validators - Domain Layer.

Grundlegende Feld-Validatoren für verschiedene Datentypen.
"""

import re
from typing import Optional, Any
from .validation_result import ValidationResult


class FieldValidator:
    """Sammlung von statischen Feld-Validatoren."""

    @staticmethod
    def validate_required(
        value: Any, field_name: str, field_label: Optional[str] = None
    ) -> ValidationResult:
        """
        Validiert ob ein Pflichtfeld ausgefüllt ist.

        Args:
            value: Wert zu validieren
            field_name: Technischer Feldname
            field_label: Anzeigename (optional)

        Returns:
            ValidationResult
        """
        label = field_label or field_name

        # None oder leerer String
        if value is None or (isinstance(value, str) and not value.strip()):
            return ValidationResult.failure(
                field_name, f"{label} ist ein Pflichtfeld", "REQUIRED"
            )

        return ValidationResult.success()

    @staticmethod
    def validate_string_length(
        value: Optional[str],
        field_name: str,
        max_length: int,
        field_label: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validiert die maximale Länge eines Strings.

        Args:
            value: String zu validieren
            field_name: Technischer Feldname
            max_length: Maximale Länge
            field_label: Anzeigename (optional)

        Returns:
            ValidationResult
        """
        label = field_label or field_name

        if value is None:
            return ValidationResult.success()  # Nur Länge prüfen, nicht required

        if len(value) > max_length:
            return ValidationResult.failure(
                field_name,
                f"{label} darf maximal {max_length} Zeichen lang sein (aktuell: {len(value)})",
                "TOO_LONG",
            )

        return ValidationResult.success()

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        field_label: Optional[str] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> ValidationResult:
        """
        Validiert ob ein Wert ein Integer ist.

        Args:
            value: Wert zu validieren
            field_name: Technischer Feldname
            field_label: Anzeigename (optional)
            min_value: Minimum (optional)
            max_value: Maximum (optional)

        Returns:
            ValidationResult
        """
        label = field_label or field_name

        if value is None:
            return ValidationResult.success()  # Nur Typ prüfen, nicht required

        # Try to convert to int
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return ValidationResult.failure(
                field_name, f"{label} muss eine ganze Zahl sein", "INVALID_TYPE"
            )

        # Check range
        if min_value is not None and int_value < min_value:
            return ValidationResult.failure(
                field_name, f"{label} muss mindestens {min_value} sein", "OUT_OF_RANGE"
            )

        if max_value is not None and int_value > max_value:
            return ValidationResult.failure(
                field_name, f"{label} darf maximal {max_value} sein", "OUT_OF_RANGE"
            )

        return ValidationResult.success()

    @staticmethod
    def validate_regex(
        value: Optional[str],
        field_name: str,
        pattern: str,
        error_message: str,
        field_label: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validiert ob ein String einem Regex-Pattern entspricht.

        Args:
            value: String zu validieren
            field_name: Technischer Feldname
            pattern: Regex-Pattern
            error_message: Fehlermeldung bei Mismatch
            field_label: Anzeigename (optional)

        Returns:
            ValidationResult
        """
        label = field_label or field_name

        if value is None or not value.strip():
            return ValidationResult.success()  # Nur Pattern prüfen, nicht required

        if not re.match(pattern, value):
            return ValidationResult.failure(
                field_name, f"{label}: {error_message}", "INVALID_FORMAT"
            )

        return ValidationResult.success()

    @staticmethod
    def validate_choice(
        value: Any,
        field_name: str,
        valid_choices: list,
        field_label: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validiert ob ein Wert aus einer Liste von erlaubten Werten ist.

        Args:
            value: Wert zu validieren
            field_name: Technischer Feldname
            valid_choices: Liste erlaubter Werte
            field_label: Anzeigename (optional)

        Returns:
            ValidationResult
        """
        label = field_label or field_name

        if value is None:
            return ValidationResult.success()  # Nur Choice prüfen, nicht required

        if value not in valid_choices:
            return ValidationResult.failure(
                field_name,
                f"{label} muss einer der folgenden Werte sein: {', '.join(map(str, valid_choices))}",
                "INVALID_CHOICE",
            )

        return ValidationResult.success()

    @staticmethod
    def validate_boolean_true(
        value: Any,
        field_name: str,
        error_message: str,
        field_label: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validiert ob ein Boolean True ist (für Checkbox-Pflichtfelder).

        Args:
            value: Wert zu validieren
            field_name: Technischer Feldname
            error_message: Fehlermeldung
            field_label: Anzeigename (optional)

        Returns:
            ValidationResult
        """
        label = field_label or field_name

        if not value:
            return ValidationResult.failure(field_name, error_message, "REQUIRED_TRUE")

        return ValidationResult.success()
