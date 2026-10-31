"""Authenticated endpoints for queued evaluation jobs."""

import asyncio
import uuid

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user_required
from src.api.schemas.requests import AsyncEvaluationRequest
from src.models import User
from src.workers.celery_app import celery_app
from src.workers.tasks import evaluate_session_task

router = APIRouter(prefix="/api/evaluations", tags=["Background Evaluations"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_evaluation(
    request: AsyncEvaluationRequest,
    current_user: User = Depends(get_current_user_required),
):
    """Queue an evaluation; results are saved in the user's session history."""
    session_id = f"async-{uuid.uuid4().hex}"
    task_id = f"{current_user.id}.{uuid.uuid4().hex}"
    mode = request.mode
    if request.generate and request.generate.custom_api_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Background evaluations use API keys saved to your account; request-supplied keys are not accepted.",
        )
    payload = (
        request.generate.model_dump(exclude_none=True)
        if request.generate
        else request.manual.model_dump(exclude_none=True)
    )
    try:
        await asyncio.to_thread(
            evaluate_session_task.apply_async,
            kwargs={
                "session_id": session_id,
                "user_id": current_user.id,
                "mode": mode,
                "payload": payload,
            },
            task_id=task_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background evaluation queue is unavailable.",
        ) from exc
    return {"task_id": task_id, "session_id": session_id, "status": "PENDING"}


@router.get("/{task_id}")
async def get_evaluation_status(
    task_id: str,
    current_user: User = Depends(get_current_user_required),
):
    """Return task state and the report once the evaluation has completed."""
    if not task_id.startswith(f"{current_user.id}."):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    result = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": result.state}
    if result.successful():
        response["result"] = result.result
    elif result.failed():
        response["error"] = "Evaluation failed. Check worker logs for details."
    return response
