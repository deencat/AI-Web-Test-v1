"""
Browser Profile Model
Created: February 3, 2026
Purpose: Store browser profile metadata (no sensitive session data)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class BrowserProfile(Base):
    """
    Browser Profile metadata registry.
    
    Stores ONLY metadata about profiles - NO session data stored server-side.
    Session data (cookies, localStorage) is:
    - Created by user on their device
    - Packaged as ZIP file
    - Uploaded temporarily during execution
    - Processed entirely in RAM (zero disk exposure)
    - Auto-cleaned by Python garbage collection
    """
    __tablename__ = "browser_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Profile metadata
    profile_name = Column(String(100), nullable=False)
    os_type = Column(String(20), nullable=False)  # "windows", "linux", "macos"
    browser_type = Column(String(20), nullable=False, default="chromium")  # "chromium", "firefox", "webkit"
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)  # Last time profile was exported/synced
    
    # Relationships
    user = relationship("User", back_populates="browser_profiles")

    def __repr__(self):
        return f"<BrowserProfile(id={self.id}, name='{self.profile_name}', os='{self.os_type}', user_id={self.user_id})>"
