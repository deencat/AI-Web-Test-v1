# Sprint 2 - Day 7: Test Generation Engine Enhancement

**Date**: November 27, 2025  
**Status**: In Progress  
**Goal**: Build intelligent AI-powered test generation engine with templates, multi-step scenarios, and faker integration

---

## 📋 Overview

Day 7 transforms the basic test generation (from Sprint 1) into an advanced, AI-powered test creation system. The engine will support multiple test types (API, Mobile, E2E, Performance), generate multi-step scenarios with dependencies, and use faker for realistic test data.

---

## 🎯 Objectives

1. **Test Template System** - Pre-built templates for common test patterns
2. **Multi-Step Scenario Generator** - AI creates complex test flows
3. **Intelligent Test Data** - Faker integration for realistic data
4. **Validation Engine** - Verify test quality before execution
5. **Batch Generation API** - Create multiple tests efficiently

---

## 🗄️ Database Models

### 1. TestTemplate Model
```python
# backend/app/models/test_template.py
class TestTemplate(Base):
    __tablename__ = "test_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    template_type = Column(String(50))  # api, mobile, e2e, performance
    category_id = Column(Integer, ForeignKey("kb_categories.id"))
    
    # Template structure
    steps_template = Column(JSON)  # Array of step templates
    assertion_template = Column(JSON)  # Expected behavior patterns
    data_requirements = Column(JSON)  # Faker fields needed
    
    # Metadata
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("KBCategory", back_populates="test_templates")
    creator = relationship("User")
    scenarios = relationship("TestScenario", back_populates="template")
```

### 2. TestScenario Model
```python
# backend/app/models/test_scenario.py
class TestScenario(Base):
    __tablename__ = "test_scenarios"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_id = Column(Integer, ForeignKey("test_templates.id"))
    
    # Scenario structure
    steps = Column(JSON)  # Array of {action, target, data, assertion}
    dependencies = Column(JSON)  # Array of step dependency mappings
    test_data = Column(JSON)  # Generated faker data
    expected_results = Column(JSON)  # Expected outcomes
    
    # Execution tracking
    status = Column(String(50), default="draft")  # draft, validated, ready, executed
    validation_errors = Column(JSON)
    execution_count = Column(Integer, default=0)
    last_execution = Column(DateTime)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    template = relationship("TestTemplate", back_populates="scenarios")
    creator = relationship("User")
```

---

## 🔧 Services

### 1. TestTemplateService
```python
# backend/app/services/test_template_service.py

class TestTemplateService:
    """Manage test templates"""
    
    @staticmethod
    def get_templates_by_type(db: Session, template_type: str) -> List[TestTemplate]:
        """Get all templates of a specific type"""
        
    @staticmethod
    def create_template(db: Session, template_data: dict, user_id: int) -> TestTemplate:
        """Create a new test template"""
        
    @staticmethod
    def validate_template_structure(template: dict) -> Tuple[bool, List[str]]:
        """Validate template JSON structure"""
        
    @staticmethod
    def increment_usage(db: Session, template_id: int):
        """Track template usage statistics"""
```

### 2. ScenarioGeneratorService
```python
# backend/app/services/scenario_generator_service.py

class ScenarioGeneratorService:
    """AI-powered test scenario generation"""
    
    @staticmethod
    async def generate_from_template(
        db: Session,
        template_id: int,
        context: dict,
        use_ai: bool = True
    ) -> TestScenario:
        """Generate scenario from template with AI enhancement"""
        
    @staticmethod
    def generate_faker_data(data_requirements: dict) -> dict:
        """Generate realistic test data using Faker"""
        # Examples:
        # - user.email, user.name, user.phone
        # - address.street, address.city
        # - product.name, product.price
        # - lorem.paragraph, lorem.sentence
        
    @staticmethod
    def expand_multi_step_scenario(
        template_steps: List[dict],
        context: dict
    ) -> List[dict]:
        """Expand template steps into detailed scenario"""
        
    @staticmethod
    def validate_dependencies(steps: List[dict]) -> Tuple[bool, List[str]]:
        """Check for circular dependencies and missing prerequisites"""
```

