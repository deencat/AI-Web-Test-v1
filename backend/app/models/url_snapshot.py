"""URL snapshot model for Loop C change detection (HF-4)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON

from app.db.base import Base


class UrlSnapshot(Base):
    __tablename__ = "url_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, index=True)
    url_hash = Column(String(64), nullable=False, index=True)
    page_title = Column(String(512), nullable=True)
    html_summary = Column(Text, nullable=True)
    element_fingerprint = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=True)
    capture_meta = Column(JSON, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
