"""xAI Grok provider implementation."""

import time
from typing import Optional, Dict, Any
import httpx
from src.config.settings import settings
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig


class GrokProvider(BaseProvider):
    """Provider for xAI Grok API (OpenAI-compatible /v1/chat/completions)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.x.ai/v1"
    ):
        self.api_key = api_key or settings.grok_api_key or settings.xai_api_key
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "grok"

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
                    message="GROK_API_KEY / XAI_API_KEY is not configured.",
                    retryable=False
                )
            )

        clean_model = model_name
        if clean_model.startswith("grok:"):
            clean_model = clean_model.replace("grok:", "", 1)

        # Auto-detect Groq keys (gsk_...) vs xAI Grok keys (xai-...)
        target_url = self.base_url
        if self.api_key.startswith("gsk_"):
            target_url = "https://api.groq.com/openai/v1"
            if clean_model in ("grok-2-latest", "grok-2-vision-1212", "grok-beta"):
                clean_model = "groq/compound"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        cfg = generation_config or GenerationConfig()
        payload = {
            "model": clean_model,
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
                    f"{target_url}/chat/completions",
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
                            message="xAI Grok rate limit reached.",
                            retryable=True
                        )
                    )
                elif resp.status_code in (401, 403):
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="AuthenticationError",
                            message="Invalid xAI Grok API key.",
                            retryable=False
                        )
                    )
                elif resp.status_code != 200:
                    err_text = resp.text[:300]
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="APIError",
                            message=f"xAI Grok HTTP {resp.status_code}: {err_text}",
                            retryable=resp.status_code >= 500
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
                            message="Grok returned no completions.",
                            retryable=False
                        )
                    )

                answer = choices[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens")
                output_tokens = usage.get("completion_tokens")

                return ProviderResponse(
                    success=True,
                    model=model_name,
                    provider=self.provider_name,
                    answer=answer,
                    latency_seconds=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    raw_metadata=data
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
                    message=f"Grok request timed out after {settings.generation_timeout_seconds}s.",
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
