"""
Test ObservationAgent with Three HK 5G Broadband page
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from agents.observation_agent import ObservationAgent
from messaging.message_bus_stub import MessageBusStub
from agents.base_agent import TaskContext

async def test_three_hk_website():
    print("=" * 60)
    print("Testing ObservationAgent with Three HK 5G Broadband Page")
    print("=" * 60)
    
    # Create agent
    message_bus = MessageBusStub()
    agent = ObservationAgent(
        message_queue=message_bus,
        config={
            "use_llm": True,  # Enable LLM enhancement
            "max_depth": 1,   # Just analyze main page
            "timeout": 30000  # 30 second timeout
        }
    )
    
    # Company website URL
    url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
    
    # Create task
    task = TaskContext(
        task_id="three-hk-test",
        task_type="web_crawling",
        payload={
            "url": url,
            "max_depth": 1,
            "extract_forms": True
        },
        conversation_id="test-session"
    )
    
    # Check if agent can handle
    can_handle, confidence = await agent.can_handle(task)
    print(f"\n1. Can Handle Task?")
    print(f"   Can handle: {can_handle}")
    print(f"   Confidence: {confidence}")
    
    if not can_handle:
        print("   ❌ Agent cannot handle this task")
        return
    
    # Execute task
    print(f"\n2. Executing Task...")
    print(f"   URL: {url}")
    print(f"   Crawling Three HK website...")
    
    result = await agent.execute_task(task)
    
    # Display results
    print(f"\n3. Results:")
    print(f"   Success: {result.success}")
    print(f"   Confidence: {result.confidence}")
    
    if result.success:
        data = result.result
        summary = data.get("summary", {})
        
        print(f"\n   📊 Summary:")
        print(f"   - Pages Crawled: {summary.get('pages', 0)}")
        print(f"   - Total UI Elements: {summary.get('total_elements', 0)}")
        print(f"   - Buttons: {summary.get('buttons', 0)}")
        print(f"   - Inputs: {summary.get('inputs', 0)}")
        print(f"   - Links: {summary.get('links', 0)}")
        print(f"   - Forms: {summary.get('forms', 0)}")
        
        # Show LLM analysis if available
        llm_analysis = data.get("llm_analysis", {})
        if llm_analysis.get("used"):
            print(f"\n   🤖 LLM Enhancement:")
            print(f"   - LLM Elements Found: {llm_analysis.get('elements_found', 0)}")
            print(f"   - Playwright Baseline: {summary.get('playwright_elements', 0)}")
            print(f"   - Total with LLM: {summary.get('total_elements', 0)}")
            
            page_patterns = llm_analysis.get("page_patterns", {})
            if page_patterns:
                print(f"\n   📋 Page Analysis:")
                print(f"   - Page Type: {page_patterns.get('page_type', 'unknown')}")
                print(f"   - Framework: {page_patterns.get('framework', 'unknown')}")
                print(f"   - Complexity: {page_patterns.get('complexity', 'unknown')}")
            
            missed = llm_analysis.get("missed_by_playwright", [])
            if missed:
                print(f"\n   🔍 Elements Missed by Playwright (found by LLM):")
                for item in missed[:5]:  # Show first 5
                    print(f"   - {item.get('element', 'Unknown')}")
                    print(f"     Reason: {item.get('reason', 'N/A')}")
                if len(missed) > 5:
                    print(f"   ... and {len(missed) - 5} more")
        else:
            print(f"\n   ℹ️ LLM enhancement not available (stub mode)")
            print(f"      Install cerebras-cloud-sdk and set CEREBRAS_API_KEY to enable")
        
        # Show sample elements
        ui_elements = data.get("ui_elements", [])
        if ui_elements:
            print(f"\n   📝 Sample UI Elements (first 10):")
            for elem in ui_elements[:10]:
                elem_type = elem.get("type", "unknown")
                text = elem.get("text", "")[:50]  # Truncate long text
                selector = elem.get("selector", "")[:60]
                print(f"   - [{elem_type}] {text}")
                print(f"     Selector: {selector}")
            if len(ui_elements) > 10:
                print(f"   ... and {len(ui_elements) - 10} more elements")
        
        # Show forms
        forms = data.get("forms", [])
        if forms:
            print(f"\n   📋 Forms Found:")
            for form in forms:
                form_id = form.get("form_id", "unknown")
                fields = form.get("fields", [])
                print(f"   - Form: {form_id}")
                print(f"     Fields: {len(fields)}")
                for field in fields[:3]:
                    print(f"       • {field.get('name', 'unknown')} ({field.get('type', 'unknown')})")
                if len(fields) > 3:
                    print(f"       ... and {len(fields) - 3} more fields")
    else:
        print(f"   ❌ Task failed")
        if result.error:
            print(f"   Error: {result.error}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_three_hk_website())
