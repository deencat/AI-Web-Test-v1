"""
A/B Test Result Model
Stores A/B test results for prompt variant comparisons in EvolutionAgent
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.base import Base


class ABTestResult(Base):
    """
    A/B Test Result Model - Stores results of prompt variant A/B tests
    
    This model tracks:
    - Which variants were tested
    - Metrics for each variant (tokens, confidence, execution success, etc.)
    - Winner selection and composite scores
    - Recommendations and statistical significance
    """
    __tablename__ = "ab_test_results"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Test identification
    test_id = Column(String(100), unique=True, nullable=False, index=True)
    test_name = Column(String(255), nullable=False)
    
    # Test configuration
    variants_tested = Column(JSON, nullable=False)  # List of variant names tested
    total_scenarios = Column(Integer, nullable=False, default=0)
    min_samples = Column(Integer, nullable=False, default=10)
    
    # Test timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    variant_metrics = Column(JSON, nullable=False)  # Dict of variant_name -> metrics
    winner = Column(String(50), nullable=True, index=True)  # Winning variant name
    winner_score = Column(Float, nullable=True)  # Composite score of winner
    statistical_significance = Column(Boolean, default=False)
    
    # Recommendations and insights
    recommendations = Column(JSON, nullable=True)  # List of recommendation strings
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<ABTestResult(id={self.id}, test_id='{self.test_id}', winner='{self.winner}')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "test_id": self.test_id,
            "test_name": self.test_name,
            "variants_tested": self.variants_tested,
            "total_scenarios": self.total_scenarios,
            "min_samples": self.min_samples,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "variant_metrics": self.variant_metrics,
            "winner": self.winner,
            "winner_score": self.winner_score,
            "statistical_significance": self.statistical_significance,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

