class PositionBiasTester:

    def __init__(self, judge):
        self.judge = judge

    def test_pair(
        self,
        problem,
        good_answer,
        bad_answer
    ):

        original = self.judge.evaluate(
            problem=problem,
            answer_a=good_answer,
            answer_b=bad_answer
        )

        reversed_order = self.judge.evaluate(
            problem=problem,
            answer_a=bad_answer,
            answer_b=good_answer
        )

        original_winner = original["result"]["winner"]
        reversed_winner = reversed_order["result"]["winner"]

        original_correct = original_winner == "A"
        reversed_correct = reversed_winner == "B"

        if (
            original_winner == "A"
            and reversed_winner == "B"
        ):
            bias_type = "none"

        elif (
            original_winner == "A"
            and reversed_winner == "A"
        ):
            bias_type = "first_position"

        elif (
            original_winner == "B"
            and reversed_winner == "B"
        ):
            bias_type = "second_position"

        elif (
            original_winner == "B"
            and reversed_winner == "A"
        ):
            bias_type = "inconsistent"

        else:
            bias_type = "tie_or_other"

        return {
            "original": {
                "winner": original_winner,
                "expected": "A",
                "correct": original_correct
            },
            "reversed": {
                "winner": reversed_winner,
                "expected": "B",
                "correct": reversed_correct
            },
            "position_consistent": (
                original_correct
                and reversed_correct
            ),
            "position_bias_detected": (
                bias_type in [
                    "first_position",
                    "second_position"
                ]
            ),
            "bias_type": bias_type
        }

    def run(self, dataset):

        results = []

        for item in dataset:

            print(
                f"Testing {item['id']}"
            )

            try:

                result = self.test_pair(
                    problem=item["problem"],
                    good_answer=item["good_answer"],
                    bad_answer=item["bad_answer"]
                )

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    **result
                })

            except Exception as error:

                results.append({
                    "id": item["id"],
                    "category": item["category"],
                    "error": str(error)
                })

        return results

    @staticmethod
    def calculate_metrics(results):

        successful = [
            result
            for result in results
            if "error" not in result
        ]

        total_pairs = len(results)
        successful_pairs = len(successful)
        failed_pairs = (
            total_pairs - successful_pairs
        )

        if successful_pairs == 0:

            return {
                "total_pairs": total_pairs,
                "successful_pairs": 0,
                "failed_pairs": failed_pairs,
                "original_accuracy": 0,
                "reversed_accuracy": 0,
                "position_consistency": 0,
                "position_bias_rate": 0,
                "first_position_bias": 0,
                "second_position_bias": 0,
                "inconsistent_judgments": 0,
                "tie_or_other": 0
            }

        original_correct = sum(
            result["original"]["correct"]
            for result in successful
        )

        reversed_correct = sum(
            result["reversed"]["correct"]
            for result in successful
        )

        consistent = sum(
            result["position_consistent"]
            for result in successful
        )

        biased = sum(
            result["position_bias_detected"]
            for result in successful
        )

        first_position = sum(
            result["bias_type"] == "first_position"
            for result in successful
        )

        second_position = sum(
            result["bias_type"] == "second_position"
            for result in successful
        )

        inconsistent = sum(
            result["bias_type"] == "inconsistent"
            for result in successful
        )

        ties = sum(
            result["bias_type"] == "tie_or_other"
            for result in successful
        )

        return {
            "total_pairs": total_pairs,
            "successful_pairs": successful_pairs,
            "failed_pairs": failed_pairs,

            "original_accuracy": round(
                original_correct / successful_pairs,
                4
            ),

            "reversed_accuracy": round(
                reversed_correct / successful_pairs,
                4
            ),

            "position_consistency": round(
                consistent / successful_pairs,
                4
            ),

            "position_bias_rate": round(
                biased / successful_pairs,
                4
            ),

            "first_position_bias": first_position,
            "second_position_bias": second_position,
            "inconsistent_judgments": inconsistent,
            "tie_or_other": ties
        }