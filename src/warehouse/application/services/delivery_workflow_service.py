"""
Delivery Workflow Service - Orchestrates delivery document creation workflows.

This service coordinates multiple existing services to provide a complete
delivery document workflow. It replaces the orchestration logic from
EnhancedDocumentService while using existing specialized services.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import existing services
from .data_integration_service import data_integration_service
from .document_storage.document_storage_service import DocumentStorageService
from .document_operations.document_opening_service import DocumentOpeningService
from .document_operations.pdf_merge_service import PDFMergeService

logger = logging.getLogger(__name__)


@dataclass
class DeliveryWorkflowResult:
    """Result of delivery workflow operation."""
    success: bool
    delivery_number: str
    documents_created: List[Dict[str, Any]]
    folder_path: Optional[Path] = None
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class DeliveryWorkflowService:
    """
    Orchestrates delivery document creation workflows.

    Coordinates existing services:
    - DocumentStorageService: Path resolution and folder creation
    - DocumentOpeningService: Opening generated documents/folders
    - PDFMergeService: Merging delivery PDFs
    - DataIntegrationService: Database data retrieval
    - document_generation_service: Document generation (new system)
    - BarcodeService: Barcode generation (existing)
    """

    def __init__(self):
        """Initialize workflow service with dependencies."""
        try:
            # Core services
            self.data_integration = data_integration_service
            self.storage_service = DocumentStorageService()
            self.document_opener = DocumentOpeningService()
            self.pdf_merger = PDFMergeService()

            # External services (optional - fail gracefully)
            self.document_generation_service = None
            try:
                from .document_generation import DocumentGenerationService
                self.document_generation_service = DocumentGenerationService()
                logger.info("Document generation service available")
            except ImportError:
                logger.warning("Document generation service not available")

            logger.info("DeliveryWorkflowService initialized")

        except Exception as e:
            logger.error(f"Failed to initialize DeliveryWorkflowService: {e}")
            raise

    def create_delivery_documents(
        self,
        delivery_number: str,
        batch_number: Optional[str] = None,
        open_documents: bool = False,
        create_folder: bool = True,
        document_types: Optional[List[str]] = None,
        override_status: Optional[str] = None
    ) -> DeliveryWorkflowResult:
        """
        Complete delivery document workflow.

        Args:
            delivery_number: Delivery number
            batch_number: Optional specific batch number
            open_documents: Whether to open generated documents
            create_folder: Whether to create organized folder structure
            document_types: List of document types to create. If None, creates all
            override_status: Optional status override for validation

        Returns:
            DeliveryWorkflowResult with complete workflow results
        """
        result = DeliveryWorkflowResult(
            success=False,
            delivery_number=delivery_number,
            documents_created=[]
        )

        try:
            logger.info(f"Starting delivery workflow for {delivery_number}")

            # Step 1: Validate batch number if provided
            if batch_number:
                if not self._validate_batch_number(batch_number):
                    result.errors.append(
                        f"Batch Number '{batch_number}' hat nicht das erforderliche Format "
                        "P-XXXXXXXXXXXX-XXXX oder P-XXXXXXXXXXXX-XXXXX für die Dokumentenerstellung."
                    )
                    return result

            # Step 2: Get delivery data
            delivery_data = self.data_integration.get_complete_delivery_data(
                delivery_number, batch_number
            )

            if not delivery_data.get('items'):
                result.errors.append("No items found in delivery data - cannot create documents")
                return result

            # Step 3: Create folder structure if requested
            if create_folder:
                folder_result = self._create_delivery_folder(delivery_data)
                if folder_result['success']:
                    result.folder_path = folder_result['folder_path']
                else:
                    result.warnings.extend(folder_result.get('warnings', []))

            # Step 4: Generate documents
            document_results = self._generate_delivery_documents(
                delivery_data, document_types, override_status
            )
            result.documents_created = document_results['documents_created']
            result.errors.extend(document_results.get('errors', []))

            # Step 5: Open documents/folder if requested
            if open_documents and result.documents_created:
                self._open_generated_documents(result.documents_created, result.folder_path)

            # Determine overall success
            result.success = len(result.documents_created) > 0 and len(result.errors) == 0

            logger.info(f"Delivery workflow completed: {len(result.documents_created)} documents created")
            return result

        except Exception as e:
            error_msg = f"Delivery workflow failed: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result

    def merge_delivery_pdfs(
        self,
        delivery_number: str,
        batch_number: Optional[str] = None,
        output_filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Merge PDF files for a delivery.

        Args:
            delivery_number: Delivery number
            batch_number: Optional batch number
            output_filename: Optional custom output filename

        Returns:
            Path to merged PDF or None if failed
        """
        try:
            # Get delivery folder path
            delivery_data = self.data_integration.get_complete_delivery_data(
                delivery_number, batch_number
            )

            folder_result = self._create_delivery_folder(delivery_data)
            if not folder_result['success']:
                logger.error("Could not resolve delivery folder for PDF merge")
                return None

            folder_path = folder_result['folder_path']

            # Use PDF merge service
            return self.pdf_merger.merge_delivery_pdfs(
                folder_path=folder_path,
                delivery_number=delivery_number,
                output_filename=output_filename
            )

        except Exception as e:
            logger.error(f"Error in delivery PDF merge: {e}")
            return None

    def _validate_batch_number(self, batch_number: str) -> bool:
        """Validate batch number format."""
        try:
            from warehouse.domain.value_objects.batch_number import BatchNumber
            batch_num_obj = BatchNumber(batch_number)
            return not batch_num_obj.needs_completion()
        except Exception as e:
            logger.warning(f"Batch number validation failed: {e}")
            return False

    def _create_delivery_folder(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create delivery folder using storage service."""
        try:
            # Extract required data
            batch_number = delivery_data.get('batch_number', '')
            delivery_number = delivery_data.get('delivery_number', '')

            if not batch_number or not delivery_number:
                return {
                    'success': False,
                    'warnings': ['Incomplete data for folder creation']
                }

            # Use storage service to get/create path
            folder_path, warnings = self.storage_service.get_document_path(
                batch_number=batch_number,
                delivery_number=delivery_number,
                create_folders=True
            )

            return {
                'success': True,
                'folder_path': folder_path,
                'warnings': warnings
            }

        except Exception as e:
            logger.error(f"Folder creation failed: {e}")
            return {
                'success': False,
                'warnings': [f"Folder creation failed: {e}"]
            }

    def _generate_delivery_documents(
        self,
        delivery_data: Dict[str, Any],
        document_types: Optional[List[str]],
        override_status: Optional[str]
    ) -> Dict[str, Any]:
        """Generate delivery documents using existing services."""
        result = {
            'documents_created': [],
            'errors': []
        }

        if not self.document_generation_service:
            result['errors'].append("Document generation service not available")
            return result

        try:
            # Get first item data
            first_item = delivery_data['items'][0]
            article_number = first_item.get('article_number', '')
            batch_number = first_item.get('batch_number', '')
            delivery_number = delivery_data.get('delivery_number', '')
            item_status = override_status or first_item.get('status', '').strip()

            # Define available documents with status requirements (IST-Zustand)
            # NOTE: Sichtkontrolle removed - only created via Visual Inspection Popup
            all_documents = [
                ('PDB', 'create_pdb_document', 'Daten geprüft'),
                ('Begleitschein', 'create_begleitschein_document', 'Dokumente geprüft'),
                ('Wareneingangskontrolle', 'create_wareneingangskontrolle_document', 'Dokumente geprüft'),
                ('Barcode', '_create_barcode_files', 'Daten geprüft')
            ]

            # Filter documents if specific types requested
            if document_types:
                documents_to_create = [
                    (doc_type, method, status) for doc_type, method, status in all_documents
                    if doc_type in document_types
                ]
            else:
                documents_to_create = all_documents

            # Generate each document
            for doc_type, method_name, required_status in documents_to_create:
                doc_result = self._create_single_document(
                    doc_type, method_name, required_status, item_status, override_status,
                    article_number, batch_number, delivery_number
                )

                if doc_result['success']:
                    result['documents_created'].append(doc_result)
                else:
                    result['errors'].append(doc_result['error'])

        except Exception as e:
            logger.error(f"Document generation failed: {e}")
            result['errors'].append(f"Document generation failed: {e}")

        return result

    def _create_single_document(
        self, doc_type: str, method_name: str, required_status: str,
        item_status: str, override_status: Optional[str],
        article_number: str, batch_number: str, delivery_number: str
    ) -> Dict[str, Any]:
        """Create single document with status validation."""
        try:
            # Status validation (skip if override provided)
            if required_status and not override_status:
                if item_status != required_status:
                    return {
                        'success': False,
                        'error': f"{doc_type} kann erst erstellt werden wenn Status '{required_status}' erreicht ist. Aktueller Status: '{item_status}'"
                    }

            # Create document using appropriate service
            if doc_type == 'Barcode':
                return self._create_barcode_document(article_number, batch_number, delivery_number)
            else:
                return self._create_word_document(doc_type, method_name, article_number, batch_number, delivery_number)

        except Exception as e:
            logger.error(f"Error creating {doc_type}: {e}")
            return {
                'success': False,
                'error': f"{doc_type} creation failed: {e}"
            }

    def _create_word_document(
        self, doc_type: str, method_name: str,
        article_number: str, batch_number: str, delivery_number: str
    ) -> Dict[str, Any]:
        """Create Word document using word template service."""
        try:
            # Use new document generation service
            from .document_generation import DocumentType

            doc_type_map = {
                'create_begleitschein_document': DocumentType.BEGLEITSCHEIN,
                'create_wareneingangskontrolle_document': DocumentType.WARENEINGANGSKONTROLLE
            }

            if method_name in doc_type_map:
                doc_result = self.document_generation_service.generate_document(
                    document_type=doc_type_map[method_name],
                    article_number=first_item.get('article_number', ''),
                    batch_number=first_item.get('batch_number', ''),
                    delivery_number=delivery_number,
                    auto_open=False
                )
                if doc_result.success:
                    document_path = doc_result.output_path
                else:
                    document_path = None

            # Special handling for different document types
            if method_name == 'create_wareneingangskontrolle_document':
                from datetime import date
                we_date = date.today().strftime("%d.%m.%Y")
                doc_path = method(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    we_date=we_date,
                    open_document=False  # Don't auto-open, workflow handles this
                )
            else:
                doc_path = method(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    open_document=False  # Don't auto-open, workflow handles this
                )

            return {
                'success': True,
                'type': doc_type,
                'path': doc_path,
                'format': 'docx'
            }

        except Exception as e:
            logger.error(f"Word document creation failed for {doc_type}: {e}")
            return {
                'success': False,
                'error': f"Word document creation failed: {e}"
            }

    def _create_barcode_document(
        self, article_number: str, batch_number: str, delivery_number: str
    ) -> Dict[str, Any]:
        """Create barcode files using new DocumentGenerationService."""
        try:
            # Use new DocumentGenerationService instead of deprecated BarcodeService
            from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService

            logger.info("DEBUG: Creating barcode via DocumentGenerationService...")
            generation_service = DocumentGenerationService()
            barcode_result = generation_service.generate_document(
                document_type="barcode",
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name="",  # Will be auto-determined
                quantity=0,
                employee_name="System",
                additional_data={
                    'filename_prefix': 'barcode',
                    'barcode_type': 'CODE128',
                    'open_after_creation': False  # Don't auto-open, workflow handles this
                }
            )

            if barcode_result.success and barcode_result.document_path:
                logger.info(f"Barcode generated successfully via DocumentGenerationService: {barcode_result.document_path}")
                return {
                    'success': True,
                    'type': 'Barcode',
                    'path': barcode_result.document_path,
                    'format': 'png'
                }
            else:
                error_msg = barcode_result.error if hasattr(barcode_result, 'error') else 'No barcode file was created'
                logger.warning(f"Barcode generation failed: {error_msg}")
                return {
                    'success': False,
                    'error': f'Barcode generation failed: {error_msg}'
                }

        except Exception as e:
            logger.error(f"Barcode creation failed: {e}")
            return {
                'success': False,
                'error': f"Barcode creation failed: {e}"
            }

    def _open_generated_documents(
        self, documents: List[Dict[str, Any]], folder_path: Optional[Path]
    ):
        """Open generated documents and folder."""
        try:
            # Open individual documents
            for doc in documents:
                if doc.get('path'):
                    self.document_opener.open_document(doc['path'])

            # Open folder if available
            if folder_path:
                self.document_opener.open_folder(folder_path)

        except Exception as e:
            logger.warning(f"Error opening documents: {e}")


# Global instance for convenience
delivery_workflow_service = DeliveryWorkflowService()