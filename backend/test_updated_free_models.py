"""Test updated free model IDs based on OpenRouter's current naming."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.openrouter import OpenRouterService
from app.core.config import settings


# Updated list based on OpenRouter's current model naming conventions
UPDATED_FREE_MODELS = [
    # Qwen models - try different naming patterns
    "qwen/qwen-2.5-7b-instruct",
    "qwen/qwen2-7b-instruct",
    "qwen/qwen-72b-chat",
    
    # Meta Llama models - remove :free or try different versions
    "meta-llama/llama-3.2-3b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3-8b-instruct",
    
    # Google Gemma - try without :free
    "google/gemma-2-9b-it",
    "google/gemma-7b-it",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    
    # Microsoft Phi - try without :free
    "microsoft/phi-3-mini-128k-instruct",
    "microsoft/phi-3-medium-128k-instruct",
    
    # Mistral - additional models
    "mistralai/mistral-7b-instruct-v0.3",
    "mistralai/mistral-nemo",
    
    # Other providers
    "openchat/openchat-7b",
    "openchat/openchat-8b",
    "nousresearch/hermes-3-llama-3.1-405b",
    
    # HuggingFace
    "huggingfaceh4/zephyr-7b-beta",
    
    # Additional free/cheap models
    "gryphe/mythomax-l2-13b",
    "undi95/toppy-m-7b",
]


async def test_model_quick(service: OpenRouterService, model: str) -> dict:
    """Quick test of a model."""
    result = {
        "model": model,
        "status": "unknown",
        "error": None
    }
    
    messages = [{"role": "user", "content": "Hi"}]
    
    try:
        response = await service.chat_completion(
            messages=messages,
            model=model,
            max_tokens=5
        )
        
        if "choices" in response and len(response["choices"]) > 0:
            result["status"] = "success"
        else:
            result["status"] = "failed"
            result["error"] = "Invalid response"
            
    except Exception as e:
        result["status"] = "failed"
        error_msg = str(e)
        
        if "404" in error_msg:
            result["error"] = "404 Not Found"
        elif "403" in error_msg:
            result["error"] = "403 Forbidden"
        elif "429" in error_msg:
            result["error"] = "429 Rate Limited"
        elif "500" in error_msg:
            result["error"] = "500 Server Error"
        else:
            result["error"] = error_msg[:80]
    
    return result


async def main():
    """Main test function."""
    print("=" * 80)
    print("Testing Updated Free Model IDs")
    print("=" * 80)
    
    if not settings.OPENROUTER_API_KEY:
        print("\nERROR: OPENROUTER_API_KEY not found!")
        return False
    
    print(f"\nTesting {len(UPDATED_FREE_MODELS)} updated model IDs...\n")
    
    service = OpenRouterService()
    
    results = {
        "success": [],
        "rate_limited": [],
        "not_found": [],
        "other_errors": []
    }
    
    for i, model in enumerate(UPDATED_FREE_MODELS, 1):
        print(f"[{i}/{len(UPDATED_FREE_MODELS)}] {model}... ", end="", flush=True)
        
        result = await test_model_quick(service, model)
        
        if result["status"] == "success":
            print("✅ WORKING")
            results["success"].append(model)
        elif result["error"] == "429 Rate Limited":
            print("⚠️ RATE-LIMITED")
            results["rate_limited"].append(model)
        elif result["error"] == "404 Not Found":
            print("❌ NOT FOUND")
            results["not_found"].append(model)
        else:
            print(f"❌ {result['error']}")
            results["other_errors"].append((model, result['error']))
        
        await asyncio.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ WORKING MODELS ({len(results['success'])}):")
    for model in results['success']:
        print(f"  - {model}")
    
    print(f"\n⚠️ RATE-LIMITED MODELS ({len(results['rate_limited'])}):")
    for model in results['rate_limited']:
        print(f"  - {model}")
    
    print(f"\n❌ NOT FOUND ({len(results['not_found'])}):")
    if len(results['not_found']) > 5:
        for model in results['not_found'][:5]:
            print(f"  - {model}")
        print(f"  ... and {len(results['not_found']) - 5} more")
    else:
        for model in results['not_found']:
            print(f"  - {model}")
    
    if results['other_errors']:
        print(f"\n⚠️ OTHER ERRORS ({len(results['other_errors'])}):")
        for model, error in results['other_errors']:
            print(f"  - {model}: {error[:60]}")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("UPDATED FREE MODELS LIST")
    print("=" * 80)
    
    all_working = results['success'] + results['rate_limited']
    
    if all_working:
        print("\nAdd these to FREE_MODELS list:")
        print("\nFREE_MODELS = [")
        for model in all_working:
            suffix = "  # Rate-limited" if model in results['rate_limited'] else ""
            print(f'    "{model}",{suffix}')
        print("]\n")
    else:
        print("\nNo new working models found.")
    
    print("=" * 80)
    
    return len(all_working) > 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        sys.exit(1)

