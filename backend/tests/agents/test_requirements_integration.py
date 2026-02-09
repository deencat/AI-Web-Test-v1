"""
Integration test for RequirementsAgent with ObservationAgent
Tests the complete flow: ObservationAgent ??RequirementsAgent
"""
import pytest
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.requirements_agent import RequirementsAgent
from agents.base_agent import TaskContext


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
        "use_llm": False
    }
    return RequirementsAgent(
        agent_id="integration_test_requirements_agent",
        agent_type="requirements",
        priority=5,
        message_queue=MockMessageQueue(),
        config=config
    )


@pytest.fixture
def three_hk_observation_data():
    """
    Real observation data from Three HK website test
    This simulates the output from ObservationAgent
    """
    return {
        "ui_elements": [
            # Header navigation
            {"type": "link", "selector": "a.logo", "text": "3香港", "href": "/"},
            {"type": "link", "selector": "#nav-5g-plans", "text": "5G 計�?", "href": "/5g-plans"},
            {"type": "link", "selector": "#nav-broadband", "text": "家�?寬頻", "href": "/broadband"},
            {"type": "link", "selector": "#nav-roaming", "text": "漫�?", "href": "/roaming"},
            {"type": "button", "selector": "#header-login", "text": "?�入", "actions": ["click"]},
            
            # Main content - Pricing plans
            {"type": "button", "selector": ".plan-card-1 .btn-select", "text": "?��?計�?", "actions": ["click"]},
            {"type": "button", "selector": ".plan-card-2 .btn-select", "text": "?��?計�?", "actions": ["click"]},
            {"type": "button", "selector": ".plan-card-3 .btn-select", "text": "?��?計�?", "actions": ["click"]},
            
            # Forms
            {"type": "form", "selector": "#newsletter-form", "action": "/subscribe", "method": "POST"},
            {"type": "input", "selector": "#newsletter-email", "input_type": "email", 
             "name": "email", "required": True, "placeholder": "輸入?��??�郵?��?"},
            {"type": "button", "selector": "#newsletter-submit", "text": "訂閱", "actions": ["click"]},
            
            # Footer
            {"type": "link", "selector": "#footer-privacy", "text": "Privacy Policy", "href": "/privacy"},
            {"type": "link", "selector": "#footer-terms", "text": "Terms & Conditions", "href": "/terms"},
            {"type": "link", "selector": "#footer-contact", "text": "Contact Us", "href": "/contact"}
        ],
        "page_structure": {
            "url": "https://www.three.com.hk/",
            "title": "3HK - 5G Network Provider",
            "forms": ["#newsletter-form"],
            "navigation": ["#nav-5g-plans", "#nav-broadband", "#nav-roaming"]
        },
        "page_context": {
            "framework": "jQuery",
            "page_type": "pricing",
            "complexity": "medium"
        }
    }


