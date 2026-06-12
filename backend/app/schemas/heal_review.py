"""Schemas for heal-from-feedback and heal review queue (HF-5)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealFromFeedbackRequest(BaseModel):
    execution_id: int
    retry_execution: bool = Field(
        True,
        description="For xpath/selector failures, queue a re-run after clearing cache",
    )


class HealFromFeedbackResponse(BaseModel):
    execution_id: int
    action: str
    strategy: str
    test_case_id: Optional[int] = None
    new_execution_id: Optional[int] = None
    workflow_id: Optional[str] = None
    cache_entries_cleared: int = 0
    attempt_count: int = 0
    escalated: bool = False
    heal_review_id: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class HealReviewItemResponse(BaseModel):
    id: int
    execution_id: int
    test_case_id: Optional[int] = None
    reason: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by_user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class HealReviewListResponse(BaseModel):
    items: List[HealReviewItemResponse]
    total: int


class HealReviewPatch(BaseModel):
    status: str = Field(..., description="open | resolved")
