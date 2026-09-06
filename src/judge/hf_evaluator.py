"""Hugging Face Remote Qwen Judge Evaluator for free tier Spaces and Inference API."""

import json
import re
import logging
from typing import Optional, Dict, Any
import httpx
from src.judge.prompts import JUDGE_SYSTEM_PROMPT
from src.config.settings import settings

logger = logging.getLogger("llm_judge.hf_evaluator")


class HuggingFaceJudgeEvaluator:
    """
    Evaluator that queries a remote fine-tuned Qwen model hosted on Hugging Face
    (either as a free Hugging Face Space running an OpenAI-compatible API, or HF Inference API).
    """

    CRITERIA = {
        "correctness": 0.40,
        "relevance": 0.20,
        "completeness": 0.15,
        "reasoning": 0.15,
        "clarity": 0.10
    }

    def __init__(
        self,
        api_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.api_url = (api_url or settings.qwen_hf_api_url or "").rstrip("/")
        self.token = token or settings.qwen_hf_token
        self.timeout = timeout or settings.judge_timeout_seconds

    def _build_prompt_payload(self, problem: str, answer_a: str, answer_b: str) -> list:
        user_content = f"""PROBLEM:

{problem}

ANSWER A:

{answer_a}

ANSWER B:

{answer_b}

Evaluate both answers independently against correctness, relevance, completeness, reasoning, and clarity.
Return ONLY valid JSON matching this schema:
{{
  "A": {{"correctness": 8, "relevance": 9, "completeness": 8, "reasoning": 8, "clarity": 9, "feedback": "..."}},
  "B": {{"correctness": 7, "relevance": 8, "completeness": 7, "reasoning": 7, "clarity": 8, "feedback": "..."}}
}}"""
        return [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

    def _calculate_final_score(self, score_dict: Dict[str, Any]) -> float:
        total = 0.0
        for criterion, weight in self.CRITERIA.items():
            val = float(score_dict.get(criterion, 7))
            total += val * weight
        return round(total, 2)

    def _determine_winner(self, score_a: float, score_b: float) -> str:
        diff = score_a - score_b
        if abs(diff) < 0.1:
            return "TIE"
        return "A" if diff > 0 else "B"

    def _calculate_confidence(self, score_a: float, score_b: float) -> float:
        diff = abs(score_a - score_b)
        if diff >= 2.0:
            return 0.95
        if diff >= 1.0:
            return 0.85
        if diff >= 0.5:
            return 0.70
        return 0.55

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from Qwen response text."""
        # Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try markdown code fence regex
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try bracket extraction
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse valid JSON from judge model response: {text[:200]}")

    def evaluate(self, problem: str, answer_a: str, answer_b: str) -> dict:
        """Synchronous evaluate method signature for PairwiseEvaluator compatibility."""
        messages = self._build_prompt_payload(problem, answer_a, answer_b)
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        endpoint = self.api_url
        if not endpoint.endswith("/chat/completions") and not endpoint.endswith("/v1"):
            if "hf.space" in endpoint or "localhost" in endpoint or "127.0.0.1" in endpoint:
                endpoint = f"{endpoint}/v1/chat/completions"

        payload = {
            "model": "qwen-judge",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 400
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Hugging Face Qwen judge request failed (HTTP {resp.status_code}): {resp.text[:300]}"
                )
            data = resp.json()

        # Extract text from OpenAI-compatible or HF raw response
        if "choices" in data and len(data["choices"]) > 0:
            raw_text = data["choices"][0].get("message", {}).get("content", "")
        elif isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            raw_text = data[0]["generated_text"]
        elif "response" in data:
            raw_text = data["response"]
        else:
            raw_text = json.dumps(data)

        parsed_scores = self._parse_json_response(raw_text)
        s_a = parsed_scores.get("A", {})
        s_b = parsed_scores.get("B", {})

        score_a_final = self._calculate_final_score(s_a)
        score_b_final = self._calculate_final_score(s_b)

        s_a["final_score"] = score_a_final
        s_b["final_score"] = score_b_final

        winner = self._determine_winner(score_a_final, score_b_final)
        confidence = self._calculate_confidence(score_a_final, score_b_final)
        reason = s_a.get("feedback", "") if winner == "A" else (
            s_b.get("feedback", "") if winner == "B" else "Both answers demonstrated comparable technical depth."
        )

        result = {
            "winner": winner,
            "scores": {
                "A": s_a,
                "B": s_b
            },
            "confidence": confidence,
            "reason": reason
        }

        return {
            "result": result,
            "raw_response": raw_text,
            "attempts": 1
        }
