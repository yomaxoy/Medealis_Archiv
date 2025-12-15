# src/warehouse/domain/value_objects/username.py

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Username:
    """Value Object für Benutzernamen."""

    value: str

    MIN_LENGTH = 3
    MAX_LENGTH = 50

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Benutzername darf nicht leer sein")

        normalized = self.value.strip()

        # Längenvalidierung
        if len(normalized) < self.MIN_LENGTH:
            raise ValueError(
                f"Benutzername muss mindestens {self.MIN_LENGTH} Zeichen lang sein"
            )

        if len(normalized) > self.MAX_LENGTH:
            raise ValueError(
                f"Benutzername darf maximal {self.MAX_LENGTH} Zeichen lang sein"
            )

        # Format-Validierung: Buchstaben, Zahlen, Unterstrich, Punkt
        pattern = r"^[a-zA-Z0-9_.]+$"
        if not re.match(pattern, normalized):
            raise ValueError(
                "Benutzername darf nur Buchstaben, Zahlen, "
                "Unterstriche und Punkte enthalten"
            )

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, Username):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)
