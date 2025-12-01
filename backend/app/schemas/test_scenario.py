"""
Test Scenario Schemas
Pydantic models for test scenario API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestScenarioBase(BaseModel):
    """Base scenario schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    template_id: Optional[int] = Field(None, description="Template ID if generated from template")
    steps: List[Dict[str, Any]] = Field(..., description="Array of test steps")
    dependencies: Optional[List[Dict[str, Any]]] = Field(None, description="Step dependencies")
    test_data: Optional[Dict[str, Any]] = Field(None, description="Test data (generated or manual)")
    expected_results: Optional[Dict[str, Any]] = Field(None, description="Expected outcomes")


class TestScenarioCreate(TestScenarioBase):
    """Schema for creating a new scenario manually"""
    pass


class ScenarioGenerationRequest(BaseModel):
    """Schema for generating scenario from template"""
    template_id: int = Field(..., description="ID of template to use")
    name: Optional[str] = Field(None, description="Custom scenario name")
    description: Optional[str] = Field(None, description="Custom scenario description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context for variable substitution")
    use_ai: bool = Field(True, description="Use AI enhancement (future feature)")
    generate_data: bool = Field(True, description="Generate faker data automatically")


class BatchGenerationRequest(BaseModel):
    """Schema for batch scenario generation"""
    template_ids: List[int] = Field(..., min_items=1, description="Template IDs to generate from")
    base_context: Dict[str, Any] = Field(default_factory=dict, description="Base context for all scenarios")
    variations: List[Dict[str, Any]] = Field(..., min_items=1, description="Context variations for each scenario")


class TestScenarioUpdate(BaseModel):
    """Schema for updating a scenario"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[Dict[str, Any]]] = None
    test_data: Optional[Dict[str, Any]] = None
    expected_results: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class TestScenarioResponse(TestScenarioBase):
    """Schema for scenario response"""
    id: int
    status: str
    validation_errors: Optional[List[str]]
    execution_count: int
    last_execution: Optional[datetime]
    last_execution_status: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TestScenarioListResponse(BaseModel):
    """Schema for paginated scenario list"""
    total: int
    scenarios: List[TestScenarioResponse]


class ScenarioValidationRequest(BaseModel):
    """Schema for validating scenario JSON"""
    name: str = Field(..., min_length=1, max_length=200)
    steps: List[Dict[str, Any]] = Field(..., min_items=1)
    dependencies: Optional[List[Dict[str, Any]]] = None


class ScenarioValidationResponse(BaseModel):
    """Schema for validation results"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class FakerDataRequest(BaseModel):
    """Schema for generating faker data"""
    data_requirements: Dict[str, List[str]] = Field(
        ...,
        description="Faker fields by category",
        example={
            "user": ["email", "name", "phone"],
            "address": ["city", "country"]
        }
    )


class FakerDataResponse(BaseModel):
    """Schema for generated faker data"""
    data: Dict[str, Dict[str, Any]]


class FakerFieldsResponse(BaseModel):
    """Schema for available faker fields"""
    fields: Dict[str, List[str]]
    description: str = "Available faker fields organized by category"


class BatchGenerationResponse(BaseModel):
    """Schema for batch generation results"""
    total_requested: int
    generated: int
    failed: int
    scenarios: List[TestScenarioResponse]
    errors: List[Dict[str, Any]]
