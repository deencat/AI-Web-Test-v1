"""Debug session models for Local Persistent Browser Debug Mode."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class DebugMode(str, enum.Enum):
    """Debug session mode enumeration."""
    AUTO = "auto"  # AI executes prerequisite steps automatically (600 tokens)
    MANUAL = "manual"  # User follows manual instructions (0 tokens)


class DebugSessionStatus(str, enum.Enum):
    """Debug session status enumeration."""
    INITIALIZING = "initializing"  # Browser launching
    SETUP_IN_PROGRESS = "setup_in_progress"  # Executing prerequisite steps (auto mode)
    READY = "ready"  # Browser ready, waiting for step execution
    EXECUTING = "executing"  # Executing target step
    COMPLETED = "completed"  # Session ended successfully
    FAILED = "failed"  # Session failed
    CANCELLED = "cancelled"  # User cancelled session


class DebugSession(Base):
    """Debug session model - tracks persistent browser debug sessions."""
    
    __tablename__ = "debug_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session metadata
    session_id = Column(String(100), unique=True, nullable=False, index=True)  # UUID
    mode = Column(SQLEnum(DebugMode), nullable=False, index=True)  # auto or manual
    status = Column(SQLEnum(DebugSessionStatus), nullable=False, default=DebugSessionStatus.INITIALIZING, index=True)
    
    # Test execution reference
    execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=False, index=True)
    execution = relationship("TestExecution")
    
    # Target step
    target_step_number = Column(Integer, nullable=False)  # The step user wants to debug
    prerequisite_steps_count = Column(Integer, nullable=False, default=0)  # Steps 1 to target-1
    
    # Browser session tracking
    user_data_dir = Column(String(500), nullable=True)  # Path to userDataDir for persistence
    browser_port = Column(Integer, nullable=True)  # DevTools port for remote debugging
    browser_pid = Column(Integer, nullable=True)  # Browser process ID
    
    # Progress tracking
    current_step = Column(Integer, nullable=True)  # Current step being executed
    setup_completed = Column(Boolean, default=False)  # Whether prerequisite steps are done
    
    # Token tracking
    tokens_used = Column(Integer, default=0)  # Total tokens used in this session
    iterations_count = Column(Integer, default=0)  # Number of times target step was executed
    
    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    setup_completed_at = Column(DateTime, nullable=True)  # When prerequisite steps finished
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Results
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DebugSession(id={self.id}, session_id={self.session_id}, mode={self.mode}, status={self.status})>"


class DebugStepExecution(Base):
    """Debug step execution model - tracks individual step executions within a debug session."""
    
    __tablename__ = "debug_step_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session reference
    session_id = Column(String(100), ForeignKey("debug_sessions.session_id"), nullable=False, index=True)
    
    # Step details
    step_number = Column(Integer, nullable=False)
    step_description = Column(Text, nullable=False)
    
    # Execution result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Token usage
    tokens_used = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DebugStepExecution(id={self.id}, session_id={self.session_id}, step={self.step_number}, success={self.success})>"
