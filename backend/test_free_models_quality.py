"""Test quality of working free models."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.openrouter import OpenRouterService
from app.core.config import settings


WORKING_FREE_MODELS = [
    "deepseek/deepseek-chat",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mistral-7b-instruct",
    "mistralai/mixtral-8x7b-instruct",
]


async def test_quality(service: OpenRouterService, model: str) -> dict:
    """Test model quality with a test generation prompt."""
    
    messages = [
        {
            "role": "system",
            "content": "You are a test case generator. Generate test cases in a structured format."
        },
        {
            "role": "user",
            "content": "Generate 2 test cases for testing a login page. Be brief but clear."
        }
    ]
    
    result = {
        "model": model,
        "status": "unknown",
        "response": None,
        "tokens": None,
        "time": 0
    }
    
    try:
        import time
        start = time.time()
        
        response = await service.chat_completion(
            messages=messages,
            model=model,
            max_tokens=300
        )
        
        result["time"] = round(time.time() - start, 2)
        
        if "choices" in response and len(response["choices"]) > 0:
            result["status"] = "success"
            result["response"] = response["choices"][0]["message"]["content"]
            if "usage" in response:
                result["tokens"] = response["usage"].get("total_tokens", 0)
        else:
            result["status"] = "failed"
            
    except Exception as e:
        result["status"] = "failed"
        result["response"] = str(e)[:200]
    
    return result


async def main():
    """Main test function."""
    print("=" * 80)
    print("Testing Quality of Working Free Models")
    print("=" * 80)
    
    if not settings.OPENROUTER_API_KEY:
        print("\nERROR: OPENROUTER_API_KEY not found!")
        return False
    
    print(f"\nTesting {len(WORKING_FREE_MODELS)} models for test generation quality...\n")
    
    service = OpenRouterService()
    results = []
    
    for i, model in enumerate(WORKING_FREE_MODELS, 1):
        print(f"[{i}/{len(WORKING_FREE_MODELS)}] Testing: {model}")
        
        result = await test_quality(service, model)
        results.append(result)
        
        if result["status"] == "success":
            print(f"  ✅ SUCCESS ({result['time']}s, {result['tokens']} tokens)")
            print(f"  Response preview:")
            print(f"  {result['response'][:150]}...")
        else:
            print(f"  ❌ FAILED: {result['response'][:100]}")
        
        print()
        await asyncio.sleep(1)
    
    # Summary
    print("=" * 80)
    print("QUALITY COMPARISON")
    print("=" * 80)
    
    successful = [r for r in results if r["status"] == "success"]
    
    if not successful:
        print("\nNo models succeeded!")
        return False
    
    # Sort by response length (longer = more detailed)
    successful.sort(key=lambda x: len(x["response"]), reverse=True)
    
    print("\n🏆 RANKED BY QUALITY (response detail):\n")
    
    for i, r in enumerate(successful, 1):
        print(f"{i}. {r['model']}")
        print(f"   Speed: {r['time']}s")
        print(f"   Tokens: {r['tokens']}")
        print(f"   Response length: {len(r['response'])} chars")
        print(f"   Response:")
        print(f"   {'-' * 70}")
        for line in r['response'].split('\n')[:10]:  # First 10 lines
            print(f"   {line}")
        if r['response'].count('\n') > 10:
            print(f"   ... ({r['response'].count(chr(10)) - 10} more lines)")
        print()
    
    # Recommendation
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    best = successful[0]
    print(f"\n🎯 BEST FREE MODEL: {best['model']}")
    print(f"   ✅ Good response quality")
    print(f"   ✅ Free (no cost)")
    print(f"   ✅ Speed: {best['time']}s")
    print(f"   ✅ Tokens: {best['tokens']}")
    
    print(f"\n📝 ADD TO YOUR .ENV FILE:")
    print(f"OPENROUTER_MODEL={best['model']}")
    
    print("\n" + "=" * 80)
    
    return True


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

