"""
End-to-End Test: ObservationAgent → RequirementsAgent
Tests the complete pipeline with real Three HK website
"""
import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from messaging.message_bus_stub import MessageBusStub
from agents.base_agent import TaskContext

async def test_observation_to_requirements_pipeline():
    print("=" * 80)
    print("END-TO-END TEST: ObservationAgent → RequirementsAgent")
    print("Testing with Real Three HK 5G Broadband Page")
    print("=" * 80)
    
    # ==================== STAGE 1: ObservationAgent ====================
    print("\n" + "=" * 80)
    print("STAGE 1: ObservationAgent - Web Crawling & UI Element Extraction")
    print("=" * 80)
    
    message_bus = MessageBusStub()
    observation_agent = ObservationAgent(
        message_queue=message_bus,
        config={
            "use_llm": True,  # Enable LLM enhancement
            "max_depth": 1,   # Just analyze main page
            "timeout": 30000  # 30 second timeout
        }
    )
    
    # Company website URL
    url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
    
    # Create observation task
    observation_task = TaskContext(
        conversation_id="e2e-test-session",
        task_id="observation-three-hk",
        task_type="web_crawling",
        payload={
            "url": url,
            "max_depth": 1,
            "extract_forms": True
        }
    )
    
    print(f"\n📍 Target URL:")
    print(f"   {url}")
    print(f"\n⏳ Crawling website...")
    
    observation_result = await observation_agent.execute_task(observation_task)
    
    if not observation_result.success:
        print(f"\n❌ ObservationAgent Failed!")
        print(f"   Error: {observation_result.error}")
        return
    
    # Display ObservationAgent results
    obs_data = observation_result.result
    summary = obs_data.get("summary", {})
    ui_elements = obs_data.get("ui_elements", [])
    llm_analysis = obs_data.get("llm_analysis", {})
    
    # Calculate actual counts
    total_elements = len(ui_elements)
    button_count = len([e for e in ui_elements if e.get("type") == "button"])
    input_count = len([e for e in ui_elements if e.get("type") == "input"])
    link_count = len([e for e in ui_elements if e.get("type") == "link"])
    form_count = len(obs_data.get("forms", []))

    print(f"\n✅ ObservationAgent Complete!")
    print(f"   Confidence: {observation_result.confidence:.2f}")
    print(f"   Execution Time: {observation_result.execution_time_seconds:.1f}s")

    print(f"\n📊 Observation Summary:")
    print(f"   - Pages Crawled: 1")  # Main page successfully crawled
    print(f"   - Total UI Elements: {total_elements}")
    print(f"   - Buttons: {button_count}")
    print(f"   - Inputs: {input_count}")
    print(f"   - Links: {link_count}")
    print(f"   - Forms: {form_count}")
    
    # Show LLM analysis
    if llm_analysis.get("used"):
        print(f"\n🤖 LLM Enhancement:")
        print(f"   - Elements Found by LLM: {llm_analysis.get('elements_found', 0)}")
        print(f"   - Playwright Baseline: {summary.get('playwright_elements', 0)}")
        
        page_patterns = llm_analysis.get("page_patterns", {})
        if page_patterns:
            print(f"\n📋 Page Analysis:")
            print(f"   - Page Type: {page_patterns.get('page_type', 'unknown')}")
            print(f"   - Framework: {page_patterns.get('framework', 'unknown')}")
            print(f"   - Complexity: {page_patterns.get('complexity', 'unknown')}")
    
    # ==================== STAGE 2: RequirementsAgent ====================
    print("\n" + "=" * 80)
    print("STAGE 2: RequirementsAgent - Test Scenario Generation")
    print("=" * 80)
    
    requirements_agent = RequirementsAgent(
        agent_id="requirements_agent_e2e",
        agent_type="requirements",
        priority=5,
        message_queue=message_bus,
        config={"use_llm": True}  # Enable LLM for higher quality scenarios
    )
    
    # Prepare payload for RequirementsAgent (from ObservationAgent output)
    requirements_payload = {
        "ui_elements": obs_data.get("ui_elements", []),
        "page_structure": {
            "url": url,
            "title": obs_data.get("page_title", "Three HK 5G Broadband"),
            "forms": [f.get("form_id") for f in obs_data.get("forms", [])],
            "navigation": []  # Extract from ui_elements if needed
        },
        "page_context": llm_analysis.get("page_patterns", {
            "framework": "unknown",
            "page_type": "pricing",
            "complexity": "medium"
        })
    }
    
    # Create requirements task
    requirements_task = TaskContext(
        conversation_id="e2e-test-session",
        task_id="requirements-three-hk",
        task_type="requirement_extraction",
        payload=requirements_payload
    )
    
    print(f"\n⏳ Generating test scenarios...")
    print(f"   Input: {len(requirements_payload['ui_elements'])} UI elements")
    
    requirements_result = await requirements_agent.execute_task(requirements_task)
    
    if not requirements_result.success:
        print(f"\n❌ RequirementsAgent Failed!")
        print(f"   Error: {requirements_result.error}")
        return
    
    # Display RequirementsAgent results
    req_data = requirements_result.result
    scenarios = req_data.get("scenarios", [])
    coverage = req_data.get("coverage_metrics", {})
    quality = req_data.get("quality_indicators", {})
    
    print(f"\n✅ RequirementsAgent Complete!")
    print(f"   Confidence: {requirements_result.confidence:.2f}")
    print(f"   Execution Time: {requirements_result.execution_time_seconds:.1f}s")
    
    print(f"\n📊 Requirements Summary:")
    print(f"   - Total Scenarios: {len(scenarios)}")
    print(f"   - UI Coverage: {coverage.get('ui_coverage_percent', 0):.1f}%")
    print(f"   - Completeness: {quality.get('completeness', 0):.1f}%")
    
    # Scenarios by type
    scenarios_by_type = coverage.get("scenarios_by_type", {})
    if scenarios_by_type:
        print(f"\n📋 Scenarios by Type:")
        for scenario_type, count in scenarios_by_type.items():
            print(f"   - {scenario_type}: {count}")
    
    # Scenarios by priority
    priority_dist = quality.get("priority_distribution", {})
    if priority_dist:
        print(f"\n🎯 Priority Distribution:")
        for priority, count in priority_dist.items():
            print(f"   - {priority}: {count}")
    
    # Show sample scenarios
    if scenarios:
        print(f"\n📝 Sample Scenarios (first 5):")
        for i, scenario in enumerate(scenarios[:5], 1):
            print(f"\n   {i}. [{scenario.get('scenario_type', 'unknown').upper()}] "
                  f"{scenario.get('title', 'Unknown')}")
            print(f"      ID: {scenario.get('scenario_id', 'N/A')}")
            print(f"      Priority: {scenario.get('priority', 'N/A')}")
            print(f"      Confidence: {scenario.get('confidence', 0):.2f}")
            print(f"      Given: {scenario.get('given', 'N/A')[:80]}...")
            print(f"      When: {scenario.get('when', 'N/A')[:80]}...")
            print(f"      Then: {scenario.get('then', 'N/A')[:80]}...")
        
        if len(scenarios) > 5:
            print(f"\n   ... and {len(scenarios) - 5} more scenarios")
    
    # ==================== PIPELINE SUMMARY ====================
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ End-to-End Test Complete!")
    print(f"\n📊 Pipeline Statistics:")
    print(f"   ObservationAgent:")
    print(f"   - UI Elements Extracted: {total_elements}")
    print(f"   - Execution Time: {observation_result.execution_time_seconds:.1f}s")
    print(f"   - Confidence: {observation_result.confidence:.2f}")
    
    print(f"\n   RequirementsAgent:")
    print(f"   - Test Scenarios Generated: {len(scenarios)}")
    print(f"   - Execution Time: {requirements_result.execution_time_seconds:.1f}s")
    print(f"   - Confidence: {requirements_result.confidence:.2f}")
    print(f"   - UI Coverage: {coverage.get('ui_coverage_percent', 0):.1f}%")
    
    total_time = observation_result.execution_time_seconds + requirements_result.execution_time_seconds
    print(f"\n   Total Pipeline Time: {total_time:.1f}s")
    
    # Token usage if available
    if "token_usage" in requirements_result.metadata:
        token_usage = requirements_result.metadata["token_usage"]
        if isinstance(token_usage, dict):
            print(f"\n   Token Usage (Requirements):")
            print(f"   - Estimated Tokens: {token_usage.get('total_estimated_tokens', 0)}")
        else:
            print(f"\n   Token Usage (Requirements): {token_usage}")
    
    print(f"\n🎉 Pipeline successfully generated {len(scenarios)} test scenarios from "
          f"{total_elements} UI elements!")
    
    # Save results to file for inspection
    output_file = Path(__file__).parent / "e2e_test_results.json"
    output_data = {
        "observation": {
            "success": observation_result.success,
            "confidence": observation_result.confidence,
            "execution_time": observation_result.execution_time_seconds,
            "summary": summary,
            "total_elements": len(obs_data.get("ui_elements", []))
        },
        "requirements": {
            "success": requirements_result.success,
            "confidence": requirements_result.confidence,
            "execution_time": requirements_result.execution_time_seconds,
            "total_scenarios": len(scenarios),
            "coverage": coverage,
            "quality": quality,
            "scenarios": scenarios[:10]  # Save first 10 scenarios
        },
        "pipeline": {
            "total_time": total_time,
            "url": url
        }
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full results saved to: {output_file}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_observation_to_requirements_pipeline())
