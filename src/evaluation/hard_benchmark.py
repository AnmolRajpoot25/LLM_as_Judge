import json
import time
from pathlib import Path


class HardTechnicalBenchmark:

    def __init__(self, judge, dataset_path):
        self.judge = judge
        self.dataset_path = Path(dataset_path)

    def load_dataset(self):
        with open(self.dataset_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def evaluate(self, problem, answer_a, answer_b, expected):
        start_time = time.perf_counter()

        evaluation = self.judge.evaluate(
            problem=problem,
            answer_a=answer_a,
            answer_b=answer_b
        )

        latency = time.perf_counter() - start_time

        winner = evaluation["result"]["winner"]

        return {
            "winner": winner,
            "expected": expected,
            "correct": winner == expected,
            "latency_seconds": round(latency, 3),
            "attempts": evaluation.get("attempts", 1),
            "confidence": evaluation["result"].get("confidence", 0),
            "result": evaluation["result"]
        }

    def run(self):
        dataset = self.load_dataset()

        results = []

        for index, item in enumerate(dataset, start=1):

            print(
                f"[{index}/{len(dataset)}] "
                f"{item['id']} | "
                f"{item['category']} | "
                f"{item['failure_type']}"
            )

            try:

                original = self.evaluate(
                    problem=item["problem"],
                    answer_a=item["good_answer"],
                    answer_b=item["bad_answer"],
                    expected="A"
                )

                reversed_order = self.evaluate(
                    problem=item["problem"],
                    answer_a=item["bad_answer"],
                    answer_b=item["good_answer"],
                    expected="B"
                )

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "failure_type": item["failure_type"],
                    "original": original,
                    "reversed": reversed_order
                })

            except Exception as error:

                print(f"ERROR: {error}")

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "failure_type": item["failure_type"],
                    "error": str(error)
                })

        return results

    @staticmethod
    def calculate_metrics(results):

        total_pairs = len(results)

        successful_pairs = [
            result
            for result in results
            if "error" not in result
        ]

        failed_pairs = total_pairs - len(successful_pairs)

        if not successful_pairs:

            return {
                "total_pairs": total_pairs,
                "successful_pairs": 0,
                "failed_pairs": failed_pairs
            }

        total_evaluations = len(successful_pairs) * 2

        original_correct = sum(
            result["original"]["correct"]
            for result in successful_pairs
        )

        reversed_correct = sum(
            result["reversed"]["correct"]
            for result in successful_pairs
        )

        position_consistent = sum(
            result["original"]["correct"]
            and result["reversed"]["correct"]
            for result in successful_pairs
        )

        first_position_bias = sum(
            result["original"]["winner"] == "A"
            and result["reversed"]["winner"] == "A"
            for result in successful_pairs
        )

        second_position_bias = sum(
            result["original"]["winner"] == "B"
            and result["reversed"]["winner"] == "B"
            for result in successful_pairs
        )

        latencies = []

        attempts = []

        confidences = []

        for result in successful_pairs:

            latencies.append(
                result["original"]["latency_seconds"]
            )

            latencies.append(
                result["reversed"]["latency_seconds"]
            )

            attempts.append(
                result["original"]["attempts"]
            )

            attempts.append(
                result["reversed"]["attempts"]
            )

            confidences.append(
                result["original"]["confidence"]
            )

            confidences.append(
                result["reversed"]["confidence"]
            )

        retry_evaluations = sum(
            attempt > 1
            for attempt in attempts
        )

        return {
            "total_pairs": total_pairs,
            "successful_pairs": len(successful_pairs),
            "failed_pairs": failed_pairs,

            "total_evaluations": total_evaluations,

            "original_accuracy": round(
                original_correct / len(successful_pairs),
                4
            ),

            "reversed_accuracy": round(
                reversed_correct / len(successful_pairs),
                4
            ),

            "position_consistency": round(
                position_consistent / len(successful_pairs),
                4
            ),

            "first_position_bias": first_position_bias,

            "second_position_bias": second_position_bias,

            "position_bias_rate": round(
                (
                    first_position_bias
                    + second_position_bias
                ) / len(successful_pairs),
                4
            ),

            "retry_rate": round(
                retry_evaluations / total_evaluations,
                4
            ),

            "average_latency_seconds": round(
                sum(latencies) / len(latencies),
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
                sum(attempts) / len(attempts),
                2
            ),

            "average_confidence": round(
                sum(confidences) / len(confidences),
                4
            )
        }

    @staticmethod
    def category_metrics(results):

        successful = [
            result
            for result in results
            if "error" not in result
        ]

        categories = {}

        for result in successful:

            category = result["category"]

            if category not in categories:

                categories[category] = {
                    "pairs": 0,
                    "original_correct": 0,
                    "reversed_correct": 0,
                    "consistent": 0
                }

            categories[category]["pairs"] += 1

            if result["original"]["correct"]:
                categories[category]["original_correct"] += 1

            if result["reversed"]["correct"]:
                categories[category]["reversed_correct"] += 1

            if (
                result["original"]["correct"]
                and result["reversed"]["correct"]
            ):
                categories[category]["consistent"] += 1

        output = {}

        for category, stats in categories.items():

            pairs = stats["pairs"]

            output[category] = {
                "pairs": pairs,

                "original_accuracy": round(
                    stats["original_correct"] / pairs,
                    4
                ),

                "reversed_accuracy": round(
                    stats["reversed_correct"] / pairs,
                    4
                ),

                "position_consistency": round(
                    stats["consistent"] / pairs,
                    4
                )
            }

        return output

    @staticmethod
    def failure_type_metrics(results):

        successful = [
            result
            for result in results
            if "error" not in result
        ]

        failure_types = {}

        for result in successful:

            failure_type = result["failure_type"]

            if failure_type not in failure_types:

                failure_types[failure_type] = {
                    "pairs": 0,
                    "consistent": 0
                }

            failure_types[failure_type]["pairs"] += 1

            if (
                result["original"]["correct"]
                and result["reversed"]["correct"]
            ):
                failure_types[failure_type]["consistent"] += 1

        output = {}

        for failure_type, stats in failure_types.items():

            pairs = stats["pairs"]

            output[failure_type] = {
                "pairs": pairs,
                "accuracy": round(
                    stats["consistent"] / pairs,
                    4
                )
            }

        return output