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


# ============================================================================
# Export/Import Operations (Sprint 4 - Team Collaboration)
# ============================================================================

def export_feedback_to_dict(
    db: Session,
    include_html: bool = False,
    include_screenshots: bool = False,
    since_date: Optional[datetime] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Export feedback entries to dictionary format for JSON serialization.
    
    Security features:
    - Sanitizes URLs (strips query parameters)
    - Excludes HTML snapshots by default
    - Converts user IDs to emails
    - Removes execution FK references
    """
    from urllib.parse import urlparse, urlunparse
    from app.models.user import User
    from app.models.test_execution import TestExecution
    from app.models.test_case import TestCase
    
    query = db.query(ExecutionFeedback)
    
    if since_date:
        query = query.filter(ExecutionFeedback.created_at >= since_date)
    
    feedback_items = query.order_by(desc(ExecutionFeedback.created_at)).limit(limit).all()
    
    exported_data = []
    
    for feedback in feedback_items:
        # Get execution metadata (handle missing execution gracefully)
        execution = None
        test_case = None
        
        try:
            execution = db.query(TestExecution).filter(TestExecution.id == feedback.execution_id).first()
            if execution:
                test_case = db.query(TestCase).filter(TestCase.id == execution.test_case_id).first()
        except:
            pass  # Handle missing execution gracefully
        
        # Get user email
        corrected_by_email = None
        if feedback.corrected_by_user_id:
            try:
                user = db.query(User).filter(User.id == feedback.corrected_by_user_id).first()
                if user:
                    corrected_by_email = user.email
            except:
                pass  # Handle missing user gracefully
        
        # Sanitize URL (strip query parameters)
        sanitized_url = None
        if feedback.page_url:
            try:
                parsed = urlparse(feedback.page_url)
                sanitized_url = urlunparse(parsed._replace(query="", fragment=""))
            except:
                sanitized_url = feedback.page_url
        
        # Build export item
        export_item = {
            # Execution metadata (no FK reference)
            "execution_metadata": {
                "test_name": test_case.title if test_case else None,
                "test_case_id": execution.test_case_id if execution else None,
                "execution_date": execution.started_at.isoformat() if execution and execution.started_at else None
            },
            
            # User reference by email
            "corrected_by": corrected_by_email,
            
            # Feedback data
            "step_index": feedback.step_index,
            "failure_type": feedback.failure_type,
            "error_message": feedback.error_message,
            "page_url": sanitized_url,
            
            # Conditionally include HTML and screenshots
            "page_html_snapshot": feedback.page_html_snapshot if include_html else None,
            "screenshot_url": feedback.screenshot_url if include_screenshots else None,
            
            # Browser context
            "browser_type": feedback.browser_type,
            "viewport_width": feedback.viewport_width,
            "viewport_height": feedback.viewport_height,
            
            # Selector info
            "failed_selector": feedback.failed_selector,
            "selector_type": feedback.selector_type,
            
            # Correction data
            "corrected_step": feedback.corrected_step,
            "correction_source": feedback.correction_source,
            "correction_confidence": feedback.correction_confidence,
            "correction_applied_at": feedback.correction_applied_at.isoformat() if feedback.correction_applied_at else None,
            
            # Performance metrics
            "step_duration_ms": feedback.step_duration_ms,
            "memory_usage_mb": feedback.memory_usage_mb,
            "network_requests": feedback.network_requests,
            
            # Anomaly detection
            "is_anomaly": feedback.is_anomaly,
            "anomaly_score": feedback.anomaly_score,
            "anomaly_type": feedback.anomaly_type,
            
            # Metadata
            "notes": feedback.notes,
            "tags": feedback.tags,
            "created_at": feedback.created_at.isoformat(),
            "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None
        }
        
        exported_data.append(export_item)
    
    return exported_data


def generate_feedback_hash(feedback_data: Dict[str, Any]) -> str:
    """
    Generate a unique hash for feedback data to detect duplicates.
    Based on: failure_type, failed_selector, page_url, created_at
    """
    import hashlib
    import json
    
    # Create hash key from identifying fields
    hash_fields = {
        "failure_type": feedback_data.get("failure_type"),
        "failed_selector": feedback_data.get("failed_selector"),
        "page_url": feedback_data.get("page_url"),
        "created_at": feedback_data.get("created_at"),
        "step_index": feedback_data.get("step_index")
    }
    
    hash_string = json.dumps(hash_fields, sort_keys=True)
    return hashlib.sha256(hash_string.encode()).hexdigest()


def import_feedback_from_dict(
    db: Session,
    feedback_data: Dict[str, Any],
    current_user_id: int,
    merge_strategy: str = "skip_duplicates"
) -> tuple[bool, str]:
    """
    Import a single feedback entry from dictionary.
    
    Returns: (success: bool, message: str)
    
    merge_strategy:
    - skip_duplicates: Skip if already exists
    - update_existing: Update if exists
    - create_all: Always create new entry
    """
    from app.models.user import User
    
    # Check for duplicate
    feedback_hash = generate_feedback_hash(feedback_data)
    
    if merge_strategy != "create_all":
        # Check if similar feedback exists
        existing = db.query(ExecutionFeedback).filter(
            and_(
                ExecutionFeedback.failure_type == feedback_data.get("failure_type"),
                ExecutionFeedback.failed_selector == feedback_data.get("failed_selector"),
                ExecutionFeedback.page_url == feedback_data.get("page_url")
            )
        ).first()
        
        if existing:
            if merge_strategy == "skip_duplicates":
                return (False, f"Skipped: Duplicate feedback (hash: {feedback_hash[:8]})")
            elif merge_strategy == "update_existing":
                # Update existing feedback
                if feedback_data.get("corrected_step"):
                    existing.corrected_step = feedback_data.get("corrected_step")
                    existing.correction_source = feedback_data.get("correction_source")
                    existing.correction_confidence = feedback_data.get("correction_confidence")
                    existing.corrected_by_user_id = current_user_id
                    existing.notes = feedback_data.get("notes")
                    existing.tags = feedback_data.get("tags")
                    existing.updated_at = datetime.utcnow()
                    db.commit()
                    return (True, f"Updated: Existing feedback {existing.id}")
    
    # Map email to user ID
    corrected_by_user_id = None
    if feedback_data.get("corrected_by"):
        user = db.query(User).filter(User.email == feedback_data.get("corrected_by")).first()
        corrected_by_user_id = user.id if user else current_user_id
    else:
        corrected_by_user_id = current_user_id if feedback_data.get("corrected_step") else None
    
    # Parse datetime strings
    created_at = datetime.fromisoformat(feedback_data["created_at"]) if feedback_data.get("created_at") else datetime.utcnow()
    correction_applied_at = datetime.fromisoformat(feedback_data["correction_applied_at"]) if feedback_data.get("correction_applied_at") else None
    
    # Create new feedback entry (without execution_id FK)
    new_feedback = ExecutionFeedback(
        execution_id=None,  # No FK reference - imported feedback is standalone
        step_index=feedback_data.get("step_index"),
        failure_type=feedback_data.get("failure_type"),
        error_message=feedback_data.get("error_message"),
        page_url=feedback_data.get("page_url"),
        page_html_snapshot=feedback_data.get("page_html_snapshot"),
        screenshot_url=feedback_data.get("screenshot_url"),
        browser_type=feedback_data.get("browser_type"),
        viewport_width=feedback_data.get("viewport_width"),
        viewport_height=feedback_data.get("viewport_height"),
        failed_selector=feedback_data.get("failed_selector"),
        selector_type=feedback_data.get("selector_type"),
        corrected_step=feedback_data.get("corrected_step"),
        correction_source=feedback_data.get("correction_source") or "imported",
        correction_confidence=feedback_data.get("correction_confidence"),
        correction_applied_at=correction_applied_at,
        corrected_by_user_id=corrected_by_user_id,
        step_duration_ms=feedback_data.get("step_duration_ms"),
        memory_usage_mb=feedback_data.get("memory_usage_mb"),
        network_requests=feedback_data.get("network_requests"),
        is_anomaly=feedback_data.get("is_anomaly", False),
        anomaly_score=feedback_data.get("anomaly_score"),
        anomaly_type=feedback_data.get("anomaly_type"),
        notes=feedback_data.get("notes"),
        tags=feedback_data.get("tags"),
        created_at=created_at,
        updated_at=datetime.utcnow()
    )
    
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    
    return (True, f"Created: New feedback {new_feedback.id}")