class TestObservationToRequirements:
    """Test integration between ObservationAgent and RequirementsAgent"""
    
    @pytest.mark.asyncio
    async def test_process_three_hk_observation(self, requirements_agent, three_hk_observation_data):
        """Test processing real Three HK observation data"""
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="integration-three-hk",
            task_type="requirement_extraction",
            payload=three_hk_observation_data
        )
        
        result = await requirements_agent.execute_task(task)
        
        # Verify success
        assert result.success is True
        assert result.confidence >= 0.75
        
        # Verify scenarios generated
        scenarios = result.result["scenarios"]
        assert len(scenarios) >= 12, f"Expected at least 12 scenarios, got {len(scenarios)}"
        
        # Verify scenario types
        scenario_types = {s["scenario_type"] for s in scenarios}
        assert "functional" in scenario_types
        assert "accessibility" in scenario_types
        assert "security" in scenario_types
        
        # Verify functional scenarios reference actual UI elements
        functional_scenarios = [s for s in scenarios if s["scenario_type"] == "functional"]
        assert len(functional_scenarios) >= 5
        
        # Check for pricing-specific scenarios
        pricing_scenarios = [s for s in functional_scenarios 
                            if "?��?計�?" in s["title"] or "plan" in s["title"].lower()]
        assert len(pricing_scenarios) > 0, "Expected pricing-related scenarios"
        
        # Verify accessibility scenarios (WCAG 2.1)
        accessibility_scenarios = [s for s in scenarios if s["scenario_type"] == "accessibility"]
        assert len(accessibility_scenarios) == 4
        assert any("keyboard" in s["title"].lower() for s in accessibility_scenarios)
        assert any("screen reader" in s["title"].lower() for s in accessibility_scenarios)
        
        # Verify security scenarios (OWASP)
        security_scenarios = [s for s in scenarios if s["scenario_type"] == "security"]
        assert len(security_scenarios) == 4
        assert any("xss" in s["title"].lower() for s in security_scenarios)
        assert any("sql injection" in s["title"].lower() for s in security_scenarios)
        
        # Verify test data extracted from form
        test_data = result.result["test_data"]
        assert len(test_data) >= 1
        
        email_field = next((f for f in test_data if "email" in f["field_name"]), None)
        assert email_field is not None
        assert email_field["field_type"] == "email"
        assert email_field["required"] is True
        
        # Verify coverage metrics
        coverage = result.result["coverage_metrics"]
        assert coverage["total_elements"] == len(three_hk_observation_data["ui_elements"])
        assert coverage["interactive_elements"] > 0
        assert coverage["ui_coverage_percent"] > 0
        
        # Verify quality indicators
        quality = result.result["quality_indicators"]
        assert quality["scenario_count"] == len(scenarios)
        assert quality["confidence"] >= 0.75
        assert quality["completeness"] > 0
        
        # Verify priority distribution
        priority_dist = quality["priority_distribution"]
        assert priority_dist["critical"] > 0  # Security scenarios should be critical
        assert priority_dist["high"] > 0      # Accessibility scenarios should be high
    
    @pytest.mark.asyncio
    async def test_scenario_traceability(self, requirements_agent, three_hk_observation_data):
        """Test scenarios are traceable to UI elements"""
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="traceability-test",
            task_type="requirement_extraction",
            payload=three_hk_observation_data
        )
        
        result = await requirements_agent.execute_task(task)
        scenarios = result.result["scenarios"]
        
        # Check functional scenarios reference actual UI elements
        functional_scenarios = [s for s in scenarios if s["scenario_type"] == "functional"]
        
        ui_texts = {el["text"] for el in three_hk_observation_data["ui_elements"] 
                    if "text" in el}
        
        # At least some scenarios should reference actual UI element text
        references_found = 0
        for scenario in functional_scenarios:
            scenario_text = f"{scenario['title']} {scenario['when']} {scenario['then']}"
            for ui_text in ui_texts:
                if ui_text in scenario_text:
                    references_found += 1
                    break
        
        assert references_found > 0, "Scenarios should reference actual UI elements"
    
    @pytest.mark.asyncio
    async def test_coverage_calculation_accuracy(self, requirements_agent, three_hk_observation_data):
        """Test coverage calculation is accurate"""
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="coverage-test",
            task_type="requirement_extraction",
            payload=three_hk_observation_data
        )
        
        result = await requirements_agent.execute_task(task)
        coverage = result.result["coverage_metrics"]
        
        # Manually count interactive elements
        interactive_types = {"button", "link", "input", "select"}
        expected_interactive = len([el for el in three_hk_observation_data["ui_elements"]
                                    if el["type"] in interactive_types])
        
        assert coverage["interactive_elements"] == expected_interactive
        assert coverage["total_elements"] == len(three_hk_observation_data["ui_elements"])
    
    @pytest.mark.asyncio
    async def test_scenario_quality(self, requirements_agent, three_hk_observation_data):
        """Test generated scenarios follow BDD format"""
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="quality-test",
            task_type="requirement_extraction",
            payload=three_hk_observation_data
        )
        
        result = await requirements_agent.execute_task(task)
        scenarios = result.result["scenarios"]
        
        for scenario in scenarios:
            # Verify BDD structure
            assert "given" in scenario and len(scenario["given"]) > 0
            assert "when" in scenario and len(scenario["when"]) > 0
            assert "then" in scenario and len(scenario["then"]) > 0
            
            # Verify metadata
            assert "scenario_id" in scenario
            assert "title" in scenario
            assert "priority" in scenario
            assert "scenario_type" in scenario
            assert "confidence" in scenario
            
            # Verify confidence range
            assert 0.0 <= scenario["confidence"] <= 1.0
            
            # Verify priority is valid
            assert scenario["priority"] in ["critical", "high", "medium", "low"]
            
            # Verify scenario type is valid
            assert scenario["scenario_type"] in [
                "functional", "accessibility", "security", "edge_case", "performance", "usability"
            ]


