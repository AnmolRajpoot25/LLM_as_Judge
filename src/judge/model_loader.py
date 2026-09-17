"""Model loader and GPU inference concurrency guard for LLM-Judge."""

import asyncio
import hashlib
import json
import logging
from typing import Optional, Any, Tuple
from src.judge.evaluator import JudgeEvaluator

logger = logging.getLogger("llm_judge.loader")


class MockJudgeEvaluator:
    """
    Mock Judge Evaluator that implements the exact JudgeEvaluator interface.
    Used for automated tests and development environments without local GPU weights.
    Evaluates answers deterministically based on answer quality heuristics.
    """

    CRITERIA = {
        "correctness": 0.40,
        "relevance": 0.20,
        "completeness": 0.15,
        "reasoning": 0.15,
        "clarity": 0.10
    }

    def __init__(self, max_new_tokens: int = 300, max_retries: int = 1):
        self.max_new_tokens = max_new_tokens
        self.max_retries = max_retries

    def evaluate(self, problem: str, answer_a: str, answer_b: str) -> dict:
        if not problem or not problem.strip():
            raise ValueError("Problem cannot be empty.")
        if not answer_a or not answer_a.strip():
            raise ValueError("Answer A cannot be empty.")
        if not answer_b or not answer_b.strip():
            raise ValueError("Answer B cannot be empty.")

        # Deterministic scoring calculation based on content depth and hash
        def score_answer(ans: str) -> dict:
            words = len(ans.split())
            code_bonus = 1 if ("```" in ans or "def " in ans or "class " in ans) else 0
            structure_bonus = 1 if ("1." in ans or "- " in ans or "###" in ans) else 0

            # Base score bounded [6, 10]
            corr = min(10, max(5, 7 + code_bonus + (1 if words > 40 else 0)))
            rel = min(10, max(6, 8 + structure_bonus))
            comp = min(10, max(5, 7 + (1 if words > 50 else 0) + structure_bonus))
            reas = min(10, max(5, 8 + code_bonus))
            clar = min(10, max(6, 8 + structure_bonus))

            final_score = round(
                corr * 0.40 + rel * 0.20 + comp * 0.15 + reas * 0.15 + clar * 0.10,
                2
            )

            return {
                "correctness": corr,
                "relevance": rel,
                "completeness": comp,
                "reasoning": reas,
                "clarity": clar,
                "feedback": f"Evaluated answer with {words} words. Structured logical flow observed.",
                "final_score": final_score
            }

        scores_a = score_answer(answer_a)
        scores_b = score_answer(answer_b)

        if scores_a["final_score"] > scores_b["final_score"]:
            winner = "A"
            reason = scores_a["feedback"]
        elif scores_b["final_score"] > scores_a["final_score"]:
            winner = "B"
            reason = scores_b["feedback"]
        else:
            winner = "TIE"
            reason = "Both answers demonstrated equivalent technical quality and depth."

        diff = abs(scores_a["final_score"] - scores_b["final_score"])
        confidence = 0.90 if diff >= 1.0 else (0.75 if diff >= 0.5 else 0.60)

        result = {
            "winner": winner,
            "scores": {
                "A": scores_a,
                "B": scores_b
            },
            "confidence": confidence,
            "reason": reason
        }

        return {
            "result": result,
            "raw_response": json.dumps({"A": scores_a, "B": scores_b}),
            "attempts": 1
        }


class JudgeManager:
    """
    Singleton manager for loading and accessing the Judge model.
    Provides an asyncio lock to serialize local GPU inference and prevent CUDA OOM.
    """

    _instance: Optional["JudgeManager"] = None
    _judge_instance: Optional[Any] = None
    _lock: Optional[asyncio.Lock] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JudgeManager, cls).__new__(cls)
            cls._instance._judge_instance = None
            cls._instance._lock = None
        return cls._instance

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def set_judge(self, judge: Any) -> None:
        """Explicitly set or inject the active judge evaluator."""
        self._judge_instance = judge

    def get_judge(self) -> Any:
        """Get the active judge, defaulting to remote Hugging Face JudgeEvaluator."""
        if self._judge_instance is None:
            from src.judge.evaluator import JudgeEvaluator
            self._judge_instance = JudgeEvaluator()
        return self._judge_instance

    def load_qwen_judge(
        self,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        max_new_tokens: int = 300,
        max_retries: int = 1
    ) -> JudgeEvaluator:
        """Load real Qwen model using existing ModelLoader."""
        from src.model.loader import ModelLoader

        logger.info("Loading Qwen judge model '%s'...", model_name)
        loader = ModelLoader(model_name)
        tokenizer, model = loader.load()
        evaluator = JudgeEvaluator(
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
            max_retries=max_retries
        )
        self._judge_instance = evaluator
        logger.info("Qwen judge model loaded successfully.")
        return evaluator


judge_manager = JudgeManager()
