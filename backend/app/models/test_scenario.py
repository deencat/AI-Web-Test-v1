"""
Test Scenario Model
Stores generated test scenarios with steps, dependencies, and test data
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base, utc_now


class TestScenario(Base):
    """Test scenario model for generated multi-step tests"""
    __tablename__ = "test_scenarios"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    template_id = Column(Integer, ForeignKey("test_templates.id"), nullable=True)
    
    # Scenario structure (JSON)
    steps = Column(JSON, nullable=False)  # Array of {action, target, data, assertion}
    dependencies = Column(JSON)  # Array of {step_index, depends_on: [step_indices]}
    test_data = Column(JSON)  # Generated faker data or user-provided data
    expected_results = Column(JSON)  # Expected outcomes for each step
    
    # Execution tracking
    status = Column(String(50), default="draft", index=True)  # draft, validated, ready, executed, failed
    validation_errors = Column(JSON)  # Array of error messages
    execution_count = Column(Integer, default=0)
    last_execution = Column(DateTime)
    last_execution_status = Column(String(50))  # passed, failed, error
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    template = relationship("TestTemplate", back_populates="scenarios")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<TestScenario {self.name} ({self.status})>"
    
    def mark_validated(self, is_valid: bool, errors: list = None):
        """Mark scenario as validated or invalid"""
        if is_valid:
            self.status = "validated"
            self.validation_errors = None
        else:
            self.status = "validation_failed"
            self.validation_errors = errors or []
    
    def record_execution(self, success: bool):
        """Record execution result"""
        self.execution_count += 1
        self.last_execution = datetime.now(timezone.utc)
        self.last_execution_status = "passed" if success else "failed"
        self.status = "executed"
    
    def get_step_count(self) -> int:
        """Get number of steps in scenario"""
        return len(self.steps) if self.steps else 0
