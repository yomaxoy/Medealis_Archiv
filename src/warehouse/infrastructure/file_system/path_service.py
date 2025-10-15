# src/warehouse/infrastructure/file_system/path_service.py

"""
Infrastructure Layer: Path Service
Handles file system path operations and folder creation.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PathService:
    """
    Infrastructure service for file system path operations.
    Handles the actual path construction and folder creation.
    """

    def __init__(self):
        """Initialize path service with base paths."""
        # Base path for Medealis documents
        self.base_path = Path.home() / "Medealis" / "Wareneingang"
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Document output path for generated templates
        self.document_output_path = Path.home() / ".medealis" / "documents"
        self.document_output_path.mkdir(parents=True, exist_ok=True)

        # Temporary path for processing
        self.temp_path = Path.home() / ".medealis" / "temp"
        self.temp_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"PathService initialized - Base: {self.base_path}")

    def create_delivery_folder_path(
        self,
        supplier_name: str,
        manufacturer: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        create_folders: bool = True
    ) -> Path:
        """
        Creates and returns the full folder path for a delivery.

        Args:
            supplier_name: Name of supplier
            manufacturer: Manufacturer/implant type
            article_number: Article number
            batch_number: Batch number
            delivery_number: Delivery number
            create_folders: Whether to create the folder structure

        Returns:
            Path to delivery folder
        """
        # Clean names for filesystem
        clean_supplier = self._clean_filename(supplier_name)
        clean_manufacturer = self._clean_filename(manufacturer)
        clean_article = self._clean_filename(article_number)
        clean_batch = self._clean_filename(batch_number)
        clean_delivery = self._clean_filename(delivery_number)

        # Build path: Base / Supplier / Manufacturer / Article / Batch / Delivery
        folder_path = (
            self.base_path /
            clean_supplier /
            clean_manufacturer /
            clean_article /
            clean_batch /
            clean_delivery
        )

        # Create folder structure if requested
        if create_folders:
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Delivery folder created: {folder_path}")

        return folder_path

    def get_document_output_path(self, filename: str) -> Path:
        """
        Gets path for document output (generated templates).

        Args:
            filename: Document filename

        Returns:
            Full path to document
        """
        return self.document_output_path / filename

    def get_temp_path(self, filename: str) -> Path:
        """
        Gets temporary path for file processing.

        Args:
            filename: Temporary filename

        Returns:
            Path to temporary file
        """
        return self.temp_path / filename

    def _clean_filename(self, name: str) -> str:
        """
        Cleans a name for use as filename/folder name.

        Args:
            name: Original name

        Returns:
            Cleaned name safe for filesystem
        """
        if not name:
            return "Unknown"

        # Replace problematic characters
        replacements = {
            ' ': '_',
            '/': '-',
            '\\': '-',
            ':': '-',
            '*': '',
            '?': '',
            '"': '',
            '<': '',
            '>': '',
            '|': '-',
            'ä': 'ae',
            'ö': 'oe',
            'ü': 'ue',
            'ß': 'ss'
        }

        cleaned = name
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        # Remove multiple consecutive underscores/dashes
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
        while '--' in cleaned:
            cleaned = cleaned.replace('--', '-')

        return cleaned.strip('_-')

    def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """
        Cleans up old temporary files.

        Args:
            max_age_hours: Maximum age of temp files to keep
        """
        try:
            if not self.temp_path.exists():
                return

            import time
            current_time = time.time()
            cutoff_time = current_time - (max_age_hours * 3600)

            for temp_file in self.temp_path.iterdir():
                if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")

        except Exception as e:
            logger.warning(f"Error cleaning temp files: {e}")


# Global instance
path_service = PathService()