"""
Quick test script for ObservationAgent (Web Application Observer)
Tests web crawling and UI element extraction functionality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from agents.observation_agent import ObservationAgent
from agents.base_agent import TaskContext
from messaging.message_bus_stub import MessageBusStub


async def test_observation_agent():
    """Test ObservationAgent functionality (stub mode without Playwright)."""
    print("=" * 60)
    print("Testing ObservationAgent (Web Application Observer)")
    print("=" * 60)
    
    # Create dependencies
    message_queue = MessageBusStub()
    
    # Create agent
    agent = ObservationAgent(
        message_queue=message_queue,
        agent_id="test-observation-agent",
        priority=8
    )
    
    print("\n1. Agent Capabilities:")
    for cap in agent.capabilities:
        print(f"   - {cap.name} v{cap.version} (threshold: {cap.confidence_threshold})")
        print(f"     Description: {cap.description}")
    
    # Create task to crawl a web application
    task = TaskContext(
        task_id="test-001",
        task_type="web_crawling",
        payload={
            "url": "https://example.com",
            "max_depth": 2,
            "auth": None  # No authentication needed
        },
        conversation_id="conv-001",
        priority=5
    )
    
    print("\n2. Can Handle Task?")
    can_handle, confidence = await agent.can_handle(task)
    print(f"   Can handle: {can_handle}")
    print(f"   Confidence: {confidence}")
    
    if can_handle:
        print("\n3. Executing Task (STUB MODE - Playwright not installed)...")
        result = await agent.execute_task(task)
        
        print(f"\n4. Results:")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.confidence}")
        
        if result.success:
            data = result.result
            
            print(f"\n   Summary:")
            print(f"   - Pages Crawled: {data['pages_crawled']}")
            print(f"   - Total UI Elements: {data['total_elements']}")
            print(f"   - Total Forms: {data['total_forms']}")
            print(f"   - Buttons: {data['summary']['buttons']}")
            print(f"   - Inputs: {data['summary']['inputs']}")
            print(f"   - Links: {data['summary']['links']}")
            print(f"   - Forms: {data['summary']['forms']}")
            
            print(f"\n   Pages Found:")
            for page in data['pages']:
                print(f"   - {page['title']} ({page['url']}) - Status: {page['status_code']}")
            
            print(f"\n   UI Elements Sample:")
            for elem in data['ui_elements'][:5]:
                elem_text = elem.get('text', elem.get('selector', 'N/A'))
                print(f"   - [{elem['type']}] {elem_text} on {elem.get('page_url', 'unknown page')}")
            
            print(f"\n   Forms Found:")
            for form in data['forms']:
                fields_list = [f"{f['name']} ({f['type']})" for f in form['fields']]
                fields_str = ', '.join(fields_list)
                print(f"   - {form['method']} {form['action']}")
                print(f"     Fields: {fields_str}")
                print(f"     Page: {form.get('page_url', 'unknown')}")
            
            if '_note' in data:
                print(f"\n   NOTE: {data['_note']}")
        else:
            print(f"   Error: {result.error}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nTo use real Playwright functionality:")
    print("  1. pip install playwright")
    print("  2. playwright install")
    print("  3. Run this test again")


async def test_invalid_url():
    """Test ObservationAgent with invalid URL."""
    print("\n" + "=" * 60)
    print("Testing ObservationAgent with Invalid URL")
    print("=" * 60)
    
    # Create dependencies
    message_queue = MessageBusStub()
    
    # Create agent
    agent = ObservationAgent(
        message_queue=message_queue
    )
    
    # Invalid URL
    task = TaskContext(
        task_id="test-002",
        task_type="web_crawling",
        payload={
            "url": "not-a-valid-url",
            "max_depth": 2
        },
        conversation_id="conv-002",
        priority=5
    )
    
    print("\n1. Can Handle Invalid URL?")
    can_handle, confidence = await agent.can_handle(task)
    print(f"   Can handle: {can_handle}")
    print(f"   Confidence: {confidence}")
    
    if not can_handle:
        print("   ✅ Correctly rejected invalid URL")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_observation_agent())
    asyncio.run(test_invalid_url())
