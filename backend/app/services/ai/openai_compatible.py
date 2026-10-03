from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.ai.base import (
    AIProvider,
    AIProviderError,
    AIProviderUnavailableError,
    extract_json_from_text,
)

T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleProvider(AIProvider):
    """
    Generic provider for OpenAI-compatible inference APIs (Cerebras, Groq, OpenRouter, etc.).
    """

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key_getter: callable,
        default_model: str,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        self._name = provider_name
        self.base_url = base_url.rstrip("/")
        self._api_key_getter = api_key_getter
        self.default_model = default_model
        self.extra_headers = extra_headers or {}

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        key = self._api_key_getter()
        return bool(key and key.strip())

    def _get_api_key(self) -> str:
        key = self._api_key_getter()
        if not key or not key.strip():
            raise AIProviderUnavailableError(
                f"Provider '{self.name}' is not configured with an API key."
            )
        return key.strip()

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        api_key = self._get_api_key()
        target_model = model or self.default_model

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        timeout = float(settings.AI_REQUEST_TIMEOUT_SECONDS)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    raise AIProviderError(
                        f"Provider '{self.name}' failed with status {response.status_code}: {response.text[:400]}"
                    )

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise AIProviderError(f"Provider '{self.name}' returned no completion choices.")

                return choices[0]["message"]["content"]
        except httpx.RequestError as exc:
            raise AIProviderError(f"Network error calling provider '{self.name}': {exc}") from exc

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        schema_json = schema.model_json_schema()
        augmented_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Respond with ONLY a valid JSON object strictly complying with this JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any greeting, preamble, or commentary outside the JSON."
        )

        sys_prompt = system_prompt or "You are an expert AI software architect that outputs strict valid JSON."

        raw_text = await self.generate_text(
            prompt=augmented_prompt,
            system_prompt=sys_prompt,
            model=model,
            temperature=temperature,
        )

        parsed_dict = extract_json_from_text(raw_text)
        try:
            return schema.model_validate(parsed_dict)
        except Exception as exc:
            raise AIProviderError(
                f"Failed to validate response from '{self.name}' against schema {schema.__name__}: {exc}"
            ) from exc
