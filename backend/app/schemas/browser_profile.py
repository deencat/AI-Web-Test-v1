"""
Browser Profile Schemas
Created: February 3, 2026
Purpose: Pydantic schemas for browser profile API operations
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class BrowserProfileBase(BaseModel):
    """Base schema for browser profile"""
    profile_name: str = Field(..., min_length=1, max_length=100, description="Human-readable profile name")
    os_type: str = Field(..., description="Operating system: windows, linux, or macos")
    browser_type: str = Field(default="chromium", description="Browser type: chromium, firefox, or webkit")
    description: Optional[str] = Field(None, description="Optional profile description")

    @validator('os_type')
    def validate_os_type(cls, v):
        allowed = ['windows', 'linux', 'macos']
        if v.lower() not in allowed:
            raise ValueError(f"os_type must be one of: {', '.join(allowed)}")
        return v.lower()

    @validator('browser_type')
    def validate_browser_type(cls, v):
        allowed = ['chromium', 'firefox', 'webkit']
        if v.lower() not in allowed:
            raise ValueError(f"browser_type must be one of: {', '.join(allowed)}")
        return v.lower()


class BrowserProfileCreate(BrowserProfileBase):
    """Schema for creating a new browser profile"""
    http_username: Optional[str] = Field(None, max_length=255, description="Optional HTTP Basic Auth username")
    http_password: Optional[str] = Field(None, max_length=255, description="Optional HTTP Basic Auth password")


class BrowserProfileUpdate(BaseModel):
    """Schema for updating an existing browser profile"""
    profile_name: Optional[str] = Field(None, min_length=1, max_length=100)
    os_type: Optional[str] = None
    browser_type: Optional[str] = None
    description: Optional[str] = None
    http_username: Optional[str] = Field(None, max_length=255, description="HTTP Basic Auth username")
    http_password: Optional[str] = Field(None, max_length=255, description="HTTP Basic Auth password")
    clear_http_credentials: Optional[bool] = Field(
        default=False,
        description="If true, clears stored HTTP credentials"
    )

    @validator('os_type')
    def validate_os_type(cls, v):
        if v is not None:
            allowed = ['windows', 'linux', 'macos']
            if v.lower() not in allowed:
                raise ValueError(f"os_type must be one of: {', '.join(allowed)}")
            return v.lower()
        return v

    @validator('browser_type')
    def validate_browser_type(cls, v):
        if v is not None:
            allowed = ['chromium', 'firefox', 'webkit']
            if v.lower() not in allowed:
                raise ValueError(f"browser_type must be one of: {', '.join(allowed)}")
            return v.lower()
        return v


class BrowserProfileResponse(BrowserProfileBase):
    """Schema for browser profile API response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime] = None
    has_http_credentials: bool = Field(False, description="Indicates if HTTP credentials are configured")
    http_username: Optional[str] = Field(None, description="Configured HTTP Basic Auth username")

    class Config:
        from_attributes = True


class BrowserProfileListResponse(BaseModel):
    """Schema for list of browser profiles"""
    profiles: List[BrowserProfileResponse]
    total: int


class BrowserProfileExportRequest(BaseModel):
    """Schema for requesting profile export after manual login"""
    session_id: str = Field(..., description="Debug session ID from manual login")


class BrowserProfileExportResponse(BaseModel):
    """Schema for profile export response"""
    success: bool
    message: str
    profile_id: int
    file_size_bytes: int
    last_sync_at: datetime
