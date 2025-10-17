"""
Performance Optimization Package

Zentrale Performance-Optimierungen für das Warehouse System:
- Database Connection Pooling & Query Optimization
- Parallel Processing für CPU/IO-intensive Tasks
- Document Generation Pipeline mit Template Caching
- TTL Caching Integration
"""

from .db_optimizer import (
    ConnectionPool,
    QueryBatcher,
    BulkOperationOptimizer,
    IndexOptimizer,
    query_performance_monitor,
    initialize_performance_optimizers,
    get_connection_pool,
    get_bulk_optimizer,
    get_index_optimizer,
    cleanup_performance_optimizers
)

from .parallel_processor import (
    ParallelProcessor,
    DocumentGenerationBatch,
    AsyncIOProcessor,
    TaskResult,
    parallel_task,
    PerformanceProfiler,
    get_performance_profiler
)

from .document_pipeline import (
    OptimizedDocumentPipeline,
    DocumentRequest,
    DocumentResult,
    TemplateCache,
    generate_inspection_documents_optimized,
    get_global_pipeline,
    cleanup_global_pipeline
)

__all__ = [
    # DB Optimization
    'ConnectionPool',
    'QueryBatcher',
    'BulkOperationOptimizer',
    'IndexOptimizer',
    'query_performance_monitor',
    'initialize_performance_optimizers',
    'get_connection_pool',
    'get_bulk_optimizer',
    'get_index_optimizer',
    'cleanup_performance_optimizers',

    # Parallel Processing
    'ParallelProcessor',
    'DocumentGenerationBatch',
    'AsyncIOProcessor',
    'TaskResult',
    'parallel_task',
    'PerformanceProfiler',
    'get_performance_profiler',

    # Document Pipeline
    'OptimizedDocumentPipeline',
    'DocumentRequest',
    'DocumentResult',
    'TemplateCache',
    'generate_inspection_documents_optimized',
    'get_global_pipeline',
    'cleanup_global_pipeline'
]