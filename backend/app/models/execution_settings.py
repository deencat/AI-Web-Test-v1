"""
Execution Settings Model for 3-Tier Execution Engine
Sprint 5.5: Configurable fallback strategies for test execution
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ExecutionSettings(Base):
    """
    User-specific execution settings for 3-Tier Execution Engine.
    
    Configures fallback strategies for test execution:
    - Option A: Tier 1 → Tier 2 (Cost-conscious, 90-95% success)
    - Option B: Tier 1 → Tier 3 (AI-first, 92-94% success)
    - Option C: Tier 1 → Tier 2 → Tier 3 (Maximum reliability, 97-99% success)
    """
    __tablename__ = "execution_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Fallback Strategy Selection
    # Options: 'option_a', 'option_b', 'option_c'
    fallback_strategy = Column(String(20), nullable=False, default="option_c")
    
    # Performance Tuning
    max_retry_per_tier = Column(Integer, default=1)
    timeout_per_tier_seconds = Column(Integer, default=30)
    track_fallback_reasons = Column(Boolean, default=True)
    
    # Analytics
    track_strategy_effectiveness = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="execution_settings")


class XPathCache(Base):
    """
    XPath cache for Tier 2 (Hybrid Mode) performance optimization.
    
    Stores extracted XPath selectors from Stagehand observe() to avoid
    repeated LLM calls for the same element locators.
    """
    __tablename__ = "xpath_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cache key components
    page_url = Column(String(500), nullable=False, index=True)
    instruction = Column(String(500), nullable=False, index=True)
    cache_key = Column(String(100), nullable=False, unique=True, index=True)
    
    # Cached data
    xpath = Column(String(1000), nullable=False)
    selector_type = Column(String(50), default="xpath")
    
    # Validation & Self-Healing
    last_validated = Column(DateTime(timezone=True), nullable=True)
    validation_failures = Column(Integer, default=0)
    is_valid = Column(Boolean, default=True)
    
    # Performance Metrics
    hit_count = Column(Integer, default=0)
    extraction_time_ms = Column(Float, nullable=True)
    
    # Additional Info
    page_title = Column(String(200), nullable=True)
    element_text = Column(String(500), nullable=True)
    extra_data = Column(String(2000), nullable=True)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TierExecutionLog(Base):
    """
    Tracks which tier succeeded for each step execution.
    
    Used for analytics and strategy effectiveness monitoring.
    """
    __tablename__ = "tier_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Execution context
    execution_id = Column(Integer, ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    
    # Strategy & Result
    fallback_strategy = Column(String(20), nullable=False)
    final_tier = Column(Integer, nullable=False)  # 1, 2, or 3
    success = Column(Boolean, nullable=False)
    
    # Tier attempts (JSON array of tier numbers attempted)
    tiers_attempted = Column(String(100), nullable=False)  # e.g., "[1, 2]" or "[1, 2, 3]"
    
    # Performance metrics
    total_execution_time_ms = Column(Float, nullable=False)
    tier1_time_ms = Column(Float, nullable=True)
    tier2_time_ms = Column(Float, nullable=True)
    tier3_time_ms = Column(Float, nullable=True)
    
    # Error tracking
    tier1_error = Column(String(500), nullable=True)
    tier2_error = Column(String(500), nullable=True)
    tier3_error = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    execution = relationship("TestExecution", back_populates="tier_logs")
