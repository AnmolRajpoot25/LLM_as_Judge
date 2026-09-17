"""Pairwise evaluation service using combinations and remote Qwen JudgeEvaluator."""

import asyncio
import itertools
import time
import uuid
from typing import List, Dict, Any, Optional

from src.config.settings import settings
from src.judge.evaluator import JudgeEvaluator


class PairwiseEvaluator:
    """
    Orchestrates pairwise LLM evaluations.

    The actual judging is performed by the fine-tuned
    Qwen2.5-7B model deployed on Hugging Face ZeroGPU.
    """

    def __init__(
        self,
        judge: Optional[Any] = None,
        concurrency_lock: Optional[asyncio.Lock] = None
    ):
        """
        Initialize the pairwise evaluator.

        A JudgeEvaluator can be injected for testing or custom
        implementations. Otherwise, the remote Hugging Face
        JudgeEvaluator is used automatically.
        """

        self.judge = judge or JudgeEvaluator()

        # ZeroGPU should receive one inference request at a time.
        self.lock = concurrency_lock or asyncio.Lock()

    def _get_judge(self):
        """Return the configured judge."""
        return self.judge

    # ========================================================
    # SINGLE PAIR EVALUATION
    # ========================================================

    async def _evaluate_pair_safe(
        self,
        problem: str,
        answer_a: str,
        answer_b: str
    ) -> Dict[str, Any]:
        """
        Evaluate one pair safely.

        The synchronous Gradio client runs inside a worker thread
        so that the FastAPI event loop remains responsive.
        """

        judge = self._get_judge()
        start_time = time.perf_counter()

        # ----------------------------------------------------
        # Serialize judge requests.
        #
        # This is important because the HF Space is running
        # the model on ZeroGPU.
        # ----------------------------------------------------

        async with self.lock:

            try:

                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        judge.evaluate,
                        problem,
                        answer_a,
                        answer_b
                    ),
                    timeout=settings.judge_timeout_seconds
                )

                latency = (
                    time.perf_counter() - start_time
                )

                return {
                    "success": True,
                    "result": result["result"],
                    "raw_response": result.get(
                        "raw_response"
                    ),
                    "attempts": result.get(
                        "attempts",
                        1
                    ),
                    "latency_seconds": round(
                        latency,
                        3
                    ),
                    "error": None
                }

            except asyncio.TimeoutError:

                latency = (
                    time.perf_counter() - start_time
                )

                return {
                    "success": False,
                    "result": None,
                    "raw_response": None,
                    "attempts": 1,
                    "latency_seconds": round(
                        latency,
                        3
                    ),
                    "error": {
                        "type": "JudgeTimeoutError",
                        "message": (
                            f"Judge evaluation timed out "
                            f"after "
                            f"{settings.judge_timeout_seconds}s"
                        )
                    }
                }

            except Exception as exc:

                latency = (
                    time.perf_counter() - start_time
                )

                return {
                    "success": False,
                    "result": None,
                    "raw_response": None,
                    "attempts": 1,
                    "latency_seconds": round(
                        latency,
                        3
                    ),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc)
                    }
                }

    # ========================================================
    # WINNER MAPPING
    # ========================================================

    @staticmethod
    def _map_winner(
        winner: str,
        model_a_info: Dict[str, Any],
        model_b_info: Dict[str, Any]
    ) -> str:
        """
        Convert relative judge winner A/B into the actual
        model identifier.
        """

        if winner == "A":
            return (
                model_a_info.get("model_id")
                or model_a_info.get("model_name")
                or "unknown"
            )

        if winner == "B":
            return (
                model_b_info.get("model_id")
                or model_b_info.get("model_name")
                or "unknown"
            )

        return "TIE"

    # ========================================================
    # ALL PAIRWISE COMPARISONS
    # ========================================================

    async def evaluate_all_pairs(
        self,
        problem: str,
        model_answers: List[Dict[str, Any]],
        position_swap_check: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate all N*(N-1)/2 pairs of model answers.

        If position_swap_check is True:

            Original:
                A vs B

            Swapped:
                B vs A

        This is used to detect position bias in the judge.
        """

        # ----------------------------------------------------
        # Validate number of models.
        # ----------------------------------------------------

        if len(model_answers) < 2:
            raise ValueError(
                "At least 2 model answers are required "
                "for pairwise comparison "
                f"(got {len(model_answers)})."
            )

        comparisons = []

        # ----------------------------------------------------
        # Generate every unique pair.
        # ----------------------------------------------------

        pairs = list(
            itertools.combinations(
                model_answers,
                2
            )
        )

        # ----------------------------------------------------
        # Evaluate each pair.
        # ----------------------------------------------------

        for pair_idx, (
            model_a_info,
            model_b_info
        ) in enumerate(
            pairs,
            start=1
        ):

            comparison_id = (
                f"cmp-{uuid.uuid4().hex[:8]}"
            )

            ans_a = model_a_info["answer"]
            ans_b = model_b_info["answer"]

            # ------------------------------------------------
            # Original evaluation: A vs B
            # ------------------------------------------------

            eval_res = await self._evaluate_pair_safe(
                problem=problem,
                answer_a=ans_a,
                answer_b=ans_b
            )

            # ------------------------------------------------
            # Map A/B to actual model.
            # ------------------------------------------------

            actual_winner = None

            if (
                eval_res["success"]
                and eval_res["result"]
            ):

                relative_winner = (
                    eval_res["result"]["winner"]
                )

                actual_winner = self._map_winner(
                    relative_winner,
                    model_a_info,
                    model_b_info
                )

            # ------------------------------------------------
            # Build comparison record.
            # ------------------------------------------------

            comparison_entry = {
                "comparison_id": comparison_id,

                "pair_number": pair_idx,

                "model_a": {
                    "model_id": model_a_info.get(
                        "model_id",
                        "unknown"
                    ),
                    "name": (
                        model_a_info.get("model_name")
                        or model_a_info.get(
                            "model_id",
                            "Model A"
                        )
                    )
                },

                "model_b": {
                    "model_id": model_b_info.get(
                        "model_id",
                        "unknown"
                    ),
                    "name": (
                        model_b_info.get("model_name")
                        or model_b_info.get(
                            "model_id",
                            "Model B"
                        )
                    )
                },

                "winner_model_id": actual_winner,

                "success": eval_res["success"],

                "judge_latency": (
                    eval_res["latency_seconds"]
                ),

                "judge_result": eval_res["result"],

                "raw_judge_response": (
                    eval_res.get(
                        "raw_response"
                    )
                ),

                "error": eval_res["error"],

                "position_swap_check": None
            }

            # =================================================
            # POSITION SWAP CHECK
            # =================================================

            if (
                position_swap_check
                and eval_res["success"]
            ):

                # --------------------------------------------
                # Swapped evaluation:
                #
                # Original:
                #   A = model A
                #   B = model B
                #
                # Swapped:
                #   A = model B
                #   B = model A
                # --------------------------------------------

                swap_res = await self._evaluate_pair_safe(
                    problem=problem,
                    answer_a=ans_b,
                    answer_b=ans_a
                )

                if (
                    swap_res["success"]
                    and swap_res["result"]
                ):

                    swap_relative_winner = (
                        swap_res["result"]["winner"]
                    )

                    # ----------------------------------------
                    # Map swapped A/B back to actual models.
                    # ----------------------------------------

                    if swap_relative_winner == "A":

                        # Swapped A = original model B
                        swap_winner_id = (
                            model_b_info.get("model_id")
                            or model_b_info.get(
                                "model_name"
                            )
                            or "unknown"
                        )

                    elif swap_relative_winner == "B":

                        # Swapped B = original model A
                        swap_winner_id = (
                            model_a_info.get("model_id")
                            or model_a_info.get(
                                "model_name"
                            )
                            or "unknown"
                        )

                    else:

                        swap_winner_id = "TIE"

                    # ----------------------------------------
                    # Compare actual model winners.
                    # ----------------------------------------

                    is_consistent = (
                        swap_winner_id
                        == actual_winner
                    )

                    comparison_entry[
                        "position_swap_check"
                    ] = {

                        "executed": True,

                        "consistent": (
                            is_consistent
                        ),

                        "original_winner": (
                            actual_winner
                        ),

                        "swapped_winner": (
                            swap_winner_id
                        ),

                        "swap_judge_result": (
                            swap_res["result"]
                        ),

                        "swap_raw_judge_response": (
                            swap_res.get(
                                "raw_response"
                            )
                        ),

                        "swap_latency": (
                            swap_res[
                                "latency_seconds"
                            ]
                        )
                    }

                else:

                    comparison_entry[
                        "position_swap_check"
                    ] = {

                        "executed": True,

                        "consistent": False,

                        "error": (
                            swap_res["error"]
                        )
                    }

            comparisons.append(
                comparison_entry
            )

        # ====================================================
        # SUMMARY
        # ====================================================

        total_comparisons = len(
            comparisons
        )

        successful_comparisons = sum(
            1
            for comparison in comparisons
            if comparison["success"]
        )

        failed_comparisons = (
            total_comparisons
            - successful_comparisons
        )

        # ----------------------------------------------------
        # Position consistency statistics.
        # ----------------------------------------------------

        swap_checks = [
            comparison["position_swap_check"]
            for comparison in comparisons
            if comparison[
                "position_swap_check"
            ] is not None
        ]

        executed_swap_checks = len(
            swap_checks
        )

        consistent_swap_checks = sum(
            1
            for check in swap_checks
            if check.get("consistent") is True
        )

        inconsistent_swap_checks = (
            executed_swap_checks
            - consistent_swap_checks
        )

        return {

            "comparisons": comparisons,

            "total_comparisons": (
                total_comparisons
            ),

            "successful_comparisons": (
                successful_comparisons
            ),

            "failed_comparisons": (
                failed_comparisons
            ),

            "position_swap_summary": {

                "enabled": (
                    position_swap_check
                ),

                "executed": (
                    executed_swap_checks
                ),

                "consistent": (
                    consistent_swap_checks
                ),

                "inconsistent": (
                    inconsistent_swap_checks
                )
            }
        }
