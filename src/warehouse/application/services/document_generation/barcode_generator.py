# src/warehouse/application/services/document_generation/barcode_generator.py

"""
Barcode Generator Service - Integrated PNG Barcode Generation

Migrated from domain/services/barcode_service.py to application
layer for clean architecture. Provides PNG barcode generation with
DocumentStorageService integration for consistent file storage.
"""

import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BarcodeGenerationResult:
    """Result of a barcode generation operation."""

    success: bool = False
    barcode_path: Optional[Path] = None
    barcode_type: str = "CODE128"
    generation_time: float = 0.0
    error: Optional[str] = None
    warnings: list = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

    def add_warning(self, warning: str):
        """Add warning message."""
        self.warnings.append(warning)
        logger.warning(warning)

    def set_error(self, error: str):
        """Set error and mark as failed."""
        self.error = error
        self.success = False
        logger.error(error)


class BarcodeGenerator:
    """
    Barcode generation service integrated with document generation architecture.

    Migrated from domain layer BarcodeService to application
    layer for proper Clean Architecture.
    Uses DocumentStorageService for consistent file paths with other documents.
    """

    def __init__(self):
        """Initialize barcode generator."""
        self.stats = {
            "barcodes_generated": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_generation_time": 0.0,
        }

        # Check barcode library availability
        self.barcode_available = self._check_barcode_library()

        lib_status = "available" if self.barcode_available else "not available"
        logger.info(
            "BarcodeGenerator initialized" " (barcode library: %s)",
            lib_status,
        )

    def _check_barcode_library(self) -> bool:
        """Check if python-barcode library is available."""
        try:
            import barcode  # noqa: F401
            from barcode.writer import ImageWriter  # noqa: F401

            return True
        except ImportError:
            logger.warning(
                "python-barcode library not" " available - using fallback" " generation"
            )
            return False

    def generate_barcode(
        self,
        value: str,
        output_path: Optional[Path] = None,
        barcode_type: str = "CODE128",
        filename_prefix: str = "barcode",
        open_after_creation: bool = False,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> BarcodeGenerationResult:
        """
        Generate PNG barcode file.

        Args:
            value: The value to encode in the barcode
            output_path: Full output path for the barcode file (optional)
            barcode_type: Type of barcode (CODE128, CODE39, EAN13)
            filename_prefix: Prefix for the filename
            open_after_creation: Whether to open the file after creation

        Returns:
            BarcodeGenerationResult with success/error information
        """
        start_time = datetime.now()
        result = BarcodeGenerationResult()

        try:
            # Validate input
            if not value or not value.strip():
                result.set_error("Empty value provided for barcode generation")
                return result

            # Generate output path if not provided (fallback only)
            if output_path is None:
                # Fallback: temp directory (should normally be
                # provided by DocumentGenerationService)
                from tempfile import gettempdir

                temp_dir = Path(gettempdir()) / "medealis_barcodes"
                temp_dir.mkdir(parents=True, exist_ok=True)

                clean_value = self._sanitize_filename(value)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename_prefix}_{clean_value}_{timestamp}.png"
                output_path = temp_dir / filename

                logger.warning(
                    "BarcodeGenerator using fallback"
                    " temp path -"
                    " DocumentGenerationService"
                    " should provide correct"
                    " path: %s",
                    output_path,
                )

            # Generate barcode
            if self.barcode_available:
                actual_barcode_path = self._generate_with_barcode_library(
                    value, output_path, barcode_type, additional_data or {}
                )
            else:
                actual_barcode_path = self._generate_fallback_barcode(
                    value, output_path, filename_prefix, additional_data or {}
                )

            if actual_barcode_path and actual_barcode_path.exists():
                result.success = True
                result.barcode_path = actual_barcode_path
                result.barcode_type = barcode_type

                # Open file if requested
                if open_after_creation:
                    self._open_file(str(actual_barcode_path))

                # Update statistics
                self.stats["barcodes_generated"] += 1
                self.stats["successful_generations"] += 1

                logger.info(
                    f"Barcode generated successfully: {actual_barcode_path.name}"
                )
            else:
                result.set_error(
                    "Barcode generation failed"
                    " - file not created"
                    f" at {output_path}"
                )
                self.stats["failed_generations"] += 1

        except Exception as e:
            result.set_error(f"Barcode generation error: {str(e)}")
            self.stats["failed_generations"] += 1
            logger.error(f"Error generating barcode: {e}")

        # Final timing
        end_time = datetime.now()
        result.generation_time = (end_time - start_time).total_seconds()
        self.stats["total_generation_time"] += result.generation_time

        # Metadata
        result.metadata.update(
            {
                "barcode_value": value,
                "barcode_type": barcode_type,
                "filename_prefix": filename_prefix,
                "file_size": output_path.stat().st_size if result.success else 0,
                "generation_method": (
                    "python-barcode" if self.barcode_available else "fallback"
                ),
                "platform": platform.system(),
            }
        )

        return result

    def _generate_with_barcode_library(
        self,
        value: str,
        output_path: Path,
        barcode_type: str,
        additional_data: Dict[str, Any],
    ) -> Optional[Path]:
        """Generate custom label with barcode using python-barcode library and PIL."""
        try:
            import barcode
            from barcode.writer import ImageWriter
            from PIL import Image, ImageDraw, ImageFont
            import io

            # Use additional_data if available, otherwise parse from value
            if additional_data:
                article_number = additional_data.get("article_number", "UNKNOWN")
                batch_number = additional_data.get("batch_number", value)
                storage_location = additional_data.get("storage_location", "LAGER-001")
            else:
                # Fallback: Parse the barcode value to extract components
                # Expected format: "ArticleNumber-BatchNumber-DeliveryNumber"
                parts = value.split("-")
                if len(parts) >= 2:
                    article_number = parts[0]
                    batch_number = parts[1]
                    storage_location = "LAGER-001"
                else:
                    article_number = "UNKNOWN"
                    batch_number = value
                    storage_location = "LAGER-001"

            # Get storage location from database if not provided or is default
            if (
                article_number
                and article_number != "UNKNOWN"
                and (not storage_location or storage_location == "LAGER-001")
            ):
                try:
                    from warehouse.infrastructure.database.repositories.sql_item_rep_domain import (  # noqa: E501
                        SQLAlchemyItemRepositoryDomain,
                    )

                    item_repo = SQLAlchemyItemRepositoryDomain()
                    item_info = item_repo.find_item_info_by_article_number(
                        article_number
                    )
                    if item_info and item_info.get("storage_location"):
                        storage_location = item_info["storage_location"]
                        logger.info(
                            "Storage location loaded" " from database for" " %s: '%s'",
                            article_number,
                            storage_location,
                        )
                    else:
                        logger.warning(
                            "No storage location found"
                            " in database for %s,"
                            " using default",
                            article_number,
                        )
                except Exception as e:
                    logger.warning(
                        "Could not load storage"
                        " location from database"
                        " for %s: %s",
                        article_number,
                        e,
                    )

            logger.info(
                "Generating label with:" " Article=%s, Batch=%s," " Storage=%s",
                article_number,
                batch_number,
                storage_location,
            )

            # Validate barcode type
            barcode_type_lower = barcode_type.lower()
            if barcode_type_lower not in ["code128", "code39", "ean13"]:
                barcode_type_lower = "code128"

            # Create barcode for batch number only
            code_instance = barcode.get(
                barcode_type_lower, batch_number, writer=ImageWriter()
            )

            # Generate barcode to memory buffer first
            buffer = io.BytesIO()
            code_instance.write(
                buffer,
                options={
                    "module_height": 15.0,
                    "module_width": 0.3,
                    "quiet_zone": 2.0,
                    "font_size": 10,
                    "text_distance": 5.0,
                    "background": "white",
                    "foreground": "black",
                    "dpi": 300,
                    "write_text": False,  # We'll add our own text
                },
            )
            buffer.seek(0)

            # Load the barcode image
            barcode_img = Image.open(buffer)

            # Create the label in landscape format (11cm x 7.5cm at 300 DPI)
            label_width = int(11 * 300 / 2.54)  # ~1299px
            label_height = int(7.5 * 300 / 2.54)  # ~886px

            # Create label background
            label = Image.new("RGB", (label_width, label_height), "white")
            draw = ImageDraw.Draw(label)

            # Load fonts
            try:
                # Liberation Sans = Linux-Ersatz fuer Arial
                # Reduzierte Schriftgroessen
                _lib_bold = (
                    "/usr/share/fonts/truetype/" "liberation/LiberationSans-Bold.ttf"
                )
                _lib_regular = (
                    "/usr/share/fonts/truetype/"
                    "liberation/"
                    "LiberationSans-Regular.ttf"
                )
                try:
                    # Try Liberation Sans Bold
                    bold_font_large = ImageFont.truetype(
                        _lib_bold,
                        106,
                    )
                    bold_font_medium = ImageFont.truetype(
                        _lib_bold,
                        70,
                    )
                    normal_font = ImageFont.truetype(
                        _lib_regular,
                        55,
                    )
                except Exception:
                    # Fallback to Arial (Windows)
                    try:
                        bold_font_large = ImageFont.truetype(
                            "arialbd.ttf",
                            106,
                        )
                        bold_font_medium = ImageFont.truetype(
                            "arialbd.ttf",
                            70,
                        )
                        normal_font = ImageFont.truetype(
                            "arial.ttf",
                            55,
                        )
                    except Exception:
                        # Final fallback to DejaVu
                        bold_font_large = ImageFont.truetype(
                            "/usr/share/fonts/truetype/" "dejavu/DejaVuSans-Bold.ttf",
                            106,
                        )
                        bold_font_medium = ImageFont.truetype(
                            "/usr/share/fonts/truetype/" "dejavu/DejaVuSans-Bold.ttf",
                            70,
                        )
                        normal_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/" "dejavu/DejaVuSans.ttf",
                            55,
                        )
            except Exception:
                # Ultimate fallback to default fonts
                try:
                    bold_font_large = ImageFont.load_default()
                    bold_font_medium = ImageFont.load_default()
                    normal_font = ImageFont.load_default()
                except Exception:
                    bold_font_large = None
                    bold_font_medium = None
                    normal_font = None

            # Define padding from all edges
            padding_top = 30
            padding_bottom = 30
            padding_left = 30
            padding_right = 30

            # Calculate usable area after padding
            usable_width = label_width - padding_left - padding_right
            usable_height = label_height - padding_top - padding_bottom

            # Calculate layout areas
            upper_half_height = usable_height // 2
            lower_half_height = usable_height - upper_half_height

            # UPPER HALF: Left side (Article + Storage) + Right side (QR Code)
            upper_y_start = padding_top + 20

            # Calculate space for QR code on the right (about 1/3 of width)
            qr_section_width = usable_width // 3
            text_section_width = usable_width - qr_section_width - 20  # 20px gap

            margin_left = padding_left + 10

            # ROW 1: Storage Location (OBEN - getauscht mit Artikelnummer)
            # Header text "Lagernummer:"
            draw.text(
                (margin_left, upper_y_start),
                "Lagernummer:",
                fill="black",
                font=bold_font_medium,
            )
            # Storage location below header - BOLD
            if storage_location and storage_location.strip():
                storage_y = upper_y_start + 40
                draw.text(
                    (margin_left, storage_y),
                    storage_location.strip(),
                    fill="black",
                    font=bold_font_large,
                )
            else:
                # Draw empty field for manual writing if no storage location
                storage_y = upper_y_start + 40
                # Draw line for manual writing
                line_end_x = margin_left + text_section_width - 20
                draw.line(
                    [margin_left, storage_y + 20, line_end_x, storage_y + 20],
                    fill="black",
                    width=2,
                )

            # ROW 2: Article Number (UNTEN - getauscht mit Lagernummer)
            # Kleiner Zeilenabstand zwischen Lagernummer und Artikelnummer
            article_header_y = storage_y + 150  # Space below storage location
            # Header text "Artikelnummer:"
            draw.text(
                (margin_left, article_header_y),
                "Artikelnummer:",
                fill="black",
                font=bold_font_medium,
            )
            # Article number below header - BOLD
            article_y = article_header_y + 40
            draw.text(
                (margin_left, article_y),
                article_number,
                fill="black",
                font=bold_font_large,
            )

            # QR Code on the right side
            qr_section_x = padding_left + text_section_width + 20
            qr_code_path = self._get_qr_code_for_article(article_number)
            if qr_code_path and qr_code_path.exists():
                try:
                    # QR-Code laden
                    qr_img = Image.open(qr_code_path)

                    # Optimale Größe für rechte obere Ecke berechnen
                    available_width = qr_section_width - 20
                    available_height = (
                        upper_half_height - 60
                    )  # Platz für Header + Margin
                    qr_size = min(
                        available_width,
                        available_height,
                        200,
                    )

                    # QR-Code auf optimale Größe skalieren
                    qr_resized = qr_img.resize(
                        (qr_size, qr_size), Image.Resampling.LANCZOS
                    )

                    # Position: Rechts oben, zentriert in der Sektion
                    qr_x = qr_section_x + (available_width - qr_size) // 2
                    qr_y = upper_y_start + 10

                    # QR-Code ins Label einfügen
                    label.paste(qr_resized, (qr_x, qr_y))

                    logger.info(
                        "QR-Code erfolgreich eingefuegt:" " %s",
                        qr_code_path.name,
                    )
                except Exception as e:
                    logger.warning(
                        "QR-Code konnte nicht geladen" " werden: %s",
                        e,
                    )
            else:
                logger.info(
                    "Kein QR-Code gefunden fuer" " Artikel %s",
                    article_number,
                )

            # Add a subtle separator line
            separator_y = padding_top + upper_half_height - 10
            draw.line(
                [
                    (padding_left, separator_y),
                    (label_width - padding_right, separator_y),
                ],
                fill="lightgray",
                width=2,
            )

            # LOWER HALF: Barcode and Batch Number
            lower_start_y = padding_top + upper_half_height + 20

            # Resize barcode to fit nicely in lower half
            barcode_target_width = usable_width - 40  # Leave internal margins
            barcode_target_height = lower_half_height - 80  # Leave space for text

            # Resize barcode maintaining aspect ratio
            barcode_resized = barcode_img.resize(
                (barcode_target_width, barcode_target_height),
                Image.Resampling.LANCZOS,
            )

            # Center the barcode horizontally within usable area
            barcode_x = padding_left + (usable_width - barcode_resized.width) // 2
            barcode_y = lower_start_y

            # Paste barcode onto label
            label.paste(barcode_resized, (barcode_x, barcode_y))

            # Add batch number text below barcode
            batch_text = f"Charge: {batch_number}"
            batch_y = barcode_y + barcode_resized.height + 10

            # Center the batch text within usable area
            try:
                bbox = draw.textbbox((0, 0), batch_text, font=normal_font)
                text_width = bbox[2] - bbox[0]
            except Exception:
                text_width = len(batch_text) * 12

            batch_x = padding_left + (usable_width - text_width) // 2
            draw.text(
                (batch_x, batch_y),
                batch_text,
                fill="black",
                font=normal_font,
            )

            # Add border around the entire label
            border_color = "black"
            border_width = 3
            draw.rectangle(
                [0, 0, label_width - 1, label_height - 1],
                outline=border_color,
                width=border_width,
            )

            # Save the complete label
            label.save(str(output_path), "PNG", dpi=(300, 300))
            logger.info(f"Custom label saved to: {output_path}")

            if output_path.exists():
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Custom label generation failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _generate_fallback_barcode(
        self,
        value: str,
        output_path: Path,
        filename_prefix: str,
        additional_data: Dict[str, Any],
    ) -> Optional[Path]:
        """Generate fallback barcode using PIL (text-based representation)."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create simple text-based barcode representation
            img_width, img_height = 400, 150
            img = Image.new("RGB", (img_width, img_height), "white")
            draw = ImageDraw.Draw(img)

            # Draw simple barcode-like pattern
            bar_width = 3
            x = 20
            for i, char in enumerate(value):
                # Create pattern based on character ASCII value
                pattern = ord(char) % 8
                for j in range(pattern + 1):
                    if j % 2 == 0:
                        draw.rectangle([x, 20, x + bar_width, 80], fill="black")
                    x += bar_width + 1

            # Add text below
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            text_y = 90
            draw.text((20, text_y), value, fill="black", font=font)
            draw.text(
                (20, text_y + 20),
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                fill="gray",
                font=font,
            )

            # Save image
            img.save(str(output_path), "PNG")
            if output_path.exists():
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Fallback barcode generation failed: {e}")
            return None

    def _sanitize_filename(self, value: str) -> str:
        """Sanitize value for use in filename."""
        # Remove or replace problematic characters
        safe_chars = []
        for char in value:
            if char.isalnum() or char in "-_":
                safe_chars.append(char)
            else:
                safe_chars.append("_")

        result = "".join(safe_chars)
        return result[:50]  # Limit length

    def _open_file(self, file_path: str):
        """Open file with default system application."""
        try:
            if platform.system() == "Windows":
                import os

                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                import subprocess

                subprocess.run(["open", file_path], check=False)
            else:  # Linux
                import subprocess

                subprocess.run(["xdg-open", file_path], check=False)
        except Exception as e:
            logger.warning(f"Could not open file: {e}")

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get barcode generation statistics."""
        success_rate = 0.0
        if self.stats["barcodes_generated"] > 0:
            success_rate = (
                self.stats["successful_generations"] / self.stats["barcodes_generated"]
            ) * 100

        return {
            "barcodes_generated": self.stats["barcodes_generated"],
            "successful_generations": self.stats["successful_generations"],
            "failed_generations": self.stats["failed_generations"],
            "success_rate": round(success_rate, 2),
            "total_generation_time": round(self.stats["total_generation_time"], 2),
            "barcode_library_available": self.barcode_available,
            "platform": platform.system(),
        }

    def validate_generation_capabilities(self) -> Dict[str, Any]:
        """Validate barcode generation capabilities."""
        try:
            validation_result = {
                "barcode_generation_ready": True,
                "barcode_library_available": (self.barcode_available),
                "fallback_available": True,  # PIL-based fallback
                "platform": platform.system(),
                "recommendations": [],
            }

            if not self.barcode_available:
                validation_result["recommendations"].append(
                    "Install python-barcode library"
                    " for best barcode quality:"
                    " pip install"
                    " python-barcode[images]"
                )

            # Test PIL availability for fallback
            try:
                from PIL import Image  # noqa: F401

                validation_result["pil_available"] = True
            except ImportError:
                validation_result["pil_available"] = False
                validation_result["fallback_available"] = False
                validation_result["recommendations"].append(
                    "Install Pillow for fallback"
                    " barcode generation:"
                    " pip install Pillow"
                )

            if (
                not validation_result["barcode_library_available"]
                and not validation_result["fallback_available"]
            ):
                validation_result["barcode_generation_ready"] = False
                validation_result["status"] = "not_ready"
            elif validation_result["barcode_library_available"]:
                validation_result["status"] = "ready"
            else:
                validation_result["status"] = "partial"  # Fallback only

            return validation_result

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_qr_code_for_article(self, article_number: str) -> Optional[Path]:
        r"""
        Suche QR-Code PNG basierend auf Artikelnummer.

        PRIMAER: Server-Pfad
        (\\10.190.140.10\Allgemein -
        Keyence Messprogramme Ordner)
        FALLBACK: Lokaler Pfad
        (~/Medealis/Wareneingang/
        QR-Codes Messprogramme)

        Args:
            article_number: Artikelnummer für QR-Code-Suche

        Returns:
            Path zum gefundenen QR-Code oder None
        """
        try:
            from ..document_storage.path_resolver import path_resolver

            # Liste von Pfaden zum Durchsuchen (Priorität: Server → Lokal)
            search_paths = []

            # PRIMÄR: Server-Pfad (wenn verfügbar)
            server_qr_path = path_resolver.server_qr_code_path
            if server_qr_path.exists():
                search_paths.append(("Server", server_qr_path))
                logger.info(
                    "QR-Code Suche: Server-Pfad" " verfuegbar: %s",
                    server_qr_path,
                )
            else:
                logger.warning(
                    "QR-Code Suche: Server-Pfad" " nicht verfuegbar: %s",
                    server_qr_path,
                )

            # FALLBACK: Lokaler Pfad
            local_qr_path = path_resolver.local_qr_code_path
            if local_qr_path.exists():
                search_paths.append(("Lokal", local_qr_path))
                logger.info(
                    "QR-Code Suche: Lokaler" " Fallback-Pfad verfuegbar: %s",
                    local_qr_path,
                )
            else:
                logger.warning(
                    "QR-Code Suche: Lokaler Pfad" " nicht verfuegbar: %s",
                    local_qr_path,
                )

            # Prüfe ob überhaupt ein Pfad verfügbar ist
            if not search_paths:
                logger.error(
                    "QR-Code Suche: Weder Server" " noch lokaler Pfad verfuegbar!"
                )
                return None

            # Durchsuche Pfade in Prioritätsreihenfolge
            for source_name, qr_base_path in search_paths:
                logger.info(
                    "QR-Code Suche: Durchsuche" " %s-Pfad: %s",
                    source_name,
                    qr_base_path,
                )

                # Suche nach Datei die mit Artikelnummer beginnt
                for qr_file in qr_base_path.glob(f"{article_number}*.png"):
                    logger.info(
                        "QR-Code gefunden (%s): %s",
                        source_name,
                        qr_file,
                    )
                    return qr_file

                # Fallback: Exakte Suche
                exact_match = qr_base_path / f"{article_number}.png"
                if exact_match.exists():
                    logger.info(
                        "QR-Code gefunden" " (exakt, %s): %s",
                        source_name,
                        exact_match,
                    )
                    return exact_match

                logger.debug(
                    "Kein QR-Code in %s-Pfad" " gefunden fuer: %s",
                    source_name,
                    article_number,
                )

            # Kein QR-Code in allen Pfaden gefunden
            logger.info(
                "Kein QR-Code gefunden fuer" " Artikel: %s (durchsuchte" " Pfade: %s)",
                article_number,
                len(search_paths),
            )
            return None

        except Exception as e:
            logger.error(f"Fehler bei QR-Code Suche: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None


# Global instance for easy access
barcode_generator = BarcodeGenerator()
