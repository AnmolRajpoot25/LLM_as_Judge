import statistics


class ReliabilityAnalyzer:

    def __init__(self, results):
        self.results = results

    def analyze(self):
        total_pairs = len(self.results)

        successful_pairs = [
            result
            for result in self.results
            if "error" not in result
        ]

        failed_pairs = total_pairs - len(successful_pairs)

        total_evaluations = len(successful_pairs) * 2

        if total_evaluations == 0:
            return {
                "total_pairs": total_pairs,
                "successful_pairs": 0,
                "failed_pairs": failed_pairs,
                "total_evaluations": 0,
                "evaluation_success_rate": 0,
                "retry_rate": 0,
                "score_consistency": 0,
                "winner_consistency": 0,
                "average_confidence": 0,
                "average_latency_seconds": 0,
            }

        attempts = []
        latencies = []
        confidences = []
        score_differences = []
        winner_consistency_values = []

        for result in successful_pairs:

            original = result["original"]
            reversed_order = result["reversed"]

            attempts.append(original.get("attempts", 1))
            attempts.append(reversed_order.get("attempts", 1))

            latencies.append(original["latency_seconds"])
            latencies.append(reversed_order["latency_seconds"])

            confidences.append(
                original["result"].get("confidence", 0)
            )
            confidences.append(
                reversed_order["result"].get("confidence", 0)
            )

            original_scores = original["result"]["scores"]
            reversed_scores = reversed_order["result"]["scores"]

            original_a_score = original_scores["A"]["final_score"]
            original_b_score = original_scores["B"]["final_score"]

            reversed_a_score = reversed_scores["A"]["final_score"]
            reversed_b_score = reversed_scores["B"]["final_score"]

            # Original A corresponds to reversed B.
            # Original B corresponds to reversed A.
            good_answer_difference = abs(
                original_a_score - reversed_b_score
            )

            bad_answer_difference = abs(
                original_b_score - reversed_a_score
            )

            average_difference = (
                good_answer_difference + bad_answer_difference
            ) / 2

            score_differences.append(average_difference)

            original_correct = original["correct"]
            reversed_correct = reversed_order["correct"]

            winner_consistency_values.append(
                int(original_correct and reversed_correct)
            )

        retry_evaluations = sum(
            1 for attempt in attempts
            if attempt > 1
        )

        average_score_difference = statistics.mean(
            score_differences
        )

        score_consistency = max(
            0,
            1 - (average_score_difference / 10)
        )

        winner_consistency = statistics.mean(
            winner_consistency_values
        )

        return {
            "total_pairs": total_pairs,
            "successful_pairs": len(successful_pairs),
            "failed_pairs": failed_pairs,
            "total_evaluations": total_evaluations,
            "evaluation_success_rate": round(
                total_evaluations / (total_pairs * 2),
                4
            ),
            "retry_rate": round(
                retry_evaluations / total_evaluations,
                4
            ),
            "score_consistency": round(
                score_consistency,
                4
            ),
            "average_score_difference": round(
                average_score_difference,
                4
            ),
            "winner_consistency": round(
                winner_consistency,
                4
            ),
            "average_confidence": round(
                statistics.mean(confidences),
                4
            ),
            "average_latency_seconds": round(
                statistics.mean(latencies),
                3
            ),
            "min_latency_seconds": round(
                min(latencies),
                3
            ),
            "max_latency_seconds": round(
                max(latencies),
                3
            ),
            "average_attempts": round(
                statistics.mean(attempts),
                2
            ),
        }