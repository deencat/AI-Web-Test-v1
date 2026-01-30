"""
REAL 4-Agent E2E Test: ObservationAgent → RequirementsAgent → AnalysisAgent → EvolutionAgent

This is a TRUE end-to-end test that:
1. Actually crawls a real web page (ObservationAgent with Playwright)
2. Uses real LLM calls (RequirementsAgent, AnalysisAgent, EvolutionAgent with Azure OpenAI)
3. Executes real test scenarios (AnalysisAgent with real-time execution enabled)
4. Generates real Playwright test code (EvolutionAgent with LLM)

Expected execution time: 45-155 seconds (depending on LLM response times and execution)
"""
import pytest
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# This must be done BEFORE importing agents that use Azure OpenAI
backend_path = Path(__file__).parent.parent.parent
env_path = backend_path / '.env'
load_dotenv(dotenv_path=env_path)

# Add backend to path
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
def observation_agent_real(mock_message_queue):
    """Create ObservationAgent instance with REAL web crawling enabled"""
    config = {
        "use_llm": True,  # ENABLE LLM for real observation
        "max_depth": 1,
        "max_pages": 1
    }
    return ObservationAgent(
        message_queue=mock_message_queue,
        agent_id="e2e_test_observation_agent",
        priority=8,
        config=config
    )


