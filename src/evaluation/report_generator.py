"""Report generator assembling full evaluation sessions into structured reports."""

from typing import Dict, Any, List, Optional
import time


class ReportGenerator:
    """Compiles prompt, answers, pairwise results, rankings, and metrics into a standardized report."""

    @staticmethod
    def generate_report(
        session_id: str,
        mode: str,
        prompt: str,
        system_prompt: Optional[str],
        answers: List[Dict[str, Any]],
        pairwise_comparisons: List[Dict[str, Any]],
        rankings: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        status: str = "COMPLETED"
    ) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "mode": mode,
            "status": status,
            "timestamp": time.time(),
            "input": {
                "prompt": prompt,
                "system_prompt": system_prompt
            },
            "answers": answers,
            "pairwise_comparisons": pairwise_comparisons,
            "rankings": rankings,
            "metrics": metrics
        }
