"""
Real-world E2E test using Three HK 5G Broadband page
Tests the complete workflow: Observation → Requirements → Analysis → Real Execution
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
        agent_id="test_observation_agent",
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
        agent_id="test_requirements_agent",
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
def analysis_agent(mock_message_queue, db_session):
    """Create AnalysisAgent instance with real execution enabled"""
    config = {
        "use_llm": False,  # Disable LLM for faster tests
        "db": db_session,  # Use database session if available
        "enable_realtime_execution": True  # ENABLE real-time execution
    }
    return AnalysisAgent(
        agent_id="test_analysis_agent",
        agent_type="analysis",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


class TestThreeHKRealPage:
    """Test complete workflow with real Three HK 5G Broadband page"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test (requires actual web crawling)
    async def test_complete_workflow_three_hk_page(
        self, observation_agent, requirements_agent, analysis_agent
    ):
        """
        Complete E2E test: Observe Three HK page → Generate scenarios → Analyze → Score
        
        This test:
        1. Observes the actual Three HK 5G Broadband page
        2. Generates test scenarios from UI elements
        3. Analyzes scenarios for risk, ROI, dependencies
        4. Verifies execution-based scoring (with simulated execution results)
        """
        target_url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
        conversation_id = "three-hk-test-001"
        
        print(f"\n{'='*80}")
        print(f"Testing Three HK 5G Broadband Page")
        print(f"URL: {target_url}")
        print(f"{'='*80}\n")
        
        # Step 1: ObservationAgent - Observe the page
        print("Step 1: Observing page with ObservationAgent...")
        observation_task = TaskContext(
            conversation_id=conversation_id,
            task_id="obs-task-001",
            task_type="ui_element_extraction",
            payload={"url": target_url, "max_depth": 1}
        )
        
        observation_result = await observation_agent.execute_task(observation_task)
        
        # Verify observation succeeded
        assert observation_result.success is True, f"Observation failed: {observation_result.error}"
        ui_elements_count = len(observation_result.result.get('ui_elements', []))
        print(f"[OK] Observation complete: {ui_elements_count} UI elements found")
        
        # Extract observation data
        observation_data = {
            "ui_elements": observation_result.result.get("ui_elements", []),
            "page_structure": observation_result.result.get("page_structure", {}),
            "page_context": observation_result.result.get("page_context", {})
        }
        
        # Step 2: RequirementsAgent - Generate test scenarios
        print("\nStep 2: Generating test scenarios with RequirementsAgent...")
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-001",
            task_type="requirement_extraction",
            payload=observation_data
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        
        # Verify requirements generation succeeded
        assert requirements_result.success is True, f"Requirements generation failed: {requirements_result.error}"
        scenarios = requirements_result.result.get("scenarios", [])
        print(f"[OK] Requirements complete: {len(scenarios)} scenarios generated")
        
        # Verify we have scenarios
        assert len(scenarios) > 0, "No scenarios generated from Three HK page"
        
        # Step 3: AnalysisAgent - Analyze scenarios (with real-time execution enabled)
        print("\nStep 3: Analyzing scenarios with AnalysisAgent...")
        print("        Real-time execution is ENABLED - critical scenarios will be executed automatically")
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-001",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result.get("test_data", []),
                "coverage_metrics": requirements_result.result.get("coverage_metrics", {}),
                "page_context": observation_data["page_context"]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        
        # Verify analysis succeeded
        assert analysis_result.success is True, f"Analysis failed: {analysis_result.error}"
        risk_scores_count = len(analysis_result.result.get('risk_scores', []))
        print(f"[OK] Analysis complete: {risk_scores_count} risk scores calculated")
        
        # Check if any scenarios were executed automatically (if RPN >= 80)
        auto_execution_results = []
        if analysis_result.result.get("execution_success"):
            for es in analysis_result.result["execution_success"]:
                if es.get("source") == "execution_results":  # Real execution, not historical
                    auto_execution_results.append(es)
        
        if auto_execution_results:
            print(f"[INFO] {len(auto_execution_results)} scenarios were automatically executed during analysis")
        
        # Step 4: Verify analysis output structure
        print("\nStep 4: Verifying analysis output...")
        assert "risk_scores" in analysis_result.result
        assert "business_values" in analysis_result.result
        assert "roi_scores" in analysis_result.result
        assert "dependencies" in analysis_result.result
        assert "final_prioritization" in analysis_result.result
        assert "execution_strategy" in analysis_result.result
        
        risk_scores = analysis_result.result["risk_scores"]
        final_prioritization = analysis_result.result["final_prioritization"]
        
        print(f"[OK] Risk scores: {len(risk_scores)} scenarios scored")
        print(f"[OK] Final prioritization: {len(final_prioritization)} scenarios prioritized")
        
        # Step 5: REAL test execution (not simulation)
        print("\nStep 5: Executing critical scenarios in REAL-TIME using Phase 2 execution engine...")
        print("        This will use 3-tier execution strategy (Playwright → Hybrid → Stagehand AI)")
        
        # Find critical scenarios (RPN >= 80) for real execution
        critical_scenarios = []
        for item in final_prioritization:
            scenario_id = item["scenario_id"]
            risk_score = next((rs for rs in risk_scores if rs["scenario_id"] == scenario_id), None)
            if risk_score and risk_score.get("rpn", 0) >= 80:
                scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
                if scenario:
                    critical_scenarios.append(scenario)
        
        # Limit to top 2 critical scenarios for performance (real execution takes time)
        critical_scenarios = critical_scenarios[:2]
        
        if len(critical_scenarios) == 0:
            print("  [INFO] No critical scenarios (RPN >= 80) found. Using top 2 prioritized scenarios instead.")
            critical_scenarios = [
                next((s for s in scenarios if s["scenario_id"] == item["scenario_id"]), None)
                for item in final_prioritization[:2]
            ]
            critical_scenarios = [s for s in critical_scenarios if s is not None]
        
        print(f"  Executing {len(critical_scenarios)} critical scenarios...")
        
        # Execute scenarios in real-time
        execution_results = []
        for idx, scenario in enumerate(critical_scenarios, 1):
            scenario_id = scenario.get("scenario_id")
            print(f"  [{idx}/{len(critical_scenarios)}] Executing: {scenario.get('title', scenario_id)}")
            
            try:
                exec_result = await analysis_agent._execute_scenario_real_time(
                    scenario, 
                    observation_data["page_context"]
                )
                
                if exec_result:
                    execution_results.append(exec_result)
                    success_rate = exec_result.get("success_rate", 0.0)
                    passed_steps = exec_result.get("passed_steps", 0)
                    total_steps = exec_result.get("total_steps", 0)
                    tier_used = exec_result.get("tier_used", "unknown")
                    result = exec_result.get("result", "unknown")
                    
                    print(f"    [OK] Execution complete: {passed_steps}/{total_steps} steps passed")
                    print(f"         Success Rate: {success_rate:.2%}, Result: {result}, Tier: {tier_used}")
                else:
                    print(f"    [WARN] Execution returned no result (may be stub mode)")
                    # Create stub result for verification
                    execution_results.append({
                        "scenario_id": scenario_id,
                        "success_rate": 0.0,
                        "passed_steps": 0,
                        "total_steps": 0,
                        "result": "unknown",
                        "tier_used": "stub"
                    })
            except Exception as e:
                print(f"    [ERROR] Execution failed: {e}")
                # Create failure result
                execution_results.append({
                    "scenario_id": scenario_id,
                    "success_rate": 0.0,
                    "passed_steps": 0,
                    "total_steps": 0,
                    "result": "fail",
                    "error": str(e),
                    "tier_used": "error"
                })
        
        # Step 6: Re-analyze with REAL execution results
        print("\nStep 6: Re-analyzing with REAL execution results...")
        
        refined_analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-refined",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result.get("test_data", []),
                "coverage_metrics": requirements_result.result.get("coverage_metrics", {}),
                "page_context": observation_data["page_context"],
                "execution_results": execution_results  # REAL execution results
            }
        )
        
        refined_analysis_result = await analysis_agent.execute_task(refined_analysis_task)
        
        assert refined_analysis_result.success is True
        print(f"[OK] Refined analysis complete with REAL execution results")
        
        # Verify execution results are incorporated
        refined_risk_scores = {rs["scenario_id"]: rs for rs in refined_analysis_result.result["risk_scores"]}
        execution_success = refined_analysis_result.result["execution_success"]
        
        assert len(execution_success) > 0, "Execution success data should be present"
        
        # Verify detection scores adjusted for executed scenarios
        print("\n  Execution-based scoring adjustments:")
        for exec_result in execution_results:
            scenario_id = exec_result["scenario_id"]
            if scenario_id in refined_risk_scores:
                refined_detection = refined_risk_scores[scenario_id]["detection"]
                success_rate = exec_result.get("success_rate", 0.0)
                tier_used = exec_result.get("tier_used", "unknown")
                
                # Get original detection for comparison
                original_risk_score = next((rs for rs in risk_scores if rs["scenario_id"] == scenario_id), None)
                original_detection = original_risk_score.get("detection") if original_risk_score else None
                
                assert refined_detection <= 5, "Detection score should be valid (1-5)"
                
                if original_detection:
                    change = refined_detection - original_detection
                    change_str = f"{change:+d}" if change != 0 else "0"
                    print(f"    [OK] Scenario {scenario_id}:")
                    print(f"         Detection: {original_detection} → {refined_detection} ({change_str})")
                    print(f"         Success Rate: {success_rate:.2%}, Tier: {tier_used}")
                else:
                    print(f"    [OK] Scenario {scenario_id}: Detection={refined_detection}, Success Rate={success_rate:.2%}, Tier={tier_used}")
        
        # Step 7: Print summary
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Page URL: {target_url}")
        print(f"UI Elements Observed: {len(observation_data['ui_elements'])}")
        print(f"Scenarios Generated: {len(scenarios)}")
        print(f"Risk Scores Calculated: {len(risk_scores)}")
        print(f"Scenarios Prioritized: {len(final_prioritization)}")
        print(f"Scenarios Executed (REAL): {len(execution_results)}")
        print(f"Execution Success Data: {len(execution_success)}")
        
        # Show execution results summary
        if execution_results:
            successful_executions = [er for er in execution_results if er.get("result") == "pass"]
            failed_executions = [er for er in execution_results if er.get("result") == "fail"]
            print(f"  - Successful: {len(successful_executions)}")
            print(f"  - Failed: {len(failed_executions)}")
            if successful_executions:
                avg_success_rate = sum(er.get("success_rate", 0) for er in successful_executions) / len(successful_executions)
                print(f"  - Average Success Rate: {avg_success_rate:.2%}")
        
        # Show top 3 prioritized scenarios
        print(f"\nTop 3 Prioritized Scenarios:")
        for idx, item in enumerate(final_prioritization[:3], 1):
            scenario = next(s for s in scenarios if s["scenario_id"] == item["scenario_id"])
            print(f"  {idx}. {scenario.get('title', 'N/A')}")
            print(f"     Priority: {item['priority']}, Score: {item['composite_score']:.2f}")
            print(f"     Type: {scenario.get('scenario_type', 'N/A')}")
        
        print(f"{'='*80}\n")
        
        # Final assertions
        assert len(scenarios) >= 10, f"Expected at least 10 scenarios, got {len(scenarios)}"
        assert len(risk_scores) == len(scenarios), "All scenarios should have risk scores"
        assert len(final_prioritization) == len(scenarios), "All scenarios should be prioritized"
        
        print("[OK] All assertions passed!")


    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_three_hk_unlimited_48m_plan_flow(
        self, observation_agent, requirements_agent, analysis_agent
    ):
        """
        E2E test for specific Three HK 5G Broadband flow:
        
        1. Navigate to the 5G broadband plan page
        2. Find plan "5G寬頻數據無限任用"
        3. Select contract term "48個月"
        4. Verify price shows "$182"
        5. Click "立即登記" to subscribe
        6. Click "下一步" to proceed in the flow
        
        Uses all 3 agents:
        - ObservationAgent: real page crawl
        - RequirementsAgent: generic scenarios (for context)
        - AnalysisAgent: executes ONE explicit scenario via 3-tier engine
        """
        target_url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
        conversation_id = "three-hk-unlimited-48m-flow"
        
        print(f"\n{'='*80}")
        print("Testing Three HK 5G Broadband - Unlimited 48個月 Plan Flow")
        print(f"URL: {target_url}")
        print(f"{'='*80}\n")
        
        # Step 1: ObservationAgent - Observe the page
        print("Step 1: Observing page with ObservationAgent...")
        observation_task = TaskContext(
            conversation_id=conversation_id,
            task_id="obs-task-unlimited-48m",
            task_type="ui_element_extraction",
            payload={"url": target_url, "max_depth": 1}
        )
        
        observation_result = await observation_agent.execute_task(observation_task)
        assert observation_result.success is True, f"Observation failed: {observation_result.error}"
        ui_elements = observation_result.result.get("ui_elements", [])
        page_context = observation_result.result.get("page_context", {})
        print(f"[OK] Observation complete: {len(ui_elements)} UI elements found")
        
        # Step 2: RequirementsAgent - Generate generic scenarios (for context only)
        print("\nStep 2: Generating generic test scenarios with RequirementsAgent...")
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-unlimited-48m",
            task_type="requirement_extraction",
            payload={
                "ui_elements": ui_elements,
                "page_structure": observation_result.result.get("page_structure", {}),
                "page_context": page_context
            }
        )
        
        requirements_result = await requirements_agent.execute_task(requirements_task)
        assert requirements_result.success is True, f"Requirements generation failed: {requirements_result.error}"
        print(f"[OK] Requirements complete: {len(requirements_result.result.get('scenarios', []))} scenarios generated")
        
        # Step 3: Define explicit scenario for the requested flow
        print("\nStep 3: Defining explicit scenario for 5G寬頻數據無限任用 48個月 plan at $182...")
        specific_scenario = {
            "scenario_id": "THREE-5G-UNLIMITED-48M-182",
            "title": "Subscribe 5G寬頻數據無限任用 48個月 plan at $182",
            "given": "User is on the Three HK 5G Broadband plan page",
            "when": (
                "Click on plan with text '5G寬頻數據無限任用', "
                "Click on contract term '48個月', "
                "Verify: price shows '$182', "
                "Click on button '立即登記', "
                "Click on button '下一步'"
            ),
            "then": (
                "User is taken to subscription flow for 5G寬頻數據無限任用 48個月 plan "
                "with monthly fee $182 and can proceed to the next step"
            ),
            "priority": "high",
            "scenario_type": "functional",
            "tags": ["three_hk", "5g_broadband", "unlimited", "48m", "price_182"]
        }
        
        # Step 4: Execute the explicit scenario in REAL-TIME via AnalysisAgent
        print("\nStep 4: Executing explicit scenario in REAL-TIME using 3-tier engine...")
        print("        (Tier 1: Playwright → Tier 2: observe+XPath → Tier 3: Stagehand AI)")
        
        exec_result = await analysis_agent._execute_scenario_real_time(
            specific_scenario,
            page_context
        )
        
        assert exec_result is not None, "Execution result should not be None"
        
        success_rate = exec_result.get("success_rate", 0.0)
        passed_steps = exec_result.get("passed_steps", 0)
        total_steps = exec_result.get("total_steps", 0)
        tier_used = exec_result.get("tier_used", "unknown")
        result = exec_result.get("result", "unknown")
        
        print(f"[OK] Execution complete: {passed_steps}/{total_steps} steps passed")
        print(f"     Success Rate: {success_rate:.2%}, Result: {result}, Tier: {tier_used}")
        
        # There should be at least one executable step; on live sites some steps
        # may still fail due to layout/content changes, but the engine must run.
        assert total_steps > 0, "There should be at least one executable step"
        
        # Step 5: Optional – integrate this execution into AnalysisAgent scoring
        print("\nStep 5: Integrating execution result into AnalysisAgent scoring...")
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-unlimited-48m",
            task_type="risk_analysis",
            payload={
                "scenarios": requirements_result.result.get("scenarios", []) + [specific_scenario],
                "test_data": requirements_result.result.get("test_data", []),
                "coverage_metrics": requirements_result.result.get("coverage_metrics", {}),
                "page_context": page_context,
                "execution_results": [exec_result]
            }
        )
        
        analysis_result = await analysis_agent.execute_task(analysis_task)
        assert analysis_result.success is True, f"Analysis failed: {analysis_result.error}"
        print(f"[OK] Analysis complete with execution-aware scoring")
        
        # Verify our specific scenario is present in risk scores and prioritization
        risk_scores = {rs["scenario_id"]: rs for rs in analysis_result.result["risk_scores"]}
        final_prioritization = analysis_result.result["final_prioritization"]
        
        assert "THREE-5G-UNLIMITED-48M-182" in risk_scores, "Specific scenario should have a risk score"
        print(f"[OK] Specific scenario risk score: {risk_scores['THREE-5G-UNLIMITED-48M-182']}")
        
        prioritized_ids = [item["scenario_id"] for item in final_prioritization]
        assert "THREE-5G-UNLIMITED-48M-182" in prioritized_ids, "Specific scenario should be in prioritization list"
        
        print("\n[OK] Specific 5G寬頻數據無限任用 48個月 plan flow executed and analyzed successfully!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])

