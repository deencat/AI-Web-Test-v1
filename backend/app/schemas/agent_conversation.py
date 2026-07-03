"""Schemas for persisted Agent Console conversations."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AgentConversationMessageResponse(BaseModel):
    id: int
    role: str
    text: str
    job_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentConversationResponse(BaseModel):
    conversation_id: str
    project: Optional[str] = None
    hermes_resume_session: Optional[str] = None
    is_active: bool = True
    messages: List[AgentConversationMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentConversationListItem(BaseModel):
    conversation_id: str
    preview: Optional[str] = None
    message_count: int = 0
    is_active: bool = False
    updated_at: datetime
    created_at: datetime


class AgentConversationListResponse(BaseModel):
    items: List[AgentConversationListItem] = Field(default_factory=list)
