"""Password Reset Token model for forgot password functionality."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import secrets

from app.db.base import Base


class PasswordResetToken(Base):
    """Password reset token model for forgot password flow."""
    
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Token validity
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", backref="password_reset_tokens")
    
    @classmethod
    def create_token(cls, user_id: int, expires_in_hours: int = 24) -> "PasswordResetToken":
        """Create a new password reset token."""
        return cls(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
        )
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return (
            not self.is_used and
            self.expires_at > datetime.utcnow()
        )
    
    def mark_used(self):
        """Mark token as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.is_used})>"
