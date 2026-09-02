import json
import time
from pathlib import Path


class TechnicalBenchmark:

    def __init__(self, judge, dataset_path):
        self.judge = judge
        self.dataset_path = Path(dataset_path)

    def load_dataset(self):

        with open(
            self.dataset_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def evaluate_pair(
        self,
        item,
        answer_a,
        answer_b,
        expected
    ):

        start_time = time.perf_counter()

        evaluation = self.judge.evaluate(
            problem=item["problem"],
            answer_a=answer_a,
            answer_b=answer_b
        )

        latency = (
            time.perf_counter()
            - start_time
        )

        winner = evaluation["result"]["winner"]

        return {
            "winner": winner,
            "expected": expected,
            "correct": winner == expected,
            "latency_seconds": round(
                latency,
                3
            ),
            "attempts": evaluation.get(
                "attempts",
                1
            ),
            "result": evaluation["result"]
        }

    def run(self):

        dataset = self.load_dataset()

        results = []

        for index, item in enumerate(
            dataset,
            start=1
        ):

            print(
                f"[{index}/{len(dataset)}] "
                f"{item['id']} | "
                f"{item['category']} | "
                f"{item['difficulty']}"
            )

            try:

                original = self.evaluate_pair(
                    item=item,
                    answer_a=item["good_answer"],
                    answer_b=item["bad_answer"],
                    expected="A"
                )

                reversed_order = self.evaluate_pair(
                    item=item,
                    answer_a=item["bad_answer"],
                    answer_b=item["good_answer"],
                    expected="B"
                )

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "original": original,
                    "reversed": reversed_order
                })

            except Exception as error:

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "error": str(error)
                })

        return results

    @staticmethod
    def calculate_metrics(results):

        successful_pairs = [
            result
            for result in results
            if "error" not in result
        ]

        total_pairs = len(results)
        failed_pairs = (
            total_pairs
            - len(successful_pairs)
        )

        if not successful_pairs:

            return {
                "total_pairs": total_pairs,
                "successful_pairs": 0,
                "failed_pairs": failed_pairs
            }

        original_correct = sum(
            result["original"]["correct"]
            for result in successful_pairs
        )

        reversed_correct = sum(
            result["reversed"]["correct"]
            for result in successful_pairs
        )

        consistent = sum(
            (
                result["original"]["correct"]
                and result["reversed"]["correct"]
            )
            for result in successful_pairs
        )

        first_position_bias = sum(
            (
                result["original"]["winner"] == "A"
                and result["reversed"]["winner"] == "A"
            )
            for result in successful_pairs
        )

        second_position_bias = sum(
            (
                result["original"]["winner"] == "B"
                and result["reversed"]["winner"] == "B"
            )
            for result in successful_pairs
        )

        total_evaluations = (
            len(successful_pairs) * 2
        )

        total_attempts = sum(
            result["original"]["attempts"]
            + result["reversed"]["attempts"]
            for result in successful_pairs
        )

        total_latency = sum(
            result["original"]["latency_seconds"]
            + result["reversed"]["latency_seconds"]
            for result in successful_pairs
        )

        return {
            "total_pairs": total_pairs,

            "successful_pairs": len(
                successful_pairs
            ),

            "failed_pairs": failed_pairs,

            "total_evaluations": (
                total_evaluations
            ),

            "original_accuracy": round(
                original_correct
                / len(successful_pairs),
                4
            ),

            "reversed_accuracy": round(
                reversed_correct
                / len(successful_pairs),
                4
            ),

            "position_consistency": round(
                consistent
                / len(successful_pairs),
                4
            ),

            "first_position_bias": (
                first_position_bias
            ),

            "second_position_bias": (
                second_position_bias
            ),

            "position_bias_rate": round(
                (
                    first_position_bias
                    + second_position_bias
                )
                / len(successful_pairs),
                4
            ),

            "average_latency_seconds": round(
                total_latency
                / total_evaluations,
                3
            ),

            "average_attempts": round(
                total_attempts
                / total_evaluations,
                2
            )
        }