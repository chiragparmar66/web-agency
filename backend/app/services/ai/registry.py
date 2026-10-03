from typing import Dict, List, Optional
from app.services.ai.base import AIProvider, AIProviderUnavailableError
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.cerebras_provider import CerebrasProvider
from app.services.ai.groq_provider import GroqProvider
from app.services.ai.openrouter_provider import OpenRouterProvider


class AIProviderRegistry:
    """Central registry for managing and discovering AI providers."""

    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.name.lower()] = provider

    def get(self, name: str) -> AIProvider:
        """Retrieve a provider by name."""
        name_lower = name.lower()
        if name_lower not in self._providers:
            raise AIProviderUnavailableError(
                f"Unknown AI provider '{name}'. Available: {list(self._providers.keys())}"
            )
        return self._providers[name_lower]

    def list_all(self) -> List[str]:
        """Return names of all registered providers."""
        return list(self._providers.keys())

    def list_available(self) -> List[str]:
        """Return names of providers that have valid credentials configured."""
        return [name for name, p in self._providers.items() if p.is_available()]


def create_default_registry() -> AIProviderRegistry:
    """Create and populate registry with default providers."""
    registry = AIProviderRegistry()
    registry.register(GeminiProvider())
    registry.register(CerebrasProvider())
    registry.register(GroqProvider())
    registry.register(OpenRouterProvider())
    return registry


# Global shared registry instance
default_registry = create_default_registry()
