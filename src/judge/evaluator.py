import json
import re

import torch

from src.judge.prompts import JUDGE_SYSTEM_PROMPT


class JudgeEvaluator:

    CRITERIA = {
        "correctness": 0.40,
        "relevance": 0.20,
        "completeness": 0.15,
        "reasoning": 0.15,
        "clarity": 0.10
    }

    def __init__(
        self,
        model,
        tokenizer,
        max_new_tokens=300,
        max_retries=1
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens
        self.max_retries = max_retries

    def _build_messages(
        self,
        problem,
        answer_a,
        answer_b
    ):
        return [
            {
                "role": "system",
                "content": JUDGE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
PROBLEM:

{problem}

ANSWER A:

{answer_a}

ANSWER B:

{answer_b}

Evaluate both answers independently.

Return ONLY the required JSON.
"""
            }
        ]

    def _generate(self, messages):

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt"
        )

        inputs = {
            key: value.to(self.model.device)
            for key, value in inputs.items()
        }

        with torch.inference_mode():

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False
            )

        input_length = inputs["input_ids"].shape[1]

        generated_tokens = outputs[0][input_length:]

        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        )

        return response.strip()

    def _extract_json(self, response):

        response = response.strip()

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            pass

        cleaned = re.sub(
            r"```(?:json)?",
            "",
            response,
            flags=re.IGNORECASE
        )

        cleaned = cleaned.replace(
            "```",
            ""
        ).strip()

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:
            pass

        match = re.search(
            r"\{.*\}",
            cleaned,
            re.DOTALL
        )

        if not match:
            raise ValueError(
                "Judge did not return valid JSON."
            )

        try:
            return json.loads(match.group())

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Failed to parse judge JSON: {error}"
            ) from error

    def _validate_scores(self, scores):

        required_criteria = set(
            self.CRITERIA.keys()
        )

        for candidate in ["A", "B"]:

            if candidate not in scores:
                raise ValueError(
                    f"Missing candidate: {candidate}"
                )

            candidate_scores = scores[candidate]

            if not isinstance(
                candidate_scores,
                dict
            ):
                raise ValueError(
                    f"{candidate} must contain an object."
                )

            missing = (
                required_criteria
                - set(candidate_scores.keys())
            )

            if missing:
                raise ValueError(
                    f"Missing scores for {candidate}: {missing}"
                )

            for criterion in required_criteria:

                value = candidate_scores[criterion]

                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                ):
                    raise ValueError(
                        f"{candidate}.{criterion} "
                        "must be an integer."
                    )

                if not 0 <= value <= 10:
                    raise ValueError(
                        f"{candidate}.{criterion} "
                        "must be between 0 and 10."
                    )

            if "feedback" not in candidate_scores:
                raise ValueError(
                    f"Missing feedback for {candidate}"
                )

            if not isinstance(
                candidate_scores["feedback"],
                str
            ):
                raise ValueError(
                    f"{candidate}.feedback must be a string."
                )

    def _calculate_final_score(
        self,
        scores
    ):

        final_score = 0.0

        for criterion, weight in self.CRITERIA.items():

            final_score += (
                scores[criterion] * weight
            )

        return round(
            final_score,
            2
        )

    def _determine_winner(
        self,
        scores
    ):

        score_a = scores["A"]["final_score"]
        score_b = scores["B"]["final_score"]

        if score_a > score_b:
            return "A"

        if score_b > score_a:
            return "B"

        return "TIE"

    def _calculate_confidence(
        self,
        score_a,
        score_b
    ):

        difference = abs(
            score_a - score_b
        )

        if difference >= 2.0:
            return 0.90

        if difference >= 1.0:
            return 0.75

        if difference >= 0.5:
            return 0.60

        return 0.50

    def _build_result(
        self,
        scores
    ):

        scores["A"]["final_score"] = (
            self._calculate_final_score(
                scores["A"]
            )
        )

        scores["B"]["final_score"] = (
            self._calculate_final_score(
                scores["B"]
            )
        )

        winner = self._determine_winner(
            scores
        )

        confidence = self._calculate_confidence(
            scores["A"]["final_score"],
            scores["B"]["final_score"]
        )

        if winner == "TIE":

            reason = (
                "Both answers received equal "
                "weighted scores."
            )

        else:

            reason = scores[winner]["feedback"]

        return {
            "winner": winner,

            "scores": {
                "A": scores["A"],
                "B": scores["B"]
            },

            "confidence": confidence,

            "reason": reason
        }

    def evaluate(
        self,
        problem,
        answer_a,
        answer_b
    ):

        if not problem or not problem.strip():
            raise ValueError(
                "Problem cannot be empty."
            )

        if not answer_a or not answer_a.strip():
            raise ValueError(
                "Answer A cannot be empty."
            )

        if not answer_b or not answer_b.strip():
            raise ValueError(
                "Answer B cannot be empty."
            )

        messages = self._build_messages(
            problem,
            answer_a,
            answer_b
        )

        last_error = None
        raw_response = None

        for attempt in range(
            self.max_retries + 1
        ):

            try:

                raw_response = self._generate(
                    messages
                )

                parsed_response = (
                    self._extract_json(
                        raw_response
                    )
                )

                self._validate_scores(
                    parsed_response
                )

                result = self._build_result(
                    parsed_response
                )

                return {
                    "result": result,
                    "raw_response": raw_response,
                    "attempts": attempt + 1
                }

            except Exception as error:

                last_error = error

                if attempt < self.max_retries:

                    messages = self._build_messages(
                        problem,
                        answer_a,
                        answer_b
                    )

                    messages.append({
                        "role": "user",
                        "content": """
Your previous response was invalid.

Return ONLY valid JSON.

Requirements:

- Use exactly two top-level keys: "A" and "B".
- Do not create any other top-level keys.
- Each candidate must contain:
  correctness
  relevance
  completeness
  reasoning
  clarity
  feedback
- All scores must be integers from 0 to 10.
- Feedback must be a string.
- Use double quotes for all JSON keys.
- Do not use trailing commas.
- Do not use markdown.
- Do not include any text outside the JSON object.
"""
                    })

        raise ValueError(
            f"Judge evaluation failed after "
            f"{self.max_retries + 1} attempts: "
            f"{last_error}"
        )