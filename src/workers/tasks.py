"""Celery tasks for running and persisting evaluation sessions."""

import asyncio
import logging
from typing import Any

from src.database.connection import SessionLocal
from src.database.models import UserApiKeyRecord
from src.database.repository import SessionRepository
from src.services.auth import decrypt_api_key
from src.services.comparison_service import ComparisonService
from src.workers.celery_app import celery_app

logger = logging.getLogger("llm_judge.tasks")


@celery_app.task(name="tasks.evaluate_session", bind=True)
def evaluate_session_task(
    self,
    session_id: str,
    user_id: str,
    mode: str,
    payload: dict[str, Any],
):
    """Evaluate a queued session and persist the report for its owner."""

    with SessionLocal() as db:
        user_keys = {
            record.provider: decrypt_api_key(record.api_key)
            for record in db.query(UserApiKeyRecord).filter(
                UserApiKeyRecord.user_id == user_id
            ).all()
            if record.api_key
        }

    async def evaluate() -> dict[str, Any]:
        service = ComparisonService()
        if mode == "MANUAL_COMPARE":
            return await service.run_manual_compare(
                problem=payload["problem"],
                answers=payload["answers"],
                position_swap_check=payload.get("position_swap_check"),
            )
        if mode == "GENERATE_AND_COMPARE":
            config_data = payload.get("generation_config")
            generation_config = None
            if config_data:
                from src.providers.base import GenerationConfig

                generation_config = GenerationConfig(**config_data)
            return await service.run_generate_and_compare(
                models=payload["models"],
                prompt=payload["prompt"],
                system_prompt=payload.get("system_prompt"),
                generation_config=generation_config,
                position_swap_check=payload.get("position_swap_check"),
                custom_api_keys=user_keys or None,
            )
        raise ValueError(f"Unsupported evaluation mode: {mode}")

    logger.info("Starting evaluation task %s for session %s", self.request.id, session_id)
    report = asyncio.run(evaluate())
    report["session_id"] = session_id

    with SessionLocal() as db:
        SessionRepository(db).save_session(
            session_id=session_id,
            session_data=report,
            save_options={
                "prompt": True,
                "answers": True,
                "evaluations": True,
                "metrics": True,
                "raw_responses": False,
            },
            user_id=user_id,
        )

    return report
