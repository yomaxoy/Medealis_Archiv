"""
AI Service Konfiguration.

Zentrale Konfiguration fuer alle KI-Provider und Anwendungsfaelle.
Liest Einstellungen aus Umgebungsvariablen (.env).
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict

from .providers.base import ProviderType

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Konfiguration fuer einen einzelnen KI-Provider."""

    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 2


@dataclass
class UseCaseConfig:
    """Standard-Parameter pro Anwendungsfall."""

    max_tokens: int = 2000
    temperature: float = 0.0


@dataclass
class AIServiceConfig:
    """Zentrale KI-Service-Konfiguration."""

    # Aktiver Provider
    active_provider: ProviderType = ProviderType.CLAUDE

    # Provider-spezifische Konfigurationen
    providers: Dict[ProviderType, ProviderConfig] = field(default_factory=dict)

    # Anwendungsfall-spezifische Defaults
    use_case_defaults: Dict[str, UseCaseConfig] = field(default_factory=dict)

    @classmethod
    def from_environment(cls) -> "AIServiceConfig":
        """Laedt Konfiguration aus Umgebungsvariablen."""
        config = cls()

        # .env laden falls vorhanden
        try:
            from dotenv import load_dotenv
            from pathlib import Path

            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass

        # Aktiver Provider
        provider_name = os.getenv("AI_PROVIDER", "claude").lower()
        try:
            config.active_provider = ProviderType(provider_name)
        except ValueError:
            logger.warning(
                f"Unbekannter AI_PROVIDER '{provider_name}', verwende 'claude'"
            )
            config.active_provider = ProviderType.CLAUDE

        # Claude Konfiguration
        config.providers[ProviderType.CLAUDE] = ProviderConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            default_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            timeout=float(os.getenv("CLAUDE_TIMEOUT", "60.0")),
            max_retries=int(os.getenv("CLAUDE_MAX_RETRIES", "2")),
        )

        # OpenAI Konfiguration (vorbereitet fuer spaeter)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            config.providers[ProviderType.OPENAI] = ProviderConfig(
                api_key=openai_key,
                default_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )

        # Ollama Konfiguration (vorbereitet fuer spaeter)
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_url:
            config.providers[ProviderType.OLLAMA] = ProviderConfig(
                base_url=ollama_url,
                default_model=os.getenv("OLLAMA_MODEL", "llama3"),
            )

        # Anwendungsfall-Defaults
        config.use_case_defaults = {
            "document_extraction": UseCaseConfig(max_tokens=4000, temperature=0.1),
            "data_extraction": UseCaseConfig(max_tokens=2000, temperature=0.0),
            "report_generation": UseCaseConfig(max_tokens=8000, temperature=0.3),
            "risk_assessment": UseCaseConfig(max_tokens=4000, temperature=0.1),
            "supplier_evaluation": UseCaseConfig(max_tokens=6000, temperature=0.2),
            "capa_analysis": UseCaseConfig(max_tokens=6000, temperature=0.1),
            "pms_research": UseCaseConfig(max_tokens=8000, temperature=0.2),
            "general": UseCaseConfig(max_tokens=2000, temperature=0.0),
        }

        return config

    def get_provider_config(
        self, provider_type: Optional[ProviderType] = None
    ) -> Optional[ProviderConfig]:
        """Gibt die Konfiguration fuer den angegebenen
        (oder aktiven) Provider zurueck."""
        pt = provider_type or self.active_provider
        return self.providers.get(pt)

    def get_use_case_config(self, use_case: str) -> UseCaseConfig:
        """Gibt die Konfiguration fuer einen Anwendungsfall zurueck."""
        return self.use_case_defaults.get(use_case, UseCaseConfig())


# Globale Konfigurationsinstanz
ai_config = AIServiceConfig.from_environment()
