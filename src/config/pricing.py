"""Centralized LLM API pricing configuration."""

from typing import Optional, Dict, Any

PRICING_VERSION = "2025-02"
PRICING_CURRENCY = "USD"

MODEL_PRICING: Dict[str, Dict[str, Any]] = {
    # OpenAI
    "openai:gpt-4o": {
        "provider": "openai",
        "model": "gpt-4o",
        "input_price_per_million": 2.50,
        "output_price_per_million": 10.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "openai:gpt-4o-mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "input_price_per_million": 0.15,
        "output_price_per_million": 0.60,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "openai:gpt-4.1": {
        "provider": "openai",
        "model": "gpt-4.1",
        "input_price_per_million": 3.00,
        "output_price_per_million": 12.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },

    # Anthropic
    "anthropic:claude-3-5-sonnet": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "input_price_per_million": 3.00,
        "output_price_per_million": 15.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "anthropic:claude-3-5-haiku": {
        "provider": "anthropic",
        "model": "claude-3-5-haiku-20241022",
        "input_price_per_million": 0.80,
        "output_price_per_million": 4.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },

    # Google Gemini
    "gemini:gemini-1.5-pro": {
        "provider": "gemini",
        "model": "gemini-1.5-pro",
        "input_price_per_million": 1.25,
        "output_price_per_million": 5.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "gemini:gemini-1.5-flash": {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "input_price_per_million": 0.075,
        "output_price_per_million": 0.30,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "gemini:gemini-2.0-flash": {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "input_price_per_million": 0.10,
        "output_price_per_million": 0.40,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },

    # DeepSeek
    "deepseek:deepseek-chat": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "input_price_per_million": 0.14,
        "output_price_per_million": 0.28,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "deepseek:deepseek-reasoner": {
        "provider": "deepseek",
        "model": "deepseek-reasoner",
        "input_price_per_million": 0.55,
        "output_price_per_million": 2.19,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },

    # Mistral
    "mistral:mistral-large-latest": {
        "provider": "mistral",
        "model": "mistral-large-latest",
        "input_price_per_million": 2.00,
        "output_price_per_million": 6.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "mistral:mistral-small-latest": {
        "provider": "mistral",
        "model": "mistral-small-latest",
        "input_price_per_million": 0.20,
        "output_price_per_million": 0.60,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },

    # Ollama (Local open source = 0.00)
    "ollama:qwen2.5:7b": {
        "provider": "ollama",
        "model": "qwen2.5:7b",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "ollama:llama3.1:8b": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "ollama:deepseek-r1:8b": {
        "provider": "ollama",
        "model": "deepseek-r1:8b",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },

    # OpenRouter Free Tier ($0.00)
    "openrouter:google/gemini-2.0-flash-lite:free": {
        "provider": "openrouter",
        "model": "google/gemini-2.0-flash-lite:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:meta-llama/llama-3.3-70b-instruct:free": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:deepseek/deepseek-r1:free": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-r1:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:qwen/qwen-2.5-72b-instruct:free": {
        "provider": "openrouter",
        "model": "qwen/qwen-2.5-72b-instruct:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:nvidia/nemotron-3-super-120b-a12b:free": {
        "provider": "openrouter",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:nvidia/nemotron-3-ultra-550b-a55b:free": {
        "provider": "openrouter",
        "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:nvidia/nemotron-3.5-lightning:free": {
        "provider": "openrouter",
        "model": "nvidia/nemotron-3.5-lightning:free",
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0,
        "currency": PRICING_CURRENCY,
        "estimated": False,
        "pricing_date": PRICING_VERSION
    },

    # OpenRouter Paid Tier
    "openrouter:anthropic/claude-3.5-sonnet": {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "input_price_per_million": 3.00,
        "output_price_per_million": 15.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "openrouter:openai/gpt-4o": {
        "provider": "openrouter",
        "model": "openai/gpt-4o",
        "input_price_per_million": 2.50,
        "output_price_per_million": 10.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },

    # xAI Grok
    "grok:grok-2-latest": {
        "provider": "grok",
        "model": "grok-2-latest",
        "input_price_per_million": 2.00,
        "output_price_per_million": 10.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "grok:grok-2-vision-1212": {
        "provider": "grok",
        "model": "grok-2-vision-1212",
        "input_price_per_million": 2.00,
        "output_price_per_million": 10.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    },
    "grok:grok-beta": {
        "provider": "grok",
        "model": "grok-beta",
        "input_price_per_million": 5.00,
        "output_price_per_million": 15.00,
        "currency": PRICING_CURRENCY,
        "estimated": True,
        "pricing_date": PRICING_VERSION
    }
}


def get_model_pricing(model_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve pricing metadata for a given model key (e.g. 'openai:gpt-4o')."""
    return MODEL_PRICING.get(model_key)
