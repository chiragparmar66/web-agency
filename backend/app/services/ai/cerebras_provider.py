from app.core.config import settings
from app.services.ai.openai_compatible import OpenAICompatibleProvider


class CerebrasProvider(OpenAICompatibleProvider):
    """Cerebras Inference API Provider (fast Llama-3.3-70b inference)."""

    def __init__(self):
        super().__init__(
            provider_name="cerebras",
            base_url="https://api.cerebras.ai/v1",
            api_key_getter=lambda: settings.CEREBRAS_API_KEY,
            default_model=settings.AI_GENERATION_MODEL or "llama3.3-70b",
        )
