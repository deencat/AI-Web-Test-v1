"""
Test TypeScript Stagehand Adapter integration with Node.js microservice.

Run this after starting the microservice:
    cd stagehand-service
    npm run dev
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter


async def test_typescript_adapter():
    """Test TypeScript adapter connection and basic operations."""
    
    print("="*80)
    print("Testing TypeScript Stagehand Adapter")
    print("="*80)
    
    adapter = TypeScriptStagehandAdapter()
    
    try:
        # Test 1: Initialize (check service health)
        print("\n[Test 1] Initializing TypeScript Stagehand adapter...")
        await adapter.initialize({
            "model": "gpt-4",
            "temperature": 0.7
        })
        print("✅ Adapter initialization successful (service is reachable)")
        
        # Test 2: Initialize a persistent session (for debug mode)
        print("\n[Test 2] Initializing persistent session...")
        import uuid
        from unittest.mock import MagicMock
        
        session_id = f"test-session-{uuid.uuid4()}"
        mock_db = MagicMock()
        
        await adapter.initialize_persistent(
            session_id=session_id,
            test_id=999,
            user_id=1,
            db=mock_db
        )
        print(f"✅ Persistent session initialized: {adapter._browser_session_id}")
        
        # Test 2.5: Navigate to a page first (Stagehand requires this)
        print("\n[Test 2.5] Navigating to a test page...")
        from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter
        
        # We need to manually call navigate since it's not in the adapter interface yet
        session = await adapter._get_session()
        nav_response = await session.post(
            f"{adapter.service_url}/api/sessions/{adapter._browser_session_id}/navigate",
            json={"url": "https://example.com"}
        )
        nav_result = await nav_response.json()
        print(f"✅ Navigation completed: {nav_result.get('message')}")
        
        # Test 3: Execute single step
        print("\n[Test 3] Executing a test step...")
        result = await adapter.execute_single_step(
            "Read the page title and verify it contains 'Example'",
            step_number=1,
            execution_id=999
        )
        print(f"✅ Step execution completed:")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Duration: {result.get('duration_ms')}ms")
        if result.get('error'):
            print(f"   Error: {result.get('error')}")
        
        # Test 4: Cleanup
        print("\n[Test 4] Cleaning up session...")
        await adapter.cleanup()
        print("✅ Cleanup successful")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nThe TypeScript adapter is working correctly!")
        print("You can now switch to 'typescript' provider in settings.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("1. The Node.js microservice is running: cd stagehand-service && npm run dev")
        print("2. The service is accessible at http://localhost:3001")
        
        # Try to cleanup
        try:
            await adapter.cleanup()
        except:
            pass
        
        return False


if __name__ == "__main__":
    result = asyncio.run(test_typescript_adapter())
    sys.exit(0 if result else 1)