class TestMinimalObservation:
    """Test with minimal observation data"""
    
    @pytest.mark.asyncio
    async def test_minimal_ui_elements(self, requirements_agent):
        """Test with minimal UI elements"""
        minimal_data = {
            "ui_elements": [
                {"type": "button", "selector": "#btn", "text": "Click"}
            ],
            "page_structure": {"url": "https://example.com"},
            "page_context": {"page_type": "unknown"}
        }
        
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="minimal-test",
            task_type="requirement_extraction",
            payload=minimal_data
        )
        
        result = await requirements_agent.execute_task(task)
        
        assert result.success is True
        assert len(result.result["scenarios"]) > 0
        
        # Should still generate accessibility scenarios
        scenarios = result.result["scenarios"]
        accessibility_count = len([s for s in scenarios if s["scenario_type"] == "accessibility"])
        assert accessibility_count == 4


class TestComplexObservation:
    """Test with complex observation data"""
    
    @pytest.mark.asyncio
    async def test_large_number_of_elements(self, requirements_agent):
        """Test with large number of UI elements"""
        # Simulate complex page with many elements
        complex_data = {
            "ui_elements": [
                {"type": "button", "selector": f"#btn-{i}", "text": f"Button {i}"}
                for i in range(50)
            ] + [
                {"type": "input", "selector": f"#input-{i}", "input_type": "text", "name": f"field_{i}"}
                for i in range(20)
            ],
            "page_structure": {"url": "https://complex-app.com"},
            "page_context": {"page_type": "dashboard", "complexity": "high"}
        }
        
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="complex-test",
            task_type="requirement_extraction",
            payload=complex_data
        )
        
        result = await requirements_agent.execute_task(task)
        
        assert result.success is True
        assert result.execution_time_seconds < 10.0  # Should complete within 10 seconds
        
        scenarios = result.result["scenarios"]
        assert len(scenarios) >= 12  # Minimum scenarios even for complex pages
        
        # Coverage should be reasonable
        coverage = result.result["coverage_metrics"]
        assert coverage["ui_coverage_percent"] > 0


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_missing_ui_elements(self, requirements_agent):
        """Test with missing UI elements"""
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="error-test-1",
            task_type="requirement_extraction",
            payload={
                "page_structure": {},
                "page_context": {}
            }
        )
        
        result = await requirements_agent.execute_task(task)
        
        # Should handle gracefully
        assert result.success is True
        # Should still generate accessibility scenarios
        assert len(result.result["scenarios"]) >= 4
    
    @pytest.mark.asyncio
    async def test_malformed_ui_elements(self, requirements_agent):
        """Test with malformed UI elements"""
        task = TaskContext(
            conversation_id="integration-test-conv",
            task_id="error-test-2",
            task_type="requirement_extraction",
            payload={
                "ui_elements": [
                    {},  # Empty element
                    {"type": "button"},  # Missing selector
                    {"selector": "#btn"}  # Missing type
                ],
                "page_structure": {},
                "page_context": {}
            }
        )
        
        result = await requirements_agent.execute_task(task)
        
        # Should handle gracefully
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
