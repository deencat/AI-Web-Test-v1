"""
Direct test to verify clicking on 30 months button actually works.
Uses Stagehand directly to see the exact behavior.
"""
import asyncio
import os
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

load_dotenv()

async def test_direct_click():
    print("\n" + "=" * 70)
    print("🎯 Direct Click Test - 3HK 5G Broadband '30 Months' Button")
    print("=" * 70)
    
    # Get API configuration
    openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")
    
    # Configure Stagehand
    config = StagehandConfig(
        env="LOCAL",
        headless=False,  # Show browser so we can see what happens
        verbose=1,
        model_name=f"openrouter/{openrouter_model}",
        model_api_key=openrouter_key,
    )
    
    print(f"\n[1] Initializing Stagehand with OpenRouter ({openrouter_model})...")
    stagehand = Stagehand(config)
    await stagehand.init()
    page = stagehand.page
    
    try:
        # Navigate to the page
        url = "https://web.three.com.hk/5gbroadband/plan-hsbc-en.html"
        print(f"[2] Navigating to {url}...")
        await page.goto(url)
        await asyncio.sleep(2)
        
        # Scroll to see the buttons
        print("[3] Scrolling to find contract period options...")
        await page.act("Scroll down to see the contract period selection buttons")
        await asyncio.sleep(2)
        
        # Take screenshot before clicking
        await page.screenshot(path="before_click.png")
        print("    📸 Saved: before_click.png")
        
        # Observe the current state
        print("[4] Observing the page state before clicking...")
        observation = await page.observe("What contract period buttons are visible? Describe their appearance and colors.")
        print(f"    👁️  AI sees: {observation}")
        
        # Try to click the 30 months button with very specific instruction
        print("[5] Attempting to click '30 months' button...")
        print("    Instruction: Click directly on the button labeled '30 months' under the first plan")
        await page.act("Click on the button that says '30 months' - it's under 'Please select contract period' in the first card")
        await asyncio.sleep(3)  # Wait for animation
        
        # Take screenshot after clicking
        await page.screenshot(path="after_click.png")
        print("    📸 Saved: after_click.png")
        
        # Observe the new state
        print("[6] Observing the page state after clicking...")
        observation_after = await page.observe("What contract period buttons are visible now? Are any buttons selected or highlighted? Describe colors and borders.")
        print(f"    👁️  AI sees: {observation_after}")
        
        # Check if the button state changed
        print("\n[7] Verification:")
        print("    ✓ Check 'before_click.png' and 'after_click.png'")
        print("    ✓ The '30 months' button should have a purple/violet border in the 'after' screenshot")
        print("    ✓ Compare the AI observations above")
        
        # Try alternative approach: use Playwright directly
        print("\n[8] Alternative: Direct Playwright click...")
        print("    Finding button with text '30 months'...")
        
        # Get the underlying Playwright page
        pw_page = page._page
        
        # Try to find and click using Playwright's built-in methods
        button_selector = "text='30 months'"
        button = await pw_page.wait_for_selector(button_selector, timeout=5000)
        
        if button:
            print(f"    ✓ Found button with selector: {button_selector}")
            
            # Get button info
            is_visible = await button.is_visible()
            is_enabled = await button.is_enabled()
            print(f"    Button state: visible={is_visible}, enabled={is_enabled}")
            
            # Take screenshot before direct click
            await page.screenshot(path="before_direct_click.png")
            print("    📸 Saved: before_direct_click.png")
            
            # Click with Playwright
            print("    Clicking with Playwright...")
            await button.click()
            await asyncio.sleep(2)
            
            # Take screenshot after direct click
            await page.screenshot(path="after_direct_click.png")
            print("    📸 Saved: after_direct_click.png")
            
            # Observe result
            observation_direct = await page.observe("Is the '30 months' button now selected with a purple border?")
            print(f"    👁️  AI sees after direct click: {observation_direct}")
            
        print("\n" + "=" * 70)
        print("✅ Test complete! Check the screenshots:")
        print("   - before_click.png")
        print("   - after_click.png")
        print("   - before_direct_click.png")
        print("   - after_direct_click.png")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n[9] Cleaning up...")
        await stagehand.close()
        print("    Browser closed.")


if __name__ == "__main__":
    asyncio.run(test_direct_click())
