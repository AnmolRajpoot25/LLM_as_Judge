from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from src.config.settings import settings
from src.config.pricing import MODEL_PRICING, get_model_pricing
from src.providers.base import BaseProvider
from src.providers.mock_provider import MockProvider
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.gemini_provider import GeminiProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.mistral_provider import MistralProvider
from src.providers.ollama_provider import OllamaProvider
from src.providers.openrouter_provider import OpenRouterProvider
from src.providers.grok_provider import GrokProvider


@dataclass
class ModelMetadata:
    id: str  # format: 'provider:model'
    name: str  # Display name, e.g. 'GPT-4o'
    provider: str  # 'openai', 'anthropic', etc.
    enabled: bool = True
    available: bool = False
    pricing: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModelRegistry:
    """Registry maintaining available models, provider mappings, and availability state."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._models: Dict[str, ModelMetadata] = {}
        self._init_default_catalog()

    def _init_default_catalog(self):
        # Register all supported production providers
        self.register_provider(OpenAIProvider())
        self.register_provider(AnthropicProvider())
        self.register_provider(GeminiProvider())
        self.register_provider(DeepSeekProvider())
        self.register_provider(MistralProvider())
        self.register_provider(OpenRouterProvider())
        self.register_provider(GrokProvider())
        self.register_provider(OllamaProvider())

        # Catalog of models supported by the platform (Production real models)
        catalog = [
            # Google Gemini
            ("gemini:gemini-1.5-pro", "Gemini 1.5 Pro", "gemini", "Google's capable large context model"),
            ("gemini:gemini-1.5-flash", "Gemini 1.5 Flash", "gemini", "Google's fast multimodal model"),
            ("gemini:gemini-2.0-flash", "Gemini 2.0 Flash", "gemini", "Next generation speed and multimodal capabilities"),

            # OpenRouter Free Tier
            ("openrouter:google/gemini-2.0-flash-lite:free", "Gemini 2.0 Flash Lite (Free)", "openrouter", "Free low-latency Google model via OpenRouter"),
            ("openrouter:meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (Free)", "openrouter", "Free flagship open weights by Meta via OpenRouter"),
            ("openrouter:deepseek/deepseek-r1:free", "DeepSeek R1 Reasoning (Free)", "openrouter", "Free advanced reasoning model via OpenRouter"),
            ("openrouter:qwen/qwen-2.5-72b-instruct:free", "Qwen 2.5 72B (Free)", "openrouter", "Free leading open-weight LLM by Alibaba via OpenRouter"),
            ("openrouter:nvidia/nemotron-3-super-120b-a12b:free", "Nemotron 120B (Free)", "openrouter", "Free flagship reasoning LLM by NVIDIA via OpenRouter"),
            ("openrouter:nvidia/nemotron-3-ultra-550b-a55b:free", "Nemotron 550B (Free)", "openrouter", "Free frontier 550B powerhouse by NVIDIA via OpenRouter"),
            ("openrouter:nvidia/nemotron-3.5-lightning:free", "Nemotron 3.5 Lightning (Free)", "openrouter", "Ultra-fast free reasoning model by NVIDIA via OpenRouter"),

            # OpenRouter Paid Tier
            ("openrouter:anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet (OpenRouter)", "openrouter", "Anthropic flagship via OpenRouter"),
            ("openrouter:openai/gpt-4o", "GPT-4o (OpenRouter)", "openrouter", "OpenAI multimodal flagship via OpenRouter"),

            # xAI Grok
            ("grok:grok-2-latest", "Grok 2", "grok", "xAI's flagship frontier reasoning model"),
            ("grok:grok-2-vision-1212", "Grok 2 Vision", "grok", "xAI's multimodal visual understanding model"),
            ("grok:grok-beta", "Grok Beta", "grok", "xAI experimental model preview"),

            # OpenAI
            ("openai:gpt-4o", "GPT-4o", "openai", "OpenAI's flagship multimodal model"),
            ("openai:gpt-4o-mini", "GPT-4o Mini", "openai", "Fast and lightweight model"),
            ("openai:gpt-4.1", "GPT-4.1", "openai", "Next-gen GPT architecture"),

            # Anthropic
            ("anthropic:claude-3-5-sonnet", "Claude 3.5 Sonnet", "anthropic", "Anthropic's most intelligent model"),
            ("anthropic:claude-3-5-haiku", "Claude 3.5 Haiku", "anthropic", "Anthropic's fastest model"),

            # DeepSeek
            ("deepseek:deepseek-chat", "DeepSeek V3", "deepseek", "High capability open-weight reasoning API"),
            ("deepseek:deepseek-reasoner", "DeepSeek R1", "deepseek", "Reasoning model trained with RL"),

            # Mistral
            ("mistral:mistral-large-latest", "Mistral Large", "mistral", "Mistral's flagship enterprise model"),
            ("mistral:mistral-small-latest", "Mistral Small", "mistral", "Mistral's cost-effective low-latency model"),

            # Ollama (Local open source)
            ("ollama:qwen2.5:7b", "Ollama: Qwen 2.5 7B", "ollama", "Locally served Qwen 2.5 7B model"),
            ("ollama:llama3.1:8b", "Ollama: Llama 3.1 8B", "ollama", "Locally served Llama 3.1 8B model"),
            ("ollama:deepseek-r1:8b", "Ollama: DeepSeek R1 8B", "ollama", "Locally served DeepSeek R1 8B model"),
        ]

        for model_id, name, provider, desc in catalog:
            pricing = get_model_pricing(model_id)
            self._models[model_id] = ModelMetadata(
                id=model_id,
                name=name,
                provider=provider,
                enabled=True,
                available=False,
                pricing=pricing,
                description=desc
            )

    def register_provider(self, provider: BaseProvider) -> None:
        """Register or override an active provider instance."""
        self._providers[provider.provider_name] = provider

    def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        return self._providers.get(provider_name)

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        return self._models.get(model_id)

    def is_provider_available(self, provider_name: str) -> bool:
        provider = self._providers.get(provider_name)
        if provider:
            return provider.is_available()
        # Fallback check on API keys from settings
        key_map = {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "gemini": bool(settings.google_api_key or getattr(settings, "gemini_api_key", None)),
            "deepseek": bool(settings.deepseek_api_key),
            "mistral": bool(settings.mistral_api_key),
            "openrouter": bool(settings.openrouter_api_key),
            "grok": bool(settings.grok_api_key or getattr(settings, "xai_api_key", None)),
            "ollama": True  # Ollama reachability checked dynamically
        }
        return key_map.get(provider_name, False)

    def list_models(self, user_providers: Optional[Any] = None) -> List[Dict[str, Any]]:
        """List all models with dynamic availability computation including per-user keys."""
        result = []
        user_prov_set = {p.lower() for p in user_providers} if user_providers else set()
        for model_id, meta in self._models.items():
            is_avail = self.is_provider_available(meta.provider)
            if not is_avail and meta.provider.lower() in user_prov_set:
                is_avail = True
            data = meta.to_dict()
            data["available"] = is_avail
            result.append(data)
        return result


# Global default registry instance
model_registry = ModelRegistry()
