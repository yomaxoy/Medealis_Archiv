"""
Terrats Medical - Lieferanten-spezifische Parser-Regeln

Definiert Format-Regeln und Parsing-Logik für Terrats Medical Lieferscheine.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TerratsMedicalParserRules:
    """
    Definiert Terrats Medical-spezifische Lieferschein-Format-Regeln.
    """

    # === ARTIKELNUMMER-FORMAT ===
    ARTICLE_NUMBER_PATTERN = r'^71000\d{2}-\d{1,3}$'
    ARTICLE_NUMBER_EXAMPLES = ["7100001-1", "7100012-45", "7100099-123"]

    # === CHARGENNUMMER-FORMAT (LOT NUMBER) ===
    BATCH_NUMBER_PATTERN = r'^\d{6}$'
    BATCH_NUMBER_LENGTH = 6
    BATCH_NUMBER_EXAMPLES = ["123456", "789012", "456789"]

    # === BESTELLNUMMER-FORMAT (PURCHASE ORDER) ===
    ORDER_NUMBER_LENGTH = 5
    ORDER_NUMBER_POSITION = "below_table"  # Position: unterhalb der Artikel-Tabelle
    ORDER_NUMBER_LABEL = "Purchase Order:"  # Exakte Bezeichnung im Lieferschein
    ORDER_NUMBER_PATTERN = r'^\d{5}$'

    # === LIEFERSCHEIN-LAYOUT ===
    LAYOUT_TYPE = "single_table"  # Nur eine Tabelle pro Lieferschein
    LAYOUT_DESCRIPTION = "Eine Tabelle mit allen Artikeln, Bestellnummer unterhalb"

    # Kopfzeilen-Struktur
    HEADER_SUPPLIER_POSITION = "top_left"
    HEADER_DELIVERY_INFO_POSITION = "top_right"

    # === TABELLEN-SPALTEN ===
    TABLE_COLUMNS = [
        "Artikelnr",      # Spalte 1: Artikelnummer (71000XX-X)
        "[LEER]",         # Spalte 2: Immer leer
        "Beschreibung",   # Spalte 3: Artikel-Beschreibung
        "Lot-Nummer",     # Spalte 4: 6-stellige Chargennummer
        "Menge",          # Spalte 5: Stückzahl
        "Preis",          # Spalte 6: Einzelpreis (nicht relevant für Wareneingang)
        "Rabatt",         # Spalte 7: Rabatt (nicht relevant für Wareneingang)
        "Total"           # Spalte 8: Gesamtpreis (nicht relevant für Wareneingang)
    ]

    # Relevante Spalten für Wareneingang
    RELEVANT_COLUMNS = {
        "article_number": 0,   # Index der Artikelnummer-Spalte
        "description": 2,      # Index der Beschreibungs-Spalte
        "lot_number": 3,       # Index der Lot-Nummer-Spalte
        "quantity": 4          # Index der Mengen-Spalte
    }

    # === BESONDERHEITEN ===
    FEATURES = {
        "single_order_per_slip": True,          # Nur eine Bestellung pro Lieferschein
        "order_number_below_table": True,       # Bestellnummer unterhalb Tabelle
        "no_order_date_on_slip": True,          # Bestelldatum NICHT auf Lieferschein
        "empty_second_column": True,            # Zweite Spalte immer leer
        "requires_manual_order_date": True,     # Bestelldatum muss manuell eingegeben werden
    }


class TerratsMedicalParser:
    """
    Parser für Terrats Medical Lieferscheine.

    Verarbeitet Lieferscheine mit Terrats Medical-spezifischer Struktur.
    """

    def __init__(self):
        self.rules = TerratsMedicalParserRules()
        self.logger = logger

    def validate_article_number(self, article_number: str) -> bool:
        """
        Validiert Terrats Medical Artikelnummer.

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
        Validiert Terrats Medical Chargennummer (Lot Number).

        Args:
            batch_number: Zu validierende Chargennummer

        Returns:
            True wenn valide (6 Ziffern)
        """
        if not batch_number:
            return False

        return bool(re.match(self.rules.BATCH_NUMBER_PATTERN, batch_number))

    def validate_order_number(self, order_number: str) -> bool:
        """
        Validiert Terrats Medical Bestellnummer (Purchase Order).

        Args:
            order_number: Zu validierende Bestellnummer

        Returns:
            True wenn valide (5 Ziffern)
        """
        if not order_number:
            return False

        return bool(re.match(self.rules.ORDER_NUMBER_PATTERN, order_number))

    def extract_order_number_from_text(self, text: str) -> Optional[str]:
        """
        Extrahiert Bestellnummer aus Lieferschein-Text.

        Sucht nach Pattern: "Purchase Order: XXXXX"

        Args:
            text: Lieferschein-Text (OCR oder Claude API Extraktion)

        Returns:
            Extrahierte Bestellnummer oder None
        """
        try:
            # Suche nach "Purchase Order: XXXXX" Pattern
            pattern = r'Purchase\s+Order:\s*(\d{5})'
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                order_number = match.group(1)
                self.logger.info(f"Extracted Terrats Medical order number: {order_number}")
                return order_number

            self.logger.warning("No Purchase Order found in text")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting order number: {e}")
            return None

    def parse_table_row(self, row_data: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parsed eine Tabellenzeile aus Terrats Medical Lieferschein.

        Args:
            row_data: Liste der Spaltenwerte

        Returns:
            Dictionary mit extrahierten Daten oder None bei Fehler
        """
        try:
            if len(row_data) < 5:
                self.logger.warning(f"Insufficient columns in row: {len(row_data)} < 5")
                return None

            # Extrahiere relevante Spalten
            article_number = row_data[self.rules.RELEVANT_COLUMNS["article_number"]].strip()
            description = row_data[self.rules.RELEVANT_COLUMNS["description"]].strip()
            lot_number = row_data[self.rules.RELEVANT_COLUMNS["lot_number"]].strip()
            quantity_str = row_data[self.rules.RELEVANT_COLUMNS["quantity"]].strip()

            # Validierung
            if not self.validate_article_number(article_number):
                self.logger.warning(f"Invalid article number: {article_number}")
                return None

            if not self.validate_batch_number(lot_number):
                self.logger.warning(f"Invalid lot number: {lot_number}")
                return None

            # Parse Quantity
            try:
                quantity = int(quantity_str)
            except ValueError:
                self.logger.warning(f"Invalid quantity: {quantity_str}")
                quantity = 0

            return {
                "article_number": article_number,
                "description": description,
                "batch_number": lot_number,
                "quantity": quantity,
                "unit": "Stück"  # Standard-Einheit
            }

        except Exception as e:
            self.logger.error(f"Error parsing table row: {e}")
            return None

    def get_prompt_instructions(self) -> str:
        """
        Gibt Terrats Medical-spezifische Anweisungen für Claude API Prompt zurück.

        Returns:
            Prompt-Anweisungen als String
        """
        return f"""
TERRATS MEDICAL LIEFERSCHEIN-STRUKTUR:

Layout:
- Lieferantenname: {self.rules.HEADER_SUPPLIER_POSITION} (oben links)
- Lieferscheinnummer + Datum: {self.rules.HEADER_DELIVERY_INFO_POSITION} (oben rechts)
- Artikel-Tabelle mit {len(self.rules.TABLE_COLUMNS)} Spalten
- Bestellnummer: Unterhalb der Tabelle ("Purchase Order: XXXXX")

Tabellen-Spalten (von links nach rechts):
1. Artikelnummer (Format: 71000XX-X, z.B. 7100001-1)
2. [LEER] - Diese Spalte ist immer leer, ignorieren
3. Beschreibung - Artikel-Beschreibung
4. Lot-Nummer - 6-stellige Chargennummer (z.B. 123456)
5. Menge - Stückzahl
6-8. Preis/Rabatt/Total - NICHT relevant für Wareneingang

WICHTIGE PARSING-REGELN:
✓ Artikelnummer: Muss Format 71000XX-X haben (71000 + 2 Ziffern + Bindestrich + 1-3 Ziffern)
✓ Lot-Nummer: Genau 6 Ziffern
✓ Bestellnummer: Suche nach "Purchase Order: XXXXX" unterhalb der Tabelle (5-stellig)
✓ KEINE Block-Struktur: Alle Artikel gehören zur GLEICHEN Bestellnummer
✗ Bestelldatum: NICHT auf Lieferschein vorhanden (wird manuell im System eingegeben)

Beispiel-Extraktion:
{{
    "supplier_name": "Terrats Medical",
    "delivery_number": "LS123456",
    "delivery_date": "01.01.2024",
    "items": [
        {{
            "article_number": "7100001-1",
            "description": "Dental Implantat XY",
            "batch_number": "123456",
            "quantity": 10,
            "unit": "Stück",
            "order_number": "12345"
        }}
    ],
    "order_number": "12345"
}}
"""

    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Gibt Validierungs-Regeln für Terrats Medical zurück.

        Returns:
            Dictionary mit Validierungs-Regeln
        """
        return {
            "article_number": {
                "pattern": self.rules.ARTICLE_NUMBER_PATTERN,
                "examples": self.rules.ARTICLE_NUMBER_EXAMPLES,
                "description": "Format: 71000XX-X (71000 + 2 Ziffern + Bindestrich + 1-3 Ziffern)"
            },
            "batch_number": {
                "pattern": self.rules.BATCH_NUMBER_PATTERN,
                "length": self.rules.BATCH_NUMBER_LENGTH,
                "examples": self.rules.BATCH_NUMBER_EXAMPLES,
                "description": "6-stellige Lot-Nummer"
            },
            "order_number": {
                "pattern": self.rules.ORDER_NUMBER_PATTERN,
                "length": self.rules.ORDER_NUMBER_LENGTH,
                "position": self.rules.ORDER_NUMBER_POSITION,
                "label": self.rules.ORDER_NUMBER_LABEL,
                "description": "5-stellige Purchase Order, unterhalb der Tabelle"
            },
            "layout": {
                "type": self.rules.LAYOUT_TYPE,
                "description": self.rules.LAYOUT_DESCRIPTION,
                "features": self.rules.FEATURES
            }
        }


# Global instance
terrats_medical_parser = TerratsMedicalParser()
