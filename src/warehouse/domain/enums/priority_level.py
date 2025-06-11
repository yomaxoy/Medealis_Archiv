# src/warehouse/domain/enums/priority_level.py

from enum import Enum


class PriorityLevel(Enum):
    """
    Enum für Prioritätsstufen im Wareneingangs-Workflow.

    Definiert die Bearbeitungspriorität für Lieferungen und Artikel
    basierend auf Dringlichkeit, Kundenanforderungen und regulatorischen Aspekten.
    """

    LOW = "Niedrig"
    MEDIUM = "Mittel"
    HIGH = "Hoch"

    @property
    def numeric_value(self) -> int:
        """
        Gibt einen numerischen Wert für Sortierung und Vergleiche zurück.

        Returns:
            Numerischer Prioritätswert (höher = wichtiger)
        """
        value_mapping = {
            PriorityLevel.LOW: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.HIGH: 3,
        }
        return value_mapping[self]

    def get_display_color(self) -> str:
        """
        Gibt eine Farbe für die UI-Darstellung zurück.

        Returns:
            Hex-Farbcode für die Prioritätsanzeige
        """
        color_mapping = {
            PriorityLevel.LOW: "#4CAF50",  # Grün
            PriorityLevel.MEDIUM: "#2196F3",  # Blau
            PriorityLevel.HIGH: "#FF9800",  # Orange
        }
        return color_mapping[self]
