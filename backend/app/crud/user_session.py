"""CRUD operations for user sessions."""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.models.user_session import UserSession


def create_user_session(
    db: Session,
    user_id: int,
    device_name: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expires_in_days: int = 30
) -> UserSession:
    """Create a new user session."""
    session = UserSession.create_session(
        user_id=user_id,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_in_days=expires_in_days
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_session(db: Session, session_id: int) -> Optional[UserSession]:
    """Get user session by ID."""
    return db.query(UserSession).filter(UserSession.id == session_id).first()


def get_user_session_by_token(db: Session, session_token: str) -> Optional[UserSession]:
    """Get user session by session token."""
    return db.query(UserSession).filter(
        UserSession.session_token == session_token
    ).first()


def get_user_sessions(
    db: Session,
    user_id: int,
    active_only: bool = False
) -> List[UserSession]:
    """Get all sessions for a user."""
    query = db.query(UserSession).filter(UserSession.user_id == user_id)
    
    if active_only:
        query = query.filter(
            UserSession.is_active.is_(True),  # type: ignore
            UserSession.expires_at > datetime.utcnow()
        )
    
    return query.order_by(UserSession.last_activity.desc()).all()  # type: ignore


def update_session_activity(db: Session, session: UserSession) -> UserSession:
    """Update session's last activity timestamp."""
    session.update_activity()
    db.commit()
    db.refresh(session)
    return session


def logout_session(db: Session, session: UserSession) -> UserSession:
    """Logout a specific session."""
    session.logout()
    db.commit()
    db.refresh(session)
    return session


def logout_user_sessions(db: Session, user_id: int) -> int:
    """Logout all active sessions for a user."""
    count = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active.is_(True)  # type: ignore
    ).update({
        "is_active": False,
        "logged_out_at": datetime.utcnow()
    })
    db.commit()
    return count


def delete_session(db: Session, session_id: int) -> bool:
    """Delete a specific session."""
    session = get_user_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def cleanup_expired_sessions(db: Session) -> int:
    """Delete expired sessions (cleanup job)."""
    count = db.query(UserSession).filter(
        UserSession.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    return count
