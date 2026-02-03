"""
Test User Instruction Support in RequirementsAgent

This test verifies that RequirementsAgent can accept user instructions
and generate scenarios that match the user's specific requirements.
"""
import pytest
import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
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
        "use_llm": True,  # Enable LLM for better observation
        "max_depth": 1,
        "max_pages": 1
    }
    return ObservationAgent(
        message_queue=mock_message_queue,
        agent_id="test_observation_agent",
        priority=8,
        config=config
    )


@pytest.fixture
def requirements_agent(mock_message_queue):
    """Create RequirementsAgent instance with LLM enabled"""
    config = {
        "use_llm": True  # Enable LLM for scenario generation
    }
    return RequirementsAgent(
        agent_id="test_requirements_agent",
        agent_type="requirements",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


class TestUserInstructionSupport:
    """Test RequirementsAgent user instruction support"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_user_instruction_generates_matching_scenario(
        self, observation_agent, requirements_agent
    ):
        """
        Test that RequirementsAgent generates scenarios matching user instruction
        
        User provides:
        - URL: Three HK 5G Broadband page
        - Instruction: "Test purchase flow for '5G寬頻數據無限任用' plan"
        
        Expected:
        - At least one scenario should match the user instruction
        - Matching scenario should have high/critical priority
        - Scenario should include specific details from instruction
        """
        target_url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
        user_instruction = "Test purchase flow for '5G寬頻數據無限任用' plan"
        conversation_id = "user-instruction-test-001"
        
        print(f"\n{'='*80}")
        print("Test: User Instruction Support")
        print(f"URL: {target_url}")
        print(f"User Instruction: {user_instruction}")
        print(f"{'='*80}\n")
        
        # Step 1: Observe the page
        print("Step 1: Observing page with ObservationAgent...")
        observation_task = TaskContext(
            conversation_id=conversation_id,
            task_id="obs-task-001",
            task_type="ui_element_extraction",
            payload={"url": target_url, "max_depth": 1}
        )
        
        observation_result = await observation_agent.execute_task(observation_task)
        assert observation_result.success is True, f"Observation failed: {observation_result.error}"
        ui_elements_count = len(observation_result.result.get('ui_elements', []))
        print(f"[OK] Observation complete: {ui_elements_count} UI elements found")
        assert ui_elements_count > 0, "No UI elements found"
        
        # Extract observation data
        observation_data = {
            "ui_elements": observation_result.result.get("ui_elements", []),
            "page_structure": observation_result.result.get("page_structure", {}),
            "page_context": observation_result.result.get("page_context", {})
        }
        
        # Step 2: Generate scenarios WITH user instruction
        print(f"\nStep 2: Generating scenarios with RequirementsAgent...")
        print(f"        User instruction: '{user_instruction}'")
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-001",
            task_type="requirement_extraction",
            payload={
                **observation_data,
                "user_instruction": user_instruction  # NEW: User instruction
            }
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        
        # Verify requirements generation succeeded
        assert requirements_result.success is True, f"Requirements generation failed: {requirements_result.error}"
        scenarios = requirements_result.result.get("scenarios", [])
        print(f"[OK] Requirements complete: {len(scenarios)} scenarios generated")
        assert len(scenarios) > 0, "No scenarios generated"
        
        # Step 3: Verify at least one scenario matches user instruction
        print(f"\nStep 3: Verifying scenarios match user instruction...")
        matching_scenarios = []
        instruction_keywords = user_instruction.lower().split()
        
        for scenario in scenarios:
            title_lower = scenario.get("title", "").lower()
            when_lower = scenario.get("when", "").lower()
            then_lower = scenario.get("then", "").lower()
            
            # Check if scenario contains keywords from user instruction
            matches = sum(1 for keyword in instruction_keywords 
                         if keyword in title_lower or keyword in when_lower or keyword in then_lower)
            
            # Also check for specific plan name (Chinese characters)
            if "5g寬頻數據無限任用" in title_lower or "5g寬頻數據無限任用" in when_lower:
                matches += 3  # Strong match
            
            if matches >= 2:  # At least 2 keywords match
                matching_scenarios.append(scenario)
                print(f"  [MATCH] Scenario: {scenario.get('title')}")
                print(f"          Priority: {scenario.get('priority')}")
                print(f"          When: {scenario.get('when')[:80]}...")
        
        # Assertions
        assert len(matching_scenarios) > 0, \
            f"No scenarios match user instruction '{user_instruction}'. " \
            f"Generated {len(scenarios)} scenarios but none matched."
        
        print(f"\n[OK] Found {len(matching_scenarios)} scenario(s) matching user instruction")
        
        # Verify matching scenarios have high priority
        high_priority_matches = [s for s in matching_scenarios 
                                 if s.get("priority") in ["critical", "high"]]
        print(f"  - High/Critical priority: {len(high_priority_matches)}/{len(matching_scenarios)}")
        
        # Show matching scenario details
        if matching_scenarios:
            best_match = matching_scenarios[0]
            print(f"\n  Best Match:")
            print(f"    Title: {best_match.get('title')}")
            print(f"    Priority: {best_match.get('priority')}")
            print(f"    Given: {best_match.get('given')}")
            print(f"    When: {best_match.get('when')}")
            print(f"    Then: {best_match.get('then')}")
            print(f"    Tags: {best_match.get('tags', [])}")
        
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Scenarios Generated: {len(scenarios)}")
        print(f"Matching Scenarios: {len(matching_scenarios)}")
        print(f"High Priority Matches: {len(high_priority_matches)}")
        print(f"{'='*80}\n")
        
        # Final assertion
        assert len(high_priority_matches) > 0, \
            "At least one matching scenario should have high/critical priority"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

