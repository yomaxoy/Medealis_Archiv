"""
Claude AI Provider - Anthropic Claude API Integration.

Implementiert das AIProvider-Interface fuer Claude-Modelle.
Portiert und konsolidiert die Logik aus den bestehenden Claude-Clients:
- infrastructure/external_services/claude_client.py (httpx, Fallback)
- application/services/document_processing/claude_api_client.py (Dokument-Handling)
"""

import os
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .base import AIProvider, AIResponse, ProviderType

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """
    Claude AI Provider via Anthropic SDK.

    Features:
    - Model-Fallback-Kette (neueste -> aelteste Modelle)
    - httpx-Client mit Retries und Timeouts
    - Dokument-Analyse (PDF, DOCX, DOC, TXT)
    - Base64-Encoding fuer Dokumente
    """

    # Model-Fallback-Kette (in Praeferenz-Reihenfolge)
    DEFAULT_MODELS = [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20250106",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        # Try to get API key from EnvironmentConfig first (ensures .env is loaded)
        if not api_key:
            try:
                from warehouse.shared.config.environment_config import env_config
                api_key = env_config.get("ANTHROPIC_API_KEY")
            except ImportError:
                api_key = os.getenv("ANTHROPIC_API_KEY")

        self.api_key = api_key
        self.default_model = default_model or self.DEFAULT_MODELS[0]
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = self._setup_client()

    def _setup_client(self):
        """Initialisiert den Anthropic-Client mit httpx-Transport."""
        if not self.api_key:
            logger.warning(
                "ANTHROPIC_API_KEY nicht gesetzt - Claude Provider nicht verfuegbar"
            )
            return None

        try:
            import anthropic
            import httpx

            custom_client = httpx.Client(
                timeout=self.timeout,
                verify=True,
                follow_redirects=True,
                headers={
                    "User-Agent": "Medealis-QMS/2.0",
                    "Connection": "keep-alive",
                },
                transport=httpx.HTTPTransport(retries=3),
            )

            return anthropic.Anthropic(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
                http_client=custom_client,
            )
        except ImportError:
            logger.error("anthropic oder httpx Bibliothek nicht installiert")
            return None
        except Exception as e:
            logger.error(f"Claude-Client Initialisierung fehlgeschlagen: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> AIResponse:
        """Generiere Text-Completion mit Model-Fallback."""
        if not self.is_available():
            raise RuntimeError(
                "Claude Provider nicht verfuegbar"
                " (API-Key fehlt oder Client"
                " nicht initialisiert)"
            )

        messages = [{"role": "user", "content": prompt}]
        return self._call_with_fallback(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def generate_with_document(
        self,
        document_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1,
    ) -> AIResponse:
        """Generiere Completion mit Dokument-Kontext."""
        if not self.is_available():
            raise RuntimeError("Claude Provider nicht verfuegbar")

        # Dokument lesen und Base64-kodieren
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"Dokument nicht gefunden: {document_path}")

        with open(doc_path, "rb") as f:
            document_data = f.read()

        media_type = self._detect_media_type(document_data, str(doc_path))
        doc_base64 = base64.b64encode(document_data).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": doc_base64,
                        },
                    },
                ],
            }
        ]

        return self._call_with_fallback(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def is_available(self) -> bool:
        """Prueft ob Claude API konfiguriert ist."""
        return self.client is not None and self.api_key is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Gibt Provider-Informationen zurueck."""
        return {
            "provider": ProviderType.CLAUDE.value,
            "default_model": self.default_model,
            "available_models": self.DEFAULT_MODELS,
            "api_key_set": self.api_key is not None,
            "client_initialized": self.client is not None,
        }

    def _call_with_fallback(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> AIResponse:
        """Fuehrt API-Call mit Model-Fallback-Kette aus."""
        models_to_try = [self.default_model] + [
            m for m in self.DEFAULT_MODELS if m != self.default_model
        ]

        last_error = None
        for model in models_to_try:
            try:
                kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                }
                if system_prompt:
                    kwargs["system"] = system_prompt

                response = self.client.messages.create(**kwargs)

                usage = None
                if hasattr(response, "usage") and response.usage:
                    usage = {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    }

                logger.info(f"Claude API Erfolg mit Model: {model}")
                return AIResponse(
                    text=response.content[0].text,
                    model_used=model,
                    provider=ProviderType.CLAUDE,
                    usage=usage,
                    raw_response=response,
                )

            except Exception as e:
                error_str = str(e)
                if "not_found_error" in error_str:
                    logger.warning(
                        f"Model {model} nicht verfuegbar, versuche naechstes"
                    )
                    last_error = e
                    continue
                else:
                    logger.error(f"Claude API Fehler mit Model {model}: {e}")
                    last_error = e
                    break

        raise RuntimeError(
            f"Alle Claude-Modelle fehlgeschlagen. Letzter Fehler: {last_error}"
        )

    def _detect_media_type(self, document_data: bytes, file_path: str) -> str:
        """Erkennt den Media-Type eines Dokuments."""
        # Dateiendung pruefen
        file_path_lower = file_path.lower()
        if file_path_lower.endswith(".pdf"):
            return "application/pdf"
        elif file_path_lower.endswith(".docx"):
            return (
                "application/vnd.openxmlformats"
                "-officedocument.wordprocessingml"
                ".document"
            )
        elif file_path_lower.endswith(".doc"):
            return "application/msword"
        elif file_path_lower.endswith(".txt"):
            return "text/plain"

        # Magic Bytes pruefen
        if document_data.startswith(b"%PDF"):
            return "application/pdf"
        elif document_data.startswith(b"PK"):
            if b"word/" in document_data[:1024]:
                return (
                    "application/vnd.openxmlformats"
                    "-officedocument"
                    ".wordprocessingml.document"
                )

        # Default
        return "application/pdf"
