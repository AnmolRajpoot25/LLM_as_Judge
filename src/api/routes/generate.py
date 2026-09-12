from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import UserApiKeyRecord
from src.api.routes.auth import get_current_user_optional
from src.api.schemas.requests import GenerateCompareRequest
from src.api.dependencies import get_comparison_service
from src.services.comparison_service import ComparisonService
from src.providers.base import GenerationConfig

from src.services.auth import decrypt_api_key

router = APIRouter(prefix="/api/generate-compare", tags=["Generation & Comparison"])


@router.post("")
async def generate_and_compare(
    request: GenerateCompareRequest,
    service: ComparisonService = Depends(get_comparison_service),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Mode 1: Concurrently generates answers for selected models and evaluates them pairwise.
    Supports 2 to 4 models. Gracefully handles partial provider failures.
    Supports user-configured API keys.
    """
    try:
        # Resolve custom API keys
        effective_keys = {}
        # 1. Load keys from authenticated user if available
        if user:
            user_keys = db.query(UserApiKeyRecord).filter(UserApiKeyRecord.user_id == user.id).all()
            for k in user_keys:
                if k.api_key and k.api_key.strip():
                    effective_keys[k.provider] = decrypt_api_key(k.api_key.strip())

        # 2. Override with any explicitly passed keys in request
        if request.custom_api_keys:
            effective_keys.update(request.custom_api_keys)

        gen_config = None
        if request.generation_config:
            gen_config = GenerationConfig(
                temperature=request.generation_config.temperature,
                max_tokens=request.generation_config.max_tokens,
                top_p=request.generation_config.top_p,
                extra_params=request.generation_config.extra_params
            )

        report = await service.run_generate_and_compare(
            models=request.models,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            generation_config=gen_config,
            position_swap_check=request.position_swap_check,
            custom_api_keys=effective_keys if effective_keys else None
        )
        return report

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation comparison failed: {str(exc)}"
        )
