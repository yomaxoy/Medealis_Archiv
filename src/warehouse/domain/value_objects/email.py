# src/warehouse/domain/value_objects/email.py

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Email:
    """Value Object für E-Mail-Adressen."""

    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("E-Mail darf nicht leer sein")

        # Einfache aber robuste Email-Validierung
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value.strip()):
            raise ValueError(f"Ungültige E-Mail-Adresse: {self.value}")

        # Normalisierung: lowercase
        object.__setattr__(self, "value", self.value.strip().lower())

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)
