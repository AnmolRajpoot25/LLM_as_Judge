"""Repository for persisting evaluation sessions with user-controlled partial saving."""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from src.database.models import (
    SessionRecord,
    PromptRecord,
    ModelResponseRecord,
    PairwiseComparisonRecord,
    EvaluationResultRecord,
)


class SessionRepository:
    """Handles CRUD and selective persistence for evaluation sessions."""

    def __init__(self, db: Session):
        self.db = db

    def save_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        save_options: Dict[str, bool],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Persist session with user-selected partial saving options.
        Guarantees relational integrity without orphan records.
        """
        opt_prompt = save_options.get("prompt", True)
        opt_answers = save_options.get("answers", True)
        opt_evaluations = save_options.get("evaluations", True)
        opt_metrics = save_options.get("metrics", True)
        opt_raw = save_options.get("raw_responses", False)

        # 1. Upsert SessionRecord
        session_rec = self.db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
        if not session_rec:
            session_rec = SessionRecord(
                id=session_id,
                mode=session_data.get("mode", "GENERATE_AND_COMPARE"),
                status=session_data.get("status", "COMPLETED"),
                user_id=user_id
            )
            self.db.add(session_rec)
        elif user_id and not session_rec.user_id:
            session_rec.user_id = user_id

        session_rec.saved_options = save_options
        session_rec.rankings_summary = session_data.get("rankings", [])
        if opt_metrics:
            session_rec.metrics_summary = session_data.get("metrics", {})
        else:
            session_rec.metrics_summary = None

        # 2. Save Prompt if requested
        if opt_prompt and "input" in session_data:
            inp = session_data["input"]
            prompt_rec = self.db.query(PromptRecord).filter(PromptRecord.session_id == session_id).first()
            if not prompt_rec:
                prompt_rec = PromptRecord(
                    id=f"prm-{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    content=inp.get("prompt", ""),
                    system_prompt=inp.get("system_prompt")
                )
                self.db.add(prompt_rec)
            else:
                prompt_rec.content = inp.get("prompt", "")
                prompt_rec.system_prompt = inp.get("system_prompt")

        # 3. Save Answers if requested
        if opt_answers and "answers" in session_data:
            # Clear previous to prevent duplicates on update
            self.db.query(ModelResponseRecord).filter(ModelResponseRecord.session_id == session_id).delete()
            for ans in session_data["answers"]:
                resp_rec = ModelResponseRecord(
                    id=f"rsp-{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    provider=ans.get("provider", "unknown"),
                    model_id=ans.get("model", ans.get("model_id", "unknown")),
                    model_name=ans.get("model_name", ans.get("model", "Model")),
                    answer=ans.get("answer"),
                    generation_latency=ans.get("latency_seconds") if opt_metrics else None,
                    input_tokens=ans.get("input_tokens") if opt_metrics else None,
                    output_tokens=ans.get("output_tokens") if opt_metrics else None,
                    estimated_cost=ans.get("estimated_cost") if opt_metrics else None,
                    status="SUCCESS" if ans.get("success", True) else "FAILED",
                    error_message=str(ans.get("error")) if ans.get("error") else None
                )
                self.db.add(resp_rec)

        # 4. Save Comparisons and Evaluations if requested
        if opt_evaluations and "pairwise_comparisons" in session_data:
            self.db.query(PairwiseComparisonRecord).filter(PairwiseComparisonRecord.session_id == session_id).delete()
            for comp in session_data["pairwise_comparisons"]:
                comp_id = comp.get("comparison_id") or f"cmp-{uuid.uuid4().hex[:8]}"
                m_a = comp.get("model_a", {})
                m_b = comp.get("model_b", {})

                comp_rec = PairwiseComparisonRecord(
                    id=comp_id,
                    session_id=session_id,
                    model_a_id=m_a.get("model_id", "A"),
                    model_a_name=m_a.get("name", "Model A"),
                    model_b_id=m_b.get("model_id", "B"),
                    model_b_name=m_b.get("name", "Model B"),
                    winner=comp.get("winner_model_id"),
                    status="SUCCESS" if comp.get("success", True) else "FAILED",
                    judge_latency=comp.get("judge_latency") if opt_metrics else None
                )
                self.db.add(comp_rec)

                # Attach EvaluationResult
                judge_res = comp.get("judge_result")
                if judge_res:
                    scores = judge_res.get("scores", {})
                    s_a = scores.get("A", {})
                    s_b = scores.get("B", {})

                    eval_rec = EvaluationResultRecord(
                        id=f"evl-{uuid.uuid4().hex[:8]}",
                        comparison_id=comp_id,
                        score_a_correctness=s_a.get("correctness"),
                        score_a_relevance=s_a.get("relevance"),
                        score_a_completeness=s_a.get("completeness"),
                        score_a_reasoning=s_a.get("reasoning"),
                        score_a_clarity=s_a.get("clarity"),
                        score_a_final=s_a.get("final_score"),
                        score_b_correctness=s_b.get("correctness"),
                        score_b_relevance=s_b.get("relevance"),
                        score_b_completeness=s_b.get("completeness"),
                        score_b_reasoning=s_b.get("reasoning"),
                        score_b_clarity=s_b.get("clarity"),
                        score_b_final=s_b.get("final_score"),
                        confidence=judge_res.get("confidence"),
                        reason=judge_res.get("reason"),
                        raw_judge_response=comp.get("raw_judge_response") if opt_raw else None,
                        position_swap_result=comp.get("position_swap_check")
                    )
                    self.db.add(eval_rec)

        self.db.commit()
        return {
            "session_id": session_id,
            "saved": True,
            "saved_options": save_options
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a saved session."""
        session_rec = self.db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
        if not session_rec:
            return None

        prompt_data = None
        if session_rec.prompt:
            prompt_data = {
                "prompt": session_rec.prompt.content,
                "system_prompt": session_rec.prompt.system_prompt
            }

        answers_data = [
            {
                "model_id": r.model_id,
                "model_name": r.model_name,
                "provider": r.provider,
                "answer": r.answer,
                "latency_seconds": r.generation_latency,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "estimated_cost": r.estimated_cost,
                "success": r.status == "SUCCESS",
                "error": r.error_message
            }
            for r in session_rec.responses
        ]

        comparisons_data = []
        for c in session_rec.comparisons:
            entry = {
                "comparison_id": c.id,
                "model_a": {"model_id": c.model_a_id, "name": c.model_a_name},
                "model_b": {"model_id": c.model_b_id, "name": c.model_b_name},
                "winner_model_id": c.winner,
                "status": c.status,
                "judge_latency": c.judge_latency,
                "judge_result": None,
                "position_swap_check": None
            }
            if c.evaluation:
                ev = c.evaluation
                entry["judge_result"] = {
                    "winner": "A" if c.winner == c.model_a_id else ("B" if c.winner == c.model_b_id else "TIE"),
                    "scores": {
                        "A": {
                            "correctness": ev.score_a_correctness,
                            "relevance": ev.score_a_relevance,
                            "completeness": ev.score_a_completeness,
                            "reasoning": ev.score_a_reasoning,
                            "clarity": ev.score_a_clarity,
                            "final_score": ev.score_a_final
                        },
                        "B": {
                            "correctness": ev.score_b_correctness,
                            "relevance": ev.score_b_relevance,
                            "completeness": ev.score_b_completeness,
                            "reasoning": ev.score_b_reasoning,
                            "clarity": ev.score_b_clarity,
                            "final_score": ev.score_b_final
                        }
                    },
                    "confidence": ev.confidence,
                    "reason": ev.reason
                }
                entry["raw_judge_response"] = ev.raw_judge_response
                entry["position_swap_check"] = ev.position_swap_result

            comparisons_data.append(entry)

        return {
            "session_id": session_rec.id,
            "mode": session_rec.mode,
            "status": session_rec.status,
            "created_at": session_rec.created_at.isoformat() if session_rec.created_at else None,
            "saved_options": session_rec.saved_options,
            "input": prompt_data,
            "answers": answers_data,
            "pairwise_comparisons": comparisons_data,
            "rankings": session_rec.rankings_summary or [],
            "metrics": session_rec.metrics_summary or {}
        }

    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List summary info for saved sessions. If user_id provided, filter by user."""
        query = self.db.query(SessionRecord)
        if user_id:
            query = query.filter(SessionRecord.user_id == user_id)

        records = (
            query
            .order_by(SessionRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        summaries = []
        for r in records:
            prompt_preview = r.prompt.content[:120] if r.prompt else "No prompt saved"
            models_list = [resp.model_name for resp in r.responses] if r.responses else []
            summaries.append({
                "session_id": r.id,
                "mode": r.mode,
                "status": r.status,
                "prompt_preview": prompt_preview,
                "models": models_list,
                "rankings_count": len(r.rankings_summary) if r.rankings_summary else 0,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "saved_options": r.saved_options
            })

        return summaries
