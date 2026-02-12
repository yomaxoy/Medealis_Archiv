"""
Medealis AI Service - Zentrale KI-Abstraktionsschicht.

Bietet eine provider-agnostische API fuer KI-Interaktionen.
Aktuell unterstuetzt: Claude (Anthropic).
Erweiterbar fuer: OpenAI, Ollama, etc.

Usage:
    from ai_service import AIClient, PromptType

    client = AIClient()
    response = client.generate("Analysiere diese Daten...")
    response = client.generate_with_context("...", PromptType.SUPPLIER_EVALUATION)
"""

from .providers.base import AIProvider, AIResponse, ProviderType
from .ai_client import AIClient, ai_client
from .prompts import PromptType, SystemPromptRepository
from .config import AIServiceConfig, ai_config

__all__ = [
    "AIClient",
    "ai_client",
    "AIProvider",
    "AIResponse",
    "ProviderType",
    "PromptType",
    "SystemPromptRepository",
    "AIServiceConfig",
    "ai_config",
]
