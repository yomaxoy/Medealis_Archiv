"""
Unified Document Processing Service - Hauptservice für alle Dokumenttypen
Ersetzt die drei verschiedenen Workflows mit einheitlicher API
"""

import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .claude_api_client import claude_api_client
from .prompt_template_manager import prompt_manager
from .prompt_template_manager import DocumentType as PromptDocumentType
from ..document_generation.document_types import DocumentType
from .document_validator import document_validator
from .document_cache import document_cache

logger = logging.getLogger(__name__)


class UnifiedDocumentProcessingService:
    """
    Einheitlicher Service für alle Dokumenttypen.
    Workflow: Upload → Cache Check → Claude API → Validation → Parse
    """

    def __init__(self):
        self.cache = document_cache
        self.claude_api = claude_api_client
        self.prompt_manager = prompt_manager
        self.validator = document_validator
        self.logger = logger

    def process_document(
        self,
        document_data: bytes,
        document_type: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Haupt-Entry-Point für alle Dokumentverarbeitung.

        ZWEI-PHASEN ARCHITEKTUR:
        Phase 1: Raw Extraction (cacheable, ohne expected values)
        Phase 2: Expected Values Validation (live, mit expected values)

        Args:
            document_data: Dokument als Bytes
            document_type: Typ ("delivery", "order", "accompanying")
            context: Zusätzliche Daten (z.B. expected_article_number)

        Returns:
            Standardisiertes Ergebnis mit validation_status
        """
        if context is None:
            context = {}

        try:
            self.logger.info(f"Processing {document_type} document ({len(document_data)} bytes)")

            # PHASE 1: Raw Extraction (cacheable)
            raw_extraction = self._get_raw_extraction(document_data, document_type, context)

            if not raw_extraction or raw_extraction.get('error'):
                return raw_extraction

            # PHASE 2: Expected Values Validation (live)
            final_result = self._apply_expected_values_validation(raw_extraction, context)

            # PHASE 3: PDF Storage für Lieferscheine (nach erfolgreicher Datenextraktion)
            if document_type == "delivery" and final_result.get('success'):
                self.logger.info(f"DEBUG: Starting PDF storage phase for delivery document")
                pdf_storage_result = self._handle_delivery_slip_pdf_storage(final_result, context)
                if pdf_storage_result:
                    self.logger.info(f"DEBUG: PDF storage successful: {pdf_storage_result.get('pdf_stored', False)}")
                    final_result.update(pdf_storage_result)
                else:
                    self.logger.info(f"DEBUG: PDF storage was skipped or returned None")

            self.logger.info(f"Successfully processed {document_type} document")
            return final_result

        except Exception as e:
            self.logger.error(f"Error processing {document_type} document: {e}")
            return self._create_error_result(f"Processing failed: {str(e)}")

        finally:
            # Cleanup temporary file after all processing phases (including PDF storage)
            temp_file_path = context.get('temp_file_path')
            if temp_file_path:
                self._cleanup_temp_file(temp_file_path)

    def _get_raw_extraction(
        self,
        document_data: bytes,
        document_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 1: Raw Extraction mit Caching (ohne expected values).

        Diese Phase cached nur die reine Claude API Extraktion,
        ohne validation-spezifische expected_* values zu berücksichtigen.
        """
        try:
            # 1. Cache Check (mit gefiltertem Context ohne expected_* keys)
            cache_key = self.cache.generate_cache_key(document_data, document_type, context)
            cached_result = self.cache.get_cached_result(cache_key)

            if cached_result:
                self.logger.info(f"Cache hit for {document_type} raw extraction")
                return self._add_processing_metadata(cached_result, from_cache=True)

            # 2. Temporär speichern
            temp_file_path = self._save_temporarily(document_data)
            if not temp_file_path:
                return self._create_error_result("Failed to save document temporarily")

            # Store temp_file_path in context for later use (e.g., PDF storage)
            context['temp_file_path'] = temp_file_path

            try:
                # 3. Prompt generieren (ohne expected values für besseres Caching)
                doc_type_enum = self._get_document_type_enum(document_type)
                prompt_doc_type = self._get_prompt_document_type(document_type)

                # Context für Prompt OHNE expected_* keys (für konsistente Prompts)
                prompt_context = {k: v for k, v in context.items()
                                if not k.startswith('expected_')}

                prompt = self.prompt_manager.get_prompt(prompt_doc_type, prompt_context)

                # 4. Claude API Call
                claude_result = self.claude_api.analyze_document(
                    document_path=temp_file_path,
                    prompt=prompt,
                    debug=True
                )

                if not claude_result:
                    return self._create_error_result("Claude API call failed")

                # 5. Basis-Validierung (strukturelle Validierung ohne expected values)
                is_valid, validated_data, validation_errors = self.validator.validate_document_data(
                    claude_result, document_type, {}  # Leerer context für strukturelle Validierung
                )

                # 6. Cache Result (Raw Extraction ohne expected values validation)
                self.cache.cache_result(cache_key, validated_data)

                # 7. Processing Metadata hinzufügen
                final_result = self._add_processing_metadata(
                    validated_data,
                    from_cache=False,
                    validation_errors=validation_errors
                )

                self.logger.info(f"Raw extraction completed for {document_type} document")
                return final_result

            finally:
                # 8. Cleanup wird später gemacht - nach PDF storage phase
                pass

        except Exception as e:
            error_msg = f"Error in raw extraction for {document_type}: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_result(error_msg)

    def _apply_expected_values_validation(
        self,
        raw_extraction: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 2: Expected Values Validation (live, uncached).

        Wendet expected_* validation auf die gecachte Raw Extraction an.
        Diese Phase läuft bei jedem Request und ist nicht gecacht.
        """
        try:
            # Extract expected values from context
            expected_values = {k: v for k, v in context.items()
                             if k.startswith('expected_')}

            if not expected_values:
                # Keine expected values → return raw extraction with success=True for downstream processing
                self.logger.debug("No expected values provided, skipping validation phase")
                result = dict(raw_extraction)
                result['success'] = True  # Critical: Enable downstream processing like PDF storage
                return result

            # Expected values validation durch Validator
            validation_result = self.validator.validate_against_expected_values(
                raw_extraction, expected_values
            )

            # Merge raw extraction mit expected values validation
            final_result = {**raw_extraction}
            final_result['success'] = True  # Critical: Enable downstream processing like PDF storage

            # Update validation_status mit expected values results
            if 'validation_status' in final_result:
                final_result['validation_status'].update(validation_result)
            else:
                final_result['validation_status'] = validation_result

            # Processing metadata aktualisieren
            if '_processing_metadata' in final_result:
                final_result['_processing_metadata']['expected_values_applied'] = True
                final_result['_processing_metadata']['expected_values_count'] = len(expected_values)

            self.logger.debug(f"Applied expected values validation: {list(expected_values.keys())}")
            return final_result

        except Exception as e:
            error_msg = f"Error in expected values validation: {str(e)}"
            self.logger.error(error_msg)
            # Return raw extraction with success=True even if validation fails
            result = dict(raw_extraction)
            result['success'] = True  # Critical: Enable downstream processing even on validation errors
            return result

    def _save_temporarily(self, document_data: bytes, suffix: str = ".pdf") -> Optional[str]:
        """
        Speichert Dokument temporär - basiert auf bestehenden Implementierungen.
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(document_data)
                temp_file_path = temp_file.name

            self.logger.debug(f"Saved document temporarily: {temp_file_path}")
            return temp_file_path

        except Exception as e:
            self.logger.error(f"Failed to save document temporarily: {e}")
            return None

    def _cleanup_temp_file(self, file_path: str) -> None:
        """Räumt temporäre Datei auf."""
        try:
            if file_path and Path(file_path).exists():
                Path(file_path).unlink()
                self.logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

    def _get_document_type_enum(self, document_type: str) -> DocumentType:
        """Konvertiert String zu DocumentType Enum."""
        type_mapping = {
            "delivery": DocumentType.BEGLEITSCHEIN,  # Mapping zu korrektem Type
            "order": DocumentType.PDB,               # Fallback zu PDB
            "accompanying": DocumentType.BEGLEITSCHEIN,
            "lieferschein": DocumentType.LIEFERSCHEIN
        }

        if document_type not in type_mapping:
            raise ValueError(f"Unknown document type: {document_type}")

        return type_mapping[document_type]

    def _get_prompt_document_type(self, document_type: str) -> PromptDocumentType:
        """Konvertiert String zu PromptDocumentType für prompt_manager."""
        prompt_type_mapping = {
            "delivery": PromptDocumentType.DELIVERY,
            "order": PromptDocumentType.ORDER,
            "accompanying": PromptDocumentType.ACCOMPANYING,
            "lieferschein": PromptDocumentType.DELIVERY  # Lieferschein nutzt delivery prompt
        }

        if document_type not in prompt_type_mapping:
            # Fallback auf DELIVERY
            return PromptDocumentType.DELIVERY

        return prompt_type_mapping[document_type]

    def _add_processing_metadata(
        self,
        result: Dict[str, Any],
        from_cache: bool = False,
        validation_errors: list = None
    ) -> Dict[str, Any]:
        """
        Fügt Processing-Metadata zum Ergebnis hinzu.
        """
        if validation_errors is None:
            validation_errors = []

        # Processing Metadata
        processing_metadata = {
            "processed_with": "UnifiedDocumentProcessingService",
            "from_cache": from_cache,
            "has_validation_errors": len(validation_errors) > 0,
            "validation_error_count": len(validation_errors)
        }

        # Validation errors zu result hinzufügen wenn vorhanden
        if validation_errors:
            processing_metadata["validation_errors"] = validation_errors

        # Metadata zu result hinzufügen
        result["_processing_metadata"] = processing_metadata

        return result

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Erstellt standardisiertes Fehler-Result."""
        return {
            "success": False,
            "error": error_message,
            "validation_status": {
                "completeness_score": 0,
                "missing_critical_fields": ["all"],
                "user_guidance": f"Verarbeitung fehlgeschlagen: {error_message}",
                "document_quality": "schlecht",
                "extraction_confidence": "niedrig",
                "manual_review_needed": True
            },
            "_processing_metadata": {
                "processed_with": "UnifiedDocumentProcessingService",
                "from_cache": False,
                "has_validation_errors": True,
                "validation_error_count": 1,
                "validation_errors": [error_message]
            }
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück."""
        return self.cache.get_cache_stats()

    def cleanup_cache(self) -> int:
        """Bereinigt abgelaufene Cache-Einträge."""
        return self.cache.cleanup_expired()

    def is_available(self) -> bool:
        """Prüft ob Service verfügbar ist."""
        return self.claude_api.is_available()

    def get_status(self) -> Dict[str, Any]:
        """Service-Status für Monitoring."""
        return {
            "service": "UnifiedDocumentProcessingService",
            "claude_api_available": self.claude_api.is_available(),
            "cache_stats": self.get_cache_stats(),
            "supported_document_types": ["delivery", "order", "accompanying", "lieferschein"]
        }

    # =============================================================================
    # DATABASE STORAGE FUNCTIONS
    # =============================================================================

    def save_order_data_to_database(
        self,
        article_number: str,
        order_quantity: int,
        order_number: str = "",
        order_date: str = ""
    ) -> Dict[str, Any]:
        """
        Speichert Bestelldaten in der Datenbank (sowohl Item- als auch Order-Tabelle).

        Args:
            article_number: Artikelnummer
            order_quantity: Bestellmenge
            order_number: Bestellnummer (optional)
            order_date: Bestelldatum (optional)

        Returns:
            Dictionary mit Erfolgs-/Fehlerstatus und Details
        """
        result = {
            'success': False,
            'item_updated': False,
            'order_created_or_updated': False,
            'errors': [],
            'details': {}
        }

        try:
            # Import services
            from warehouse.infrastructure.database.repositories.sql_item_rep_domain import SQLAlchemyItemRepositoryDomain
            from warehouse.infrastructure.database.repositories.sql_order_rep_domain import SQLAlchemyOrderRepositoryDomain

            item_repo = SQLAlchemyItemRepositoryDomain()
            order_repo = SQLAlchemyOrderRepositoryDomain()

            # 1. Update ItemInfo with order quantity
            item_success = item_repo.update_item_info_order_quantity(
                article_number=article_number,
                order_quantity=order_quantity,
                order_number=order_number
            )

            if item_success:
                result['item_updated'] = True
                result['details']['item_quantity_saved'] = order_quantity
                self.logger.info(f"Updated order quantity for {article_number}: {order_quantity}")
            else:
                result['errors'].append(f"Failed to update item quantity for {article_number}")

            # 2. Create or update Order entry if order_number provided
            if order_number.strip():
                try:
                    # Check if order exists
                    existing_order = order_repo.find_by_order_number(order_number)

                    if existing_order:
                        # Update existing order date if provided
                        if order_date.strip():
                            order_update_success = order_repo.update_order_date(
                                order_number=order_number,
                                order_date=order_date
                            )
                            if order_update_success:
                                result['order_created_or_updated'] = True
                                result['details']['order_action'] = 'aktualisiert'
                                result['details']['order_date_updated'] = order_date
                                self.logger.info(f"Updated order date for {order_number}: {order_date}")
                            else:
                                result['errors'].append(f"Failed to update order date for {order_number}")
                        else:
                            result['order_created_or_updated'] = True
                            result['details']['order_action'] = 'bereits vorhanden'
                    else:
                        # Create new order
                        order_creation_success = order_repo.create_order(
                            order_number=order_number,
                            order_date=order_date if order_date.strip() else None,
                            supplier_name="",  # Will be updated later if needed
                            employee_name="System"
                        )
                        if order_creation_success:
                            result['order_created_or_updated'] = True
                            result['details']['order_action'] = 'erstellt'
                            if order_date.strip():
                                result['details']['order_date_saved'] = order_date
                            self.logger.info(f"Created new order: {order_number}")
                        else:
                            result['errors'].append(f"Failed to create order {order_number}")

                except Exception as order_error:
                    result['errors'].append(f"Order processing error: {str(order_error)}")
                    self.logger.error(f"Order processing error: {order_error}")

            # Overall success determination
            result['success'] = result['item_updated'] or result['order_created_or_updated']

            if not result['success'] and not result['errors']:
                result['errors'].append("No operations were successful")

            return result

        except Exception as e:
            error_msg = f"Database operation failed: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            return result

    def save_accompanying_document(
        self,
        document_data: bytes,
        document_name: str,
        article_number: str,
        batch_number: str,
        delivery_number: str = "",
        supplier_name: str = ""
    ) -> Dict[str, Any]:
        """
        Speichert ein Begleitdokument im korrekten Delivery-Ordner mit PathManager.

        Args:
            document_data: Binärdaten des Dokuments
            document_name: Name der Datei
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer (für korrekte Ordnerstruktur)
            supplier_name: Lieferantenname (für korrekte Ordnerstruktur)

        Returns:
            Speicher-Ergebnis
        """
        try:
            # Use DocumentStorageService for path resolution
            from warehouse.application.services.document_storage.document_storage_service import DocumentStorageService
            storage_service = DocumentStorageService()

            # Get manufacturer from batch number (P-number contains manufacturer info)
            try:
                context = storage_service._get_storage_context(batch_number)
                manufacturer = context.get('manufacturer', 'Unknown')
            except Exception as e:
                logger.warning(f"Could not determine manufacturer from batch {batch_number}: {e}")
                # Fallback: extract from article number pattern
                manufacturer = article_number.split('/')[0] if '/' in article_number else 'Unknown'

            # Get correct delivery folder path using DocumentStorageService
            try:
                delivery_folder = storage_service.get_storage_path(batch_number)
            except Exception as e:
                logger.warning(f"Could not get storage path for batch {batch_number}: {e}")
                # Fallback: create basic path structure
                delivery_folder = Path(f"C:/Users/krueg/Medealis/Wareneingang/{supplier_name or 'Unbekannt'}/{manufacturer}/{article_number}/{batch_number}/{delivery_number or 'Unbekannt'}")

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(document_name).suffix
            safe_filename = (
                f"begleitdokument_{batch_number}_{timestamp}{file_extension}"
            )

            # Remove invalid characters
            safe_filename = "".join(
                c for c in safe_filename if c.isalnum() or c in ".-_"
            )

            # Save file
            file_path = delivery_folder / safe_filename

            with open(file_path, 'wb') as f:
                f.write(document_data)

            self.logger.info(f"Saved accompanying document: {file_path}")

            return {
                'success': True,
                'file_path': str(file_path),
                'filename': safe_filename,
                'delivery_folder': str(delivery_folder)
            }

        except Exception as e:
            error_msg = f"Failed to save accompanying document: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def save_delivery_slip_PDF(
        self,
        supplier_name: str,
        delivery_number: str,
        temp_file_path: str
    ) -> Dict[str, Any]:
        """
        Speichert Lieferschein-PDF im Lieferanten-Ordner.

        Einfache Funktion die nach erfolgreicher Datenextraktion aufgerufen wird,
        um das PDF physisch im korrekten Ordner zu speichern.

        Args:
            supplier_name: Lieferantenname (bereits normalisiert)
            delivery_number: Lieferscheinnummer
            temp_file_path: Pfad zur temporären Datei

        Returns:
            Storage-Result mit Erfolg/Fehler-Info
        """
        try:
            self.logger.info(f"Saving delivery slip PDF: {supplier_name} - {delivery_number}")

            # Lese temporäre Datei
            with open(temp_file_path, 'rb') as f:
                document_data = f.read()

            # Erstelle Dateiname
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lieferschein_{delivery_number}_{timestamp}.pdf" if delivery_number else f"lieferschein_{timestamp}.pdf"

            # Normalisiere Lieferantennamen für Storage (einheitlich mit storage_context)
            from ..document_storage.storage_context import storage_context
            normalized_supplier = storage_context._basic_supplier_normalization(supplier_name)

            # Speichere PDF
            from ..service_registry import get_document_storage_service
            storage_service = get_document_storage_service()

            if not storage_service:
                return {
                    'success': False,
                    'error': 'Document storage service not available'
                }

            storage_result = storage_service.save_delivery_slip_pdf(
                document_data=document_data,
                document_name=filename,
                supplier_name=normalized_supplier,
                delivery_number=delivery_number,
                auto_detected=True
            )

            if storage_result.success:
                self.logger.info(f"Delivery slip PDF saved: {storage_result.file_path}")
                return {
                    'success': True,
                    'file_path': storage_result.file_path,
                    'storage_folder': storage_result.storage_folder,
                    'normalized_supplier': normalized_supplier
                }
            else:
                self.logger.error(f"PDF storage failed: {storage_result.error}")
                return {
                    'success': False,
                    'error': storage_result.error
                }

        except Exception as e:
            error_msg = f"Failed to save delivery slip PDF: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }



    def _handle_delivery_slip_pdf_storage(
        self,
        processing_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Behandelt PDF-Speicherung für Lieferscheine nach erfolgreicher Datenextraktion.

        Wird nur aufgerufen wenn:
        - document_type == "delivery"
        - processing_result['success'] == True
        - Lieferant und/oder Lieferscheinnummer erkannt wurden
        """
        try:
            # Prüfe ob kritische Daten vorhanden sind
            supplier_name = processing_result.get('supplier_name')
            delivery_number = processing_result.get('delivery_number')

            self.logger.info(f"DEBUG: PDF storage - supplier_name: '{supplier_name}', delivery_number: '{delivery_number}'")

            if not supplier_name and not delivery_number:
                self.logger.info("DEBUG: No supplier or delivery number found - skipping PDF storage")
                return None

            # Hole temp_file_path aus dem context falls vorhanden
            temp_file_path = context.get('temp_file_path')
            self.logger.info(f"DEBUG: temp_file_path from context: '{temp_file_path}'")

            # Falls temp_file_path nicht vorhanden (z.B. Cache-Hit),
            # versuche document_data zu verwenden
            if not temp_file_path:
                document_data = context.get('document_data')
                self.logger.info(f"DEBUG: document_data available: {len(document_data) if document_data else 0} bytes")
                if document_data:
                    # Erstelle temporäre Datei für PDF Storage
                    temp_file_path = self._save_temporarily(document_data)
                    if temp_file_path:
                        context['temp_file_path'] = temp_file_path
                        self.logger.info(f"DEBUG: Created temporary file for PDF storage: {temp_file_path}")

                if not temp_file_path:
                    self.logger.info("DEBUG: No temp_file_path or document_data available - skipping PDF storage")
                    return None

            # Verwende Fallback-Werte wenn nötig
            supplier_for_storage = supplier_name or "Unbekannt"
            delivery_for_storage = delivery_number or ""

            self.logger.info(f"Storing delivery slip PDF: {supplier_for_storage} - {delivery_for_storage}")

            # Rufe save_delivery_slip_PDF auf
            storage_result = self.save_delivery_slip_PDF(
                supplier_name=supplier_for_storage,
                delivery_number=delivery_for_storage,
                temp_file_path=temp_file_path
            )

            if storage_result.get('success'):
                self.logger.info(f"Delivery slip PDF stored successfully")
                return {
                    'pdf_stored': True,
                    'pdf_path': storage_result.get('file_path'),
                    'storage_folder': storage_result.get('storage_folder'),
                    'normalized_supplier': storage_result.get('normalized_supplier')
                }
            else:
                self.logger.warning(f"PDF storage failed: {storage_result.get('error')}")
                return {
                    'pdf_stored': False,
                    'storage_error': storage_result.get('error')
                }

        except Exception as e:
            self.logger.error(f"Error in delivery slip PDF storage: {e}")
            return {
                'pdf_stored': False,
                'storage_error': str(e)
            }


# Global instance
document_processing_service = UnifiedDocumentProcessingService()