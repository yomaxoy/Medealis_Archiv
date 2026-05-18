"""
XML Delivery Parser - Parst Lieferscheine im XML-Format ohne AI
Konvertiert XML-Struktur direkt zu standardisiertem JSON-Format
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class XMLDeliveryParser:
    """
    Parser für Lieferscheine im XML-Format.
    Erkennt und konvertiert das standardisierte XML-Format zu JSON.
    """

    # Lieferanten-Normalisierung (aus prompt_template_manager.py)
    SUPPLIER_MAPPINGS = {
        "primec": "Primec",
        "terrats medical": "Terrats Medical",
        "megagen": "MEGAGEN",
        "c-tech": "C-Tech",
        "medealis": "Medealis",
    }

    # Liste der Implantatmarken, die NICHT als Lieferanten akzeptiert werden
    IMPLANT_BRANDS = {
        "straumann", "nobel biocare", "camlog", "bego", "dentsply",
        "zimmer", "astra tech", "anthogyr", "bio horizon", "cortex",
        "dentium", "hiossen", "implantium", "osstem", "southern imps",
        "thommen", "tium", "neodent", "lifecore", "misfit"
    }

    def __init__(self):
        self.logger = logger

    def parse_xml_delivery(self, xml_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parst XML-Lieferschein und konvertiert zu standardisiertem Format.

        Args:
            xml_data: XML-Dokument als Bytes

        Returns:
            Standardisiertes Lieferschein-Dictionary oder None bei Fehler
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_data)

            # Prüfe ob dies das erwartete XML-Format ist
            if root.tag != "Export":
                self.logger.debug(f"XML root tag is '{root.tag}', expected 'Export'")
                return None

            beleg = root.find("Beleg")
            if beleg is None:
                self.logger.debug("No 'Beleg' element found in XML")
                return None

            # Extrahiere Kopfdaten
            delivery_number = self._get_text(beleg, "Belegnummer")
            delivery_date = self._parse_date(self._get_text(beleg, "Datum"))
            customer_name = self._get_text(beleg, "Name")
            supplier_name = self._normalize_supplier_name(customer_name)

            # Extrahiere Positionen (Items)
            items = []
            positions = beleg.findall("Position")

            for position in positions:
                item = self._parse_position(position)
                if item:
                    items.append(item)

            # Baue Result-Struktur
            result = {
                "delivery_number": delivery_number or "Unbekannt",
                "delivery_date": delivery_date or datetime.now().strftime("%d.%m.%Y"),
                "supplier_name": supplier_name,
                "supplier_id": "",
                "employee_name": "Automatischer Import",
                "notes": "Importiert via XML-Parser (ohne KI)",
                "order_number": "",
                "items": items,
                "total_items": len(items),
                "validation_status": {
                    "completeness_score": self._calculate_completeness_score(
                        delivery_number, delivery_date, supplier_name, items
                    ),
                    "missing_critical_fields": self._identify_missing_fields(
                        delivery_number, delivery_date, supplier_name, items
                    ),
                    "uncertain_extractions": [],
                    "user_guidance": "Daten direkt aus XML-Struktur geparst ohne AI-Verarbeitung",
                    "document_quality": "gut" if items else "mittel",
                    "extraction_confidence": "hoch",
                    "manual_review_needed": False,
                    "xml_parsed": True,
                },
                "customer_info": {
                    "kundennummer": self._get_text(beleg, "Kundennummer"),
                    "strasse": self._get_text(beleg, "Strasse"),
                    "plz": self._get_text(beleg, "PLZ"),
                    "ort": self._get_text(beleg, "Ort"),
                }
            }

            self.logger.info(f"Successfully parsed XML delivery: {delivery_number} with {len(items)} items")
            return result

        except ET.ParseError as e:
            self.logger.debug(f"XML parse error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing XML delivery: {e}")
            return None

    def _parse_position(self, position: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parst eine Beleg-Position (Item) aus dem XML.

        Args:
            position: Position XML-Element

        Returns:
            Item-Dictionary oder None
        """
        try:
            article_number = self._get_text(position, "Artikelnummer")
            if not article_number:
                return None

            # Parse quantity - kann Dezimalzahl sein, als Float parsen
            quantity_str = self._get_text(position, "Menge")
            try:
                quantity = float(quantity_str) if quantity_str else 1.0
                # Zu Int konvertieren wenn es eine ganze Zahl ist
                if quantity == int(quantity):
                    quantity = int(quantity)
            except (ValueError, TypeError):
                quantity = 1

            item = {
                "article_number": article_number,
                "batch_number": self._get_text(position, "Charge") or "",
                "quantity": quantity,
                "description": self._get_text(position, "Bezeichnung") or "",
                "unit": self._get_text(position, "Mengeneinheit") or "Stück",
                "order_number": self._get_text(position, "Bestellnummer") or "",
                "order_date": self._parse_date(self._get_text(position, "BestellDatum")),
                "pos_nr": self._get_text(position, "PosNr") or "",
            }

            return item

        except Exception as e:
            self.logger.warning(f"Error parsing position: {e}")
            return None

    def _get_text(self, element: ET.Element, tag: str) -> Optional[str]:
        """
        Extrahiert Textinhalt eines Subelements.

        Args:
            element: Parent-Element
            tag: Tag-Name des Subelements

        Returns:
            Text oder None wenn Element nicht existiert
        """
        sub_element = element.find(tag)
        if sub_element is not None and sub_element.text:
            return sub_element.text.strip()
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Konvertiert Datum zu deutschem Format DD.MM.YYYY.

        Args:
            date_str: Datumsstring in beliebigem Format

        Returns:
            Datum im Format DD.MM.YYYY oder None
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Versuche verschiedene Formate zu parsen
        formats = [
            "%d.%m.%Y",     # Deutsch: 14.04.2026
            "%d.%m.%y",     # Deutsch kurz: 14.04.26
            "%Y-%m-%d",     # ISO: 2026-04-14
            "%d/%m/%Y",     # 14/04/2026
            "%m/%d/%Y",     # US: 04/14/2026
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%d.%m.%Y")
            except ValueError:
                continue

        self.logger.warning(f"Could not parse date: {date_str}")
        return None

    def _normalize_supplier_name(self, name: Optional[str]) -> str:
        """
        Normalisiert Lieferantennamen gemäß Vorgaben.

        Args:
            name: Original-Name des Lieferanten

        Returns:
            Normalisierter Name
        """
        if not name:
            return "Unbekannt"

        name_lower = name.lower().strip()

        # Prüfe auf Implantatmarken (sollten nicht als Lieferanten akzeptiert werden)
        for brand in self.IMPLANT_BRANDS:
            if brand in name_lower:
                self.logger.warning(f"Detected implant brand '{name}' as supplier name, returning 'Unbekannt'")
                return "Unbekannt"

        # Normalisierung durchführen
        for key, normalized in self.SUPPLIER_MAPPINGS.items():
            if key in name_lower:
                return normalized

        # Falls keine Normalisierung möglich, Original zurückgeben
        return name

    def _calculate_completeness_score(
        self,
        delivery_number: Optional[str],
        delivery_date: Optional[str],
        supplier_name: Optional[str],
        items: List[Dict[str, Any]]
    ) -> int:
        """
        Berechnet Vollständigkeitsgrad der extrahierten Daten.

        Args:
            delivery_number: Lieferscheinnummer
            delivery_date: Lieferdatum
            supplier_name: Lieferantenname
            items: Items

        Returns:
            Prozentsatz (0-100)
        """
        score = 0
        max_score = 100

        # Gewichtung für verschiedene Felder
        if delivery_number and delivery_number != "Unbekannt":
            score += 25
        if delivery_date:
            score += 20
        if supplier_name and supplier_name != "Unbekannt":
            score += 20
        if items:
            score += 35
            # Prüfe ob Items vollständig sind
            complete_items = sum(
                1 for item in items
                if item.get("article_number") and item.get("quantity")
            )
            if complete_items == len(items):
                score = min(score, max_score)

        return min(score, max_score)

    def _identify_missing_fields(
        self,
        delivery_number: Optional[str],
        delivery_date: Optional[str],
        supplier_name: Optional[str],
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Identifiziert fehlende kritische Felder.

        Args:
            delivery_number: Lieferscheinnummer
            delivery_date: Lieferdatum
            supplier_name: Lieferantenname
            items: Items

        Returns:
            Liste von fehlenden Feldern
        """
        missing = []

        if not delivery_number or delivery_number == "Unbekannt":
            missing.append("delivery_number")
        if not delivery_date:
            missing.append("delivery_date")
        if not supplier_name or supplier_name == "Unbekannt":
            missing.append("supplier_name")
        if not items:
            missing.append("items")

        return missing

    def is_xml_delivery(self, data: bytes) -> bool:
        """
        Prüft ob Daten ein XML-Lieferschein im erwarteten Format sind.

        Args:
            data: Bytes der zu prüfenden Datei

        Returns:
            True wenn XML-Format erkannt, False sonst
        """
        try:
            root = ET.fromstring(data)
            # Prüfe auf erwartete Struktur
            return (
                root.tag == "Export" and
                root.find("Beleg") is not None and
                root.find("Beleg/Belegnummer") is not None
            )
        except ET.ParseError:
            return False
        except Exception:
            return False
