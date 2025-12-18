"""Pydantic schemas for user settings."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class UserSettingBase(BaseModel):
    """Base schema for user settings."""
    # Test Generation Configuration
    generation_provider: str = Field(..., description="AI provider for test generation (google, cerebras, openrouter)")
    generation_model: str = Field(..., description="AI model for test generation")
    generation_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation (0.0-2.0)")
    generation_max_tokens: int = Field(default=4096, ge=100, le=32000, description="Max tokens for generation")
    
    # Test Execution Configuration
    execution_provider: str = Field(..., description="AI provider for test execution (google, cerebras, openrouter)")
    execution_model: str = Field(..., description="AI model for test execution")
    execution_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for execution (0.0-2.0)")
    execution_max_tokens: int = Field(default=4096, ge=100, le=32000, description="Max tokens for execution")
    
    @validator('generation_provider', 'execution_provider')
    def validate_provider(cls, v):
        allowed = ['google', 'cerebras', 'openrouter']
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v


class UserSettingCreate(UserSettingBase):
    """Schema for creating user settings."""
    pass


class UserSettingUpdate(BaseModel):
    """Schema for updating user settings (all fields optional)."""
    generation_provider: Optional[str] = None
    generation_model: Optional[str] = None
    generation_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    generation_max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    
    execution_provider: Optional[str] = None
    execution_model: Optional[str] = None
    execution_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    execution_max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    
    @validator('generation_provider', 'execution_provider')
    def validate_provider(cls, v):
        if v is not None:
            allowed = ['google', 'cerebras', 'openrouter']
            if v not in allowed:
                raise ValueError(f"Provider must be one of: {allowed}")
        return v


class UserSettingInDB(UserSettingBase):
    """Schema for user settings in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AvailableProvider(BaseModel):
    """Schema for available provider information."""
    name: str = Field(..., description="Provider name (google, cerebras, openrouter)")
    display_name: str = Field(..., description="Display name for UI")
    is_configured: bool = Field(..., description="Whether API key is configured in backend")
    models: list[str] = Field(..., description="Available models for this provider")
    recommended_model: Optional[str] = Field(None, description="Recommended model for this provider")


class AvailableProvidersResponse(BaseModel):
    """Schema for available providers response."""
    providers: list[AvailableProvider]
    default_generation_provider: str
    default_generation_model: str
    default_execution_provider: str
    default_execution_model: str
