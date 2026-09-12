"""API routes for saving and retrieving comparison sessions."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.repository import SessionRepository
from src.api.schemas.requests import SaveSessionRequest
from src.api.routes.auth import get_current_user_optional

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.post("/{session_id}/save")
async def save_session(
    session_id: str,
    request: SaveSessionRequest,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Save selected portions of an evaluation session."""
    repo = SessionRepository(db)
    save_opts = request.save_options.model_dump()

    try:
        result = repo.save_session(
            session_id=session_id,
            session_data=request.session_data,
            save_options=save_opts,
            user_id=user.id if user else None
        )
        return {"success": True, "data": result}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save session: {str(exc)}"
        )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve full details of a saved comparison session."""
    repo = SessionRepository(db)
    session_data = repo.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    return {"success": True, "data": session_data}


@router.get("")
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """List summary history of saved comparison sessions. If logged in, filters to user's sessions."""
    repo = SessionRepository(db)
    user_id = user.id if user else None
    sessions = repo.list_sessions(limit=limit, offset=offset, user_id=user_id)
    return {"success": True, "data": sessions, "count": len(sessions)}

