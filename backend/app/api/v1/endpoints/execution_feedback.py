"""API endpoints for execution feedback."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

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


@router.get("/feedback/export")
def export_feedback(
    include_html: bool = Query(False, description="Include HTML snapshots (increases file size)"),
    include_screenshots: bool = Query(False, description="Include screenshot paths"),
    since_date: Optional[str] = Query(None, description="Export feedback created after this date (ISO format)"),
    limit: int = Query(1000, ge=1, le=10000, description="Max feedback entries to export"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Export feedback to JSON format for team collaboration.
    
    **Sprint 4 Feature: Team Data Sync**
    
    Security features:
    - Strips sensitive query parameters from URLs
    - Excludes HTML snapshots by default (configurable)
    - Converts user IDs to emails for cross-database compatibility
    - Excludes execution FK references (stores metadata instead)
    
    Returns JSON object for download.
    """
    # Parse since_date if provided
    since_datetime = None
    if since_date:
        try:
            since_datetime = datetime.fromisoformat(since_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SS"
            )
    
    # Export feedback
    try:
        feedback_data = crud_feedback.export_feedback_to_dict(
            db=db,
            include_html=include_html,
            include_screenshots=include_screenshots,
            since_date=since_datetime,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
    
    # Build export file
    export_file = {
        "export_version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": current_user.email,
        "total_count": len(feedback_data),
        "sanitized": True,
        "includes_html": include_html,
        "includes_screenshots": include_screenshots,
        "feedback_items": feedback_data
    }
    
    # Return as JSON (FastAPI will handle serialization)
    return export_file


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


@router.post("/feedback/import")
async def import_feedback(
    file: UploadFile = File(..., description="JSON file exported from /feedback/export"),
    merge_strategy: str = Query(
        "skip_duplicates",
        description="Import strategy",
        regex="^(skip_duplicates|update_existing|create_all)$"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Import feedback from JSON file.
    
    **Sprint 4 Feature: Team Data Sync**
    
    Security features:
    - Validates JSON schema before import
    - Maps user emails to local user IDs
    - Detects duplicates via hash comparison
    - Requires authentication
    
    Merge strategies:
    - skip_duplicates: Skip if similar feedback exists (default)
    - update_existing: Update existing feedback with new corrections
    - create_all: Always create new entries (no duplicate check)
    
    Returns summary of import operation.
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file"
        )
    
    # Read and parse JSON
    try:
        content = await file.read()
        import_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    
    # Validate export format
    if "export_version" not in import_data or "feedback_items" not in import_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export file format. Must contain 'export_version' and 'feedback_items'"
        )
    
    feedback_items = import_data.get("feedback_items", [])
    
    if not feedback_items:
        return {
            "success": True,
            "message": "No feedback items to import",
            "imported_count": 0,
            "skipped_count": 0,
            "updated_count": 0,
            "failed_count": 0,
            "errors": []
        }
    
    # Import each feedback item
    imported_count = 0
    skipped_count = 0
    updated_count = 0
    failed_count = 0
    errors = []
    
    for idx, feedback_data in enumerate(feedback_items):
        try:
            success, message = crud_feedback.import_feedback_from_dict(
                db=db,
                feedback_data=feedback_data,
                current_user_id=current_user.id,
                merge_strategy=merge_strategy
            )
            
            if success:
                if "Updated" in message:
                    updated_count += 1
                else:
                    imported_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            failed_count += 1
            errors.append(f"Item {idx + 1}: {str(e)}")
    
    return {
        "success": True,
        "message": f"Import completed: {imported_count} created, {updated_count} updated, {skipped_count} skipped, {failed_count} failed",
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "updated_count": updated_count,
        "failed_count": failed_count,
        "total_processed": len(feedback_items),
        "errors": errors[:10]  # Return first 10 errors only
    }