### 3. TestValidationService
```python
# backend/app/services/test_validation_service.py

class TestValidationService:
    """Validate test scenarios before execution"""
    
    @staticmethod
    def validate_scenario(scenario: TestScenario) -> Tuple[bool, List[str]]:
        """Comprehensive scenario validation"""
        # Check:
        # - All required fields present
        # - Valid step structure
        # - No dependency cycles
        # - Assertion patterns valid
        # - Test data matches requirements
        
    @staticmethod
    def check_step_completeness(step: dict) -> List[str]:
        """Validate individual step structure"""
        
    @staticmethod
    def suggest_improvements(scenario: TestScenario) -> List[str]:
        """AI suggestions to improve test coverage"""
```

---

## 📊 Schemas

### Template Schemas
```python
# backend/app/schemas/test_template.py

class TestTemplateBase(BaseModel):
    name: str
    description: Optional[str]
    template_type: str  # api, mobile, e2e, performance
    category_id: int
    steps_template: List[dict]
    assertion_template: dict
    data_requirements: Optional[dict]

class TestTemplateCreate(TestTemplateBase):
    pass

class TestTemplateUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    steps_template: Optional[List[dict]]
    assertion_template: Optional[dict]
    is_active: Optional[bool]

class TestTemplateResponse(TestTemplateBase):
    id: int
    is_active: bool
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

### Scenario Schemas
```python
# backend/app/schemas/test_scenario.py

class TestScenarioBase(BaseModel):
    name: str
    description: Optional[str]
    template_id: int
    steps: List[dict]
    dependencies: Optional[List[dict]]
    test_data: Optional[dict]
    expected_results: Optional[dict]

class ScenarioGenerationRequest(BaseModel):
    template_id: int
    context: dict  # User-provided context for AI generation
    use_ai: bool = True
    generate_data: bool = True

class ScenarioValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class TestScenarioResponse(TestScenarioBase):
    id: int
    status: str
    validation_errors: Optional[List[str]]
    execution_count: int
    last_execution: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Batch Generation Schemas
```python
class BatchGenerationRequest(BaseModel):
    template_ids: List[int]
    base_context: dict
    variations: List[dict]  # Generate multiple variations
    
class BatchGenerationResponse(BaseModel):
    total_requested: int
    generated: int
    failed: int
    scenarios: List[TestScenarioResponse]
    errors: List[dict]
```

---

## 🛣️ API Endpoints

### Test Template Endpoints
```python
# backend/app/api/v1/endpoints/test_templates.py

# Template Management
POST   /api/v1/test-templates              # Create new template
GET    /api/v1/test-templates              # List all templates (filter by type)
GET    /api/v1/test-templates/{id}         # Get template details
PUT    /api/v1/test-templates/{id}         # Update template
DELETE /api/v1/test-templates/{id}         # Delete template
POST   /api/v1/test-templates/{id}/clone   # Clone existing template

# Template by Type
GET    /api/v1/test-templates/type/{type}  # Get templates by type (api, mobile, etc)

# Template Statistics
GET    /api/v1/test-templates/{id}/stats   # Usage stats and success rate
```

### Test Scenario Endpoints
```python
# backend/app/api/v1/endpoints/test_scenarios.py

# Scenario Generation
POST   /api/v1/scenarios/generate           # Generate from template
POST   /api/v1/scenarios/batch-generate     # Batch generation
POST   /api/v1/scenarios                    # Create manual scenario

# Scenario Management
GET    /api/v1/scenarios                    # List scenarios (filter by status)
GET    /api/v1/scenarios/{id}               # Get scenario details
PUT    /api/v1/scenarios/{id}               # Update scenario
DELETE /api/v1/scenarios/{id}               # Delete scenario

# Validation
POST   /api/v1/scenarios/{id}/validate      # Validate scenario
POST   /api/v1/scenarios/validate           # Validate scenario JSON

# Data Generation
POST   /api/v1/scenarios/generate-data      # Generate faker data
GET    /api/v1/scenarios/faker-fields       # List available faker fields
```

