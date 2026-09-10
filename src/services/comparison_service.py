"""Comparison service orchestrating end-to-end Mode 1 and Mode 2 evaluation pipelines."""

import time
import uuid
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.providers.base import GenerationConfig
from src.services.generation_service import GenerationService, GenerationServiceError
from src.services.cost_calculator import CostCalculator
from src.evaluation.pairwise import PairwiseEvaluator
from src.evaluation.ranking import RankingEngine
from src.evaluation.metrics import MetricsTracker
from src.evaluation.report_generator import ReportGenerator


class ComparisonService:
    """End-to-end evaluation orchestrator for Mode 1 (Generate & Compare / Single Generate) and Mode 2 (Manual Compare)."""

    def __init__(
        self,
        generation_service: Optional[GenerationService] = None,
        pairwise_evaluator: Optional[PairwiseEvaluator] = None,
        judge: Optional[Any] = None
    ):
        self.generation_service = generation_service or GenerationService()
        self.pairwise_evaluator = pairwise_evaluator or PairwiseEvaluator(judge=judge)

    async def run_generate_and_compare(
        self,
        models: List[str],
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        position_swap_check: Optional[bool] = None,
        custom_api_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Mode 1: Generate answers from selected models and evaluate pairwise (or single output if 1 model)."""
        session_id = f"gen-{uuid.uuid4().hex[:10]}"
        start_time = time.perf_counter()
        swap_check = settings.position_swap_check if position_swap_check is None else position_swap_check

        # Step 1: Concurrent Generation with optional custom API keys
        gen_result = await self.generation_service.generate_answers(
            models=models,
            prompt=prompt,
            system_prompt=system_prompt,
            generation_config=generation_config,
            custom_api_keys=custom_api_keys
        )

        all_responses = gen_result["all_responses"]
        successful_responses = gen_result["successful_responses"]

        # Step 2: Partial Failure / Insufficient check
        if not gen_result["has_sufficient_models"] or len(successful_responses) == 0:
            elapsed = time.perf_counter() - start_time
            metrics = MetricsTracker.calculate_session_metrics(
                generation_responses=all_responses,
                pairwise_comparisons=[],
                session_wall_clock_seconds=elapsed
            )
            return ReportGenerator.generate_report(
                session_id=session_id,
                mode="GENERATE_AND_COMPARE" if len(models) > 1 else "SINGLE_GENERATION",
                prompt=prompt,
                system_prompt=system_prompt,
                answers=all_responses,
                pairwise_comparisons=[],
                rankings=[],
                metrics=metrics,
                status="INSUFFICIENT_SUCCESSFUL_MODELS"
            )

        # Step 3: Single-model bypass (no pairwise judge evaluation needed)
        if len(models) == 1:
            elapsed = time.perf_counter() - start_time
            metrics = MetricsTracker.calculate_session_metrics(
                generation_responses=all_responses,
                pairwise_comparisons=[],
                session_wall_clock_seconds=elapsed
            )
            rankings = [{
                "rank": 1,
                "model_id": successful_responses[0]["model"],
                "model_name": successful_responses[0].get("model_name") or successful_responses[0]["model"],
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "win_rate": 1.0,
                "score": 100.0,
                "total_matches": 0
            }]
            return ReportGenerator.generate_report(
                session_id=session_id,
                mode="SINGLE_GENERATION",
                prompt=prompt,
                system_prompt=system_prompt,
                answers=all_responses,
                pairwise_comparisons=[],
                rankings=rankings,
                metrics=metrics,
                status="COMPLETED"
            )

        # If multiple models were selected but only 1 succeeded
        if len(successful_responses) < 2:
            elapsed = time.perf_counter() - start_time
            metrics = MetricsTracker.calculate_session_metrics(
                generation_responses=all_responses,
                pairwise_comparisons=[],
                session_wall_clock_seconds=elapsed
            )
            rankings = [{
                "rank": 1,
                "model_id": successful_responses[0]["model"],
                "model_name": successful_responses[0].get("model_name") or successful_responses[0]["model"],
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "win_rate": 1.0,
                "score": 100.0,
                "total_matches": 0
            }]
            return ReportGenerator.generate_report(
                session_id=session_id,
                mode="GENERATE_AND_COMPARE",
                prompt=prompt,
                system_prompt=system_prompt,
                answers=all_responses,
                pairwise_comparisons=[],
                rankings=rankings,
                metrics=metrics,
                status="COMPLETED_WITH_WARNINGS"
            )

        # Step 4: Multiple models succeeded - Run Pairwise Evaluation
        model_answers = [
            {
                "model_id": r["model"],
                "model_name": r.get("model_name") or r["model"],
                "answer": r["answer"]
            }
            for r in successful_responses
        ]

        eval_result = await self.pairwise_evaluator.evaluate_all_pairs(
            problem=prompt,
            model_answers=model_answers,
            position_swap_check=swap_check
        )
        comparisons = eval_result["comparisons"]

        # Step 5: Ranking Engine
        all_model_ids = [m["model_id"] for m in model_answers]
        name_map = {m["model_id"]: m["model_name"] for m in model_answers}
        rankings = RankingEngine.rank_models(
            comparisons=comparisons,
            all_model_ids=all_model_ids,
            model_name_map=name_map
        )

        # Step 6: Session Metrics
        elapsed = time.perf_counter() - start_time
        metrics = MetricsTracker.calculate_session_metrics(
            generation_responses=all_responses,
            pairwise_comparisons=comparisons,
            session_wall_clock_seconds=elapsed
        )

        # Determine Final Status
        status = "COMPLETED"
        if gen_result["failed_count"] > 0 or eval_result["failed_comparisons"] > 0:
            status = "COMPLETED_WITH_WARNINGS"

        return ReportGenerator.generate_report(
            session_id=session_id,
            mode="GENERATE_AND_COMPARE",
            prompt=prompt,
            system_prompt=system_prompt,
            answers=all_responses,
            pairwise_comparisons=comparisons,
            rankings=rankings,
            metrics=metrics,
            status=status
        )

    async def run_manual_compare(
        self,
        problem: str,
        answers: List[Dict[str, str]],
        position_swap_check: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Mode 2: Evaluate manually entered candidate answers pairwise."""
        session_id = f"man-{uuid.uuid4().hex[:10]}"
        start_time = time.perf_counter()
        swap_check = settings.position_swap_check if position_swap_check is None else position_swap_check

        # Validation
        if not problem or not problem.strip():
            raise GenerationServiceError("Problem cannot be empty.", "EmptyProblemError")

        if len(answers) < 2:
            raise GenerationServiceError(
                "At least 2 answers are required for comparison.",
                "InsufficientAnswersError"
            )

        if len(answers) > settings.max_selected_models:
            raise GenerationServiceError(
                f"At most {settings.max_selected_models} answers can be compared (got {len(answers)}).",
                "ExcessiveAnswersError"
            )

        model_names = [a.get("model_name", "").strip() for a in answers]
        if any(not name for name in model_names):
            raise GenerationServiceError("All model names must be provided.", "EmptyModelNameError")

        if len(set(model_names)) != len(model_names):
            raise GenerationServiceError("Model names must be unique.", "DuplicateModelNameError")

        for a in answers:
            if not a.get("answer", "").strip():
                raise GenerationServiceError(
                    f"Answer for model '{a.get('model_name')}' cannot be empty.",
                    "EmptyAnswerError"
                )

        # Format answers
        formatted_answers = []
        for a in answers:
            cost_info = CostCalculator.format_manual_cost()
            formatted_answers.append({
                "model_id": a["model_name"],
                "model_name": a["model_name"],
                "provider": "manual",
                "answer": a["answer"],
                "latency_seconds": 0.0,
                "input_tokens": None,
                "output_tokens": None,
                "estimated_cost": cost_info["estimated_cost"],
                "cost_source": cost_info["cost_source"],
                "success": True,
                "raw_metadata": {"manual_input": True}
            })

        # Run Pairwise Evaluation
        eval_result = await self.pairwise_evaluator.evaluate_all_pairs(
            problem=problem,
            model_answers=formatted_answers,
            position_swap_check=swap_check
        )
        comparisons = eval_result["comparisons"]

        # Ranking
        all_model_ids = [a["model_name"] for a in answers]
        name_map = {a["model_name"]: a["model_name"] for a in answers}
        rankings = RankingEngine.rank_models(
            comparisons=comparisons,
            all_model_ids=all_model_ids,
            model_name_map=name_map
        )

        # Metrics
        elapsed = time.perf_counter() - start_time
        metrics = MetricsTracker.calculate_session_metrics(
            generation_responses=formatted_answers,
            pairwise_comparisons=comparisons,
            session_wall_clock_seconds=elapsed
        )

        status = "COMPLETED" if eval_result["failed_comparisons"] == 0 else "COMPLETED_WITH_WARNINGS"

        return ReportGenerator.generate_report(
            session_id=session_id,
            mode="MANUAL_COMPARE",
            prompt=problem,
            system_prompt=None,
            answers=formatted_answers,
            pairwise_comparisons=comparisons,
            rankings=rankings,
            metrics=metrics,
            status=status
        )
