"""Pairwise evaluation service using combinations and Qwen JudgeEvaluator."""

import asyncio
import itertools
import time
import uuid
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.judge.model_loader import judge_manager


class PairwiseEvaluator:
    """Orchestrates pairwise LLM evaluations using combinations."""

    def __init__(self, judge: Optional[Any] = None, concurrency_lock: Optional[asyncio.Lock] = None):
        self.judge = judge
        self.lock = concurrency_lock or judge_manager.lock

    def _get_judge(self):
        return self.judge or judge_manager.get_judge()

    async def _evaluate_pair_safe(
        self,
        problem: str,
        answer_a: str,
        answer_b: str
    ) -> Dict[str, Any]:
        """Invoke judge evaluation with timeout and GPU concurrency lock."""
        judge = self._get_judge()
        start_time = time.perf_counter()

        async with self.lock:
            try:
                # Run synchronous judge evaluation in worker thread so event loop is not blocked
                result = await asyncio.wait_for(
                    asyncio.to_thread(judge.evaluate, problem, answer_a, answer_b),
                    timeout=settings.judge_timeout_seconds
                )
                latency = time.perf_counter() - start_time
                return {
                    "success": True,
                    "result": result["result"],
                    "raw_response": result.get("raw_response"),
                    "attempts": result.get("attempts", 1),
                    "latency_seconds": round(latency, 3),
                    "error": None
                }
            except asyncio.TimeoutError:
                latency = time.perf_counter() - start_time
                return {
                    "success": False,
                    "result": None,
                    "raw_response": None,
                    "attempts": 1,
                    "latency_seconds": round(latency, 3),
                    "error": {
                        "type": "JudgeTimeoutError",
                        "message": f"Judge evaluation timed out after {settings.judge_timeout_seconds}s"
                    }
                }
            except Exception as exc:
                latency = time.perf_counter() - start_time
                return {
                    "success": False,
                    "result": None,
                    "raw_response": None,
                    "attempts": 1,
                    "latency_seconds": round(latency, 3),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc)
                    }
                }

    async def evaluate_all_pairs(
        self,
        problem: str,
        model_answers: List[Dict[str, Any]],
        position_swap_check: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate all N*(N-1)/2 pairs of model answers.
        If position_swap_check is True, also evaluates swapped order (B vs A) to verify consistency.
        """
        if len(model_answers) < 2:
            raise ValueError(f"At least 2 model answers are required for pairwise comparison (got {len(model_answers)}).")

        comparisons = []
        pairs = list(itertools.combinations(model_answers, 2))

        for pair_idx, (model_a_info, model_b_info) in enumerate(pairs, start=1):
            comparison_id = f"cmp-{uuid.uuid4().hex[:8]}"

            ans_a = model_a_info["answer"]
            ans_b = model_b_info["answer"]

            eval_res = await self._evaluate_pair_safe(
                problem=problem,
                answer_a=ans_a,
                answer_b=ans_b
            )

            # Map the relative winner 'A' or 'B' to the actual model identifier
            actual_winner = None
            if eval_res["success"] and eval_res["result"]:
                rel_winner = eval_res["result"]["winner"]
                if rel_winner == "A":
                    actual_winner = model_a_info.get("model_id") or model_a_info.get("model_name")
                elif rel_winner == "B":
                    actual_winner = model_b_info.get("model_id") or model_b_info.get("model_name")
                else:
                    actual_winner = "TIE"

            comparison_entry = {
                "comparison_id": comparison_id,
                "pair_number": pair_idx,
                "model_a": {
                    "model_id": model_a_info.get("model_id", "unknown"),
                    "name": model_a_info.get("model_name") or model_a_info.get("model_id", "Model A")
                },
                "model_b": {
                    "model_id": model_b_info.get("model_id", "unknown"),
                    "name": model_b_info.get("model_name") or model_b_info.get("model_id", "Model B")
                },
                "winner_model_id": actual_winner,
                "success": eval_res["success"],
                "judge_latency": eval_res["latency_seconds"],
                "judge_result": eval_res["result"],
                "raw_judge_response": eval_res.get("raw_response"),
                "error": eval_res["error"],
                "position_swap_check": None
            }

            # Optional Position Swap Check
            if position_swap_check and eval_res["success"]:
                swap_res = await self._evaluate_pair_safe(
                    problem=problem,
                    answer_a=ans_b,
                    answer_b=ans_a
                )
                if swap_res["success"] and swap_res["result"]:
                    swap_rel_winner = swap_res["result"]["winner"]
                    # In swap: Candidate A is model_b, Candidate B is model_a
                    if swap_rel_winner == "A":
                        swap_winner_id = model_b_info.get("model_id") or model_b_info.get("model_name")
                    elif swap_rel_winner == "B":
                        swap_winner_id = model_a_info.get("model_id") or model_a_info.get("model_name")
                    else:
                        swap_winner_id = "TIE"

                    is_consistent = (swap_winner_id == actual_winner)
                    comparison_entry["position_swap_check"] = {
                        "executed": True,
                        "consistent": is_consistent,
                        "original_winner": actual_winner,
                        "swapped_winner": swap_winner_id,
                        "swap_judge_result": swap_res["result"]
                    }
                else:
                    comparison_entry["position_swap_check"] = {
                        "executed": True,
                        "consistent": False,
                        "error": swap_res["error"]
                    }

            comparisons.append(comparison_entry)

        total_comparisons = len(comparisons)
        successful_comparisons = sum(1 for c in comparisons if c["success"])
        failed_comparisons = total_comparisons - successful_comparisons

        return {
            "comparisons": comparisons,
            "total_comparisons": total_comparisons,
            "successful_comparisons": successful_comparisons,
            "failed_comparisons": failed_comparisons
        }