---

## 🧪 Built-in Templates

### API Test Template
```json
{
  "name": "REST API Endpoint Test",
  "type": "api",
  "steps_template": [
    {
      "action": "request",
      "method": "${method}",
      "endpoint": "${endpoint}",
      "headers": "${headers}",
      "body": "${request_body}"
    },
    {
      "action": "assert_response",
      "status_code": "${expected_status}",
      "response_schema": "${schema}"
    }
  ],
  "data_requirements": {
    "headers": ["authorization_token"],
    "request_body": ["user.email", "user.name"]
  }
}
```

### E2E Login Flow Template
```json
{
  "name": "User Login Flow",
  "type": "e2e",
  "steps_template": [
    {
      "action": "navigate",
      "url": "${base_url}/login"
    },
    {
      "action": "fill_field",
      "selector": "${email_selector}",
      "value": "${test_email}"
    },
    {
      "action": "fill_field",
      "selector": "${password_selector}",
      "value": "${test_password}"
    },
    {
      "action": "click",
      "selector": "${login_button}"
    },
    {
      "action": "wait_for_navigation",
      "expected_url": "${dashboard_url}"
    },
    {
      "action": "assert_element",
      "selector": "${success_indicator}",
      "visible": true
    }
  ],
  "data_requirements": {
    "credentials": ["user.email", "user.password"]
  }
}
```

---

## 🔄 Implementation Steps

### Phase 1: Database & Models (30 min)
1. ✅ Create `test_templates.py` model
2. ✅ Create `test_scenarios.py` model
3. ✅ Update model imports in `__init__.py`
4. ✅ Auto-create tables on server restart

### Phase 2: Services (60 min)
1. ✅ Install faker: `pip install faker`
2. ✅ Build TestTemplateService
3. ✅ Build ScenarioGeneratorService with faker
4. ✅ Build TestValidationService

### Phase 3: Schemas (30 min)
1. ✅ Create test_template schemas
2. ✅ Create test_scenario schemas
3. ✅ Create batch generation schemas

### Phase 4: API Endpoints (60 min)
1. ✅ Template management endpoints
2. ✅ Scenario generation endpoints
3. ✅ Validation endpoints
4. ✅ Register routes in main.py

### Phase 5: Seed Built-in Templates (20 min)
1. ✅ Create startup script to seed templates
2. ✅ Add API, E2E, Mobile, Performance templates

### Phase 6: Testing (30 min)
1. ✅ Test template CRUD via Swagger
2. ✅ Test scenario generation with AI
3. ✅ Test faker data generation
4. ✅ Test batch generation

---

## 📈 Success Metrics

- ✅ 4+ built-in templates (API, E2E, Mobile, Performance)
- ✅ AI-powered scenario generation working
- ✅ Faker integration generating realistic data
- ✅ Validation engine catching errors
- ✅ Batch generation creating 10+ scenarios
- ✅ All endpoints documented in Swagger
- ✅ Server restart maintains template data

---

## 🚀 Next Steps (Day 8)

After Day 7 completion:
- **Day 8**: Test Execution Framework (Playwright + Stagehand + Celery)
- **Day 9**: Hybrid Testing Framework (Orchestration layer)
- **Day 10**: Backend Hardening (Security, performance, monitoring)

---

## 📝 Notes

- Keep templates flexible with variable substitution
- AI enhancement optional (fallback to template-only)
- Faker provides 50+ data types (names, addresses, emails, etc)
- Validation prevents bad tests from executing
- Track template success rates for recommendations
