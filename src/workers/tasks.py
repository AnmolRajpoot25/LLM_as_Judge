"""Celery background tasks for async LLM generation and evaluation."""

import logging
from src.workers.celery_app import celery_app

logger = logging.getLogger("llm_judge.tasks")


@celery_app.task(name="tasks.evaluate_session", bind=True)
def evaluate_session_task(self, session_id: str):
    """Background task to run model generation and pairwise evaluation for a session."""
    logger.info(f"Starting background evaluation task for session: {session_id}")
    try:
        # Task placeholder for async evaluation execution
        return {
            "session_id": session_id,
            "status": "COMPLETED",
            "task_id": self.request.id,
        }
    except Exception as exc:
        logger.error(f"Error evaluating session {session_id}: {exc}")
        raise
