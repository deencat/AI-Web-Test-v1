"""
Browser Profile Model
Created: February 3, 2026
Purpose: Store browser profile metadata and encrypted session data
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class BrowserProfile(Base):
    """
    Browser Profile metadata registry.
    
    Stores profile metadata and encrypted session data for server-side reuse.
    Session data (cookies, localStorage, sessionStorage) is encrypted at rest
    using the system-wide CREDENTIAL_ENCRYPTION_KEY.
    """
    __tablename__ = "browser_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Profile metadata
    profile_name = Column(String(100), nullable=False)
    os_type = Column(String(20), nullable=False)  # "windows", "linux", "macos"
    browser_type = Column(String(20), nullable=False, default="chromium")  # "chromium", "firefox", "webkit"
    description = Column(Text, nullable=True)

    # Optional HTTP Basic Auth credentials (encrypted at rest)
    http_username = Column(String(255), nullable=True)
    http_password_encrypted = Column(Text, nullable=True)
    encryption_key_id = Column(Integer, nullable=True)

    # Encrypted session storage (server-side persistence)
    cookies_encrypted = Column(Text, nullable=True)
    local_storage_encrypted = Column(Text, nullable=True)
    session_storage_encrypted = Column(Text, nullable=True)
    auto_sync = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)  # Last time profile was synced
    
    # Relationships
    user = relationship("User", back_populates="browser_profiles")

    @property
    def has_http_credentials(self) -> bool:
        return bool(self.http_username and self.http_password_encrypted)

    @property
    def has_session_data(self) -> bool:
        return bool(
            self.cookies_encrypted
            or self.local_storage_encrypted
            or self.session_storage_encrypted
        )

    def __repr__(self):
        return f"<BrowserProfile(id={self.id}, name='{self.profile_name}', os='{self.os_type}', user_id={self.user_id})>"
