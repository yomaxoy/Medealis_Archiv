# src/warehouse/application/services/reporting_service.py

"""
Reporting Service - Application Layer fuer das Warehouse Management System.

Koordiniert Document- und Export-Services fuer einheitliche Reporting-API.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Internal imports
from .document_generation.document_generation_service import DocumentGenerationService
from .export_service import ExportService
from .entity_services.supplier_service import SupplierService
from .entity_services.delivery_service import DeliveryService
from .entity_services.item_service import ItemService
from .entity_services.order_service import OrderService

logger = logging.getLogger(__name__)


class ReportingService:
    """
    Unified Service fuer alle Reporting-Funktionen.

    Koordiniert:
    - Dokumentenerstellung (PDF, Word)
    - Daten-Exporte (Excel, CSV)
    - Template-basierte Reports
    """

    def __init__(self):
        """Initialisiert den ReportingService mit allen benoetigten Services."""
        try:
            # Sub-Services initialisieren
            self.document_service = DocumentGenerationService()
            self.export_service = ExportService()

            # Business Services (fuer Datenabruf)
            self.supplier_service = SupplierService()
            self.delivery_service = DeliveryService()
            self.item_service = ItemService()
            self.order_service = OrderService()

            logger.info("ReportingService erfolgreich initialisiert")

        except Exception as e:
            logger.error(f"Fehler bei ReportingService Initialisierung: {e}")
            raise

    # === DOCUMENT GENERATION ===

    def create_delivery_document(
        self,
        delivery_number: str,
        format_type: str = "docx",
        include_inspection: bool = False,
    ) -> Path:
        """
        Erstellt Lieferschein-Dokument fuer eine Delivery.

        Args:
            delivery_number: Lieferscheinnummer
            format_type: Ausgabeformat (docx, pdf, txt)
            include_inspection: Pruefprotokoll einschliessen

        Returns:
            Pfad zum erstellten Dokument
        """
        try:
            logger.info(f"Erstelle Lieferschein fuer Delivery: {delivery_number}")

            # Delivery-Daten abrufen
            delivery_data = self.delivery_service.get_delivery(delivery_number)
            if not delivery_data:
                raise ValueError(f"Delivery {delivery_number} nicht gefunden")

            # Items-Daten abrufen
            items_data = self.delivery_service.get_delivery_items(delivery_number)

            # Lieferschein erstellen
            document_path = self.document_service.generate_delivery_document(
                delivery_data, items_data, format_type
            )

            # Optional: Pruefprotokoll erstellen
            if include_inspection:
                inspection_path = self.document_service.generate_inspection_checklist(
                    delivery_data, items_data, format_type=format_type
                )
                logger.info(f"Pruefprotokoll zusaetzlich erstellt: {inspection_path}")

            return document_path

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Lieferscheins: {e}")
            raise

    # === DATA EXPORTS ===

    def export_suppliers_report(self, format_type: str = "xlsx") -> Path:
        """
        Exportiert alle Suppliers.

        Args:
            format_type: Ausgabeformat (xlsx)

        Returns:
            Pfad zur Export-Datei
        """
        try:
            logger.info("Exportiere Suppliers-Report")

            suppliers_data = self.supplier_service.get_all_suppliers()

            if format_type == "xlsx":
                return self.export_service.export_suppliers_to_excel(suppliers_data)
            else:
                raise ValueError(f"Format {format_type} nicht unterstuetzt")

        except Exception as e:
            logger.error(f"Fehler beim Suppliers-Export: {e}")
            raise

    def export_deliveries_report(self, format_type: str = "xlsx") -> Path:
        """
        Exportiert alle Deliveries.
        """
        try:
            deliveries_data = self.delivery_service.get_all_deliveries()
            return self.export_service.export_deliveries_to_excel(deliveries_data)
        except Exception as e:
            logger.error(f"Fehler beim Deliveries-Export: {e}")
            raise

    def export_items_report(self, format_type: str = "xlsx") -> Path:
        """Exportiert alle Items."""
        try:
            items_data = self.item_service.get_all_items()
            return self.export_service.export_items_to_excel(items_data)
        except Exception as e:
            logger.error(f"Fehler beim Items-Export: {e}")
            raise

    def export_orders_report(self, format_type: str = "xlsx") -> Path:
        """Exportiert alle Orders."""
        try:
            orders_data = self.order_service.get_all_orders()
            return self.export_service.export_orders_to_excel(orders_data)
        except Exception as e:
            logger.error(f"Fehler beim Orders-Export: {e}")
            raise

    def get_output_directory(self) -> Path:
        """Gibt das Output-Verzeichnis zurueck."""
        return self.document_service.output_dir


# Test-Funktion
if __name__ == "__main__":
    print("Testing ReportingService...")
    try:
        service = ReportingService()
        print("ReportingService erfolgreich erstellt!")
    except Exception as e:
        print(f"Fehler: {e}")
