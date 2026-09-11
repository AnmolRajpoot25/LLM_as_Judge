"""FastAPI dependencies for dependency injection."""

from typing import Generator
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.repository import SessionRepository
from src.services.comparison_service import ComparisonService
from src.judge.model_loader import judge_manager


def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    yield from get_db()


def get_session_repo(db: Session = None) -> SessionRepository:
    """Instantiate session repository."""
    return SessionRepository(db)


def get_comparison_service() -> ComparisonService:
    """Instantiate ComparisonService with active judge."""
    active_judge = judge_manager.get_judge()
    return ComparisonService(judge=active_judge)
