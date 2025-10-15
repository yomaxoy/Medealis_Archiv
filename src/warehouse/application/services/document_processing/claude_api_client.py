"""
Claude API Client - Vereinheitlichter Client für alle Dokumenttypen
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from config.settings import settings
except ImportError:
    # Fallback wie im Original
    import os
    from pathlib import Path
    import sys

    project_root = Path(__file__).parent.parent.parent.parent
    config_path = project_root / "config"
    sys.path.insert(0, str(config_path))

    try:
        from settings import settings
    except ImportError:
        class FallbackSettings:
            ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        settings = FallbackSettings()


class ClaudeAPIClient:
    """
    Vereinheitlichter Claude API Client.
    """

    def __init__(self):
        self.client = None
        self.primary_model = "claude-sonnet-4-20250514"
        # Fallback-Modelle aus dem Original übernommen
        self.fallback_models = [
            "claude-3-5-sonnet-20250106",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        self._initialize_client()

    def _initialize_client(self):
        """Initialisiert Anthropic Client - kopiert aus Original."""
        try:
            api_key = (
                os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
                if hasattr(settings, "ANTHROPIC_API_KEY")
                else None
            )
            if api_key and ANTHROPIC_AVAILABLE:
                self.client = Anthropic(api_key=api_key)
                logger.info("Claude API Client initialized successfully")
            else:
                logger.warning("No Anthropic API key found or anthropic library not available")
        except Exception as e:
            logger.error(f"Claude client initialization failed: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Prüft ob Claude Service verfügbar ist."""
        return self.client is not None and ANTHROPIC_AVAILABLE

    def analyze_document(
        self,
        document_path: str,
        prompt: str,
        debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Einheitlicher Claude API Call - basiert auf _call_claude_api aus Original.

        Args:
            document_path: Pfad zum temporären Dokument
            prompt: Vollständiger Prompt
            debug: Debug-Ausgaben

        Returns:
            Geparste JSON-Response
        """
        if not self.is_available():
            logger.error("Claude client not available")
            return None

        try:
            # Read document data
            with open(document_path, 'rb') as f:
                document_data = f.read()

            if debug:
                logger.info(f"📤 Claude API call started - Document: {Path(document_path).name}")

            # Determine media type - aus Original übernommen
            media_type = self._get_media_type_from_data(document_data, document_path)

            if debug:
                logger.info(f"📄 Detected media type: {media_type}")

            # Create message with document - Format aus Original
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.b64encode(document_data).decode('utf-8')
                        }
                    }
                ]
            }

            # Call Claude API with fallback models - Logik aus Original
            response = None
            models_to_try = [self.primary_model] + self.fallback_models

            for model in models_to_try:
                try:
                    if debug:
                        logger.info(f"📤 Trying model: {model}")

                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[message]
                    )

                    if debug:
                        logger.info(f"✅ Success with model: {model}")
                    break

                except Exception as e:
                    if "not_found_error" in str(e):
                        if debug:
                            logger.warning(f"❌ Model {model} not available")
                        continue
                    else:
                        # Other error, re-raise
                        raise e

            if not response:
                raise Exception("All models failed - no available Claude models")

            # Extract and parse response - aus Original übernommen
            response_text = response.content[0].text

            if debug:
                logger.info(f"📥 RAW RESPONSE ({len(response_text)} chars):")
                logger.info(response_text[:500] + "..." if len(response_text) > 500 else response_text)

            # Clean and parse JSON - Methode aus Original
            parsed_data = self._clean_and_parse_response(response_text, debug)

            if parsed_data:
                if debug:
                    logger.info("✅ JSON successfully parsed!")
                return parsed_data
            else:
                if debug:
                    logger.error("❌ Failed to parse JSON response")
                return None

        except Exception as e:
            logger.error(f"Error in Claude API call: {e}")
            if debug:
                logger.error(f"❌ CLAUDE API ERROR: {e}")
            return None

    def _get_media_type_from_data(self, document_data: bytes, file_path: str = None) -> str:
        """
        Bestimmt Media-Type - aus Original übernommen.
        """
        # Check file extension if path provided
        if file_path:
            file_path_lower = file_path.lower()
            if file_path_lower.endswith('.pdf'):
                return "application/pdf"
            elif file_path_lower.endswith('.docx'):
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_path_lower.endswith('.doc'):
                return "application/msword"
            elif file_path_lower.endswith('.txt'):
                return "text/plain"

        # Check magic bytes for common formats - aus Original
        if document_data.startswith(b'%PDF'):
            return "application/pdf"
        elif document_data.startswith(b'PK'):  # ZIP-based formats like DOCX
            if b'word/' in document_data[:1024]:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        # Default fallback
        return "application/pdf"

    def _clean_and_parse_response(self, response_text: str, debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        JSON Response bereinigen und parsen - aus Original übernommen und vereinfacht.
        """
        try:
            # Remove code blocks - aus Original
            cleaned_text = response_text.strip()

            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]

            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            if debug:
                logger.info(f"🧹 Cleaned response: {len(cleaned_text)} chars")

            # Parse JSON
            return json.loads(cleaned_text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {e}")
            return None


# Global instance
claude_api_client = ClaudeAPIClient()