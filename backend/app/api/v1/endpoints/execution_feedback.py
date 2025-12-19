"""API endpoints for execution feedback."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import execution_feedback as crud_feedback
from app.schemas.execution_feedback import (
    ExecutionFeedbackCreate,
    ExecutionFeedbackUpdate,
    ExecutionFeedbackResponse,
    ExecutionFeedbackListItem,
    ExecutionFeedbackListResponse,
    ExecutionFeedbackStats,
    CorrectionSubmit
)
from app.models.user import User

router = APIRouter()


@router.get("/executions/{execution_id}/feedback", response_model=List[ExecutionFeedbackResponse])
def get_execution_feedback(
    execution_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all feedback entries for a specific execution.
    
    Returns feedback items ordered by step_index, then created_at.
    """
    feedback_items = crud_feedback.get_feedback_by_execution(
        db=db,
        execution_id=execution_id,
        skip=skip,
        limit=limit
    )
    
    return feedback_items


@router.get("/feedback", response_model=ExecutionFeedbackListResponse)
def list_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    failure_type: Optional[str] = Query(None, description="Filter by failure type"),
    correction_source: Optional[str] = Query(None, description="Filter by correction source"),
    is_anomaly: Optional[bool] = Query(None, description="Filter by anomaly status"),
    has_correction: Optional[bool] = Query(None, description="Filter by correction presence"),
    execution_id: Optional[int] = Query(None, description="Filter by execution ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List execution feedback with optional filters.
    
    Supports filtering by:
    - failure_type: Type of failure (selector_not_found, timeout, etc.)
    - correction_source: Source of correction (human, ai_suggestion, auto_applied)
    - is_anomaly: Whether flagged as anomaly
    - has_correction: Whether correction has been submitted
    - execution_id: Filter by specific execution
    """
    items = crud_feedback.list_feedback(
        db=db,
        skip=skip,
        limit=limit,
        failure_type=failure_type,
        correction_source=correction_source,
        is_anomaly=is_anomaly,
        has_correction=has_correction,
        execution_id=execution_id
    )
    
    total = crud_feedback.count_feedback(
        db=db,
        failure_type=failure_type,
        correction_source=correction_source,
        is_anomaly=is_anomaly,
        has_correction=has_correction,
        execution_id=execution_id
    )
    
    return ExecutionFeedbackListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/feedback/{feedback_id}", response_model=ExecutionFeedbackResponse)
def get_feedback(
    feedback_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get a specific feedback entry by ID.
    
    Includes full details including HTML snapshot.
    """
    feedback = crud_feedback.get_feedback(db=db, feedback_id=feedback_id)
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )
    
    return feedback


@router.post("/feedback", response_model=ExecutionFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    feedback: ExecutionFeedbackCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new execution feedback entry (typically called by execution service).
    
    This endpoint is primarily for manual feedback creation or testing.
    In production, feedback is automatically created during test execution.
    """
    return crud_feedback.create_feedback(db=db, feedback=feedback)


@router.put("/feedback/{feedback_id}", response_model=ExecutionFeedbackResponse)
def update_feedback(
    feedback_id: int,
    updates: ExecutionFeedbackUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update a feedback entry.
    
    Allows updating:
    - failure_type
    - error_message
    - notes
    - tags
    - anomaly detection fields
    """
    feedback = crud_feedback.update_feedback(
        db=db,
        feedback_id=feedback_id,
        updates=updates
    )
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )
    
    return feedback


@router.post("/feedback/{feedback_id}/correction", response_model=ExecutionFeedbackResponse)
def submit_correction(
    feedback_id: int,
    correction: CorrectionSubmit,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submit a correction for a feedback entry.
    
    This is the primary way users provide feedback to the learning system.
    The corrected step data will be used by PatternAnalyzer to suggest fixes.
    
    correction_source values:
    - human: User manually corrected the issue
    - ai_suggestion: AI suggested the correction, user accepted
    - auto_applied: System automatically applied high-confidence correction
    """
    feedback = crud_feedback.submit_correction(
        db=db,
        feedback_id=feedback_id,
        correction=correction,
        user_id=current_user.id
    )
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )
    
    return feedback


@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a feedback entry.
    """
    success = crud_feedback.delete_feedback(db=db, feedback_id=feedback_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )
    
    return None


@router.get("/feedback/stats/summary", response_model=ExecutionFeedbackStats)
def get_feedback_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get overall feedback statistics.
    
    Returns:
    - Total feedback entries
    - Total failures
    - Total corrected failures
    - Total anomalies
    - Correction rate (%)
    - Top 10 failure types with counts
    - Top 10 failed selectors with counts
    """
    stats = crud_feedback.get_feedback_stats(db=db)
    return ExecutionFeedbackStats(**stats)
