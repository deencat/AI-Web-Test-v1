"""
Test Playwright directly to isolate the issue.
"""
import asyncio
import sys

# Set Windows event loop policy FIRST
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[OK] Set WindowsProactorEventLoopPolicy")

from playwright.async_api import async_playwright

async def test_playwright():
    print("\n=== Testing Playwright Browser Launch ===")
    
    try:
        print("[1] Creating playwright instance...")
        async with async_playwright() as p:
            print("[OK] Playwright instance created")
            
            print("[2] Launching Chromium browser...")
            browser = await p.chromium.launch(headless=True)
            print("[OK] Browser launched successfully!")
            
            print("[3] Creating new page...")
            page = await browser.new_page()
            print("[OK] Page created")
            
            print("[4] Navigating to example.com...")
            await page.goto("https://example.com")
            print("[OK] Navigation successful")
            
            print("[5] Getting page title...")
            title = await page.title()
            print(f"[OK] Page title: {title}")
            
            print("[6] Closing browser...")
            await browser.close()
            print("[OK] Browser closed")
            
        print("\n✅ ALL TESTS PASSED! Playwright works correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_playwright())
    exit(0 if success else 1)