@pytest.fixture
def requirements_agent_real(mock_message_queue):
    """Create RequirementsAgent instance with REAL LLM enabled"""
    config = {
        "use_llm": True,  # ENABLE LLM for real scenario generation
        "cache_enabled": False  # DISABLE caching for real E2E test
    }
    return RequirementsAgent(
        agent_id="e2e_test_requirements_agent",
        agent_type="requirements",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def db_session():
    """Create a test database session for real execution"""
    try:
        from app.db.session import SessionLocal
        db = SessionLocal()
        yield db
        db.close()
    except Exception as e:
        # If database is not available, return None (will use stub mode)
        print(f"Warning: Database not available: {e}. Using stub mode.")
        yield None


@pytest.fixture
def analysis_agent_real(mock_message_queue, db_session):
    """Create AnalysisAgent instance with REAL LLM and real-time execution enabled"""
    config = {
        "use_llm": True,  # ENABLE LLM for real risk analysis
        "db": db_session,  # Use database session if available
        "enable_realtime_execution": True,  # ENABLE real-time execution
        "execution_rpn_threshold": 0,  # Lower threshold for testing (execute top scenarios)
        "headless_browser": False,  # Show browser during execution (set to True to hide)
        "cache_enabled": False  # DISABLE caching for real E2E test
    }
    return AnalysisAgent(
        agent_id="e2e_test_analysis_agent",
        agent_type="analysis",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def evolution_agent_real(mock_message_queue, db_session):
    """Create EvolutionAgent instance with REAL LLM enabled and database session"""
    config = {
        "use_llm": True,  # ENABLE LLM for real test steps generation
        "cache_enabled": False,  # DISABLE caching for real E2E test
        "db": db_session  # Use database session if available
    }
    return EvolutionAgent(
        agent_id="e2e_test_evolution_agent",
        agent_type="evolution",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


class TestFourAgentE2EReal:
    """REAL 4-Agent E2E Test with actual web crawling, LLM calls, and execution"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test (requires real web crawling, LLM calls, and execution)
    async def test_complete_4_agent_workflow_real(
        self,
        observation_agent_real,
        requirements_agent_real,
        analysis_agent_real,
        evolution_agent_real,
        db_session
    ):
        """
        REAL 4-Agent E2E Test: Complete workflow with actual execution
        
        This test:
        1. Actually crawls the Three HK 5G Broadband page (ObservationAgent)
        2. Uses real LLM to generate BDD scenarios (RequirementsAgent)
        3. Uses real LLM to analyze risk and executes real test scenarios (AnalysisAgent)
        4. Uses real LLM to generate test steps and stores in database (EvolutionAgent)
        
        Expected duration: 45-155 seconds
        """
        target_url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
        conversation_id = "e2e-4agent-real-001"
        
        print(f"\n{'='*80}")
        print(f"REAL 4-Agent E2E Test: Complete Workflow")
        print(f"URL: {target_url}")
        print(f"{'='*80}\n")
        
        # Step 1: ObservationAgent - Observe the page
        print("Step 1: Observing page with ObservationAgent...")
        observation_task = TaskContext(
            conversation_id=conversation_id,
            task_id="obs-task-real-001",
            task_type="ui_element_extraction",
            payload={"url": target_url, "max_depth": 1}
        )
        
        observation_result = await observation_agent_real.execute_task(observation_task)
        
        # Verify observation succeeded
        assert observation_result.success is True, f"Observation failed: {observation_result.error}"
        ui_elements_count = len(observation_result.result.get('ui_elements', []))
        print(f"[OK] Observation complete: {ui_elements_count} UI elements found")
        assert ui_elements_count > 0, "No UI elements found - observation failed"
        
        # Extract observation data
        observation_data = {
            "ui_elements": observation_result.result.get("ui_elements", []),
            "page_structure": observation_result.result.get("page_structure", {}),
            "page_context": observation_result.result.get("page_context", {})
        }
        
        # Ensure URL is in page_context for EvolutionAgent
        if "url" not in observation_data["page_context"]:
            observation_data["page_context"]["url"] = target_url
        
        # Step 2: RequirementsAgent - Generate test scenarios
        print("\nStep 2: Generating test scenarios with RequirementsAgent...")
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-real-001",
            task_type="requirement_extraction",
            payload=observation_data
        )
        
        requirements_result = await requirements_agent_real.execute_task(requirements_task)
        
        # Verify requirements generation succeeded
        assert requirements_result.success is True, f"Requirements generation failed: {requirements_result.error}"
        scenarios = requirements_result.result.get("scenarios", [])
        print(f"[OK] Requirements complete: {len(scenarios)} BDD scenarios generated")
        assert len(scenarios) > 0, "No scenarios generated"
        
        # Verify scenarios have BDD format (Given/When/Then)
        for scenario in scenarios[:3]:  # Check first 3
            assert "given" in scenario, f"Scenario {scenario.get('scenario_id')} missing 'given'"
            assert "when" in scenario, f"Scenario {scenario.get('scenario_id')} missing 'when'"
            assert "then" in scenario, f"Scenario {scenario.get('scenario_id')} missing 'then'"
        
        # Step 3: AnalysisAgent - Analyze scenarios (with real-time execution enabled)
        print("\nStep 3: Analyzing scenarios with AnalysisAgent...")
        print("        Real-time execution is ENABLED - critical scenarios will be executed automatically")
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-real-001",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result.get("test_data", []),
                "coverage_metrics": requirements_result.result.get("coverage_metrics", {}),
                "page_context": observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent_real.execute_task(analysis_task)
        
        # Verify analysis succeeded
        assert analysis_result.success is True, f"Analysis failed: {analysis_result.error}"
        risk_scores_count = len(analysis_result.result.get('risk_scores', []))
        print(f"[OK] Analysis complete: {risk_scores_count} risk scores calculated")
        assert risk_scores_count > 0, "No risk scores calculated"
        
        # Check if any scenarios were executed automatically (if RPN >= 80)
        execution_success = analysis_result.result.get("execution_success", [])
        real_execution_count = len([
            es for es in execution_success 
            if es.get("source") in ["real_time_execution", "execution_results"]
        ])
        
        if real_execution_count > 0:
            print(f"[INFO] {real_execution_count} scenarios were automatically executed during analysis")
        
        # Verify analysis output structure
        assert "risk_scores" in analysis_result.result
        assert "business_values" in analysis_result.result
        assert "roi_scores" in analysis_result.result
        assert "final_prioritization" in analysis_result.result
        assert "execution_strategy" in analysis_result.result
        
        # Step 4: EvolutionAgent - Generate test steps and store in database
        print("\nStep 4: Generating test steps with EvolutionAgent...")
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-real-001",
            task_type="test_generation",
            payload={
                "scenarios": scenarios,  # BDD scenarios from RequirementsAgent
                "risk_scores": analysis_result.result["risk_scores"],
                "final_prioritization": analysis_result.result["final_prioritization"],
                "page_context": observation_data["page_context"],
                "test_data": requirements_result.result.get("test_data", []),
                "db": db_session  # Pass database session if available
            }
        )
        
        evolution_result = await evolution_agent_real.execute_task(evolution_task)
        
        # Verify EvolutionAgent succeeded
        assert evolution_result.success is True, f"EvolutionAgent failed: {evolution_result.error}"
        assert "generation_id" in evolution_result.result
        assert "test_count" in evolution_result.result
        assert "test_cases" in evolution_result.result
        assert evolution_result.result["test_count"] == len(scenarios)
        
        generation_id = evolution_result.result["generation_id"]
        test_case_ids = evolution_result.result.get("test_case_ids", [])
        stored_in_db = evolution_result.result.get("stored_in_database", False)
        
        print(f"[OK] Evolution complete: {evolution_result.result['test_count']} test cases generated")
        print(f"        Generation ID: {generation_id}")
        print(f"        Stored in database: {stored_in_db}")
        if test_case_ids:
            print(f"        Database IDs: {test_case_ids[:5]}{'...' if len(test_case_ids) > 5 else ''}")
        
        # Verify each scenario has corresponding test steps
        test_cases = evolution_result.result["test_cases"]
        assert len(test_cases) == len(scenarios)
        for test_case_data in test_cases[:3]:  # Check first 3
            assert "steps" in test_case_data, \
                f"Test case {test_case_data.get('scenario_id')} missing steps"
            assert isinstance(test_case_data["steps"], list), \
                f"Test case {test_case_data.get('scenario_id')} steps should be a list"
            assert len(test_case_data["steps"]) > 0, \
                f"Test case {test_case_data.get('scenario_id')} has empty steps"
        
        # Verify confidence score
        assert evolution_result.confidence > 0.0
        assert evolution_result.result["confidence"] > 0.0
        print(f"        Confidence: {evolution_result.result['confidence']:.2f}")
        
        # Step 4.5: Verify test cases are stored in database (if database available)
        if db_session and stored_in_db and test_case_ids:
            print("\nStep 4.5: Verifying test cases in database...")
            from app.models.test_case import TestCase
            import json
            
            # Query database for test cases by IDs (more reliable than JSON query)
            db_test_cases = db_session.query(TestCase).filter(
                TestCase.id.in_(test_case_ids)
            ).all()
            
            assert len(db_test_cases) == len(test_case_ids), \
                f"Expected {len(test_case_ids)} test cases in database, got {len(db_test_cases)}"
            
            print(f"[OK] Verified {len(db_test_cases)} test cases in database")
            
            # Verify test case structure
            for db_tc in db_test_cases[:3]:  # Check first 3
                assert db_tc.title is not None and len(db_tc.title) > 0, "Test case title should not be empty"
                assert db_tc.steps is not None and isinstance(db_tc.steps, list), "Test case steps should be a list"
                assert len(db_tc.steps) > 0, "Test case should have at least one step"
                assert db_tc.expected_result is not None, "Test case should have expected result"
                
                # Verify metadata contains generation_id
                if db_tc.test_metadata:
                    metadata = db_tc.test_metadata if isinstance(db_tc.test_metadata, dict) else json.loads(db_tc.test_metadata)
                    assert metadata.get("generation_id") == generation_id, \
                        f"Test case metadata should contain generation_id: {generation_id}"
                
                print(f"        - {db_tc.title}: {len(db_tc.steps)} steps")
                print(f"          Steps: {db_tc.steps[:2]}{'...' if len(db_tc.steps) > 2 else ''}")
        else:
            print("\nStep 4.5: Skipping database verification (database not available or not stored)")
        
        # Step 5: Print summary
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Page URL: {target_url}")
        print(f"UI Elements Observed: {len(observation_data['ui_elements'])}")
        print(f"Scenarios Generated: {len(scenarios)}")
        print(f"Risk Scores Calculated: {len(analysis_result.result['risk_scores'])}")
        print(f"Scenarios Prioritized: {len(analysis_result.result['final_prioritization'])}")
        print(f"Scenarios Executed (REAL): {real_execution_count}")
        print(f"Test Cases Generated: {evolution_result.result['test_count']}")
        if evolution_result.result.get("stored_in_database"):
            print(f"Test Cases Stored in DB: {len(evolution_result.result.get('test_case_ids', []))}")
        
        # Show top 3 prioritized scenarios
        print(f"\nTop 3 Prioritized Scenarios:")
        final_prioritization = analysis_result.result["final_prioritization"]
        for idx, item in enumerate(final_prioritization[:3], 1):
            scenario = next((s for s in scenarios if s["scenario_id"] == item["scenario_id"]), None)
            if scenario:
                print(f"  {idx}. {scenario.get('title', 'N/A')}")
                print(f"     Priority: {item['priority']}, Score: {item['composite_score']:.2f}")
                print(f"     Type: {scenario.get('scenario_type', 'N/A')}")
        
        print(f"{'='*80}\n")
        
        # Final assertions
        assert len(scenarios) >= 5, f"Expected at least 5 scenarios, got {len(scenarios)}"
        # Some scenarios might be filtered out (circular dependencies, etc.), so allow some variance
        risk_scores_count = len(analysis_result.result["risk_scores"])
        assert risk_scores_count >= len(scenarios) * 0.7, \
            f"Expected at least 70% of scenarios to have risk scores, got {risk_scores_count}/{len(scenarios)}"
        assert len(final_prioritization) >= len(scenarios) * 0.7, \
            f"Expected at least 70% of scenarios to be prioritized, got {len(final_prioritization)}/{len(scenarios)}"
        
        print("[OK] All assertions passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
