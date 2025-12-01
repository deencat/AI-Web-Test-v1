"""CRUD operations for password reset tokens."""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models.password_reset import PasswordResetToken
from app.models.user import User


def create_password_reset_token(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expires_in_hours: int = 24
) -> PasswordResetToken:
    """Create a new password reset token for a user."""
    token = PasswordResetToken.create_token(user_id, expires_in_hours)
    token.ip_address = ip_address  # type: ignore
    token.user_agent = user_agent  # type: ignore
    
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_password_reset_token(db: Session, token: str) -> Optional[PasswordResetToken]:
    """Get password reset token by token string."""
    return db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()


def get_valid_password_reset_token(db: Session, token: str) -> Optional[PasswordResetToken]:
    """Get valid (unused and not expired) password reset token."""
    reset_token = get_password_reset_token(db, token)
    if reset_token and reset_token.is_valid():
        return reset_token
    return None


def mark_token_as_used(db: Session, token: PasswordResetToken) -> PasswordResetToken:
    """Mark password reset token as used."""
    token.mark_used()
    db.commit()
    db.refresh(token)
    return token


def invalidate_user_tokens(db: Session, user_id: int) -> int:
    """Invalidate all unused password reset tokens for a user."""
    count = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.is_used.is_(False),  # type: ignore
        PasswordResetToken.expires_at > datetime.utcnow()
    ).update({"is_used": True, "used_at": datetime.utcnow()})
    db.commit()
    return count


def cleanup_expired_tokens(db: Session) -> int:
    """Delete expired password reset tokens (cleanup job)."""
    count = db.query(PasswordResetToken).filter(
        PasswordResetToken.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    return count
