"""
Service Registry - Singleton Pattern für Service-Instanzen

Verhindert wiederholte Service-Initialisierungen durch Singleton Pattern.
Einfache und effektive Lösung für Performance-Optimierung.
"""

import logging
from typing import Dict, Type, Any, Optional
import threading

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Singleton Registry für Service-Instanzen.

    Stellt sicher, dass jede Service-Klasse nur einmal instanziiert wird
    und die gleiche Instanz bei wiederholten Aufrufen zurückgegeben wird.

    Features:
    - Thread-safe
    - Lazy initialization
    - Memory management
    - Logging für Debugging
    """

    _instances: Dict[Type, Any] = {}
    _lock = threading.Lock()

    @classmethod
    def get_service(cls, service_class: Type, *args, lazy_init: bool = True, **kwargs) -> Any:
        """
        Gibt Service-Instanz zurück. Erstellt bei Bedarf neue Instanz.

        Args:
            service_class: Service-Klasse die instanziiert werden soll
            *args: Positional arguments für Service-Konstruktor
            **kwargs: Keyword arguments für Service-Konstruktor

        Returns:
            Service-Instanz (Singleton)

        Note:
            Wenn args/kwargs übergeben werden, werden diese nur bei der
            ersten Instanziierung verwendet. Nachfolgende Aufrufe
            ignorieren diese Parameter.
        """
        # Quick check without lock (performance optimization)
        if service_class in cls._instances:
            return cls._instances[service_class]

        # Double-check locking pattern for thread safety
        with cls._lock:
            if service_class not in cls._instances:
                try:
                    logger.debug(f"Creating new instance of {service_class.__name__}")
                    instance = service_class(*args, **kwargs)
                    cls._instances[service_class] = instance
                    logger.info(f"Service registered: {service_class.__name__}")
                except Exception as e:
                    logger.error(f"Failed to create service {service_class.__name__}: {e}")
                    raise
            else:
                if args or kwargs:
                    logger.warning(
                        f"Service {service_class.__name__} already exists. "
                        f"Constructor arguments ignored: args={args}, kwargs={kwargs}"
                    )

            return cls._instances[service_class]

    @classmethod
    def has_service(cls, service_class: Type) -> bool:
        """
        Prüft ob Service bereits im Registry ist.

        Args:
            service_class: Service-Klasse zu prüfen

        Returns:
            True wenn Service existiert, False sonst
        """
        return service_class in cls._instances

    @classmethod
    def remove_service(cls, service_class: Type) -> bool:
        """
        Entfernt Service aus Registry.

        Args:
            service_class: Service-Klasse zu entfernen

        Returns:
            True wenn Service entfernt wurde, False wenn nicht vorhanden
        """
        with cls._lock:
            if service_class in cls._instances:
                instance = cls._instances.pop(service_class)
                logger.info(f"Service removed: {service_class.__name__}")

                # Cleanup wenn Service close() Methode hat
                if hasattr(instance, 'close'):
                    try:
                        instance.close()
                        logger.debug(f"Service {service_class.__name__} closed successfully")
                    except Exception as e:
                        logger.warning(f"Error closing service {service_class.__name__}: {e}")

                return True
            return False

    @classmethod
    def clear_all(cls) -> int:
        """
        Entfernt alle Services aus Registry.

        Returns:
            Anzahl der entfernten Services
        """
        with cls._lock:
            count = len(cls._instances)

            # Cleanup alle Services
            for service_class, instance in cls._instances.items():
                if hasattr(instance, 'close'):
                    try:
                        instance.close()
                        logger.debug(f"Service {service_class.__name__} closed during clear_all")
                    except Exception as e:
                        logger.warning(f"Error closing service {service_class.__name__}: {e}")

            cls._instances.clear()
            logger.info(f"ServiceRegistry cleared. {count} services removed.")
            return count

    @classmethod
    def get_registered_services(cls) -> Dict[str, Any]:
        """
        Gibt alle registrierten Services zurück.

        Returns:
            Dictionary mit Service-Namen und Instanzen
        """
        return {service_class.__name__: instance
                for service_class, instance in cls._instances.items()}

    @classmethod
    def get_service_count(cls) -> int:
        """
        Gibt Anzahl der registrierten Services zurück.

        Returns:
            Anzahl der Services im Registry
        """
        return len(cls._instances)

    @classmethod
    def get_registry_stats(cls) -> Dict[str, Any]:
        """
        Gibt Registry-Statistiken zurück.

        Returns:
            Dictionary mit Statistiken
        """
        stats = {
            "total_services": len(cls._instances),
            "service_names": [service_class.__name__ for service_class in cls._instances.keys()],
            "memory_info": {}
        }

        # Memory usage (basic estimation)
        try:
            import sys
            total_size = sum(sys.getsizeof(instance) for instance in cls._instances.values())
            stats["memory_info"] = {
                "estimated_total_bytes": total_size,
                "estimated_total_mb": total_size / (1024 * 1024)
            }
        except Exception as e:
            logger.debug(f"Could not calculate memory stats: {e}")
            stats["memory_info"] = {"error": "Could not calculate"}

        return stats


# Convenience functions für häufig verwendete Services
def get_document_storage_service():
    """Convenience function für DocumentStorageService."""
    from .document_storage.document_storage_service import DocumentStorageService
    return ServiceRegistry.get_service(DocumentStorageService)


def get_data_integration_service():
    """Convenience function für DataIntegrationService."""
    from .data_integration_service import DataIntegrationService
    return ServiceRegistry.get_service(DataIntegrationService)


def get_item_service():
    """Convenience function für ItemService."""
    from .entity_services.item_service import ItemService
    return ServiceRegistry.get_service(ItemService)


def get_delivery_service():
    """Convenience function für DeliveryService."""
    from .entity_services.delivery_service import DeliveryService
    return ServiceRegistry.get_service(DeliveryService)


def get_supplier_service():
    """Convenience function für SupplierService."""
    from .entity_services.supplier_service import SupplierService
    return ServiceRegistry.get_service(SupplierService)


def get_pdf_merge_service():
    """Convenience function für PDFMergeService."""
    from .document_operations import PDFMergeService
    return ServiceRegistry.get_service(PDFMergeService)


def get_delivery_workflow_service():
    """Convenience function für DeliveryWorkflowService."""
    from .delivery_workflow_service import DeliveryWorkflowService
    return ServiceRegistry.get_service(DeliveryWorkflowService)


# Registry Management Functions
def clear_service_registry():
    """Leert das komplette Service Registry."""
    return ServiceRegistry.clear_all()


def get_service_registry_stats():
    """Gibt Service Registry Statistiken zurück."""
    return ServiceRegistry.get_registry_stats()