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
    
    # Day 7 Integration: Link to templates and scenarios
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=True, index=True)
    template_id = Column(Integer, ForeignKey("test_templates.id"), nullable=True, index=True)
    
    # Additional fields for categorization
    category_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=True, index=True)
    tags = Column(JSON, nullable=True)  # Array of strings
    metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User association
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="test_cases")
    
    # Category relationship
    category = relationship("KBCategory", backref="test_cases")
    
    # Template/Scenario relationships (Day 7 integration)
    scenario = relationship("TestScenario", backref="generated_tests", foreign_keys=[scenario_id])
    template = relationship("TestTemplate", backref="generated_tests", foreign_keys=[template_id])
    
    # Executions
    executions = relationship("TestExecution", back_populates="test_case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestCase(id={self.id}, title='{self.title}', type={self.test_type}, status={self.status})>"

