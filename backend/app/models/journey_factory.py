"""Journey registry and backlog models (Hermes QA Factory HF-2)."""
import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, UniqueConstraint

from app.db.base import Base


class BacklogStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class JourneyRegistryProject(Base):
    """Per-project registry metadata (ReqIQ id, default crawl config)."""

    __tablename__ = "journey_registry_projects"

    project = Column(String(128), primary_key=True)
    reqiq_project_id = Column(String(64), nullable=True)
    default_env_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class JourneyRegistryEntry(Base):
    """UAT journey definition for autonomous test generation."""

    __tablename__ = "journey_registry_entries"
    __table_args__ = (UniqueConstraint("project", "slug", name="uq_journey_project_slug"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(128), nullable=False, index=True)
    project = Column(String(128), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    feature_url = Column(String(2048), nullable=False)
    tags = Column(JSON, nullable=True)
    capability_keys = Column(JSON, nullable=True)
    reference_test_id = Column(Integer, nullable=True)
    requires_login = Column(Boolean, default=False, nullable=False)
    stop_at_page_hint = Column(String(512), nullable=True)
    extra_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class JourneyBacklogItem(Base):
    """Queued journey for factory worker / planner drain."""

    __tablename__ = "journey_backlog_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(128), nullable=False, index=True)
    journey_slug = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default=BacklogStatus.PENDING.value, index=True)
    priority = Column(Integer, default=0, nullable=False)
    params = Column(JSON, nullable=True)
    factory_job_id = Column(String(36), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
