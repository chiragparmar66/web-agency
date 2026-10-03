from app.core.config import settings
from app.services.ai.openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    """Groq Cloud API Provider (ultra-fast inference for review and planning)."""

    def __init__(self):
        super().__init__(
            provider_name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key_getter=lambda: settings.GROQ_API_KEY,
            default_model=settings.AI_REVIEW_MODEL or "llama-3.3-70b-versatile",
        )
