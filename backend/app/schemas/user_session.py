"""User Session Schemas for API requests and responses."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserSessionResponse(BaseModel):
    """Response schema for user session."""
    id: int
    session_token: str
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    is_active: bool
    created_at: datetime
    last_activity: datetime
    logged_out_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserSessionListResponse(BaseModel):
    """Response schema for list of user sessions."""
    sessions: list[UserSessionResponse]
    total: int
    active_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [],
                "total": 5,
                "active_count": 2
            }
        }
