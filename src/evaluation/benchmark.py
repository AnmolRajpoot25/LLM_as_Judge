import json
from pathlib import Path


class JudgeBenchmark:

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

    def run(self):

        dataset = self.load_dataset()

        results = []

        for item in dataset:

            print(
                f"Evaluating {item['id']}/{len(dataset)}..."
            )

            try:

                evaluation = self.judge.evaluate(
                    problem=item["problem"],
                    answer_a=item["answer_a"],
                    answer_b=item["answer_b"]
                )

                predicted = evaluation["result"]["winner"]

                expected = item["expected_winner"]

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "expected": expected,
                    "predicted": predicted,
                    "correct": predicted == expected,
                    "result": evaluation["result"]
                })

            except Exception as error:

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "expected": item["expected_winner"],
                    "predicted": None,
                    "correct": False,
                    "error": str(error)
                })

        return results