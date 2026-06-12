"""Agent Observatory access audit log (HF-6)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db.base import Base


class ObservatoryAccessLog(Base):
    __tablename__ = "observatory_access_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(String(36), nullable=True, index=True)
    hermes_session_id = Column(String(128), nullable=True, index=True)
    resource = Column(String(128), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
