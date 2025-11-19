"""Test multiple free open-source models on OpenRouter."""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.openrouter import OpenRouterService
from app.core.config import settings


# List of free models to test
# Updated with correct model IDs (November 2025)
FREE_MODELS = [
    # DeepSeek models
    "deepseek/deepseek-chat",
    
    # Qwen models
    "qwen/qwen-2.5-7b-instruct",
    
    # Meta Llama models
    "meta-llama/llama-3.2-3b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3-8b-instruct",
    
    # Google models
    "google/gemma-2-9b-it",
    
    # Mistral models
    "mistralai/mistral-7b-instruct",
    "mistralai/mixtral-8x7b-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "mistralai/mistral-nemo",
    
    # Microsoft models
    "microsoft/phi-3-mini-128k-instruct",
    "microsoft/phi-3-medium-128k-instruct",
    
    # Nous Research
    "nousresearch/hermes-3-llama-3.1-405b",
    
    # Other models
    "gryphe/mythomax-l2-13b",
]


async def test_model(service: OpenRouterService, model: str) -> dict:
    """
    Test a single model.
    
    Returns:
        dict with 'model', 'status', 'error', 'response', 'tokens'
    """
    result = {
        "model": model,
        "status": "unknown",
        "error": None,
        "response": None,
        "tokens": None
    }
    
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
            result["status"] = "success"
            result["response"] = response["choices"][0]["message"]["content"]
            if "usage" in response:
                result["tokens"] = response["usage"].get("total_tokens", 0)
        else:
            result["status"] = "failed"
            result["error"] = "Invalid response format"
            
    except Exception as e:
        result["status"] = "failed"
        error_msg = str(e)
        
        # Parse error type
        if "404" in error_msg:
            result["error"] = "404 Not Found"
        elif "403" in error_msg:
            result["error"] = "403 Forbidden (region/unsupported)"
        elif "500" in error_msg:
            result["error"] = "500 Server Error"
        elif "timeout" in error_msg.lower():
            result["error"] = "Timeout"
        else:
            result["error"] = error_msg[:100]  # Truncate long errors
    
    return result


async def main():
    """Main test function."""
    print("=" * 80)
    print("Testing Free Open-Source Models on OpenRouter")
    print("=" * 80)
    
    # Check API key
    if not settings.OPENROUTER_API_KEY:
        print("\nERROR: OPENROUTER_API_KEY not found in .env file!")
        return False
    
    print(f"\nAPI Key: {settings.OPENROUTER_API_KEY[:20]}...")
    print(f"Testing {len(FREE_MODELS)} models...\n")
    
    service = OpenRouterService()
    
    results = {
        "success": [],
        "failed": []
    }
    
    # Test each model
    for i, model in enumerate(FREE_MODELS, 1):
        print(f"[{i}/{len(FREE_MODELS)}] Testing: {model}")
        
        result = await test_model(service, model)
        
        if result["status"] == "success":
            print(f"  ✅ SUCCESS - Response: {result['response'][:50]}...")
            if result["tokens"]:
                print(f"     Tokens: {result['tokens']}")
            results["success"].append(result)
        else:
            print(f"  ❌ FAILED - {result['error']}")
            results["failed"].append(result)
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ WORKING MODELS ({len(results['success'])}):")
    if results["success"]:
        for r in results["success"]:
            print(f"  - {r['model']}")
            print(f"    Response: {r['response'][:60]}...")
            if r["tokens"]:
                print(f"    Tokens: {r['tokens']}")
    else:
        print("  None found")
    
    print(f"\n❌ FAILED MODELS ({len(results['failed'])}):")
    if results["failed"]:
        # Group by error type
        error_groups = {}
        for r in results["failed"]:
            error = r["error"]
            if error not in error_groups:
                error_groups[error] = []
            error_groups[error].append(r["model"])
        
        for error, models in error_groups.items():
            print(f"\n  {error} ({len(models)} models):")
            for model in models:
                print(f"    - {model}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if results["success"]:
        print("\n🎯 RECOMMENDED FREE MODELS:")
        for i, r in enumerate(results["success"][:3], 1):
            print(f"\n{i}. {r['model']}")
            print(f"   ✅ Working")
            print(f"   ✅ Free")
            print(f"   Response quality: {r['response']}")
        
        print("\n📝 TO USE IN YOUR .ENV FILE:")
        print(f"OPENROUTER_MODEL={results['success'][0]['model']}")
    else:
        print("\n⚠️ No free models found working.")
        print("Recommendation: Use paid models like Claude 3 Haiku (~$0.75/1000 tests)")
    
    print("\n" + "=" * 80)
    
    return len(results["success"]) > 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

