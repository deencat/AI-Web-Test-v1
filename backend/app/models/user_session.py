"""User Session model for session management and tracking."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional
import secrets

from app.db.base import Base


class UserSession(Base):
    """User session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session details
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    
    # Session validity
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    logged_out_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="sessions")
    
    @classmethod
    def create_session(
        cls, 
        user_id: int, 
        expires_in_days: int = 30,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "UserSession":
        """Create a new user session."""
        return cls(
            session_token=secrets.token_urlsafe(32),
            user_id=user_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        return (
            self.is_active and
            self.expires_at > datetime.utcnow()
        )
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def logout(self):
        """Mark session as logged out."""
        self.is_active = False
        self.logged_out_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
