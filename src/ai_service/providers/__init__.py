"""
AI Provider Registry.

Verwaltet die Registrierung und den Zugriff auf KI-Provider.
"""

from typing import Dict, Type
from .base import AIProvider, AIResponse, ProviderType

# Provider-Registry: Mappt ProviderType auf Provider-Klasse
_PROVIDER_REGISTRY: Dict[ProviderType, Type[AIProvider]] = {}


def register_provider(
    provider_type: ProviderType, provider_class: Type[AIProvider]
) -> None:
    """Registriert einen neuen AI-Provider."""
    _PROVIDER_REGISTRY[provider_type] = provider_class


def get_provider_class(provider_type: ProviderType) -> Type[AIProvider]:
    """Gibt die Provider-Klasse fuer den angegebenen Typ zurueck."""
    if provider_type not in _PROVIDER_REGISTRY:
        available = [p.value for p in _PROVIDER_REGISTRY.keys()]
        raise ValueError(
            f"Unbekannter Provider: {provider_type.value}. " f"Verfuegbar: {available}"
        )
    return _PROVIDER_REGISTRY[provider_type]


def list_registered_providers() -> list:
    """Listet alle registrierten Provider auf."""
    return [pt.value for pt in _PROVIDER_REGISTRY.keys()]


# Claude Provider automatisch registrieren
try:
    from .claude_provider import ClaudeProvider

    register_provider(ProviderType.CLAUDE, ClaudeProvider)
except ImportError:
    pass

__all__ = [
    "AIProvider",
    "AIResponse",
    "ProviderType",
    "register_provider",
    "get_provider_class",
    "list_registered_providers",
]
