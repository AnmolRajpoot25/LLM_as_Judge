"""Authentication API routes for user registration, login, and session validation."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1)


def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """Optional dependency extracting user from Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "").strip()
    return AuthService.get_current_user_from_token(db, token)


def get_current_user_required(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """Required dependency requiring valid authenticated user."""
    user = get_current_user_optional(authorization, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token."
        )
    return user


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    try:
        result = AuthService.register_user(
            db=db,
            username=request.username,
            email=request.email,
            password=request.password
        )
        return {"success": True, **result}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(exc)}"
        )


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Log in and retrieve auth bearer token."""
    try:
        result = AuthService.authenticate_user(
            db=db,
            username_or_email=request.username_or_email,
            password=request.password
        )
        return {"success": True, **result}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(exc)}"
        )


@router.get("/me")
async def get_me(user=Depends(get_current_user_required)):
    """Get authenticated user profile."""
    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }
