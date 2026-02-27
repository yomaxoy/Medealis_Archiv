"""
Storage Availability Checker

Prüft Verfügbarkeit aller Speicher-Optionen und liefert detaillierte Informationen
für GUI-Warnungen bei Server-Ausfall.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

from .path_resolver import path_resolver
from .sharepoint_graph_client import sharepoint_graph_client
from ....shared.config.environment_config import env_config

logger = logging.getLogger(__name__)


@dataclass
class StorageOption:
    """Repräsentiert eine verfügbare Speicher-Option."""
    name: str
    type: str  # "server", "local", "sharepoint"
    available: bool
    path: str
    priority: int  # 1=primär, 2=fallback1, 3=fallback2
    status_message: str
    recommendation: str = ""


class StorageAvailabilityChecker:
    """
    Prüft Verfügbarkeit aller Speicher-Optionen.

    Liefert detaillierte Informationen für GUI-Warnungen wenn
    Server nicht verfügbar ist.
    """

    def __init__(self):
        self.logger = logger

    def check_all_storage_options(
        self,
        batch_number: str = None,
        delivery_number: str = None,
        article_number: str = None,
        supplier_name: str = None
    ) -> Dict[str, Any]:
        """
        Prüft alle verfügbaren Speicher-Optionen.

        Args:
            batch_number: Optional - für konkrete Pfad-Beispiele
            delivery_number: Optional
            article_number: Optional
            supplier_name: Optional

        Returns:
            Dictionary mit allen Speicher-Optionen und Status
        """
        options = []

        # 1. SERVER-STORAGE prüfen
        server_option = self._check_server_storage(
            batch_number, delivery_number, article_number, supplier_name
        )
        options.append(server_option)

        # 2. LOCAL-STORAGE prüfen
        local_option = self._check_local_storage(
            batch_number, delivery_number, article_number, supplier_name
        )
        options.append(local_option)

        # 3. SHAREPOINT prüfen
        sharepoint_option = self._check_sharepoint_storage()
        options.append(sharepoint_option)

        # Bestimme aktuelle Konfiguration
        storage_mode = env_config.get_storage_mode()
        server_enabled = env_config.is_server_storage_enabled()
        sharepoint_enabled = env_config.is_sharepoint_enabled()

        # Bestimme primäre Option basierend auf Verfügbarkeit
        primary_option = None
        fallback_options = []

        for option in options:
            if option.priority == 1 and option.available:
                primary_option = option
            elif option.available and option.priority > 1:
                fallback_options.append(option)

        # Sortiere Fallbacks nach Priorität
        fallback_options.sort(key=lambda x: x.priority)

        return {
            "storage_mode": storage_mode,
            "server_enabled": server_enabled,
            "sharepoint_enabled": sharepoint_enabled,
            "all_options": options,
            "primary_option": primary_option,
            "fallback_options": fallback_options,
            "has_available_storage": any(opt.available for opt in options),
            "server_unavailable_warning": server_enabled and not server_option.available
        }

    def _check_server_storage(
        self,
        batch_number: str = None,
        delivery_number: str = None,
        article_number: str = None,
        supplier_name: str = None
    ) -> StorageOption:
        """Prüft Server-Storage Verfügbarkeit."""
        server_enabled = env_config.is_server_storage_enabled()
        # Prüfe UNC-Pfad direkt (robuster als gemapptes Laufwerk)
        try:
            server_available = path_resolver.server_storage_path.exists()
        except (OSError, PermissionError) as e:
            self.logger.warning(f"Server-Storage nicht erreichbar: {e}")
            server_available = False

        # Basis-Pfad
        base_path = str(path_resolver.server_storage_path)

        # Beispiel-Pfad wenn Daten vorhanden
        example_path = base_path
        if batch_number and supplier_name:
            try:
                from .storage_context import storage_context
                context = storage_context.get_complete_storage_context(
                    batch_number=batch_number,
                    delivery_number=delivery_number or "",
                    article_number=article_number or "",
                    supplier_name=supplier_name or ""
                )
                path_result = path_resolver.resolve_server_storage_path(context, create_folders=False)
                if path_result.success:
                    example_path = str(path_result.path)
            except Exception as e:
                self.logger.debug(f"Could not resolve example path: {e}")

        # Status-Message
        if not server_enabled:
            status_message = "Server-Storage ist deaktiviert (USE_SERVER_STORAGE=false)"
            recommendation = "In .env aktivieren: USE_SERVER_STORAGE=true"
        elif not server_available:
            status_message = f"❌ Server nicht erreichbar! Pfad: {path_resolver.server_storage_path}"
            recommendation = "Netzwerkverbindung prüfen oder IT-Support kontaktieren"
        else:
            status_message = "✅ Server verfügbar und bereit"
            recommendation = "Primäre Speicher-Option"

        return StorageOption(
            name="Firmenserver (empfohlen)",
            type="server",
            available=server_enabled and server_available,
            path=example_path,
            priority=1,
            status_message=status_message,
            recommendation=recommendation
        )

    def _check_local_storage(
        self,
        batch_number: str = None,
        delivery_number: str = None,
        article_number: str = None,
        supplier_name: str = None
    ) -> StorageOption:
        """Prüft lokale Storage Verfügbarkeit."""
        # Lokale Storage ist immer verfügbar
        base_path = str(path_resolver.base_storage_path)

        # Beispiel-Pfad wenn Daten vorhanden
        example_path = base_path
        if batch_number and supplier_name:
            try:
                from .storage_context import storage_context
                context = storage_context.get_complete_storage_context(
                    batch_number=batch_number,
                    delivery_number=delivery_number or "",
                    article_number=article_number or "",
                    supplier_name=supplier_name or ""
                )
                path_result = path_resolver.resolve_storage_path(context, create_folders=False)
                if path_result.success:
                    example_path = str(path_result.path)
            except Exception as e:
                self.logger.debug(f"Could not resolve example path: {e}")

        # Prüfe ob Ordner schreibbar ist
        try:
            test_path = Path(base_path)
            test_path.mkdir(parents=True, exist_ok=True)
            writable = True
            status_message = "✅ Lokale Festplatte verfügbar"
        except Exception as e:
            writable = False
            status_message = f"❌ Keine Schreibrechte: {str(e)}"

        server_enabled = env_config.is_server_storage_enabled()
        if server_enabled:
            recommendation = "Fallback-Option (wenn Server nicht verfügbar)"
        else:
            recommendation = "Primäre Speicher-Option"

        return StorageOption(
            name="Lokale Festplatte",
            type="local",
            available=writable,
            path=example_path,
            priority=2 if server_enabled else 1,
            status_message=status_message,
            recommendation=recommendation
        )

    def _check_sharepoint_storage(self) -> StorageOption:
        """Prüft SharePoint Verfügbarkeit."""
        sharepoint_enabled = env_config.is_sharepoint_enabled()
        sharepoint_available = sharepoint_graph_client.is_available()

        # Status-Message
        if not sharepoint_enabled:
            status_message = "SharePoint ist deaktiviert (USE_SHAREPOINT=false)"
            recommendation = "Optional: In .env aktivieren für Cloud-Backup"
            available = False
        elif not sharepoint_available:
            status_message = "❌ SharePoint nicht konfiguriert (Credentials fehlen)"
            recommendation = "SharePoint-Credentials in .env hinzufügen"
            available = False
        else:
            # Versuche Verbindung zu testen
            try:
                test_result = sharepoint_graph_client.test_connection()
                if test_result.get("success"):
                    status_message = f"✅ SharePoint verbunden: {test_result.get('site_title', 'N/A')}"
                    recommendation = "Cloud-Backup Option"
                    available = True
                else:
                    status_message = f"❌ SharePoint-Verbindung fehlgeschlagen: {test_result.get('error', 'Unknown')}"
                    recommendation = "SharePoint-Konfiguration prüfen"
                    available = False
            except Exception as e:
                status_message = f"❌ SharePoint-Fehler: {str(e)}"
                recommendation = "SharePoint-Konfiguration prüfen"
                available = False

        path = "Cloud: SharePoint Online"

        server_enabled = env_config.is_server_storage_enabled()
        priority = 3 if server_enabled else 2

        return StorageOption(
            name="SharePoint Cloud",
            type="sharepoint",
            available=available,
            path=path,
            priority=priority,
            status_message=status_message,
            recommendation=recommendation
        )

    def get_server_unavailable_warning(
        self,
        batch_number: str = None,
        delivery_number: str = None,
        article_number: str = None,
        supplier_name: str = None
    ) -> Dict[str, Any]:
        """
        Erstellt detaillierte Warnung für GUI wenn Server nicht verfügbar.

        Returns:
            Dictionary mit Warnung und Alternativen für GUI
        """
        status = self.check_all_storage_options(
            batch_number, delivery_number, article_number, supplier_name
        )

        if not status["server_unavailable_warning"]:
            return None  # Keine Warnung nötig

        # Erstelle GUI-Warnung
        warning = {
            "title": "⚠️ Server-Speicherung nicht verfügbar",
            "message": (
                f"Der Firmenserver ({path_resolver.server_storage_path}) ist nicht erreichbar.\n"
                "Das System wird automatisch auf eine Fallback-Option ausweichen."
            ),
            "severity": "warning",
            "options": status["all_options"],
            "primary_unavailable": not status["primary_option"],
            "fallback_available": len(status["fallback_options"]) > 0,
            "recommended_action": self._get_recommended_action(status)
        }

        return warning

    def _get_recommended_action(self, status: Dict[str, Any]) -> str:
        """Bestimmt empfohlene Aktion basierend auf Status."""
        if status["fallback_options"]:
            primary_fallback = status["fallback_options"][0]
            return (
                f"Dokumente werden auf '{primary_fallback.name}' gespeichert.\n\n"
                f"📁 Speicherort: {primary_fallback.path}\n\n"
                f"💡 Empfehlung: {primary_fallback.recommendation}"
            )
        else:
            return (
                "❌ KEINE SPEICHER-OPTION VERFÜGBAR!\n\n"
                "Bitte kontaktieren Sie sofort den IT-Administrator."
            )


# Global instance
storage_availability_checker = StorageAvailabilityChecker()
