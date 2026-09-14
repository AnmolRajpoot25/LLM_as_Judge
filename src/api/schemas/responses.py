"""Pydantic response models for API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ModelInfoResponse(BaseModel):
    id: str
    name: str
    provider: str
    enabled: bool
    available: bool
    pricing: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ModelListResponse(BaseModel):
    models: List[ModelInfoResponse]
    total: int


class GenericSuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
