"""API routes for inspecting available models and providers."""

from fastapi import APIRouter
from src.providers.registry import model_registry
from src.api.schemas.responses import ModelListResponse, ModelInfoResponse

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("", response_model=ModelListResponse)
async def list_available_models():
    """Retrieve all configured models with availability and pricing metadata."""
    models_data = model_registry.list_models()
    model_items = [ModelInfoResponse(**m) for m in models_data]
    return ModelListResponse(models=model_items, total=len(model_items))
