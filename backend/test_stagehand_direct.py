"""
Test Stagehand directly to isolate the issue.
"""
import asyncio
import sys

# Set Windows event loop policy FIRST
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[OK] Set WindowsProactorEventLoopPolicy")

from stagehand import Stagehand, StagehandConfig

async def test_stagehand():
    print("\n=== Testing Stagehand Browser Launch ===")
    
    stagehand = None
    try:
        print("[1] Creating Stagehand config...")
        config = StagehandConfig(
            env="LOCAL",
            headless=True,
            verbose=0
        )
        print("[OK] Config created")
        
        print("[2] Creating Stagehand instance...")
        stagehand = Stagehand(config)
        print("[OK] Stagehand instance created")
        
        print("[3] Initializing Stagehand (launching browser)...")
        await stagehand.init()
        print("[OK] Stagehand initialized, browser launched!")
        
        print("[4] Getting page object...")
        page = stagehand.page
        print("[OK] Page object available")
        
        print("[5] Navigating to example.com...")
        await page.goto("https://example.com")
        print("[OK] Navigation successful")
        
        print("[6] Getting page title...")
        title = await page.title()
        print(f"[OK] Page title: {title}")
        
        print("[7] Closing Stagehand...")
        await stagehand.close()
        print("[OK] Stagehand closed")
        
        print("\n✅ ALL TESTS PASSED! Stagehand works correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        if stagehand:
            try:
                await stagehand.close()
            except:
                pass
        return False

if __name__ == "__main__":
    success = asyncio.run(test_stagehand())
    exit(0 if success else 1)

