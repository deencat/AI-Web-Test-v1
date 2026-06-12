"""Notification schemas (HF-6)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    notification_type: str
    link: Optional[str] = None
    read: bool
    metadata_json: Optional[Dict[str, Any]] = Field(None, validation_alias="metadata_json")
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread: int


class NotificationMarkRead(BaseModel):
    read: bool = True
