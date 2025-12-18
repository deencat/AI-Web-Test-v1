"""User settings model for AI provider configuration."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserSetting(Base):
    """User-specific settings for AI model configuration."""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Test Generation Configuration (user-configurable)
    generation_provider = Column(String(50), nullable=False, default="openrouter")
    generation_model = Column(String(100), nullable=False)
    generation_temperature = Column(Float, default=0.7)
    generation_max_tokens = Column(Integer, default=4096)
    
    # Test Execution Configuration (Stagehand/Playwright)
    execution_provider = Column(String(50), nullable=False, default="openrouter")
    execution_model = Column(String(100), nullable=False)
    execution_temperature = Column(Float, default=0.7)
    execution_max_tokens = Column(Integer, default=4096)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="settings")
