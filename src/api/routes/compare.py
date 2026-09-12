"""API route for Mode 2: Manual Compare."""

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas.requests import ManualCompareRequest
from src.api.dependencies import get_comparison_service
from src.services.comparison_service import ComparisonService

router = APIRouter(prefix="/api/manual-compare", tags=["Manual Comparison"])


@router.post("")
async def manual_compare(
    request: ManualCompareRequest,
    service: ComparisonService = Depends(get_comparison_service)
):
    """
    Mode 2: Evaluates 2 to 4 user-entered candidate answers pairwise.
    No model generation API calls required.
    """
    try:
        answers_list = [
            {"model_name": a.model_name, "answer": a.answer}
            for a in request.answers
        ]
        report = await service.run_manual_compare(
            problem=request.problem,
            answers=answers_list,
            position_swap_check=request.position_swap_check
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
            detail=f"Manual comparison failed: {str(exc)}"
        )
