"""Test case version model for tracking test editing history."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base, utc_now


class TestCaseVersion(Base):
    """
    Test case version model for version control.
    
    Stores complete snapshots of test cases whenever they are edited,
    enabling full version history and rollback capabilities.
    """
    
    __tablename__ = "test_versions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)  # Auto-incremented per test_case
    
    # Version content (complete snapshot)
    steps = Column(JSON, nullable=False)  # Complete test steps at this version
    expected_result = Column(Text, nullable=True)  # Expected result at this version
    test_data = Column(JSON, nullable=True)  # Test data at this version
    
    # Version metadata
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)
    created_by = Column(String(50), nullable=False)  # "user", "ai", or user_id
    change_reason = Column(String(100), nullable=True)  # "manual_fix", "ai_improvement", "execution_failure", etc.
    
    # Version tree structure (for rollback tracking)
    parent_version_id = Column(Integer, ForeignKey("test_versions.id"), nullable=True)
    
    # Relationships
    test_case = relationship("TestCase", backref="versions")
    parent_version = relationship("TestCaseVersion", remote_side=[id], backref="child_versions")
    
    def __repr__(self):
        return f"<TestCaseVersion(id={self.id}, test_case_id={self.test_case_id}, version={self.version_number}, created_by={self.created_by})>"
    
    def to_dict(self):
        """Convert version to dictionary."""
        return {
            "id": self.id,
            "test_case_id": self.test_case_id,
            "version_number": self.version_number,
            "steps": self.steps,
            "expected_result": self.expected_result,
            "test_data": self.test_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "change_reason": self.change_reason,
            "parent_version_id": self.parent_version_id
        }
