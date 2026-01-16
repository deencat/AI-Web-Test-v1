"""
Test Stagehand observe() method to understand what it returns
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

load_dotenv()

async def test_observe_api():
    """Test what stagehand.observe() returns."""
    print("\n" + "="*70)
    print("Testing Stagehand observe() API")
    print("="*70 + "\n")
    
    try:
        # Setup
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")
        
        config = StagehandConfig(
            env="LOCAL",
            headless=False,  # Keep visible to see what's happening
            verbose=1,
            model_name=f"openrouter/{openrouter_model}",
            model_api_key=openrouter_key
        )
        
        print(f"[INFO] Using model: {openrouter_model}")
        stagehand = Stagehand(config)
        await stagehand.init()
        print("[OK] Stagehand initialized\n")
        
        page = stagehand.page
        
        # Navigate to a test page
        print("[INFO] Navigating to GitHub login page...")
        await page.goto("https://github.com/login")
        await asyncio.sleep(2)  # Wait for page to stabilize
        print("[OK] Page loaded\n")
        
        # Test observe() method
        print("="*70)
        print("Calling page.observe() to find login button...")
        print("="*70)
        
        # Try different ways to call observe
        print("\n[TEST 1] Calling observe with instruction...")
        try:
            observe_result = await page.observe("find the login button")
            print(f"\n✅ observe() returned successfully!")
            print(f"\nResult type: {type(observe_result)}")
            print(f"Is list: {isinstance(observe_result, list)}")
            print(f"Is dict: {isinstance(observe_result, dict)}")
            
            print("\n" + "="*70)
            print("OBSERVE RESULT:")
            print("="*70)
            print(json.dumps(observe_result, indent=2, default=str))
            print("="*70)
            
            # Check structure
            if isinstance(observe_result, list):
                print(f"\nReturned {len(observe_result)} elements")
                if len(observe_result) > 0:
                    print("\nFirst element structure:")
                    first = observe_result[0]
                    print(f"  Type: {type(first)}")
                    if hasattr(first, '__dict__'):
                        print(f"  Attributes: {first.__dict__}")
                    if isinstance(first, dict):
                        print(f"  Keys: {first.keys()}")
                        for key, value in first.items():
                            print(f"    {key}: {value}")
                    
                    # Look for XPath/selector
                    if isinstance(first, dict):
                        xpath_keys = [k for k in first.keys() if 'xpath' in k.lower() or 'selector' in k.lower()]
                        if xpath_keys:
                            print(f"\n✅ Found selector keys: {xpath_keys}")
                            for key in xpath_keys:
                                print(f"  {key}: {first[key]}")
            
        except TypeError as e:
            print(f"❌ observe() signature error: {e}")
            print("\n[TEST 2] Trying observe with no arguments...")
            try:
                observe_result = await page.observe()
                print(f"✅ observe() with no args succeeded!")
                print(json.dumps(observe_result, indent=2, default=str))
            except Exception as e2:
                print(f"❌ Also failed: {e2}")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETE")
        print("="*70)
        
        await stagehand.close()
        return True
        
    except Exception as e:
        print(f"\n❌ [FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_observe_api())
    exit(0 if result else 1)
