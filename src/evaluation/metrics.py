"""Metrics aggregation and telemetry tracking for evaluation sessions."""

from typing import List, Dict, Any, Optional


class MetricsTracker:
    """Calculates summary latency, token usage, cost, and reliability metrics."""

    @staticmethod
    def calculate_session_metrics(
        generation_responses: List[Dict[str, Any]],
        pairwise_comparisons: List[Dict[str, Any]],
        session_wall_clock_seconds: float
    ) -> Dict[str, Any]:
        # Generation metrics
        gen_latencies = [
            r["latency_seconds"] for r in generation_responses
            if r.get("latency_seconds") is not None
        ]
        avg_gen_latency = (
            round(sum(gen_latencies) / len(gen_latencies), 3)
            if gen_latencies else 0.0
        )

        total_input_tokens = sum(
            r.get("input_tokens") or 0 for r in generation_responses
        )
        total_output_tokens = sum(
            r.get("output_tokens") or 0 for r in generation_responses
        )

        # Cost calculation
        costs = [
            r.get("estimated_cost") for r in generation_responses
            if r.get("estimated_cost") is not None
        ]
        total_cost = round(sum(costs), 6) if costs else (0.0 if not costs and generation_responses else None)

        successful_models = sum(1 for r in generation_responses if r.get("success"))
        failed_models = len(generation_responses) - successful_models

        # Evaluation metrics
        judge_latencies = [
            c["judge_latency"] for c in pairwise_comparisons
            if c.get("judge_latency") is not None
        ]
        total_eval_latency = round(sum(judge_latencies), 3)
        avg_eval_latency = (
            round(total_eval_latency / len(judge_latencies), 3)
            if judge_latencies else 0.0
        )

        successful_judge = sum(1 for c in pairwise_comparisons if c.get("success"))
        failed_judge = len(pairwise_comparisons) - successful_judge

        return {
            "total_session_latency_seconds": round(session_wall_clock_seconds, 3),
            "generation": {
                "average_latency_seconds": avg_gen_latency,
                "successful_models": successful_models,
                "failed_models": failed_models,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_estimated_cost": total_cost,
                "currency": "USD"
            },
            "evaluation": {
                "total_evaluation_latency_seconds": total_eval_latency,
                "average_judge_latency_seconds": avg_eval_latency,
                "total_comparisons": len(pairwise_comparisons),
                "successful_evaluations": successful_judge,
                "failed_evaluations": failed_judge
            }
        }