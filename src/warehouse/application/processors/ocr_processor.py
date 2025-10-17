"""
OCR Processing Module - Application Layer  
Handles OCR text extraction with quality enhancement.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handles OCR text extraction with Tesseract."""
    
    def __init__(self):
        """Initialize OCR processor and check dependencies."""
        self.available_languages = ['eng']  # Default fallback
        self.ocr_available = self._check_ocr_availability()
        
    def _check_ocr_availability(self) -> bool:
        """Check if OCR libraries and tesseract are available."""
        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np
            import os

            # Set Tesseract path for Windows
            # Check .env file first, then fallback to standard locations
            tesseract_paths = []

            # Try environment variable from .env file first
            env_tesseract_path = os.getenv('TESSERACT_PATH')
            if env_tesseract_path:
                tesseract_paths.append(env_tesseract_path)

            # Add standard locations as fallback
            tesseract_paths.extend([
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ])

            tesseract_dir = None
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_dir = os.path.dirname(path)
                    logger.info(f"Tesseract path set to: {path}")
                    break
            else:
                logger.warning("Tesseract executable not found in standard locations")
                return False

            # Set TESSDATA_PREFIX environment variable
            if tesseract_dir:
                tessdata_path = os.path.join(tesseract_dir, 'tessdata')
                if os.path.exists(tessdata_path):
                    # TESSDATA_PREFIX should point to tessdata directory itself
                    os.environ['TESSDATA_PREFIX'] = tessdata_path + os.path.sep
                    logger.info(f"TESSDATA_PREFIX set to: {tessdata_path + os.path.sep}")
                else:
                    logger.warning(f"tessdata directory not found at: {tessdata_path}")
                    # Try alternative - sometimes tessdata is in parent directory
                    parent_tessdata = os.path.join(os.path.dirname(tesseract_dir), 'tessdata')
                    if os.path.exists(parent_tessdata):
                        os.environ['TESSDATA_PREFIX'] = parent_tessdata + os.path.sep
                        logger.info(f"TESSDATA_PREFIX set to alternative: {parent_tessdata + os.path.sep}")
                    else:
                        logger.warning(f"Alternative tessdata directory not found at: {parent_tessdata}")

            # Test if tesseract binary is available and check languages
            version = pytesseract.get_tesseract_version()
            logger.info(f"OCR available: Tesseract found (version: {version})")

            # Check available languages
            try:
                languages = pytesseract.get_languages()
                logger.info(f"Available languages: {languages}")
                self.available_languages = languages
            except Exception as e:
                logger.warning(f"Could not get available languages: {e}")
                self.available_languages = ['eng']  # Default fallback

            return True
        except (ImportError, Exception) as e:
            logger.warning(f"OCR not available: {e}")
            return False
    
    def is_ocr_available(self) -> bool:
        """Check if OCR is available."""
        return self.ocr_available

    def _resolve_language(self, requested_language: str) -> str:
        """Resolve the best available language for OCR."""
        if not hasattr(self, 'available_languages'):
            return 'eng'  # Fallback if not initialized

        # If requested language is available, use it
        if requested_language in self.available_languages:
            return requested_language

        # Fallback logic
        if requested_language == 'deu' and 'eng' in self.available_languages:
            logger.warning("German (deu) not available, falling back to English (eng)")
            return 'eng'
        elif requested_language == 'deu+eng':
            # Try combined, then individual languages
            if 'deu+eng' in self.available_languages:
                return 'deu+eng'
            elif 'eng' in self.available_languages:
                logger.warning("Combined deu+eng not available, falling back to English (eng)")
                return 'eng'

        # Default fallback
        if 'eng' in self.available_languages:
            logger.warning(f"Language {requested_language} not available, falling back to English (eng)")
            return 'eng'

        # Use first available language
        if self.available_languages:
            fallback = self.available_languages[0]
            logger.warning(f"Language {requested_language} not available, using {fallback}")
            return fallback

        # Last resort
        return 'eng'
    
    def extract_text_with_ocr(self, file_path: str, language: str = "deu", enhance_quality: bool = True) -> str:
        """Extract text from image/PDF files using OCR."""
        if not self.ocr_available:
            logger.error("OCR not available - Tesseract not found")
            return self._get_fallback_text()

        # Resolve the best available language
        resolved_language = self._resolve_language(language)
        if resolved_language != language:
            logger.info(f"Using language: {resolved_language} (requested: {language})")

        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np

            file_path = Path(file_path)

            # For PDF files, convert to images first
            if file_path.suffix.lower() == '.pdf':
                return self._extract_from_pdf_with_ocr(file_path, resolved_language, enhance_quality)

            # For image files, process directly
            elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                return self._extract_from_image(file_path, resolved_language, enhance_quality)

            else:
                logger.warning(f"Unsupported file type for OCR: {file_path.suffix}")
                return ""

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def _extract_from_pdf_with_ocr(self, pdf_path: Path, language: str, enhance_quality: bool) -> str:
        """Extract text from PDF using OCR after converting to images."""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            extracted_texts = []
            
            for i, image in enumerate(images):
                logger.info(f"Processing PDF page {i+1}/{len(images)} with OCR")
                
                if enhance_quality:
                    image = self._enhance_image_quality(image)
                
                # Extract text using OCR
                text = pytesseract.image_to_string(image, lang=language)
                if text.strip():
                    extracted_texts.append(text)
                    logger.info(f"Page {i+1}: Extracted {len(text)} characters")
                else:
                    logger.warning(f"Page {i+1}: No text found")
            
            combined_text = "\n\n--- PAGE BREAK ---\n\n".join(extracted_texts)
            logger.info(f"Total OCR extraction: {len(combined_text)} characters from {len(images)} pages")
            return combined_text
            
        except ImportError:
            logger.error("pdf2image not available for PDF OCR processing")
            return ""
        except Exception as e:
            logger.error(f"PDF OCR processing failed: {e}")
            return ""
    
    def _extract_from_image(self, image_path: Path, language: str, enhance_quality: bool) -> str:
        """Extract text from image file using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            # Load image
            image = Image.open(image_path)
            
            if enhance_quality:
                image = self._enhance_image_quality(image)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image, lang=language)
            logger.info(f"Image OCR extracted: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Image OCR processing failed: {e}")
            return ""
    
    def _enhance_image_quality(self, image):
        """Enhance image quality for better OCR results."""
        try:
            import cv2
            import numpy as np
            from PIL import Image
            
            # Convert PIL Image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding for better text contrast
            adaptive_thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL Image
            enhanced_image = Image.fromarray(adaptive_thresh)
            logger.debug("Image quality enhanced for OCR")
            return enhanced_image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed, using original: {e}")
            return image
    
    def _get_fallback_text(self) -> str:
        """Return fallback demo text when OCR is not available."""
        return """
        LIEFERSCHEIN Nr. LS-2024-001
        
        Lieferant: Primec
        Datum: 2024-12-01
        
        Artikel:    Menge:
        A0001       10 Stück
        A0002       5 Stück
        
        Chargennummer: P-123456789012-1234
        """
    
    def get_ocr_status_info(self) -> Dict[str, Any]:
        """Get detailed OCR status information."""
        status = {
            "ocr_available": self.ocr_available,
            "tesseract_found": False,
            "required_packages": ["pytesseract", "PIL", "cv2", "numpy", "pdf2image"],
            "missing_packages": []
        }
        
        if self.ocr_available:
            try:
                import pytesseract
                version = pytesseract.get_tesseract_version()
                status["tesseract_found"] = True
                status["tesseract_version"] = str(version)
                status["tesseract_path"] = pytesseract.pytesseract.tesseract_cmd
            except:
                pass
        
        # Check which packages are missing
        for package in status["required_packages"]:
            try:
                __import__(package)
            except ImportError:
                status["missing_packages"].append(package)
        
        return status


# Global instance
ocr_processor = OCRProcessor()