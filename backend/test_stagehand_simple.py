"""
Simple test to verify Stagehand works in LOCAL mode
"""
import asyncio
import os
from stagehand import Stagehand, StagehandConfig

async def test_stagehand():
    """Test Stagehand in LOCAL mode."""
    print("\n" + "="*60)
    print("Testing Stagehand in LOCAL Mode")
    print("="*60 + "\n")
    
    try:
        # Create configuration for LOCAL mode (uses local Playwright)
        config = StagehandConfig(
            env="LOCAL",  # Use local Playwright instead of Browserbase
            headless=True,  # Run in headless mode
            verbose=1  # Enable logging
        )
        
        print("[INFO] Initializing Stagehand with LOCAL mode...")
        stagehand = Stagehand(config)
        
        await stagehand.init()
        print("[OK] Stagehand initialized successfully!")
        
        page = stagehand.page
        
        print("[INFO] Navigating to example.com...")
        await page.goto("https://example.com")
        print("[OK] Page loaded!")
        
        print("[INFO] Observing page elements...")
        result = await page.observe("find the main heading")
        print(f"[OK] Observation result: {result}")
        
        print("\n[OK] Stagehand is working correctly in LOCAL mode!")
        
        print("\n[INFO] Closing Stagehand...")
        await stagehand.close()
        print("[OK] Closed successfully!")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_stagehand())
    exit(0 if result else 1)

