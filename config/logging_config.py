"""
Logging-Konfiguration für das Warehouse Management System.
Zentrale Stelle für alle Logging-Einstellungen.
"""

import logging
import logging.handlers
import sys
from typing import Optional

from .settings import settings


class LoggerSetup:
    """Zentrale Klasse für Logging-Setup."""

    @staticmethod
    def setup_logging(
        log_level: Optional[str] = None,
        log_to_file: bool = True,
        log_to_console: bool = True,
    ) -> logging.Logger:
        """
        Konfiguriert das Logging-System.

        Args:
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Soll in Datei geloggt werden
            log_to_console: Soll in Konsole geloggt werden

        Returns:
            Konfigurierter Root-Logger
        """
        # Log-Level bestimmen
        if log_level is None:
            log_level = settings.LOG_LEVEL

        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Root-Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Entferne existierende Handler
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Formatter erstellen
        formatter = logging.Formatter(
            fmt=settings.LOG_FORMAT, datefmt=settings.LOG_DATE_FORMAT
        )

        # Console Handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File Handler
        if log_to_file:
            # Haupt-Logdatei
            file_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOG_DIR / "application.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # Error-spezifische Logdatei
            error_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOG_DIR / "error.log",
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)

        return root_logger

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Holt einen Logger für ein spezifisches Modul.

        Args:
            name: Name des Loggers (meist __name__)

        Returns:
            Konfigurierter Logger
        """
        return logging.getLogger(name)

    @staticmethod
    def log_system_info():
        """Loggt wichtige Systeminformationen beim Start."""
        sys_logger = logging.getLogger(__name__)

        sys_logger.info("=== %s v%s ===", settings.APP_NAME, settings.APP_VERSION)
        sys_logger.info("Environment: %s", settings.ENVIRONMENT)
        sys_logger.info("Debug Mode: %s", settings.DEBUG)
        sys_logger.info("Database Path: %s", settings.DATABASE_PATH)
        sys_logger.info("User Data Dir: %s", settings.USER_DATA_DIR)
        sys_logger.info("Log Directory: %s", settings.LOG_DIR)


# Convenience-Funktionen
def setup_logging(**kwargs) -> logging.Logger:
    """Wrapper für LoggerSetup.setup_logging()."""
    return LoggerSetup.setup_logging(**kwargs)


def get_logger(name: str) -> logging.Logger:
    """Wrapper für LoggerSetup.get_logger()."""
    return LoggerSetup.get_logger(name)


def log_system_info():
    """Wrapper für LoggerSetup.log_system_info()."""
    LoggerSetup.log_system_info()


# Standard-Logger für das Config-Modul
logger = get_logger(__name__)
