"""
Word Converter - DOCX to PDF Conversion Service

Erweitert die Document Generation um PDF-Konvertierung:
- DOCX zu PDF Konvertierung mit verschiedenen Engines
- Automatisches Speichern von DOCX + PDF
- Plattformspezifische Optimierungen (Windows win32com)
- Fallback-Systeme für maximale Kompatibilität
"""

import logging
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

# External dependencies (optional)
try:
    if platform.system() == "Windows":
        import win32com.client as win32
        import pythoncom
        WIN32_AVAILABLE = True
    else:
        WIN32_AVAILABLE = False
except ImportError:
    WIN32_AVAILABLE = False

try:
    from docx2pdf import convert as docx2pdf_convert
    DOCX2PDF_AVAILABLE = True
except ImportError:
    DOCX2PDF_AVAILABLE = False

try:
    import subprocess
    SUBPROCESS_AVAILABLE = True
except ImportError:
    SUBPROCESS_AVAILABLE = False

# Internal imports
from .generation_models import GenerationContext, GenerationResult
from .document_types import DocumentType, get_template_info
from .word_processor import WordProcessor

logger = logging.getLogger(__name__)


class ConversionResult:
    """
    Ergebnis einer PDF-Konvertierung.
    Standardisierte Rückgabe für alle Konvertierungs-Operationen.
    """

    def __init__(self, success: bool = False):
        self.success: bool = success
        self.docx_path: Optional[Path] = None
        self.pdf_path: Optional[Path] = None
        self.conversion_method: Optional[str] = None
        self.conversion_time: float = 0.0
        self.error: Optional[str] = None
        self.warnings: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def add_warning(self, warning: str):
        """Fügt Warnung hinzu."""
        self.warnings.append(warning)
        logger.warning(warning)

    def set_error(self, error: str):
        """Setzt Fehler und markiert als nicht erfolgreich."""
        self.error = error
        self.success = False
        logger.error(error)


