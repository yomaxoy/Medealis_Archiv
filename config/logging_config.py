"""
Logging-Konfiguration für das Warehouse Management System.
Zentrale Stelle für alle Logging-Einstellungen.

Features:
- User-Context aus Streamlit Session State
- File Rotation (10MB application.log, 5MB error.log)
- Streamlit-safe (idempotent, delay=True)
"""

import logging
import logging.handlers
import sys
from typing import Optional

# Import settings - funktioniert mit absolutem und relativem Import
try:
    from .settings import settings  # Relative import (wenn als Package importiert)
except ImportError:
    from settings import settings  # Absolute import (wenn config/ im Path)


# Globaler Flag für Idempotenz (Streamlit-safe)
_LOGGING_INITIALIZED = False


class UserContextFilter(logging.Filter):
    """
    Fügt Benutzer-Info aus Streamlit Session State zu jedem Log hinzu.

    Format: %(user)s wird ersetzt durch Username oder "System"
    """

    def filter(self, record):
        """
        Erweitert LogRecord um User-Attribut.

        Args:
            record: logging.LogRecord

        Returns:
            True (Log wird durchgelassen)
        """
        try:
            # Versuche User aus Streamlit Session State zu holen
            import streamlit as st

            if hasattr(st, 'session_state') and 'current_user' in st.session_state:
                user = st.session_state.current_user

                # current_user kann dict oder string sein
                if isinstance(user, dict):
                    record.user = user.get('username', 'System')
                elif isinstance(user, str):
                    record.user = user
                else:
                    record.user = str(user) if user else "System"
            else:
                record.user = "System"

        except (ImportError, RuntimeError, Exception):
            # Außerhalb Streamlit-Context oder andere Fehler
            record.user = "System"

        return True


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

        IDEMPOTENT: Kann mehrfach aufgerufen werden ohne Probleme (Streamlit-safe).

        Args:
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Soll in Datei geloggt werden
            log_to_console: Soll in Konsole geloggt werden

        Returns:
            Konfigurierter Root-Logger
        """
        global _LOGGING_INITIALIZED

        # Idempotenz-Check: Wenn bereits initialisiert, gib existierenden Logger zurück
        if _LOGGING_INITIALIZED:
            return logging.getLogger()

        # Log-Level bestimmen
        if log_level is None:
            log_level = settings.LOG_LEVEL

        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Root-Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Entferne existierende Handler (nur beim ersten Aufruf)
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # User-Context-Filter erstellen
        user_filter = UserContextFilter()

        # Formatter mit User-Info erstellen
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(user)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(user_filter)
            root_logger.addHandler(console_handler)

        # File Handler
        if log_to_file:
            # Stelle sicher dass LOG_DIR existiert
            settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

            # Haupt-Logdatei
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=settings.LOG_DIR / "application.log",
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding="utf-8",
                    delay=True  # Öffne Datei erst beim ersten Log (Streamlit-safe)
                )
                file_handler.setLevel(numeric_level)
                file_handler.setFormatter(formatter)
                file_handler.addFilter(user_filter)
                root_logger.addHandler(file_handler)
            except (PermissionError, OSError) as e:
                # Fehler beim File-Handler nicht kritisch (z.B. Read-Only-Filesystem)
                sys.stderr.write(f"WARNING: Could not setup application.log: {e}\n")

            # Error-spezifische Logdatei
            try:
                error_handler = logging.handlers.RotatingFileHandler(
                    filename=settings.LOG_DIR / "error.log",
                    maxBytes=5 * 1024 * 1024,  # 5MB
                    backupCount=3,
                    encoding="utf-8",
                    delay=True  # Öffne Datei erst beim ersten Log (Streamlit-safe)
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(formatter)
                error_handler.addFilter(user_filter)
                root_logger.addHandler(error_handler)
            except (PermissionError, OSError) as e:
                # Fehler beim File-Handler nicht kritisch
                sys.stderr.write(f"WARNING: Could not setup error.log: {e}\n")

        # Markiere als initialisiert
        _LOGGING_INITIALIZED = True

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
