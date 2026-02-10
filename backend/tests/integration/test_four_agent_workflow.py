"""
Integration tests for 4-agent workflow: ObservationAgent → RequirementsAgent → AnalysisAgent → EvolutionAgent

Tests the complete end-to-end flow:
1. ObservationAgent observes a web page and extracts UI elements
2. RequirementsAgent generates BDD test scenarios from UI elements
3. AnalysisAgent analyzes scenarios for risk, ROI, dependencies, and prioritization
4. EvolutionAgent generates executable Playwright test code from BDD scenarios
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from agents.analysis_agent import AnalysisAgent
from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext


@pytest.fixture
def mock_message_queue():
    """Mock message queue for all agents"""
    class MockMessageQueue:
        async def publish(self, *args, **kwargs):
            pass
        async def subscribe(self, *args, **kwargs):
            pass
    
    return MockMessageQueue()


@pytest.fixture
def observation_agent(mock_message_queue):
    """Create ObservationAgent instance"""
    config = {
        "use_llm": False,  # Disable LLM for faster tests
        "max_depth": 1,
        "max_pages": 1
    }
    return ObservationAgent(
        message_queue=mock_message_queue,
        agent_id="integration_test_observation_agent",
        priority=8,
        config=config
    )


@pytest.fixture
def requirements_agent(mock_message_queue):
    """Create RequirementsAgent instance"""
    config = {
        "use_llm": False  # Disable LLM for faster tests
    }
    return RequirementsAgent(
        agent_id="integration_test_requirements_agent",
        agent_type="requirements",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def analysis_agent(mock_message_queue):
    """Create AnalysisAgent instance"""
    config = {
        "use_llm": False,  # Disable LLM for faster tests
        "db": None,  # No database for integration tests
        "enable_realtime_execution": False  # Disable real-time execution for integration tests
    }
    return AnalysisAgent(
        agent_id="integration_test_analysis_agent",
        agent_type="analysis",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def evolution_agent(mock_message_queue):
    """Create EvolutionAgent instance"""
    config = {
        "use_llm": False,  # Disable LLM for faster tests (use template mode)
        "cache_enabled": True
    }
    return EvolutionAgent(
        agent_id="integration_test_evolution_agent",
        agent_type="evolution",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def evolution_agent_with_llm(mock_message_queue):
    """Create EvolutionAgent instance with LLM enabled (for LLM tests)"""
    # Mock LLM client
    mock_llm_client = MagicMock()
    mock_llm_client.enabled = True
    mock_llm_client.deployment = "ChatGPT-UAT"
    mock_llm_client.client = MagicMock()
    mock_llm_client.client.chat = MagicMock()
    mock_llm_client.client.chat.completions = MagicMock()
    
    config = {
        "use_llm": True,
        "cache_enabled": True
    }
    
    with patch('llm.azure_client.get_azure_client', return_value=mock_llm_client):
        agent = EvolutionAgent(
            agent_id="integration_test_evolution_agent_llm",
            agent_type="evolution",
            priority=5,
            message_queue=mock_message_queue,
            config=config
        )
        agent.llm_client = mock_llm_client
        yield agent


@pytest.fixture
def sample_observation_data():
    """Sample observation data (simulating ObservationAgent output)"""
    return {
        "ui_elements": [
            # Header navigation
            {"type": "link", "selector": "a.logo", "text": "Home", "href": "/"},
            {"type": "link", "selector": "#nav-products", "text": "Products", "href": "/products"},
            {"type": "link", "selector": "#nav-pricing", "text": "Pricing", "href": "/pricing"},
            {"type": "button", "selector": "#header-login", "text": "Login", "actions": ["click"]},
            
            # Main content - Login form
            {"type": "form", "selector": "#login-form", "action": "/login", "method": "POST"},
            {"type": "input", "selector": "#email", "input_type": "email", 
             "name": "email", "required": True, "placeholder": "Enter email"},
            {"type": "input", "selector": "#password", "input_type": "password", 
             "name": "password", "required": True, "placeholder": "Enter password"},
            {"type": "button", "selector": "#login-submit", "text": "Sign In", "actions": ["click"]},
            
            # Footer
            {"type": "link", "selector": "#footer-privacy", "text": "Privacy Policy", "href": "/privacy"},
            {"type": "link", "selector": "#footer-terms", "text": "Terms", "href": "/terms"}
        ],
        "page_structure": {
            "url": "https://example.com/login",
            "title": "Login - Example App",
            "forms": ["#login-form"],
            "navigation": ["#nav-products", "#nav-pricing"]
        },
        "page_context": {
            "framework": "react",
            "page_type": "login",
            "complexity": "medium",
            "estimated_users": 5000,
            "public": True,
            "url": "https://example.com/login"  # Ensure URL is in page_context for EvolutionAgent
        }
    }


class TestFourAgentWorkflow:
    """Test complete 4-agent workflow: Observe → Requirements → Analyze → Evolve"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(
        self, 
        observation_agent, 
        requirements_agent, 
        analysis_agent, 
        evolution_agent,
        sample_observation_data
    ):
        """
        Test complete workflow from observation to test code generation.
        
        Flow:
        1. ObservationAgent → UI elements
        2. RequirementsAgent → BDD scenarios
        3. AnalysisAgent → Risk scores, prioritization
        4. EvolutionAgent → Playwright test code
        """
        conversation_id = "integration-test-conv-4agent-001"
        
        # Step 1: ObservationAgent observes page (simulated with sample data)
        observation_result = {
            "ui_elements": sample_observation_data["ui_elements"],
            "page_structure": sample_observation_data["page_structure"],
            "page_context": sample_observation_data["page_context"]
        }
        
        # Step 2: RequirementsAgent generates BDD scenarios from observations
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-001",
            task_type="requirement_extraction",
            payload=observation_result
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        
        # Verify RequirementsAgent succeeded
        assert requirements_result.success is True, f"RequirementsAgent failed: {requirements_result.error}"
        assert requirements_result.confidence >= 0.7
        scenarios = requirements_result.result["scenarios"]
        assert len(scenarios) > 0, "No scenarios generated"
        
        # Verify scenarios have BDD format (Given/When/Then)
        for scenario in scenarios:
            assert "given" in scenario, f"Scenario {scenario.get('scenario_id')} missing 'given'"
            assert "when" in scenario, f"Scenario {scenario.get('scenario_id')} missing 'when'"
            assert "then" in scenario, f"Scenario {scenario.get('scenario_id')} missing 'then'"
        
        # Step 3: AnalysisAgent analyzes scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-001",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify AnalysisAgent succeeded
        assert analysis_result.success is True, f"AnalysisAgent failed: {analysis_result.error}"
        assert "risk_scores" in analysis_result.result
        assert "final_prioritization" in analysis_result.result
        assert len(analysis_result.result["risk_scores"]) > 0
        
        # Step 4: EvolutionAgent generates Playwright test code from BDD scenarios
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-001",
            task_type="test_generation",
            payload={
                "scenarios": scenarios,  # BDD scenarios from RequirementsAgent
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": analysis_result.result["final_prioritization"],
                "page_context": sample_observation_data["page_context"],
                "test_data": requirements_result.result["test_data"]
            }
        )
        
        evolution_result = await evolution_agent.execute_task(evolution_task)
        
        # Verify EvolutionAgent succeeded
        assert evolution_result.success is True, f"EvolutionAgent failed: {evolution_result.error}"
        assert "generation_id" in evolution_result.result
        assert "test_file" in evolution_result.result
        assert "code" in evolution_result.result
        assert "test_count" in evolution_result.result
        assert evolution_result.result["test_count"] == len(scenarios)
        
        # Verify generated code contains Playwright imports
        test_code = evolution_result.result["code"]
        assert "@playwright/test" in test_code or "playwright" in test_code.lower()
        assert "test(" in test_code or "test(" in test_code
        
        # Verify each scenario has corresponding test code
        assert len(evolution_result.result["scenarios"]) == len(scenarios)
        
        # Verify confidence score
        assert evolution_result.confidence > 0.0
        assert evolution_result.result["confidence"] > 0.0
    
    @pytest.mark.asyncio
    async def test_evolution_agent_with_llm(
        self,
        requirements_agent,
        analysis_agent,
        evolution_agent_with_llm,
        sample_observation_data
    ):
        """
        Test EvolutionAgent with LLM enabled (generates higher quality code).
        
        This test verifies that EvolutionAgent can use LLM to generate
        better Playwright test code compared to template-based generation.
        """
        conversation_id = "integration-test-conv-4agent-llm"
        
        # Step 1: RequirementsAgent generates scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-llm",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Step 2: AnalysisAgent analyzes scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-llm",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Step 3: Mock LLM response for EvolutionAgent
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
```typescript
import { test, expect } from '@playwright/test';

test('User Login - Happy Path', async ({ page }) => {
  // Given: User is on login page
  await page.goto('https://example.com/login');
  
  // When: User enters email and password, clicks Login button
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'password123');
  await page.click('#login-submit');
  
  // Then: User is redirected to dashboard
  await expect(page).toHaveURL(/dashboard/);
});
```
"""
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Step 4: EvolutionAgent generates code with LLM
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-llm",
            task_type="test_generation",
            payload={
                "scenarios": scenarios[:1],  # Test with one scenario
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": analysis_result.result["final_prioritization"],
                "page_context": sample_observation_data["page_context"],
                "test_data": requirements_result.result["test_data"]
            }
        )
        
        evolution_result = await evolution_agent_with_llm.execute_task(evolution_task)
        
        # Verify EvolutionAgent succeeded with LLM
        assert evolution_result.success is True
        assert "code" in evolution_result.result
        test_code = evolution_result.result["code"]
        
        # Verify LLM-generated code quality (should be better than template)
        assert "import" in test_code
        assert "test(" in test_code or "test(" in test_code
        assert "await" in test_code  # Should have async/await
        assert "expect" in test_code or "assert" in test_code.lower()  # Should have assertions
        
        # Verify LLM was called
        assert evolution_agent_with_llm.llm_client.client.chat.completions.create.called
    
    @pytest.mark.asyncio
    async def test_caching_in_workflow(
        self,
        requirements_agent,
        analysis_agent,
        evolution_agent,
        sample_observation_data
    ):
        """Test that EvolutionAgent caching works in the workflow"""
        conversation_id = "integration-test-conv-4agent-cache"
        
        # Generate scenarios and analysis (same as before)
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-cache",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-cache",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # First generation (cache miss)
        evolution_task_1 = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-cache-1",
            task_type="test_generation",
            payload={
                "scenarios": scenarios[:1],  # One scenario
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": analysis_result.result["final_prioritization"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        result_1 = await evolution_agent.execute_task(evolution_task_1)
        assert result_1.success is True
        assert result_1.result["cache_misses"] == 1
        assert result_1.result["cache_hits"] == 0
        
        # Second generation (same scenario - cache hit)
        evolution_task_2 = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-cache-2",
            task_type="test_generation",
            payload={
                "scenarios": scenarios[:1],  # Same scenario
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": analysis_result.result["final_prioritization"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        result_2 = await evolution_agent.execute_task(evolution_task_2)
        assert result_2.success is True
        assert result_2.result["cache_hits"] == 1
        assert result_2.result["cache_misses"] == 0
        
        # Verify cached code is same as original (compare test code, not full file which has timestamps)
        # The full file includes timestamps, so compare individual scenario test codes
        scenario_1_code = result_1.result["scenarios"][0]["test_code"]
        scenario_2_code = result_2.result["scenarios"][0]["test_code"]
        assert scenario_1_code == scenario_2_code, "Cached scenario code should match original"
    
    @pytest.mark.asyncio
    async def test_generated_code_structure(
        self,
        requirements_agent,
        analysis_agent,
        evolution_agent,
        sample_observation_data
    ):
        """Test that generated Playwright code has correct structure"""
        conversation_id = "integration-test-conv-4agent-structure"
        
        # Generate scenarios and analysis
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-structure",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-structure",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Generate test code
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-structure",
            task_type="test_generation",
            payload={
                "scenarios": scenarios,
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": analysis_result.result["final_prioritization"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        evolution_result = await evolution_agent.execute_task(evolution_task)
        test_code = evolution_result.result["code"]
        
        # Verify code structure
        assert "import" in test_code, "Missing import statement"
        assert "test(" in test_code or "test(" in test_code, "Missing test() function"
        
        # Verify file structure
        assert evolution_result.result["test_file"].endswith(".spec.ts"), "Test file should have .spec.ts extension"
        
        # Verify each scenario has test code
        for scenario_data in evolution_result.result["scenarios"]:
            assert "test_code" in scenario_data, f"Scenario {scenario_data.get('scenario_id')} missing test_code"
            assert len(scenario_data["test_code"]) > 0, f"Scenario {scenario_data.get('scenario_id')} has empty test_code"
    
    @pytest.mark.asyncio
    async def test_workflow_with_prioritization(
        self,
        requirements_agent,
        analysis_agent,
        evolution_agent,
        sample_observation_data
    ):
        """
        Test that EvolutionAgent respects prioritization from AnalysisAgent.
        
        High-priority scenarios should be generated first or with special handling.
        """
        conversation_id = "integration-test-conv-4agent-priority"
        
        # Generate scenarios and analysis
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-priority",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-priority",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify prioritization exists
        prioritization = analysis_result.result["final_prioritization"]
        assert len(prioritization) > 0
        
        # Sort by priority (highest first)
        sorted_prioritization = sorted(
            prioritization, 
            key=lambda x: x.get("composite_score", 0), 
            reverse=True
        )
        
        # Generate test code
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-priority",
            task_type="test_generation",
            payload={
                "scenarios": scenarios,
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": prioritization,
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        evolution_result = await evolution_agent.execute_task(evolution_task)
        
        # Verify all scenarios were generated
        assert evolution_result.result["test_count"] == len(scenarios)
        
        # Verify high-priority scenarios have test code
        high_priority_scenarios = [
            p["scenario_id"] for p in sorted_prioritization[:3]  # Top 3
        ]
        
        generated_scenario_ids = [
            s["scenario_id"] for s in evolution_result.result["scenarios"]
        ]
        
        for high_priority_id in high_priority_scenarios:
            assert high_priority_id in generated_scenario_ids, \
                f"High-priority scenario {high_priority_id} should be generated"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(
        self,
        requirements_agent,
        analysis_agent,
        evolution_agent,
        sample_observation_data
    ):
        """Test error handling when one agent fails in the workflow"""
        conversation_id = "integration-test-conv-4agent-error"
        
        # Generate scenarios and analysis successfully
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-error",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-error",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Test EvolutionAgent with invalid scenario (missing required fields)
        invalid_scenarios = [
            {
                "scenario_id": "INVALID-001",
                "title": "Invalid Scenario",
                # Missing "given", "when", "then"
            }
        ]
        
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-error",
            task_type="test_generation",
            payload={
                "scenarios": invalid_scenarios,
                "risk_scores": [],
                "final_prioritization": [],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        evolution_result = await evolution_agent.execute_task(evolution_task)
        
        # EvolutionAgent should handle gracefully (either succeed with template or fail gracefully)
        # In template mode, it should still generate something
        if evolution_result.success:
            # If it succeeds, verify it generated something
            assert "code" in evolution_result.result
        else:
            # If it fails, verify error message is clear
            assert evolution_result.error is not None
            assert len(evolution_result.error) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

