"""
OCR Client - Infrastructure Layer
Low-level OCR integration with Tesseract and image processing.
"""

import os
import logging
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class OCRClient:
    """Low-level OCR client for infrastructure layer."""
    
    def __init__(self):
        """Initialize OCR client and configure Tesseract."""
        self.tesseract_available = self._configure_tesseract()
        self.dependencies_available = self._check_dependencies()
        
    def _configure_tesseract(self) -> bool:
        """Configure Tesseract path for Windows."""
        try:
            import pytesseract
            
            if platform.system() == 'Windows':
                # Common Tesseract installation paths on Windows
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(
                        os.getenv('USERNAME', '')
                    ),
                    r'C:\tools\tesseract\tesseract.exe'
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Tesseract configured at: {path}")
                        break
            
            # Test if Tesseract is working
            pytesseract.get_tesseract_version()
            return True
            
        except (ImportError, Exception) as e:
            logger.warning(f"Tesseract configuration failed: {e}")
            return False
    
    def _check_dependencies(self) -> Dict[str, bool]:
        """Check availability of all OCR dependencies."""
        dependencies = {}
        
        try:
            import pytesseract
            dependencies['pytesseract'] = True
        except ImportError:
            dependencies['pytesseract'] = False
        
        try:
            from PIL import Image
            dependencies['pillow'] = True
        except ImportError:
            dependencies['pillow'] = False
        
        try:
            import cv2
            dependencies['opencv'] = True
        except ImportError:
            dependencies['opencv'] = False
        
        try:
            import numpy as np
            dependencies['numpy'] = True
        except ImportError:
            dependencies['numpy'] = False
        
        try:
            from pdf2image import convert_from_path
            dependencies['pdf2image'] = True
        except ImportError:
            dependencies['pdf2image'] = False
        
        return dependencies
    
    def is_available(self) -> bool:
        """Check if OCR is fully available."""
        required_deps = ['pytesseract', 'pillow']
        available_deps = [dep for dep, available in self.dependencies_available.items() if available]
        
        return (self.tesseract_available and 
                all(dep in available_deps for dep in required_deps))
    
    def extract_text_from_image(self, image_path: str, language: str = "deu") -> Optional[str]:
        """Extract text from image file using OCR."""
        if not self.is_available():
            logger.error("OCR not available")
            return None
        
        try:
            import pytesseract
            from PIL import Image
            
            # Load and process image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=language)
            logger.info(f"OCR extracted {len(text)} characters from image")
            
            return text
            
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return None
    
    def extract_text_from_pdf_pages(self, pdf_path: str, language: str = "deu") -> Optional[str]:
        """Extract text from PDF using OCR (convert to images first)."""
        if not self.is_available():
            logger.error("OCR not available")
            return None
        
        if not self.dependencies_available.get('pdf2image', False):
            logger.error("pdf2image not available for PDF OCR")
            return None
        
        try:
            import pytesseract
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            extracted_texts = []
            
            for i, image in enumerate(images):
                logger.info(f"Processing PDF page {i+1}/{len(images)} with OCR")
                
                # Extract text from this page
                text = pytesseract.image_to_string(image, lang=language)
                if text.strip():
                    extracted_texts.append(text)
                    logger.debug(f"Page {i+1}: Extracted {len(text)} characters")
                else:
                    logger.warning(f"Page {i+1}: No text found")
            
            # Combine all page texts
            combined_text = "\n\n--- PAGE BREAK ---\n\n".join(extracted_texts)
            logger.info(f"PDF OCR extracted {len(combined_text)} characters from {len(images)} pages")
            
            return combined_text if combined_text.strip() else None
            
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return None
    
    def enhance_image_for_ocr(self, image_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Enhance image quality for better OCR results."""
        if not self.dependencies_available.get('opencv', False):
            logger.warning("OpenCV not available for image enhancement")
            return image_path  # Return original path
        
        try:
            import cv2
            import numpy as np
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding for better text contrast
            adaptive_thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Save enhanced image
            if output_path is None:
                # Create temp file for enhanced image
                import tempfile
                output_path = tempfile.mktemp(suffix='.png')
            
            cv2.imwrite(output_path, adaptive_thresh)
            logger.debug(f"Enhanced image saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {e}")
            return image_path  # Return original path on failure
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported OCR languages."""
        if not self.is_available():
            return []
        
        try:
            import pytesseract
            languages = pytesseract.get_languages(config='')
            return languages
        except Exception as e:
            logger.error(f"Could not get supported languages: {e}")
            return ['eng', 'deu']  # Default fallback
    
    def get_tesseract_info(self) -> Dict[str, Any]:
        """Get Tesseract version and configuration info."""
        if not self.tesseract_available:
            return {"available": False, "error": "Tesseract not found"}
        
        try:
            import pytesseract
            
            version = pytesseract.get_tesseract_version()
            tesseract_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', 'tesseract')
            languages = self.get_supported_languages()
            
            return {
                "available": True,
                "version": str(version),
                "path": tesseract_cmd,
                "supported_languages": languages,
                "language_count": len(languages)
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive OCR client status."""
        return {
            "tesseract_available": self.tesseract_available,
            "is_available": self.is_available(),
            "dependencies": self.dependencies_available,
            "tesseract_info": self.get_tesseract_info(),
            "supported_languages": self.get_supported_languages()
        }


# Global instance
ocr_client = OCRClient()