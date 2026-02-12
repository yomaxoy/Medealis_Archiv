"""
Claude API Client - Backward-kompatibler Wrapper.

Delegiert an die neue ai_service-Abstraktionsschicht wenn verfuegbar,
faellt auf die bisherige Implementierung zurueck wenn nicht.

Bestehende Imports bleiben funktionsfaehig:
    from .claude_api_client import ClaudeAPIClient, claude_api_client
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Versuche die neue AI-Service-Schicht zu laden
_AI_SERVICE_AVAILABLE = False
_ai_client_instance = None

try:
    from ai_service import AIClient

    _ai_client_instance = AIClient()
    _AI_SERVICE_AVAILABLE = True
    logger.info("Claude API Client: Verwende neue ai_service-Abstraktionsschicht")
except ImportError:
    logger.info(
        "Claude API Client: ai_service nicht verfuegbar,"
        " verwende Legacy-Implementierung"
    )
except Exception as e:
    logger.warning(f"Claude API Client: ai_service-Initialisierung fehlgeschlagen: {e}")


# Legacy-Imports (nur wenn ai_service nicht verfuegbar)
if not _AI_SERVICE_AVAILABLE:
    try:
        from dotenv import load_dotenv

        env_file = Path(__file__).parent.parent.parent.parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except (ImportError, Exception):
        pass

    try:
        from anthropic import Anthropic

        ANTHROPIC_AVAILABLE = True
    except ImportError:
        ANTHROPIC_AVAILABLE = False

    try:
        from config.settings import settings
    except ImportError:
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

    Delegiert an ai_service.AIClient wenn verfuegbar,
    nutzt sonst die direkte Anthropic-API als Fallback.
    """

    def __init__(self):
        self._use_new_service = (
            _AI_SERVICE_AVAILABLE and _ai_client_instance is not None
        )
        self.client = None
        self.primary_model = "claude-sonnet-4-20250514"
        self.fallback_models = [
            "claude-3-5-sonnet-20250106",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

        if not self._use_new_service:
            self._initialize_legacy_client()

    def _initialize_legacy_client(self):
        """Legacy: Initialisiert Anthropic Client direkt."""
        try:
            if not ANTHROPIC_AVAILABLE:
                logger.warning("Anthropic library not available")
                return

            api_key = (
                os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
                if hasattr(settings, "ANTHROPIC_API_KEY")
                else None
            )
            if api_key:
                self.client = Anthropic(api_key=api_key)
                logger.info("Claude API Client initialized (legacy mode)")
            else:
                logger.warning("No Anthropic API key found")
        except Exception as e:
            logger.error(f"Claude client initialization failed: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Prueft ob Claude Service verfuegbar ist."""
        if self._use_new_service:
            return _ai_client_instance.is_available()
        return self.client is not None

    def analyze_document(
        self, document_path: str, prompt: str, debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Einheitlicher Claude API Call fuer Dokument-Analyse.

        Args:
            document_path: Pfad zum Dokument
            prompt: Vollstaendiger Prompt
            debug: Debug-Ausgaben

        Returns:
            Geparste JSON-Response
        """
        # Neue AI-Service-Schicht verwenden
        if self._use_new_service:
            try:
                if debug:
                    doc_name = Path(document_path).name
                    logger.info(
                        "Claude API call via ai_service" f" - Document: {doc_name}"
                    )
                result = _ai_client_instance.analyze_document_json(
                    document_path=document_path,
                    prompt=prompt,
                )
                if debug and result:
                    logger.info("JSON successfully parsed via ai_service!")
                return result
            except Exception as e:
                logger.error(f"ai_service Dokument-Analyse fehlgeschlagen: {e}")
                return None

        # Legacy-Fallback
        return self._legacy_analyze_document(document_path, prompt, debug)

    def _legacy_analyze_document(
        self, document_path: str, prompt: str, debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Legacy: Direkte Anthropic API fuer Dokument-Analyse."""
        if not self.is_available():
            logger.error("Claude client not available")
            return None

        try:
            with open(document_path, "rb") as f:
                document_data = f.read()

            media_type = self._get_media_type_from_data(document_data, document_path)

            message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.b64encode(document_data).decode("utf-8"),
                        },
                    },
                ],
            }

            response = None
            models_to_try = [self.primary_model] + self.fallback_models

            for model in models_to_try:
                try:
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[message],
                    )
                    if debug:
                        logger.info(f"Success with model: {model}")
                    break
                except Exception as e:
                    if "not_found_error" in str(e):
                        continue
                    else:
                        raise e

            if not response:
                raise Exception("All models failed")

            response_text = response.content[0].text
            return self._clean_and_parse_response(response_text, debug)

        except Exception as e:
            logger.error(f"Error in Claude API call: {e}")
            return None

    def _get_media_type_from_data(
        self, document_data: bytes, file_path: str = None
    ) -> str:
        """Bestimmt Media-Type eines Dokuments."""
        if file_path:
            file_path_lower = file_path.lower()
            if file_path_lower.endswith(".pdf"):
                return "application/pdf"
            elif file_path_lower.endswith(".docx"):
                return (
                    "application/vnd.openxmlformats"
                    "-officedocument"
                    ".wordprocessingml.document"
                )
            elif file_path_lower.endswith(".doc"):
                return "application/msword"
            elif file_path_lower.endswith(".txt"):
                return "text/plain"

        if document_data.startswith(b"%PDF"):
            return "application/pdf"
        elif document_data.startswith(b"PK"):
            if b"word/" in document_data[:1024]:
                return (
                    "application/vnd.openxmlformats"
                    "-officedocument"
                    ".wordprocessingml.document"
                )

        return "application/pdf"

    def _clean_and_parse_response(
        self, response_text: str, debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """JSON Response bereinigen und parsen."""
        try:
            cleaned_text = response_text.strip()

            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]

            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()
            return json.loads(cleaned_text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {e}")
            return None


# Global instance (backward-kompatibel)
claude_api_client = ClaudeAPIClient()
