"""Test execution models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class ExecutionStatus(str, enum.Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionResult(str, enum.Enum):
    """Execution result enumeration."""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


class TestExecution(Base):
    """Test execution model - tracks test runs."""
    
    __tablename__ = "test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Test case reference
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    test_case = relationship("TestCase", back_populates="executions")
    
    # Execution metadata
    status = Column(SQLEnum(ExecutionStatus), nullable=False, default=ExecutionStatus.PENDING, index=True)
    result = Column(SQLEnum(ExecutionResult), nullable=True, index=True)  # Final result after completion
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # Total execution time
    
    # Environment
    browser = Column(String(50), nullable=True)  # chromium, firefox, webkit
    environment = Column(String(50), nullable=True)  # dev, staging, production
    base_url = Column(String(500), nullable=True)  # Target URL
    
    # Results summary
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    skipped_steps = Column(Integer, default=0)
    
    # Logs and artifacts
    console_log = Column(Text, nullable=True)  # Console output
    error_message = Column(Text, nullable=True)  # Error details if failed
    screenshot_path = Column(String(500), nullable=True)  # Failure screenshot
    video_path = Column(String(500), nullable=True)  # Execution video
    
    # Metadata
    triggered_by = Column(String(50), nullable=True)  # manual, scheduled, ci_cd, webhook
    trigger_details = Column(Text, nullable=True)  # Additional trigger info (JSON)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="test_executions")
    
    steps = relationship("TestExecutionStep", back_populates="execution", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TestExecution(id={self.id}, test_case_id={self.test_case_id}, status={self.status}, result={self.result})>"


class TestExecutionStep(Base):
    """Test execution step model - tracks individual step results."""
    
    __tablename__ = "test_execution_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Execution reference
    execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=False, index=True)
    execution = relationship("TestExecution", back_populates="steps")
    
    # Step details
    step_number = Column(Integer, nullable=False)  # 1, 2, 3...
    step_description = Column(Text, nullable=False)  # What this step does
    expected_result = Column(Text, nullable=True)  # What should happen
    
    # Result
    result = Column(SQLEnum(ExecutionResult), nullable=False, index=True)
    actual_result = Column(Text, nullable=True)  # What actually happened
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Artifacts
    screenshot_path = Column(String(500), nullable=True)  # Step screenshot
    screenshot_before = Column(String(500), nullable=True)  # Before action
    screenshot_after = Column(String(500), nullable=True)  # After action
    
    # Metadata
    retry_count = Column(Integer, default=0)  # Number of retries
    is_critical = Column(Boolean, default=False)  # If this step fails, stop execution
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TestExecutionStep(id={self.id}, execution_id={self.execution_id}, step={self.step_number}, result={self.result})>"

