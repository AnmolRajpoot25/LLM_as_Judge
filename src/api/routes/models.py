"""API routes for inspecting available models and providers."""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import UserApiKeyRecord
from src.api.routes.auth import get_current_user_optional
from src.providers.registry import model_registry
from src.api.schemas.responses import ModelListResponse, ModelInfoResponse

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("", response_model=ModelListResponse)
async def list_available_models(
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve all configured models with availability and pricing metadata, reflecting user keys."""
    user_providers = set()
    if user:
        user_keys = db.query(UserApiKeyRecord).filter(UserApiKeyRecord.user_id == user.id).all()
        user_providers = {r.provider.lower() for r in user_keys if r.api_key and r.api_key.strip()}

    models_data = model_registry.list_models(user_providers=user_providers)
    model_items = [ModelInfoResponse(**m) for m in models_data]
    return ModelListResponse(models=model_items, total=len(model_items))

