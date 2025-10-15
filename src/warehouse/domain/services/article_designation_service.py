# src/warehouse/domain/services/article_designation_service.py

"""
Service für standardisierte Artikelbezeichnungen nach Docklocs Schema.
"""

import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)


class ArticleDesignationService:
    """Service für Artikelbezeichnungen nach Docklocs Schema."""

    def __init__(self):
        # Bekannte Implantathersteller und ihre Systeme
        self.implant_systems = {
            "Straumann": ["Standard Plus", "Bone Level", "Tissue Level", "BLX", "BLT"],
            "Nobel": ["Replace", "Active", "Parallel", "Conical", "CC"],
            "Zimmer": ["TSV", "Tapered Screw", "SwissPlus"],
            "Dentsply": ["Astra Tech", "Implant System", "EV"],
            "Camlog": ["Screw Line", "Tube Line", "iSy"],
            "Osstem": ["TS", "GS", "MS", "US"],
            "Hiossen": ["ET", "SA", "SS"],
            # Erweitere diese Liste nach Bedarf
        }

        # Pattern für verschiedene Komponenten
        self.gingival_heights = [
            "0.5mm", "1mm", "1.5mm", "2mm", "2.5mm", "3mm", "3.5mm", "4mm", "4.5mm", "5mm", "6mm"
        ]

    def standardize_designation(self, raw_designation: str) -> Dict[str, str]:
        """
        Standardisiert eine Artikelbezeichnung nach Docklocs Schema.

        Args:
            raw_designation: Rohe Bezeichnung aus dem Lieferschein

        Returns:
            Dict mit standardized_designation, type, manufacturer, system, gingival_height
        """
        logger.info(f"Standardizing designation: {raw_designation}")

        if not raw_designation:
            return {
                "standardized_designation": "",
                "type": "unknown",
                "manufacturer": "",
                "system": "",
                "gingival_height": ""
            }

        # Bereinige Input
        designation = raw_designation.strip()

        # Prüfe ob es sich um ein Accessoire handelt
        if self._is_accessory(designation):
            return self._create_accessory_designation(designation)

        # Prüfe ob es sich um ein Abutment handelt
        if self._is_abutment(designation):
            return self._create_abutment_designation(designation)

        # Fallback - unbekannter Typ
        return {
            "standardized_designation": f"Docklocs Accessories {designation}",
            "type": "accessory",
            "manufacturer": "",
            "system": "",
            "gingival_height": ""
        }

    def _is_abutment(self, designation: str) -> bool:
        """Prüft ob es sich um ein Abutment handelt."""
        abutment_keywords = [
            "abutment", "aufbau", "pfosten", "gingivaformer",
            "healing", "cap", "base", "crown"
        ]
        designation_lower = designation.lower()
        return any(keyword in designation_lower for keyword in abutment_keywords)

    def _is_accessory(self, designation: str) -> bool:
        """Prüft ob es sich um ein Accessoire handelt."""
        accessory_keywords = [
            "screw", "schraube", "tool", "werkzeug", "key", "schlüssel",
            "driver", "dreher", "wrench", "kit", "set"
        ]
        designation_lower = designation.lower()
        return any(keyword in designation_lower for keyword in accessory_keywords)

    def _create_accessory_designation(self, designation: str) -> Dict[str, str]:
        """Erstellt standardisierte Bezeichnung für Accessories."""
        return {
            "standardized_designation": f"Docklocs Accessories {designation}",
            "type": "accessory",
            "manufacturer": "",
            "system": "",
            "gingival_height": ""
        }

    def _create_abutment_designation(self, designation: str) -> Dict[str, str]:
        """Erstellt standardisierte Bezeichnung für Abutments."""
        # Extrahiere Hersteller und System
        manufacturers = self._extract_manufacturers(designation)
        gingival_height = self._extract_gingival_height(designation)

        if not manufacturers:
            # Fallback wenn kein Hersteller erkannt
            return {
                "standardized_designation": f"Docklocs Abutment for Unknown System {gingival_height}".strip(),
                "type": "abutment",
                "manufacturer": "Unknown",
                "system": "Unknown",
                "gingival_height": gingival_height
            }

        # Erstelle Bezeichnung basierend auf Anzahl der Hersteller
        if len(manufacturers) == 1:
            # Einzelner Hersteller
            manufacturer = manufacturers[0]
            return {
                "standardized_designation": f"Docklocs Abutment for {manufacturer['name']} {manufacturer['system']} {gingival_height}".strip(),
                "type": "abutment",
                "manufacturer": manufacturer['name'],
                "system": manufacturer['system'],
                "gingival_height": gingival_height
            }
        else:
            # Multiple Hersteller - mit " / " trennen
            manufacturer_strings = []
            manufacturer_names = []
            system_names = []

            for manufacturer in manufacturers:
                manufacturer_strings.append(f"{manufacturer['name']} {manufacturer['system']}")
                manufacturer_names.append(manufacturer['name'])
                system_names.append(manufacturer['system'])

            designation_text = " / ".join(manufacturer_strings)

            return {
                "standardized_designation": f"Docklocs Abutment for {designation_text} {gingival_height}".strip(),
                "type": "abutment",
                "manufacturer": " / ".join(manufacturer_names),
                "system": " / ".join(system_names),
                "gingival_height": gingival_height
            }

    def _extract_manufacturers(self, designation: str) -> List[Dict[str, str]]:
        """Extrahiert Hersteller und Systeme aus der Bezeichnung."""
        found_manufacturers = []
        designation_upper = designation.upper()

        for manufacturer, systems in self.implant_systems.items():
            manufacturer_upper = manufacturer.upper()

            # Prüfe ob Hersteller im Text vorkommt
            if manufacturer_upper in designation_upper:
                # Suche nach System
                found_system = "Standard"  # Default

                for system in systems:
                    system_upper = system.upper()
                    if system_upper in designation_upper:
                        found_system = system
                        break

                found_manufacturers.append({
                    "name": manufacturer,
                    "system": found_system
                })

        return found_manufacturers

    def _extract_gingival_height(self, designation: str) -> str:
        """Extrahiert Gingivahöhe aus der Bezeichnung."""
        # Suche nach mm-Angaben
        mm_pattern = r'(\d+(?:\.\d+)?)\s*mm'
        matches = re.findall(mm_pattern, designation.lower())

        if matches:
            # Nimm die erste gefundene mm-Angabe
            height_value = matches[0]
            return f"{height_value}mm"

        # Suche nach bekannten Gingivahöhen
        designation_lower = designation.lower()
        for height in self.gingival_heights:
            if height in designation_lower:
                return height

        return ""  # Keine Höhe gefunden


# Singleton instance
article_designation_service = ArticleDesignationService()