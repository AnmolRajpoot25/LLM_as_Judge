"""Authentication API routes for user registration, login, and session validation."""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from src.config.database import get_db
from src.models import User
from src.services.auth_jwt import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.api.dependencies import get_current_user_required, get_current_user_optional

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str | None = None


class AuthResponse(BaseModel):
    success: bool
    user: UserResponse
    token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    success: bool = True
    user: UserResponse


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    clean_user = request.username.strip().lower()
    clean_email = request.email.strip().lower()

    if len(clean_user) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long."
        )
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )
    if "@" not in clean_email or "." not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid email address is required."
        )

    # Check existing
    existing_user = await db.execute(
        select(User).where(
            (User.username == clean_user) | (User.email == clean_email)
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered."
        )

    user_id = f"usr-{uuid.uuid4().hex}"
    pwd_hash = get_password_hash(request.password)

    new_user = User(
        id=user_id,
        username=clean_user,
        email=clean_email,
        password_hash=pwd_hash,
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered.",
        ) from exc
    await db.refresh(new_user)

    expires_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": new_user.id, "username": new_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return AuthResponse(
        success=True,
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            created_at=new_user.created_at.isoformat() if new_user.created_at else None,
        ),
        token=access_token,
        token_type="bearer",
        expires_in=expires_seconds,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in and retrieve auth bearer token."""
    query_val = request.username_or_email.strip()

    result = await db.execute(
        select(User).where(
            (func.lower(User.username) == query_val.lower())
            | (func.lower(User.email) == query_val.lower())
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    user.last_login = datetime.utcnow()
    await db.commit()

    expires_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return AuthResponse(
        success=True,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at.isoformat() if user.created_at else None,
        ),
        token=access_token,
        token_type="bearer",
        expires_in=expires_seconds,
    )


@router.get("/me", response_model=MeResponse)
async def get_me(current_user: User = Depends(get_current_user_required)):
    """Get authenticated user profile."""
    return MeResponse(
        success=True,
        user=UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        )
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user_required)):
    """Refresh access token."""
    access_token = create_access_token(
        data={"sub": current_user.id, "username": current_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
