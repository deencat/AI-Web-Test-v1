"""Pydantic schemas for factory jobs (HF-1)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FactoryJobCreate(BaseModel):
    job_type: str = Field(..., examples=["run_regression", "full_cycle"])
    project: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class FactoryJobEventResponse(BaseModel):
    id: int
    event_type: str
    profile: Optional[str] = None
    message: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    llm_turns: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FactoryJobResponse(BaseModel):
    job_id: str
    job_type: str
    project: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    orchestrator_reply: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    events: List[FactoryJobEventResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class FactoryJobCreatedResponse(BaseModel):
    job_id: str
    status: str


class AgentChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentChatResponse(BaseModel):
    job_id: str
    conversation_id: Optional[str] = None
    reply: str
