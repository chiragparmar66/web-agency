import logging
from typing import Optional, Tuple, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.services.ai.base import (
    AITask,
    AIProvider,
    AIProviderError,
    AIProviderUnavailableError,
)
from app.services.ai.registry import AIProviderRegistry, default_registry

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class AITaskRouter:
    """
    Routes AI tasks to designated providers and models based on configuration,
    with automatic fallback and retry mechanisms.
    """

    def __init__(self, registry: Optional[AIProviderRegistry] = None):
        self.registry = registry or default_registry

    def resolve_target(self, task: AITask) -> Tuple[str, str]:
        """
        Determine primary provider name and model for a given task.
        """
        if task == AITask.ANALYSIS:
            return settings.AI_ANALYSIS_PROVIDER, settings.AI_ANALYSIS_MODEL
        elif task == AITask.PLANNING:
            return settings.AI_PLANNING_PROVIDER, settings.AI_PLANNING_MODEL
        elif task == AITask.WEBSITE_GENERATION:
            return settings.AI_GENERATION_PROVIDER, settings.AI_GENERATION_MODEL
        elif task in (AITask.CODE_REVIEW, AITask.VALIDATION):
            return settings.AI_REVIEW_PROVIDER, settings.AI_REVIEW_MODEL
        elif task == AITask.REPAIR:
            return settings.AI_GENERATION_PROVIDER, settings.AI_GENERATION_MODEL
        return settings.AI_GENERATION_PROVIDER, settings.AI_GENERATION_MODEL

    def get_fallback_target(self) -> Tuple[str, str]:
        """Return configured fallback provider name and model."""
        return settings.AI_FALLBACK_PROVIDER, settings.AI_FALLBACK_MODEL

    async def execute_task_text(
        self,
        task: AITask,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Tuple[str, str]:
        """
        Execute a text generation task.
        Returns: Tuple of (generated_text, provider_name_used).
        """
        retries = max_retries if max_retries is not None else settings.AI_MAX_RETRIES
        primary_provider_name, primary_model = self.resolve_target(task)
        fallback_provider_name, fallback_model = self.get_fallback_target()

        # Candidates to try: primary, then fallback
        candidates = [(primary_provider_name, primary_model)]
        if fallback_provider_name != primary_provider_name:
            candidates.append((fallback_provider_name, fallback_model))

        last_error = None

        for provider_name, model in candidates:
            try:
                provider = self.registry.get(provider_name)
                if not provider.is_available():
                    logger.warning("Provider '%s' is not available (missing credentials).", provider_name)
                    continue

                for attempt in range(retries + 1):
                    try:
                        logger.info("Task %s: Attempting with provider '%s' (model: %s)", task.value, provider_name, model)
                        text = await provider.generate_text(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            model=model,
                        )
                        return text, provider_name
                    except AIProviderError as err:
                        last_error = err
                        logger.warning(
                            "Provider '%s' attempt %d failed for task %s: %s",
                            provider_name, attempt + 1, task.value, err
                        )
            except AIProviderUnavailableError as err:
                last_error = err
                continue

        # If primary and configured fallback failed, try any available provider as last resort
        available = self.registry.list_available()
        for alt_name in available:
            if alt_name not in [c[0] for c in candidates]:
                try:
                    alt_provider = self.registry.get(alt_name)
                    logger.info("Task %s: Last resort attempt with available provider '%s'", task.value, alt_name)
                    text = await alt_provider.generate_text(prompt=prompt, system_prompt=system_prompt)
                    return text, alt_name
                except Exception as err:
                    last_error = err
                    continue

        raise AIProviderError(
            f"All providers exhausted for task '{task.value}'. Last error: {last_error}"
        )

    async def execute_task_structured(
        self,
        task: AITask,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Tuple[T, str]:
        """
        Execute a structured generation task returning a validated Pydantic model.
        Returns: Tuple of (validated_model_instance, provider_name_used).
        """
        retries = max_retries if max_retries is not None else settings.AI_MAX_RETRIES
        primary_provider_name, primary_model = self.resolve_target(task)
        fallback_provider_name, fallback_model = self.get_fallback_target()

        candidates = [(primary_provider_name, primary_model)]
        if fallback_provider_name != primary_provider_name:
            candidates.append((fallback_provider_name, fallback_model))

        last_error = None

        for provider_name, model in candidates:
            try:
                provider = self.registry.get(provider_name)
                if not provider.is_available():
                    logger.warning("Provider '%s' is not available (missing credentials).", provider_name)
                    continue

                for attempt in range(retries + 1):
                    try:
                        logger.info("Task %s: Generating structured data with '%s' (model: %s)", task.value, provider_name, model)
                        obj = await provider.generate_structured(
                            prompt=prompt,
                            schema=schema,
                            system_prompt=system_prompt,
                            model=model,
                        )
                        return obj, provider_name
                    except AIProviderError as err:
                        last_error = err
                        logger.warning(
                            "Provider '%s' structured attempt %d failed for task %s: %s",
                            provider_name, attempt + 1, task.value, err
                        )
            except AIProviderUnavailableError as err:
                last_error = err
                continue

        available = self.registry.list_available()
        for alt_name in available:
            if alt_name not in [c[0] for c in candidates]:
                try:
                    alt_provider = self.registry.get(alt_name)
                    logger.info("Task %s: Last resort structured attempt with '%s'", task.value, alt_name)
                    obj = await alt_provider.generate_structured(
                        prompt=prompt,
                        schema=schema,
                        system_prompt=system_prompt,
                    )
                    return obj, alt_name
                except Exception as err:
                    last_error = err
                    continue

        raise AIProviderError(
            f"All providers exhausted for structured task '{task.value}'. Last error: {last_error}"
        )
