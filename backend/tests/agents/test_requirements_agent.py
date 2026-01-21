"""
Unit tests for RequirementsAgent
Tests scenario generation, test data extraction, coverage metrics
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.requirements_agent import (
    RequirementsAgent, 
    Scenario, 
    ScenarioPriority, 
    ScenarioType
)
from agents.base_agent import TaskContext, AgentCapability


@pytest.fixture
def requirements_agent():
    """Create RequirementsAgent instance"""
    # Mock message queue
    class MockMessageQueue:
        async def publish(self, *args, **kwargs):
            pass
        async def subscribe(self, *args, **kwargs):
            pass
    
    config = {
        "use_llm": False  # Disable LLM for unit tests
    }
    return RequirementsAgent(
        agent_id="test_requirements_agent",
        agent_type="requirements",
        priority=5,
        message_queue=MockMessageQueue(),
        config=config
    )


@pytest.fixture
def sample_ui_elements():
    """Sample UI elements from observation"""
    return [
        {
            "type": "button",
            "selector": "#header-login-btn",
            "text": "Login",
            "actions": ["click"]
        },
        {
            "type": "input",
            "selector": "#login-form-email",
            "input_type": "email",
            "name": "email",
            "required": True,
            "placeholder": "Enter your email"
        },
        {
            "type": "input",
            "selector": "#login-form-password",
            "input_type": "password",
            "name": "password",
            "required": True
        },
        {
            "type": "link",
            "selector": "#nav-pricing",
            "text": "Pricing",
            "href": "/pricing"
        },
        {
            "type": "form",
            "selector": "#login-form",
            "action": "/login",
            "method": "POST"
        }
    ]


@pytest.fixture
def sample_page_structure():
    """Sample page structure"""
    return {
        "url": "https://example.com/login",
        "title": "Login Page",
        "forms": ["#login-form"],
        "navigation": ["#nav-pricing", "#nav-features"]
    }


@pytest.fixture
def sample_page_context():
    """Sample page context"""
    return {
        "framework": "React",
        "page_type": "login",
        "complexity": "simple"
    }


class TestRequirementsAgentCapabilities:
    """Test agent capabilities and initialization"""
    
    def test_agent_capabilities(self, requirements_agent):
        """Test agent declares correct capabilities"""
        capabilities = requirements_agent.capabilities
        
        assert len(capabilities) == 3
        assert any(c.name == "requirement_extraction" for c in capabilities)
        assert any(c.name == "scenario_generation" for c in capabilities)
        assert any(c.name == "test_data_extraction" for c in capabilities)
    
    @pytest.mark.asyncio
    async def test_can_handle_valid_task(self, requirements_agent, sample_ui_elements):
        """Test agent can handle valid requirement extraction task"""
        task = TaskContext(
            conversation_id="test-conv",
            task_id="test-001",
            task_type="requirement_extraction",
            payload={"ui_elements": sample_ui_elements}
        )
        
        can_handle, confidence = await requirements_agent.can_handle(task)
        
        assert can_handle is True
        assert confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_cannot_handle_invalid_task(self, requirements_agent):
        """Test agent rejects invalid task type"""
        task = TaskContext(
            conversation_id="test-conv",
            task_id="test-002",
            task_type="invalid_task_type",
            payload={}
        )
        
        can_handle, confidence = await requirements_agent.can_handle(task)
        
        assert can_handle is False
        assert confidence == 0.0


class TestElementGrouping:
    """Test UI element grouping by section"""
    
    def test_group_elements_by_page(self, requirements_agent, sample_ui_elements, sample_page_structure):
        """Test element grouping creates correct sections"""
        groups = requirements_agent._group_elements_by_page(sample_ui_elements, sample_page_structure)
        
        assert len(groups) > 0
        assert "header" in str(groups) or "login-form" in str(groups) or "nav" in str(groups)
    
    def test_extract_section_from_selector(self, requirements_agent):
        """Test section extraction from CSS selectors"""
        assert "header" in requirements_agent._extract_section_from_selector("#header-login-btn")
        assert "nav" in requirements_agent._extract_section_from_selector(".nav-menu")
        assert "form" in requirements_agent._extract_section_from_selector("#login-form")
        assert "footer" in requirements_agent._extract_section_from_selector(".footer-links")


class TestUserJourneyMapping:
    """Test user journey identification"""
    
    def test_map_login_journey(self, requirements_agent, sample_page_context):
        """Test login page journey mapping"""
        element_groups = {"header": [], "form": []}
        page_context = {"page_type": "login"}
        
        journeys = requirements_agent._map_user_journeys(element_groups, page_context)
        
        assert len(journeys) > 0
        assert any("Login" in j["journey_name"] for j in journeys)
        assert any(j["priority"] == ScenarioPriority.CRITICAL for j in journeys)
    
    def test_map_registration_journey(self, requirements_agent):
        """Test registration page journey mapping"""
        page_context = {"page_type": "registration"}
        
        journeys = requirements_agent._map_user_journeys({}, page_context)
        
        assert len(journeys) > 0
        assert any("Registration" in j["journey_name"] for j in journeys)
    
    def test_map_checkout_journey(self, requirements_agent):
        """Test checkout page journey mapping"""
        page_context = {"page_type": "checkout"}
        
        journeys = requirements_agent._map_user_journeys({}, page_context)
        
        assert len(journeys) > 0
        assert any("Purchase" in j["journey_name"] for j in journeys)
    
    def test_map_generic_journey(self, requirements_agent):
        """Test generic page journey mapping"""
        page_context = {"page_type": "homepage"}
        
        journeys = requirements_agent._map_user_journeys({}, page_context)
        
        assert len(journeys) > 0
        assert any("Navigation" in j["journey_name"] for j in journeys)


class TestAccessibilityScenarios:
    """Test WCAG 2.1 accessibility scenario generation"""
    
    def test_generate_accessibility_scenarios(self, requirements_agent, sample_ui_elements):
        """Test accessibility scenario generation"""
        scenarios = requirements_agent._generate_accessibility_scenarios(sample_ui_elements)
        
        assert len(scenarios) == 4  # REQ-A-001 to REQ-A-004
        
        # Check for keyboard navigation scenario
        assert any("keyboard" in s.title.lower() for s in scenarios)
        
        # Check for screen reader scenario
        assert any("screen reader" in s.title.lower() for s in scenarios)
        
        # Check for color contrast scenario
        assert any("contrast" in s.title.lower() for s in scenarios)
        
        # Check for text resize scenario
        assert any("resize" in s.title.lower() or "zoom" in s.title.lower() for s in scenarios)
    
    def test_accessibility_scenario_properties(self, requirements_agent, sample_ui_elements):
        """Test accessibility scenarios have correct properties"""
        scenarios = requirements_agent._generate_accessibility_scenarios(sample_ui_elements)
        
        for scenario in scenarios:
            assert scenario.scenario_type == ScenarioType.ACCESSIBILITY
            assert "wcag-2.1" in scenario.tags
            assert "a11y" in scenario.tags
            assert scenario.confidence == 0.90
            assert scenario.priority in [ScenarioPriority.HIGH, ScenarioPriority.MEDIUM]


class TestSecurityScenarios:
    """Test OWASP Top 10 security scenario generation"""
    
    def test_generate_security_scenarios_with_forms(self, requirements_agent, sample_ui_elements, sample_page_context):
        """Test security scenarios generated when forms present"""
        scenarios = requirements_agent._generate_security_scenarios(sample_ui_elements, sample_page_context)
        
        assert len(scenarios) == 4  # REQ-S-001 to REQ-S-004
        
        # Check for XSS scenario
        assert any("xss" in s.title.lower() for s in scenarios)
        
        # Check for SQL injection scenario
        assert any("sql injection" in s.title.lower() for s in scenarios)
        
        # Check for CSRF scenario
        assert any("csrf" in s.title.lower() for s in scenarios)
        
        # Check for input validation scenario
        assert any("validation" in s.title.lower() for s in scenarios)
    
    def test_no_security_scenarios_without_forms(self, requirements_agent):
        """Test no security scenarios when no forms/inputs present"""
        ui_elements = [
            {"type": "button", "text": "Read More"},
            {"type": "link", "text": "About Us"}
        ]
        
        scenarios = requirements_agent._generate_security_scenarios(ui_elements, {})
        
        assert len(scenarios) == 0
    
    def test_security_scenario_properties(self, requirements_agent, sample_ui_elements, sample_page_context):
        """Test security scenarios have correct properties"""
        scenarios = requirements_agent._generate_security_scenarios(sample_ui_elements, sample_page_context)
        
        for scenario in scenarios:
            assert scenario.scenario_type == ScenarioType.SECURITY
            assert "owasp" in scenario.tags or "security" in scenario.tags
            assert scenario.confidence == 0.85
            assert scenario.priority in [ScenarioPriority.CRITICAL, ScenarioPriority.HIGH]


class TestEdgeCaseScenarios:
    """Test edge case scenario generation"""
    
    def test_generate_edge_case_scenarios(self, requirements_agent, sample_ui_elements):
        """Test edge case scenario generation"""
        scenarios = requirements_agent._generate_edge_case_scenarios(sample_ui_elements)
        
        assert len(scenarios) > 0
        
        # Check scenarios reference input fields
        for scenario in scenarios:
            assert scenario.scenario_type == ScenarioType.EDGE_CASE
            assert "boundary" in scenario.tags or "validation" in scenario.tags
            assert scenario.confidence == 0.75
    
    def test_edge_case_limited_to_five(self, requirements_agent):
        """Test edge case generation limited to first 5 inputs"""
        ui_elements = [
            {"type": "input", "name": f"field_{i}", "input_type": "text"}
            for i in range(10)
        ]
        
        scenarios = requirements_agent._generate_edge_case_scenarios(ui_elements)
        
        assert len(scenarios) <= 5


class TestTestDataExtraction:
    """Test test data extraction from forms"""
    
    def test_extract_test_data(self, requirements_agent, sample_ui_elements):
        """Test test data extraction"""
        test_data = requirements_agent._extract_test_data(sample_ui_elements)
        
        assert len(test_data) > 0
        
        # Check email field extracted
        email_field = next((f for f in test_data if "email" in f["field_name"]), None)
        assert email_field is not None
        assert email_field["field_type"] == "email"
        assert email_field["required"] is True
        
        # Check password field extracted
        password_field = next((f for f in test_data if "password" in f["field_name"]), None)
        assert password_field is not None
        assert password_field["required"] is True
    
    def test_extract_validation_rules(self, requirements_agent):
        """Test validation rule extraction"""
        element = {
            "type": "input",
            "input_type": "email",
            "required": True,
            "maxlength": 100,
            "minlength": 5
        }
        
        rules = requirements_agent._extract_validation_rules(element)
        
        assert rules["required"] is True
        assert rules["max_length"] == 100
        assert rules["min_length"] == 5
        assert rules["format"] == "email"
    
    def test_generate_example_values_email(self, requirements_agent):
        """Test example value generation for email field"""
        element = {"input_type": "email"}
        
        examples = requirements_agent._generate_example_values(element)
        
        assert len(examples) > 0
        assert any("@" in ex for ex in examples)
        assert any("invalid" in ex.lower() for ex in examples)
    
    def test_generate_example_values_password(self, requirements_agent):
        """Test example value generation for password field"""
        element = {"input_type": "password"}
        
        examples = requirements_agent._generate_example_values(element)
        
        assert len(examples) > 0
        assert any(ex == "" for ex in examples)  # Empty password test


class TestCoverageMetrics:
    """Test coverage calculation"""
    
    def test_calculate_coverage(self, requirements_agent, sample_ui_elements):
        """Test coverage metrics calculation"""
        # Create sample scenarios
        scenarios = [
            Scenario(
                scenario_id="REQ-F-001",
                title="Click Login button",
                given="User on page",
                when="User clicks Login",
                then="Login processed",
                priority=ScenarioPriority.CRITICAL,
                scenario_type=ScenarioType.FUNCTIONAL
            )
        ]
        
        coverage = requirements_agent._calculate_coverage(sample_ui_elements, scenarios)
        
        assert "total_elements" in coverage
        assert "interactive_elements" in coverage
        assert "ui_coverage_percent" in coverage
        assert "scenario_count" in coverage
        assert coverage["total_elements"] == len(sample_ui_elements)
        assert coverage["scenario_count"] == len(scenarios)
    
    def test_calculate_confidence(self, requirements_agent):
        """Test confidence score calculation"""
        scenarios = [
            Scenario("1", "Test 1", "given", "when", "then", 
                        ScenarioPriority.HIGH, ScenarioType.FUNCTIONAL),
            Scenario("2", "Test 2", "given", "when", "then",
                        ScenarioPriority.HIGH, ScenarioType.FUNCTIONAL)
        ]
        scenarios[0].confidence = 0.8
        scenarios[1].confidence = 0.9
        
        confidence = requirements_agent._calculate_confidence(scenarios)
        
        assert confidence == 0.85
    
    def test_get_priority_distribution(self, requirements_agent):
        """Test priority distribution calculation"""
        scenarios = [
            Scenario("1", "Test 1", "given", "when", "then",
                        ScenarioPriority.CRITICAL, ScenarioType.FUNCTIONAL),
            Scenario("2", "Test 2", "given", "when", "then",
                        ScenarioPriority.HIGH, ScenarioType.FUNCTIONAL),
            Scenario("3", "Test 3", "given", "when", "then",
                        ScenarioPriority.HIGH, ScenarioType.FUNCTIONAL),
            Scenario("4", "Test 4", "given", "when", "then",
                        ScenarioPriority.MEDIUM, ScenarioType.FUNCTIONAL)
        ]
        
        distribution = requirements_agent._get_priority_distribution(scenarios)
        
        assert distribution["critical"] == 1
        assert distribution["high"] == 2
        assert distribution["medium"] == 1
        assert distribution["low"] == 0


class TestEndToEndExecution:
    """Test complete task execution"""
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, requirements_agent, sample_ui_elements, 
                                        sample_page_structure, sample_page_context):
        """Test successful task execution"""
        task = TaskContext(
            conversation_id="test-conv",
            task_id="test-e2e-001",
            task_type="requirement_extraction",
            payload={
                "ui_elements": sample_ui_elements,
                "page_structure": sample_page_structure,
                "page_context": sample_page_context
            }
        )
        
        result = await requirements_agent.execute_task(task)
        
        assert result.success is True
        assert result.confidence >= 0.7
        assert "scenarios" in result.result
        assert "test_data" in result.result
        assert "coverage_metrics" in result.result
        assert "quality_indicators" in result.result
        
        # Check scenarios generated
        scenarios = result.result["scenarios"]
        assert len(scenarios) >= 10  # At least functional + accessibility + security
        
        # Check scenario types present
        scenario_types = {s["scenario_type"] for s in scenarios}
        assert "functional" in scenario_types
        assert "accessibility" in scenario_types
        assert "security" in scenario_types
        
        # Check test data extracted
        test_data = result.result["test_data"]
        assert len(test_data) > 0
        
        # Check coverage metrics
        coverage = result.result["coverage_metrics"]
        assert coverage["scenario_count"] == len(scenarios)
        assert coverage["ui_coverage_percent"] >= 0
    
    @pytest.mark.asyncio
    async def test_execute_task_with_minimal_data(self, requirements_agent):
        """Test task execution with minimal UI elements"""
        task = TaskContext(
            conversation_id="test-conv",
            task_id="test-minimal",
            task_type="requirement_extraction",
            payload={
                "ui_elements": [{"type": "button", "text": "Click Me"}],
                "page_structure": {},
                "page_context": {}
            }
        )
        
        result = await requirements_agent.execute_task(task)
        
        assert result.success is True
        assert len(result.result["scenarios"]) > 0


class ScenarioSerialization:
    """Test scenario conversion to dictionary"""
    
    def test_scenario_to_dict(self, requirements_agent):
        """Test scenario serialization"""
        scenario = Scenario(
            scenario_id="REQ-F-001",
            title="Test Login",
            given="User on login page",
            when="User enters credentials and clicks Login",
            then="User is redirected to dashboard",
            priority=ScenarioPriority.CRITICAL,
            scenario_type=ScenarioType.FUNCTIONAL,
            test_data=[{"field": "email", "value": "test@example.com"}],
            tags=["smoke", "critical"]
        )
        scenario.confidence = 0.92
        
        result = requirements_agent._scenario_to_dict(scenario)
        
        assert result["scenario_id"] == "REQ-F-001"
        assert result["title"] == "Test Login"
        assert result["priority"] == "critical"
        assert result["scenario_type"] == "functional"
        assert result["confidence"] == 0.92
        assert "smoke" in result["tags"]


class TestTokenEstimation:
    """Test token usage estimation"""
    
    def test_estimate_token_usage(self, requirements_agent, sample_ui_elements):
        """Test token usage estimation"""
        scenarios = [
            Scenario("1", "Test", "given", "when", "then",
                        ScenarioPriority.HIGH, ScenarioType.FUNCTIONAL)
        ]
        
        tokens = requirements_agent._estimate_token_usage(sample_ui_elements, scenarios)
        
        assert tokens > 0
        assert isinstance(tokens, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
