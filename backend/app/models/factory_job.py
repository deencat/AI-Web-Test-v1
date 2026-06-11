"""Factory job models for Hermes QA Factory control plane (HF-1)."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class FactoryJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FactoryJob(Base):
    __tablename__ = "factory_jobs"

    id = Column(String(36), primary_key=True, index=True)
    job_type = Column(String(64), nullable=False, index=True)
    project = Column(String(128), nullable=True)
    params = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default=FactoryJobStatus.QUEUED.value, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    events = relationship(
        "FactoryJobEvent",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="FactoryJobEvent.id",
    )


class FactoryJobEvent(Base):
    __tablename__ = "factory_job_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("factory_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    profile = Column(String(64), nullable=True)
    message = Column(Text, nullable=True)
    payload_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("FactoryJob", back_populates="events")
