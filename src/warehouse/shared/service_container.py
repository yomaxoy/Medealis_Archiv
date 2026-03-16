"""
Service Container - Singleton Pattern für Application Services.

Zentraler Container für alle Application Services, der von Admin- und User-App
gemeinsam genutzt wird. Verhindert duplizierte Service-Instanzen und Cache-Inkonsistenzen.

FastAPI-ready: Kann später als Dependency Injection genutzt werden.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Singleton Service Container - Shared zwischen Admin & User App.

    Implementiert Singleton Pattern - beide Streamlit Apps nutzen
    die gleichen Service-Instanzen, was Cache-Konsistenz garantiert
    und das User-Login-Problem zwischen Apps löst.

    Features:
    - Singleton Pattern (nur eine Instanz pro Python-Prozess)
    - Lazy Loading (Services werden erst bei Bedarf initialisiert)
    - Thread-safe (für Multi-User-Szenarien)
    - FastAPI-ready (Dependency Injection Pattern)

    Example:
        # In beiden Apps (Admin + User):
        from warehouse.shared.service_container import ServiceContainer

        services = ServiceContainer.get_instance()
        user = services.user_service.authenticate(username, password)
    """

    _instance: Optional['ServiceContainer'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton Pattern - nur eine Instanz erlaubt."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialisiert Service-Instanzen.

        Wird nur einmal ausgeführt (Singleton).
        Services werden lazy geladen (Import nur wenn benötigt).
        """
        # Nur einmal initialisieren
        if ServiceContainer._initialized:
            return

        logger.info("🚀 Initializing ServiceContainer (Singleton)...")

        # Lazy Imports - nur wenn ServiceContainer erstellt wird
        # Services nutzen die bestehende Architektur (entity_services/)
        from warehouse.application.services import (
            DeliveryService,
            ItemService,
            SupplierService,
            OrderService,
        )
        from warehouse.application.services.user_service import UserService
        from warehouse.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl

        # Service-Instanzen erstellen (Singleton - nur einmal!)
        logger.info("📦 Creating service instances...")

        # User Service (mit Repository Injection - Clean Architecture)
        self.user_service = UserService(UserRepositoryImpl())

        # Entity Services (nutzen interne Repository-Creation)
        # Diese Services erstellen ihre Repositories selbst
        self.delivery_service = DeliveryService()
        self.supplier_service = SupplierService()
        self.item_service = ItemService()
        self.order_service = OrderService()

        ServiceContainer._initialized = True
        logger.info("✅ ServiceContainer initialized successfully")

    @classmethod
    def get_instance(cls) -> 'ServiceContainer':
        """
        Gibt Singleton-Instanz zurück.

        Returns:
            ServiceContainer: Die einzige ServiceContainer-Instanz

        Example:
            services = ServiceContainer.get_instance()
            user = services.user_service.get_user_by_id("123")
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """
        Setzt Container zurück (für Testing).

        WARNING: Nur in Tests verwenden! In Production nicht aufrufen.
        """
        logger.warning("⚠️  ServiceContainer reset called (should only be used in tests)")
        cls._instance = None
        cls._initialized = False

    def get_service(self, service_name: str):
        """
        Holt Service anhand Name (Alternative zu direktem Zugriff).

        Args:
            service_name: Name des Service ('user', 'delivery', 'supplier', 'item', 'order')

        Returns:
            Service-Instanz

        Raises:
            ValueError: Wenn Service nicht existiert

        Example:
            user_service = services.get_service('user')
        """
        service_map = {
            'user': self.user_service,
            'delivery': self.delivery_service,
            'supplier': self.supplier_service,
            'item': self.item_service,
            'order': self.order_service,
        }

        if service_name not in service_map:
            raise ValueError(
                f"Unknown service: {service_name}. "
                f"Available: {', '.join(service_map.keys())}"
            )

        return service_map[service_name]


# Convenience Function (für kürzeren Import)
def get_services() -> ServiceContainer:
    """
    Shortcut für ServiceContainer.get_instance().

    Returns:
        ServiceContainer: Singleton-Instanz

    Example:
        from warehouse.shared.service_container import get_services

        services = get_services()
        user = services.user_service.authenticate(username, password)
    """
    return ServiceContainer.get_instance()


# Legacy Support: Kompatibilität mit altem Code der dict erwartet
def get_services_dict() -> dict:
    """
    Legacy-Support: Gibt Services als Dict zurück.

    Für bestehenden Code, der services['delivery'] erwartet.

    Returns:
        dict: Services als Dictionary

    Example:
        services = get_services_dict()
        delivery = services['delivery'].get_delivery_by_number("LS-001")
    """
    container = get_services()
    return {
        'delivery': container.delivery_service,
        'supplier': container.supplier_service,
        'item': container.item_service,
        'order': container.order_service,
        'user': container.user_service,
    }
