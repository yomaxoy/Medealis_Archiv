"""
Optimierte Document Generation Pipeline

Implementiert parallele Dokument-Generierung, Template-Caching,
und Batch-PDF-Conversion für maximale Performance.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .parallel_processor import DocumentGenerationBatch, AsyncIOProcessor
from ..caching import ttl_cache

logger = logging.getLogger(__name__)


@dataclass
class DocumentRequest:
    """Request für Dokument-Generierung."""
    document_type: str
    batch_number: str
    delivery_number: str = ""
    article_number: str = ""
    employee_name: str = ""
    priority: int = 0  # 0 = normal, 1 = high, 2 = critical
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def unique_key(self) -> str:
        """Eindeutiger Key für Request."""
        return f"{self.document_type}_{self.batch_number}_{self.delivery_number}_{self.article_number}"


@dataclass
class DocumentResult:
    """Ergebnis der Dokument-Generierung."""
    request: DocumentRequest
    success: bool
    file_path: Optional[str] = None
    file_size: int = 0
    generation_time: float = 0.0
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class TemplateCache:
    """
    Optimierter Template-Cache für bessere Performance.

    Cached geladene Templates und Word-Objekte zwischen Generierungen.
    """

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self._template_cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}

    @ttl_cache(seconds=1800, maxsize=20, key_prefix="template")
    def get_template(self, template_name: str, template_path: Path) -> Any:
        """
        Holt Template aus Cache oder lädt es.

        Args:
            template_name: Name des Templates
            template_path: Pfad zum Template

        Returns:
            Template-Objekt
        """
        try:
            # Template laden (wird durch TTL-Cache gecacht)
            from docx import Document
            template = Document(str(template_path))

            # Access-Zeit aktualisieren
            self._access_times[template_name] = time.time()

            logger.debug(f"Template loaded: {template_name}")
            return template

        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise

    def clear_old_templates(self, max_age_seconds: int = 3600):
        """Entfernt alte Templates aus Cache."""
        current_time = time.time()
        old_templates = [
            name for name, access_time in self._access_times.items()
            if current_time - access_time > max_age_seconds
        ]

        for template_name in old_templates:
            if hasattr(self.get_template, 'cache_clear'):
                # Spezifischen Cache-Entry löschen wäre ideal
                pass
            del self._access_times[template_name]

        if old_templates:
            logger.info(f"Cleared {len(old_templates)} old templates from cache")


class OptimizedDocumentPipeline:
    """
    Optimierte Pipeline für Batch-Dokument-Generierung.

    Features:
    - Parallele Generierung
    - Template Caching
    - Batch PDF-Conversion
    - Smart Prioritization
    """

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.template_cache = TemplateCache()
        self.async_processor = AsyncIOProcessor()
        self._generation_stats: Dict[str, Any] = {}

    async def generate_documents_optimized(
        self,
        requests: List[DocumentRequest]
    ) -> List[DocumentResult]:
        """
        Generiert Dokumente mit optimierter Pipeline.

        Args:
            requests: Liste von Document Requests

        Returns:
            Liste von Document Results
        """
        start_time = time.time()

        # 1. Prioritization & Deduplication
        unique_requests = self._deduplicate_requests(requests)
        prioritized_requests = self._prioritize_requests(unique_requests)

        # 2. Batch-Verarbeitung nach Typ
        batched_requests = self._group_by_type(prioritized_requests)

        # 3. Parallele Generierung pro Typ
        all_results = []
        for doc_type, type_requests in batched_requests.items():
            type_results = await self._generate_batch_parallel(doc_type, type_requests)
            all_results.extend(type_results)

        # 4. Batch PDF-Conversion
        await self._batch_convert_to_pdf(all_results)

        # 5. Statistiken
        total_time = time.time() - start_time
        self._update_statistics(requests, all_results, total_time)

        logger.info(
            f"Optimized document generation completed: "
            f"{len(all_results)} documents in {total_time:.2f}s"
        )

        return all_results

    def _deduplicate_requests(self, requests: List[DocumentRequest]) -> List[DocumentRequest]:
        """Entfernt doppelte Requests."""
        seen_keys: Set[str] = set()
        unique_requests = []

        for request in requests:
            if request.unique_key not in seen_keys:
                unique_requests.append(request)
                seen_keys.add(request.unique_key)
            else:
                logger.debug(f"Duplicate request removed: {request.unique_key}")

        return unique_requests

    def _prioritize_requests(self, requests: List[DocumentRequest]) -> List[DocumentRequest]:
        """Sortiert Requests nach Priorität."""
        return sorted(requests, key=lambda r: r.priority, reverse=True)

    def _group_by_type(self, requests: List[DocumentRequest]) -> Dict[str, List[DocumentRequest]]:
        """Gruppiert Requests nach Dokument-Typ."""
        batches: Dict[str, List[DocumentRequest]] = {}

        for request in requests:
            if request.document_type not in batches:
                batches[request.document_type] = []
            batches[request.document_type].append(request)

        return batches

    async def _generate_batch_parallel(
        self,
        doc_type: str,
        requests: List[DocumentRequest]
    ) -> List[DocumentResult]:
        """Generiert Batch von gleichen Dokument-Typen parallel."""
        logger.info(f"Generating {len(requests)} {doc_type} documents in parallel")

        # Template einmal laden für alle Requests dieses Typs
        template = await self._preload_template(doc_type)

        # Parallele Generierung
        tasks = []
        for request in requests:
            task = self._generate_single_document_async(request, template)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Konvertiere Exceptions zu Error-Results
        document_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = DocumentResult(
                    request=requests[i],
                    success=False,
                    error=str(result)
                )
                document_results.append(error_result)
            else:
                document_results.append(result)

        return document_results

    async def _preload_template(self, doc_type: str) -> Optional[Any]:
        """Lädt Template für Dokument-Typ vor."""
        try:
            # Template-Pfad bestimmen
            template_map = {
                'begleitschein': 'Fo00057_Begleitschein.docx',
                'wareneingangskontrolle': 'Fo0113_Wareneingangskontrolle.docx',
                'pdb': 'Fo00040_PDB_Template.docx',
                'sichtkontrolle': 'Fo00141_Sichtkontrolle.docx'
            }

            template_file = template_map.get(doc_type)
            if not template_file:
                return None

            # Template async laden
            template_path = Path("resources/templates") / template_file
            template = await self.async_processor.async_file_operation(
                self.template_cache.get_template,
                doc_type,
                template_path
            )

            return template

        except Exception as e:
            logger.error(f"Failed to preload template for {doc_type}: {e}")
            return None

    async def _generate_single_document_async(
        self,
        request: DocumentRequest,
        template: Optional[Any] = None
    ) -> DocumentResult:
        """Generiert einzelnes Dokument asynchron."""
        start_time = time.time()

        try:
            # Import hier um Thread-Issues zu vermeiden
            from ...application.services.document_generation.document_generation_service import DocumentGenerationService

            # Document Service holen
            doc_service = DocumentGenerationService()

            # Dokument generieren (IO-bound Operation)
            result = await self.async_processor.async_file_operation(
                doc_service.generate_document,
                document_type=request.document_type,
                batch_number=request.batch_number,
                delivery_number=request.delivery_number,
                article_number=request.article_number,
                employee_name=request.employee_name,
                **request.metadata
            )

            generation_time = time.time() - start_time

            return DocumentResult(
                request=request,
                success=True,
                file_path=result.get('file_path'),
                file_size=result.get('file_size', 0),
                generation_time=generation_time
            )

        except Exception as e:
            generation_time = time.time() - start_time
            logger.error(f"Document generation failed for {request.unique_key}: {e}")

            return DocumentResult(
                request=request,
                success=False,
                error=str(e),
                generation_time=generation_time
            )

    async def _batch_convert_to_pdf(self, results: List[DocumentResult]):
        """Konvertiert generierte DOCX-Dateien batch-weise zu PDF."""
        docx_files = [
            result for result in results
            if result.success and result.file_path and result.file_path.endswith('.docx')
        ]

        if not docx_files:
            return

        logger.info(f"Batch converting {len(docx_files)} DOCX files to PDF")

        # PDF-Conversion Tasks
        conversion_tasks = []
        for result in docx_files:
            task = self.async_processor.async_file_operation(
                self._convert_single_pdf,
                result.file_path
            )
            conversion_tasks.append(task)

        # Parallele Ausführung
        await asyncio.gather(*conversion_tasks, return_exceptions=True)

    def _convert_single_pdf(self, docx_path: str) -> Optional[str]:
        """Konvertiert einzelne DOCX zu PDF."""
        try:
            from ...application.services.document_generation.word_converter import WordConverter

            converter = WordConverter()
            pdf_path = converter.convert_to_pdf(docx_path)

            return pdf_path

        except Exception as e:
            logger.error(f"PDF conversion failed for {docx_path}: {e}")
            return None

    def _update_statistics(
        self,
        requests: List[DocumentRequest],
        results: List[DocumentResult],
        total_time: float
    ):
        """Aktualisiert Pipeline-Statistiken."""
        successful = len([r for r in results if r.success])

        self._generation_stats = {
            'total_requests': len(requests),
            'unique_documents': len(results),
            'successful': successful,
            'failed': len(results) - successful,
            'total_time': total_time,
            'avg_time_per_doc': total_time / max(len(results), 1),
            'throughput_docs_per_sec': len(results) / max(total_time, 0.001)
        }

        # Per-Type Statistics
        type_stats = {}
        for result in results:
            doc_type = result.request.document_type
            if doc_type not in type_stats:
                type_stats[doc_type] = {'count': 0, 'successful': 0, 'total_time': 0.0}

            type_stats[doc_type]['count'] += 1
            if result.success:
                type_stats[doc_type]['successful'] += 1
            type_stats[doc_type]['total_time'] += result.generation_time

        self._generation_stats['by_type'] = type_stats

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Gibt Pipeline-Statistiken zurück."""
        return self._generation_stats.copy()

    def cleanup(self):
        """Räumt Pipeline-Ressourcen auf."""
        self.async_processor.cleanup()
        self.template_cache.clear_old_templates()


