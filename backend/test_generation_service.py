"""Test the test generation service."""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.test_generation import TestGenerationService
from app.core.config import settings


async def test_basic_generation():
    """Test basic test case generation."""
    print("=" * 80)
    print("Testing Test Generation Service")
    print("=" * 80)
    
    if not settings.OPENROUTER_API_KEY:
        print("\nERROR: OPENROUTER_API_KEY not found!")
        return False
    
    print(f"\nModel: {settings.OPENROUTER_MODEL}")
    print("\n" + "-" * 80)
    
    service = TestGenerationService()
    
    # Test 1: Simple requirement
    print("\n[Test 1] Generating tests for login functionality...")
    print("-" * 80)
    
    try:
        result = await service.generate_tests(
            requirement="User login with username and password",
            test_type="e2e",
            num_tests=3
        )
        
        print(f"✅ SUCCESS - Generated {len(result['test_cases'])} test cases")
        print(f"\nMetadata:")
        print(f"  Model: {result['metadata']['model']}")
        print(f"  Tokens: {result['metadata']['tokens']}")
        print(f"\nTest Cases:")
        
        for i, test in enumerate(result['test_cases'], 1):
            print(f"\n{i}. {test['title']}")
            print(f"   Type: {test.get('test_type', 'N/A')}")
            print(f"   Priority: {test.get('priority', 'N/A')}")
            print(f"   Description: {test.get('description', 'N/A')}")
            print(f"   Steps: {len(test.get('steps', []))} steps")
            print(f"   Expected: {test.get('expected_result', 'N/A')[:60]}...")
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 2: Page-specific generation
    print("\n" + "-" * 80)
    print("\n[Test 2] Generating tests for a specific page...")
    print("-" * 80)
    
    try:
        result = await service.generate_tests_for_page(
            page_name="Dashboard",
            page_description="""
            The dashboard displays:
            - Test execution statistics (total, passed, failed)
            - Recent test runs with status
            - Quick actions (Run All Tests, View Reports)
            - System health indicators
            """,
            num_tests=4
        )
        
        print(f"✅ SUCCESS - Generated {len(result['test_cases'])} test cases")
        print(f"\nTest Cases:")
        
        for i, test in enumerate(result['test_cases'], 1):
            print(f"\n{i}. {test['title']}")
            print(f"   Priority: {test.get('priority', 'N/A')}")
            steps = test.get('steps', [])
            print(f"   Steps ({len(steps)}):")
            for step in steps[:3]:  # Show first 3 steps
                print(f"     - {step}")
            if len(steps) > 3:
                print(f"     ... and {len(steps) - 3} more")
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 3: API endpoint generation
    print("\n" + "-" * 80)
    print("\n[Test 3] Generating API tests...")
    print("-" * 80)
    
    try:
        result = await service.generate_api_tests(
            endpoint="/api/v1/tests",
            method="POST",
            description="Create a new test case. Requires authentication. Accepts test details in JSON format.",
            num_tests=3
        )
        
        print(f"✅ SUCCESS - Generated {len(result['test_cases'])} test cases")
        print(f"\nTest Cases:")
        
        for i, test in enumerate(result['test_cases'], 1):
            print(f"\n{i}. {test['title']}")
            print(f"   Type: {test.get('test_type', 'N/A')}")
            print(f"   Description: {test.get('description', 'N/A')[:80]}...")
            if 'test_data' in test and test['test_data']:
                print(f"   Test Data: {list(test['test_data'].keys())}")
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 4: Save sample output
    print("\n" + "-" * 80)
    print("\n[Test 4] Saving sample output to file...")
    print("-" * 80)
    
    try:
        output_file = "sample_generated_tests.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ SUCCESS - Saved to {output_file}")
        print(f"   File size: {os.path.getsize(output_file)} bytes")
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    return True


async def main():
    """Main test function."""
    print("\nStarting Test Generation Service Tests...\n")
    
    success = await test_basic_generation()
    
    print("\n" + "=" * 80)
    if success:
        print("ALL TESTS PASSED!")
        print("\nTest generation service is working correctly.")
        print("\nNext steps:")
        print("1. Create API endpoints for test generation")
        print("2. Integrate with frontend")
        print("3. Add test case storage (database)")
    else:
        print("TESTS FAILED!")
        print("Please check the errors above.")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

