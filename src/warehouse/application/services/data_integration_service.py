# src/warehouse/application/services/data_integration_service.py

"""
Data Integration Service - Zentrale Datenintegration für Document Generation.

Ersetzt database_integration helper und zentralisiert die Datenabfrage
für Document Generation gemäß Clean Architecture Principles.
"""

import logging
from typing import Dict, Any, Optional

# Import Application Services (Clean Architecture konform)
from .entity_services.supplier_service import SupplierService
from .entity_services.delivery_service import DeliveryService
from .entity_services.item_service import ItemService

# Import Caching
from ...shared.caching import ttl_cache

logger = logging.getLogger(__name__)


class DataIntegrationService:
    """
    Zentrale Service für Datenintegration bei Document Generation.

    Ersetzt helpers.database_integration mit einem richtigen Application Service.
    """

    def __init__(self):
        """Initialize with service instances."""
        try:
            self.supplier_service = SupplierService()
            self.delivery_service = DeliveryService()
            self.item_service = ItemService()
            logger.info("DataIntegrationService initialized")
        except Exception as e:
            logger.error(f"Error initializing DataIntegrationService: {e}")
            raise

    @ttl_cache(seconds=600, maxsize=64, key_prefix="delivery_data")
    def get_complete_delivery_data(
        self, delivery_number: str, batch_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete delivery data for document generation.

        Args:
            delivery_number: The delivery number
            batch_number: Optional batch number for filtering

        Returns:
            Complete delivery data dictionary
        """
        try:
            logger.info(f"Fetching complete delivery data for {delivery_number}")

            # Get delivery data
            delivery_data = self.delivery_service.get_delivery(delivery_number)
            if not delivery_data:
                logger.warning(f"No delivery found for number: {delivery_number}")
                return {}

            # Get supplier data
            supplier_data = {}
            if delivery_data.get("supplier_id"):
                supplier_data = (
                    self.supplier_service.get_supplier(delivery_data["supplier_id"])
                    or {}
                )

            # Get items for this delivery
            items_data = self.item_service.get_items_by_delivery(delivery_number)

            # Filter by batch number if specified
            if batch_number:
                items_data = [
                    item
                    for item in items_data
                    if item.get("batch_number") == batch_number
                ]

            # Combine all data
            complete_data = {
                "delivery_number": delivery_number,
                "delivery_date": delivery_data.get("delivery_date"),
                "employee_name": delivery_data.get("employee_name"),
                "supplier_name": supplier_data.get("name", "Unknown Supplier"),
                "supplier_id": delivery_data.get("supplier_id"),
                "items": items_data,
                "batch_number": batch_number,
                "document_path": delivery_data.get("document_path"),
                "notes": delivery_data.get("notes"),
            }

            # Add specific item data if batch_number specified
            if batch_number and items_data:
                item = items_data[0]  # Get first matching item
                complete_data.update(
                    {
                        "article_number": item.get("article_number"),
                        "quantity": item.get("quantity"),
                        "unit": item.get("unit"),
                        "description": item.get("description"),
                        "kompatibilitaet": item.get("kompatibilitaet"),
                        "status": item.get("status"),
                    }
                )

            logger.info(f"Complete delivery data fetched for {delivery_number}")
            return complete_data

        except Exception as e:
            logger.error(f"Error fetching delivery data for {delivery_number}: {e}")
            return {}

    @ttl_cache(seconds=300, maxsize=128, key_prefix="item_certs")
    def get_item_certificates(self, item_id: str) -> Dict[str, bool]:
        """
        Get certificate status for an item.

        Args:
            item_id: The item ID

        Returns:
            Dictionary with certificate status
        """
        try:
            # Parse composite key: "ArticleNumber#BatchNumber#DeliveryNumber"
            parts = item_id.split("#")
            if len(parts) != 3:
                logger.error(f"Invalid item_id format: {item_id}")
                return {}

            article_number, batch_number, delivery_number = parts
            item_data = self.item_service.get_item(
                article_number, batch_number, delivery_number
            )
            if not item_data:
                return {}

            return {
                "measurement_protocol": item_data.get("measurement_protocol", False),
                "material_certificate": item_data.get("material_certificate", False),
                "coating_certificate": item_data.get("coating_certificate", False),
                "hardness_certificate": item_data.get("hardness_certificate", False),
                "additional_certificates": item_data.get(
                    "additional_certificates", False
                ),
                "label_present": item_data.get("label_present", False),
                "accompanying_document": item_data.get("accompanying_document", False),
            }

        except Exception as e:
            logger.error(f"Error fetching certificates for item {item_id}: {e}")
            return {}

    def normalize_supplier_name(self, supplier_name: str) -> str:
        """
        Normalize supplier name for consistent usage.

        Args:
            supplier_name: Raw supplier name

        Returns:
            Normalized supplier name
        """
        if not supplier_name:
            return "Unknown"

        supplier_lower = supplier_name.lower().strip()

        # Basic Mapping-Regeln - MUSS mit storage_context._basic_supplier_normalization() synchron sein!
        if "primec" in supplier_lower:
            return "Primec"
        elif "terrats" in supplier_lower:
            return "Terrats_Medical"
        elif "fleima" in supplier_lower:
            return "Fleima"
        elif "megagen" in supplier_lower:
            return "MEGAGEN"
        elif "ctech" in supplier_lower or "c-tech" in supplier_lower:
            return "C-Tech"
        elif any(brand in supplier_lower for brand in ["straumann", "nobel", "camlog", "bego", "dentsply", "zimmer"]):
            logger.warning(
                f"Implantatmarke '{supplier_name}' wurde als Lieferantenname übergeben. "
                "Dies ist ein Fehler - prüfe die OCR/Input-Quelle. Nutze 'Unbekannt' als Fallback."
            )
            return "Unknown"
        else:
            # Fallback: Ersetze Leerzeichen durch Unterstriche für unbekannte Lieferanten
            return supplier_name.replace(" ", "_")

    @ttl_cache(seconds=180, maxsize=32, key_prefix="delivery_stats")
    def get_delivery_statistics(self, delivery_number: str) -> Dict[str, Any]:
        """
        Get delivery statistics for reporting.

        Args:
            delivery_number: The delivery number

        Returns:
            Statistics dictionary
        """
        try:
            items = self.item_service.get_items_by_delivery(delivery_number)

            total_items = len(items)
            completed_items = len(
                [
                    item
                    for item in items
                    if item.get("status") in ["Geprüft", "Abgeschlossen"]
                ]
            )

            return {
                "total_items": total_items,
                "completed_items": completed_items,
                "completion_rate": completed_items / max(total_items, 1) * 100,
                "pending_items": total_items - completed_items,
            }

        except Exception as e:
            logger.error(f"Error calculating statistics for {delivery_number}: {e}")
            return {}

    def clear_cache(self) -> Dict[str, int]:
        """
        Leert alle Caches des DataIntegrationService.

        Returns:
            Dictionary mit Clear-Statistiken
        """
        cleared_methods = 0

        if hasattr(self.get_complete_delivery_data, "cache_clear"):
            self.get_complete_delivery_data.cache_clear()
            cleared_methods += 1

        if hasattr(self.get_item_certificates, "cache_clear"):
            self.get_item_certificates.cache_clear()
            cleared_methods += 1

        if hasattr(self.get_delivery_statistics, "cache_clear"):
            self.get_delivery_statistics.cache_clear()
            cleared_methods += 1

        logger.info(
            f"Cleared {cleared_methods} method caches in DataIntegrationService"
        )
        return {"cleared_methods": cleared_methods}

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Gibt Cache-Statistiken für alle gecachten Methoden zurück.

        Returns:
            Dictionary mit Cache-Statistiken
        """
        stats = {}

        if hasattr(self.get_complete_delivery_data, "cache_stats"):
            stats["delivery_data"] = self.get_complete_delivery_data.cache_stats()

        if hasattr(self.get_item_certificates, "cache_stats"):
            stats["item_certificates"] = self.get_item_certificates.cache_stats()

        if hasattr(self.get_delivery_statistics, "cache_stats"):
            stats["delivery_statistics"] = self.get_delivery_statistics.cache_stats()

        return stats


# Singleton instance für Kompatibilität
data_integration_service = DataIntegrationService()
