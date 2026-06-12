"""Agent Observatory schemas (HF-6)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HermesTraceEventResponse(BaseModel):
    id: int
    event_type: str
    profile: Optional[str] = None
    parent_profile: Optional[str] = None
    message: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    payload_full: Optional[Dict[str, Any]] = None
    llm_turns: Optional[List[Dict[str, Any]]] = None
    hermes_session_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HermesTraceResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    hermes_session_ids: List[str] = Field(default_factory=list)
    events: List[HermesTraceEventResponse]


class HermesSessionResponse(BaseModel):
    hermes_session_id: str
    job_ids: List[str] = Field(default_factory=list)
    events: List[HermesTraceEventResponse]
    node_log_hint: str = "~/.hermes/logs/ (Node 1 — see ops runbook)"
