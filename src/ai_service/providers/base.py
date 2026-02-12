"""
AI Provider Abstraktion - Basis-Interface fuer alle KI-Provider.

Ermoeglicht den Austausch von KI-Providern (Claude, OpenAI, Ollama)
ohne Aenderungen im Consumer-Code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class ProviderType(Enum):
    """Unterstuetzte KI-Provider."""

    CLAUDE = "claude"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class AIResponse:
    """Standardisierte Antwort von jedem KI-Provider."""

    text: str
    model_used: str
    provider: ProviderType
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None

    @property
    def input_tokens(self) -> int:
        if self.usage:
            return self.usage.get("input_tokens", 0)
        return 0

    @property
    def output_tokens(self) -> int:
        if self.usage:
            return self.usage.get("output_tokens", 0)
        return 0


class AIProvider(ABC):
    """
    Abstrakte Basisklasse fuer KI-Provider.

    Jeder Provider (Claude, OpenAI, Ollama) implementiert dieses Interface.
    Der AIClient nutzt den konfigurierten Provider ueber diese einheitliche API.
    """

    @abstractmethod
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
            prompt: Der User-Prompt
            system_prompt: Optionaler System-Prompt (Kontext/Rolle)
            max_tokens: Maximale Antwortlaenge
            temperature: Kreativitaet (0.0 = deterministisch, 1.0 = kreativ)

        Returns:
            AIResponse mit generiertem Text
        """
        ...

    @abstractmethod
    def generate_with_document(
        self,
        document_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1,
    ) -> AIResponse:
        """
        Generiere eine Completion mit Dokument-Kontext (PDF, DOCX, etc.).

        Args:
            document_path: Pfad zum Dokument
            prompt: Analyse-Prompt
            system_prompt: Optionaler System-Prompt
            max_tokens: Maximale Antwortlaenge
            temperature: Kreativitaet

        Returns:
            AIResponse mit Analyse-Ergebnis
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Prueft ob der Provider konfiguriert und erreichbar ist."""
        ...

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Gibt Provider-Informationen zurueck.

        Returns:
            Dict mit: provider, default_model, available_models, status
        """
        ...
