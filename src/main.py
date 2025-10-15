#!/usr/bin/env python3
"""
Main Entry Point für das Medealis Warehouse Management System.

Bootstraps das komplette System mit Clean Architecture:
- Database Initialization
- Logging Configuration
- Service Layer Setup
- Basic System Operations

Autor: Medealis
Version: 2.0.0
"""

import sys
import logging
from pathlib import Path
from datetime import date  # , datetime
from typing import Optional

# Add src and config to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
config_path = project_root / "config"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(config_path))

# Import infrastructure
from warehouse.infrastructure.database.connection import (
    initialize_database,
    create_tables,
    test_connection,
    is_initialized,
)

# Import application services
from warehouse.application.services.entity_services.delivery_service import (
    DeliveryService,
)
from warehouse.application.services.entity_services.item_service import ItemService
from warehouse.application.services.entity_services.supplier_service import (
    SupplierService,
)
from warehouse.application.services.entity_services.order_service import OrderService

# Import configuration
try:
    from config.logging_config import setup_logging, log_system_info
    from config.settings import settings
except ImportError:
    # Fallback to simple logging setup if config not available
    import logging

    def setup_logging(**kwargs):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger()

    def log_system_info():
        pass

    class SimpleSettings:
        APP_NAME = "Warehouse Management System"
        APP_VERSION = "2.0.0"
        LOG_LEVEL = "INFO"
        DEBUG = True
        ENVIRONMENT = "development"
        DATABASE_PATH = Path.home() / ".medealis" / "warehouse_new.db"  # NEU: neue DB mit Workflow-Steps

        @classmethod
        def ensure_directories(cls):
            cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    settings = SimpleSettings()
    settings.ensure_directories()

# Global logger
logger: Optional[logging.Logger] = None


