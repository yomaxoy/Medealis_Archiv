"""
Document Opening Service - Cross-platform document and folder opening.

Extracted from EnhancedDocumentService to provide standalone document opening capabilities.
Supports Windows, macOS, and Linux with optional specific application targeting.

FEATURE: Auto-Open nach Dokument-Generierung für direktes Drucken
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Union, List

logger = logging.getLogger(__name__)


class DocumentOpeningService:
    """
    Cross-platform service for opening documents and folders.

    Features:
    - Automatic detection of installed applications (Word, Excel)
    - Platform-specific opening (Windows/macOS/Linux)
    - Option to open with specific application or system default
    - Folder opening support
    """

    def __init__(self):
        """Initialize document opening service with application detection."""
        self.app_paths = self._detect_application_paths()

        # Auto-Open Configuration (kann via Umgebungsvariablen überschrieben werden)
        self.auto_open_enabled = self._get_env_bool("AUTO_OPEN_DOCUMENTS", default=True)
        self.auto_open_barcodes = self._get_env_bool("AUTO_OPEN_BARCODES", default=True)
        self.auto_open_limit = int(os.getenv("AUTO_OPEN_LIMIT", "5"))

        logger.info(f"DocumentOpeningService initialized (auto_open={self.auto_open_enabled}, limit={self.auto_open_limit})")

    def open_document(self, document_path: Union[str, Path], app_name: Optional[str] = None) -> bool:
        """
        Open document with system default or specified application.

        Args:
            document_path: Path to document or folder
            app_name: Optional specific application name ('word', 'excel')

        Returns:
            True if successful, False otherwise

        Example:
            service = DocumentOpeningService()
            service.open_document("C:/path/to/document.docx")
            service.open_document("C:/path/to/document.docx", app_name="word")
        """
        try:
            document_path = Path(document_path)

            if not document_path.exists():
                logger.error(f"Document not found: {document_path}")
                return False

            if sys.platform == "win32":
                if app_name and app_name in self.app_paths and self.app_paths[app_name]:
                    # Open with specific application
                    subprocess.Popen([self.app_paths[app_name], str(document_path)])
                else:
                    # Open with system default
                    os.startfile(str(document_path))
            elif sys.platform == "darwin":
                # macOS
                subprocess.call(['open', str(document_path)])
            else:
                # Linux
                subprocess.call(['xdg-open', str(document_path)])

            logger.info(f"Opened document: {document_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to open document {document_path}: {e}")
            return False

    def open_folder(self, folder_path: Union[str, Path]) -> bool:
        """
        Open folder in system file manager.

        Args:
            folder_path: Path to folder

        Returns:
            True if successful, False otherwise
        """
        return self.open_document(folder_path)  # Same logic works for folders

    def get_available_applications(self) -> Dict[str, Optional[str]]:
        """
        Get dictionary of available applications and their paths.

        Returns:
            Dictionary with app names as keys and paths as values
        """
        return self.app_paths.copy()

    def is_application_available(self, app_name: str) -> bool:
        """
        Check if specific application is available.

        Args:
            app_name: Application name to check

        Returns:
            True if application is installed and found
        """
        return app_name in self.app_paths and self.app_paths[app_name] is not None

    def open_after_generation(
        self,
        file_paths: Union[str, Path, List[Union[str, Path]]],
        document_type: str = "document"
    ) -> Dict[str, any]:
        """
        Öffnet Dokument(e) automatisch nach Generierung.

        Args:
            file_paths: Einzelner Pfad oder Liste von Pfaden
            document_type: Typ des Dokuments ("document", "barcode", "pdf")

        Returns:
            Dict mit Statistiken: {opened: int, skipped: int, failed: int, reason: str}

        Example:
            result = service.open_after_generation("C:/path/PDB_CT0004.docx")
            result = service.open_after_generation(["file1.pdf", "file2.pdf"])
        """
        # Normalisiere zu Liste
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        result = {"opened": 0, "skipped": 0, "failed": 0, "reason": None}

        # Check: Auto-Open aktiviert?
        if not self.auto_open_enabled:
            result["skipped"] = len(file_paths)
            result["reason"] = "Auto-Open deaktiviert (AUTO_OPEN_DOCUMENTS=false)"
            logger.debug(f"Auto-Open skipped: {result['reason']}")
            return result

        # Check: Barcode-spezifische Config
        if document_type == "barcode" and not self.auto_open_barcodes:
            result["skipped"] = len(file_paths)
            result["reason"] = "Barcode Auto-Open deaktiviert (AUTO_OPEN_BARCODES=false)"
            logger.debug(f"Auto-Open skipped: {result['reason']}")
            return result

        # Check: Limit
        if len(file_paths) > self.auto_open_limit:
            result["skipped"] = len(file_paths)
            result["reason"] = f"Zu viele Dateien ({len(file_paths)} > {self.auto_open_limit}). Bitte manuell öffnen."
            logger.warning(f"Auto-Open limit exceeded: {result['reason']}")
            return result

        # Öffne Dateien
        for file_path in file_paths:
            try:
                if self.open_document(file_path):
                    result["opened"] += 1
                    logger.info(f"✅ Auto-opened: {Path(file_path).name}")
                else:
                    result["failed"] += 1
                    logger.warning(f"❌ Failed to auto-open: {file_path}")
            except Exception as e:
                result["failed"] += 1
                logger.error(f"❌ Error auto-opening {file_path}: {e}")

        return result

    def _get_env_bool(self, key: str, default: bool = True) -> bool:
        """Holt Boolean-Wert aus Umgebungsvariable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _detect_application_paths(self) -> Dict[str, Optional[str]]:
        """
        Detect available application paths.

        Returns:
            Dictionary mapping application names to their executable paths
        """
        apps = {}

        if sys.platform == "win32":
            # Common Windows applications
            possible_paths = {
                'word': [
                    r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE"
                ],
                'excel': [
                    r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"
                ]
            }

            for app, paths in possible_paths.items():
                for path in paths:
                    if Path(path).exists():
                        apps[app] = path
                        logger.debug(f"Found {app} at: {path}")
                        break
                else:
                    apps[app] = None
                    logger.debug(f"{app} not found")

        return apps


# Global instance for convenience
document_opening_service = DocumentOpeningService()