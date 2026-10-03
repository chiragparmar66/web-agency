from typing import Any, Dict, Optional, Type, TypeVar
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


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider implementation."""

    def __init__(self):
        self._name = "gemini"
        self.default_model = settings.AI_ANALYSIS_MODEL or "gemini-2.0-flash-lite"

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        key = settings.GEMINI_API_KEY
        return bool(key and key.strip())

    def _get_api_key(self) -> str:
        key = settings.GEMINI_API_KEY
        if not key or not key.strip():
            raise AIProviderUnavailableError("Gemini API key is not configured in settings.")
        return key.strip()

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_mime_type: Optional[str] = None,
    ) -> str:
        api_key = self._get_api_key()
        target_model = model or self.default_model

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        gen_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if response_mime_type:
            gen_config["responseMimeType"] = response_mime_type

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
        }

        if system_prompt:
            body["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        timeout = float(settings.AI_REQUEST_TIMEOUT_SECONDS)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=body)
                if response.status_code != 200:
                    raise AIProviderError(
                        f"Gemini API returned error {response.status_code}: {response.text[:400]}"
                    )

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise AIProviderError("Gemini API returned no response candidates.")

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise AIProviderError("Gemini candidate contains no content parts.")

                return parts[0].get("text", "")
        except httpx.RequestError as exc:
            raise AIProviderError(f"Network error communicating with Gemini API: {exc}") from exc

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
        )
        sys_prompt = system_prompt or "You are an expert AI software architect that outputs strict valid JSON."

        raw_text = await self.generate_text(
            prompt=augmented_prompt,
            system_prompt=sys_prompt,
            model=model,
            temperature=temperature,
            response_mime_type="application/json",
        )

        parsed_dict = extract_json_from_text(raw_text)
        try:
            return schema.model_validate(parsed_dict)
        except Exception as exc:
            raise AIProviderError(
                f"Failed to validate response from Gemini against schema {schema.__name__}: {exc}"
            ) from exc
