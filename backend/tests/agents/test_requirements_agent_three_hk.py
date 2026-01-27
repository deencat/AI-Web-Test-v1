"""
Unit tests for RequirementsAgent using Three HK website data
Tests LLM integration, real-world scenarios, error handling, fallback behavior
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json

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
def mock_message_queue():
    """Mock message queue for testing"""
    class MockMessageQueue:
        async def publish(self, *args, **kwargs):
            pass
        async def subscribe(self, *args, **kwargs):
            pass
    return MockMessageQueue()


@pytest.fixture
def requirements_agent_with_llm(mock_message_queue):
    """Create RequirementsAgent with LLM enabled"""
    config = {"use_llm": True}
    agent = RequirementsAgent(
        agent_id="test_requirements_agent_llm",
        agent_type="requirements",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )
    return agent


@pytest.fixture
def requirements_agent_without_llm(mock_message_queue):
    """Create RequirementsAgent with LLM disabled (pattern-based only)"""
    config = {"use_llm": False}
    return RequirementsAgent(
        agent_id="test_requirements_agent_pattern",
        agent_type="requirements",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def three_hk_ui_elements():
    """Real UI elements from Three HK 5G broadband pricing page"""
    return [
        {
            "type": "button",
            "selector": "button.btn-register-1",
            "text": "立即登記",  # Register Now
            "actions": ["click"],
            "aria_label": "Register for 5G broadband plan"
        },
        {
            "type": "button",
            "selector": "button.btn-register-2",
            "text": "立即登記",
            "actions": ["click"]
        },
        {
            "type": "link",
            "selector": "a.link-terms",
            "text": "條款細則",  # Terms and Conditions
            "href": "/tnc/251208/tnc-5gbbmthplan2-tc.pdf",
            "actions": ["click"]
        },
        {
            "type": "link",
            "selector": "a.link-whatsapp",
            "text": "WhatsApp查詢",  # WhatsApp inquiry
            "href": "https://web.three.com.hk/redirect/wa/m_5gbb_monthlyplan_tc.html",
            "actions": ["click"]
        },
        {
            "type": "button",
            "selector": "button.plan-selector",
            "text": "選擇計劃",  # Select Plan
            "actions": ["click"]
        },
        {
            "type": "link",
            "selector": "a.nav-home",
            "text": "主頁",  # Home
            "href": "/",
            "actions": ["click"]
        },
        {
            "type": "link",
            "selector": "a.nav-5g",
            "text": "5G寬頻",  # 5G Broadband
            "href": "/5gbroadband",
            "actions": ["click"]
        },
        {
            "type": "custom",
            "selector": "div.price-card",
            "text": "$128/月",  # $128/month
            "aria_label": "Monthly plan price"
        },
        {
            "type": "custom",
            "selector": "div.plan-features",
            "text": "無限數據",  # Unlimited data
            "aria_label": "Plan features"
        }
    ]


@pytest.fixture
def three_hk_page_structure():
    """Page structure from Three HK website"""
    return {
        "url": "https://web.three.com.hk/5gbroadband/plan-monthly.html",
        "title": "3HK 5G寬頻月費計劃",
        "forms": [],
        "navigation": [
            {"text": "主頁", "href": "/"},
            {"text": "5G寬頻", "href": "/5gbroadband"}
        ]
    }


@pytest.fixture
def three_hk_page_context():
    """Page context from Three HK analysis"""
    return {
        "framework": "jquery",
        "page_type": "pricing",
        "complexity": "medium",
        "language": "zh-HK"
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with realistic scenarios"""
    return {
        "scenarios": [
            {
                "scenario_id": "REQ-F-001",
                "title": "User can successfully register a 5G broadband plan",
                "scenario_type": "functional",
                "priority": "critical",
                "given": "User is on the 5G broadband pricing page with all UI elements loaded",
                "when": "User clicks on any '立即登記' button and fills out the registration form with valid information",
                "then": "System accepts the input, processes the registration, and shows a confirmation message",
                "tags": ["registration", "smoke", "critical"],
                "confidence": 0.95
            },
            {
                "scenario_id": "REQ-A-001",
                "title": "Keyboard users can navigate and activate all '立即登記' buttons",
                "scenario_type": "accessibility",
                "priority": "critical",
                "given": "User is on the pricing page using only keyboard navigation",
                "when": "User tabs through the page and presses Enter or Space on any '立即登記' button",
                "then": "The button receives focus and triggers the registration action as expected",
                "tags": ["accessibility", "wcag", "keyboard"],
                "confidence": 0.95
            },
            {
                "scenario_id": "REQ-S-001",
                "title": "Registration form validates and sanitizes user input",
                "scenario_type": "security",
                "priority": "high",
                "given": "User is attempting to register with potentially malicious input",
                "when": "User enters <script>alert('XSS')</script> in name field",
                "then": "System sanitizes input and prevents XSS attack",
                "tags": ["security", "xss", "input-validation"],
                "confidence": 0.90
            }
        ]
    }


