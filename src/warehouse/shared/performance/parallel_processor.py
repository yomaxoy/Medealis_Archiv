"""
Parallel Processing für Performance-kritische Operationen

Ermöglicht parallele Dokument-Generierung, Batch-Verarbeitung
und asynchrone IO-Operationen.
"""

import asyncio
import logging
import time
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Ergebnis einer parallelen Task."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ParallelProcessor:
    """
    Verwaltet parallele Verarbeitung von Tasks.

    Unterstützt Thread- und Process-basierte Parallelisierung
    mit intelligenter Task-Verteilung.
    """

    def __init__(self, max_workers: int = 4, use_processes: bool = False):
        self.max_workers = max_workers
        self.use_processes = use_processes
        self._executor = None
        self._active_tasks: Dict[str, concurrent.futures.Future] = {}
        self._task_counter = 0
        self._lock = threading.Lock()

    def __enter__(self):
        self._start_executor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._shutdown_executor()

    def _start_executor(self):
        """Startet Executor basierend auf Konfiguration."""
        if self.use_processes:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
            logger.info(f"Started ProcessPoolExecutor with {self.max_workers} workers")
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
            logger.info(f"Started ThreadPoolExecutor with {self.max_workers} workers")

    def _shutdown_executor(self):
        """Beendet Executor und wartet auf Tasks."""
        if self._executor:
            self._executor.shutdown(wait=True)
            logger.info("Executor shutdown completed")

    def submit_task(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Übermittelt Task zur parallelen Ausführung.

        Args:
            func: Funktion die ausgeführt werden soll
            *args: Argumente für die Funktion
            task_id: Optional Task-ID
            **kwargs: Keyword-Argumente für die Funktion

        Returns:
            Task-ID
        """
        if not self._executor:
            self._start_executor()

        with self._lock:
            if task_id is None:
                self._task_counter += 1
                task_id = f"task_{self._task_counter}"

            future = self._executor.submit(func, *args, **kwargs)
            self._active_tasks[task_id] = future

        logger.debug(f"Submitted task {task_id}")
        return task_id

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """
        Wartet auf Completion einer spezifischen Task.

        Args:
            task_id: ID der Task
            timeout: Optional Timeout in Sekunden

        Returns:
            TaskResult mit Ergebnis
        """
        if task_id not in self._active_tasks:
            return TaskResult(
                task_id=task_id,
                success=False,
                error=f"Task {task_id} not found"
            )

        future = self._active_tasks[task_id]
        start_time = time.time()

        try:
            result = future.result(timeout=timeout)
            execution_time = time.time() - start_time

            with self._lock:
                del self._active_tasks[task_id]

            return TaskResult(
                task_id=task_id,
                success=True,
                result=result,
                execution_time=execution_time
            )

        except concurrent.futures.TimeoutError:
            return TaskResult(
                task_id=task_id,
                success=False,
                error=f"Task {task_id} timed out after {timeout}s",
                execution_time=time.time() - start_time
            )

        except Exception as e:
            execution_time = time.time() - start_time

            with self._lock:
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]

            return TaskResult(
                task_id=task_id,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    def wait_for_all(self, timeout: Optional[float] = None) -> List[TaskResult]:
        """
        Wartet auf Completion aller aktiven Tasks.

        Args:
            timeout: Optional Timeout in Sekunden

        Returns:
            Liste von TaskResults
        """
        results = []
        task_ids = list(self._active_tasks.keys())

        for task_id in task_ids:
            result = self.wait_for_task(task_id, timeout)
            results.append(result)

        return results

    def get_active_task_count(self) -> int:
        """Gibt Anzahl der aktiven Tasks zurück."""
        return len(self._active_tasks)


class DocumentGenerationBatch:
    """
    Spezialisierte Batch-Verarbeitung für Dokument-Generierung.

    Optimiert für parallele Erstellung mehrerer Dokumente
    mit geteilten Ressourcen.
    """

    def __init__(self, max_workers: int = 2):
        self.processor = ParallelProcessor(max_workers=max_workers, use_processes=False)
        self._generation_stats: Dict[str, Any] = {}

    def generate_documents_parallel(
        self,
        document_requests: List[Dict[str, Any]]
    ) -> List[TaskResult]:
        """
        Generiert mehrere Dokumente parallel.

        Args:
            document_requests: Liste von Dokument-Requests
                [{'type': 'begleitschein', 'batch_number': '...', ...}, ...]

        Returns:
            Liste von TaskResults
        """
        start_time = time.time()

        with self.processor:
            # Übermittle alle Tasks
            task_ids = []
            for i, request in enumerate(document_requests):
                task_id = f"doc_gen_{i}_{request.get('type', 'unknown')}"
                self.processor.submit_task(
                    self._generate_single_document,
                    request,
                    task_id=task_id
                )
                task_ids.append(task_id)

            # Warte auf alle Results
            results = []
            for task_id in task_ids:
                result = self.processor.wait_for_task(task_id, timeout=60.0)
                results.append(result)

        total_time = time.time() - start_time
        successful = len([r for r in results if r.success])

        self._generation_stats = {
            'total_documents': len(document_requests),
            'successful': successful,
            'failed': len(document_requests) - successful,
            'total_time': total_time,
            'avg_time_per_doc': total_time / max(len(document_requests), 1)
        }

        logger.info(
            f"Parallel document generation completed: "
            f"{successful}/{len(document_requests)} successful in {total_time:.2f}s"
        )

        return results

    def _generate_single_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generiert einzelnes Dokument - wird parallel ausgeführt.

        Args:
            request: Dokument Request

        Returns:
            Generierungs-Ergebnis
        """
        try:
            # Import hier um Thread-Probleme zu vermeiden
            from ...application.services.service_registry import get_data_integration_service
            from ...application.services.document_generation.document_generation_service import DocumentGenerationService

            # Services holen
            data_service = get_data_integration_service()
            doc_service = DocumentGenerationService()

            # Dokument generieren
            result = doc_service.generate_document(
                document_type=request['type'],
                batch_number=request['batch_number'],
                delivery_number=request.get('delivery_number', ''),
                article_number=request.get('article_number', ''),
                **request.get('additional_params', {})
            )

            return {
                'success': True,
                'document_type': request['type'],
                'file_path': result.get('file_path'),
                'file_size': result.get('file_size', 0)
            }

        except Exception as e:
            logger.error(f"Document generation failed for {request}: {e}")
            return {
                'success': False,
                'document_type': request['type'],
                'error': str(e)
            }

    def get_generation_stats(self) -> Dict[str, Any]:
        """Gibt Generierungs-Statistiken zurück."""
        return self._generation_stats.copy()


class AsyncIOProcessor:
    """
    Asynchrone IO-Operationen für File-System und Network-Tasks.

    Optimiert für IO-bound Operationen wie File-Operationen,
    PDF-Conversions und API-Calls.
    """

    def __init__(self):
        self._loop = None
        self._executor = ThreadPoolExecutor(max_workers=8)

    async def async_file_operation(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Führt File-Operation asynchron aus.

        Args:
            operation: File-Operation Funktion
            *args: Argumente
            **kwargs: Keyword-Argumente

        Returns:
            Ergebnis der Operation
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            operation,
            *args,
            **kwargs
        )

    async def batch_file_operations(
        self,
        operations: List[Tuple[Callable, tuple, dict]]
    ) -> List[Any]:
        """
        Führt mehrere File-Operationen parallel aus.

        Args:
            operations: Liste von (function, args, kwargs) Tupeln

        Returns:
            Liste von Ergebnissen
        """
        tasks = []
        for func, args, kwargs in operations:
            task = self.async_file_operation(func, *args, **kwargs)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    def cleanup(self):
        """Räumt Executor auf."""
        self._executor.shutdown(wait=True)


def parallel_task(max_workers: int = 4, use_processes: bool = False):
    """
    Decorator für automatische Parallelisierung von Funktionen.

    Args:
        max_workers: Maximale Anzahl Workers
        use_processes: Ob Processes statt Threads verwendet werden sollen

    Usage:
        @parallel_task(max_workers=2)
        def process_items(items):
            return [process_item(item) for item in items]
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with ParallelProcessor(max_workers, use_processes) as processor:
                task_id = processor.submit_task(func, *args, **kwargs)
                result = processor.wait_for_task(task_id)

                if result.success:
                    return result.result
                else:
                    raise RuntimeError(f"Parallel task failed: {result.error}")

        return wrapper
    return decorator


# Performance Monitoring
class PerformanceProfiler:
    """
    Profiler für Performance-Monitoring paralleler Operationen.
    """

    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def record_operation(self, operation_name: str, execution_time: float):
        """Zeichnet Operation-Metrics auf."""
        with self._lock:
            if operation_name not in self._metrics:
                self._metrics[operation_name] = []
            self._metrics[operation_name].append(execution_time)

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Gibt Performance-Statistiken zurück."""
        stats = {}

        with self._lock:
            for operation, times in self._metrics.items():
                if times:
                    stats[operation] = {
                        'count': len(times),
                        'total_time': sum(times),
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times)
                    }

        return stats

    def clear_metrics(self):
        """Leert gesammelte Metrics."""
        with self._lock:
            self._metrics.clear()


# Global Instances
_performance_profiler = PerformanceProfiler()


def get_performance_profiler() -> PerformanceProfiler:
    """Gibt globalen Performance Profiler zurück."""
    return _performance_profiler