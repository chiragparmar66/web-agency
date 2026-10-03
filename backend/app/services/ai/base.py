from abc import ABC, abstractmethod
from enum import Enum
import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AITask(str, Enum):
    """Task types supported by the AI Generation Engine."""
    ANALYSIS = "ANALYSIS"
    PLANNING = "PLANNING"
    WEBSITE_GENERATION = "WEBSITE_GENERATION"
    CODE_REVIEW = "CODE_REVIEW"
    VALIDATION = "VALIDATION"
    REPAIR = "REPAIR"


class AIProviderError(Exception):
    """Base exception for AI provider call errors."""
    pass


class AIProviderUnavailableError(AIProviderError):
    """Raised when an AI provider is requested but its API key/service is not configured."""
    pass


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Robust JSON extraction from LLM responses, handling markdown code fences,
    leading/trailing prose, and raw JSON strings.
    """
    cleaned = text.strip()
    # Check for markdown code fences (```json ... ``` or ``` ...)
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    fence_match = re.search(fence_pattern, cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # Try standard parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Find outermost { ... } or [ ... ]
        brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if brace_match:
            try:
                return json.loads(brace_match.group(1).strip())
            except json.JSONDecodeError as err:
                raise AIProviderError(f"Failed to parse extracted JSON block: {err}\nContent: {cleaned[:300]}")
        raise AIProviderError(f"No valid JSON structure found in response: {cleaned[:300]}")


class AIProvider(ABC):
    """Abstract base class for all AI model providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'gemini', 'cerebras', 'groq', 'openrouter')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured with necessary API keys."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate raw text/code from prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        """Generate a validated Pydantic model instance from prompt."""
        pass
