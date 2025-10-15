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
            env_file = Path(__file__).parent.parent.parent.parent / ".env"
            if env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(env_file)
                logger.debug(f"Loaded .env file: {env_file}")
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
            'USE_SERVER_STORAGE',  # NEU: Server-Storage aktivieren
            'DEBUG'
        ]

        for var in env_vars:
            value = os.getenv(var)
            if value:
                self._config_cache[var] = value

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

    def is_server_storage_enabled(self) -> bool:
        """
        Prüft ob Server-Storage aktiviert ist.

        Returns:
            True wenn Server-Storage als primärer Speicherort verwendet werden soll
        """
        return self.get_bool('USE_SERVER_STORAGE', True)  # Default: True (Server als Standard)

    def get_storage_mode(self) -> str:
        """
        Bestimmt aktuellen Storage-Modus basierend auf Konfiguration.

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

    def get_config_status(self) -> Dict[str, Any]:
        """
        Gibt Konfigurationsstatus zurück.

        Returns:
            Dictionary mit Konfigurationsstatus
        """
        sp_config = self.get_sharepoint_config()

        return {
            'storage_mode': self.get_storage_mode(),
            'server_storage_enabled': self.is_server_storage_enabled(),
            'server_available': Path("A:\\").exists(),
            'sharepoint_enabled': self.is_sharepoint_enabled(),
            'sharepoint_configured': all(sp_config.values()),
            'missing_sharepoint_config': [
                key for key, value in sp_config.items() if not value
            ],
            'config_sources_available': {
                'env_file': (Path(__file__).parent.parent.parent.parent / ".env").exists(),
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