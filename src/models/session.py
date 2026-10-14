import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, DateTime, Float, Integer, Boolean, ForeignKey, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    api_keys: Mapped[List["UserApiKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserApiKey(Base):
    __tablename__ = "user_api_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="api_keys")


class SessionStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    INSUFFICIENT_SUCCESSFUL_MODELS = "INSUFFICIENT_SUCCESSFUL_MODELS"


class SessionMode(str, enum.Enum):
    GENERATE_AND_COMPARE = "GENERATE_AND_COMPARE"
    SINGLE_GENERATION = "SINGLE_GENERATION"
    MANUAL_COMPARE = "MANUAL_COMPARE"
    BATCH_EVALUATION = "BATCH_EVALUATION"


class GenerationModel(Base):
    __tablename__ = "generation_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="generations")

    __table_args__ = (
        Index("ix_generation_models_session_id", "session_id"),
        Index("ix_generation_models_model_id", "model_id"),
    )


class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    comparison_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    pair_number: Mapped[int] = mapped_column(Integer, nullable=False)
    model_a_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_a_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_b_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_b_name: Mapped[str] = mapped_column(String(255), nullable=False)
    winner_model_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    judge_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_judge_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position_swap_check: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="comparisons")

    __table_args__ = (
        Index("ix_comparisons_session_id", "session_id"),
        Index("ix_comparisons_winner_model_id", "winner_model_id"),
    )


class Ranking(Base):
    __tablename__ = "rankings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    total_matches: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="rankings")

    __table_args__ = (
        Index("ix_rankings_session_id", "session_id"),
        Index("ix_rankings_model_id", "model_id"),
    )


class Metrics(Base):
    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_models: Mapped[int] = mapped_column(Integer, default=0)
    successful_generations: Mapped[int] = mapped_column(Integer, default=0)
    failed_generations: Mapped[int] = mapped_column(Integer, default=0)
    total_comparisons: Mapped[int] = mapped_column(Integer, default=0)
    successful_comparisons: Mapped[int] = mapped_column(Integer, default=0)
    failed_comparisons: Mapped[int] = mapped_column(Integer, default=0)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    avg_generation_latency: Mapped[float] = mapped_column(Float, default=0.0)
    avg_judge_latency: Mapped[float] = mapped_column(Float, default=0.0)
    session_wall_clock_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    position_swap_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    position_swap_executed: Mapped[int] = mapped_column(Integer, default=0)
    position_swap_consistent: Mapped[int] = mapped_column(Integer, default=0)
    position_swap_inconsistent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="metrics")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    mode: Mapped[SessionMode] = mapped_column(SQLEnum(SessionMode), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(SQLEnum(SessionStatus), default=SessionStatus.PENDING, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_models: Mapped[List[str]] = mapped_column(JSON, default=list)
    position_swap_check: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    generations: Mapped[List["GenerationModel"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    comparisons: Mapped[List["Comparison"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    rankings: Mapped[List["Ranking"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    metrics: Mapped[Optional["Metrics"]] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        Index("ix_sessions_status", "status"),
        Index("ix_sessions_created_at", "created_at"),
    )