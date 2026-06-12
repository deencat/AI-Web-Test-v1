"""Heal review queue and attempt tracking (HF-5)."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class HealReviewStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class FactoryHealAttempt(Base):
    """Tracks automated heal attempts per failed execution."""

    __tablename__ = "factory_heal_attempts"

    execution_id = Column(
        Integer,
        ForeignKey("test_executions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    attempt_count = Column(Integer, default=0, nullable=False)
    last_action = Column(String(64), nullable=True)
    last_test_case_id = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class HealReviewItem(Base):
    """Escalation queue when automated healing fails twice."""

    __tablename__ = "heal_review_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(32), default=HealReviewStatus.OPEN.value, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
