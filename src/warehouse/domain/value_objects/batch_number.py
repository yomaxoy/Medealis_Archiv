# src/warehouse/domain/value_objects/batch_number.py

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class BatchNumber:
    """
    Chargennummer für verschiedene Lieferanten.

    Unterstützte Formate:
    - Primec: P-XXXXXXXXXXXX-XXXX (z.B. P-293520240528-1234)
    - Terrats Medical: 6-stellige Ziffern (z.B. 123456)
    - Fleima: xxFL + 6-8 Ziffern (z.B. 26FL007400)
    - Standard: Buchstabe + Zahlen (z.B. B123456, CH789)
    """

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Chargennummer darf nicht leer sein")

        # Keine führenden/nachfolgenden Leerzeichen
        if len(self.value.strip()) != len(self.value):
            raise ValueError("Chargennummer darf keine führenden/nachfolgenden Leerzeichen haben")

        # Validierung verschiedener Formate
        if not self._is_valid_format():
            raise ValueError(
                f"Ungültiges Chargennummern-Format: '{self.value}'. "
                "Erlaubt: Primec (P-XXXXXXXXXXXX-XXXX), Terrats (6 Ziffern), "
                "Fleima (xxFL + 7-8 Ziffern), Standard (Buchstabe+Zahlen)"
            )

    def _is_valid_format(self) -> bool:
        """
        Prüft ob Chargennummer einem bekannten Format entspricht.

        Returns:
            True wenn Format valide ist
        """
        # Format 1: Primec - P-XXXXXXXXXXXX-XXXX
        if self.value.startswith("P-") and "-" in self.value[2:]:
            parts = self.value.split("-")
            if len(parts) == 3:
                if parts[1].isdigit() and parts[2].isdigit():
                    # Strikte Validierung für vollständiges Primec-Format
                    if len(parts[1]) == 12 and len(parts[2]) in [4, 5]:
                        return True

        # Format 2: Terrats Medical - 6 Ziffern
        if re.match(r'^\d{6}$', self.value):
            return True

        # Format 3: Fleima - 2 Ziffern + FL + 6-8 Ziffern
        if re.match(r'^\d{2}FL\d{6,8}$', self.value):
            return True

        # Format 4: Standard - Buchstabe + Zahlen (mindestens 5 Zeichen)
        if len(self.value) >= 5:
            if self.value[0].isalpha() and any(c.isdigit() for c in self.value):
                return True

        # Format 5: Nur Zahlen mit 6+ Stellen (flexibler Fallback)
        if self.value.isdigit() and len(self.value) >= 6:
            return True

        return False

    def is_complete_format(self) -> bool:
        """Prüft ob die Chargennummer ein vollständiges Format hat."""
        # Primec: P-XXXXXXXXXXXX-XXXX
        if self.value.startswith("P-"):
            parts = self.value.split("-")
            if len(parts) != 3:
                return False
            return (len(parts[1]) == 12 and parts[1].isdigit() and
                    len(parts[2]) in [4, 5] and parts[2].isdigit())

        # Terrats: 6 Ziffern
        if re.match(r'^\d{6}$', self.value):
            return True

        # Fleima: 2 Ziffern + FL + 6-8 Ziffern
        if re.match(r'^\d{2}FL\d{6,8}$', self.value):
            return True

        return False

    def needs_completion(self) -> bool:
        """Prüft ob die Chargennummer noch vervollständigt werden muss"""
        return not self.is_complete_format()

    def get_supplier_hint(self) -> str:
        """
        Leitet Lieferanten-Hinweis aus Chargennummer ab.

        Returns:
            Lieferanten-Name oder "Unknown"
        """
        # Terrats Medical Pattern - 6 Ziffern
        if re.match(r'^\d{6}$', self.value):
            return "Terrats Medical"

        # Primec Pattern - P-Format
        if self.value.startswith("P-"):
            return "Primec"

        # Fleima Pattern - xxFL...
        if re.match(r'^\d{2}FL', self.value):
            return "Fleima"

        return "Unknown"

    def __str__(self) -> str:
        return self.value
