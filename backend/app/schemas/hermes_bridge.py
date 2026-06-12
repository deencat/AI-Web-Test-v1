"""Schemas for Hermes Bridge event ingestion (HF-6.2)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HermesBridgeEventCreate(BaseModel):
    job_id: str
    event_type: str = Field(
        ...,
        examples=["delegate_complete", "job_started", "job_complete"],
    )
    hermes_session_id: Optional[str] = None
    profile: Optional[str] = None
    parent_profile: Optional[str] = None
    message: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    payload_full: Optional[Dict[str, Any]] = None
    llm_turns: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[datetime] = None


class HermesBridgeEventResponse(BaseModel):
    event_id: int
    job_id: str
    event_type: str
    created_at: datetime
