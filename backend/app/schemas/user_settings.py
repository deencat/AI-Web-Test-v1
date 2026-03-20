"""Pydantic schemas for user settings."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ModelOption(BaseModel):
    """A single model entry with metadata for free/paid grouping in the UI."""

    id: str = Field(..., description="Model identifier (e.g. 'google/gemini-2.0-flash-exp:free')")
    display_name: str = Field(..., description="Human-readable label shown in dropdowns")
    is_free: bool = Field(..., description="True if the model is $0/M input and $0/M output")


class UserSettingBase(BaseModel):
    """Base schema for user settings."""
    # Test Generation Configuration
    generation_provider: str = Field(..., description="AI provider for test generation (google, cerebras, openrouter, azure)")
    generation_model: str = Field(..., description="AI model for test generation")
    generation_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation (0.0-2.0)")
    generation_max_tokens: int = Field(default=4096, ge=100, le=32000, description="Max tokens for generation")
    
    # Test Execution Configuration
    execution_provider: str = Field(..., description="AI provider for test execution (google, cerebras, openrouter, azure)")
    execution_model: str = Field(..., description="AI model for test execution")
    execution_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for execution (0.0-2.0)")
    execution_max_tokens: int = Field(default=4096, ge=100, le=32000, description="Max tokens for execution")
    
    # Stagehand Provider Configuration (Sprint 5: Dual Stagehand Provider System)
    stagehand_provider: str = Field(default="python", description="Stagehand implementation to use (python, typescript)")

    # Per-Agent Model Overrides (Sprint 10.6: Per-Agent Model Provider & Model Selection)
    # Optional — None means "use Azure default (ChatGPT-UAT)"
    observation_provider: Optional[str] = Field(default=None, description="LLM provider for ObservationAgent (overrides Azure default)")
    observation_model: Optional[str] = Field(default=None, description="LLM model for ObservationAgent")
    requirements_provider: Optional[str] = Field(default=None, description="LLM provider for RequirementsAgent")
    requirements_model: Optional[str] = Field(default=None, description="LLM model for RequirementsAgent")
    analysis_provider: Optional[str] = Field(default=None, description="LLM provider for AnalysisAgent")
    analysis_model: Optional[str] = Field(default=None, description="LLM model for AnalysisAgent")
    evolution_provider: Optional[str] = Field(default=None, description="LLM provider for EvolutionAgent")
    evolution_model: Optional[str] = Field(default=None, description="LLM model for EvolutionAgent")

    @validator('generation_provider', 'execution_provider')
    def validate_provider(cls, v):
        allowed = ['google', 'cerebras', 'openrouter', 'azure']
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v

    @validator(
        'observation_provider', 'requirements_provider',
        'analysis_provider', 'evolution_provider',
        pre=True, always=True,
    )
    def validate_agent_provider(cls, v):
        """Validate per-agent provider; None is allowed (means use default)."""
        if v is not None:
            allowed = ['google', 'cerebras', 'openrouter', 'azure']
            if v not in allowed:
                raise ValueError(f"Provider must be one of: {allowed}")
        return v

    @validator('stagehand_provider')
    def validate_stagehand_provider(cls, v):
        allowed = ['python', 'typescript']
        if v not in allowed:
            raise ValueError(f"Stagehand provider must be one of: {allowed}")
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

    stagehand_provider: Optional[str] = None

    # Per-Agent Model Overrides (Sprint 10.6)
    observation_provider: Optional[str] = None
    observation_model: Optional[str] = None
    requirements_provider: Optional[str] = None
    requirements_model: Optional[str] = None
    analysis_provider: Optional[str] = None
    analysis_model: Optional[str] = None
    evolution_provider: Optional[str] = None
    evolution_model: Optional[str] = None

    @validator('generation_provider', 'execution_provider')
    def validate_provider(cls, v):
        if v is not None:
            allowed = ['google', 'cerebras', 'openrouter', 'azure']
            if v not in allowed:
                raise ValueError(f"Provider must be one of: {allowed}")
        return v

    @validator(
        'observation_provider', 'requirements_provider',
        'analysis_provider', 'evolution_provider',
        pre=True, always=True,
    )
    def validate_agent_provider(cls, v):
        """Validate per-agent provider; None is allowed (means use default)."""
        if v is not None:
            allowed = ['google', 'cerebras', 'openrouter', 'azure']
            if v not in allowed:
                raise ValueError(f"Provider must be one of: {allowed}")
        return v

    @validator('stagehand_provider')
    def validate_stagehand_provider(cls, v):
        if v is not None:
            allowed = ['python', 'typescript']
            if v not in allowed:
                raise ValueError(f"Stagehand provider must be one of: {allowed}")
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

    name: str = Field(..., description="Provider name (google, cerebras, openrouter, azure)")
    display_name: str = Field(..., description="Display name for UI")
    is_configured: bool = Field(..., description="Whether API key is configured in backend")
    models: list[str] = Field(..., description="Available model IDs for this provider (legacy flat list)")
    recommended_model: Optional[str] = Field(None, description="Recommended model for this provider")
    # Sprint 10.5: rich model list with free/paid metadata; ordered recommended-first.
    # Backwards-compatible addition — old clients still read `models`.
    model_options: list[ModelOption] = Field(
        default_factory=list,
        description="Rich model list with is_free flag and display names (Sprint 10.5+)",
    )


class AvailableProvidersResponse(BaseModel):
    """Schema for available providers response."""
    providers: list[AvailableProvider]
    default_generation_provider: str
    default_generation_model: str
    default_execution_provider: str
    default_execution_model: str


# Sprint 5: Dual Stagehand Provider System Schemas

class StagehandProviderResponse(BaseModel):
    """Schema for stagehand provider response."""
    provider: str = Field(..., description="Current stagehand provider (python, typescript)")
    available_providers: list[str] = Field(..., description="List of available stagehand providers")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "python",
                "available_providers": ["python", "typescript"]
            }
        }


class StagehandProviderUpdate(BaseModel):
    """Schema for updating stagehand provider."""
    provider: str = Field(..., description="Stagehand provider to switch to (python, typescript)")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['python', 'typescript']
        if v not in allowed:
            raise ValueError(f"Stagehand provider must be one of: {allowed}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "typescript"
            }
        }
