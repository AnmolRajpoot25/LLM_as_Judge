"""Mistral API provider implementation."""

import time
from typing import Optional, Dict, Any
import httpx
from src.config.settings import settings
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig


class MistralProvider(BaseProvider):
    """Provider for Mistral AI API."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.mistral.ai/v1"):
        self.api_key = api_key or settings.mistral_api_key
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "mistral"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> ProviderResponse:
        start_time = time.perf_counter()

        if not self.is_available():
            return ProviderResponse(
                success=False,
                model=model_name,
                provider=self.provider_name,
                answer=None,
                latency_seconds=0.0,
                error=ProviderError(
                    type="ConfigurationError",
                    message="MISTRAL_API_KEY is not configured in environment.",
                    retryable=False
                )
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        cfg = generation_config or GenerationConfig()
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            **cfg.extra_params
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.generation_timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                elapsed = time.perf_counter() - start_time

                if resp.status_code != 200:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="APIError",
                            message=f"Mistral error HTTP {resp.status_code}: {resp.text[:200]}",
                            retryable=resp.status_code in [429, 500, 502, 503]
                        )
                    )

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="EmptyResponseError",
                            message="Mistral returned empty choices.",
                            retryable=False
                        )
                    )

                answer = choices[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})

                return ProviderResponse(
                    success=True,
                    model=model_name,
                    provider=self.provider_name,
                    answer=answer,
                    latency_seconds=elapsed,
                    input_tokens=usage.get("prompt_tokens"),
                    output_tokens=usage.get("completion_tokens"),
                    raw_metadata={"id": data.get("id")}
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
                    message=f"Mistral request timed out after {settings.generation_timeout_seconds}s.",
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
