"""SQLAlchemy model for test schedules."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.base import Base


class TestSchedule(Base):
    __tablename__ = "test_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=True)

    # 'interval' = every N minutes, 'cron' = cron expression
    schedule_type = Column(String(20), nullable=False, default="interval")
    interval_minutes = Column(Integer, nullable=True)   # used when schedule_type='interval'
    cron_expression = Column(String(100), nullable=True)  # used when schedule_type='cron'

    # Execution parameters
    browser = Column(String(50), nullable=False, default="chromium")
    environment = Column(String(50), nullable=False, default="dev")
    base_url = Column(String(500), nullable=True)

    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)
