"""
Test what page.act() returns in Stagehand
"""
import asyncio
import os
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

load_dotenv()

async def test_act_return_value():
    """Test what page.act() returns."""
    print("\n" + "="*60)
    print("Testing Stagehand page.act() Return Value")
    print("="*60 + "\n")
    
    try:
        # Create configuration
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")
        
        config = StagehandConfig(
            env="LOCAL",
            headless=True,
            verbose=2,  # Max verbosity
            model_name=f"openrouter/{openrouter_model}",
            model_api_key=openrouter_key
        )
        
        print(f"[INFO] Initializing Stagehand with model: {openrouter_model}...")
        stagehand = Stagehand(config)
        await stagehand.init()
        print("[OK] Stagehand initialized!")
        
        page = stagehand.page
        
        print("\n[INFO] Navigating to example.com...")
        await page.goto("https://example.com")
        print("[OK] Page loaded!")
        
        print("\n[INFO] Testing page.act() return value...")
        print("[INFO] Calling: page.act('click on the More information link')")
        
        # CAPTURE THE RETURN VALUE
        result = await page.act("click on the 'More information...' link")
        
        print("\n" + "="*60)
        print("RESULT FROM page.act():")
        print("="*60)
        print(f"Type: {type(result)}")
        print(f"Value: {result}")
        
        if result:
            print("\nResult attributes:")
            if hasattr(result, '__dict__'):
                for key, value in result.__dict__.items():
                    print(f"  {key}: {value}")
            
            # Check for common attributes
            for attr in ['xpath', 'selector', 'element', 'locator', 'success', 'data']:
                if hasattr(result, attr):
                    print(f"\nFound attribute '{attr}': {getattr(result, attr)}")
        
        print("\n" + "="*60)
        
        print("\n[INFO] Also testing page.observe() for comparison...")
        observe_result = await page.observe("find the main heading")
        print("\n" + "="*60)
        print("RESULT FROM page.observe():")
        print("="*60)
        print(f"Type: {type(observe_result)}")
        print(f"Value: {observe_result}")
        
        if observe_result and hasattr(observe_result, '__dict__'):
            print("\nObserve result attributes:")
            for key, value in observe_result.__dict__.items():
                print(f"  {key}: {value}")
        
        print("\n[INFO] Closing Stagehand...")
        await stagehand.close()
        print("[OK] Test complete!")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_act_return_value())
    exit(0 if result else 1)
