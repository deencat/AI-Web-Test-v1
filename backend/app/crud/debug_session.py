"""CRUD operations for debug sessions."""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.debug_session import DebugSession, DebugStepExecution, DebugMode, DebugSessionStatus
from app.schemas.debug_session import DebugSessionStartRequest


def create_debug_session(
    db: Session,
    user_id: int,
    request: DebugSessionStartRequest,
    session_id: str
) -> DebugSession:
    """Create a new debug session."""
    # Calculate prerequisite steps count (target_step - 1)
    # If skip_prerequisites is True, set to 0
    if request.skip_prerequisites:
        prerequisite_steps = 0
    else:
        prerequisite_steps = max(0, request.target_step_number - 1)
    
    session = DebugSession(
        session_id=session_id,
        mode=request.mode,
        status=DebugSessionStatus.INITIALIZING,
        execution_id=request.execution_id,
        target_step_number=request.target_step_number,
        end_step_number=request.end_step_number,
        skip_prerequisites=request.skip_prerequisites,
        prerequisite_steps_count=prerequisite_steps,
        user_id=user_id,
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_debug_session(db: Session, session_id: str) -> Optional[DebugSession]:
    """Get debug session by session ID."""
    return db.query(DebugSession).filter(DebugSession.session_id == session_id).first()


def get_debug_session_by_id(db: Session, id: int) -> Optional[DebugSession]:
    """Get debug session by primary key ID."""
    return db.query(DebugSession).filter(DebugSession.id == id).first()


def get_user_debug_sessions(
    db: Session,
    user_id: int,
    status: Optional[DebugSessionStatus] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[List[DebugSession], int]:
    """Get user's debug sessions with optional filtering."""
    query = db.query(DebugSession).filter(DebugSession.user_id == user_id)
    
    if status:
        query = query.filter(DebugSession.status == status)
    
    total = query.count()
    sessions = query.order_by(DebugSession.created_at.desc()).limit(limit).offset(offset).all()
    
    return sessions, total


def update_debug_session_status(
    db: Session,
    session_id: str,
    status: DebugSessionStatus,
    error_message: Optional[str] = None
) -> Optional[DebugSession]:
    """Update debug session status."""
    session = get_debug_session(db, session_id)
    if not session:
        return None
    
    session.status = status
    session.last_activity_at = datetime.utcnow()
    
    if error_message:
        session.error_message = error_message
    
    if status in [DebugSessionStatus.COMPLETED, DebugSessionStatus.FAILED, DebugSessionStatus.CANCELLED]:
        session.ended_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


def update_debug_session_browser_info(
    db: Session,
    session_id: str,
    user_data_dir: Optional[str] = None,
    browser_port: Optional[int] = None,
    browser_pid: Optional[int] = None
) -> Optional[DebugSession]:
    """Update debug session browser information."""
    session = get_debug_session(db, session_id)
    if not session:
        return None
    
    if user_data_dir:
        session.user_data_dir = user_data_dir
    if browser_port:
        session.browser_port = browser_port
    if browser_pid:
        session.browser_pid = browser_pid
    
    session.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


def mark_setup_completed(db: Session, session_id: str) -> Optional[DebugSession]:
    """Mark prerequisite steps setup as completed."""
    session = get_debug_session(db, session_id)
    if not session:
        return None
    
    session.setup_completed = True
    session.setup_completed_at = datetime.utcnow()
    session.status = DebugSessionStatus.READY
    session.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


def increment_debug_session_tokens(
    db: Session,
    session_id: str,
    tokens: int
) -> Optional[DebugSession]:
    """Increment token usage for a debug session."""
    session = get_debug_session(db, session_id)
    if not session:
        return None
    
    session.tokens_used += tokens
    session.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


def increment_debug_session_iterations(db: Session, session_id: str) -> Optional[DebugSession]:
    """Increment iteration count for a debug session."""
    session = get_debug_session(db, session_id)
    if not session:
        return None
    
    session.iterations_count += 1
    session.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


def update_current_step(
    db: Session,
    session_id: str,
    step_number: int
) -> Optional[DebugSession]:
    """Update current step number in debug session."""
    session = get_debug_session(db, session_id)
    if not session:
        return None
    
    session.current_step = step_number
    session.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


# ============================================================================
# Debug Step Execution CRUD
# ============================================================================

def create_debug_step_execution(
    db: Session,
    session_id: str,
    step_number: int,
    step_description: str,
    success: bool,
    error_message: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    tokens_used: int = 0
) -> DebugStepExecution:
    """Create a debug step execution record."""
    step_execution = DebugStepExecution(
        session_id=session_id,
        step_number=step_number,
        step_description=step_description,
        success=success,
        error_message=error_message,
        screenshot_path=screenshot_path,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        duration_seconds=duration_seconds,
        tokens_used=tokens_used
    )
    
    db.add(step_execution)
    db.commit()
    db.refresh(step_execution)
    return step_execution


def get_debug_step_executions(
    db: Session,
    session_id: str
) -> List[DebugStepExecution]:
    """Get all step executions for a debug session."""
    return db.query(DebugStepExecution).filter(
        DebugStepExecution.session_id == session_id
    ).order_by(DebugStepExecution.created_at).all()


def delete_debug_session(db: Session, session_id: str) -> bool:
    """Delete a debug session and all related step executions."""
    session = get_debug_session(db, session_id)
    if not session:
        return False
    
    # Delete related step executions
    db.query(DebugStepExecution).filter(DebugStepExecution.session_id == session_id).delete()
    
    # Delete session
    db.delete(session)
    db.commit()
    return True
