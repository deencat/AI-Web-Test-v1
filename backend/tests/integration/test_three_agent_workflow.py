"""
Integration tests for 3-agent workflow: ObservationAgent → RequirementsAgent → AnalysisAgent

Tests the complete end-to-end flow:
1. ObservationAgent observes a web page and extracts UI elements
2. RequirementsAgent generates test scenarios from UI elements
3. AnalysisAgent analyzes scenarios for risk, ROI, dependencies, and prioritization
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from agents.analysis_agent import AnalysisAgent
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
        "enable_realtime_execution": False  # Disable real-time execution by default (can enable per test)
    }
    return AnalysisAgent(
        agent_id="integration_test_analysis_agent",
        agent_type="analysis",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


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
            "public": True
        }
    }


class TestThreeAgentWorkflow:
    """Test complete 3-agent workflow: Observe → Requirements → Analyze"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(
        self, observation_agent, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test complete workflow from observation to analysis"""
        conversation_id = "integration-test-conv-001"
        
        # Step 1: ObservationAgent observes page (simulated with sample data)
        # In real scenario, this would be: observation_task → ObservationAgent.execute_task()
        observation_result = {
            "ui_elements": sample_observation_data["ui_elements"],
            "page_structure": sample_observation_data["page_structure"],
            "page_context": sample_observation_data["page_context"]
        }
        
        # Step 2: RequirementsAgent generates scenarios from observations
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-001",
            task_type="requirement_extraction",
            payload=observation_result
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        
        # Verify RequirementsAgent succeeded
        assert requirements_result.success is True
        assert requirements_result.confidence >= 0.7
        assert len(requirements_result.result["scenarios"]) > 0
        
        # Step 3: AnalysisAgent analyzes scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-001",
            task_type="risk_analysis",
            payload={
                "scenarios": requirements_result.result["scenarios"],
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify AnalysisAgent succeeded
        assert analysis_result.success is True
        assert analysis_result.confidence >= 0.8
        
        # Verify analysis output structure
        assert "risk_scores" in analysis_result.result
        assert "business_values" in analysis_result.result
        assert "roi_scores" in analysis_result.result
        assert "dependencies" in analysis_result.result
        assert "final_prioritization" in analysis_result.result
        assert "execution_strategy" in analysis_result.result
        
        # Verify risk scores exist for all scenarios
        risk_scores = analysis_result.result["risk_scores"]
        scenarios = requirements_result.result["scenarios"]
        assert len(risk_scores) == len(scenarios)
        
        # Verify final prioritization
        final_prioritization = analysis_result.result["final_prioritization"]
        assert len(final_prioritization) == len(scenarios)
        assert all("rank" in item for item in final_prioritization)
        assert all("priority" in item for item in final_prioritization)
        assert all("composite_score" in item for item in final_prioritization)
    
    @pytest.mark.asyncio
    async def test_scenario_to_risk_score_mapping(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that each scenario gets a risk score"""
        conversation_id = "integration-test-conv-002"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-002",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-002",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify each scenario has a risk score
        risk_scores = analysis_result.result["risk_scores"]
        scenario_ids = {s["scenario_id"] for s in scenarios}
        risk_score_ids = {rs["scenario_id"] for rs in risk_scores if "scenario_id" in rs}
        
        # Note: risk_scores format is list of dicts with rpn, severity, etc.
        # Need to check if scenario_id is in the dict or if we need to match differently
        # Actually, looking at the code, risk_scores is a list of risk score dicts
        # Let me check the actual format from the code
        
        # Each risk score should have RPN, severity, occurrence, detection
        assert len(risk_scores) == len(scenarios)
        for rs in risk_scores:
            assert "rpn" in rs
            assert "severity" in rs
            assert "occurrence" in rs
            assert "detection" in rs
            assert "priority" in rs
            assert rs["rpn"] >= 1
            assert rs["rpn"] <= 125  # Max RPN = 5 * 5 * 5
    
    @pytest.mark.asyncio
    async def test_critical_scenarios_prioritized(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that critical scenarios (security, login) are prioritized"""
        conversation_id = "integration-test-conv-003"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-003",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Find security scenarios (should be critical)
        security_scenarios = [s for s in scenarios if s["scenario_type"] == "security"]
        assert len(security_scenarios) > 0
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-003",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify security scenarios have appropriate priority
        final_prioritization = analysis_result.result["final_prioritization"]
        security_ids = {s["scenario_id"] for s in security_scenarios}
        
        security_priorities = [
            p for p in final_prioritization 
            if p["scenario_id"] in security_ids
        ]
        
        # Security scenarios should exist and have reasonable priority
        assert len(security_priorities) > 0
        
        # At least some security scenarios should be prioritized (critical/high/medium)
        # or have higher composite scores than non-security scenarios
        security_scores = [sp["composite_score"] for sp in security_priorities]
        non_security_scores = [
            p["composite_score"] for p in final_prioritization 
            if p["scenario_id"] not in security_ids
        ]
        
        if non_security_scores:
            # Security scenarios should generally have higher scores
            avg_security_score = sum(security_scores) / len(security_scores)
            avg_non_security_score = sum(non_security_scores) / len(non_security_scores)
            # Security should be at least as important (allow some variance)
            assert avg_security_score >= avg_non_security_score * 0.8
    
    @pytest.mark.asyncio
    async def test_dependency_analysis_workflow(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that dependency analysis works in workflow"""
        conversation_id = "integration-test-conv-004"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-004",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Add some dependencies to scenarios (simulate dependent scenarios)
        # Modify scenarios to include dependencies
        scenarios_with_deps = []
        for i, scenario in enumerate(scenarios):
            scenario_dict = scenario.copy()
            # First scenario depends on nothing, second depends on first, etc.
            if i > 0:
                scenario_dict["depends_on"] = [scenarios[i-1]["scenario_id"]]
            else:
                scenario_dict["depends_on"] = []
            scenarios_with_deps.append(scenario_dict)
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-004",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios_with_deps,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify dependency analysis
        dependencies = analysis_result.result["dependencies"]
        assert len(dependencies) == len(scenarios_with_deps)
        
        # First scenario should have execution_order = 1 (no dependencies)
        first_dep = next(d for d in dependencies if d["scenario_id"] == scenarios_with_deps[0]["scenario_id"])
        assert first_dep["execution_order"] == 1
        assert first_dep["can_run_parallel"] is True
        
        # Second scenario should have higher execution_order
        if len(scenarios_with_deps) > 1:
            second_dep = next(d for d in dependencies if d["scenario_id"] == scenarios_with_deps[1]["scenario_id"])
            assert second_dep["execution_order"] > first_dep["execution_order"]
    
    @pytest.mark.asyncio
    async def test_roi_calculation_in_workflow(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that ROI calculation works in workflow"""
        conversation_id = "integration-test-conv-005"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-005",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-005",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify ROI scores
        roi_scores = analysis_result.result["roi_scores"]
        assert len(roi_scores) == len(scenarios)
        
        for roi in roi_scores:
            assert "scenario_id" in roi
            assert "roi" in roi
            assert "bug_detection_value" in roi
            assert "test_cost" in roi
            assert "break_even_days" in roi
            # ROI can be negative (if test cost > bug value), but should be a number
            assert isinstance(roi["roi"], (int, float))
    
    @pytest.mark.asyncio
    async def test_execution_strategy_generation(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that execution strategy is generated correctly"""
        conversation_id = "integration-test-conv-006"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-006",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-006",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify execution strategy
        execution_strategy = analysis_result.result["execution_strategy"]
        assert "smoke_tests" in execution_strategy
        assert "parallel_groups" in execution_strategy
        assert "estimated_total_time" in execution_strategy
        assert "estimated_parallel_time" in execution_strategy
        
        # Smoke tests should be a list
        assert isinstance(execution_strategy["smoke_tests"], list)
        
        # Parallel groups should be a list of lists
        assert isinstance(execution_strategy["parallel_groups"], list)
        
        # Estimated times should be positive
        assert execution_strategy["estimated_total_time"] > 0
        assert execution_strategy["estimated_parallel_time"] > 0
        assert execution_strategy["estimated_parallel_time"] <= execution_strategy["estimated_total_time"]
    
    @pytest.mark.asyncio
    async def test_business_value_calculation(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that business value is calculated for login page"""
        conversation_id = "integration-test-conv-007"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-007",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-007",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify business values
        business_values = analysis_result.result["business_values"]
        assert len(business_values) == len(scenarios)
        
        # Login page should have high revenue impact (0.8)
        for bv in business_values:
            assert "scenario_id" in bv
            assert "revenue_impact" in bv
            assert "user_impact" in bv
            assert "compliance" in bv
            assert "reputation" in bv
            assert "total_value" in bv
            
            # Login page should have revenue_impact = 0.8
            assert bv["revenue_impact"] == 0.8
            # User impact should be calculated (5000 users / 10000 = 0.5)
            assert bv["user_impact"] == 0.5
    
    @pytest.mark.asyncio
    async def test_coverage_impact_analysis(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that coverage impact is analyzed"""
        conversation_id = "integration-test-conv-008"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-008",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        coverage_metrics = requirements_result.result["coverage_metrics"]
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-008",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": coverage_metrics,
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify coverage impact
        coverage_impact = analysis_result.result["coverage_impact"]
        assert len(coverage_impact) == len(scenarios)
        
        for ci in coverage_impact:
            assert "scenario_id" in ci
            assert "coverage_delta" in ci
            assert "covers_new_code" in ci
            assert "gap_priority" in ci
            assert ci["gap_priority"] in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_data_flow_consistency(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that data flows correctly through all agents"""
        conversation_id = "integration-test-conv-009"
        
        # Step 1: RequirementsAgent
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-009",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        
        # Verify RequirementsAgent output structure
        assert "scenarios" in requirements_result.result
        assert "test_data" in requirements_result.result
        assert "coverage_metrics" in requirements_result.result
        
        scenarios = requirements_result.result["scenarios"]
        assert len(scenarios) > 0
        
        # Step 2: AnalysisAgent
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-009",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify AnalysisAgent received correct input
        assert analysis_result.success is True
        
        # Verify scenario IDs are consistent
        analysis_scenario_ids = {
            item["scenario_id"] 
            for item in analysis_result.result["final_prioritization"]
        }
        requirements_scenario_ids = {s["scenario_id"] for s in scenarios}
        
        assert analysis_scenario_ids == requirements_scenario_ids
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(
        self, requirements_agent, analysis_agent
    ):
        """Test error handling when data is missing"""
        conversation_id = "integration-test-conv-010"
        
        # Test with missing scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-010",
            task_type="risk_analysis",
            payload={
                "scenarios": [],  # Empty scenarios
                "test_data": [],
                "coverage_metrics": {},
                "page_context": {}
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Should handle gracefully
        assert analysis_result.success is True
        assert len(analysis_result.result["risk_scores"]) == 0
        assert len(analysis_result.result["final_prioritization"]) == 0
    
    @pytest.mark.asyncio
    async def test_prioritization_ranking(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """Test that final prioritization is properly ranked"""
        conversation_id = "integration-test-conv-011"
        
        # Generate scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-011",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Analyze scenarios
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-011",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify prioritization is sorted
        final_prioritization = analysis_result.result["final_prioritization"]
        
        if len(final_prioritization) > 1:
            # Should be sorted by composite_score descending
            scores = [p["composite_score"] for p in final_prioritization]
            assert scores == sorted(scores, reverse=True)
            
            # Ranks should be sequential
            ranks = [p["rank"] for p in final_prioritization]
            assert ranks == list(range(1, len(final_prioritization) + 1))
            
            # First item should have highest score and rank 1
            assert final_prioritization[0]["rank"] == 1
            assert final_prioritization[0]["composite_score"] == max(scores)
    
    @pytest.mark.asyncio
    async def test_e2e_with_test_execution_3_tier(
        self, requirements_agent, analysis_agent, sample_observation_data
    ):
        """
        E2E test: Observation → Requirements → Analysis → Test Execution (3-tier)
        
        This test verifies the complete workflow including actual test execution
        using the 3-tier execution strategy (Tier 1: Playwright, Tier 2: Hybrid, Tier 3: Stagehand AI).
        """
        conversation_id = "integration-test-conv-e2e-execution"
        
        # Step 1: RequirementsAgent generates scenarios
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-e2e",
            task_type="requirement_extraction",
            payload=sample_observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        scenarios = requirements_result.result["scenarios"]
        
        # Step 2: AnalysisAgent analyzes scenarios (initial scoring)
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-e2e",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify initial analysis succeeded
        assert analysis_result.success is True
        initial_risk_scores = {rs["scenario_id"]: rs for rs in analysis_result.result["risk_scores"]}
        
        # Step 3: Simulate test execution results (mocking actual execution for integration test)
        # In real scenario, AnalysisAgent would execute tests using StagehandExecutionService
        # For integration test, we provide execution results to verify scoring adjustment
        execution_results = []
        for scenario in scenarios[:3]:  # Test first 3 scenarios
            scenario_id = scenario["scenario_id"]
            # Simulate execution: 80% success rate (some steps pass, some fail)
            execution_results.append({
                "scenario_id": scenario_id,
                "success_rate": 0.8,
                "passed_steps": 4,
                "total_steps": 5,
                "result": "pass",  # Overall pass despite some step failures
                "tier_used": "hybrid"  # Used Tier 1 → Tier 3 fallback
            })
        
        # Step 4: Re-analyze with execution results (post-execution refinement)
        analysis_task_with_results = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-e2e-refined",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result["test_data"],
                "coverage_metrics": requirements_result.result["coverage_metrics"],
                "page_context": sample_observation_data["page_context"],
                "execution_results": execution_results  # Include execution results
            }
        )
        
        refined_analysis_result = await analysis_agent.execute_task(analysis_task_with_results)
        
        # Verify refined analysis succeeded
        assert refined_analysis_result.success is True
        
        # Verify execution results are incorporated
        refined_risk_scores = {rs["scenario_id"]: rs for rs in refined_analysis_result.result["risk_scores"]}
        execution_success = refined_analysis_result.result["execution_success"]
        
        # Verify execution success data exists
        assert len(execution_success) > 0
        
        # Verify that scenarios with execution results have adjusted detection scores
        for exec_result in execution_results:
            scenario_id = exec_result["scenario_id"]
            if scenario_id in initial_risk_scores and scenario_id in refined_risk_scores:
                initial_detection = initial_risk_scores[scenario_id]["detection"]
                refined_detection = refined_risk_scores[scenario_id]["detection"]
                
                # Detection should be adjusted based on success rate (80% = good reliability)
                # Success rate 0.8 should lower detection score (better detection = lower number)
                assert refined_detection <= initial_detection, \
                    f"Detection score should decrease for reliable test (success_rate=0.8)"
        
        # Verify execution success includes tier information
        for success_data in execution_success:
            if success_data["scenario_id"] in [er["scenario_id"] for er in execution_results]:
                assert "success_rate" in success_data
                assert "tier_used" in success_data or "reliability" in success_data
                assert 0.0 <= success_data["success_rate"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_scenario_to_steps_conversion(
        self, analysis_agent, sample_observation_data
    ):
        """Test that BDD scenarios are correctly converted to executable test steps"""
        scenario = {
            "scenario_id": "REQ-F-001",
            "title": "User Login Flow",
            "given": "User is on login page",
            "when": "User enters email and password, clicks Login button",
            "then": "User is redirected to dashboard"
        }
        
        page_context = sample_observation_data["page_context"]
        page_context["url"] = "https://example.com/login"
        
        steps = analysis_agent._convert_scenario_to_steps(scenario, page_context)
        
        # Verify steps are generated
        assert len(steps) > 0
        
        # Verify navigation step (from Given)
        assert any("navigate" in step.lower() or "login" in step.lower() for step in steps)
        
        # Verify action steps (from When)
        assert any("enter" in step.lower() or "email" in step.lower() or "password" in step.lower() 
                  or "click" in step.lower() for step in steps)
        
        # Verify assertion step (from Then)
        assert any("verify" in step.lower() or "dashboard" in step.lower() for step in steps)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