class WarehouseApp:
    """
    Hauptanwendungsklasse für das Warehouse Management System.

    Orchestriert alle Komponenten der Clean Architecture:
    - Infrastructure Layer (Database)
    - Application Layer (Services)
    - Presentation Layer (CLI/API)
    """

    def __init__(self):
        """Initialisiert die Warehouse-Anwendung."""
        self.delivery_service: Optional[DeliveryService] = None
        self.item_service: Optional[ItemService] = None
        self.supplier_service: Optional[SupplierService] = None
        self.order_service: Optional[OrderService] = None
        self.initialized = False

    def initialize(self) -> bool:
        """
        Initialisiert das komplette System.

        Returns:
            True wenn erfolgreich initialisiert
        """
        try:
            logger.info("=== Starte Warehouse Management System ===")

            # 1. Database Setup
            if not self._setup_database():
                return False

            # 2. Service Initialization
            if not self._setup_services():
                return False

            # 3. System Validation
            if not self._validate_system():
                return False

            self.initialized = True
            logger.info("System erfolgreich initialisiert!")
            return True

        except Exception as e:
            logger.error("Kritischer Fehler bei System-Initialisierung: %s", e)
            return False

    def _setup_database(self) -> bool:
        """
        Initialisiert die Database.

        Returns:
            True wenn Database erfolgreich eingerichtet
        """
        try:
            logger.info("Initialisiere Database...")

            # Database Connection initialisieren
            initialize_database(str(settings.DATABASE_PATH))

            # Tabellen erstellen falls nicht vorhanden
            create_tables()

            # Connection testen
            if not test_connection():
                logger.error("Database Connection Test fehlgeschlagen")
                return False

            logger.info(
                "Database erfolgreich initialisiert: %s", settings.DATABASE_PATH
            )
            return True

        except Exception as e:
            logger.error("Database Setup fehlgeschlagen: %s", e)
            return False

    def _setup_services(self) -> bool:
        """
        Initialisiert alle Application Services.

        Returns:
            True wenn alle Services erfolgreich erstellt
        """
        try:
            logger.info("Initialisiere Application Services...")

            # Services in Dependency-Order initialisieren
            self.supplier_service = SupplierService()
            logger.info("SupplierService initialisiert")

            self.delivery_service = DeliveryService()
            logger.info("DeliveryService initialisiert")

            self.item_service = ItemService()
            logger.info("ItemService initialisiert")

            self.order_service = OrderService()
            logger.info("OrderService initialisiert")

            logger.info("Alle Application Services erfolgreich initialisiert")
            return True

        except Exception as e:
            logger.error("Service Setup fehlgeschlagen: %s", e)
            return False

    def _validate_system(self) -> bool:
        """
        Validiert das komplette System.

        Returns:
            True wenn System funktionsfähig
        """
        try:
            logger.info("Validiere System...")

            # Database Validation
            if not is_initialized():
                logger.error("Database nicht korrekt initialisiert")
                return False

            # Service Validation
            services = [
                ("SupplierService", self.supplier_service),
                ("DeliveryService", self.delivery_service),
                ("ItemService", self.item_service),
                ("OrderService", self.order_service),
            ]

            for service_name, service in services:
                if service is None:
                    logger.error("%s nicht initialisiert", service_name)
                    return False

            logger.info("System-Validation erfolgreich")
            return True

        except Exception as e:
            logger.error("System-Validation fehlgeschlagen: %s", e)
            return False

    def get_system_info(self) -> dict:
        """
        Gibt System-Informationen zurück.

        Returns:
            Dictionary mit System-Status
        """
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_path": str(settings.DATABASE_PATH),
            "initialized": self.initialized,
            "services_available": {
                "supplier_service": self.supplier_service is not None,
                "delivery_service": self.delivery_service is not None,
                "item_service": self.item_service is not None,
                "order_service": self.order_service is not None,
            },
        }

    def run_basic_operations(self):
        """
        Führt grundlegende System-Operationen aus.
        Demonstriert die Funktionalität aller Services.
        """
        if not self.initialized:
            logger.error(
                "System nicht initialisiert - kann keine Operationen ausführen"
            )
            return

        logger.info("=== Starte Basic Operations Demo ===")

        try:
            # 1. Supplier Operations
            self._demo_supplier_operations()

            # 2. Order Operations
            self._demo_order_operations()

            # 3. Delivery Operations
            self._demo_delivery_operations()

            # 4. Item Operations
            self._demo_item_operations()

            # 5. System Statistics
            self._show_system_statistics()

            logger.info("=== Basic Operations Demo abgeschlossen ===")

        except Exception as e:
            logger.error("Fehler bei Basic Operations: %s", e)

    def _demo_supplier_operations(self):
        """Demonstriert Supplier-Operationen."""
        logger.info("--- Supplier Operations ---")

        # Test Supplier erstellen
        try:
            supplier_id = "MAIN_TEST_001"
            if not self.supplier_service.supplier_exists(supplier_id):
                self.supplier_service.create_supplier(
                    supplier_id=supplier_id,
                    name="Main Test Supplier GmbH",
                    notes="Demo Supplier für System-Test",
                )
                logger.info("Test-Supplier erstellt: %s", supplier_id)
            else:
                logger.info("Test-Supplier bereits vorhanden: %s", supplier_id)

        except Exception as e:
            logger.warning("Supplier Demo-Operation fehlgeschlagen: %s", e)

    def _demo_order_operations(self):
        """Demonstriert Order-Operationen."""
        logger.info("--- Order Operations ---")

        try:
            order_number = "ORD-TEST-001"
            if not self.order_service.order_exists(order_number):
                self.order_service.create_order(
                    order_number=order_number,
                    supplier_id="MAIN_TEST_001",
                    order_date=date.today(),
                    employee_name="System Test",
                    expected_delivery_date=date.today(),
                )
                logger.info("Test-Order erstellt: %s", order_number)
            else:
                logger.info("Test-Order bereits vorhanden: %s", order_number)

        except Exception as e:
            logger.warning("Order Demo-Operation fehlgeschlagen: %s", e)

    def _demo_delivery_operations(self):
        """Demonstriert Delivery-Operationen."""
        logger.info("--- Delivery Operations ---")

        try:
            delivery_number = "DEL-TEST-001"
            if not self.delivery_service.delivery_exists(delivery_number):
                self.delivery_service.create_delivery(
                    delivery_number=delivery_number,
                    supplier_id="MAIN_TEST_001",
                    delivery_date=date.today(),
                    employee_name="System Test",
                )
                logger.info("Test-Delivery erstellt: %s", delivery_number)
            else:
                logger.info("Test-Delivery bereits vorhanden: %s", delivery_number)

        except Exception as e:
            logger.warning("Delivery Demo-Operation fehlgeschlagen: %s", e)

    def _demo_item_operations(self):
        """Demonstriert Item-Operationen."""
        logger.info("--- Item Operations ---")

        try:
            # Item zu Delivery hinzufügen
            article_number = "A0001"
            batch_number = "P-123456789012-1234"

            result = self.item_service.get_item(
                article_number, batch_number, "DEL-TEST-001"
            )
            if not result:
                self.delivery_service.add_item_to_delivery(
                    delivery_number="DEL-TEST-001",
                    article_number=article_number,
                    batch_number=batch_number,
                    quantity=1,
                    employee_name="System Test",
                )
                logger.info("Test-Item erstellt: %s/%s", article_number, batch_number)
            else:
                logger.info(
                    "Test-Item bereits vorhanden: %s/%s", article_number, batch_number
                )

        except Exception as e:
            logger.warning("Item Demo-Operation fehlgeschlagen: %s", e)

    def _show_system_statistics(self):
        """Zeigt System-Statistiken an."""
        logger.info("--- System Statistics ---")

        try:
            # Supplier Statistics
            supplier_stats = self.supplier_service.get_supplier_statistics()
            logger.info("Supplier Statistiken: %s", supplier_stats)

            # Delivery Statistics
            delivery_stats = self.delivery_service.get_delivery_statistics()
            logger.info("Delivery Statistiken: %s", delivery_stats)

            # Item Statistics
            item_stats = self.item_service.get_item_statistics()
            logger.info("Item Statistiken: %s", item_stats)

            # Order Statistics
            order_stats = self.order_service.get_order_statistics()
            logger.info("Order Statistiken: %s", order_stats)

        except Exception as e:
            logger.warning("Fehler beim Laden der Statistiken: %s", e)

    def shutdown(self):
        """Fährt das System ordnungsgemäß herunter."""
        logger.info("=== System Shutdown ===")

        # Services cleanup (falls erforderlich)
        self.supplier_service = None
        self.delivery_service = None
        self.item_service = None
        self.order_service = None

        self.initialized = False
        logger.info("System erfolgreich heruntergefahren")


