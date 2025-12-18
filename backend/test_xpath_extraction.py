"""
Test XPath extraction from Stagehand act() results
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

load_dotenv()

async def test_xpath_extraction():
    """Test that we can extract XPath from Stagehand act() results."""
    print("\n" + "="*60)
    print("Testing XPath Extraction from Stagehand")
    print("="*60 + "\n")
    
    try:
        # Setup
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")
        
        config = StagehandConfig(
            env="LOCAL",
            headless=True,
            verbose=1,
            model_name=f"openrouter/{openrouter_model}",
            model_api_key=openrouter_key
        )
        
        print(f"[INFO] Using model: {openrouter_model}")
        stagehand = Stagehand(config)
        await stagehand.init()
        print("[OK] Stagehand initialized\n")
        
        page = stagehand.page
        
        # Test 1: Click action
        print("="*60)
        print("TEST 1: Click Action")
        print("="*60)
        await page.goto("https://example.com")
        print("[INFO] Navigated to example.com")
        
        print("[INFO] Executing: page.act('click on the More information link')")
        act_result = await page.act("click on the 'More information...' link")
        
        print(f"\n[RESULT] Type: {type(act_result)}")
        print(f"[RESULT] Success: {act_result.success}")
        print(f"[RESULT] Action: {act_result.action}")
        print(f"[RESULT] Message: {act_result.message}")
        
        # Extract XPath
        import re
        xpath_used = None
        if act_result and hasattr(act_result, 'message') and act_result.message:
            xpath_match = re.search(r'selector:\s*(xpath=[^\s]+)', act_result.message)
            if xpath_match:
                xpath_used = xpath_match.group(1)
                print(f"\n✅ [EXTRACTED] XPath: {xpath_used}")
            else:
                print(f"\n⚠️  Could not extract XPath from message")
        
        # Verify we got what we need
        assert act_result.success, "Action should succeed"
        assert xpath_used is not None, "Should extract XPath from result"
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print(f"  - Stagehand act() returns ActResult object")
        print(f"  - ActResult has .success, .action, .message attributes")
        print(f"  - XPath can be extracted from .message")
        print(f"  - Example XPath extracted: {xpath_used}")
        print("\n" + "="*60)
        
        await stagehand.close()
        return True
        
    except Exception as e:
        print(f"\n❌ [FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_xpath_extraction())
    exit(0 if result else 1)
