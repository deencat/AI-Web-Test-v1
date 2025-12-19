"""CRUD operations for execution feedback."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime

from app.models.execution_feedback import ExecutionFeedback
from app.schemas.execution_feedback import (
    ExecutionFeedbackCreate,
    ExecutionFeedbackUpdate,
    CorrectionSubmit
)


# ============================================================================
# Execution Feedback CRUD
# ============================================================================

def create_feedback(
    db: Session,
    feedback: ExecutionFeedbackCreate
) -> ExecutionFeedback:
    """Create a new execution feedback entry."""
    db_feedback = ExecutionFeedback(**feedback.model_dump())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback(db: Session, feedback_id: int) -> Optional[ExecutionFeedback]:
    """Get a specific feedback entry by ID."""
    return db.query(ExecutionFeedback).filter(ExecutionFeedback.id == feedback_id).first()


def get_feedback_by_execution(
    db: Session,
    execution_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ExecutionFeedback]:
    """Get all feedback entries for a specific execution."""
    return db.query(ExecutionFeedback).filter(
        ExecutionFeedback.execution_id == execution_id
    ).order_by(
        ExecutionFeedback.step_index.asc().nullslast(),
        ExecutionFeedback.created_at.asc()
    ).offset(skip).limit(limit).all()


def get_feedback_count_by_execution(db: Session, execution_id: int) -> int:
    """Get count of feedback entries for a specific execution."""
    return db.query(ExecutionFeedback).filter(
        ExecutionFeedback.execution_id == execution_id
    ).count()


def list_feedback(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    failure_type: Optional[str] = None,
    correction_source: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    has_correction: Optional[bool] = None,
    execution_id: Optional[int] = None
) -> List[ExecutionFeedback]:
    """List feedback entries with optional filters."""
    query = db.query(ExecutionFeedback)
    
    if failure_type:
        query = query.filter(ExecutionFeedback.failure_type == failure_type)
    
    if correction_source:
        query = query.filter(ExecutionFeedback.correction_source == correction_source)
    
    if is_anomaly is not None:
        query = query.filter(ExecutionFeedback.is_anomaly == is_anomaly)
    
    if has_correction is not None:
        if has_correction:
            query = query.filter(ExecutionFeedback.corrected_step.isnot(None))
        else:
            query = query.filter(ExecutionFeedback.corrected_step.is_(None))
    
    if execution_id:
        query = query.filter(ExecutionFeedback.execution_id == execution_id)
    
    return query.order_by(desc(ExecutionFeedback.created_at)).offset(skip).limit(limit).all()


def count_feedback(
    db: Session,
    failure_type: Optional[str] = None,
    correction_source: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    has_correction: Optional[bool] = None,
    execution_id: Optional[int] = None
) -> int:
    """Count feedback entries matching filters."""
    query = db.query(ExecutionFeedback)
    
    if failure_type:
        query = query.filter(ExecutionFeedback.failure_type == failure_type)
    
    if correction_source:
        query = query.filter(ExecutionFeedback.correction_source == correction_source)
    
    if is_anomaly is not None:
        query = query.filter(ExecutionFeedback.is_anomaly == is_anomaly)
    
    if has_correction is not None:
        if has_correction:
            query = query.filter(ExecutionFeedback.corrected_step.isnot(None))
        else:
            query = query.filter(ExecutionFeedback.corrected_step.is_(None))
    
    if execution_id:
        query = query.filter(ExecutionFeedback.execution_id == execution_id)
    
    return query.count()


def update_feedback(
    db: Session,
    feedback_id: int,
    updates: ExecutionFeedbackUpdate
) -> Optional[ExecutionFeedback]:
    """Update a feedback entry."""
    feedback = db.query(ExecutionFeedback).filter(ExecutionFeedback.id == feedback_id).first()
    
    if feedback:
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feedback, field, value)
        
        feedback.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(feedback)
    
    return feedback


def submit_correction(
    db: Session,
    feedback_id: int,
    correction: CorrectionSubmit,
    user_id: Optional[int] = None
) -> Optional[ExecutionFeedback]:
    """Submit a correction for a feedback entry."""
    feedback = db.query(ExecutionFeedback).filter(ExecutionFeedback.id == feedback_id).first()
    
    if feedback:
        feedback.corrected_step = correction.corrected_step
        feedback.correction_source = correction.correction_source
        feedback.correction_confidence = correction.correction_confidence
        feedback.correction_applied_at = datetime.utcnow()
        feedback.corrected_by_user_id = user_id
        
        if correction.notes:
            feedback.notes = correction.notes
        
        feedback.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(feedback)
    
    return feedback


def delete_feedback(db: Session, feedback_id: int) -> bool:
    """Delete a feedback entry."""
    feedback = db.query(ExecutionFeedback).filter(ExecutionFeedback.id == feedback_id).first()
    
    if feedback:
        db.delete(feedback)
        db.commit()
        return True
    
    return False


# ============================================================================
# Feedback Statistics
# ============================================================================

def get_feedback_stats(db: Session) -> Dict[str, Any]:
    """Get overall feedback statistics."""
    total_feedback = db.query(ExecutionFeedback).count()
    total_failures = db.query(ExecutionFeedback).filter(
        ExecutionFeedback.failure_type.isnot(None)
    ).count()
    total_corrected = db.query(ExecutionFeedback).filter(
        ExecutionFeedback.corrected_step.isnot(None)
    ).count()
    total_anomalies = db.query(ExecutionFeedback).filter(
        ExecutionFeedback.is_anomaly == True
    ).count()
    
    correction_rate = (total_corrected / total_failures * 100) if total_failures > 0 else 0.0
    
    # Top failure types
    top_failure_types = db.query(
        ExecutionFeedback.failure_type,
        func.count(ExecutionFeedback.id).label('count')
    ).filter(
        ExecutionFeedback.failure_type.isnot(None)
    ).group_by(
        ExecutionFeedback.failure_type
    ).order_by(
        desc('count')
    ).limit(10).all()
    
    # Top failed selectors
    top_failed_selectors = db.query(
        ExecutionFeedback.failed_selector,
        func.count(ExecutionFeedback.id).label('count')
    ).filter(
        ExecutionFeedback.failed_selector.isnot(None)
    ).group_by(
        ExecutionFeedback.failed_selector
    ).order_by(
        desc('count')
    ).limit(10).all()
    
    return {
        "total_feedback": total_feedback,
        "total_failures": total_failures,
        "total_corrected": total_corrected,
        "total_anomalies": total_anomalies,
        "correction_rate": round(correction_rate, 2),
        "top_failure_types": [
            {"type": ft, "count": count} 
            for ft, count in top_failure_types
        ],
        "top_failed_selectors": [
            {"selector": selector[:100], "count": count}  # Truncate long selectors
            for selector, count in top_failed_selectors
        ]
    }


def get_similar_failures(
    db: Session,
    failure_type: str,
    page_url: str,
    limit: int = 10
) -> List[ExecutionFeedback]:
    """
    Find similar failures for pattern analysis.
    Used by PatternAnalyzer in Sprint 5.
    """
    # Extract domain from page_url
    from urllib.parse import urlparse
    domain = urlparse(page_url).netloc
    
    return db.query(ExecutionFeedback).filter(
        and_(
            ExecutionFeedback.failure_type == failure_type,
            ExecutionFeedback.page_url.like(f'%{domain}%'),
            ExecutionFeedback.corrected_step.isnot(None)  # Only return corrected failures
        )
    ).order_by(
        desc(ExecutionFeedback.correction_confidence)
    ).limit(limit).all()
