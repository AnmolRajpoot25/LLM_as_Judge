





















































































































"""Cost calculation service for model invocations and token usage."""

from typing import Optional, Dict, Any
from src.config.pricing import get_model_pricing


class CostCalculator:
    """Calculates financial costs for model generations based on token counts and pricing tables."""

    @staticmethod
    def calculate_cost(
        model_id: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int]
    ) -> Optional[float]:
        """
        Calculate total cost for a model invocation.
        Returns None if input_tokens or output_tokens are None or if pricing is not configured.
        """
        if input_tokens is None or output_tokens is None:
            return None

        pricing = get_model_pricing(model_id)
        if not pricing:
            # Fallback check: try stripping prefix or matching standard name
            # If still unknown, return None (do not invent costs)
            return None

        in_price = pricing.get("input_price_per_million", 0.0)
        out_price = pricing.get("output_price_per_million", 0.0)

        in_cost = (input_tokens / 1_000_000.0) * in_price
        out_cost = (output_tokens / 1_000_000.0) * out_price

        return round(in_cost + out_cost, 6)

    @staticmethod
    def format_manual_cost() -> Dict[str, Any]:
        """Return standardized cost descriptor for manually provided answers."""
        return {
            "estimated_cost": None,
            "cost_source": "manual input",
            "is_manual": True
        }
