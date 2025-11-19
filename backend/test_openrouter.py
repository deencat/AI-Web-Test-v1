"""Test OpenRouter API connection and functionality."""
import asyncio
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.openrouter import OpenRouterService
from app.core.config import settings


async def test_basic_connection():
    """Test basic OpenRouter API connection."""
    print("=" * 60)
    print("Testing OpenRouter API Connection")
    print("=" * 60)
    
    # Check if API key is configured
    if not settings.OPENROUTER_API_KEY:
        print("\nERROR: OPENROUTER_API_KEY not found in .env file!")
        print("Please add: OPENROUTER_API_KEY=sk-or-v1-xxxxx")
        return False
    
    print(f"\nAPI Key configured: {settings.OPENROUTER_API_KEY[:20]}...")
    print(f"Model configured: {settings.OPENROUTER_MODEL}")
    
    # Initialize service
    service = OpenRouterService()
    
    # Test 1: Simple connection test
    print("\n[Test 1] Testing basic connection...")
    try:
        result = await service.test_connection()
        if result:
            print("SUCCESS: OpenRouter API is accessible")
        else:
            print("FAILED: Could not connect to OpenRouter API")
            print("Trying direct test to get more details...")
            # Try a direct call to see the actual error
            messages = [
                {"role": "user", "content": "test"}
            ]
            response = await service.chat_completion(messages, max_tokens=5)
            print(f"Unexpected: Got response but test_connection failed: {response}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Simple chat completion
    print("\n[Test 2] Testing chat completion...")
    print(f"Using model: {settings.OPENROUTER_MODEL}")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello from OpenRouter!' in one sentence."}
    ]
    
    try:
        response = await service.chat_completion(messages, max_tokens=50)
        
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"SUCCESS: Received response")
            print(f"Response: {content}")
            
            # Display usage stats
            if "usage" in response:
                usage = response["usage"]
                print(f"\nUsage Stats:")
                print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print("FAILED: Invalid response format")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    
    # Test 3: Test generation prompt (relevant to our use case)
    print("\n[Test 3] Testing test case generation prompt...")
    messages = [
        {
            "role": "system",
            "content": "You are a test case generator. Generate test cases in a structured format."
        },
        {
            "role": "user",
            "content": "Generate 2 test cases for testing a login page. Keep it brief."
        }
    ]
    
    try:
        response = await service.chat_completion(
            messages,
            temperature=0.7,
            max_tokens=300
        )
        
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"SUCCESS: Generated test cases")
            print(f"\nGenerated content:\n{content[:200]}...")
        else:
            print("FAILED: Could not generate test cases")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    
    return True


async def main():
    """Main test function."""
    print("\nStarting OpenRouter API Tests...\n")
    
    success = await test_basic_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("ALL TESTS PASSED!")
        print("OpenRouter integration is working correctly.")
        print("\nNext steps:")
        print("1. Create test generation service (Day 2)")
        print("2. Design prompt templates")
        print("3. Build test case CRUD endpoints")
    else:
        print("TESTS FAILED!")
        print("Please check the errors above and fix them.")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)

