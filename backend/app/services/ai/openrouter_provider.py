from app.core.config import settings
from app.services.ai.openai_compatible import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter API Provider (fallback routing to free and diverse models)."""

    def __init__(self):
        super().__init__(
            provider_name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key_getter=lambda: settings.OPENROUTER_API_KEY,
            default_model=settings.AI_FALLBACK_MODEL or "deepseek/deepseek-chat:free",
            extra_headers={
                "HTTP-Referer": "https://nexusstudio.local",
                "X-Title": "Nexus Studio AI Builder",
            },
        )
