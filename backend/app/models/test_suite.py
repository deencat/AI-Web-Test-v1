"""
Test Suite Database Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class TestSuite(Base):
    """Test Suite model - groups multiple test cases."""
    __tablename__ = "test_suites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags as JSON
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    items = relationship("TestSuiteItem", back_populates="suite", cascade="all, delete-orphan")
    executions = relationship("SuiteExecution", back_populates="suite", cascade="all, delete-orphan")


class TestSuiteItem(Base):
    """Test Suite Item model - links test cases to suites with execution order."""
    __tablename__ = "test_suite_items"
    
    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    execution_order = Column(Integer, nullable=False)  # Order in which tests should run
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    suite = relationship("TestSuite", back_populates="items")
    test_case = relationship("TestCase")


class SuiteExecution(Base):
    """Suite Execution model - tracks execution of entire test suites."""
    __tablename__ = "suite_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # pending, running, completed, failed
    browser = Column(String(50), nullable=False)
    environment = Column(String(50), nullable=False)
    triggered_by = Column(String(50), nullable=False)
    stop_on_failure = Column(Integer, default=0)  # 0=False, 1=True (SQLite doesn't have boolean)
    
    total_tests = Column(Integer, nullable=False)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    suite = relationship("TestSuite", back_populates="executions")
    user = relationship("User")
