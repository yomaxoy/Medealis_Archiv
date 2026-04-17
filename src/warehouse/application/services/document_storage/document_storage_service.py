"""
Document Storage Service - Zentraler Service für Dokument-Speicherung

Vereinheitlicht die Speicher-Logik die vorher in verschiedenen Services verstreut war.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass

from .storage_context import StorageContextData, storage_context
from .path_resolver import path_resolver
from .storage_validator import (
    StorageValidator,
    ValidationResult,
    ValidationLevel,
)
from .sharepoint_graph_client import sharepoint_graph_client

# Import Document Types
from ..document_generation.document_types import DocumentType

# Import Caching
from ....shared.caching import ttl_cache

# Import Environment Config
from ....shared.config.environment_config import env_config

logger = logging.getLogger(__name__)


@dataclass
class StorageResult:
    """
    Ergebnis einer Storage-Operation.
    Standardisierte Rückgabe für alle Storage-Methoden.
    """

    success: bool
    file_path: Optional[str] = None
    filename: Optional[str] = None
    storage_folder: Optional[str] = None
    document_type: Optional[str] = None
    error: Optional[str] = None
    warnings: list = None
    metadata: Dict[str, Any] = None
    sharepoint_url: Optional[str] = None  # NEU: SharePoint URL falls hochgeladen

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DocumentOperationResult:
    """
    Aggregiert-Ergebnis für Multi-Dokument-Operationen.

    Sammelt alle StorageResults einer Operation (z.B. PDF + Barcode + Lieferschein).
    Basis für das Document Confirmation Popup.

    Attributes:
        auto_open: Wenn True, werden Dokumente automatisch geöffnet nach User-Bestätigung
        trusted: Wenn True, können Dokumente ohne User-Oversight erstellt werden (Zukunft)

    Usage:
        result = DocumentOperationResult(auto_open=True)
        result.add_document(storage_result1)
        result.add_document(storage_result2)

        if result.has_documents():
            show_document_confirmation_popup(result)
    """

    documents: List[StorageResult] = None
    errors: List[str] = None
    warnings: List[str] = None
    operation_type: Optional[str] = None  # z.B. "Wareneingang", "Prüfung"
    timestamp: datetime = None
    auto_open: bool = True  # Auto-open Dokumente nach Bestätigung
    trusted: bool = False   # Für Zukunft: Bypass confirmation wenn trusted

    def __post_init__(self):
        if self.documents is None:
            self.documents = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def add_document(self, storage_result: StorageResult) -> None:
        """Fügt ein StorageResult hinzu."""
        self.documents.append(storage_result)

        # Sammle Warnungen/Fehler
        if storage_result.warnings:
            self.warnings.extend(storage_result.warnings)
        if storage_result.error:
            self.errors.append(storage_result.error)

    def add_error(self, error: str) -> None:
        """Fügt einen Operation-Level Fehler hinzu."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Fügt eine Operation-Level Warnung hinzu."""
        self.warnings.append(warning)

    @property
    def success(self) -> bool:
        """Operation erfolgreich wenn mind. 1 Dokument und keine Fehler."""
        return len(self.documents) > 0 and len(self.errors) == 0

    @property
    def partial_success(self) -> bool:
        """Partial Success: Mind. 1 Dokument, aber auch Fehler."""
        return len(self.documents) > 0 and len(self.errors) > 0

    def has_documents(self) -> bool:
        """True wenn mind. 1 Dokument erfolgreich erstellt wurde."""
        return len(self.documents) > 0

    def get_documents_by_location(self) -> Dict[str, List[StorageResult]]:
        """
        Gruppiert Dokumente nach Speicherort.

        Returns:
            Dict mit Keys: 'server', 'local', 'sharepoint'
        """
        grouped = {
            'server': [],
            'local': [],
            'sharepoint': []
        }

        for doc in self.documents:
            if doc.sharepoint_url:
                grouped['sharepoint'].append(doc)
            elif doc.storage_folder and '\\\\medealis-server\\' in doc.storage_folder:
                grouped['server'].append(doc)
            else:
                grouped['local'].append(doc)

        return grouped


