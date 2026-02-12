"""
Claude API Client - Infrastructure Layer (Backward-kompatibler Wrapper).

Delegiert an die neue ai_service-Abstraktionsschicht wenn verfuegbar.
Exportiert als 'ClaudeClient' via __init__.py.
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Versuche die neue AI-Service-Schicht zu laden
_AI_SERVICE_AVAILABLE = False
_ai_client_instance = None

try:
    from ai_service import AIClient

    _ai_client_instance = AIClient()
    _AI_SERVICE_AVAILABLE = True
except (ImportError, Exception):
    pass


class ClaudeAPIClient:
    """
    Low-level Claude API client (Infrastructure Layer).

    Delegiert an ai_service.AIClient wenn verfuegbar,
    nutzt sonst die direkte Anthropic-API als Fallback.
    """

    def __init__(self):
        self._use_new_service = (
            _AI_SERVICE_AVAILABLE and _ai_client_instance is not None
        )
        self.api_key = None
        self.client = None

        if not self._use_new_service:
            self.api_key = self._get_api_key()
            self.client = self._setup_client()

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            return None
        return api_key.strip()

    def _setup_client(self):
        """Setup Anthropic client with proper configuration."""
        if not self.api_key:
            return None

        try:
            import anthropic
            import httpx

            custom_client = httpx.Client(
                timeout=60.0,
                verify=True,
                follow_redirects=True,
                headers={"User-Agent": "Medealis-QMS/2.0", "Connection": "keep-alive"},
                transport=httpx.HTTPTransport(retries=3),
            )

            return anthropic.Anthropic(
                api_key=self.api_key,
                timeout=60.0,
                max_retries=2,
                http_client=custom_client,
            )
        except ImportError:
            logger.error("Anthropic library not installed")
            return None

    def is_available(self) -> bool:
        """Check if Claude API client is available."""
        if self._use_new_service:
            return _ai_client_instance.is_available()
        return self.client is not None and self.api_key is not None

    def send_text_message(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> Optional[str]:
        """Send text message to Claude API."""
        if self._use_new_service:
            try:
                response = _ai_client_instance.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.text
            except Exception as e:
                logger.error(f"ai_service text message failed: {e}")
                return None

        if not self.is_available():
            return None

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API text message failed: {e}")
            return None

    def send_document_message(
        self, pdf_path: str, prompt: str, model: str = "claude-sonnet-4-20250514"
    ) -> Optional[str]:
        """Send document (PDF) to Claude API with prompt."""
        if self._use_new_service:
            try:
                response = _ai_client_instance.analyze_document(
                    document_path=pdf_path,
                    prompt=prompt,
                )
                return response.text
            except Exception as e:
                logger.error(f"ai_service document message failed: {e}")
                return None

        if not self.is_available():
            return None

        try:
            import base64

            with open(pdf_path, "rb") as file:
                pdf_base64 = base64.b64encode(file.read()).decode("utf-8")

            response = self.client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API document message failed: {e}")
            return None

    def test_connection(self) -> bool:
        """Test Claude API connection."""
        if self._use_new_service:
            return _ai_client_instance.test_connection()

        if not self.is_available():
            return False

        try:
            response = self.send_text_message(
                prompt="Test connection - respond only 'OK'", max_tokens=10
            )
            return response and "OK" in response
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available Claude models."""
        if self._use_new_service:
            info = _ai_client_instance.get_status()
            provider_info = info.get("provider_info", {})
            return provider_info.get("available_models", [])

        return [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20250106",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def send_message_with_fallback(
        self, prompt: str, max_tokens: int = 2000
    ) -> Optional[str]:
        """Send message with model fallback strategy."""
        if self._use_new_service:
            return self.send_text_message(prompt=prompt, max_tokens=max_tokens)

        models = self.get_available_models()

        for model in models:
            try:
                result = self.send_text_message(
                    prompt=prompt, model=model, max_tokens=max_tokens
                )
                if result:
                    logger.info(f"Successfully used Claude model: {model}")
                    return result
            except Exception as e:
                if "not_found_error" in str(e):
                    continue
                else:
                    logger.error(f"Error with model {model}: {e}")
                    break

        logger.error("All Claude models failed")
        return None

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information and status."""
        if self._use_new_service:
            return _ai_client_instance.get_status()

        return {
            "api_key_set": self.api_key is not None,
            "client_available": self.client is not None,
            "available_models": self.get_available_models(),
        }


# Global instance
claude_api_client = ClaudeAPIClient()

# Alias fuer backward-kompatiblen Export in __init__.py
ClaudeClient = ClaudeAPIClient
