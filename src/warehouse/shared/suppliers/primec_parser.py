"""
Primec - Lieferanten-spezifische Parser-Regeln

Definiert Format-Regeln und Parsing-Logik für Primec Lieferscheine.
"""

import re
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PrimecParserRules:
    """
    Definiert Primec-spezifische Lieferschein-Format-Regeln.
    """

    # === ARTIKELNUMMER-FORMAT ===
    ARTICLE_NUMBER_PATTERN = r'^CT\d{4}$'
    ARTICLE_NUMBER_EXAMPLES = ["CT0001", "CT0003", "CT0004"]

    # === CHARGENNUMMER-FORMAT ===
    BATCH_NUMBER_PATTERN = r'^P-\d{12}-\d{4,5}$'
    BATCH_NUMBER_EXAMPLES = ["P-293520240528-1234", "P-293520240528-12345"]

    # === BESTELLNUMMER-FORMAT ===
    ORDER_NUMBER_LENGTH = 5
    ORDER_NUMBER_POSITION = "block_based"  # Position: zwischen Artikel-Blöcken
    ORDER_NUMBER_LABEL = "Bestellnummer:"  # Exakte Bezeichnung im Lieferschein
    ORDER_NUMBER_PATTERN = r'^\d{5}$'

    # === LIEFERSCHEIN-LAYOUT ===
    LAYOUT_TYPE = "block_based"  # Block-basierte Struktur mit mehreren Bestellungen
    LAYOUT_DESCRIPTION = "Mehrere Artikel-Blöcke, getrennt durch Bestellnummern"

    # === BESONDERHEITEN ===
    FEATURES = {
        "multiple_orders_per_slip": True,       # Mehrere Bestellungen pro Lieferschein möglich
        "block_based_structure": True,          # Block-basierte Artikel-Gruppierung
        "order_number_between_blocks": True,    # Bestellnummer zwischen Artikel-Blöcken
        "forward_looking_first_block": True,    # Erster Block nutzt nächste Bestellnummer
    }


class PrimecParser:
    """
    Parser für Primec Lieferscheine.

    Verarbeitet Lieferscheine mit Primec-spezifischer Block-Struktur.
    """

    def __init__(self):
        self.rules = PrimecParserRules()
        self.logger = logger

    def validate_article_number(self, article_number: str) -> bool:
        """
        Validiert Primec Artikelnummer.

        Args:
            article_number: Zu validierende Artikelnummer

        Returns:
            True wenn valide
        """
        if not article_number:
            return False

        return bool(re.match(self.rules.ARTICLE_NUMBER_PATTERN, article_number))

    def validate_batch_number(self, batch_number: str) -> bool:
        """
        Validiert Primec Chargennummer.

        Args:
            batch_number: Zu validierende Chargennummer

        Returns:
            True wenn valide (P-XXXXXXXXXXXX-XXXX Format)
        """
        if not batch_number:
            return False

        return bool(re.match(self.rules.BATCH_NUMBER_PATTERN, batch_number))

    def get_prompt_instructions(self) -> str:
        """
        Gibt Primec-spezifische Anweisungen für Claude API Prompt zurück.

        Returns:
            Prompt-Anweisungen als String
        """
        return f"""
PRIMEC LIEFERSCHEIN-STRUKTUR:

Layout:
- Block-basierte Struktur mit mehreren Artikel-Gruppen
- Bestellnummern erscheinen ZWISCHEN den Artikel-Blöcken
- Ein Lieferschein kann MEHRERE Bestellnungen enthalten

Artikel-Block-Struktur:
BLOCK 1 (bis erste Bestellnummer)
  ├─ CT0003 (Pos 1.1) ← Artikel OHNE direkte Bestellnummer
  └─ Ende bei "Bestellnummer: 10170"
BLOCK 2 (zwischen den Bestellnummern)
  ├─ CT0004 (Pos 1.2) ← Artikel bekommt 10170
  └─ Ende bei "Bestellnummer: 10172"
BLOCK 3 (nach zweiter Bestellnummer)
  └─ MG0001 (Pos 2.1) ← Artikel bekommt 10172

WICHTIGE PARSING-REGELN:
✓ Artikelnummer: Format CT#### (CT + 4 Ziffern)
✓ Chargennummer: Format P-[12 ZIFFERN]-[4-5 ZIFFERN]
  KRITISCH: Chargennummern enthalten NUR ZIFFERN (0-9), NIEMALS Buchstaben!
  Beispiel korrekt: P-293520240528-1234
  Beispiel FALSCH: P-29G520240528-1234 (G muss 6 sein)

  OCR-KORREKTUR für Chargennummern (automatisch anwenden):
  - G/g → 6 (visuell ähnlich)
  - S/s → 5 (visuell ähnlich)
  - O/o → 0 (Null, nicht Buchstabe O)
  - I/l → 1 (Eins, nicht Buchstabe I/l)
  - Z/z → 2, B/b → 8, T/t → 7, Q/q → 9

✓ Bestellnummer: 5-stellig, erscheint als "Bestellnummer: XXXXX vom DD.MM.YYYY"
✓ Block-Logik: Artikel gehören zum BLOCK in dem sie stehen
✓ Forward-Looking: Erster Block ohne Bestellnummer nutzt die NÄCHSTE gefundene Bestellnummer
"""

    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Gibt Validierungs-Regeln für Primec zurück.

        Returns:
            Dictionary mit Validierungs-Regeln
        """
        return {
            "article_number": {
                "pattern": self.rules.ARTICLE_NUMBER_PATTERN,
                "examples": self.rules.ARTICLE_NUMBER_EXAMPLES,
                "description": "Format: CT#### (CT + 4 Ziffern)"
            },
            "batch_number": {
                "pattern": self.rules.BATCH_NUMBER_PATTERN,
                "examples": self.rules.BATCH_NUMBER_EXAMPLES,
                "description": "Format: P-[12 ZIFFERN]-[4-5 ZIFFERN] (nur Ziffern 0-9, keine Buchstaben!)"
            },
            "order_number": {
                "pattern": self.rules.ORDER_NUMBER_PATTERN,
                "length": self.rules.ORDER_NUMBER_LENGTH,
                "position": self.rules.ORDER_NUMBER_POSITION,
                "label": self.rules.ORDER_NUMBER_LABEL,
                "description": "5-stellig, zwischen Artikel-Blöcken"
            },
            "layout": {
                "type": self.rules.LAYOUT_TYPE,
                "description": self.rules.LAYOUT_DESCRIPTION,
                "features": self.rules.FEATURES
            }
        }


# Global instance
primec_parser = PrimecParser()
