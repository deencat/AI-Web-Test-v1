"""Pydantic schemas for URL snapshots (HF-4)."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class ObserveSnapshotRequest(BaseModel):
    url: HttpUrl
    http_credentials: Optional[dict[str, str]] = None


class UrlSnapshotResponse(BaseModel):
    id: int
    url: str
    url_hash: str
    page_title: Optional[str] = None
    html_summary: Optional[str] = None
    element_fingerprint: str
    status_code: Optional[int] = None
    capture_meta: Optional[dict[str, Any]] = None
    captured_at: datetime

    model_config = {"from_attributes": True}


class SnapshotDiffRequest(BaseModel):
    url: Optional[HttpUrl] = None
    url_hash: Optional[str] = None
    baseline_snapshot_id: Optional[int] = None
    capture_new: bool = True


class SnapshotDiffResponse(BaseModel):
    material_change: bool
    summary: str
    url: str
    url_hash: str
    baseline_snapshot_id: Optional[int] = None
    current_snapshot_id: Optional[int] = None
    baseline_fingerprint: Optional[str] = None
    current_fingerprint: Optional[str] = None
    similarity_score: Optional[float] = None
