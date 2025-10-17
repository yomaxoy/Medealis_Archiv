"""
Document Generation Service - Central API

Hauptschnittstelle für die gesamte Dokument-Generierung.
Vereint alle Komponenten des Document Generation Systems:

- ContextBuilder: Context-Management
- WordProcessor: DOCX-Verarbeitung
- TemplateManager: Template-Verwaltung
- PlaceholderEngine: Placeholder-System

Bietet einheitliche API für:
- Einzelne Dokument-Generierung
- Batch-Generierung
- Storage System Integration (Phase 1)
- Vollständige Workflow-Unterstützung
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import asdict

# Internal imports
from .generation_models import (
    GenerationContext, GenerationResult, BatchGenerationResult,
    ProcessingOptions, ValidationResult
)
from .document_types import DocumentType, get_template_info, get_all_template_info
from .context_builder import ContextBuilder, create_context_from_parameters
from .word_processor import WordProcessor
from .barcode_generator import BarcodeGenerator

logger = logging.getLogger(__name__)

# DocumentStorageService wird jetzt lokal in _resolve_output_path importiert


class DocumentGenerationService:
    """
    Zentrale Document Generation Service API.

    Hauptschnittstelle für alle Document Generation Operationen.
    Ersetzt die verteilte Funktionalität aus WordTemplateService und anderen Services.
    """

    def __init__(self, template_base_dir: Optional[Path] = None):
        """
        Initialize Document Generation Service.

        Args:
            template_base_dir: Basis-Verzeichnis für Templates (optional)
        """
        try:
            # Core Components initialisieren
            self.context_builder = ContextBuilder()
            # FIXED: Verwende WordConverter anstatt WordProcessor für automatische PDF-Generierung
            try:
                from .word_converter import WordConverter
                self.word_processor = WordConverter(template_base_dir)
                logger.info("DocumentGenerationService initialized with PDF conversion support")
            except ImportError:
                self.word_processor = WordProcessor(template_base_dir)
                logger.warning("WordConverter not available, using basic WordProcessor")

            # Barcode Generator
            self.barcode_generator = BarcodeGenerator()
            logger.info("BarcodeGenerator initialized")

            # Note: DocumentStorageService wird jetzt direkt in _resolve_output_path verwendet
            # wie im WordProcessor - keine separate Instanz mehr nötig

            # Service Statistics
            self.stats = {
                'service_initialized': datetime.now(),
                'documents_generated': 0,
                'batch_operations': 0,
                'service_errors': 0
            }

            # Service Configuration
            self.config = {
                'default_output_format': 'docx',
                'auto_open_documents': False,
                'strict_validation': False
            }

            logger.info("DocumentGenerationService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize DocumentGenerationService: {e}")
            raise

    # =================================================================
    # HAUPTSCHNITTSTELLEN - Single Document Generation
    # =================================================================

    def generate_document(
        self,
        document_type: Union[DocumentType, str],
        batch_number: str,
        delivery_number: str,
        article_number: str = "",
        supplier_name: str = "",
        quantity: int = 0,
        employee_name: str = "",
        additional_data: Optional[Dict[str, Any]] = None,
        processing_options: Optional[ProcessingOptions] = None,
        output_path: Optional[Path] = None
    ) -> GenerationResult:
        """
        Generiert einzelnes Dokument aus Parametern.

        Args:
            document_type: Dokument-Typ (DocumentType oder String)
            batch_number: Chargennummer (Pflicht)
            delivery_number: Lieferscheinnummer (Pflicht)
            article_number: Artikelnummer (optional)
            supplier_name: Lieferantenname (optional)
            quantity: Menge (optional)
            employee_name: Mitarbeitername (optional)
            additional_data: Zusätzliche Daten/Placeholder (optional)
            processing_options: Verarbeitungsoptionen (optional)
            output_path: Ausgabepfad (optional, sonst auto-generiert)

        Returns:
            GenerationResult mit Erfolg/Fehler-Informationen

        Example:
            ```python
            service = DocumentGenerationService()
            result = service.generate_document(
                document_type=DocumentType.PDB,
                batch_number="P-123456789012",
                delivery_number="DEL-001",
                article_number="CT0001",
                supplier_name="Primec GmbH"
            )
            ```
        """
        try:
            # Document Type validieren/konvertieren
            if isinstance(document_type, str):
                document_type = DocumentType.from_string(document_type)
                if not document_type:
                    raise ValueError(f"Invalid document type: {document_type}")

            logger.info(f"Generating {document_type.value} document for batch {batch_number}")

            # 1. GenerationContext erstellen
            context = self.context_builder.build_from_parameters(
                batch_number=batch_number,
                delivery_number=delivery_number,
                document_type=document_type,
                article_number=article_number,
                supplier_name=supplier_name,
                quantity=quantity,
                employee_name=employee_name,
                additional_placeholders=additional_data or {}
            )

            # 2. Processing Options anwenden
            if processing_options:
                context = self._apply_processing_options(context, processing_options)

            # 3. Output Path bestimmen (mit Storage System Integration)
            final_output_path = self._resolve_output_path(context, output_path, processing_options)

            # 4. Dokument generieren - unterschiedlich je nach DocumentType
            if document_type == DocumentType.BARCODE:
                # BARCODE: Verwende BarcodeGenerator
                result = self._generate_barcode_document(context, final_output_path)
            else:
                # ALLE ANDEREN: Verwende WordProcessor (WordConverter mit PDF support)
                result = self.word_processor.generate_document(context, final_output_path)

            # 5. SharePoint Upload (falls aktiviert)
            if result.success:
                logger.info(f"Starting SharePoint upload for {document_type.value}, path: {result.document_path}")
                self._upload_generated_documents_to_sharepoint(
                    result=result,
                    context=context,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    article_number=article_number,
                    supplier_name=supplier_name
                )

            # 6. Post-Processing
            if result.success and processing_options and processing_options.open_after_creation:
                self._open_document(result.document_path)

            # Statistics
            self.stats['documents_generated'] += 1

            logger.info(f"Document generation {'successful' if result.success else 'failed'}: {result.get_summary()}")

            return result

        except Exception as e:
            error_msg = f"Document generation failed: {e}"
            logger.error(error_msg)
            self.stats['service_errors'] += 1

            # Return error result
            result = GenerationResult(success=False, document_type=document_type)
            result.set_error(error_msg)
            return result

    def generate_document_from_context(
        self,
        context: GenerationContext,
        processing_options: Optional[ProcessingOptions] = None,
        output_path: Optional[Path] = None
    ) -> GenerationResult:
        """
        Generiert Dokument aus vollständigem GenerationContext.

        Args:
            context: Vollständiger GenerationContext
            processing_options: Verarbeitungsoptionen (optional)
            output_path: Ausgabepfad (optional)

        Returns:
            GenerationResult
        """
        try:
            logger.info(f"Generating document from context - Type: {context.document_type.value if context.document_type else 'unknown'}")

            # Context validieren
            if not context.document_type:
                raise ValueError("document_type is required in GenerationContext")

            # Processing Options anwenden
            if processing_options:
                context = self._apply_processing_options(context, processing_options)

            # Output Path bestimmen
            final_output_path = self._resolve_output_path(context, output_path, processing_options)

            # Dokument generieren
            result = self.word_processor.generate_document(context, final_output_path)

            # Storage Integration erfolgt bereits direkt über _resolve_output_path()

            # Statistics
            self.stats['documents_generated'] += 1

            return result

        except Exception as e:
            error_msg = f"Context-based generation failed: {e}"
            logger.error(error_msg)
            self.stats['service_errors'] += 1

            result = GenerationResult(success=False, document_type=context.document_type)
            result.set_error(error_msg)
            return result

    def generate_document_from_storage_context(
        self,
        storage_context: 'StorageContextData',
        document_type: Union[DocumentType, str],
        processing_options: Optional[ProcessingOptions] = None,
        output_path: Optional[Path] = None
    ) -> GenerationResult:
        """
        Generiert Dokument aus Phase 1 StorageContextData.

        Args:
            storage_context: StorageContextData aus Phase 1
            document_type: Document Type
            processing_options: Verarbeitungsoptionen (optional)
            output_path: Ausgabepfad (optional)

        Returns:
            GenerationResult
        """
        try:
            if not STORAGE_SYSTEM_AVAILABLE:
                raise ValueError("Storage System not available for this operation")

            # Document Type konvertieren
            if isinstance(document_type, str):
                document_type = DocumentType.from_string(document_type)

            logger.info(f"Generating document from storage context - Type: {document_type.value}")

            # GenerationContext aus StorageContext erstellen
            generation_context = self.context_builder.build_from_storage_context(
                storage_context, document_type
            )

            # Über Standard-Workflow generieren
            return self.generate_document_from_context(generation_context, processing_options, output_path)

        except Exception as e:
            error_msg = f"Storage context generation failed: {e}"
            logger.error(error_msg)

            result = GenerationResult(success=False, document_type=document_type)
            result.set_error(error_msg)
            return result

    # =================================================================
    # BATCH OPERATIONS - Multiple Document Generation
    # =================================================================

    def generate_batch_documents(
        self,
        document_requests: List[Dict[str, Any]],
        batch_processing_options: Optional[ProcessingOptions] = None,
        output_base_path: Optional[Path] = None
    ) -> BatchGenerationResult:
        """
        Generiert mehrere Dokumente in einem Batch.

        Args:
            document_requests: Liste von Dokument-Request-Parametern
            batch_processing_options: Batch-Verarbeitungsoptionen
            output_base_path: Basis-Pfad für alle Dokumente

        Returns:
            BatchGenerationResult mit allen Einzel-Ergebnissen

        Example:
            ```python
            requests = [
                {
                    'document_type': 'pdb',
                    'batch_number': 'P-123456789012',
                    'delivery_number': 'DEL-001'
                },
                {
                    'document_type': 'begleitschein',
                    'batch_number': 'P-123456789012',
                    'delivery_number': 'DEL-001'
                }
            ]
            batch_result = service.generate_batch_documents(requests)
            ```
        """
        try:
            logger.info(f"Starting batch generation of {len(document_requests)} documents")

            batch_result = BatchGenerationResult(
                overall_success=False,
                batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                batch_timestamp=datetime.now(),
                requested_document_types=[req.get('document_type', 'unknown') for req in document_requests]
            )

            # Erstelle GenerationContexts aus Requests
            contexts = []
            for i, request in enumerate(document_requests):
                try:
                    context = self._create_context_from_request(request)
                    contexts.append(context)
                except Exception as e:
                    batch_result.add_batch_error(f"Request {i+1} invalid: {e}")

            if not contexts:
                batch_result.add_batch_error("No valid document requests found")
                return batch_result

            # Batch-Generation durchführen
            generation_results = self.word_processor.generate_batch_documents(
                contexts, output_base_path
            )

            # Ergebnisse in BatchResult sammeln
            for result in generation_results:
                batch_result.add_result(result)

            # Storage Integration erfolgt bereits direkt über _resolve_output_path()

            # Statistics
            self.stats['batch_operations'] += 1

            logger.info(f"Batch generation completed: {batch_result.get_summary()}")

            return batch_result

        except Exception as e:
            error_msg = f"Batch generation failed: {e}"
            logger.error(error_msg)

            batch_result = BatchGenerationResult(overall_success=False)
            batch_result.add_batch_error(error_msg)
            return batch_result

    # =================================================================
    # HILFSMETHODEN UND UTILITIES
    # =================================================================

    def _create_context_from_request(self, request: Dict[str, Any]) -> GenerationContext:
        """Erstellt GenerationContext aus Request-Dictionary."""
        try:
            # Document Type extrahieren und validieren
            document_type_str = request.get('document_type')
            if not document_type_str:
                raise ValueError("document_type is required")

            document_type = DocumentType.from_string(document_type_str)
            if not document_type:
                raise ValueError(f"Invalid document_type: {document_type_str}")

            # Context erstellen
            return self.context_builder.build_from_parameters(
                batch_number=request.get('batch_number', ''),
                delivery_number=request.get('delivery_number', ''),
                document_type=document_type,
                article_number=request.get('article_number', ''),
                supplier_name=request.get('supplier_name', ''),
                quantity=request.get('quantity', 0),
                employee_name=request.get('employee_name', ''),
                additional_placeholders=request.get('additional_data', {})
            )

        except Exception as e:
            raise ValueError(f"Invalid request format: {e}")

    def _apply_processing_options(
        self,
        context: GenerationContext,
        options: ProcessingOptions
    ) -> GenerationContext:
        """Wendet ProcessingOptions auf GenerationContext an."""
        try:
            # Template Version
            if options.template_version != "latest":
                context.template_version = options.template_version

            # Custom Data aus Options
            if options.include_metadata:
                context.custom_data['processing_options'] = asdict(options)

            return context

        except Exception as e:
            logger.warning(f"Error applying processing options: {e}")
            return context

    def _resolve_output_path(
        self,
        context: GenerationContext,
        specified_path: Optional[Path],
        options: Optional[ProcessingOptions]
    ) -> Optional[Path]:
        """
        Löst finalen Output-Pfad auf.
        Nutzt die gleiche bewährte Logik wie WordProcessor._generate_output_path()
        """
        try:
            # Explizit angegebener Pfad hat Vorrang
            if specified_path:
                return specified_path

            # Processing Options Custom Path
            if options and options.custom_output_path:
                return options.custom_output_path

            # DocumentStorageService Path (wie WordProcessor)
            if (context.batch_number and context.delivery_number and
                hasattr(context, 'article_number') and context.article_number):
                try:
                    # Import DocumentStorageService für echte Pfad-Auflösung (wie WordProcessor)
                    from ..document_storage.document_storage_service import document_storage_service

                    # Hole korrekten Artikelordner-Pfad
                    storage_path, warnings = document_storage_service.get_document_path(
                        batch_number=context.batch_number,
                        delivery_number=context.delivery_number,
                        article_number=getattr(context, 'article_number', ''),
                        supplier_name=getattr(context, 'supplier_name', ''),
                        create_folders=True
                    )

                    if storage_path and storage_path != Path("."):
                        # Dateiname generieren
                        template_info = get_template_info(context.document_type)
                        if template_info:
                            filename = template_info.generate_filename(context.to_placeholder_dict())
                        else:
                            timestamp = context.generation_timestamp.strftime("%Y%m%d_%H%M%S")
                            filename = f"{context.document_type.value}_{timestamp}.docx"

                        return storage_path / filename

                except Exception as e:
                    logger.warning(f"DocumentStorageService path resolution failed: {e}")

            # Fallback: None → WordProcessor/BarcodeGenerator wird eigenen Pfad generieren
            return None

        except Exception as e:
            logger.warning(f"Error resolving output path: {e}")
            return None


    def _open_document(self, document_path: Path):
        """Öffnet generiertes Dokument."""
        try:
            import os
            import platform

            if platform.system() == 'Windows':
                os.startfile(str(document_path))
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{document_path}"')
            else:  # Linux
                os.system(f'xdg-open "{document_path}"')

            logger.info(f"Document opened: {document_path}")

        except Exception as e:
            logger.warning(f"Could not open document: {e}")

    # =================================================================
    # SERVICE MANAGEMENT UND DIAGNOSTICS
    # =================================================================

    def get_supported_document_types(self) -> List[Dict[str, Any]]:
        """Gibt alle unterstützten Document Types mit Informationen zurück."""
        try:
            return [
                {
                    'type': doc_type.value,
                    'name': doc_type.display_name,
                    'description': doc_type.description,
                    'template_info': asdict(template_info)
                }
                for doc_type in DocumentType
                for template_info in [get_template_info(doc_type)]
                if template_info
            ]
        except Exception as e:
            logger.error(f"Error getting document types: {e}")
            return []

    def validate_service_health(self) -> Dict[str, Any]:
        """Validiert Service-Gesundheit und Verfügbarkeit."""
        try:
            health_check = {
                'service_healthy': True,
                'timestamp': datetime.now().isoformat(),
                'components': {},
                'errors': [],
                'warnings': []
            }

            # Context Builder Check
            try:
                builder_stats = self.context_builder.get_builder_statistics()
                health_check['components']['context_builder'] = {
                    'status': 'healthy',
                    'statistics': builder_stats
                }
            except Exception as e:
                health_check['components']['context_builder'] = {'status': 'error', 'error': str(e)}
                health_check['errors'].append(f"ContextBuilder: {e}")
                health_check['service_healthy'] = False

            # Word Processor Check
            try:
                processor_validation = self.word_processor.validate_processing_capabilities()
                health_check['components']['word_processor'] = {
                    'status': 'healthy' if processor_validation.get('docx_available') else 'error',
                    'capabilities': processor_validation
                }
                if not processor_validation.get('docx_available'):
                    health_check['errors'].append("DOCX processing not available")
                    health_check['service_healthy'] = False
            except Exception as e:
                health_check['components']['word_processor'] = {'status': 'error', 'error': str(e)}
                health_check['errors'].append(f"WordProcessor: {e}")
                health_check['service_healthy'] = False

            # Storage System Check - jetzt über direkte document_storage_service Integration
            try:
                from ..document_storage.document_storage_service import document_storage_service
                storage_stats = document_storage_service.get_storage_statistics()
                health_check['components']['storage_system'] = {
                    'status': 'healthy',
                    'statistics': storage_stats
                }
            except Exception as e:
                health_check['components']['storage_system'] = {'status': 'error', 'error': str(e)}
                health_check['warnings'].append(f"Storage System: {e}")

            return health_check

        except Exception as e:
            return {
                'service_healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_service_statistics(self) -> Dict[str, Any]:
        """Gibt umfassende Service-Statistiken zurück."""
        try:
            return {
                'service_stats': self.stats,
                'service_config': self.config,
                'uptime_seconds': (datetime.now() - self.stats['service_initialized']).total_seconds(),
                'context_builder_stats': self.context_builder.get_builder_statistics(),
                'word_processor_stats': self.word_processor.get_word_processor_statistics(),
                'storage_integration_enabled': self.config['storage_integration_enabled'],
                'supported_document_types': len(DocumentType),
                'available_templates': len(get_all_template_info())
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def reset_service_statistics(self):
        """Setzt Service-Statistiken zurück."""
        try:
            # Service Stats
            preserved_init_time = self.stats['service_initialized']
            for key in self.stats:
                if key != 'service_initialized':
                    self.stats[key] = 0

            # Component Stats
            self.context_builder.reset_statistics()

            logger.info("Service statistics reset")

        except Exception as e:
            logger.error(f"Error resetting statistics: {e}")

    def configure_service(self, config_updates: Dict[str, Any]):
        """Aktualisiert Service-Konfiguration."""
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    old_value = self.config[key]
                    self.config[key] = value
                    logger.info(f"Configuration updated: {key} = {value} (was: {old_value})")
                else:
                    logger.warning(f"Unknown configuration key: {key}")

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")

    def _generate_barcode_document(self, context: GenerationContext, output_path: Optional[Path] = None) -> GenerationResult:
        """
        Generate barcode document using BarcodeGenerator.

        Args:
            context: GenerationContext with barcode data
            output_path: Optional output path

        Returns:
            GenerationResult with barcode generation results
        """
        try:
            # Create barcode value from context (like Item.generate_barcode_content())
            barcode_value = f"{context.article_number}-{context.batch_number}-{context.delivery_number}"

            # output_path sollte bereits von _resolve_output_path() kommen
            # Keine eigene Pfad-Logik mehr nötig

            # Get barcode-specific options from context
            barcode_type = context.custom_data.get('barcode_type', 'CODE128')
            filename_prefix = context.custom_data.get('filename_prefix', 'barcode')
            open_after_creation = context.custom_data.get('open_after_creation', False)

            # Generate barcode with additional context data
            barcode_result = self.barcode_generator.generate_barcode(
                value=barcode_value,
                output_path=output_path,
                barcode_type=barcode_type,
                filename_prefix=filename_prefix,
                open_after_creation=open_after_creation,
                additional_data={
                    'article_number': context.article_number,
                    'batch_number': context.batch_number,
                    'delivery_number': context.delivery_number,  # ADDED: Missing delivery_number
                    'supplier_name': getattr(context, 'supplier_name', ''),  # ADDED: Missing supplier_name
                    'storage_location': context.custom_data.get('storage_location', 'LAGER-001')
                }
            )

            # Convert BarcodeGenerationResult to GenerationResult
            generation_result = GenerationResult(success=barcode_result.success)
            generation_result.document_type = DocumentType.BARCODE
            generation_result.document_path = barcode_result.barcode_path
            generation_result.generation_time = barcode_result.generation_time

            if not barcode_result.success:
                generation_result.set_error(barcode_result.error or "Barcode generation failed")
                for warning in barcode_result.warnings:
                    generation_result.add_warning(warning)

            # Add barcode-specific metadata
            generation_result.metadata.update(barcode_result.metadata)
            generation_result.metadata.update({
                'barcode_value': barcode_value,
                'document_format': 'png',
                'generation_method': 'barcode_generator'
            })

            logger.info(f"Barcode generation {'successful' if generation_result.success else 'failed'}: {barcode_value}")
            return generation_result

        except Exception as e:
            error_result = GenerationResult(success=False)
            error_result.document_type = DocumentType.BARCODE
            error_result.set_error(f"Barcode document generation error: {str(e)}")
            logger.error(f"Error generating barcode document: {e}")
            return error_result

    def _upload_generated_documents_to_sharepoint(
        self,
        result: GenerationResult,
        context: GenerationContext,
        batch_number: str,
        delivery_number: str,
        article_number: str = "",
        supplier_name: str = ""
    ) -> None:
        """
        Lädt generierte Dokumente auf SharePoint hoch (falls aktiviert).

        Args:
            result: GenerationResult mit Pfad zur generierten Datei
            context: GenerationContext mit Metadaten
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            article_number: Artikelnummer (optional)
            supplier_name: Lieferantenname (optional)
        """
        try:
            # Importiere DocumentStorageService
            from warehouse.application.services.document_storage.document_storage_service import (
                DocumentStorageService
            )
            from warehouse.shared.config.environment_config import env_config

            # Prüfe ob SharePoint aktiviert ist
            if not env_config.is_sharepoint_enabled():
                logger.debug("SharePoint not enabled, skipping upload")
                return

            # Prüfe ob Dokument erfolgreich generiert wurde
            if not result.document_path:
                logger.warning(f"No document path in result for SharePoint upload")
                return

            if not result.document_path.exists():
                logger.warning(f"Document path does not exist for SharePoint upload: {result.document_path}")
                return

            logger.debug(f"Document exists, preparing SharePoint upload: {result.document_path}")
            storage_service = DocumentStorageService()

            # Bestimme Dokument-Typ für Storage
            document_type_str = result.document_type.value if result.document_type else "document"
            logger.debug(f"Document type for storage: {document_type_str}")

            # Liste der hochzuladenden Dateien (DOCX + PDF falls vorhanden)
            files_to_upload = []

            # Haupt-Dokument (kann DOCX oder PDF oder PNG sein)
            files_to_upload.append({
                'path': result.document_path,
                'type': document_type_str
            })
            logger.debug(f"Added main document to upload list: {result.document_path.name}")

            # Wenn DOCX generiert wurde, prüfe ob auch PDF existiert
            if result.document_path.suffix.lower() == '.docx':
                # PRIMÄR: Nutze result.pdf_path falls vom WordConverter gesetzt
                pdf_path = None
                if hasattr(result, 'pdf_path') and result.pdf_path:
                    pdf_path = result.pdf_path
                    logger.debug(f"Using pdf_path from result: {pdf_path}")
                else:
                    # FALLBACK: Suche PDF im gleichen Ordner
                    pdf_path = result.document_path.with_suffix('.pdf')
                    logger.debug(f"Searching for PDF with fallback method: {pdf_path}")

                if pdf_path and pdf_path.exists():
                    files_to_upload.append({
                        'path': pdf_path,
                        'type': document_type_str
                    })
                    logger.debug(f"Added PDF to upload list: {pdf_path.name}")
                else:
                    logger.warning(f"PDF not found for upload: {pdf_path if pdf_path else 'N/A'}")

            # Lade alle Dateien hoch
            for file_info in files_to_upload:
                file_path = file_info['path']
                doc_type = file_info['type']

                # Lese Datei als bytes
                with open(file_path, 'rb') as f:
                    document_data = f.read()

                # Upload zu SharePoint via DocumentStorageService
                logger.info(f"Uploading {file_path.name} to SharePoint...")

                upload_result = storage_service.save_document(
                    document_data=document_data,
                    document_name=file_path.name,
                    document_type=doc_type,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    article_number=article_number,
                    supplier_name=supplier_name
                )

                if upload_result.success and upload_result.sharepoint_url:
                    logger.info(f"Successfully uploaded {file_path.name} to SharePoint: {upload_result.sharepoint_url}")
                    # Speichere SharePoint URL im Result Metadata
                    if 'sharepoint_urls' not in result.metadata:
                        result.metadata['sharepoint_urls'] = []
                    result.metadata['sharepoint_urls'].append(upload_result.sharepoint_url)
                elif upload_result.success:
                    logger.info(f"Document {file_path.name} saved locally (SharePoint upload skipped or failed)")
                else:
                    logger.warning(f"Failed to upload {file_path.name}: {upload_result.error}")
                    result.add_warning(f"SharePoint upload failed for {file_path.name}: {upload_result.error}")

        except Exception as e:
            logger.error(f"Error uploading to SharePoint: {e}")
            result.add_warning(f"SharePoint upload error: {str(e)}")


# =================================================================
# CONVENIENCE FUNCTIONS - Simplified API
# =================================================================

def generate_pdb_document(
    batch_number: str,
    delivery_number: str,
    article_number: str = "",
    supplier_name: str = "",
    quantity: int = 0,
    **kwargs
) -> GenerationResult:
    """
    Convenience Function: Generiert PDB-Dokument.

    Args:
        batch_number: Chargennummer
        delivery_number: Lieferscheinnummer
        article_number: Artikelnummer (optional)
        supplier_name: Lieferantenname (optional)
        quantity: Menge (optional)
        **kwargs: Weitere Parameter

    Returns:
        GenerationResult
    """
    service = DocumentGenerationService()
    return service.generate_document(
        document_type=DocumentType.PDB,
        batch_number=batch_number,
        delivery_number=delivery_number,
        article_number=article_number,
        supplier_name=supplier_name,
        quantity=quantity,
        **kwargs
    )


def generate_document_simple(
    document_type: str,
    batch_number: str,
    delivery_number: str,
    **kwargs
) -> GenerationResult:
    """
    Convenience Function: Einfache Dokument-Generierung.

    Args:
        document_type: Document Type als String
        batch_number: Chargennummer
        delivery_number: Lieferscheinnummer
        **kwargs: Weitere Parameter

    Returns:
        GenerationResult
    """
    service = DocumentGenerationService()
    return service.generate_document(
        document_type=document_type,
        batch_number=batch_number,
        delivery_number=delivery_number,
        **kwargs
    )


def validate_generation_service() -> Dict[str, Any]:
    """
    Convenience Function: Service-Validierung.

    Returns:
        Health Check Ergebnis
    """
    try:
        service = DocumentGenerationService()
        return service.validate_service_health()
    except Exception as e:
        return {
            'service_healthy': False,
            'error': f"Service initialization failed: {e}",
            'timestamp': datetime.now().isoformat()
        }