def main(start_gui: bool = None):
    """
    Hauptfunktion - Entry Point der Anwendung.

    Args:
        start_gui: If True, starts GUI automatically. If False, skips GUI.
                   If None, prompts user for GUI startup.
    """
    global logger

    try:
        # 1. Logging Setup
        logger = setup_logging(
            log_level=settings.LOG_LEVEL, log_to_file=True, log_to_console=True
        )

        # 2. System Info logging
        log_system_info()

        # 3. Application Setup
        app = WarehouseApp()

        # 4. System Initialization
        if not app.initialize():
            logger.error("System-Initialisierung fehlgeschlagen - Beende Anwendung")
            sys.exit(1)

        # 5. System Info anzeigen
        system_info = app.get_system_info()
        logger.info("System Info: %s", system_info)

        # 6. Basic Operations ausführen
        app.run_basic_operations()

        # 7. Interactive Mode (falls gewünscht)
        print("\n" + "=" * 60)
        print(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        print("=" * 60)
        print("System erfolgreich initialisiert!")
        print("Alle Services verfuegbar:")
        print("  - SupplierService: OK")
        print("  - DeliveryService: OK")
        print("  - ItemService: OK")
        print("  - OrderService: OK")
        print(f"Database: {settings.DATABASE_PATH}")
        print("=" * 60)

        # 8. Launch GUI (optional)
        launch_gui = input("\nGUI starten? (y/n, default: y): ").strip().lower()
        if launch_gui in ("", "y", "yes", "j", "ja"):
            print("\n🚀 Starte GUI...")
            try:
                launch_streamlit_gui()
            except KeyboardInterrupt:
                print("\nGUI durch Benutzer beendet.")
            except Exception as e:
                logger.error(f"GUI startup failed: {e}")
                print(f"\n❌ GUI konnte nicht gestartet werden: {e}")

        # 9. Orderly Shutdown
        app.shutdown()

        print("System erfolgreich beendet.")
        return 0

    except KeyboardInterrupt:
        if logger:
            logger.info("Benutzer-Interrupt - Beende Anwendung")
        print("\nAnwendung durch Benutzer beendet.")
        return 0

    except Exception as e:
        if logger:
            logger.critical("Kritischer Fehler in Hauptanwendung: %s", e)
        else:
            print(f"Kritischer Fehler: {e}")
        return 1


def launch_streamlit_gui():
    """
    Startet die Streamlit GUI für das Admin Interface.

    Diese Funktion startet das Streamlit Admin Interface nach der
    System-Initialisierung. Das System ist bereits vollständig
    initialisiert, wenn diese Funktion aufgerufen wird.
    """
    import subprocess
    from pathlib import Path

    # Path to admin GUI
    admin_gui_path = (
        Path(__file__).parent
        / "warehouse"
        / "presentation"
        / "admin"
        / "main_admin_app.py"
    )

    if not admin_gui_path.exists():
        raise FileNotFoundError(f"Admin GUI nicht gefunden: {admin_gui_path}")

    logger.info("Starte Streamlit Admin GUI: %s", admin_gui_path)

    # Streamlit command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(admin_gui_path),
        "--server.port=8501",
        "--server.address=localhost",
        "--server.headless=false",
    ]

    print("🌐 GUI wird gestartet...")
    print(f"📍 URL: http://localhost:8501")
    print("⏹️  Zum Beenden: Strg+C drücken")
    print("-" * 50)

    # Launch Streamlit
    try:
        # Use subprocess.run for better process control
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        raise RuntimeError(
            "Streamlit nicht installiert. Installiere mit: pip install streamlit"
        )
    except Exception as e:
        logger.error("Streamlit GUI startup failed: %s", e)
        raise


def log_system_info():
    """
    Loggt wichtige System-Informationen.
    """
    import platform

    try:
        import psutil

        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False

    logger.info("=== System-Informationen ===")
    logger.info("Python Version: %s", sys.version)
    logger.info("Platform: %s", platform.platform())

    if PSUTIL_AVAILABLE:
        logger.info("RAM: %.1f GB verfügbar", psutil.virtual_memory().total / (1024**3))
        logger.info("CPU Cores: %d", psutil.cpu_count())
    else:
        logger.info("RAM/CPU Info: psutil nicht verfügbar")

    logger.info("Working Directory: %s", Path.cwd())
    logger.info("=============================")


if __name__ == "__main__":
    sys.exit(main())
