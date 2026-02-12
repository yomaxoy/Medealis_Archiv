# src/warehouse/domain/value_objects/article_number.py

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ArticleNumber:
    """
    Artikelnummer für verschiedene Lieferanten.

    Unterstützte Formate:
    - Standard: Buchstabe + Zahlen (z.B. A0001, B0002, CT003, NE0001_SI00151)
    - Mit Punkten: Artikelnummern können Punkte enthalten (z.B. A0001.123, CT003.5)
    - Terrats Medical: 71000XX-X, 71000XX-XX, 71000XX-XXX (z.B. 7100001-1, 7100012-45)
    - Numerisch: Rein numerische Artikelnummern (z.B. 00307537 von Bredent)
    """

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Artikelnummer darf nicht leer sein")

        # Erlaubte Zeichen: Buchstaben, Zahlen, Unterstriche, Bindestriche und Punkte
        if not all(c.isalnum() or c in '_-.' for c in self.value):
            raise ValueError("Artikelnummer darf nur Buchstaben, Zahlen, Unterstriche, Bindestriche und Punkte enthalten")

        # Validierung verschiedener Formate
        if not self._is_valid_format():
            raise ValueError(
                f"Ungültiges Artikelnummern-Format: '{self.value}'. "
                "Erlaubt: Buchstaben-Prefix (z.B. CT0001), Terrats Medical "
                "(z.B. 7100001-1) oder numerisch (z.B. 00307537)"
            )

    def _is_valid_format(self) -> bool:
        """
        Prüft ob Artikelnummer einem bekannten Format entspricht.

        Returns:
            True wenn Format valide ist
        """
        # Format 1: Standard - Erstes Zeichen ist Buchstabe
        if self.value[0].isalpha():
            return True

        # Format 2: Terrats Medical - 71000XX-X(XX)
        # Pattern: ^71000\d{2}-\d{1,3}$
        terrats_pattern = r'^71000\d{2}-\d{1,3}$'
        if re.match(terrats_pattern, self.value):
            return True

        # Format 3: Numerische Artikelnummern (z.B. 00307537 von Bredent)
        # Pattern: Nur Zahlen, mindestens 4 Stellen
        if self.value.isdigit() and len(self.value) >= 4:
            return True

        # Weitere Formate können hier hinzugefügt werden

        return False

    def get_supplier_hint(self) -> str:
        """
        Leitet Lieferanten-Hinweis aus Artikelnummer ab.

        Returns:
            Lieferanten-Name oder "Unknown"
        """
        # Terrats Medical Pattern
        if re.match(r'^71000\d{2}-\d{1,3}$', self.value):
            return "Terrats Medical"

        # Primec Pattern (CT-Prefix)
        if self.value.startswith("CT"):
            return "Primec"

        # MegaGen Pattern (MG-Prefix)
        if self.value.startswith("MG"):
            return "MEGAGEN"

        return "Unknown"

    def __str__(self) -> str:
        return self.value
