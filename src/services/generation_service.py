"""Generation service orchestrating concurrent model answer generations."""

import asyncio
import time
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig
from src.providers.registry import ModelRegistry, model_registry
from src.services.cost_calculator import CostCalculator
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.gemini_provider import GeminiProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.mistral_provider import MistralProvider
from src.providers.ollama_provider import OllamaProvider
from src.providers.openrouter_provider import OpenRouterProvider
from src.providers.grok_provider import GrokProvider


class GenerationServiceError(Exception):
    def __init__(self, message: str, error_type: str = "ValidationError"):
        super().__init__(message)
        self.message = message
        self.error_type = error_type


class GenerationService:
    """Handles prompt validation, model validation, and concurrent generation dispatch."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or model_registry

    def validate_request(self, models: List[str], prompt: str) -> None:
        """Validate input parameters against business rules."""
        if not prompt or not prompt.strip():
            raise GenerationServiceError("Prompt cannot be empty.", "EmptyPromptError")

        if len(prompt) > 200_000:
            raise GenerationServiceError(
                f"Prompt exceeds maximum character length limit (length: {len(prompt)}, max: 200000).",
                "PromptTooLargeError"
            )

        if len(models) < settings.min_selected_models:
            raise GenerationServiceError(
                f"At least {settings.min_selected_models} models must be selected (got {len(models)}).",
                "InsufficientModelsError"
            )

        if len(models) > settings.max_selected_models:
            raise GenerationServiceError(
                f"At most {settings.max_selected_models} models can be selected (got {len(models)}).",
                "ExcessiveModelsError"
            )

        if len(set(models)) != len(models):
            raise GenerationServiceError(
                "Duplicate models are not permitted in comparison.",
                "DuplicateModelsError"
            )

    async def _invoke_single_model(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        custom_api_keys: Optional[Dict[str, str]] = None
    ) -> ProviderResponse:
        """Dispatch a single model generation request with timeout protection."""
        # Parse provider and model name
        parts = model_id.split(":", 1)
        if len(parts) == 2:
            provider_name, clean_model = parts
        else:
            provider_name, clean_model = "unknown", model_id

        # Check if user provided a custom key for this provider
        provider: Optional[BaseProvider] = None
        if custom_api_keys and provider_name in custom_api_keys:
            custom_key = custom_api_keys[provider_name]
            if custom_key and custom_key.strip():
                if provider_name == "openai":
                    provider = OpenAIProvider(api_key=custom_key.strip())
                elif provider_name == "anthropic":
                    provider = AnthropicProvider(api_key=custom_key.strip())
                elif provider_name == "gemini":
                    provider = GeminiProvider(api_key=custom_key.strip())
                elif provider_name == "deepseek":
                    provider = DeepSeekProvider(api_key=custom_key.strip())
                elif provider_name == "mistral":
                    provider = MistralProvider(api_key=custom_key.strip())
                elif provider_name == "ollama":
                    provider = OllamaProvider(base_url=custom_key.strip())
                elif provider_name == "openrouter":
                    provider = OpenRouterProvider(api_key=custom_key.strip())
                elif provider_name == "grok":
                    provider = GrokProvider(api_key=custom_key.strip())

        if not provider:
            provider = self.registry.get_provider(provider_name)
        start_time = time.perf_counter()

        if not provider:
            return ProviderResponse(
                success=False,
                model=model_id,
                provider=provider_name,
                answer=None,
                latency_seconds=0.0,
                error=ProviderError(
                    type="ProviderNotFoundError",
                    message=f"No provider registered for '{provider_name}'",
                    retryable=False
                )
            )

        try:
            # Wrap provider call with timeout
            response = await asyncio.wait_for(
                provider.generate(
                    model_name=clean_model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    generation_config=generation_config
                ),
                timeout=settings.generation_timeout_seconds
            )
            # Re-verify and attach calculated cost if not set
            if response.success and response.estimated_cost is None:
                response.estimated_cost = CostCalculator.calculate_cost(
                    model_id=model_id,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens
                )
            return response

        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start_time
            return ProviderResponse(
                success=False,
                model=model_id,
                provider=provider_name,
                answer=None,
                latency_seconds=elapsed,
                error=ProviderError(
                    type="TimeoutError",
                    message=f"Model generation timed out after {settings.generation_timeout_seconds} seconds.",
                    retryable=True
                )
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ProviderResponse(
                success=False,
                model=model_id,
                provider=provider_name,
                answer=None,
                latency_seconds=elapsed,
                error=ProviderError(
                    type=type(exc).__name__,
                    message=str(exc),
                    retryable=False
                )
            )

    async def generate_answers(
        self,
        models: List[str],
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        custom_api_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Concurrently run generation across all selected models.
        Returns aggregated responses and success status.
        """
        self.validate_request(models, prompt)

        tasks = [
            self._invoke_single_model(
                model_id=model_id,
                prompt=prompt,
                system_prompt=system_prompt,
                generation_config=generation_config,
                custom_api_keys=custom_api_keys
            )
            for model_id in models
        ]

        responses: List[ProviderResponse] = await asyncio.gather(*tasks)

        successful = [r for r in responses if r.success and r.answer and r.answer.strip()]
        failed = [r for r in responses if not r.success or not r.answer]

        has_sufficient_models = len(successful) >= settings.min_selected_models

        return {
            "all_responses": [r.to_dict() for r in responses],
            "successful_responses": [r.to_dict() for r in successful],
            "failed_responses": [r.to_dict() for r in failed],
            "successful_count": len(successful),
            "failed_count": len(failed),
            "has_sufficient_models": has_sufficient_models,
            "status": "SUFFICIENT" if has_sufficient_models else "INSUFFICIENT_SUCCESSFUL_MODELS"
        }
