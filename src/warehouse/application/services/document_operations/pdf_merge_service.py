"""
PDF Merge Service - PDF merging and manipulation operations.

Extracted from EnhancedDocumentService to provide standalone PDF operations.
Supports delivery-specific PDF merging with predefined file ordering.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Optional PDF merging dependency
try:
    from PyPDF2 import PdfMerger
    PDFMERGER_AVAILABLE = True
except ImportError:
    PDFMERGER_AVAILABLE = False
    logger.warning("PyPDF2 not available - PDF merging disabled")

# Optional reportlab dependency for cover page generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("Reportlab not available - Cover page generation limited")


class PDFMergeService:
    """
    Service for PDF merging and manipulation operations.

    Features:
    - Merge PDFs in delivery folders with predefined ordering
    - Custom file pattern matching
    - Flexible output naming
    - Error handling for corrupted PDFs
    """

    def __init__(self):
        """Initialize PDF merge service."""
        if not PDFMERGER_AVAILABLE:
            logger.warning("PDF merging not available - PyPDF2 not installed")
        else:
            logger.info("PDFMergeService initialized")

    def merge_delivery_pdfs(
        self,
        folder_path: Path,
        delivery_number: str,
        output_filename: Optional[str] = None,
        file_order: Optional[List[str]] = None
    ) -> Optional[Path]:
        """
        Merges PDF files in delivery folder with predefined order.

        Args:
            folder_path: Path to folder containing PDFs
            delivery_number: Delivery number for filename generation
            output_filename: Optional custom output filename
            file_order: Optional custom file order (keywords for matching)

        Returns:
            Path to merged PDF or None if failed

        Example:
            service = PDFMergeService()
            result = service.merge_delivery_pdfs(
                folder_path=Path("C:/delivery/folder"),
                delivery_number="DEL-001"
            )
        """
        if not PDFMERGER_AVAILABLE:
            logger.error("PDF merging not available - PyPDF2 not installed")
            return None

        try:
            if not folder_path.exists():
                logger.error(f"Folder not found: {folder_path}")
                return None

            # Use default file order if none provided
            if file_order is None:
                file_order = ["PDB", "Vermessungsprotokoll", "Bestellungsdokument", "Lieferschein", "Begleitpapiere"]

            # Collect PDFs in specified order
            ordered_files = self._collect_pdfs_by_order(folder_path, file_order)

            if not ordered_files:
                logger.warning("No PDF files found for merging")
                return None

            # Generate output filename
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"Merged_Delivery_{delivery_number}_{timestamp}.pdf"

            output_path = folder_path / output_filename

            # Merge PDFs
            success = self._merge_pdf_files(ordered_files, output_path)

            if success:
                logger.info(f"PDF merge completed: {output_path}")
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            return None

    def merge_pdfs_by_pattern(
        self,
        folder_path: Path,
        patterns: List[str],
        output_filename: str
    ) -> Optional[Path]:
        """
        Merge PDFs matching specific patterns.

        Args:
            folder_path: Path to folder containing PDFs
            patterns: List of filename patterns to match (in order)
            output_filename: Output filename

        Returns:
            Path to merged PDF or None if failed
        """
        if not PDFMERGER_AVAILABLE:
            logger.error("PDF merging not available - PyPDF2 not installed")
            return None

        try:
            ordered_files = self._collect_pdfs_by_order(folder_path, patterns)

            if not ordered_files:
                logger.warning("No matching PDF files found")
                return None

            output_path = folder_path / output_filename
            success = self._merge_pdf_files(ordered_files, output_path)

            if success:
                logger.info(f"Pattern-based PDF merge completed: {output_path}")
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Error in pattern-based PDF merge: {e}")
            return None

    def _collect_pdfs_by_order(self, folder_path: Path, keywords: List[str]) -> List[Path]:
        """
        Collect PDF files in specified keyword order.

        Args:
            folder_path: Path to search for PDFs
            keywords: List of keywords to match against filenames

        Returns:
            List of PDF paths in specified order
        """
        ordered_files = []

        for keyword in keywords:
            matching_files = [
                f for f in folder_path.rglob('*.pdf')
                if keyword.lower() in f.name.lower()
            ]
            if matching_files:
                matching_files.sort()  # Sort alphabetically within each keyword group
                ordered_files.extend(matching_files)
                logger.debug(f"Found {len(matching_files)} PDFs for keyword '{keyword}'")

        logger.info(f"Collected {len(ordered_files)} PDFs total")
        return ordered_files

    def _merge_pdf_files(self, pdf_files: List[Path], output_path: Path) -> bool:
        """
        Merge list of PDF files into single output file.

        Args:
            pdf_files: List of PDF file paths to merge
            output_path: Output path for merged PDF

        Returns:
            True if successful, False otherwise
        """
        try:
            merger = PdfMerger()
            merged_count = 0

            for file_path in pdf_files:
                try:
                    merger.append(str(file_path))
                    merged_count += 1
                    logger.debug(f"Added to merger: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not add {file_path} to merger: {e}")

            if merged_count == 0:
                logger.error("No PDFs could be added to merger")
                return False

            # Write merged PDF
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)

            merger.close()
            logger.info(f"Successfully merged {merged_count} PDFs")
            return True

        except Exception as e:
            logger.error(f"Error during PDF merge operation: {e}")
            return False

    def is_available(self) -> bool:
        """
        Check if PDF merging functionality is available.

        Returns:
            True if PyPDF2 is installed and available
        """
        return PDFMERGER_AVAILABLE

    def get_pdf_count_in_folder(self, folder_path: Path) -> int:
        """
        Count PDF files in folder.

        Args:
            folder_path: Path to folder

        Returns:
            Number of PDF files found
        """
        try:
            if not folder_path.exists():
                return 0

            pdf_files = list(folder_path.rglob('*.pdf'))
            return len(pdf_files)

        except Exception as e:
            logger.error(f"Error counting PDFs in {folder_path}: {e}")
            return 0

    def get_merge_preview(self, file_paths: List[Path]) -> dict:
        """
        Get preview information for PDF merge operation.

        Args:
            file_paths: List of PDF file paths to merge

        Returns:
            Dictionary with preview information
        """
        preview = {
            "pdf_files": len(file_paths),
            "total_size_mb": 0.0,
            "warnings": [],
            "mergeable": True
        }

        if not PDFMERGER_AVAILABLE:
            preview["mergeable"] = False
            preview["warnings"].append("PyPDF2 nicht verfügbar - PDF merging deaktiviert")
            return preview

        try:
            total_size_bytes = 0
            for file_path in file_paths:
                if not file_path.exists():
                    preview["warnings"].append(f"Datei nicht gefunden: {file_path.name}")
                    continue

                if file_path.suffix.lower() != '.pdf':
                    preview["warnings"].append(f"Keine PDF-Datei: {file_path.name}")
                    continue

                try:
                    total_size_bytes += file_path.stat().st_size
                except Exception:
                    preview["warnings"].append(f"Größe nicht ermittelbar: {file_path.name}")

            preview["total_size_mb"] = total_size_bytes / (1024 * 1024)

            if preview["total_size_mb"] > 100:
                preview["warnings"].append("Dateigröße sehr groß (>100MB) - Merge könnte langsam sein")

        except Exception as e:
            preview["mergeable"] = False
            preview["warnings"].append(f"Fehler bei der Vorschau-Erstellung: {str(e)}")

        return preview

    def validate_merge_input(self, file_paths: List[Path], output_path: Path) -> dict:
        """
        Validate input for PDF merge operation.

        Args:
            file_paths: List of PDF file paths to merge
            output_path: Intended output path

        Returns:
            Dictionary with validation results
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        if not PDFMERGER_AVAILABLE:
            validation["valid"] = False
            validation["errors"].append("PyPDF2 nicht verfügbar")
            return validation

        # Check if files exist and are PDFs
        valid_files = 0
        for file_path in file_paths:
            if not file_path.exists():
                validation["errors"].append(f"Datei nicht gefunden: {file_path.name}")
                continue

            if file_path.suffix.lower() != '.pdf':
                validation["errors"].append(f"Keine PDF-Datei: {file_path.name}")
                continue

            valid_files += 1

        if valid_files == 0:
            validation["valid"] = False
            validation["errors"].append("Keine gültigen PDF-Dateien gefunden")

        # Check output path
        if output_path.exists():
            validation["warnings"].append(f"Ausgabedatei existiert bereits und wird überschrieben: {output_path.name}")

        try:
            # Check if output directory is writable
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Ausgabeordner nicht beschreibbar: {str(e)}")

        if validation["errors"]:
            validation["valid"] = False

        return validation

    def sort_files_by_document_order(self, file_paths: List[Path]) -> List[Path]:
        """
        Sort PDF files according to predefined document order.

        Order: PDB, Vermessungsprotokoll, Sichtkontrolle, Bestelldokument,
               Lieferscheindokument, Begleitpapiere

        Args:
            file_paths: List of PDF file paths to sort

        Returns:
            Sorted list of PDF file paths
        """
        # Define document order with keywords for matching
        document_order = [
            {"keywords": ["pdb", "produktdatenblatt"], "priority": 1},
            {"keywords": ["vermessungsprotokoll", "vermessung", "messung", "protokoll"], "priority": 2},
            {"keywords": ["sichtkontrolle", "fo00141", "visuell", "visual"], "priority": 3},
            {"keywords": ["bestellung", "order", "bestell"], "priority": 4},
            {"keywords": ["lieferschein", "ls", "delivery"], "priority": 5},
            {"keywords": ["begleitpapiere", "begleit", "zertifikat", "certificate", "accompany"], "priority": 6},
        ]

        # Create list of (file, priority) tuples
        file_priorities = []

        for file_path in file_paths:
            file_name_lower = file_path.name.lower()
            priority = 999  # Default priority for unmatched files (goes to end)

            # Find matching document type
            for doc_type in document_order:
                if any(keyword in file_name_lower for keyword in doc_type["keywords"]):
                    priority = doc_type["priority"]
                    break

            file_priorities.append((file_path, priority))
            logger.debug(f"File '{file_path.name}' assigned priority {priority}")

        # Sort by priority, then by filename for files with same priority
        file_priorities.sort(key=lambda x: (x[1], x[0].name.lower()))

        sorted_files = [fp[0] for fp in file_priorities]
        logger.info(f"Files sorted by document order: {[f.name for f in sorted_files]}")

        return sorted_files

    def create_cover_page(
        self,
        output_path: Path,
        title: str,
        article_number: str = "",
        batch_number: str = "",
        delivery_number: str = "",
        supplier_name: str = ""
    ) -> bool:
        """
        Create a cover page PDF with document information.

        Args:
            output_path: Path where to save the cover page PDF
            title: Main title for the cover page
            article_number: Article number
            batch_number: Batch number
            delivery_number: Delivery number
            supplier_name: Supplier name

        Returns:
            True if successful, False otherwise
        """
        if not REPORTLAB_AVAILABLE:
            logger.warning("Reportlab not available - creating simple text-based cover page")
            return self._create_simple_cover_page(output_path, title, article_number, batch_number, delivery_number)

        try:
            # Create a temporary cover page PDF
            doc = SimpleDocTemplate(str(output_path), pagesize=A4)
            styles = getSampleStyleSheet()

            # Create custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=2*cm
            )

            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=1*cm
            )

            info_style = ParagraphStyle(
                'CustomInfo',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_LEFT,
                leftIndent=2*cm,
                spaceAfter=0.5*cm
            )

            # Build content
            content = []

            # Main title
            content.append(Spacer(1, 3*cm))
            content.append(Paragraph(title, title_style))

            # Subtitle
            content.append(Paragraph("Dokumentation Wareneingang", header_style))
            content.append(Spacer(1, 2*cm))

            # Document information
            if article_number:
                content.append(Paragraph(f"<b>Artikel-Nummer:</b> {article_number}", info_style))
            if batch_number:
                content.append(Paragraph(f"<b>Chargen-Nummer:</b> {batch_number}", info_style))
            if delivery_number:
                content.append(Paragraph(f"<b>Lieferschein-Nummer:</b> {delivery_number}", info_style))
            if supplier_name:
                content.append(Paragraph(f"<b>Lieferant:</b> {supplier_name}", info_style))

            content.append(Spacer(1, 1*cm))
            content.append(Paragraph(f"<b>Erstellt am:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))

            content.append(Spacer(1, 3*cm))
            content.append(Paragraph("Dokumenteninhalt:", header_style))

            # Document order list
            doc_order = [
                "1. Produktdatenblatt (PDB)",
                "2. Vermessungsprotokoll",
                "3. Sichtkontrolle",
                "4. Bestelldokument",
                "5. Lieferscheindokument",
                "6. Begleitpapiere/Zertifikate"
            ]

            for item in doc_order:
                content.append(Paragraph(item, info_style))

            # Build PDF
            doc.build(content)
            logger.info(f"Cover page created successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating cover page with reportlab: {e}")
            # Fallback to simple cover page
            return self._create_simple_cover_page(output_path, title, article_number, batch_number, delivery_number)

    def _create_simple_cover_page(self, output_path: Path, title: str, article_number: str, batch_number: str, delivery_number: str) -> bool:
        """
        Create a simple text-based cover page (fallback when reportlab not available).

        Args:
            output_path: Path where to save the cover page PDF
            title: Main title for the cover page
            article_number: Article number
            batch_number: Batch number
            delivery_number: Delivery number

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a simple cover page using PyPDF2 only (very basic)
            # For now, we'll just log that a cover page would be created
            # A full implementation would require additional libraries
            logger.info(f"Simple cover page would be created: {title}")
            logger.info(f"  Article: {article_number}, Batch: {batch_number}, Delivery: {delivery_number}")

            # Create an empty PDF file as placeholder
            with open(output_path, 'w') as f:
                f.write("")  # Empty file as placeholder

            return True

        except Exception as e:
            logger.error(f"Error creating simple cover page: {e}")
            return False

    def merge_pdfs(
        self,
        file_paths: List[Path],
        output_path: Path,
        include_cover: bool = False,
        cover_title: str = None,
        sort_by_document_order: bool = True,
        article_number: str = "",
        batch_number: str = "",
        delivery_number: str = "",
        supplier_name: str = ""
    ) -> bool:
        """
        Merge multiple PDF files into a single output file.

        Args:
            file_paths: List of PDF file paths to merge
            output_path: Output path for merged PDF
            include_cover: Whether to include a cover page
            cover_title: Title for the cover page
            sort_by_document_order: Whether to sort files by predefined document order

        Returns:
            True if successful, False otherwise
        """
        if not PDFMERGER_AVAILABLE:
            logger.error("PDF merging not available - PyPDF2 not installed")
            return False

        try:
            # Validate input first
            validation = self.validate_merge_input(file_paths, output_path)
            if not validation["valid"]:
                logger.error("Merge validation failed")
                return False

            # Sort files by document order if requested
            if sort_by_document_order:
                file_paths = self.sort_files_by_document_order(file_paths)
                logger.info("Files sorted by predefined document order")

            merger = PdfMerger()
            merged_count = 0

            # Create and add cover page if requested
            if include_cover and cover_title:
                logger.info(f"Creating cover page: {cover_title}")
                cover_path = output_path.parent / f"_temp_cover_{output_path.stem}.pdf"

                try:
                    cover_created = self.create_cover_page(
                        cover_path,
                        cover_title,
                        article_number,
                        batch_number,
                        delivery_number,
                        supplier_name
                    )

                    if cover_created and cover_path.exists():
                        merger.append(str(cover_path))
                        merged_count += 1
                        logger.info("Cover page added successfully")
                    else:
                        logger.warning("Cover page could not be created")
                except Exception as e:
                    logger.warning(f"Error adding cover page: {e}")

            # Add PDF files in order
            for file_path in file_paths:
                if not file_path.exists() or file_path.suffix.lower() != '.pdf':
                    continue

                try:
                    merger.append(str(file_path))
                    merged_count += 1
                    logger.debug(f"Added to merger: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not add {file_path} to merger: {e}")

            if merged_count == 0:
                logger.error("No PDFs could be added to merger")
                return False

            # Write merged PDF
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)

            merger.close()

            # Clean up temporary cover page file
            if include_cover and cover_title:
                try:
                    cover_path = output_path.parent / f"_temp_cover_{output_path.stem}.pdf"
                    if cover_path.exists():
                        cover_path.unlink()
                        logger.debug("Temporary cover page file cleaned up")
                except Exception as e:
                    logger.warning(f"Could not clean up temporary cover page: {e}")

            logger.info(f"Successfully merged {merged_count} PDFs to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error during PDF merge operation: {e}")
            return False


# Global instance for convenience
pdf_merge_service = PDFMergeService()