class PDFConverter:
    """
    PDF-Konvertierungs-Engine mit mehreren Fallback-Methoden.

    Unterstützt verschiedene Konvertierungs-Engines:
    1. win32com (Windows, am stabilsten)
    2. docx2pdf (plattformunabhängig)
    3. LibreOffice subprocess (Fallback)
    """

    def __init__(self):
        """Initialize PDF Converter."""
        self.available_methods = self._detect_available_methods()

        # Conversion Statistics
        self.stats = {
            'conversions_attempted': 0,
            'conversions_successful': 0,
            'conversions_failed': 0,
            'methods_used': {},
            'total_conversion_time': 0.0
        }

        logger.info(f"PDFConverter initialized with methods: {list(self.available_methods.keys())}")

    def _detect_available_methods(self) -> Dict[str, bool]:
        """Erkennt verfügbare Konvertierungs-Methoden."""
        methods = {
            'win32com': WIN32_AVAILABLE,
            'docx2pdf': DOCX2PDF_AVAILABLE,
            'libreoffice': self._check_libreoffice_available(),
        }

        available_count = sum(1 for available in methods.values() if available)
        logger.info(f"PDF conversion methods available: {available_count}/3")

        if available_count == 0:
            logger.warning("No PDF conversion methods available - PDF generation will fail")

        return methods

    def _check_libreoffice_available(self) -> bool:
        """Prüft ob LibreOffice verfügbar ist."""
        if not SUBPROCESS_AVAILABLE:
            return False

        try:
            # Teste verschiedene LibreOffice Kommandos
            libreoffice_commands = ['libreoffice', 'soffice']

            for cmd in libreoffice_commands:
                try:
                    result = subprocess.run(
                        [cmd, '--version'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info(f"LibreOffice found: {cmd}")
                        return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            return False

        except Exception as e:
            logger.debug(f"LibreOffice detection failed: {e}")
            return False

    def convert_docx_to_pdf(
        self,
        docx_path: Union[str, Path],
        pdf_path: Optional[Union[str, Path]] = None,
        preferred_method: Optional[str] = None
    ) -> ConversionResult:
        """
        Konvertiert DOCX-Datei zu PDF.

        Args:
            docx_path: Pfad zur DOCX-Datei
            pdf_path: Gewünschter PDF-Pfad (optional)
            preferred_method: Bevorzugte Konvertierungs-Methode (optional)

        Returns:
            ConversionResult mit Erfolg/Fehler-Informationen
        """
        start_time = datetime.now()
        result = ConversionResult()

        try:
            # Path validation
            docx_path = Path(docx_path)
            if not docx_path.exists():
                raise FileNotFoundError(f"DOCX file not found: {docx_path}")

            result.docx_path = docx_path

            # Generate PDF path if not provided
            if pdf_path is None:
                pdf_path = docx_path.with_suffix('.pdf')
            else:
                pdf_path = Path(pdf_path)

            result.pdf_path = pdf_path

            # Ensure output directory exists
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            # Statistics
            self.stats['conversions_attempted'] += 1

            # Try conversion methods in order of preference
            conversion_methods = self._get_conversion_methods_order(preferred_method)

            for method_name in conversion_methods:
                if not self.available_methods.get(method_name, False):
                    continue

                logger.info(f"Attempting PDF conversion using {method_name}: {docx_path.name}")

                try:
                    if method_name == 'win32com':
                        self._convert_with_win32com(docx_path, pdf_path)
                    elif method_name == 'docx2pdf':
                        self._convert_with_docx2pdf(docx_path, pdf_path)
                    elif method_name == 'libreoffice':
                        self._convert_with_libreoffice(docx_path, pdf_path)
                    else:
                        continue

                    # Verify PDF was created
                    if pdf_path.exists() and pdf_path.stat().st_size > 0:
                        result.success = True
                        result.conversion_method = method_name

                        # Update statistics
                        self.stats['conversions_successful'] += 1
                        self.stats['methods_used'][method_name] = self.stats['methods_used'].get(method_name, 0) + 1

                        logger.info(f"PDF conversion successful with {method_name}: {pdf_path.name}")
                        break
                    else:
                        raise Exception(f"PDF file not created or empty: {pdf_path}")

                except Exception as method_error:
                    logger.warning(f"PDF conversion failed with {method_name}: {method_error}")
                    result.add_warning(f"{method_name} conversion failed: {str(method_error)}")
                    continue

            if not result.success:
                error_msg = f"All PDF conversion methods failed for {docx_path.name}"
                result.set_error(error_msg)
                self.stats['conversions_failed'] += 1

            # Final timing
            end_time = datetime.now()
            result.conversion_time = (end_time - start_time).total_seconds()
            self.stats['total_conversion_time'] += result.conversion_time

            # Metadata
            result.metadata.update({
                'docx_size': docx_path.stat().st_size if docx_path.exists() else 0,
                'pdf_size': pdf_path.stat().st_size if result.success else 0,
                'available_methods': list(self.available_methods.keys()),
                'attempted_methods': [m for m in conversion_methods if self.available_methods.get(m, False)],
                'platform': platform.system()
            })

            return result

        except Exception as e:
            error_msg = f"PDF conversion error: {str(e)}"
            result.set_error(error_msg)

            end_time = datetime.now()
            result.conversion_time = (end_time - start_time).total_seconds()
            self.stats['conversions_failed'] += 1

            return result

    def _get_conversion_methods_order(self, preferred_method: Optional[str] = None) -> List[str]:
        """Gibt Reihenfolge der zu versuchenden Konvertierungs-Methoden zurück."""
        default_order = ['win32com', 'docx2pdf', 'libreoffice']  # Windows-optimiert

        if preferred_method and preferred_method in default_order:
            # Preferred method first, then others
            ordered = [preferred_method]
            ordered.extend([m for m in default_order if m != preferred_method])
            return ordered

        return default_order

    def _convert_with_win32com(self, docx_path: Path, pdf_path: Path, retry_count: int = 3):
        """Konvertierung mit win32com (Windows, am stabilsten)."""
        if not WIN32_AVAILABLE:
            raise ImportError("win32com not available")

        import time
        import pywintypes

        last_error = None

        for attempt in range(retry_count):
            word_app = None
            doc = None

            try:
                # COM für diesen Thread initialisieren
                try:
                    pythoncom.CoInitialize()
                except:
                    pass  # Already initialized

                # Bei Retry: Warte kurz bevor neuer Versuch
                if attempt > 0:
                    wait_time = attempt * 1.0  # 1s, 2s, 3s
                    logger.info(f"Retry {attempt}/{retry_count-1} after {wait_time}s wait...")
                    time.sleep(wait_time)

                # Word Application öffnen - verwende DispatchEx für neue Instanz
                word_app = win32.DispatchEx('Word.Application')
                word_app.Visible = False  # Unsichtbar
                word_app.DisplayAlerts = 0  # Keine Dialoge

                # Dokument öffnen (mit absoluten Pfaden)
                abs_docx_path = str(docx_path.resolve())
                abs_pdf_path = str(pdf_path.resolve())

                doc = word_app.Documents.Open(
                    abs_docx_path,
                    ReadOnly=True,
                    ConfirmConversions=False,
                    AddToRecentFiles=False
                )

                # Als PDF speichern (FileFormat=17 = PDF)
                doc.SaveAs(abs_pdf_path, FileFormat=17)

                # Dokument schließen
                doc.Close(SaveChanges=False)
                doc = None

                logger.debug(f"win32com conversion successful: {pdf_path.name}")
                return  # Erfolg!

            except pywintypes.com_error as e:
                last_error = e
                error_code = e.args[0] if e.args else None

                # RPC_E_CALL_REJECTED = -2147418111 oder RPC_E_SERVERCALL_RETRYLATER = -2147417846
                if error_code in [-2147418111, -2147417846]:
                    logger.warning(f"Word busy (attempt {attempt + 1}/{retry_count}), will retry...")
                    # Cleanup und retry
                else:
                    # Anderer Fehler - nicht retry-bar
                    raise Exception(f"win32com conversion failed: {str(e)}")

            except Exception as e:
                last_error = e
                raise Exception(f"win32com conversion failed: {str(e)}")

            finally:
                # Dokument sicher schließen
                if doc:
                    try:
                        doc.Close(SaveChanges=False)
                    except:
                        pass

                # Word Application sicher schließen
                if word_app:
                    try:
                        word_app.Quit()
                    except:
                        pass

                    # Explizit freigeben
                    try:
                        del word_app
                    except:
                        pass

                # COM wieder freigeben
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass

        # Alle Retries fehlgeschlagen
        raise Exception(f"win32com conversion failed after {retry_count} attempts: {str(last_error)}")

    def _convert_with_docx2pdf(self, docx_path: Path, pdf_path: Path):
        """Konvertierung mit docx2pdf library."""
        if not DOCX2PDF_AVAILABLE:
            raise ImportError("docx2pdf not available")

        try:
            # COM initialisieren für docx2pdf (verwendet intern auch COM)
            if WIN32_AVAILABLE:
                pythoncom.CoInitialize()

            docx2pdf_convert(str(docx_path), str(pdf_path))
            logger.debug(f"docx2pdf conversion successful: {pdf_path.name}")

        except Exception as e:
            raise Exception(f"docx2pdf conversion failed: {str(e)}")

        finally:
            # COM wieder freigeben
            if WIN32_AVAILABLE:
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass

    def _convert_with_libreoffice(self, docx_path: Path, pdf_path: Path):
        """Konvertierung mit LibreOffice subprocess."""
        if not SUBPROCESS_AVAILABLE:
            raise ImportError("subprocess not available")

        try:
            # LibreOffice command
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(pdf_path.parent),
                str(docx_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                raise Exception(f"LibreOffice process failed: {result.stderr}")

            # LibreOffice might create PDF with different name
            expected_pdf = pdf_path.parent / f"{docx_path.stem}.pdf"
            if expected_pdf.exists() and expected_pdf != pdf_path:
                expected_pdf.rename(pdf_path)

            logger.debug(f"LibreOffice conversion successful: {pdf_path.name}")

        except subprocess.TimeoutExpired:
            raise Exception("LibreOffice conversion timed out")
        except Exception as e:
            raise Exception(f"LibreOffice conversion failed: {str(e)}")

    def get_conversion_statistics(self) -> Dict[str, Any]:
        """Gibt Konvertierungs-Statistiken zurück."""
        success_rate = 0.0
        if self.stats['conversions_attempted'] > 0:
            success_rate = (self.stats['conversions_successful'] / self.stats['conversions_attempted']) * 100

        return {
            'conversions_attempted': self.stats['conversions_attempted'],
            'conversions_successful': self.stats['conversions_successful'],
            'conversions_failed': self.stats['conversions_failed'],
            'success_rate': round(success_rate, 2),
            'methods_used': self.stats['methods_used'],
            'total_conversion_time': round(self.stats['total_conversion_time'], 2),
            'available_methods': {k: v for k, v in self.available_methods.items() if v},
            'platform': platform.system()
        }


class WordConverter:
    """
    Enhanced Word Processor mit PDF-Konvertierung.

    Erweitert den Standard WordProcessor um automatische PDF-Generation:
    - Generiert DOCX-Dokumente wie gewohnt
    - Konvertiert automatisch zu PDF (optional)
    - Speichert beide Formate im gleichen Ordner
    - Verwaltet Dateinamen und Pfade konsistent
    """

    def __init__(self, template_base_dir: Optional[Path] = None):
        """
        Initialize Word Converter.

        Args:
            template_base_dir: Basis-Verzeichnis für Templates (optional)
        """
        # Core Components
        self.word_processor = WordProcessor(template_base_dir)
        self.pdf_converter = PDFConverter()

        # Service Statistics
        self.stats = {
            'documents_generated': 0,
            'pdfs_generated': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'total_processing_time': 0.0
        }

        logger.info("WordConverter initialized with PDF conversion support")

    def generate_document(
        self,
        context: GenerationContext,
        output_path: Optional[Path] = None,
        generate_pdf: bool = True,
        preferred_pdf_method: Optional[str] = None
    ) -> GenerationResult:
        """
        Generiert DOCX-Dokument und optional PDF aus GenerationContext.

        Args:
            context: Generation Context mit allen Daten
            output_path: Ausgabepfad für DOCX (optional)
            generate_pdf: Ob PDF zusätzlich erstellt werden soll
            preferred_pdf_method: Bevorzugte PDF-Konvertierungs-Methode

        Returns:
            GenerationResult erweitert um PDF-Informationen
        """
        start_time = datetime.now()

        try:
            # 1. Standard DOCX-Generation
            logger.info(f"Generating DOCX document for {context.document_type.value if context.document_type else 'unknown'}")
            docx_result = self.word_processor.generate_document(context, output_path)

            # Update statistics
            self.stats['documents_generated'] += 1

            if not docx_result.success:
                self.stats['failed_generations'] += 1
                return docx_result

            # 2. PDF-Konvertierung (falls gewünscht)
            if generate_pdf:
                logger.info(f"Converting to PDF: {docx_result.document_path.name}")

                # FIXED: PDF soll in denselben Ordner wie DOCX gespeichert werden
                pdf_output_path = docx_result.document_path.with_suffix('.pdf')

                pdf_conversion = self.pdf_converter.convert_docx_to_pdf(
                    docx_result.document_path,
                    pdf_path=pdf_output_path,
                    preferred_method=preferred_pdf_method
                )

                # Erweitere GenerationResult um PDF-Informationen
                if pdf_conversion.success:
                    docx_result.pdf_path = pdf_conversion.pdf_path
                    docx_result.conversion_method = pdf_conversion.conversion_method
                    docx_result.pdf_conversion_time = pdf_conversion.conversion_time

                    self.stats['pdfs_generated'] += 1

                    logger.info(f"PDF generated successfully in same folder: {pdf_conversion.pdf_path.name}")

                    # AUTO-OPEN: Öffne PDF automatisch für Druck
                    try:
                        from warehouse.application.services.document_operations import document_opening_service
                        open_result = document_opening_service.open_after_generation(
                            pdf_conversion.pdf_path,
                            document_type="pdf"
                        )
                        if open_result["opened"] > 0:
                            logger.info(f"📂 Auto-opened PDF: {pdf_conversion.pdf_path.name}")
                        elif open_result["skipped"] > 0:
                            logger.debug(f"Auto-open skipped: {open_result.get('reason', 'Unknown')}")
                    except Exception as e:
                        logger.warning(f"Auto-open failed (non-critical): {e}")

                    # Add PDF info to metadata
                    docx_result.metadata.update({
                        'pdf_generated': True,
                        'pdf_path': str(pdf_conversion.pdf_path),
                        'pdf_conversion_method': pdf_conversion.conversion_method,
                        'pdf_conversion_time': pdf_conversion.conversion_time,
                        'pdf_size': pdf_conversion.pdf_path.stat().st_size if pdf_conversion.pdf_path.exists() else 0
                    })
                else:
                    # PDF conversion failed - add warnings but don't fail overall
                    docx_result.add_warning(f"PDF conversion failed: {pdf_conversion.error}")
                    for warning in pdf_conversion.warnings:
                        docx_result.add_warning(warning)

                    docx_result.metadata.update({
                        'pdf_generated': False,
                        'pdf_error': pdf_conversion.error
                    })

            # Success statistics
            self.stats['successful_generations'] += 1

            # Total timing
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            self.stats['total_processing_time'] += total_time

            # Update result with total time
            if hasattr(docx_result, 'pdf_conversion_time'):
                docx_result.metadata['total_generation_time'] = total_time

            return docx_result

        except Exception as e:
            error_msg = f"WordConverter generation failed: {str(e)}"
            logger.error(error_msg)

            # Create error result
            error_result = GenerationResult(success=False)
            error_result.set_error(error_msg)
            error_result.document_type = context.document_type

            self.stats['documents_generated'] += 1
            self.stats['failed_generations'] += 1

            return error_result

    def generate_batch_documents(
        self,
        contexts: List[GenerationContext],
        output_base_path: Optional[Path] = None,
        generate_pdf: bool = True
    ) -> List[GenerationResult]:
        """
        Generiert mehrere Dokumente mit PDF-Konvertierung in einem Batch.

        Args:
            contexts: Liste von GenerationContexts
            output_base_path: Basis-Pfad für Ausgabe (optional)
            generate_pdf: Ob PDFs zusätzlich erstellt werden sollen

        Returns:
            Liste von GenerationResults
        """
        results = []

        try:
            logger.info(f"Starting batch generation of {len(contexts)} documents (PDF: {generate_pdf})")

            for i, context in enumerate(contexts, 1):
                logger.info(f"Processing document {i}/{len(contexts)}: {context.document_type.value if context.document_type else 'unknown'}")

                # Output path für dieses Dokument
                document_output_path = None
                if output_base_path:
                    filename = self.word_processor._generate_filename(context)
                    document_output_path = output_base_path / filename

                # Einzelnes Dokument mit PDF generieren
                result = self.generate_document(
                    context,
                    document_output_path,
                    generate_pdf=generate_pdf
                )
                results.append(result)

                # Log Zwischenergebnis
                if result.success:
                    pdf_info = f" + PDF" if hasattr(result, 'pdf_path') and result.pdf_path else ""
                    logger.debug(f"Document {i} generated successfully: DOCX{pdf_info}")
                else:
                    logger.warning(f"Document {i} generation failed: {result.error}")

            successful_count = sum(1 for r in results if r.success)
            pdf_count = sum(1 for r in results if hasattr(r, 'pdf_path') and r.pdf_path)

            logger.info(f"Batch generation completed: {successful_count}/{len(results)} documents successful, {pdf_count} PDFs created")

            return results

        except Exception as e:
            error_msg = f"Batch generation failed: {e}"
            logger.error(error_msg)

            # Return error result for any remaining contexts
            for context in contexts[len(results):]:
                error_result = GenerationResult(success=False)
                error_result.set_error(error_msg)
                error_result.document_type = context.document_type
                results.append(error_result)

            return results

    def get_converter_statistics(self) -> Dict[str, Any]:
        """Gibt vollständige WordConverter Statistiken zurück."""
        return {
            'word_converter_stats': self.stats,
            'word_processor_stats': self.word_processor.get_word_processor_statistics(),
            'pdf_converter_stats': self.pdf_converter.get_conversion_statistics()
        }

    def validate_conversion_capabilities(self) -> Dict[str, Any]:
        """Validiert WordConverter Funktionen."""
        try:
            # Word Processor Validation
            word_validation = self.word_processor.validate_processing_capabilities()

            # PDF Converter Validation
            pdf_methods = self.pdf_converter.available_methods
            pdf_available = any(pdf_methods.values())

            validation_result = {
                'word_processing_ready': word_validation.get('docx_available', False),
                'pdf_conversion_ready': pdf_available,
                'available_pdf_methods': [k for k, v in pdf_methods.items() if v],
                'word_processor_validation': word_validation,
                'pdf_converter_methods': pdf_methods,
                'overall_ready': word_validation.get('docx_available', False),  # DOCX is minimum requirement
                'platform': platform.system(),
                'recommendations': []
            }

            # Add recommendations
            if not pdf_available:
                validation_result['recommendations'].append(
                    "Install win32com (pywin32) for best PDF conversion on Windows"
                )

            if validation_result['overall_ready'] and pdf_available:
                validation_result['status'] = 'ready'
            elif validation_result['overall_ready']:
                validation_result['status'] = 'partial'  # DOCX only
                validation_result['recommendations'].append(
                    "PDF conversion not available - DOCX generation only"
                )
            else:
                validation_result['status'] = 'not_ready'

            return validation_result

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# Global instance - SINGLE POINT OF ACCESS
# Ermöglicht einheitliche DOCX + PDF Generation im gesamten System
word_converter = WordConverter()