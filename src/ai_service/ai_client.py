"""
Unified AI Client - Zentraler Einstiegspunkt fuer alle KI-Interaktionen.

Usage:
    from ai_service import AIClient, PromptType

    client = AIClient()
    response = client.generate("Analysiere diese Daten...")
    response = client.generate_with_context("...", PromptType.SUPPLIER_EVALUATION)
    result = client.analyze_document_json("/pfad/zu/pdf", "Extrahiere...")
"""

import json
import logging
from typing import Optional, Dict, Any

from .config import ai_config, AIServiceConfig
from .providers.base import AIProvider, AIResponse
from .providers import get_provider_class
from .prompts import PromptType, SystemPromptRepository

logger = logging.getLogger(__name__)


class AIClient:
    """
    Unified AI Client fuer das Medealis QMS.

    Waehlt den konfigurierten Provider, stellt eine einheitliche API bereit
    und integriert das QMS-Prompt-Repository.
    """

    def __init__(self, config: Optional[AIServiceConfig] = None):
        self._config = config or ai_config
        self._provider: Optional[AIProvider] = None
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialisiert den aktiven KI-Provider."""
        provider_type = self._config.active_provider
        provider_config = self._config.get_provider_config(provider_type)

        if not provider_config:
            logger.error(f"Keine Konfiguration fuer Provider: {provider_type.value}")
            return

        try:
            provider_class = get_provider_class(provider_type)
            self._provider = provider_class(
                api_key=provider_config.api_key,
                default_model=provider_config.default_model,
                timeout=provider_config.timeout,
                max_retries=provider_config.max_retries,
            )
            logger.info(f"AI Provider initialisiert: {provider_type.value}")
        except ValueError as e:
            logger.error(f"Provider {provider_type.value} nicht registriert: {e}")
        except Exception as e:
            logger.error(f"Provider-Initialisierung fehlgeschlagen: {e}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> AIResponse:
        """
        Generiere eine Text-Completion.

        Args:
            prompt: User-Prompt
            system_prompt: Optionaler System-Prompt
            max_tokens: Maximale Antwortlaenge
            temperature: Kreativitaet (0.0 = deterministisch)

        Returns:
            AIResponse mit generiertem Text

        Raises:
            RuntimeError: Wenn kein Provider verfuegbar
        """
        self._ensure_available()
        return self._provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def generate_with_context(
        self,
        prompt: str,
        prompt_type: PromptType,
        context: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AIResponse:
        """
        Generiere eine Completion mit QMS System-Prompt.

        Holt automatisch den passenden System-Prompt aus dem Repository
        und verwendet Anwendungsfall-spezifische Defaults.

        Args:
            prompt: User-Prompt
            prompt_type: QMS-Prompt-Typ (z.B. SUPPLIER_EVALUATION)
            context: Optionale Variablen fuer den System-Prompt
            max_tokens: Override fuer max_tokens (sonst Use-Case-Default)
            temperature: Override fuer temperature (sonst Use-Case-Default)

        Returns:
            AIResponse mit generiertem Text
        """
        self._ensure_available()

        # System-Prompt aus Repository
        system_prompt = SystemPromptRepository.get_prompt(prompt_type, context)

        # Use-Case Defaults
        uc_config = self._config.get_use_case_config(prompt_type.value)

        return self._provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens or uc_config.max_tokens,
            temperature=temperature
            if temperature is not None
            else uc_config.temperature,
        )

    def analyze_document(
        self,
        document_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1,
    ) -> AIResponse:
        """
        Analysiere ein Dokument (PDF, DOCX, etc.).

        Args:
            document_path: Pfad zum Dokument
            prompt: Analyse-Prompt
            system_prompt: Optionaler System-Prompt
            max_tokens: Maximale Antwortlaenge
            temperature: Kreativitaet

        Returns:
            AIResponse mit Analyse-Ergebnis
        """
        self._ensure_available()
        return self._provider.generate_with_document(
            document_path=document_path,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def analyze_document_json(
        self,
        document_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Analysiere ein Dokument und parse die Antwort als JSON.

        Beinhaltet automatische Bereinigung von Markdown-Code-Bloecken
        und JSON-Parsing (portiert aus dem bestehenden claude_api_client).

        Args:
            document_path: Pfad zum Dokument
            prompt: Analyse-Prompt (sollte JSON-Output anfordern)
            system_prompt: Optionaler System-Prompt
            max_tokens: Maximale Antwortlaenge
            temperature: Kreativitaet

        Returns:
            Geparste JSON-Response als Dict, oder None bei Fehler
        """
        try:
            response = self.analyze_document(
                document_path=document_path,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return self._clean_and_parse_json(response.text)
        except Exception as e:
            logger.error(f"Dokument-Analyse (JSON) fehlgeschlagen: {e}")
            return None

    def is_available(self) -> bool:
        """Prueft ob der KI-Service verfuegbar ist."""
        return self._provider is not None and self._provider.is_available()

    def test_connection(self) -> bool:
        """Testet die Verbindung zum KI-Provider."""
        if not self.is_available():
            return False
        try:
            response = self.generate(
                prompt="Antworte nur mit 'OK'",
                max_tokens=10,
            )
            return "OK" in response.text
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Gibt den Status des AI-Service zurueck."""
        status = {
            "available": self.is_available(),
            "active_provider": self._config.active_provider.value,
        }
        if self._provider:
            status["provider_info"] = self._provider.get_model_info()
        return status

    def _ensure_available(self) -> None:
        """Stellt sicher, dass ein Provider verfuegbar ist."""
        if not self.is_available():
            raise RuntimeError(
                f"AI Service nicht verfuegbar. "
                f"Provider: {self._config.active_provider.value}. "
                f"Bitte ANTHROPIC_API_KEY in .env setzen."
            )

    @staticmethod
    def _clean_and_parse_json(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Bereinigt und parst JSON aus KI-Antworten.

        Entfernt Markdown-Code-Bloecke (```json ... ```) und parst JSON.
        Portiert aus claude_api_client.py._clean_and_parse_response().
        """
        try:
            cleaned = response_text.strip()

            # Markdown Code-Block Markierungen entfernen
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parsing fehlgeschlagen: {e}")
            return None
        except Exception as e:
            logger.error(f"Fehler bei JSON-Bereinigung: {e}")
            return None


# Globale Instanz
ai_client = AIClient()
