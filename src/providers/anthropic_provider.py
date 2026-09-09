"""Anthropic Claude provider implementation."""

import time
from typing import Optional, Dict, Any
import httpx
from src.config.settings import settings
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Messages API."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key or settings.anthropic_api_key
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "anthropic"

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
                    message="ANTHROPIC_API_KEY is not configured in environment.",
                    retryable=False
                )
            )

        cfg = generation_config or GenerationConfig()
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": cfg.max_tokens or 1024,
            "temperature": cfg.temperature,
            **cfg.extra_params
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.generation_timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers
                )
                elapsed = time.perf_counter() - start_time

                if resp.status_code == 429:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="RateLimitError",
                            message="Anthropic rate limit exceeded.",
                            retryable=True
                        )
                    )
                elif resp.status_code == 401:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="AuthenticationError",
                            message="Invalid Anthropic API key.",
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
                            message=f"Anthropic error HTTP {resp.status_code}: {resp.text[:200]}",
                            retryable=resp.status_code >= 500
                        )
                    )

                data = resp.json()
                content_blocks = data.get("content", [])
                answer = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")

                return ProviderResponse(
                    success=True,
                    model=model_name,
                    provider=self.provider_name,
                    answer=answer,
                    latency_seconds=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    raw_metadata={"id": data.get("id"), "stop_reason": data.get("stop_reason")}
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
                    message=f"Anthropic request timed out after {settings.generation_timeout_seconds}s.",
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
