"""
Pydantic schemas for Execution Settings
Sprint 5.5: 3-Tier Execution Engine configuration
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


# Fallback strategy types
FallbackStrategy = Literal["option_a", "option_b", "option_c"]


class ExecutionSettingsBase(BaseModel):
    """Base schema for execution settings"""
    fallback_strategy: FallbackStrategy = Field(
        default="option_c",
        description="Fallback strategy: option_a (Tier1→Tier2), option_b (Tier1→Tier3), option_c (Tier1→Tier2→Tier3)"
    )
    max_retry_per_tier: int = Field(default=1, ge=0, le=3, description="Maximum retries per tier (0-3)")
    timeout_per_tier_seconds: int = Field(default=30, ge=10, le=120, description="Timeout per tier in seconds")
    track_fallback_reasons: bool = Field(default=True, description="Track reasons for tier fallback")
    track_strategy_effectiveness: bool = Field(default=True, description="Track strategy performance metrics")


class ExecutionSettingsCreate(ExecutionSettingsBase):
    """Schema for creating execution settings"""
    user_id: int


class ExecutionSettingsUpdate(BaseModel):
    """Schema for updating execution settings"""
    fallback_strategy: Optional[FallbackStrategy] = None
    max_retry_per_tier: Optional[int] = Field(None, ge=0, le=3)
    timeout_per_tier_seconds: Optional[int] = Field(None, ge=10, le=120)
    track_fallback_reasons: Optional[bool] = None
    track_strategy_effectiveness: Optional[bool] = None


class ExecutionSettings(ExecutionSettingsBase):
    """Schema for execution settings response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExecutionStrategyInfo(BaseModel):
    """Information about a fallback strategy"""
    name: str
    display_name: str
    description: str
    success_rate_min: int
    success_rate_max: int
    cost_level: Literal["low", "medium", "high"]
    speed_level: Literal["fast", "medium", "slow"]
    performance_level: Literal["high", "medium", "low"]  # Frontend expects this
    recommended: bool
    tier_flow: list[int]  # e.g., [1, 2] or [1, 2, 3]
    fallback_chain: list[str]  # e.g., ["Tier 1", "Tier 2"]
    recommended_for: str  # Description of ideal use cases
    use_cases: list[str]
    pros: list[str]  # Advantages of this strategy
    cons: list[str]  # Disadvantages of this strategy


class TierDistributionStats(BaseModel):
    """Statistics for tier distribution"""
    total_executions: int
    tier1_success: int
    tier1_failure: int
    tier2_success: int
    tier2_failure: int
    tier3_success: int
    tier3_failure: int
    overall_success_rate: float
    tier1_success_rate: float
    tier2_success_rate: float
    tier3_success_rate: float
    avg_tier1_time_ms: float
    avg_tier2_time_ms: float
    avg_tier3_time_ms: float


class StrategyEffectivenessStats(BaseModel):
    """Statistics for strategy effectiveness by option"""
    strategy: FallbackStrategy
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time_ms: float
    tier1_percentage: float
    tier2_percentage: float
    tier3_percentage: float
    cost_estimate: str  # "low", "medium", "high"


# XPath Cache Schemas
class XPathCacheBase(BaseModel):
    """Base schema for XPath cache"""
    page_url: str
    instruction: str
    xpath: str
    selector_type: str = "xpath"
    page_title: Optional[str] = None
    element_text: Optional[str] = None
    metadata: Optional[str] = None


class XPathCacheCreate(XPathCacheBase):
    """Schema for creating XPath cache entry"""
    cache_key: str
    extraction_time_ms: Optional[float] = None


class XPathCacheUpdate(BaseModel):
    """Schema for updating XPath cache entry"""
    xpath: Optional[str] = None
    is_valid: Optional[bool] = None
    validation_failures: Optional[int] = None
    last_validated: Optional[datetime] = None


class XPathCache(XPathCacheBase):
    """Schema for XPath cache response"""
    id: int
    cache_key: str
    last_validated: Optional[datetime] = None
    validation_failures: int
    is_valid: bool
    hit_count: int
    extraction_time_ms: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Tier Execution Log Schemas
class TierExecutionLogCreate(BaseModel):
    """Schema for creating tier execution log"""
    execution_id: int
    step_index: int
    fallback_strategy: FallbackStrategy
    final_tier: int
    success: bool
    tiers_attempted: str  # JSON string like "[1, 2]"
    total_execution_time_ms: float
    tier1_time_ms: Optional[float] = None
    tier2_time_ms: Optional[float] = None
    tier3_time_ms: Optional[float] = None
    tier1_error: Optional[str] = None
    tier2_error: Optional[str] = None
    tier3_error: Optional[str] = None


class TierExecutionLog(BaseModel):
    """Schema for tier execution log response"""
    id: int
    execution_id: int
    step_index: int
    fallback_strategy: FallbackStrategy
    final_tier: int
    success: bool
    tiers_attempted: str
    total_execution_time_ms: float
    tier1_time_ms: Optional[float] = None
    tier2_time_ms: Optional[float] = None
    tier3_time_ms: Optional[float] = None
    tier1_error: Optional[str] = None
    tier2_error: Optional[str] = None
    tier3_error: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
