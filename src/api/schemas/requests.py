"""Pydantic schemas for API request validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class GenerationConfigSchema(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class GenerateCompareRequest(BaseModel):
    models: List[str] = Field(..., description="List of 2 to 4 model identifiers (e.g. ['mock:model-a', 'mock:model-b'])")
    prompt: str = Field(..., description="Problem statement or prompt to evaluate")
    system_prompt: Optional[str] = Field(default=None, description="Optional system instructions")
    generation_config: Optional[GenerationConfigSchema] = Field(default=None)
    position_swap_check: Optional[bool] = Field(default=None, description="Run position swap consistency check")
    custom_api_keys: Optional[Dict[str, str]] = Field(default=None, description="Optional per-user API keys for providers")

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Prompt cannot be empty.")
        if len(clean) > 200_000:
            raise ValueError("Prompt exceeds maximum length limit of 200,000 characters.")
        return clean

    @field_validator("models")
    @classmethod
    def validate_models(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError(f"At least 2 models must be selected (got {len(v)}).")
        if len(v) > 4:
            raise ValueError(f"At most 4 models can be selected (got {len(v)}).")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate models are not permitted.")
        return v


class ManualAnswerItem(BaseModel):
    model_name: str = Field(..., description="Name or identifier of the candidate model")
    answer: str = Field(..., description="Candidate answer text")

    @field_validator("model_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Model name cannot be empty.")
        return clean

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Candidate answer text cannot be empty.")
        return clean


class ManualCompareRequest(BaseModel):
    problem: str = Field(..., description="Problem statement or question")
    answers: List[ManualAnswerItem] = Field(..., description="List of 2 to 4 candidate answers")
    position_swap_check: Optional[bool] = Field(default=None, description="Run position swap consistency check")

    @field_validator("problem")
    @classmethod
    def validate_problem(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Problem cannot be empty.")
        return clean

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: List[ManualAnswerItem]) -> List[ManualAnswerItem]:
        if len(v) < 2:
            raise ValueError(f"At least 2 answers are required (got {len(v)}).")
        if len(v) > 4:
            raise ValueError(f"At most 4 answers can be compared (got {len(v)}).")
        names = [a.model_name for a in v]
        if len(set(names)) != len(names):
            raise ValueError("Model names in candidate answers must be unique.")
        return v


class SaveOptionsSchema(BaseModel):
    prompt: bool = True
    answers: bool = True
    evaluations: bool = True
    metrics: bool = True
    raw_responses: bool = False


class SaveSessionRequest(BaseModel):
    save_options: SaveOptionsSchema = Field(default_factory=SaveOptionsSchema)
    session_data: Dict[str, Any] = Field(..., description="Full session report data to persist")
