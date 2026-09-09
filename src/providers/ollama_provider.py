"""Ollama local model provider implementation."""

import time
from typing import Optional, Dict, Any
import httpx
from src.config.settings import settings
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig


class OllamaProvider(BaseProvider):
    """Provider for local Ollama instance (http://localhost:11434 by default)."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        """Lightweight sync check is deferred to call time or tag inspection."""
        return True

    async def check_health(self) -> bool:
        """Check if local Ollama daemon is reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> ProviderResponse:
        start_time = time.perf_counter()

        cfg = generation_config or GenerationConfig()
        clean_model = model_name
        if clean_model.startswith("ollama:"):
            clean_model = clean_model.replace("ollama:", "")

        payload = {
            "model": clean_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": cfg.temperature,
                "num_predict": cfg.max_tokens,
                **cfg.extra_params
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=settings.generation_timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                elapsed = time.perf_counter() - start_time

                if resp.status_code == 404:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="ModelNotFoundError",
                            message=f"Model '{clean_model}' is not installed in local Ollama instance. Run 'ollama pull {clean_model}'.",
                            retryable=False
                        )
                    )
                elif resp.status_code != 200:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="APIError",
                            message=f"Ollama error HTTP {resp.status_code}: {resp.text[:200]}",
                            retryable=resp.status_code >= 500
                        )
                    )

                data = resp.json()
                answer = data.get("response", "")
                input_tokens = data.get("prompt_eval_count")
                output_tokens = data.get("eval_count")

                return ProviderResponse(
                    success=True,
                    model=model_name,
                    provider=self.provider_name,
                    answer=answer,
                    latency_seconds=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=0.0,
                    raw_metadata={"total_duration": data.get("total_duration")}
                )

        except httpx.ConnectError:
            elapsed = time.perf_counter() - start_time
            return ProviderResponse(
                success=False,
                model=model_name,
                provider=self.provider_name,
                latency_seconds=elapsed,
                error=ProviderError(
                    type="ConnectionRefusedError",
                    message=f"Cannot connect to Ollama at '{self.base_url}'. Ensure the Ollama service is running.",
                    retryable=True
                )
            )
        except httpx.TimeoutException:
            elapsed = time.perf_counter() - start_time
            return ProviderResponse(
                success=False,
                model=model_name,
                provider=self.provider_name,
                latency_seconds=elapsed,
                error=ProviderError(
                    type="TimeoutError",
                    message=f"Ollama request timed out after {settings.generation_timeout_seconds}s.",
                    retryable=True
                )
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ProviderResponse(
                success=False,
                model=model_name,
                provider=self.provider_name,
                latency_seconds=elapsed,
                error=ProviderError(
                    type=type(exc).__name__,
                    message=str(exc),
                    retryable=False
                )
            )
