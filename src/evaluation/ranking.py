"""Ranking engine for aggregating pairwise evaluation results and computing model standings."""

from typing import List, Dict, Any, Optional
from collections import defaultdict


class RankingEngine:
    """
    Computes model rankings and metrics aggregated from pairwise evaluation results.

    Ranking Strategy:
    Uses Standard Competition Ranking ('1224' ranking):
    Tied models receive the identical rank number. The subsequent model's rank
    is offset by the number of tied predecessors (e.g. 1, 2, 2, 4).
    Ties are determined when models share equal values across all 5 priority keys:
    1. win_rate (descending)
    2. wins (descending)
    3. average_final_score (descending)
    4. average_correctness (descending)
    5. successful_evaluations (descending)
    """

    CRITERIA_KEYS = ["correctness", "relevance", "completeness", "reasoning", "clarity"]

    @classmethod
    def rank_models(
        cls,
        comparisons: List[Dict[str, Any]],
        all_model_ids: Optional[List[str]] = None,
        model_name_map: Optional[Dict[str, str]] = None,
        strategy: str = "competition"  # 'competition' or 'dense'
    ) -> List[Dict[str, Any]]:
        name_map = model_name_map or {}

        # Initialize stats tracking per model
        stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "model_id": "",
            "model_name": "",
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "total_comparisons": 0,
            "successful_evaluations": 0,
            "failed_evaluations": 0,
            "final_scores": [],
            "criteria_scores": {k: [] for k in cls.CRITERIA_KEYS}
        })

        # Ensure all models are present even if all comparisons failed
        if all_model_ids:
            for mid in all_model_ids:
                s = stats[mid]
                s["model_id"] = mid
                s["model_name"] = name_map.get(mid, mid)

        # Process each comparison
        for comp in comparisons:
            m_a = comp["model_a"]["model_id"]
            m_b = comp["model_b"]["model_id"]

            stats[m_a]["model_id"] = m_a
            stats[m_a]["model_name"] = comp["model_a"]["name"]
            stats[m_b]["model_id"] = m_b
            stats[m_b]["model_name"] = comp["model_b"]["name"]

            stats[m_a]["total_comparisons"] += 1
            stats[m_b]["total_comparisons"] += 1

            if not comp["success"] or not comp.get("judge_result"):
                stats[m_a]["failed_evaluations"] += 1
                stats[m_b]["failed_evaluations"] += 1
                continue

            stats[m_a]["successful_evaluations"] += 1
            stats[m_b]["successful_evaluations"] += 1

            judge_res = comp["judge_result"]
            winner_id = comp.get("winner_model_id")
            scores = judge_res.get("scores", {})

            # Record scores for Candidate A
            if "A" in scores:
                s_a = scores["A"]
                if "final_score" in s_a:
                    stats[m_a]["final_scores"].append(float(s_a["final_score"]))
                for crit in cls.CRITERIA_KEYS:
                    if crit in s_a:
                        stats[m_a]["criteria_scores"][crit].append(float(s_a[crit]))

            # Record scores for Candidate B
            if "B" in scores:
                s_b = scores["B"]
                if "final_score" in s_b:
                    stats[m_b]["final_scores"].append(float(s_b["final_score"]))
                for crit in cls.CRITERIA_KEYS:
                    if crit in s_b:
                        stats[m_b]["criteria_scores"][crit].append(float(s_b[crit]))

            # Record Win / Loss / Tie
            if winner_id == "TIE":
                stats[m_a]["ties"] += 1
                stats[m_b]["ties"] += 1
            elif winner_id == m_a:
                stats[m_a]["wins"] += 1
                stats[m_b]["losses"] += 1
            elif winner_id == m_b:
                stats[m_b]["wins"] += 1
                stats[m_a]["losses"] += 1

        # Aggregate averages and win rates
        aggregated_models = []
        for mid, data in stats.items():
            valid_comps = data["successful_evaluations"]
            win_rate = round(data["wins"] / valid_comps, 4) if valid_comps > 0 else 0.0

            avg_final = (
                round(sum(data["final_scores"]) / len(data["final_scores"]), 2)
                if data["final_scores"] else 0.0
            )

            criteria_avgs = {}
            for crit in cls.CRITERIA_KEYS:
                vals = data["criteria_scores"][crit]
                criteria_avgs[f"average_{crit}"] = (
                    round(sum(vals) / len(vals), 2) if vals else 0.0
                )

            entry = {
                "model_id": mid,
                "model_name": data["model_name"] or mid,
                "wins": data["wins"],
                "losses": data["losses"],
                "ties": data["ties"],
                "total_comparisons": data["total_comparisons"],
                "successful_evaluations": valid_comps,
                "failed_evaluations": data["failed_evaluations"],
                "win_rate": win_rate,
                "average_final_score": avg_final,
                **criteria_avgs
            }
            aggregated_models.append(entry)

        # Sort according to required priority:
        # 1. Win rate (descending)
        # 2. Number of wins (descending)
        # 3. Average final score (descending)
        # 4. Average correctness (descending)
        # 5. Successful evaluations (descending)
        def sort_key(item: Dict[str, Any]):
            return (
                item["win_rate"],
                item["wins"],
                item["average_final_score"],
                item["average_correctness"],
                item["successful_evaluations"]
            )

        aggregated_models.sort(key=sort_key, reverse=True)

        # Assign ranks handling ties
        ranked_list = []
        current_rank = 1
        for idx, model in enumerate(aggregated_models):
            if idx == 0:
                model["rank"] = 1
            else:
                prev = aggregated_models[idx - 1]
                # Compare sort keys for equality
                if sort_key(model) == sort_key(prev):
                    model["rank"] = prev["rank"]
                else:
                    if strategy == "dense":
                        current_rank += 1
                        model["rank"] = current_rank
                    else:  # Standard competition ranking ('1224')
                        model["rank"] = idx + 1
            ranked_list.append(model)

        return ranked_list
