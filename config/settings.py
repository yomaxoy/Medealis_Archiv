"""
Grundkonfiguration für das Warehouse Management System.
Zentrale Stelle für alle Anwendungseinstellungen.
"""

import os
from pathlib import Path
from typing import Optional

# Load .env file FIRST to ensure environment variables are available
try:
    from dotenv import load_dotenv
    # .env is in project root, one level up from config/
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
except (ImportError, Exception):
    pass

# Basis-Pfade
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
CONFIG_DIR = BASE_DIR / "config"
RESOURCES_DIR = BASE_DIR / "resources"
DATA_DIR = BASE_DIR / "data"


class Settings:
    """Zentrale Konfigurationsklasse für die Anwendung."""

    # Anwendungsinfo
    APP_NAME = "Warehouse Management System"
    APP_VERSION = "2.0.0"
    APP_AUTHOR = "Medealis"

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Storage Configuration
    # UNC-Pfad statt Laufwerksbuchstabe (robuster für Sub-Prozesse)
    SERVER_BASE_PATH = Path(
        r"\\10.190.140.10\Allgemein"
        r"\Qualitätsmanagement\QM_MEDEALIS"
        r"\03. Produkte\Produktprüfung"
        r"\Medealis Archiv"
    )

    # Datenbank
    DATABASE_NAME = "warehouse_new.db"

    @classmethod
    def _get_use_server_storage(cls) -> bool:
        """Liest USE_SERVER_STORAGE dynamisch aus Umgebung (nicht beim Import!)."""
        return os.getenv("USE_SERVER_STORAGE", "true").lower() == "true"

    @classmethod
    def _get_database_path(cls) -> Path:
        r"""
        Ermittelt den Datenbank-Pfad basierend auf Verfügbarkeit.

        Primär: A:\Qualitätsmanagement\QM_MEDEALIS
            \03. Produkte\Produktprüfung
            \Medealis Archiv\database\
        Fallback: C:\Users\<Username>\.medealis\

        Returns:
            Path: Pfad zum Datenbankverzeichnis
        """
        if cls._get_use_server_storage():
            server_db_dir = cls.SERVER_BASE_PATH / "database"
            try:
                # Prüfe ob Server-Laufwerk verfügbar und beschreibbar
                if server_db_dir.parent.exists():
                    server_db_dir.mkdir(parents=True, exist_ok=True)
                    # Test Schreibrechte
                    test_file = server_db_dir / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    print(f"Datenbank-Speicherort: Server (UNC) - {server_db_dir}")
                    return server_db_dir
            except (OSError, PermissionError) as e:
                print(
                    "Server-Speicherung nicht verfügbar"
                    f" ({e}), verwende lokalen Fallback"
                )

        # Fallback: Lokaler Speicher
        local_db_dir = Path.home() / ".medealis"
        local_db_dir.mkdir(parents=True, exist_ok=True)
        print(f"Datenbank-Speicherort: Lokal - {local_db_dir}")
        return local_db_dir

    # Datenbank-Pfade werden dynamisch ermittelt
    DATABASE_DIR = None  # Wird über Property gesetzt
    DATABASE_PATH = None  # Wird über Property gesetzt

    # Verzeichnisse
    USER_DATA_DIR = Path.home() / "Medealis" / "Wareneingang"
    TEMPLATE_DIR = RESOURCES_DIR / "templates"
    LOG_DIR = DATA_DIR / "logs"
    TEMP_DIR = DATA_DIR / "temp"

    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # AI Service
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "claude")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # UI Einstellungen
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 600
    FONT_FAMILY = "Arial"
    FONT_SIZE = 10

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Manufacturer Mapping
    MANUFACTURER_MAPPING = {
        "A0": "Zubehörteile",
        "B0": "Bego",
        "C0": "Camlog",
        "D0": "Dentsply",
        "L0": "Lasak",
        "AS": "Dentsply",
        "CT": "C-Tech",
        "MG": "Megagen",
    }

    # Status-Konstanten
    ITEM_STATUS_NEW = "Artikel angelegt"
    ITEM_STATUS_CHECKED = "Daten geprüft"
    ITEM_STATUS_INSPECTED = "Sichtgeprüft"
    ITEM_STATUS_MEASURED = "Vermessen"
    ITEM_STATUS_COMPLETED = "Abgeschlossen"

    @classmethod
    def get_database_dir(cls) -> Path:
        """Gibt das Datenbankverzeichnis zurück (cached nach erstem Aufruf)."""
        if cls.DATABASE_DIR is None:
            cls.DATABASE_DIR = cls._get_database_path()
        return cls.DATABASE_DIR

    @classmethod
    def get_database_path(cls) -> Path:
        """Gibt den vollständigen Datenbank-Pfad zurück."""
        if cls.DATABASE_PATH is None:
            cls.DATABASE_PATH = cls.get_database_dir() / cls.DATABASE_NAME
        return cls.DATABASE_PATH

    @classmethod
    def ensure_directories(cls):
        """Stellt sicher, dass alle benötigten Verzeichnisse existieren."""
        # DATABASE_DIR wird dynamisch über get_database_dir() erstellt
        directories = [cls.USER_DATA_DIR, cls.LOG_DIR, cls.TEMP_DIR]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # Datenbank-Verzeichnis separat sicherstellen
        cls.get_database_dir()

    @classmethod
    def get_template_path(cls, template_name: str) -> Path:
        """Gibt den vollständigen Pfad zu einer Template-Datei zurück."""
        return cls.TEMPLATE_DIR / template_name

    @classmethod
    def is_development(cls) -> bool:
        """Prüft, ob die Anwendung im Development-Modus läuft."""
        return cls.ENVIRONMENT == "development"

    @classmethod
    def is_production(cls) -> bool:
        """Prüft, ob die Anwendung im Production-Modus läuft."""
        return cls.ENVIRONMENT == "production"


# Global verfügbare Instanz
settings = Settings()

# WICHTIG: ensure_directories() wird NICHT mehr beim Import aufgerufen!
# Stattdessen wird es in initialize_database() aufgerufen,
# wenn .env garantiert geladen ist
