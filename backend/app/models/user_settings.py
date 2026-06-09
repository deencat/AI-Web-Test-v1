"""User settings model for AI provider configuration."""
from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text
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
    generation_model = Column(String(200), nullable=False)
    generation_temperature = Column(Float, default=0.7)
    generation_max_tokens = Column(Integer, default=4096)
    
    # Test Execution Configuration (Stagehand/Playwright)
    execution_provider = Column(String(50), nullable=False, default="openrouter")
    execution_model = Column(String(200), nullable=False)
    execution_temperature = Column(Float, default=0.7)
    execution_max_tokens = Column(Integer, default=4096)
    
    # Stagehand Provider Selection (Sprint 5: Dual Stagehand Provider System)
    # Options: 'python' (default, current implementation) or 'typescript' (official library)
    stagehand_provider = Column(String(20), nullable=False, default="python")

    # Sprint 10.15: vLLM Thinking Mode Toggle
    # DEFAULT FALSE — safe for existing rows; no data loss on migration.
    local_vllm_enable_thinking = Column(Boolean, nullable=False, default=False)

    # Phase 2: Custom vLLM model — allows user to specify any model+endpoint not in the
    # hardcoded list.  NULL = no custom model configured.
    local_vllm_custom_model = Column(String(200), nullable=True)
    local_vllm_custom_endpoint = Column(String(500), nullable=True)
    local_vllm_api_key = Column(String(255), nullable=True)

    # Per-Agent Model Overrides (Sprint 10.6: Per-Agent Model Provider & Model Selection)
    # NULL = use Azure default (ChatGPT-UAT) — no data migration required.
    observation_provider = Column(String(100), nullable=True)
    observation_model = Column(String(200), nullable=True)
    requirements_provider = Column(String(100), nullable=True)
    requirements_model = Column(String(200), nullable=True)
    analysis_provider = Column(String(100), nullable=True)
    analysis_model = Column(String(200), nullable=True)
    evolution_provider = Column(String(100), nullable=True)
    evolution_model = Column(String(200), nullable=True)

    # Sprint 10.20: per-user custom model registry (JSON stored as TEXT)
    custom_models = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="settings")
