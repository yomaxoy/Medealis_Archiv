"""
Environment Configuration Service

Zentrale Konfiguration für verschiedene Deployment-Szenarien.
Unterstützt .env Dateien, Streamlit Secrets und System-Umgebungsvariablen.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """
    Zentrale Konfigurationsverwaltung für verschiedene Umgebungen.

    Priorität (höchste zuerst):
    1. System Umgebungsvariablen
    2. Streamlit Secrets
    3. .env Datei
    4. Default-Werte
    """

    def __init__(self):
        self._config_cache = {}
        self._load_config()

    def _load_config(self):
        """Lädt Konfiguration aus verschiedenen Quellen."""
        try:
            # 1. Versuche .env Datei zu laden
            self._load_env_file()

            # 2. Versuche Streamlit Secrets zu laden
            self._load_streamlit_secrets()

            # 3. System-Umgebungsvariablen haben höchste Priorität
            self._load_system_env()

            logger.info("Environment configuration loaded successfully")

        except Exception as e:
            logger.warning(f"Error loading environment config: {e}")

    def _load_env_file(self):
        """Lädt .env Datei falls vorhanden."""
        try:
            # Path: src/warehouse/shared/config/environment_config.py
            # Go up 5 levels to reach project root: config -> shared -> warehouse -> src -> root
            env_file = Path(__file__).parent.parent.parent.parent.parent / ".env"
            if env_file.exists():
                from dotenv import load_dotenv
                # Use override=True to ensure .env values are loaded even if env vars exist
                load_dotenv(env_file, override=True)
                logger.debug(f"Loaded .env file: {env_file}")
            else:
                logger.debug(f".env file not found at: {env_file}")
        except ImportError:
            logger.debug("python-dotenv not available, skipping .env file")
        except Exception as e:
            logger.debug(f"Could not load .env file: {e}")

    def _load_streamlit_secrets(self):
        """Lädt Streamlit Secrets falls verfügbar."""
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                # SharePoint Konfiguration
                if 'sharepoint' in st.secrets:
                    sp_config = st.secrets['sharepoint']
                    self._config_cache.update({
                        'SHAREPOINT_SITE_URL': sp_config.get('site_url', ''),
                        'SHAREPOINT_CLIENT_ID': sp_config.get('client_id', ''),
                        'SHAREPOINT_CLIENT_SECRET': sp_config.get('client_secret', ''),
                        'SHAREPOINT_TENANT_ID': sp_config.get('tenant_id', '')
                    })

                # Storage Konfiguration
                if 'storage' in st.secrets:
                    storage_config = st.secrets['storage']
                    self._config_cache.update({
                        'USE_SHAREPOINT': str(storage_config.get('use_sharepoint', 'false'))
                    })

                logger.debug("Loaded Streamlit secrets")
        except ImportError:
            logger.debug("Streamlit not available, skipping secrets")
        except Exception as e:
            logger.debug(f"Could not load Streamlit secrets: {e}")

    def _load_system_env(self):
        """Lädt System-Umgebungsvariablen."""
        env_vars = [
            'SHAREPOINT_SITE_URL',
            'SHAREPOINT_CLIENT_ID',
            'SHAREPOINT_CLIENT_SECRET',
            'SHAREPOINT_TENANT_ID',
            'USE_SHAREPOINT',
            'USE_SERVER_STORAGE',  # DEPRECATED: Legacy-Variable
            'USE_SERVER_STORAGE_DB',  # NEU: Getrennte DB-Storage
            'USE_SERVER_STORAGE_DOCUMENTS',  # NEU: Getrennte Dokument-Storage
            'ANTHROPIC_API_KEY',  # Claude API Key
            'AI_PROVIDER',  # AI Provider selection
            'DEBUG'
        ]

        for var in env_vars:
            value = os.getenv(var)
            if value:
                self._config_cache[var] = value
                logger.debug(f"Loaded {var} from environment")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt Konfigurationswert.

        Args:
            key: Konfigurationsschlüssel
            default: Default-Wert falls nicht gefunden

        Returns:
            Konfigurationswert oder Default
        """
        return self._config_cache.get(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Holt Boolean-Konfigurationswert.

        Args:
            key: Konfigurationsschlüssel
            default: Default-Wert

        Returns:
            Boolean-Wert
        """
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')

    def get_sharepoint_config(self) -> Dict[str, str]:
        """
        Holt vollständige SharePoint-Konfiguration.

        Returns:
            Dictionary mit SharePoint-Konfiguration
        """
        return {
            'site_url': self.get('SHAREPOINT_SITE_URL', ''),
            'client_id': self.get('SHAREPOINT_CLIENT_ID', ''),
            'client_secret': self.get('SHAREPOINT_CLIENT_SECRET', ''),
            'tenant_id': self.get('SHAREPOINT_TENANT_ID', '')
        }

    def is_sharepoint_enabled(self) -> bool:
        """Prüft ob SharePoint aktiviert ist."""
        return self.get_bool('USE_SHAREPOINT', False)

    def is_server_storage_db_enabled(self) -> bool:
        """
        Prüft ob Server-Storage für DB aktiviert ist.

        Returns:
            True wenn Server-Storage als primärer DB-Speicherort verwendet werden soll
        """
        # Neue Variable hat Priorität, Fallback auf alte Variable
        value = self.get('USE_SERVER_STORAGE_DB')
        if value is None:
            value = self.get('USE_SERVER_STORAGE', 'true')
        return str(value).lower() in ('true', '1', 'yes', 'on')

    def is_server_storage_documents_enabled(self) -> bool:
        """
        Prüft ob Server-Storage für Dokumente aktiviert ist.

        Returns:
            True wenn Server-Storage als primärer Dokument-Speicherort verwendet werden soll
        """
        # Neue Variable hat Priorität, Fallback auf alte Variable
        value = self.get('USE_SERVER_STORAGE_DOCUMENTS')
        if value is None:
            value = self.get('USE_SERVER_STORAGE', 'true')
        return str(value).lower() in ('true', '1', 'yes', 'on')

    def is_server_storage_enabled(self) -> bool:
        """
        DEPRECATED: Nutze is_server_storage_db_enabled() oder is_server_storage_documents_enabled()

        Prüft ob Server-Storage aktiviert ist (Legacy-Kompatibilität).

        Returns:
            True wenn Server-Storage als primärer Speicherort verwendet werden soll
        """
        return self.get_bool('USE_SERVER_STORAGE', True)  # Default: True (Server als Standard)

    def get_storage_mode(self) -> str:
        """
        DEPRECATED: Nutze get_db_storage_mode() oder get_documents_storage_mode()

        Bestimmt aktuellen Storage-Modus basierend auf Konfiguration (Legacy).

        Returns:
            "server" - Server primär, SharePoint fallback (Standard)
            "sharepoint" - SharePoint primär, lokal fallback (Legacy)
            "local" - Nur lokal (Entwicklung)
        """
        server_enabled = self.is_server_storage_enabled()
        sharepoint_enabled = self.is_sharepoint_enabled()

        if server_enabled:
            return "server"
        elif sharepoint_enabled:
            return "sharepoint"
        else:
            return "local"

    def get_db_storage_mode(self) -> str:
        """
        Bestimmt aktuellen Datenbank-Storage-Modus.

        Returns:
            "server" - Server/NAS primär
            "local" - Nur lokal
        """
        return "server" if self.is_server_storage_db_enabled() else "local"

    def get_documents_storage_mode(self) -> str:
        """
        Bestimmt aktuellen Dokumente-Storage-Modus.

        Returns:
            "server" - Server/NAS primär
            "sharepoint" - SharePoint primär (Legacy)
            "local" - Nur lokal
        """
        server_enabled = self.is_server_storage_documents_enabled()
        sharepoint_enabled = self.is_sharepoint_enabled()

        if server_enabled:
            return "server"
        elif sharepoint_enabled:
            return "sharepoint"
        else:
            return "local"

    def get_config_status(self) -> Dict[str, Any]:
        """
        Gibt Konfigurationsstatus zurück.

        Returns:
            Dictionary mit Konfigurationsstatus
        """
        sp_config = self.get_sharepoint_config()

        return {
            'storage_mode': self.get_storage_mode(),  # Legacy
            'db_storage_mode': self.get_db_storage_mode(),  # NEU
            'documents_storage_mode': self.get_documents_storage_mode(),  # NEU
            'server_storage_db_enabled': self.is_server_storage_db_enabled(),
            'server_storage_documents_enabled': self.is_server_storage_documents_enabled(),
            'server_storage_enabled': self.is_server_storage_enabled(),  # Legacy
            # Prüfe UNC-Pfad direkt (robuster als gemapptes Laufwerk)
            'server_available': os.path.exists(r"\\10.190.140.10\Allgemein"),
            'sharepoint_enabled': self.is_sharepoint_enabled(),
            'sharepoint_configured': all(sp_config.values()),
            'missing_sharepoint_config': [
                key for key, value in sp_config.items() if not value
            ],
            'config_sources_available': {
                'env_file': (Path(__file__).parent.parent.parent.parent.parent / ".env").exists(),
                'streamlit_secrets': self._has_streamlit_secrets(),
                'system_env': bool(os.getenv('SHAREPOINT_SITE_URL'))
            }
        }

    def _has_streamlit_secrets(self) -> bool:
        """Prüft ob Streamlit Secrets verfügbar sind."""
        try:
            import streamlit as st
            return hasattr(st, 'secrets') and ('sharepoint' in st.secrets or 'storage' in st.secrets)
        except:
            return False


# Global instance
env_config = EnvironmentConfig()