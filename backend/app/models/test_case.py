"""Test case model for storing generated and manual test cases."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class TestType(str, enum.Enum):
    """Test type enumeration."""
    E2E = "e2e"
    UNIT = "unit"
    INTEGRATION = "integration"
    API = "api"


class Priority(str, enum.Enum):
    """Priority level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestStatus(str, enum.Enum):
    """Test execution status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestCase(Base):
    """Test case model."""
    
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    test_type = Column(SQLEnum(TestType), nullable=False, index=True)
    priority = Column(SQLEnum(Priority), nullable=False, default=Priority.MEDIUM, index=True)
    status = Column(SQLEnum(TestStatus), nullable=False, default=TestStatus.PENDING, index=True)
    
    # Test details
    steps = Column(JSON, nullable=False)  # Array of strings
    expected_result = Column(Text, nullable=False)
    preconditions = Column(Text, nullable=True)
    test_data = Column(JSON, nullable=True)  # Optional test data as JSON
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User association
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="test_cases")
    
    def __repr__(self):
        return f"<TestCase(id={self.id}, title='{self.title}', type={self.test_type}, status={self.status})>"

