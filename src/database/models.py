"""SQLAlchemy models for LLM-Judge comparisons and sessions."""

import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from src.database.connection import Base


class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)
    mode = Column(String(32), nullable=False)  # GENERATE_AND_COMPARE or MANUAL_COMPARE
    status = Column(String(32), nullable=False)  # COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, etc.
    saved_options = Column(JSON, nullable=True)  # Snapshot of user save choices
    metrics_summary = Column(JSON, nullable=True)
    rankings_summary = Column(JSON, nullable=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    user = relationship("UserRecord", back_populates="sessions")
    prompt = relationship("PromptRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")
    responses = relationship("ModelResponseRecord", back_populates="session", cascade="all, delete-orphan")
    comparisons = relationship("PairwiseComparisonRecord", back_populates="session", cascade="all, delete-orphan")


class PromptRecord(Base):
    __tablename__ = "prompts"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    session = relationship("SessionRecord", back_populates="prompt")


class ModelResponseRecord(Base):
    __tablename__ = "model_responses"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    model_id = Column(String(128), nullable=False)
    model_name = Column(String(128), nullable=False)
    answer = Column(Text, nullable=True)
    generation_latency = Column(Float, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    status = Column(String(32), nullable=False)  # SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    session = relationship("SessionRecord", back_populates="responses")


class PairwiseComparisonRecord(Base):
    __tablename__ = "pairwise_comparisons"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    model_a_id = Column(String(128), nullable=False)
    model_a_name = Column(String(128), nullable=False)
    model_b_id = Column(String(128), nullable=False)
    model_b_name = Column(String(128), nullable=False)
    winner = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False)  # SUCCESS, FAILED
    judge_latency = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    session = relationship("SessionRecord", back_populates="comparisons")
    evaluation = relationship("EvaluationResultRecord", back_populates="comparison", uselist=False, cascade="all, delete-orphan")


class EvaluationResultRecord(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(64), primary_key=True, index=True)
    comparison_id = Column(String(64), ForeignKey("pairwise_comparisons.id", ondelete="CASCADE"), nullable=False, unique=True)

    score_a_correctness = Column(Integer, nullable=True)
    score_a_relevance = Column(Integer, nullable=True)
    score_a_completeness = Column(Integer, nullable=True)
    score_a_reasoning = Column(Integer, nullable=True)
    score_a_clarity = Column(Integer, nullable=True)
    score_a_final = Column(Float, nullable=True)

    score_b_correctness = Column(Integer, nullable=True)
    score_b_relevance = Column(Integer, nullable=True)
    score_b_completeness = Column(Integer, nullable=True)
    score_b_reasoning = Column(Integer, nullable=True)
    score_b_clarity = Column(Integer, nullable=True)
    score_b_final = Column(Float, nullable=True)

    confidence = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    raw_judge_response = Column(Text, nullable=True)
    position_swap_result = Column(JSON, nullable=True)

    comparison = relationship("PairwiseComparisonRecord", back_populates="evaluation")


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    api_keys = relationship("UserApiKeyRecord", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("SessionRecord", back_populates="user")


class UserApiKeyRecord(Base):
    __tablename__ = "user_api_keys"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(32), nullable=False)  # openai, anthropic, gemini, deepseek, mistral, ollama
    api_key = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = relationship("UserRecord", back_populates="api_keys")

