"""API v2: Heal test from execution feedback (HF-5)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.heal_review import HealFromFeedbackRequest, HealFromFeedbackResponse
from app.services.factory_heal_service import heal_from_feedback

router = APIRouter()


@router.post(
    "/heal-from-feedback",
    response_model=HealFromFeedbackResponse,
    summary="Heal a failed test from execution feedback",
    description=(
        "Loads execution feedback, classifies failure (xpath vs flow), then either "
        "clears XPath cache and retries or recrawls with reference_test_id."
    ),
)
def post_heal_from_feedback(
    body: HealFromFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HealFromFeedbackResponse:
    try:
        result = heal_from_feedback(
            db,
            body.execution_id,
            current_user.id,
            retry_execution=body.retry_execution,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return HealFromFeedbackResponse(**result)