class DocumentStorageService:
    """
    ZENTRALER Service für alle Dokument-Speicher-Operationen.

    Nutzt die neuen Storage-Komponenten:
    - StorageContext: Einheitliche Datenkontext-Beschaffung
    - PathResolver: Einzige Pfad-Auflösung im System
    - StorageValidator: Sicherheit und Validierung

    ERSETZT verstreute Speicher-Logik in verschiedenen Services.
    """

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.logger = logger

        # Neue Storage-Komponenten
        self.storage_context = storage_context
        self.path_resolver = path_resolver
        self.storage_validator = StorageValidator(validation_level)

        # SharePoint Client
        self.sharepoint_client = sharepoint_graph_client

        # Storage-Konfiguration (NEU: Server als Standard)
        self.use_server_storage = env_config.is_server_storage_enabled()
        self.use_sharepoint = env_config.is_sharepoint_enabled()
        self.storage_mode = env_config.get_storage_mode()

        self.logger.info(
            "DocumentStorageService initialized "
            "with validation level: "
            f"{validation_level.value}"
        )
        self.logger.info(f"Storage mode: {self.storage_mode}")
        server_status = "enabled" if self.use_server_storage else "disabled"
        self.logger.info(f"Server storage: {server_status}")
        sp_status = "enabled (fallback)" if self.use_sharepoint else "disabled"
        self.logger.info(f"SharePoint storage: {sp_status}")

    def save_document(
        self,
        document_data: bytes,
        document_name: str,
        document_type: str,
        batch_number: str,
        delivery_number: str = "",
        article_number: str = "",
        supplier_name: str = "",
        create_folders: bool = True,
        **additional_context,
    ) -> StorageResult:
        """
        ZENTRALE API für Dokument-Speicherung.
        Nutzt alle neuen Storage-Komponenten für maximale Konsistenz und Sicherheit.

        Args:
            document_data: Binärdaten des Dokuments
            document_name: Name der Datei
            document_type: Typ des Dokuments ("begleitdokument", "label", "PDB", etc.)
            batch_number: Chargennummer (Pflichtfeld)
            delivery_number: Lieferscheinnummer (optional)
            article_number: Artikelnummer (optional, überschreibt DB-Daten)
            supplier_name: Lieferantenname (optional, überschreibt DB-Daten)
            **additional_context: Zusätzliche Kontext-Daten

        Returns:
            StorageResult mit detaillierten Informationen
        """
        try:
            self.logger.info(
                f"Saving document: {document_name} (type: {document_type})"
            )

            # 1. STORAGE CONTEXT - Hole vollständigen Datenkontext
            context = self.storage_context.get_complete_storage_context(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=supplier_name,
                **additional_context,
            )

            # 2. CONTEXT VALIDATION - Validiere Kontext
            context_validation = self.storage_validator.validate_storage_context(
                context
            )
            if not context_validation.is_valid:
                return StorageResult(
                    success=False,
                    error=(
                        "Invalid storage context: "
                        f"{'; '.join(context_validation.errors)}"
                    ),
                    warnings=context_validation.warnings,
                )

            # 3. DOCUMENT VALIDATION - Validiere Dokument-Daten
            doc_validation = self.storage_validator.validate_document_data(
                document_data, document_name
            )
            if not doc_validation.is_valid:
                errs = "; ".join(doc_validation.errors)
                return StorageResult(
                    success=False,
                    error=("Document validation failed: " f"{errs}"),
                    warnings=doc_validation.warnings,
                )

            # 4. FILENAME SANITIZATION
            safe_filename, sanitize_warnings = self.storage_validator.sanitize_filename(
                document_name
            )

            # 5. PATH RESOLUTION - Löse Storage-Pfad auf (SERVER oder LOKAL)
            # NEU: Server-Storage als primär, lokal als Fallback
            server_unavailable_info = None  # Für GUI-Warnung

            # Prüfe Server-Verfügbarkeit direkt über
            # UNC-Pfad (robuster als Laufwerksbuchstabe)
            server_available = self.path_resolver.server_storage_path.exists()

            self.logger.info("DEBUG: Server storage check:")
            self.logger.info("  - use_server_storage: " f"{self.use_server_storage}")
            self.logger.info(
                "  - Server path: " f"{self.path_resolver.server_storage_path}"
            )
            self.logger.info(f"  - Server available: {server_available}")

            if self.use_server_storage and server_available:
                # SERVER-Speicherung (PRIMÄR)
                path_result = self.path_resolver.resolve_server_storage_path(
                    context,
                    create_folders=create_folders,
                )
                storage_location = "server"
                sp = path_result.path if path_result.success else "N/A"
                self.logger.info("Using SERVER storage (primary): " f"{sp}")
            else:
                # LOKALE Speicherung (Fallback wenn Server nicht verfügbar)
                path_result = self.path_resolver.resolve_storage_path(
                    context, create_folders=create_folders
                )
                storage_location = "local"

                if self.use_server_storage:
                    # Server sollte verwendet werden,
                    # ist aber nicht verfügbar
                    srv = self.path_resolver.server_storage_path
                    self.logger.warning(
                        "Server storage enabled but "
                        f"not available ({srv}), "
                        "using local fallback"
                    )

                    # Sammle Informationen für GUI-Warnung
                    local_p = str(path_result.path) if path_result.success else "N/A"
                    server_unavailable_info = {
                        "intended_storage": "server",
                        "actual_storage": "local",
                        "server_path": str(srv),
                        "local_path": local_p,
                        "reason": ("Server-Speicherpfad nicht " f"erreichbar: {srv}"),
                    }
                else:
                    self.logger.info("Using LOCAL storage " "(server disabled)")

            if not path_result.success:
                return StorageResult(
                    success=False,
                    error=f"Path resolution failed: {path_result.error}",
                    warnings=path_result.warnings,
                )

            # 6. PERMISSION CHECK - Prüfe Schreibberechtigungen
            perm_validation = self.storage_validator.validate_storage_permissions(
                path_result.path
            )
            if not perm_validation.is_valid:
                return StorageResult(
                    success=False,
                    error=f"Permission denied: {'; '.join(perm_validation.errors)}",
                    warnings=perm_validation.warnings,
                )

            # 7. PRIMARY STORAGE - Speichere auf Server/Lokal (PRIMÄR)
            final_file_path = path_result.path / safe_filename
            primary_save_success = False

            try:
                with open(final_file_path, "wb") as f:
                    f.write(document_data)
                primary_save_success = True
                self.logger.info(
                    f"Document saved to {storage_location}: {final_file_path}"
                )
            except Exception as e:
                error_msg = f"Failed to save document to {storage_location}: {str(e)}"
                self.logger.error(error_msg)
                # Speicher-Fehler ist kritisch, wenn kein SharePoint-Fallback verfügbar
                if not self.use_sharepoint:
                    return StorageResult(success=False, error=error_msg)

            # 8. SHAREPOINT UPLOAD (FALLBACK wenn primäre Speicherung fehlschlägt)
            sharepoint_url = None
            sharepoint_warnings = []
            sharepoint_upload_attempted = False

            # SharePoint als Fallback wenn:
            # - SharePoint aktiviert ist UND
            # - Primäre Speicherung fehlgeschlagen ist
            if (
                self.use_sharepoint
                and self.sharepoint_client.is_available()
                and not primary_save_success
            ):
                try:
                    sharepoint_upload_attempted = True
                    self.logger.warning(
                        "Primary storage failed, " "attempting SharePoint fallback..."
                    )

                    # Verwende PathResolver für SharePoint-Pfad-Auflösung
                    sharepoint_path = self.path_resolver.resolve_sharepoint_path(
                        document_type=document_type, context=context
                    )

                    self.logger.info(
                        "Uploading to SharePoint "
                        "(fallback): "
                        f"{sharepoint_path}/"
                        f"{safe_filename}"
                    )

                    upload_result = self.sharepoint_client.upload_document(
                        document_data=document_data,
                        sharepoint_path=sharepoint_path,
                        filename=safe_filename,
                        overwrite=True,
                    )

                    if upload_result.success:
                        sharepoint_url = upload_result.file_url
                        self.logger.info(
                            f"SharePoint fallback successful: {sharepoint_url}"
                        )
                    else:
                        error_msg = (
                            "SharePoint fallback " "failed: " f"{upload_result.error}"
                        )
                        sharepoint_warnings.append(error_msg)
                        self.logger.error(error_msg)

                except Exception as e:
                    error_msg = f"SharePoint fallback error: {str(e)}"
                    sharepoint_warnings.append(error_msg)
                    self.logger.error(error_msg)

            # Prüfe ob überhaupt eine Speicherung erfolgreich war
            if not primary_save_success and not sharepoint_url:
                return StorageResult(
                    success=False,
                    error="All storage methods failed (server/local + SharePoint)",
                    warnings=sharepoint_warnings,
                )

            # 9. RESULT - Erstelle Erfolgs-Result
            result = StorageResult(
                success=True,
                file_path=str(final_file_path) if primary_save_success else None,
                filename=safe_filename,
                storage_folder=str(path_result.path) if primary_save_success else None,
                document_type=document_type,
                sharepoint_url=sharepoint_url,
            )

            # Sammle alle Warnungen
            result.warnings.extend(context_validation.warnings)
            result.warnings.extend(doc_validation.warnings)
            result.warnings.extend(sanitize_warnings)
            result.warnings.extend(path_result.warnings)
            result.warnings.extend(perm_validation.warnings)
            result.warnings.extend(sharepoint_warnings)

            # Metadaten hinzufügen
            result.metadata.update(
                {
                    "context_completeness": context.completeness_score,
                    "context_source": context.context_source,
                    "file_size": len(document_data),
                    "validation_level": self.storage_validator.validation_level.value,
                    "path_created": path_result.created,
                    "filename_sanitized": safe_filename != document_name,
                    "server_storage_enabled": self.use_server_storage,
                    "sharepoint_enabled": self.use_sharepoint,
                    "primary_storage_location": storage_location,
                    "primary_save_success": primary_save_success,
                    "sharepoint_uploaded": sharepoint_url is not None,
                    "sharepoint_was_fallback": sharepoint_upload_attempted,
                    "storage_mode": self.storage_mode,
                    "final_storage": "server"
                    if (storage_location == "server" and primary_save_success)
                    else "local"
                    if (storage_location == "local" and primary_save_success)
                    else "sharepoint_fallback"
                    if sharepoint_url
                    else "unknown",
                    # NEU: Für GUI-Warnung
                    "server_unavailable_info": (server_unavailable_info),
                }
            )

            # Log final status
            if primary_save_success and not sharepoint_url:
                self.logger.info(
                    "Document saved to "
                    f"{storage_location.upper()}: "
                    f"{final_file_path}"
                )
            elif primary_save_success and sharepoint_url:
                self.logger.info(
                    "Document saved to "
                    f"{storage_location.upper()} + "
                    "SharePoint backup: "
                    f"{final_file_path}"
                )
            elif sharepoint_url:
                self.logger.warning(
                    "Primary storage failed, "
                    "document saved to SharePoint "
                    f"fallback: {sharepoint_url}"
                )

            return result

        except Exception as e:
            error_msg = f"Failed to save document {document_name}: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(success=False, error=error_msg)

    @ttl_cache(seconds=900, maxsize=256, key_prefix="doc_path")
    def get_document_path(
        self,
        batch_number: str,
        delivery_number: str = "",
        article_number: str = "",
        supplier_name: str = "",
        create_folders: bool = False,
    ) -> Tuple[Path, List[str]]:
        """
        ZENTRALE API für Pfad-Auflösung.
        Nutzt neue Storage-Komponenten für konsistente Pfad-Erstellung.

        WICHTIG: Verwendet Server-Storage als primär, lokalen Pfad als Fallback!

        Args:
            batch_number: Chargennummer (Pflichtfeld)
            delivery_number: Lieferscheinnummer (optional)
            article_number: Artikelnummer (optional)
            supplier_name: Lieferantenname (optional)
            create_folders: Ob Ordnerstruktur erstellt werden soll

        Returns:
            Tuple von (Pfad, Warnungen)
        """
        try:
            # Hole Storage-Kontext
            context = self.storage_context.get_complete_storage_context(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=supplier_name,
            )

            # Löse Pfad auf - PRIMÄR Server, FALLBACK Lokal
            # Prüfe Server-Verfügbarkeit direkt über UNC-Pfad
            if (
                self.use_server_storage
                and self.path_resolver.server_storage_path.exists()
            ):
                # SERVER-Pfad verwenden (PRIMÄR)
                path_result = self.path_resolver.resolve_server_storage_path(
                    context, create_folders=create_folders
                )
                self.logger.debug(
                    f"get_document_path: Using SERVER path: {path_result.path}"
                )
            else:
                # LOKALER Pfad als Fallback
                path_result = self.path_resolver.resolve_storage_path(
                    context, create_folders=create_folders
                )

                if self.use_server_storage:
                    # Server sollte verwendet werden, ist aber nicht verfügbar
                    self.logger.warning(
                        "get_document_path: Server "
                        "not available, using "
                        "local fallback"
                    )
                    path_result.add_warning(
                        "Server-Speicherung nicht "
                        "verfügbar - verwende "
                        "lokalen Fallback"
                    )
                else:
                    self.logger.debug(
                        f"get_document_path: Using LOCAL path: {path_result.path}"
                    )

            if not path_result.success:
                self.logger.warning(
                    "Path resolution failed for "
                    f"batch {batch_number}: "
                    f"{path_result.error}"
                )
                return Path("."), [path_result.error or "Unknown path resolution error"]

            return path_result.path, path_result.warnings

        except Exception as e:
            error_msg = f"Error getting document path: {e}"
            self.logger.error(error_msg)
            return Path("."), [error_msg]

    def move_temp_document(
        self,
        temp_file_path: str,
        filename: str,
        batch_number: str,
        delivery_number: str = "",
        article_number: str = "",
        supplier_name: str = "",
    ) -> StorageResult:
        """
        Verschiebt temporäres Dokument zum finalen Storage-Pfad.
        Nutzt neue Storage-Komponenten für konsistente Pfad-Auflösung.

        Args:
            temp_file_path: Pfad zur temporären Datei
            filename: Dateiname im Zielpfad
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer (optional)
            article_number: Artikelnummer (optional)
            supplier_name: Lieferantenname (optional)

        Returns:
            StorageResult mit finalem Pfad
        """
        try:
            # Hole Storage-Kontext
            context = self.storage_context.get_complete_storage_context(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=supplier_name,
            )

            # Verschiebe Datei
            source_path = Path(temp_file_path)
            path_result = self.path_resolver.move_file(source_path, context, filename)

            if not path_result.success:
                return StorageResult(
                    success=False,
                    error=f"Failed to move temp document: {path_result.error}",
                )

            return StorageResult(
                success=True,
                file_path=str(path_result.path),
                filename=path_result.path.name,
                storage_folder=str(path_result.path.parent),
                warnings=path_result.warnings,
            )

        except Exception as e:
            error_msg = f"Error moving temp document: {e}"
            self.logger.error(error_msg)
            return StorageResult(success=False, error=error_msg)

    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Räumt temporäre Dateien auf.
        Delegiert an PathResolver für konsistente Temp-Pfad-Verwaltung.

        Args:
            max_age_hours: Maximales Alter in Stunden

        Returns:
            Cleanup-Statistiken
        """
        try:
            return self.path_resolver.cleanup_temp_files(max_age_hours)
        except Exception as e:
            error_msg = f"Temp cleanup failed: {e}"
            self.logger.error(error_msg)
            return {"cleaned_files": 0, "errors": [error_msg]}

    @ttl_cache(seconds=600, maxsize=128, key_prefix="doc_validation")
    def validate_document_before_storage(
        self, document_data: bytes, filename: str, context: StorageContextData
    ) -> ValidationResult:
        """
        VALIDATION API für externe Services.
        Führt vollständige Validierung vor Storage durch.

        Args:
            document_data: Dokument-Daten
            filename: Dateiname
            context: Storage-Kontext

        Returns:
            ValidationResult mit allen Prüfungsergebnissen
        """
        try:
            # Kombiniere alle Validierungen
            doc_validation = self.storage_validator.validate_document_data(
                document_data, filename
            )
            context_validation = self.storage_validator.validate_storage_context(
                context
            )

            # Erstelle kombiniertes Ergebnis
            combined_result = ValidationResult(
                is_valid=doc_validation.is_valid and context_validation.is_valid
            )
            combined_result.errors.extend(doc_validation.errors)
            combined_result.errors.extend(context_validation.errors)
            combined_result.warnings.extend(doc_validation.warnings)
            combined_result.warnings.extend(context_validation.warnings)
            combined_result.security_risks.extend(doc_validation.security_risks)
            combined_result.security_risks.extend(context_validation.security_risks)

            # Metadaten kombinieren
            combined_result.metadata.update(doc_validation.metadata)
            combined_result.metadata.update(context_validation.metadata)

            return combined_result

        except Exception as e:
            error_result = ValidationResult(is_valid=False)
            error_result.add_error(f"Validation failed: {str(e)}")
            return error_result

    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Gibt Storage-Statistiken zurück.
        Nützlich für Monitoring und Debugging.

        Returns:
            Dictionary mit Statistiken
        """
        try:
            base_path = self.path_resolver.base_storage_path
            temp_path = self.path_resolver.temp_path
            doc_path = self.path_resolver.document_output_path

            stats = {
                "base_storage_path": str(base_path),
                "base_storage_exists": base_path.exists(),
                "temp_path": str(temp_path),
                "temp_path_exists": temp_path.exists(),
                "document_output_path": str(doc_path),
                "document_output_exists": doc_path.exists(),
                "validation_level": self.storage_validator.validation_level.value,
                "component_versions": {
                    "storage_context": "v1.0",
                    "path_resolver": "v1.0",
                    "storage_validator": "v1.0",
                },
            }

            # Storage-Größen berechnen falls Pfade existieren
            if base_path.exists():
                try:
                    total_size = sum(
                        f.stat().st_size for f in base_path.rglob("*") if f.is_file()
                    )
                    file_count = len(list(base_path.rglob("*")))
                    stats["storage_total_size"] = total_size
                    stats["storage_file_count"] = file_count
                except Exception:
                    stats["storage_total_size"] = "unknown"
                    stats["storage_file_count"] = "unknown"

            return stats

        except Exception as e:
            self.logger.error(f"Error getting storage statistics: {e}")
            return {"error": str(e)}

    def clear_cache(self) -> Dict[str, int]:
        """
        Leert alle Caches des DocumentStorageService.

        Returns:
            Dictionary mit Clear-Statistiken
        """
        cleared_methods = 0

        if hasattr(self.get_document_path, "cache_clear"):
            self.get_document_path.cache_clear()
            cleared_methods += 1

        if hasattr(self.validate_document_before_storage, "cache_clear"):
            self.validate_document_before_storage.cache_clear()
            cleared_methods += 1

        logger.info(
            f"Cleared {cleared_methods} method caches in DocumentStorageService"
        )
        return {"cleared_methods": cleared_methods}

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Gibt Cache-Statistiken für alle gecachten Methoden zurück.

        Returns:
            Dictionary mit Cache-Statistiken
        """
        stats = {}

        if hasattr(self.get_document_path, "cache_stats"):
            stats["document_path"] = self.get_document_path.cache_stats()

        if hasattr(self.validate_document_before_storage, "cache_stats"):
            stats[
                "document_validation"
            ] = self.validate_document_before_storage.cache_stats()

        return stats

    @ttl_cache(seconds=1800, maxsize=32, key_prefix="delivery_slip_path")
    def save_delivery_slip_pdf(
        self,
        document_data: bytes,
        document_name: str,
        supplier_name: str,
        delivery_number: Optional[str] = None,
        delivery_date: Optional[str] = None,
        auto_detected: bool = False,
    ) -> StorageResult:
        """
        Speichert Lieferschein-PDF in speziellem Lieferscheine-Ordner.

        Args:
            document_data: Binärdaten des Lieferscheins
            document_name: Original-Dateiname
            supplier_name: Name des Lieferanten
            delivery_number: Lieferscheinnummer (optional)
            delivery_date: Lieferdatum (optional)
            auto_detected: Ob Lieferant automatisch erkannt wurde

        Returns:
            StorageResult mit Speicher-Informationen
        """
        try:
            self.logger.info(
                "Saving delivery slip: "
                f"'{document_name}' for supplier: "
                f"'{supplier_name}'"
            )

            # 1. DELIVERY SLIP PATH RESOLUTION (SERVER oder LOKAL)
            # NEU: Server-Storage als primär, lokal als Fallback
            server_unavailable_info = None  # Für GUI-Warnung

            # Prüfe Server-Verfügbarkeit direkt über UNC-Pfad
            if (
                self.use_server_storage
                and self.path_resolver.server_storage_path.exists()
            ):
                # SERVER-Speicherung (PRIMÄR)
                path_result = self.path_resolver.resolve_server_delivery_slip_path(
                    supplier_name=supplier_name, create_folders=True
                )
                storage_location = "server"
                self.logger.info("Using SERVER storage for " "delivery slip (primary)")
            else:
                # LOKALE Speicherung (Fallback)
                path_result = self.path_resolver.resolve_delivery_slip_path(
                    supplier_name=supplier_name, create_folders=True
                )
                storage_location = "local"

                if self.use_server_storage:
                    srv = self.path_resolver.server_storage_path
                    self.logger.warning(
                        "Server storage enabled but "
                        f"not available ({srv}), "
                        "using local fallback for "
                        "delivery slip"
                    )

                    # Sammle Informationen für GUI
                    local_p = str(path_result.path) if path_result.success else "N/A"
                    server_unavailable_info = {
                        "intended_storage": "server",
                        "actual_storage": "local",
                        "server_path": str(srv / supplier_name / "Lieferscheine"),
                        "local_path": local_p,
                        "reason": ("Server-Pfad nicht " f"verfügbar ({srv})"),
                        "document_type": "delivery_slip",
                    }

            self.logger.info(
                "Path resolution result: "
                f"success={path_result.success}, "
                f"path={path_result.path}"
            )

            if not path_result.success:
                return StorageResult(
                    success=False,
                    error=f"Failed to resolve delivery slip path: {path_result.error}",
                    warnings=path_result.warnings,
                )

            # 2. DOCUMENT VALIDATION
            doc_validation = self.storage_validator.validate_document_data(
                document_data, document_name
            )
            if not doc_validation.is_valid:
                errs = "; ".join(doc_validation.errors)
                return StorageResult(
                    success=False,
                    error=("Document validation failed: " f"{errs}"),
                    warnings=doc_validation.warnings,
                )

            # 3. FILENAME GENERATION
            file_extension = Path(document_name).suffix or ".pdf"
            filename = self.path_resolver.generate_delivery_slip_filename(
                supplier_name=supplier_name,
                delivery_number=delivery_number,
                delivery_date=delivery_date,
                original_filename=document_name,
                file_extension=file_extension,
            )

            # 4. PERMISSION CHECK
            perm_validation = self.storage_validator.validate_storage_permissions(
                path_result.path
            )
            if not perm_validation.is_valid:
                return StorageResult(
                    success=False,
                    error=f"Permission denied: {'; '.join(perm_validation.errors)}",
                    warnings=perm_validation.warnings,
                )

            # 5. PRIMARY STORAGE - Speichere auf Server/Lokal (PRIMÄR)
            final_file_path = path_result.path / filename
            primary_save_success = False

            try:
                self.logger.info(f"Writing delivery slip to: {final_file_path}")

                with open(final_file_path, "wb") as f:
                    f.write(document_data)

                primary_save_success = True
                self.logger.info(
                    "Delivery slip saved to "
                    f"{storage_location.upper()}: "
                    f"{final_file_path}"
                )
                self.logger.info(
                    "Delivery slip successfully written!"
                    f" Size: {len(document_data)} bytes"
                )

            except Exception as e:
                error_msg = (
                    f"Failed to save delivery slip to {storage_location}: {str(e)}"
                )
                self.logger.error(error_msg)
                # Speicher-Fehler ist kritisch, wenn kein SharePoint-Fallback verfügbar
                if not self.use_sharepoint:
                    return StorageResult(success=False, error=error_msg)

            # 6. SHAREPOINT UPLOAD (FALLBACK wenn primäre Speicherung fehlschlägt)
            sharepoint_url = None
            sharepoint_warnings = []
            sharepoint_upload_attempted = False

            # SharePoint als Fallback wenn primäre Speicherung fehlgeschlagen
            if (
                self.use_sharepoint
                and self.sharepoint_client.is_available()
                and not primary_save_success
            ):
                try:
                    sharepoint_upload_attempted = True
                    self.logger.warning(
                        "Primary storage failed for "
                        "delivery slip, attempting "
                        "SharePoint fallback..."
                    )

                    # Erstelle minimalen StorageContext für Lieferscheine (nur Supplier)
                    from .storage_context import StorageContextData

                    # Lieferschein-Context: Nur Supplier, Rest mit Defaults
                    lieferschein_context = StorageContextData(
                        batch_number="LIEFERSCHEIN",
                        article_number="",
                        supplier_normalized=supplier_name,
                        supplier_name=supplier_name,
                        kompatibilitaet="",
                        delivery_number=delivery_number or "",
                    )

                    # Verwende PathResolver für SharePoint-Pfad
                    sharepoint_path = self.path_resolver.resolve_sharepoint_path(
                        document_type=DocumentType.LIEFERSCHEIN,
                        context=lieferschein_context,
                    )

                    self.logger.info(
                        "Uploading delivery slip to "
                        "SharePoint (fallback): "
                        f"{sharepoint_path}/{filename}"
                    )

                    upload_result = self.sharepoint_client.upload_document(
                        document_data=document_data,
                        sharepoint_path=sharepoint_path,
                        filename=filename,
                        overwrite=True,
                    )

                    if upload_result.success:
                        sharepoint_url = upload_result.file_url
                        self.logger.info(
                            "Delivery slip SharePoint "
                            "fallback successful: "
                            f"{sharepoint_url}"
                        )
                    else:
                        error_msg = (
                            "SharePoint fallback " "failed: " f"{upload_result.error}"
                        )
                        sharepoint_warnings.append(error_msg)
                        self.logger.error(error_msg)

                except Exception as e:
                    error_msg = f"SharePoint fallback error: {str(e)}"
                    sharepoint_warnings.append(error_msg)
                    self.logger.error(error_msg)

            # Prüfe ob überhaupt eine Speicherung erfolgreich war
            if not primary_save_success and not sharepoint_url:
                return StorageResult(
                    success=False,
                    error=(
                        "All storage methods failed "
                        "for delivery slip "
                        "(server/local + SharePoint)"
                    ),
                    warnings=sharepoint_warnings,
                )

            # 7. CREATE RESULT
            result = StorageResult(
                success=True,
                file_path=str(final_file_path) if primary_save_success else None,
                filename=filename,
                storage_folder=str(path_result.path) if primary_save_success else None,
                document_type=DocumentType.LIEFERSCHEIN.value,
                sharepoint_url=sharepoint_url,
            )

            # Sammle Warnungen
            result.warnings.extend(doc_validation.warnings)
            result.warnings.extend(path_result.warnings)
            result.warnings.extend(perm_validation.warnings)
            result.warnings.extend(sharepoint_warnings)

            # Metadaten hinzufügen
            result.metadata.update(
                {
                    "supplier_name": supplier_name,
                    "delivery_number": delivery_number,
                    "delivery_date": delivery_date,
                    "auto_detected": auto_detected,
                    "file_size": len(document_data),
                    "original_filename": document_name,
                    "scan_date": datetime.now().isoformat(),
                    "validation_level": self.storage_validator.validation_level.value,
                    "path_created": path_result.created,
                    "server_storage_enabled": self.use_server_storage,
                    "sharepoint_enabled": self.use_sharepoint,
                    "primary_storage_location": storage_location,
                    "primary_save_success": primary_save_success,
                    "sharepoint_uploaded": sharepoint_url is not None,
                    "sharepoint_was_fallback": sharepoint_upload_attempted,
                    "storage_mode": self.storage_mode,
                    "final_storage": "server"
                    if (storage_location == "server" and primary_save_success)
                    else "local"
                    if (storage_location == "local" and primary_save_success)
                    else "sharepoint_fallback"
                    if sharepoint_url
                    else "unknown",
                    # NEU: Für GUI-Warnung
                    "server_unavailable_info": (server_unavailable_info),
                }
            )

            # Log final status
            if primary_save_success and not sharepoint_url:
                self.logger.info(
                    "Delivery slip saved to "
                    f"{storage_location.upper()}: "
                    f"{final_file_path}"
                )
            elif sharepoint_url:
                self.logger.warning(
                    "Primary storage failed, "
                    "delivery slip saved to "
                    "SharePoint fallback: "
                    f"{sharepoint_url}"
                )

            return result

        except Exception as e:
            error_msg = f"Failed to save delivery slip {document_name}: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(success=False, error=error_msg)

    def get_delivery_slip_path(
        self, supplier_name: str, create_folders: bool = False
    ) -> Tuple[Path, List[str]]:
        """
        Gibt Pfad zum Lieferscheine-Ordner für einen Lieferanten zurück.

        Args:
            supplier_name: Name des Lieferanten
            create_folders: Ob Ordnerstruktur erstellt werden soll

        Returns:
            Tuple von (Pfad, Warnungen)
        """
        try:
            path_result = self.path_resolver.resolve_delivery_slip_path(
                supplier_name=supplier_name, create_folders=create_folders
            )

            if not path_result.success:
                self.logger.warning(
                    "Delivery slip path resolution "
                    f"failed for {supplier_name}: "
                    f"{path_result.error}"
                )
                return Path("."), [path_result.error or "Unknown path resolution error"]

            return path_result.path, path_result.warnings

        except Exception as e:
            error_msg = f"Error getting delivery slip path: {e}"
            self.logger.error(error_msg)
            return Path("."), [error_msg]

    def list_delivery_slips(
        self,
        supplier_name: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Listet alle Lieferscheine für einen Lieferanten auf.

        WICHTIG: Verwendet FLACHE Ordnerstruktur (alle Lieferscheine direkt im Ordner)

        Args:
            supplier_name: Name des Lieferanten
            year: Optionales Jahr-Filter (filtert nach Datei-Datum)
            month: Optionales Monat-Filter (filtert nach Datei-Datum)

        Returns:
            Liste von Lieferschein-Informationen
        """
        try:
            # Hole Basis-Pfad (FLACHE Struktur: Lieferant/Lieferscheine/)
            delivery_slip_path, warnings = self.get_delivery_slip_path(supplier_name)

            if not delivery_slip_path.exists():
                self.logger.warning(
                    f"Delivery slip path does not exist: {delivery_slip_path}"
                )
                return []

            delivery_slips = []

            # FLACHE STRUKTUR: Scanne direkt alle Dateien im Ordner
            self.logger.info(
                f"Scanning flat delivery slip folder: {delivery_slip_path}"
            )
            delivery_slips = self._scan_delivery_slip_folder(
                delivery_slip_path, supplier_name
            )

            # FILTER NACH JAHR/MONAT (optional, basierend auf Datei-Datum)
            if year or month:
                filtered_slips = []
                for slip in delivery_slips:
                    try:
                        # Extrahiere Datum aus modified_time
                        mod_time = slip.get("modified_time", 0)
                        file_date = datetime.fromtimestamp(mod_time)

                        # Filter nach Jahr
                        if year and file_date.year != year:
                            continue

                        # Filter nach Monat
                        if month and file_date.month != month:
                            continue

                        filtered_slips.append(slip)

                    except Exception as e:
                        self.logger.warning(f"Error filtering slip by date: {e}")
                        # Bei Fehler: Datei trotzdem einbeziehen
                        filtered_slips.append(slip)

                delivery_slips = filtered_slips
                self.logger.info(
                    "Filtered delivery slips by "
                    f"year={year}, month={month}: "
                    f"{len(delivery_slips)} results"
                )

            # Sortiere nach Datum (neueste zuerst)
            delivery_slips.sort(key=lambda x: x.get("modified_time", 0), reverse=True)

            self.logger.info(
                f"Listed {len(delivery_slips)} delivery slips for {supplier_name}"
            )
            return delivery_slips

        except Exception as e:
            self.logger.error(f"Error listing delivery slips for {supplier_name}: {e}")
            return []

    def _scan_delivery_slip_folder(
        self, folder_path: Path, supplier_name: str
    ) -> List[Dict[str, Any]]:
        """
        Scannt einen Ordner nach Lieferschein-Dateien.

        Args:
            folder_path: Pfad zum zu scannenden Ordner
            supplier_name: Name des Lieferanten

        Returns:
            Liste von Lieferschein-Informationen
        """
        delivery_slips = []

        try:
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in [
                    ".pdf",
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".tiff",
                ]:
                    stat = file_path.stat()

                    delivery_slip_info = {
                        "filename": file_path.name,
                        "filepath": str(file_path),
                        "supplier_name": supplier_name,
                        "file_size": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "modified_date": (
                            datetime.fromtimestamp(stat.st_mtime).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        ),
                        "file_extension": file_path.suffix.lower(),
                        "folder_year": folder_path.parent.name
                        if folder_path.parent.name.isdigit()
                        else None,
                        "folder_month": folder_path.name,
                    }

                    # Versuche Lieferscheinnummer aus Dateiname zu extrahieren
                    delivery_number = self._extract_delivery_number_from_filename(
                        file_path.name
                    )
                    if delivery_number:
                        delivery_slip_info["delivery_number"] = delivery_number

                    delivery_slips.append(delivery_slip_info)

        except Exception as e:
            self.logger.warning(f"Error scanning folder {folder_path}: {e}")

        return delivery_slips

    def _extract_delivery_number_from_filename(self, filename: str) -> Optional[str]:
        """
        Versucht Lieferscheinnummer aus Dateiname zu extrahieren.

        Args:
            filename: Dateiname

        Returns:
            Extrahierte Lieferscheinnummer oder None
        """
        import re

        try:
            # Typische Lieferschein-Muster
            patterns = [
                r"LS[\-_]?(\d+[\-_]\d+)",  # LS-25-219, LS_25_219
                r"Lieferschein[\-_]([A-Z0-9\-_]+)",  # Lieferschein_LS25-219
                r"([A-Z]{2}\d+[\-_]\d+)",  # LS25-219
                r"(\d{4,6})",  # Einfache Nummern
            ]

            for pattern in patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            self.logger.debug(f"Error extracting delivery number from {filename}: {e}")
            return None

    def get_documents_for_merge(
        self,
        batch_number: str,
        delivery_number: str = "",
        article_number: str = "",
        supplier_name: str = "",
        temp_folder: Optional[Path] = None,
    ) -> List[Path]:
        """
        Lädt Dokumente für Merge-Operation.

        Primär: Von Server/Lokal laden (wo die Dokumente gespeichert wurden)
        Fallback: Von SharePoint herunterladen (falls Server-Docs nicht vorhanden)

        WICHTIG: Merge-Quellen-Priorität entspricht Speicher-Strategie:
        1. Server (wenn Server-Storage aktiviert und verfügbar)
        2. Lokal (wenn Server nicht verfügbar oder deaktiviert)
        3. SharePoint (nur als Fallback wenn lokal/server keine Dateien)

        Args:
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            article_number: Artikelnummer
            supplier_name: Lieferantenname
            temp_folder: Temporärer Ordner für Downloads (optional)

        Returns:
            Liste von Pfaden zu heruntergeladenen Dokumenten

        Note:
            Sets self.last_merge_source to 'server',
            'local', or 'sharepoint' to indicate
            document source
        """
        import tempfile

        if temp_folder is None:
            temp_folder = Path(tempfile.gettempdir()) / "medealis_merge"
            temp_folder.mkdir(parents=True, exist_ok=True)

        downloaded_files = []
        self.last_merge_source = "unknown"  # Track document source

        try:
            # 1. Hole Storage Context
            context = self.storage_context.get_complete_storage_context(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=supplier_name,
            )

            # 2. PRIMARY: Server/Lokaler Ordner (wo Dokumente gespeichert wurden)
            # Bestimme primäre Quelle basierend auf Storage-Konfiguration
            # Prüfe Server-Verfügbarkeit direkt über UNC-Pfad
            if (
                self.use_server_storage
                and self.path_resolver.server_storage_path.exists()
            ):
                # SERVER-Speicherung (PRIMÄR)
                path_result = self.path_resolver.resolve_server_storage_path(
                    context, create_folders=False
                )
                primary_source = "server"
                self.logger.info(
                    "[MERGE] PRIMARY: Checking "
                    "server storage for merge "
                    f"documents: {batch_number}"
                )
            else:
                # LOKALE Speicherung (Primär-Fallback)
                path_result = self.path_resolver.resolve_storage_path(
                    context, create_folders=False
                )
                primary_source = "local"
                self.logger.info(
                    "[MERGE] PRIMARY: Checking "
                    "local storage for merge "
                    f"documents: {batch_number}"
                )

            if path_result.success and path_result.path.exists():
                self.logger.info(f"[MERGE] Primary path: {path_result.path}")
                local_pdfs = list(path_result.path.glob("*.pdf"))
                self.logger.info(
                    f"[MERGE] Found {len(local_pdfs)} PDFs in {primary_source} storage"
                )

                # Kopiere zu Temp-Ordner (für konsistente Handhabung)
                for local_pdf in local_pdfs:
                    temp_file = temp_folder / local_pdf.name
                    import shutil

                    shutil.copy2(local_pdf, temp_file)
                    downloaded_files.append(temp_file)
                    self.logger.info(
                        f"[MERGE] ✓ Loaded from {primary_source}: {local_pdf.name}"
                    )

                if downloaded_files:
                    self.last_merge_source = (
                        primary_source  # Mark as server/local source
                    )
            else:
                pp = path_result.path if path_result.path else "N/A"
                self.logger.warning("[MERGE] Primary path not found: " f"{pp}")

            # 2b. LIEFERSCHEIN aus separatem
            # Lieferscheine-Ordner holen (FLACH)
            if delivery_number and supplier_name:
                self.logger.info(
                    "[MERGE] Looking for delivery "
                    "slip in separate folder: "
                    f"{supplier_name} / "
                    f"{delivery_number}"
                )

                # Bestimme Lieferschein-Pfad (Server oder Lokal) - FLACHE STRUKTUR
                # Prüfe Server-Verfügbarkeit direkt über UNC-Pfad
                if (
                    self.use_server_storage
                    and self.path_resolver.server_storage_path.exists()
                ):
                    # SERVER-Lieferschein-Pfad
                    delivery_slip_path_result = (
                        self.path_resolver.resolve_server_delivery_slip_path(
                            supplier_name=supplier_name, create_folders=False
                        )
                    )
                else:
                    # LOKALER Lieferschein-Pfad
                    delivery_slip_path_result = (
                        self.path_resolver.resolve_delivery_slip_path(
                            supplier_name=supplier_name, create_folders=False
                        )
                    )

                if (
                    delivery_slip_path_result.success
                    and delivery_slip_path_result.path.exists()
                ):
                    self.logger.info(
                        "[MERGE] Delivery slip folder "
                        "found (FLAT): "
                        f"{delivery_slip_path_result.path}"
                    )

                    # Suche nach Lieferschein mit passender Lieferscheinnummer
                    # FLACHE STRUKTUR: Durchsuche direkt den Ordner (kein Jahr/Monat!)
                    delivery_slip_found = False
                    already_loaded_names = {f.name for f in downloaded_files}
                    for pdf_file in delivery_slip_path_result.path.glob("*.pdf"):
                        # Prüfe ob Lieferscheinnummer im Dateinamen vorkommt
                        if delivery_number.lower() in pdf_file.name.lower():
                            # Überspringe falls Datei bereits aus Artikel-Ordner geladen
                            if pdf_file.name in already_loaded_names:
                                self.logger.info(
                                    "[MERGE] Delivery slip already"
                                    " included from article folder,"
                                    f" skipping duplicate: {pdf_file.name}"
                                )
                                delivery_slip_found = True
                                break
                            # Kopiere Lieferschein zu Temp-Ordner
                            import shutil

                            temp_file = temp_folder / pdf_file.name
                            shutil.copy2(pdf_file, temp_file)
                            downloaded_files.append(temp_file)
                            self.logger.info(
                                "[MERGE] Loaded delivery"
                                " slip from "
                                f"{primary_source}: "
                                f"{pdf_file.name}"
                            )
                            delivery_slip_found = True
                            break  # Nur ersten Match verwenden

                    if not delivery_slip_found:
                        self.logger.warning(
                            "[MERGE] Delivery slip not "
                            "found in flat folder for: "
                            f"{delivery_number}"
                        )
                else:
                    dsp = (
                        delivery_slip_path_result.path
                        if delivery_slip_path_result.path
                        else "N/A"
                    )
                    self.logger.warning(
                        "[MERGE] Delivery slip folder " f"not found: {dsp}"
                    )
            else:
                if not delivery_number:
                    self.logger.info(
                        "[MERGE] No delivery number "
                        "provided - skipping delivery "
                        "slip search"
                    )
                if not supplier_name:
                    self.logger.info(
                        "[MERGE] No supplier name "
                        "provided - skipping delivery "
                        "slip search"
                    )

            # 3. FALLBACK: SharePoint-Download (nur wenn keine Dateien lokal gefunden)
            if (
                not downloaded_files
                and self.use_sharepoint
                and self.sharepoint_client.is_available()
            ):
                self.logger.warning(
                    "[MERGE] FALLBACK: No files in "
                    "primary storage, trying "
                    "SharePoint download: "
                    f"{batch_number}"
                )

                # Bestimme SharePoint-Pfad
                sharepoint_path = self.path_resolver.resolve_sharepoint_path(
                    document_type="pdb",  # Standard-Typ
                    context=context,
                )

                self.logger.info(f"[MERGE] SharePoint path: {sharepoint_path}")

                # Liste alle Dateien im SharePoint-Ordner
                files = self.sharepoint_client.list_files(sharepoint_path)

                self.logger.info(f"[MERGE] Found {len(files)} files on SharePoint")

                # PERFORMANCE OPTIMIZATION: Parallele Downloads mit ThreadPoolExecutor
                from concurrent.futures import ThreadPoolExecutor, as_completed

                # Filtere nur PDF-Dateien
                pdf_files = [
                    f for f in files if f.get("name", "").lower().endswith(".pdf")
                ]
                self.logger.info(
                    "[MERGE] Starting parallel "
                    "download of "
                    f"{len(pdf_files)} PDF files..."
                )

                def download_single_file(file_info):
                    """Download eine einzelne Datei (für parallel execution)"""
                    filename = file_info.get("name", "")
                    try:
                        self.logger.info(
                            f"[MERGE] Downloading {filename} from SharePoint..."
                        )
                        file_bytes = self.sharepoint_client.download_document(
                            sharepoint_path=sharepoint_path, filename=filename
                        )

                        if file_bytes:
                            # Speichere temporär
                            temp_file = temp_folder / filename
                            with open(temp_file, "wb") as f:
                                f.write(file_bytes)
                            self.logger.info(
                                "[MERGE] Downloaded from "
                                "SharePoint: "
                                f"{filename} "
                                f"({len(file_bytes)} bytes)"
                            )
                            return temp_file
                        else:
                            self.logger.warning(
                                "[MERGE] Failed to "
                                "download from "
                                f"SharePoint: {filename}"
                            )
                            return None
                    except Exception as e:
                        self.logger.error(f"[MERGE] Error downloading {filename}: {e}")
                        return None

                # Parallel downloads (max 5 gleichzeitig für SharePoint API limits)
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(download_single_file, f): f for f in pdf_files
                    }

                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            downloaded_files.append(result)

                self.logger.info(
                    "[MERGE] SharePoint fallback "
                    "download complete: "
                    f"{len(downloaded_files)} files"
                )
                if downloaded_files:
                    self.last_merge_source = (
                        "sharepoint"  # Mark as SharePoint fallback source
                    )
            else:
                self.logger.info(
                    "[MERGE] SharePoint not available "
                    "or disabled, no fallback available"
                )

            self.logger.info(
                f"Total documents ready for merge: {len(downloaded_files)}"
            )
            return downloaded_files

        except Exception as e:
            self.logger.error(f"Error getting documents for merge: {e}")
            return []


# Global instance - SINGLE POINT OF ACCESS
# WICHTIG: Für Migration - beide Instanzen verfügbar

# Legacy support: Lade alte Implementation in legacy_service.py falls gewünscht
# Neue zentralisierte Instanz
document_storage_service = DocumentStorageService()
