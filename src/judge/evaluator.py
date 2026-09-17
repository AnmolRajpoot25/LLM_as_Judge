import json
import re

from gradio_client import Client


class JudgeEvaluator:
    """
    Evaluator using the fine-tuned Qwen2.5-7B model
    deployed on Hugging Face ZeroGPU.

    HF Space:
        Anmol2507/LLM_as_Judge_API

    API endpoint:
        /judge

    Expected model response:
        {"A": "correct", "B": "incorrect"}
    """

    HF_SPACE = "Anmol2507/LLM_as_Judge_API"
    API_NAME = "/judge"

    def __init__(
        self,
        model=None,
        tokenizer=None,
        max_new_tokens=32,
        max_retries=1
    ):
        """
        model and tokenizer are kept as optional arguments for
        backward compatibility with the existing project.

        The actual evaluation is performed remotely through
        the Hugging Face Gradio API.
        """

        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens
        self.max_retries = max_retries

        # Connect to the deployed Hugging Face Space.
        self.client = Client(self.HF_SPACE)

    # ========================================================
    # REMOTE GENERATION
    # ========================================================

    def _generate(
        self,
        problem,
        answer_a,
        answer_b
    ):
        """
        Send the problem and two answers to the
        Hugging Face judge API.
        """

        response = self.client.predict(
            problem=problem,
            answer_a=answer_a,
            answer_b=answer_b,
            api_name=self.API_NAME
        )

        # Gradio normally returns the output as a string.
        if isinstance(response, str):
            return response.strip()

        # Handle unexpected structured responses safely.
        if isinstance(response, dict):
            return json.dumps(response)

        return str(response).strip()

    # ========================================================
    # JSON EXTRACTION
    # ========================================================

    def _extract_json(self, response):
        """
        Extract JSON from the judge response.

        Supports:
        1. Pure JSON
        2. Markdown JSON code blocks
        3. JSON embedded inside additional text
        """

        if not response:
            raise ValueError(
                "Judge returned an empty response."
            )

        response = response.strip()

        # ----------------------------------------------------
        # Case 1: Direct JSON
        # ----------------------------------------------------

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # ----------------------------------------------------
        # Case 2: Markdown code block
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Case 3: JSON embedded in text
        # ----------------------------------------------------

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

    # ========================================================
    # RESPONSE VALIDATION
    # ========================================================

    def _validate_response(
        self,
        response
    ):
        """
        Validate the correctness-only response from
        the fine-tuned judge.
        """

        if not isinstance(response, dict):
            raise ValueError(
                "Judge response must be a JSON object."
            )

        # ----------------------------------------------------
        # Exactly A and B should be present.
        # ----------------------------------------------------

        if set(response.keys()) != {"A", "B"}:
            raise ValueError(
                'Judge response must contain exactly '
                '"A" and "B".'
            )

        # ----------------------------------------------------
        # Validate labels.
        # ----------------------------------------------------

        allowed_labels = {
            "correct",
            "incorrect"
        }

        for candidate in ["A", "B"]:

            value = response[candidate]

            if not isinstance(value, str):
                raise ValueError(
                    f"{candidate} must be a string."
                )

            value = value.strip().lower()

            if value not in allowed_labels:
                raise ValueError(
                    f"{candidate} must be either "
                    '"correct" or "incorrect".'
                )

            response[candidate] = value

        return response

    # ========================================================
    # DETERMINE WINNER
    # ========================================================

    def _determine_winner(
        self,
        response
    ):
        """
        Determine winner from correctness labels.
        """

        a_correct = (
            response["A"] == "correct"
        )

        b_correct = (
            response["B"] == "correct"
        )

        if a_correct and not b_correct:
            return "A"

        if b_correct and not a_correct:
            return "B"

        # Both correct OR both incorrect.
        return "TIE"

    # ========================================================
    # BUILD RESULT
    # ========================================================

    def _build_result(
        self,
        response
    ):
        """
        Convert the native judge response into the
        project's existing result structure.
        """

        winner = self._determine_winner(
            response
        )

        # ----------------------------------------------------
        # Generate a concise reason.
        # ----------------------------------------------------

        if winner == "A":

            reason = (
                "Answer A was judged correct while "
                "Answer B was judged incorrect."
            )

        elif winner == "B":

            reason = (
                "Answer B was judged correct while "
                "Answer A was judged incorrect."
            )

        elif (
            response["A"] == "correct"
            and response["B"] == "correct"
        ):

            reason = (
                "Both answers were judged correct."
            )

        else:

            reason = (
                "Both answers were judged incorrect."
            )

        # ----------------------------------------------------
        # Compatibility structure.
        #
        # These are correctness indicators, NOT the old
        # 0-10 criterion scores.
        # ----------------------------------------------------

        scores = {
            "A": {
                "correctness": (
                    1 if response["A"] == "correct" else 0
                ),
                "label": response["A"]
            },
            "B": {
                "correctness": (
                    1 if response["B"] == "correct" else 0
                ),
                "label": response["B"]
            }
        }

        # ----------------------------------------------------
        # Confidence is only a simple certainty indicator
        # based on whether the judge separated the answers.
        # ----------------------------------------------------

        if winner == "TIE":
            confidence = 0.50
        else:
            confidence = 1.00

        return {
            "winner": winner,
            "scores": scores,
            "confidence": confidence,
            "reason": reason
        }

    # ========================================================
    # PUBLIC EVALUATE METHOD
    # ========================================================

    def evaluate(
        self,
        problem,
        answer_a,
        answer_b
    ):
        """
        Evaluate two answers using the remote
        fine-tuned Qwen judge.
        """

        # ----------------------------------------------------
        # Input validation
        # ----------------------------------------------------

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

        last_error = None
        raw_response = None

        # ----------------------------------------------------
        # Retry if the remote model returns invalid JSON.
        # ----------------------------------------------------

        for attempt in range(
            self.max_retries + 1
        ):

            try:

                # --------------------------------------------
                # Call Hugging Face ZeroGPU
                # --------------------------------------------

                raw_response = self._generate(
                    problem=problem,
                    answer_a=answer_a,
                    answer_b=answer_b
                )

                # --------------------------------------------
                # Parse JSON
                # --------------------------------------------

                parsed_response = (
                    self._extract_json(
                        raw_response
                    )
                )

                # --------------------------------------------
                # Validate response
                # --------------------------------------------

                parsed_response = (
                    self._validate_response(
                        parsed_response
                    )
                )

                # --------------------------------------------
                # Build project result
                # --------------------------------------------

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

        # ----------------------------------------------------
        # All attempts failed.
        # ----------------------------------------------------

        raise ValueError(
            f"Judge evaluation failed after "
            f"{self.max_retries + 1} attempts: "
            f"{last_error}"
        )