# src/warehouse/infrastructure/file_system/manufacturer_service.py

"""
Infrastructure Layer: Manufacturer Service
Handles manufacturer determination and supplier name normalization.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ManufacturerService:
    """
    Infrastructure service for manufacturer determination and supplier normalization.
    """

    def __init__(self):
        """Initialize manufacturer service with mapping rules."""
        # Prefix-based manufacturer detection
        self.manufacturer_map = {
            "A": "Abutments",
            "B": "Bone_Level",
            "C": "Camlog",
            "CT": "Conelog",
            "D": "Dentsply",
            "I": "Implantate",
            "S": "Straumann",
            "T": "Tissue_Level",
            "AS": "Abutments",  # Additional mapping for AS prefixes
            "MG": "Standard_Implantate",
            "L": "Standard_Implantate",
            "Z": "Standard_Implantate",
        }

        # Supplier name normalization - ERWEITERT für konsistente Speicherung
        self.supplier_normalization = {
            # Primec Varianten
            "primec": "Primec",
            "PRIMEC": "Primec",
            "Primec": "Primec",
            "primec gmbh": "Primec",
            "PRIMEC GMBH": "Primec",
            "Primec GmbH": "Primec",  # ← NEU! Häufigste Variante
            "Primec_GmbH": "Primec",  # ← NEU! Alte Ordnerstruktur
            "Primec_Gmbh": "Primec",  # ← NEU! Path-cleaning Variante
            "10006": "Primec",  # ← NEU! Supplier-ID
            # Weitere Lieferanten (vorbereitet)
            "straumann": "Straumann",
            "STRAUMANN": "Straumann",
            "Straumann": "Straumann",
            "camlog": "Camlog",
            "CAMLOG": "Camlog",
            "Camlog": "Camlog",
        }

    def determine_manufacturer(self, article_number: str) -> str:
        """
        Determines manufacturer/implant type from article number.

        Args:
            article_number: Article number (e.g., "A0001", "CT003", "AS0006")

        Returns:
            Manufacturer/implant type
        """
        if not article_number:
            return "Unbekannt"

        article_upper = article_number.upper()

        # Check for specific prefixes (longest first to handle overlaps like A vs AS)
        sorted_prefixes = sorted(self.manufacturer_map.keys(), key=len, reverse=True)

        for prefix in sorted_prefixes:
            if article_upper.startswith(prefix):
                manufacturer = self.manufacturer_map[prefix]
                logger.debug(
                    f"Article {article_number} mapped to manufacturer: {manufacturer}"
                )
                return manufacturer

        # Default fallback
        logger.debug(
            f"Article {article_number} using default manufacturer: Standard_Implantate"
        )
        return "Standard_Implantate"

    def normalize_supplier_name(self, supplier_name: str) -> str:
        """
        Normalize supplier names to consistent format.

        Args:
            supplier_name: Original supplier name

        Returns:
            Normalized supplier name
        """
        if not supplier_name:
            return "Primec"  # Default supplier

        # Clean and normalize
        clean_name = supplier_name.strip()

        # Check for exact matches first
        if clean_name in self.supplier_normalization:
            normalized = self.supplier_normalization[clean_name]
            logger.debug(f"Supplier {supplier_name} normalized to: {normalized}")
            return normalized

        # Check for case-insensitive matches
        for key, value in self.supplier_normalization.items():
            if clean_name.lower() == key.lower():
                logger.debug(f"Supplier {supplier_name} normalized to: {value}")
                return value

        # Return cleaned name if no mapping found
        logger.debug(f"Supplier {supplier_name} kept as: {clean_name}")
        return clean_name

    def add_manufacturer_mapping(self, prefix: str, manufacturer: str) -> None:
        """
        Add or update manufacturer mapping.

        Args:
            prefix: Article number prefix
            manufacturer: Manufacturer name
        """
        self.manufacturer_map[prefix.upper()] = manufacturer
        logger.info(f"Added manufacturer mapping: {prefix} -> {manufacturer}")

    def add_supplier_mapping(self, supplier_variant: str, normalized_name: str) -> None:
        """
        Add or update supplier normalization mapping.

        Args:
            supplier_variant: Supplier name variant
            normalized_name: Normalized supplier name
        """
        self.supplier_normalization[supplier_variant] = normalized_name
        logger.info(f"Added supplier mapping: {supplier_variant} -> {normalized_name}")


# Global instance
manufacturer_service = ManufacturerService()
