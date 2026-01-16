"""
Test Python Stagehand observe() API to understand what it returns.
This will help us implement observe -> extract xpath -> playwright click pattern.
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

load_dotenv()

async def test_observe_api():
    print("Testing Python Stagehand observe() API...\n")
    
    # Use OpenRouter with your configured model
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    
    config = StagehandConfig(
        env="LOCAL",
        model_name=f"openrouter/{openrouter_model}",
        model_api_key=openrouter_key,
        verbose=1,
        headless=False
    )
    
    stagehand = Stagehand(config)
    
    try:
        await stagehand.init()
        print("✅ Stagehand initialized\n")
        
        # Navigate to a test page
        await stagehand.page.goto('https://github.com/login', wait_until='networkidle')
        print("✅ Navigated to GitHub login page\n")
        
        # Test observe() using page.observe() not stagehand.observe()
        print("Calling stagehand.page.observe('find the login button')...\n")
        observe_result = await stagehand.page.observe('find the login button')
        
        print("=" * 70)
        print("OBSERVE RESULT:")
        print("=" * 70)
        print(json.dumps(observe_result, indent=2, default=str))
        print("=" * 70)
        
        # Check the type and structure
        print(f"\nResult type: {type(observe_result)}")
        print(f"Is dict: {isinstance(observe_result, dict)}")
        print(f"Is list: {isinstance(observe_result, list)}")
        
        if isinstance(observe_result, dict):
            print(f"\nKeys in result: {list(observe_result.keys())}")
            for key, value in observe_result.items():
                print(f"  {key}: {type(value).__name__}")
        
        if isinstance(observe_result, list) and len(observe_result) > 0:
            print(f"\nFirst element:")
            first_elem = observe_result[0]
            print(f"Type of first element: {type(first_elem)}")
            
            # Check if it's an object with attributes
            if hasattr(first_elem, '__dict__'):
                print(f"\nFirst element attributes:")
                for attr, value in first_elem.__dict__.items():
                    print(f"  {attr}: {value}")
            
            # Check for specific attributes we expect
            for attr in ['selector', 'xpath', 'method', 'description', 'arguments']:
                if hasattr(first_elem, attr):
                    print(f"\n✅ Found {attr}: {getattr(first_elem, attr)}")
            
            if isinstance(observe_result[0], dict):
                print(f"\nFirst element keys: {list(observe_result[0].keys())}")
        
        # Check if selector/xpath is available
        print("\n" + "=" * 70)
        print("CHECKING FOR SELECTOR/XPATH:")
        print("=" * 70)
        
        def find_selectors(obj, path=""):
            """Recursively find any selector/xpath-related fields"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(term in key.lower() for term in ['selector', 'xpath', 'locator', 'element']):
                        print(f"  Found '{current_path}': {value}")
                    if isinstance(value, (dict, list)):
                        find_selectors(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_selectors(item, f"{path}[{i}]")
        
        find_selectors(observe_result)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await stagehand.close()
            print("\n✅ Cleanup complete")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_observe_api())