# Usage Functions
async def generate_inspection_documents_optimized(
    batch_number: str,
    delivery_number: str,
    article_number: str,
    employee_name: str
) -> List[DocumentResult]:
    """
    Optimierte Generierung aller Prüf-Dokumente für einen Artikel.

    Ersetzt sequenzielle Generierung durch parallele Pipeline.
    """
    # Definiere Standard-Dokumente für Prüfung
    requests = [
        DocumentRequest(
            document_type='begleitschein',
            batch_number=batch_number,
            delivery_number=delivery_number,
            article_number=article_number,
            employee_name=employee_name,
            priority=2  # Critical
        ),
        DocumentRequest(
            document_type='wareneingangskontrolle',
            batch_number=batch_number,
            delivery_number=delivery_number,
            article_number=article_number,
            employee_name=employee_name,
            priority=2  # Critical
        ),
        DocumentRequest(
            document_type='pdb',
            batch_number=batch_number,
            delivery_number=delivery_number,
            article_number=article_number,
            employee_name=employee_name,
            priority=1  # High
        ),
        DocumentRequest(
            document_type='sichtkontrolle',
            batch_number=batch_number,
            delivery_number=delivery_number,
            article_number=article_number,
            employee_name=employee_name,
            priority=1  # High
        )
    ]

    # Pipeline verwenden
    pipeline = OptimizedDocumentPipeline(max_workers=2)
    try:
        results = await pipeline.generate_documents_optimized(requests)
        return results
    finally:
        pipeline.cleanup()


# Global Pipeline Instance
_global_pipeline: Optional[OptimizedDocumentPipeline] = None


def get_global_pipeline() -> OptimizedDocumentPipeline:
    """Gibt globale Pipeline-Instanz zurück."""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = OptimizedDocumentPipeline()
    return _global_pipeline


def cleanup_global_pipeline():
    """Räumt globale Pipeline auf."""
    global _global_pipeline
    if _global_pipeline:
        _global_pipeline.cleanup()
        _global_pipeline = None