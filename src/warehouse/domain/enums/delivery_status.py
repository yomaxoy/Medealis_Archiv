# src/warehouse/domain/enums/delivery_status.py

from enum import Enum


class DeliveryStatus(Enum):
    """
    Enum für den Status einer Lieferung im Wareneingangs-Workflow.

    Verwaltet den Gesamtstatus einer Lieferung basierend auf dem
    Bearbeitungsstand aller enthaltenen Artikel.
    """

    # Grundstatus
    EMPFANGEN = "Empfangen"  # Lieferschein eingescannt/erfasst
    ERFASST = "Erfasst"  # Alle Artikel initial angelegt
    IN_BEARBEITUNG = "In Bearbeitung"  # Mindestens ein Artikel wird bearbeitet
    QUALITAETSPRUEFUNG = "Qualitätsprüfung"  # Artikel in Sicht-/Maßprüfung
    DOKUMENTATION = "Dokumentation"  # Dokumentenerstellung läuft
    ABGESCHLOSSEN = "Abgeschlossen"  # Alle Artikel komplett bearbeitet

    @property
    def is_final_status(self) -> bool:
        """Prüft, ob dies ein Endstatus ist."""
        return self in [self.ABGESCHLOSSEN]

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        return self.value