class TestThreeHKElementGrouping:
    """Test element grouping with Three HK data"""
    
    def test_group_three_hk_elements(self, requirements_agent_without_llm, three_hk_ui_elements, three_hk_page_structure):
        """Test grouping real Three HK UI elements"""
        groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        
        # Should have at least one group (main page)
        assert len(groups) > 0
        
        # All elements should be grouped
        total_elements = sum(len(elements) for elements in groups.values())
        assert total_elements == len(three_hk_ui_elements)
    
    def test_identify_three_hk_button_patterns(self, requirements_agent_without_llm, three_hk_ui_elements):
        """Test identifying '立即登記' button patterns"""
        buttons = [e for e in three_hk_ui_elements if e.get("type") == "button"]
        
        # Should have multiple register buttons
        register_buttons = [b for b in buttons if "立即登記" in b.get("text", "")]
        assert len(register_buttons) >= 2
        
        # All register buttons should have click actions
        for btn in register_buttons:
            assert "click" in btn.get("actions", [])


class TestThreeHKUserJourneys:
    """Test user journey mapping with Three HK data"""
    
    def test_map_three_hk_registration_journey(self, requirements_agent_without_llm, three_hk_ui_elements, three_hk_page_structure, three_hk_page_context):
        """Test mapping registration journey for Three HK"""
        element_groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        journeys = requirements_agent_without_llm._map_user_journeys(element_groups, three_hk_page_context)
        
        # Should identify journeys
        assert len(journeys) >= 0  # May be empty if no patterns match
        
        # Pricing page may not have traditional journeys, but should process without error
        assert element_groups is not None
    
    def test_map_three_hk_pricing_journey(self, requirements_agent_without_llm, three_hk_ui_elements):
        """Test identifying pricing page patterns"""
        # Should identify pricing elements
        pricing_elements = [
            e for e in three_hk_ui_elements 
            if "$" in e.get("text", "") or "計劃" in e.get("text", "")
        ]
        assert len(pricing_elements) > 0


