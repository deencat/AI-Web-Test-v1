"""Singleton system-wide settings (override server .env when set)."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class SystemSettings(Base):
    """One-row table (id=1) for deployment overrides editable from Settings UI."""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    # When set, overrides HERMES_BRIDGE_URL from .env for Agent Console routing.
    factory_orchestrator_bridge_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
