# src/warehouse/domain/value_objects/batch_number.py

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchNumber:
    """19-stellige Chargennummer (z.B. P-293520240528)."""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Chargennummer darf nicht leer sein")

        # Format: P-123456789012-1234 oder P-123456789012-12345
        if not self.value.startswith("P-"):
            raise ValueError("Chargennummer muss mit 'P-' beginnen")

        parts = self.value.split("-")
        if len(parts) != 3:
            raise ValueError("Chargennummer muss Format P-XXXXXXXXXXXX-XXXX haben")

        # Prüfe ersten Teil (12 Ziffern nach P-)
        if len(parts[1]) != 12 or not parts[1].isdigit():
            raise ValueError("Nach 'P-' müssen genau 12 Ziffern folgen")

        # Prüfe zweiten Teil (4 oder 5 Ziffern)
        if len(parts[2]) not in [4, 5] or not parts[2].isdigit():
            raise ValueError(
                "Nach dem zweiten Bindestrich müssen 4 oder 5 Ziffern folgen"
            )

    def __str__(self) -> str:
        return self.value
