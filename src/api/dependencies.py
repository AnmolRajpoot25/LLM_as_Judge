from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.config.database import get_db
from src.database.connection import get_db as get_sync_db
from src.database.repository import SessionRepository
from src.services.comparison_service import ComparisonService
from src.models import User
from src.services.auth_jwt import decode_access_token
from src.config.settings import settings

security = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional synchronous database session."""
    yield from get_sync_db()


def get_session_repo(db: Session = None) -> SessionRepository:
    """Instantiate session repository."""
    return SessionRepository(db)


def get_comparison_service() -> ComparisonService:
    """Instantiate ComparisonService with active judge."""
    return ComparisonService()



async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional dependency extracting user from Authorization: Bearer <token>."""
    if not credentials or not credentials.credentials:
        return None
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user and user.is_active:
        return user
    return None


async def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Required dependency requiring valid authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """Required dependency for superuser access."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required.",
        )
    return current_user