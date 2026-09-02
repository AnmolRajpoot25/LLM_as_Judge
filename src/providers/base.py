from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class GenerationConfig:
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: Optional[float] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderError:
    type: str
    message: str
    retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderResponse:
    success: bool
    model: str
    provider: str
    answer: Optional[str] = None
    latency_seconds: float = 0.0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ProviderError] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "success": self.success,
            "model": self.model,
            "provider": self.provider,
            "answer": self.answer,
            "latency_seconds": round(self.latency_seconds, 3),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost": self.estimated_cost,
            "raw_metadata": self.raw_metadata,
        }
        if self.error:
            data["error"] = self.error.to_dict()
        else:
            data["error"] = None
        return data


class BaseProvider(ABC):
    """Abstract Base Class for all LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'openai', 'anthropic', 'mock')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""
        pass

    @abstractmethod
    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> ProviderResponse:
        """Generate response from model and return standardized ProviderResponse."""
        pass
