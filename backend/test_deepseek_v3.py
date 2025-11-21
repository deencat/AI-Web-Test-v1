"""Test the new DeepSeek Chat V3 free model."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.openrouter import OpenRouterService
from app.core.config import settings


async def test_deepseek_v3():
    """Test DeepSeek Chat V3 free model."""
    print("=" * 80)
    print("Testing DeepSeek Chat V3 Free Model")
    print("=" * 80)
    
    if not settings.OPENROUTER_API_KEY:
        print("\nERROR: OPENROUTER_API_KEY not found!")
        return False
    
    print(f"\nAPI Key: {settings.OPENROUTER_API_KEY[:20]}...")
    
    service = OpenRouterService()
    model = "deepseek/deepseek-chat-v3-0324:free"
    
    # Test 1: Simple hello
    print(f"\n[Test 1] Testing: {model}")
    print("-" * 80)
    
    messages = [
        {"role": "user", "content": "Say 'Hello' in one word."}
    ]
    
    try:
        response = await service.chat_completion(
            messages=messages,
            model=model,
            max_tokens=10
        )
        
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ SUCCESS!")
            print(f"Response: {content}")
            
            if "usage" in response:
                usage = response["usage"]
                print(f"\nUsage Stats:")
                print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print("❌ FAILED: Invalid response format")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Test generation
    print(f"\n[Test 2] Test case generation")
    print("-" * 80)
    
    messages = [
        {
            "role": "system",
            "content": "You are a test case generator."
        },
        {
            "role": "user",
            "content": "Generate 2 test cases for a login page. Be brief."
        }
    ]
    
    try:
        import time
        start = time.time()
        
        response = await service.chat_completion(
            messages=messages,
            model=model,
            max_tokens=300
        )
        
        elapsed = round(time.time() - start, 2)
        
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ SUCCESS! ({elapsed}s)")
            print(f"\nResponse length: {len(content)} chars")
            print(f"\nResponse preview:")
            print(content[:300] + "..." if len(content) > 300 else content)
            
            if "usage" in response:
                usage = response["usage"]
                print(f"\nTokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print("❌ FAILED: Invalid response format")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    return True


async def main():
    """Main test function."""
    print("\nTesting DeepSeek Chat V3...\n")
    
    success = await test_deepseek_v3()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ DEEPSEEK CHAT V3 IS WORKING!")
        print("\nThis model is:")
        print("  ✅ FREE (no cost)")
        print("  ✅ Latest version (v3-0324)")
        print("  ✅ Good quality")
        print("\nTo use in your .env file:")
        print("OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free")
    else:
        print("❌ DeepSeek Chat V3 test failed")
        print("The model may not be available or have issues.")
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

