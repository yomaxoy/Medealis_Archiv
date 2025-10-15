"""
Popup Validators
Common validation functions for popup form fields.
"""

from typing import Tuple, Any, Callable, Optional
import re
from datetime import date, datetime


class PopupValidator:
    """
    Sammlung von Validierungs-Funktionen für Popup-Felder.

    Alle Validator-Funktionen geben ein Tuple zurück: (is_valid, error_message)
    """

    @staticmethod
    def required(value: Any, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft ob Feld ausgefüllt ist.

        Args:
            value: Wert zum Validieren
            field_name: Name des Feldes für Fehlermeldung

        Returns:
            (True, "") wenn valid, sonst (False, error_message)
        """
        if value is None:
            return False, f"❌ {field_name} ist erforderlich!"

        if isinstance(value, str) and not value.strip():
            return False, f"❌ {field_name} ist erforderlich!"

        return True, ""

    @staticmethod
    def min_length(value: str, min_len: int, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft Mindestlänge eines Strings.

        Args:
            value: String-Wert
            min_len: Mindestlänge
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, str):
            return False, f"❌ {field_name} muss ein Text sein!"

        if len(value.strip()) < min_len:
            return False, f"❌ {field_name} muss mindestens {min_len} Zeichen haben!"

        return True, ""

    @staticmethod
    def max_length(value: str, max_len: int, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft Maximallänge eines Strings.

        Args:
            value: String-Wert
            max_len: Maximallänge
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, str):
            return False, f"❌ {field_name} muss ein Text sein!"

        if len(value.strip()) > max_len:
            return False, f"❌ {field_name} darf maximal {max_len} Zeichen haben!"

        return True, ""

    @staticmethod
    def min_value(value: Any, min_val: float, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft Minimalwert einer Zahl.

        Args:
            value: Numerischer Wert
            min_val: Minimalwert
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, (int, float)):
            return False, f"❌ {field_name} muss eine Zahl sein!"

        if value < min_val:
            return False, f"❌ {field_name} muss mindestens {min_val} sein!"

        return True, ""

    @staticmethod
    def max_value(value: Any, max_val: float, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft Maximalwert einer Zahl.

        Args:
            value: Numerischer Wert
            max_val: Maximalwert
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, (int, float)):
            return False, f"❌ {field_name} muss eine Zahl sein!"

        if value > max_val:
            return False, f"❌ {field_name} darf maximal {max_val} sein!"

        return True, ""

    @staticmethod
    def in_range(value: Any, min_val: float, max_val: float, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft ob Wert in Range liegt.

        Args:
            value: Numerischer Wert
            min_val: Minimalwert
            max_val: Maximalwert
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, (int, float)):
            return False, f"❌ {field_name} muss eine Zahl sein!"

        if value < min_val or value > max_val:
            return False, f"❌ {field_name} muss zwischen {min_val} und {max_val} liegen!"

        return True, ""

    @staticmethod
    def is_email(value: str, field_name: str = "E-Mail") -> Tuple[bool, str]:
        """
        Prüft ob String eine gültige E-Mail ist.

        Args:
            value: E-Mail String
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, str):
            return False, f"❌ {field_name} muss ein Text sein!"

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, value.strip()):
            return False, f"❌ {field_name} ist keine gültige E-Mail-Adresse!"

        return True, ""

    @staticmethod
    def is_date_in_past(value: date, field_name: str = "Datum") -> Tuple[bool, str]:
        """
        Prüft ob Datum in der Vergangenheit liegt.

        Args:
            value: Datum
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, date):
            return False, f"❌ {field_name} muss ein Datum sein!"

        if value > date.today():
            return False, f"❌ {field_name} darf nicht in der Zukunft liegen!"

        return True, ""

    @staticmethod
    def is_date_in_future(value: date, field_name: str = "Datum") -> Tuple[bool, str]:
        """
        Prüft ob Datum in der Zukunft liegt.

        Args:
            value: Datum
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, date):
            return False, f"❌ {field_name} muss ein Datum sein!"

        if value < date.today():
            return False, f"❌ {field_name} muss in der Zukunft liegen!"

        return True, ""

    @staticmethod
    def matches_pattern(value: str, pattern: str, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft ob String einem Regex-Pattern entspricht.

        Args:
            value: String-Wert
            pattern: Regex-Pattern
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, str):
            return False, f"❌ {field_name} muss ein Text sein!"

        if not re.match(pattern, value.strip()):
            return False, f"❌ {field_name} hat ein ungültiges Format!"

        return True, ""

    @staticmethod
    def is_article_number(value: str) -> Tuple[bool, str]:
        """
        Prüft ob String eine gültige Artikelnummer ist.

        Format: MG0001, SG0002, etc.

        Args:
            value: Artikelnummer

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, str):
            return False, "❌ Artikelnummer muss ein Text sein!"

        # Pattern: 2 Buchstaben + 4-6 Ziffern
        article_pattern = r'^[A-Z]{2}\d{4,6}$'

        if not re.match(article_pattern, value.strip().upper()):
            return False, "❌ Artikelnummer hat ungültiges Format (erwartetes Format: MG0001)!"

        return True, ""

    @staticmethod
    def is_batch_number(value: str) -> Tuple[bool, str]:
        """
        Prüft ob String eine gültige Chargennummer ist.

        Args:
            value: Chargennummer

        Returns:
            (True, "") wenn valid
        """
        if not isinstance(value, str):
            return False, "❌ Chargennummer muss ein Text sein!"

        # Mindestens 3 Zeichen
        if len(value.strip()) < 3:
            return False, "❌ Chargennummer muss mindestens 3 Zeichen haben!"

        return True, ""

    @staticmethod
    def one_of(value: Any, allowed_values: list, field_name: str = "Feld") -> Tuple[bool, str]:
        """
        Prüft ob Wert in Liste erlaubter Werte ist.

        Args:
            value: Wert
            allowed_values: Liste erlaubter Werte
            field_name: Name des Feldes

        Returns:
            (True, "") wenn valid
        """
        if value not in allowed_values:
            return False, f"❌ {field_name} muss einer der folgenden Werte sein: {', '.join(map(str, allowed_values))}"

        return True, ""

    @staticmethod
    def combine_validators(*validators: Callable[[Any], Tuple[bool, str]]) -> Callable[[Any], Tuple[bool, str]]:
        """
        Kombiniert mehrere Validatoren zu einem.

        Args:
            *validators: Liste von Validator-Funktionen

        Returns:
            Kombinierter Validator

        Beispiel:
            ```python
            validator = PopupValidator.combine_validators(
                lambda v: PopupValidator.required(v, "Name"),
                lambda v: PopupValidator.min_length(v, 2, "Name")
            )

            is_valid, error = validator("AB")
            ```
        """
        def combined_validator(value: Any) -> Tuple[bool, str]:
            for validator in validators:
                is_valid, error = validator(value)
                if not is_valid:
                    return False, error
            return True, ""

        return combined_validator


# Convenience-Funktionen für häufige Validierungen

def validate_employee_name(name: str) -> Tuple[bool, str]:
    """Validiert Mitarbeitername (min. 2 Zeichen)."""
    return PopupValidator.combine_validators(
        lambda v: PopupValidator.required(v, "Mitarbeitername"),
        lambda v: PopupValidator.min_length(v, 2, "Mitarbeitername")
    )(name)


def validate_quantity(quantity: int, min_value: int = 0) -> Tuple[bool, str]:
    """Validiert Mengenangabe."""
    return PopupValidator.combine_validators(
        lambda v: PopupValidator.required(v, "Menge"),
        lambda v: PopupValidator.min_value(v, min_value, "Menge")
    )(quantity)


def validate_article_data(article_number: str, batch_number: str) -> Tuple[bool, str]:
    """Validiert Artikel- und Chargennummer zusammen."""
    # Artikelnummer
    is_valid, error = PopupValidator.is_article_number(article_number)
    if not is_valid:
        return False, error

    # Chargennummer
    is_valid, error = PopupValidator.is_batch_number(batch_number)
    if not is_valid:
        return False, error

    return True, ""
