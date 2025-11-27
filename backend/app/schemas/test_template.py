"""
Test Template Schemas
Pydantic models for test template API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestTemplateBase(BaseModel):
    """Base template schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: str = Field(..., description="Template type (api, mobile, e2e, performance)")
    category_id: Optional[int] = Field(None, description="KB category ID")
    steps_template: List[Dict[str, Any]] = Field(..., description="Array of step templates with ${variables}")
    assertion_template: Dict[str, Any] = Field(..., description="Expected behavior patterns")
    data_requirements: Optional[Dict[str, List[str]]] = Field(None, description="Faker fields needed by category")


class TestTemplateCreate(TestTemplateBase):
    """Schema for creating a new template"""
    pass


class TestTemplateUpdate(BaseModel):
    """Schema for updating a template"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    template_type: Optional[str] = None
    category_id: Optional[int] = None
    steps_template: Optional[List[Dict[str, Any]]] = None
    assertion_template: Optional[Dict[str, Any]] = None
    data_requirements: Optional[Dict[str, List[str]]] = None
    is_active: Optional[bool] = None


class TestTemplateResponse(TestTemplateBase):
    """Schema for template response"""
    id: int
    is_active: bool
    is_system: bool
    usage_count: int
    success_rate: float
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TestTemplateListResponse(BaseModel):
    """Schema for paginated template list"""
    total: int
    templates: List[TestTemplateResponse]


class TestTemplateCloneRequest(BaseModel):
    """Schema for cloning a template"""
    new_name: str = Field(..., min_length=1, max_length=200, description="Name for cloned template")


class TestTemplateStatsResponse(BaseModel):
    """Schema for template statistics"""
    id: int
    name: str
    template_type: str
    usage_count: int
    success_rate: float
    total_scenarios: int
    active_scenarios: int
    
    class Config:
        from_attributes = True
