"""Pydantic schemas for test case API."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.models.test_case import TestType, Priority, TestStatus


# Base schema with common fields
class TestCaseBase(BaseModel):
    """Base test case schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Test case title")
    description: str = Field(..., min_length=1, description="Test case description")
    test_type: TestType = Field(..., description="Type of test (e2e, unit, integration, api)")
    priority: Priority = Field(default=Priority.MEDIUM, description="Test priority level")
    steps: List[str | Dict[str, Any]] = Field(
        ..., 
        min_items=1, 
        description="""List of test steps (strings or step objects). 
        Step objects can include:
        - action: 'click', 'fill', 'navigate', 'verify', 'upload_file', etc.
        - selector: CSS/XPath selector for element
        - value: Text value for fill actions
        - file_path: Absolute file path for upload_file actions (e.g., '/app/test_files/hkid_sample.pdf')
        - instruction: Natural language instruction for AI execution
        - expected: Expected value for verify actions
        """
    )
    expected_result: str = Field(..., min_length=1, description="Expected test result")
    preconditions: Optional[str] = Field(None, description="Test preconditions")
    test_data: Optional[Dict[str, Any]] = Field(None, description="Optional test data as JSON")
    
    # Day 7 Integration fields
    category_id: Optional[int] = Field(None, description="Knowledge base category ID")
    tags: Optional[List[str]] = Field(None, description="Test tags for categorization")
    test_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (template_id, scenario_id, etc.)")


# Schema for creating a test case
class TestCaseCreate(TestCaseBase):
    """Schema for creating a new test case."""
    status: TestStatus = Field(default=TestStatus.PENDING, description="Initial test status")
    
    @field_validator('test_data')
    @classmethod
    def validate_test_data_size(cls, v):
        """Validate test_data is not too large (max 10KB)."""
        if v is not None:
            import json
            data_str = json.dumps(v)
            if len(data_str) > 10240:  # 10KB limit
                raise ValueError("test_data cannot exceed 10KB")
        return v


# Schema for updating a test case
class TestCaseUpdate(BaseModel):
    """Schema for updating an existing test case."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    test_type: Optional[TestType] = None
    priority: Optional[Priority] = None
    status: Optional[TestStatus] = None
    steps: Optional[List[str | Dict[str, Any]]] = Field(None, min_items=1)
    expected_result: Optional[str] = Field(None, min_length=1)
    preconditions: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    test_metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('test_data')
    @classmethod
    def validate_test_data_size(cls, v):
        """Validate test_data is not too large (max 10KB)."""
        if v is not None:
            import json
            data_str = json.dumps(v)
            if len(data_str) > 10240:
                raise ValueError("test_data cannot exceed 10KB")
        return v


# Schema for test case in database
class TestCaseInDB(TestCaseBase):
    """Schema representing test case as stored in database."""
    id: int
    status: TestStatus
    created_at: datetime
    updated_at: datetime
    user_id: int
    scenario_id: Optional[int] = None
    template_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Schema for API response
class TestCaseResponse(TestCaseInDB):
    """Schema for test case API response."""
    pass


# Schema for test generation request
class TestGenerationRequest(BaseModel):
    """Schema for test generation API request."""
    requirement: str = Field(..., min_length=10, max_length=2000, description="Requirement or feature to generate tests for")
    test_type: Optional[TestType] = Field(None, description="Type of tests to generate")
    num_tests: int = Field(default=3, ge=1, le=10, description="Number of test cases to generate (1-10)")
    model: Optional[str] = Field(None, description="Optional: Specific model to use for generation")
    
    # KB Integration fields (Sprint 2 Day 11)
    category_id: Optional[int] = Field(
        None, 
        description="KB category ID for context (e.g., 1=System Guide, 2=Product Info). When provided, KB documents from this category will be used as context for test generation."
    )
    use_kb_context: bool = Field(
        True, 
        description="Whether to include KB documents in generation context (default: True if category_id is provided)"
    )
    max_kb_docs: int = Field(
        10, 
        ge=1, 
        le=20, 
        description="Maximum number of KB documents to include in context (1-20)"
    )
    
    @field_validator('requirement')
    @classmethod
    def validate_requirement(cls, v):
        """Validate requirement is meaningful."""
        if len(v.strip()) < 10:
            raise ValueError("Requirement must be at least 10 characters")
        return v.strip()


# Schema for a single generated test case
class GeneratedTestCase(BaseModel):
    """Schema for a generated test case (before saving to DB)."""
    title: str
    description: str
    test_type: str
    priority: str
    steps: List[str]
    expected_result: str
    preconditions: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None


# Schema for test generation response
class TestGenerationResponse(BaseModel):
    """Schema for test generation API response."""
    test_cases: List[GeneratedTestCase]
    metadata: Dict[str, Any] = Field(..., description="Generation metadata (model, tokens, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_cases": [
                    {
                        "title": "Valid login with correct credentials",
                        "description": "Test successful login flow",
                        "test_type": "e2e",
                        "priority": "high",
                        "steps": [
                            "Navigate to login page",
                            "Enter valid username",
                            "Enter valid password",
                            "Click login button"
                        ],
                        "expected_result": "User successfully logged in and redirected to dashboard",
                        "preconditions": "User account exists",
                        "test_data": {
                            "username": "testuser",
                            "password": "Test123!"
                        }
                    }
                ],
                "metadata": {
                    "model": "mistralai/mixtral-8x7b-instruct",
                    "tokens": 268,
                    "num_generated": 1
                }
            }
        }


# Schema for test case list response (with pagination)
class TestCaseListResponse(BaseModel):
    """Schema for paginated test case list."""
    items: List[TestCaseResponse]
    total: int
    skip: int
    limit: int


# Schema for test statistics
class TestStatistics(BaseModel):
    """Schema for test statistics."""
    total: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    by_user: Optional[Dict[int, int]] = None  # user_id: count

