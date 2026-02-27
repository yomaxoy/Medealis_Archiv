# src/warehouse/domain/enums/item_status.py

from enum import Enum


class ItemStatus(Enum):
    """
    Enum für den Status eines Artikels im Wareneingangs-Workflow.

    IST-Zustand: Status beschreibt die zuletzt abgeschlossene Aktion,
    nicht die nächste durchzuführende Aktion.

    Definiert die verschiedenen Phasen, die ein Artikel durchläuft,
    von der initialen Erfassung bis zum Abschluss der Verarbeitung.
    Wichtig für Compliance und Rückverfolgbarkeit in der Medizinprodukte-Herstellung.
    """

    # Phase 1: Wareneingang & Datenerfassung
    ARTIKEL_ANGELEGT = "Artikel angelegt"
    DATEN_GEPRUEFT = "Daten geprüft"

    # Phase 2: Dokumenten- & Qualitätsprüfung
    DOKUMENTE_GEPRUEFT = "Dokumente geprüft"
    VERMESSEN = "Vermessen"
    SICHTKONTROLLE_DURCHGEFUEHRT = "Sichtkontrolle durchgeführt"

    # Phase 3: Dokumentenerstellung & Abschluss
    DOKUMENTE_ZUSAMMENGEFUEHRT = "Dokumente zusammengeführt"

    # Phase 4: Finale Stati
    WAREN_EINGELAGERT = "Waren eingelagert"
    AUSSCHUSS = "Ausschuss"

    def is_final_status(self) -> bool:
        """Prüft, ob dies ein Endstatus ist (keine weiteren Übergänge möglich)."""
        return self in [self.WAREN_EINGELAGERT, self.AUSSCHUSS]

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        return self.value
