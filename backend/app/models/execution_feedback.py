"""Execution feedback model for collecting learning data from test executions."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class ExecutionFeedback(Base):
    """
    Execution Feedback Model - Collects detailed context from test execution failures.
    
    This model is the foundation of the learning system, capturing:
    - Failure details (type, error message, screenshots)
    - Page context (URL, HTML snapshot)
    - Human or AI corrections
    - Performance metrics
    - Anomaly detection data
    
    Used by PatternAnalyzer in Sprint 5 to learn from past failures.
    """
    __tablename__ = "execution_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Execution reference (nullable for imported feedback from other databases)
    execution_id = Column(Integer, ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=True, index=True)
    execution = relationship("TestExecution", backref="feedback_items")
    
    # Step reference (optional - can be null for execution-level feedback)
    step_index = Column(Integer, nullable=True)  # Which step failed (0-based index)
    
    # Failure details
    failure_type = Column(String(100), nullable=True, index=True)  # selector_not_found, timeout, assertion_failed, etc.
    error_message = Column(Text, nullable=True)  # Full error message
    screenshot_url = Column(String(500), nullable=True)  # Failure screenshot path
    page_url = Column(String(2000), nullable=True, index=True)  # URL where failure occurred
    page_html_snapshot = Column(Text, nullable=True)  # HTML at failure point for pattern analysis
    
    # Browser context
    browser_type = Column(String(50), nullable=True)  # chromium, firefox, webkit
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)
    
    # Selector information (for element not found errors)
    failed_selector = Column(String(2000), nullable=True)  # The selector that failed
    selector_type = Column(String(50), nullable=True)  # css, xpath, text, aria, etc.
    
    # Human or AI correction
    corrected_step = Column(JSON, nullable=True)  # What fixed it (JSON of step data)
    correction_source = Column(String(50), nullable=True, index=True)  # human, ai_suggestion, auto_applied
    correction_confidence = Column(Float, nullable=True)  # 0.0-1.0 confidence score
    correction_applied_at = Column(DateTime, nullable=True)
    corrected_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Performance metrics
    step_duration_ms = Column(Integer, nullable=True)  # How long the step took
    memory_usage_mb = Column(Float, nullable=True)  # Memory usage during step
    network_requests = Column(Integer, nullable=True)  # Number of network requests
    
    # Anomaly detection
    is_anomaly = Column(Boolean, default=False, index=True)  # Flagged as anomaly
    anomaly_score = Column(Float, nullable=True)  # 0.0-1.0 anomaly confidence
    anomaly_type = Column(String(100), nullable=True)  # performance, flaky, environment, etc.
    
    # Metadata
    notes = Column(Text, nullable=True)  # Human-added notes about the failure
    tags = Column(JSON, nullable=True)  # Tags for categorization
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ExecutionFeedback(id={self.id}, execution_id={self.execution_id}, failure_type={self.failure_type})>"
