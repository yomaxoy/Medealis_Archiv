"""
Application Processors für Datenverarbeitung.

Prozessoren für verschiedene Datenquellen und -formate.

MIGRATION NOTICE:
- claude_processor und pdf_processor wurden in document_processing_service integriert
- Für Rückwärtskompatibilität werden Wrapper bereitgestellt
"""

from .data_validator import DataValidator, data_validator
from .ocr_processor import OCRProcessor, ocr_processor

# Import new services and create compatibility wrappers
try:
    from ..services.document_processing.document_processing_service import document_processing_service

    # Compatibility wrapper for claude_processor
    class ClaudeProcessorWrapper:
        """Compatibility wrapper für alten claude_processor Import."""

        def __init__(self):
            self.service = document_processing_service

        def is_available(self):
            return self.service.is_available()

        def extract_delivery_data_from_text(self, ocr_text: str):
            # Old API: extract_delivery_data_from_text(ocr_text)
            # New API: process_document(document_data, document_type, context)
            try:
                import tempfile
                # Save text as temporary PDF for processing
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(ocr_text)
                    temp_file_path = temp_file.name

                # Read as bytes for new API
                with open(temp_file_path, 'rb') as f:
                    document_data = f.read()

                result = self.service.process_document(
                    document_data=document_data,
                    document_type='delivery',
                    context={}
                )

                # Cleanup temp file
                import os
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

                # Extract the delivery data from new result format
                if result and result.get('success', False) != False:
                    # Return the structured data directly - new service already returns structured format
                    return result
                return None
            except Exception as e:
                print(f"Error in compatibility wrapper: {e}")
                return None

        def get_status_info(self):
            return self.service.get_status()

    # Create wrapper instance
    ClaudeProcessor = ClaudeProcessorWrapper
    claude_processor = ClaudeProcessorWrapper()

except ImportError as e:
    print(f"Warning: Could not import new document processing service: {e}")
    # Fallback - create dummy classes
    class ClaudeProcessor:
        def is_available(self): return False
        def extract_delivery_data_from_text(self, text): return None
        def get_status_info(self): return {'error': 'Service not available'}

    claude_processor = ClaudeProcessor()

# PDF Processor compatibility wrapper
try:
    # Simple PDF processing can still use the existing file if it exists
    from .pdf_processor import PDFProcessor, pdf_processor
except ImportError:
    # Create dummy if not available
    class PDFProcessor:
        def extract_text_from_pdf(self, file_path): return ""
        def extract_text_from_docx(self, file_path): return ""

    pdf_processor = PDFProcessor()

__all__ = [
    "ClaudeProcessor",
    "claude_processor",
    "DataValidator",
    "data_validator",
    "OCRProcessor",
    "ocr_processor",
    "PDFProcessor",
    "pdf_processor"
]