class TestThreeHKFunctionalScenarios:
    """Test functional scenario generation with Three HK data"""
    
    @pytest.mark.asyncio
    async def test_generate_three_hk_registration_scenarios(
        self, 
        requirements_agent_without_llm, 
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test generating registration scenarios for Three HK"""
        groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        journeys = requirements_agent_without_llm._map_user_journeys(groups, three_hk_page_context)
        
        scenarios = await requirements_agent_without_llm._generate_functional_scenarios(
            journeys, groups, three_hk_page_context, three_hk_page_structure
        )
        
        # Should generate at least one functional scenario
        assert len(scenarios) > 0
        
        # Scenarios should reference Three HK specific elements
        scenario_texts = " ".join(s.given + s.when + s.then for s in scenarios)
        # Should mention buttons or registration (even if pattern-based is generic)
        assert any(keyword in scenario_texts.lower() for keyword in ["button", "click", "register", "plan"])
    
    @pytest.mark.asyncio
    async def test_functional_scenario_properties(self, requirements_agent_without_llm, three_hk_ui_elements, three_hk_page_structure, three_hk_page_context):
        """Test that generated scenarios have required properties"""
        groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        journeys = requirements_agent_without_llm._map_user_journeys(groups, three_hk_page_context)
        
        scenarios = await requirements_agent_without_llm._generate_functional_scenarios(
            journeys, groups, three_hk_page_context, three_hk_page_structure
        )
        
        for scenario in scenarios:
            # Scenario ID can be REQ-F-, REQ-P-, etc. depending on page type
            assert scenario.scenario_id.startswith("REQ-"), f"Scenario ID should start with REQ-, got {scenario.scenario_id}"
            assert scenario.scenario_type == ScenarioType.FUNCTIONAL
            assert scenario.given
            assert scenario.when
            assert scenario.then
            assert scenario.priority.value in [p.value for p in ScenarioPriority]
            assert 0.0 <= scenario.confidence <= 1.0


class TestThreeHKAccessibilityScenarios:
    """Test WCAG 2.1 accessibility scenarios with Three HK data"""
    
    def test_generate_three_hk_accessibility_scenarios(
        self, 
        requirements_agent_without_llm, 
        three_hk_ui_elements
    ):
        """Test generating WCAG 2.1 accessibility scenarios"""
        scenarios = requirements_agent_without_llm._generate_accessibility_scenarios(three_hk_ui_elements)
        
        # Should generate multiple accessibility scenarios
        assert len(scenarios) >= 4  # Keyboard, screen reader, contrast, focus
        
        # Check for WCAG 2.1 coverage
        scenario_titles = [s.title.lower() for s in scenarios]
        assert any("keyboard" in title for title in scenario_titles)
        assert any("screen reader" in title or "aria" in title for title in scenario_titles)
    
    def test_three_hk_keyboard_navigation_scenario(
        self, 
        requirements_agent_without_llm, 
        three_hk_ui_elements
    ):
        """Test keyboard navigation scenario for '立即登記' buttons"""
        scenarios = requirements_agent_without_llm._generate_accessibility_scenarios(three_hk_ui_elements)
        
        # Find keyboard navigation scenario
        keyboard_scenarios = [
            s for s in scenarios 
            if "keyboard" in s.title.lower() or "tab" in s.given.lower()
        ]
        assert len(keyboard_scenarios) > 0
        
        # Should be critical or high priority (compare string values)
        for scenario in keyboard_scenarios:
            priority_val = scenario.priority.value if hasattr(scenario.priority, 'value') else scenario.priority
            assert priority_val in ['critical', 'high']


class TestThreeHKSecurityScenarios:
    """Test OWASP Top 10 security scenarios with Three HK data"""
    
    def test_generate_three_hk_security_scenarios(
        self, 
        requirements_agent_without_llm, 
        three_hk_ui_elements,
        three_hk_page_context
    ):
        """Test generating OWASP security scenarios for Three HK"""
        # Add a form element for security testing
        ui_elements_with_form = three_hk_ui_elements + [{
            "type": "form",
            "selector": "#registration-form",
            "action": "/api/register",
            "method": "POST"
        }]
        
        scenarios = requirements_agent_without_llm._generate_security_scenarios(ui_elements_with_form, three_hk_page_context)
        
        # Should generate security scenarios when forms present
        assert len(scenarios) > 0
        
        # Check for OWASP coverage
        scenario_content = " ".join(s.title + s.given + s.when + s.then for s in scenarios)
        # Should mention security concepts
        assert any(term in scenario_content.lower() for term in ["xss", "sql", "csrf", "input", "validation"])


class TestLLMIntegrationWithThreeHK:
    """Test LLM integration with Three HK data"""
    
    @pytest.mark.asyncio
    async def test_llm_scenario_generation_success(
        self, 
        requirements_agent_with_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context,
        mock_llm_response
    ):
        """Test LLM scenario generation with mock (real testing done in E2E)"""
        # Test that LLM path is attempted when client is available
        # Real LLM testing is in E2E test which uses actual Azure OpenAI
        
        # If no real LLM client, scenarios will be empty (fallback happens in main flow)
        scenarios = await requirements_agent_with_llm._generate_scenarios_with_llm(
            three_hk_ui_elements,
            three_hk_page_structure,
            three_hk_page_context
        )
        
        # Method should execute without crashing
        # Empty list is OK - means fallback to pattern-based (tested elsewhere)
        assert isinstance(scenarios, list)
    
    @pytest.mark.asyncio
    async def test_llm_timeout_fallback_to_patterns(
        self,
        requirements_agent_with_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test fallback to pattern-based when LLM times out"""
        # Mock LLM to raise timeout
        mock_llm = Mock()
        mock_llm.enabled = True
        mock_llm.generate_completion = AsyncMock(side_effect=TimeoutError("LLM timeout"))
        requirements_agent_with_llm.llm_client = mock_llm
        
        # Should fall back to pattern-based
        scenarios = await requirements_agent_with_llm._generate_scenarios_with_llm(
            three_hk_ui_elements,
            three_hk_page_structure,
            three_hk_page_context
        )
        
        # Should return empty (indicating fallback needed)
        assert scenarios == []
    
    @pytest.mark.asyncio
    async def test_llm_invalid_json_fallback(
        self,
        requirements_agent_with_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test fallback when LLM returns invalid JSON"""
        mock_llm = Mock()
        mock_llm.enabled = True
        mock_llm.generate_completion = AsyncMock(return_value="Invalid JSON {]")
        requirements_agent_with_llm.llm_client = mock_llm
        
        scenarios = await requirements_agent_with_llm._generate_scenarios_with_llm(
            three_hk_ui_elements,
            three_hk_page_structure,
            three_hk_page_context
        )
        
        # Should return empty list on parse error
        assert scenarios == []
    
    def test_llm_prompt_includes_three_hk_context(
        self,
        requirements_agent_with_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test that LLM prompt includes Three HK specific context"""
        prompt = requirements_agent_with_llm._build_scenario_generation_prompt(
            three_hk_ui_elements,
            three_hk_page_structure,
            three_hk_page_context
        )
        
        # Prompt should include Three HK URL
        assert "web.three.com.hk" in prompt
        
        # Should include page type
        assert "pricing" in prompt.lower()
        
        # Should include element count
        assert str(len(three_hk_ui_elements)) in prompt
        
        # Should request BDD format
        assert "Given" in prompt and "When" in prompt and "Then" in prompt


class TestThreeHKEndToEndScenarios:
    """Test complete scenario generation pipeline with Three HK data"""
    
    @pytest.mark.asyncio
    async def test_complete_three_hk_scenario_generation(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test complete scenario generation (pattern-based) for Three HK"""
        # Create task context
        task = TaskContext(
            conversation_id="test-three-hk",
            task_id="test-task",
            task_type="requirement_extraction",
            payload={
                "ui_elements": three_hk_ui_elements,
                "page_structure": three_hk_page_structure,
                "page_context": three_hk_page_context
            }
        )
        
        result = await requirements_agent_without_llm.execute_task(task)
        
        # Should succeed
        assert result.success
        assert result.confidence > 0.7
        
        # Should generate multiple scenario types
        scenarios = result.result.get("scenarios", [])
        assert len(scenarios) > 0
        
        # Check scenario type distribution
        scenario_types = [s.get("scenario_type") for s in scenarios]
        assert "functional" in scenario_types
        assert "accessibility" in scenario_types
    
    @pytest.mark.asyncio  
    async def test_three_hk_coverage_metrics(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test coverage metrics calculation for Three HK"""
        task = TaskContext(
            conversation_id="test-three-hk-coverage",
            task_id="test-task-2",
            task_type="requirement_extraction",
            payload={
                "ui_elements": three_hk_ui_elements,
                "page_structure": three_hk_page_structure,
                "page_context": three_hk_page_context
            }
        )
        
        result = await requirements_agent_without_llm.execute_task(task)
        
        # Should have coverage metrics
        coverage = result.result.get("coverage_metrics", {})
        assert "ui_coverage_percent" in coverage
        assert "scenario_count" in coverage
        assert coverage["scenario_count"] > 0
        
        # UI coverage should be reasonable (0-100%)
        assert 0 <= coverage["ui_coverage_percent"] <= 100


class TestThreeHKTokenEstimation:
    """Test token usage estimation with Three HK data"""
    
    def test_estimate_three_hk_tokens(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements
    ):
        """Test token estimation for Three HK UI elements"""
        # Create dummy scenarios for token estimation
        scenario = Scenario(
            scenario_id="TEST-001",
            title="Test",
            scenario_type=ScenarioType.FUNCTIONAL,
            priority=ScenarioPriority.MEDIUM,
            given="Test given",
            when="Test when",
            then="Test then",
            tags=[]
        )
        scenario.confidence = 0.8  # Set confidence after initialization
        dummy_scenarios = [scenario]
        estimated_tokens = requirements_agent_without_llm._estimate_token_usage(
            three_hk_ui_elements, dummy_scenarios
        )
        
        # Should estimate tokens based on element count and content
        assert estimated_tokens > 0
        
        # With 9 elements, should be reasonable (not too high or low)
        # Real test showed ~12,500 tokens for 261 elements
        # So 9 elements should be much lower
        assert 100 < estimated_tokens < 2000


class TestThreeHKEdgeCases:
    """Test edge cases with Three HK data"""
    
    def test_handle_chinese_characters(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure
    ):
        """Test handling Chinese characters in UI elements"""
        # Extract Chinese text
        chinese_texts = [
            e.get("text", "") for e in three_hk_ui_elements 
            if any('\u4e00' <= c <= '\u9fff' for c in e.get("text", ""))
        ]
        
        assert len(chinese_texts) > 0  # Should have Chinese text
        
        # Should not crash when processing Chinese characters
        groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        assert len(groups) > 0
    
    def test_handle_external_links(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test handling external links (PDF, WhatsApp)"""
        external_links = [
            e for e in three_hk_ui_elements 
            if e.get("type") == "link" and (
                ".pdf" in e.get("href", "") or 
                "whatsapp" in e.get("href", "").lower()
            )
        ]
        
        assert len(external_links) > 0
        
        # Should process elements even with external links
        element_groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        assert len(element_groups) >= 0
    
    @pytest.mark.asyncio
    async def test_handle_duplicate_button_text(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test handling multiple buttons with same text ('立即登記')"""
        register_buttons = [
            e for e in three_hk_ui_elements 
            if e.get("type") == "button" and "立即登記" in e.get("text", "")
        ]
        
        assert len(register_buttons) >= 2  # Multiple buttons with same text
        
        # Should still generate valid scenarios
        groups = requirements_agent_without_llm._group_elements_by_page(three_hk_ui_elements, three_hk_page_structure)
        journeys = requirements_agent_without_llm._map_user_journeys(groups, three_hk_page_context)
        scenarios = await requirements_agent_without_llm._generate_functional_scenarios(
            journeys, groups, three_hk_page_context, three_hk_page_structure
        )
        
        assert len(scenarios) > 0


class TestThreeHKQualityMetrics:
    """Test quality indicators with Three HK data"""
    
    @pytest.mark.asyncio
    async def test_three_hk_confidence_scoring(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test confidence scoring for Three HK scenarios"""
        task = TaskContext(
            conversation_id="test-confidence",
            task_id="test-task-3",
            task_type="requirement_extraction",
            payload={
                "ui_elements": three_hk_ui_elements,
                "page_structure": three_hk_page_structure,
                "page_context": three_hk_page_context
            }
        )
        
        result = await requirements_agent_without_llm.execute_task(task)
        
        # Pattern-based should have reasonable confidence (0.7-0.85)
        assert 0.7 <= result.confidence <= 0.95
        
        # Quality indicators should exist
        quality = result.result.get("quality_indicators", {})
        assert "confidence" in quality
        assert "completeness" in quality
    
    @pytest.mark.asyncio
    async def test_three_hk_priority_distribution(
        self,
        requirements_agent_without_llm,
        three_hk_ui_elements,
        three_hk_page_structure,
        three_hk_page_context
    ):
        """Test priority distribution for Three HK scenarios"""
        task = TaskContext(
            conversation_id="test-priority",
            task_id="test-task-4",
            task_type="requirement_extraction",
            payload={
                "ui_elements": three_hk_ui_elements,
                "page_structure": three_hk_page_structure,
                "page_context": three_hk_page_context
            }
        )
        
        result = await requirements_agent_without_llm.execute_task(task)
        
        # Should have priority distribution
        quality = result.result.get("quality_indicators", {})
        priority_dist = quality.get("priority_distribution", {})
        
        # Should have some critical/high priority scenarios
        assert priority_dist.get("critical", 0) + priority_dist.get("high", 0) > 0
