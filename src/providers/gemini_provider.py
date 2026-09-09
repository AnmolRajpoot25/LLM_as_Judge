"""Google Gemini provider implementation."""

import time
from typing import Optional, Dict, Any
import httpx
from src.config.settings import settings
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini API via REST generateContent."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.google_api_key

    @property
    def provider_name(self) -> str:
        return "gemini"

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
                    message="GOOGLE_API_KEY is not configured in environment.",
                    retryable=False
                )
            )

        cfg = generation_config or GenerationConfig()
        clean_model = model_name
        if clean_model.startswith("gemini:"):
            clean_model = clean_model.replace("gemini:", "")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"

        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTION:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"}]
            })
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": cfg.temperature,
                "maxOutputTokens": cfg.max_tokens,
                **cfg.extra_params
            }
        }

        try:
            async with httpx.AsyncClient(timeout=settings.generation_timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                elapsed = time.perf_counter() - start_time

                if resp.status_code != 200:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="APIError",
                            message=f"Gemini API error HTTP {resp.status_code}: {resp.text[:200]}",
                            retryable=resp.status_code in [429, 500, 503]
                        )
                    )

                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return ProviderResponse(
                        success=False,
                        model=model_name,
                        provider=self.provider_name,
                        latency_seconds=elapsed,
                        error=ProviderError(
                            type="EmptyResponseError",
                            message="Gemini returned no candidates (possibly filtered).",
                            retryable=False
                        )
                    )

                parts = candidates[0].get("content", {}).get("parts", [])
                answer = "".join(p.get("text", "") for p in parts)

                meta = data.get("usageMetadata", {})
                input_tokens = meta.get("promptTokenCount")
                output_tokens = meta.get("candidatesTokenCount")

                return ProviderResponse(
                    success=True,
                    model=model_name,
                    provider=self.provider_name,
                    answer=answer,
                    latency_seconds=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    raw_metadata={"finishReason": candidates[0].get("finishReason")}
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
                    message=f"Gemini request timed out after {settings.generation_timeout_seconds}s.",
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
