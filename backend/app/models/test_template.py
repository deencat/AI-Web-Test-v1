"""
Test Template Model
Stores reusable test templates for different test types (API, E2E, Mobile, Performance)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base, utc_now


class TestTemplate(Base):
    """Test template model for reusable test patterns"""
    __tablename__ = "test_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    template_type = Column(String(50), nullable=False, index=True)  # api, mobile, e2e, performance
    category_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=True)
    
    # Template structure (JSON)
    steps_template = Column(JSON, nullable=False)  # Array of step templates with ${variables}
    assertion_template = Column(JSON, nullable=False)  # Expected behavior patterns
    data_requirements = Column(JSON)  # Faker fields needed: {"user": ["email", "name"], "product": ["name"]}
    
    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    is_system = Column(Boolean, default=False)  # System templates can't be deleted
    
    # Statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # 0.0 to 100.0
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    category = relationship("KBCategory", back_populates="test_templates")
    creator = relationship("User", foreign_keys=[created_by])
    scenarios = relationship("TestScenario", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestTemplate {self.name} ({self.template_type})>"
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
    
    def update_success_rate(self, new_result: bool):
        """
        Update success rate based on new execution result
        Uses exponential moving average to weigh recent results more heavily
        """
        if self.usage_count == 0:
            self.success_rate = 100.0 if new_result else 0.0
        else:
            # Weight recent results more (70% weight to new result)
            weight = 0.3
            current_success = self.success_rate / 100.0
            new_success = 1.0 if new_result else 0.0
            self.success_rate = ((weight * current_success) + ((1 - weight) * new_success)) * 100.0
