"""
Grundkonfiguration für das Warehouse Management System.
Zentrale Stelle für alle Anwendungseinstellungen.
"""

import os
from pathlib import Path
from typing import Optional

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

    # Datenbank
    DATABASE_NAME = "archiv.db"
    DATABASE_DIR = Path.home() / ".medealis"
    DATABASE_PATH = DATABASE_DIR / DATABASE_NAME

    # Verzeichnisse
    USER_DATA_DIR = Path.home() / "Medealis" / "Wareneingang"
    TEMPLATE_DIR = RESOURCES_DIR / "templates"
    LOG_DIR = DATA_DIR / "logs"
    TEMP_DIR = DATA_DIR / "temp"

    # API Keys
    OPENAI_API_KEY: Optional[str] = None

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
        "A0": "Zubehör",
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
    def ensure_directories(cls):
        """Stellt sicher, dass alle benötigten Verzeichnisse existieren."""
        directories = [cls.DATABASE_DIR, cls.USER_DATA_DIR, cls.LOG_DIR, cls.TEMP_DIR]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

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

# Verzeichnisse beim Import erstellen
settings.ensure_directories()
