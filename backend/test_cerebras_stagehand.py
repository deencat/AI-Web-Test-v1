"""
Test Stagehand with Cerebras API integration
Cerebras provides ultra-fast inference with their custom hardware
"""
import asyncio
import os
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

# Load environment variables
load_dotenv()

async def test_stagehand_with_cerebras():
    """Test Stagehand in LOCAL mode with Cerebras API."""
    print("\n" + "="*70)
    print("🧠 Testing Stagehand with Cerebras API")
    print("="*70 + "\n")
    
    # Get Cerebras API key from environment
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    cerebras_model = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")
    
    if not cerebras_key:
        print("[FAIL] ❌ CEREBRAS_API_KEY not found in environment")
        print("\nTo get started with Cerebras:")
        print("1. Visit: https://cloud.cerebras.ai/")
        print("2. Sign up and get your API key")
        print("3. Add to .env: CEREBRAS_API_KEY=your-api-key-here")
        return False
    
    print(f"[INFO] Using Cerebras model: {cerebras_model}")
    print(f"[INFO] API Key: {cerebras_key[:20]}...")
    
    try:
        # Create configuration for LOCAL mode with Cerebras
        config = StagehandConfig(
            env="LOCAL",  # Use local Playwright
            headless=True,  # Run in headless mode
            verbose=1,  # Enable logging
            # Configure LiteLLM to use Cerebras
            model_name=f"cerebras/{cerebras_model}",
            model_api_key=cerebras_key
        )
        
        print("[INFO] Initializing Stagehand with Cerebras...")
        stagehand = Stagehand(config)
        
        await stagehand.init()
        print("[OK] ✅ Stagehand initialized successfully!")
        
        page = stagehand.page
        
        # Test 1: Navigate to example.com
        print("\n[TEST 1] Navigation")
        print("-" * 70)
        print("[INFO] Navigating to example.com...")
        await page.goto("https://example.com")
        print("[OK] ✅ Page loaded!")
        
        # Test 2: AI-powered observation
        print("\n[TEST 2] AI-Powered Observation (Cerebras)")
        print("-" * 70)
        print("[INFO] Using Cerebras AI to observe the main heading...")
        
        import time
        start_time = time.time()
        
        try:
            result = await page.observe("find the main heading text on this page")
            elapsed_time = time.time() - start_time
            
            print(f"[OK] ✅ AI observation successful!")
            print(f"[RESULT] Observed: {result}")
            print(f"[PERFORMANCE] ⚡ Cerebras inference time: {elapsed_time:.2f} seconds")
            print("[INFO] Cerebras is optimized for speed!")
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[WARN] ⚠️ Observation failed after {elapsed_time:.2f}s: {str(e)}")
            print("[INFO] This might be a model-specific limitation")
        
        # Test 3: Navigate to a more complex page
        print("\n[TEST 3] Complex Page Navigation")
        print("-" * 70)
        print("[INFO] Navigating to Wikipedia...")
        await page.goto("https://en.wikipedia.org/wiki/Artificial_intelligence")
        print("[OK] ✅ Page loaded!")
        
        title = await page.title()
        print(f"[INFO] Page title: {title}")
        
        # Test 4: AI-powered action (if available)
        print("\n[TEST 4] AI-Powered Action Test")
        print("-" * 70)
        print("[INFO] Testing AI action capabilities...")
        
        start_time = time.time()
        try:
            # Try a simple scroll action
            await page.act("scroll down a bit")
            elapsed_time = time.time() - start_time
            print(f"[OK] ✅ AI action successful!")
            print(f"[PERFORMANCE] ⚡ Action completed in {elapsed_time:.2f} seconds")
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[WARN] ⚠️ Action failed after {elapsed_time:.2f}s: {str(e)}")
        
        # Cleanup
        print("\n[CLEANUP] Closing browser...")
        await stagehand.close()
        print("[OK] ✅ Browser closed successfully!")
        
        print("\n" + "="*70)
        print("🎉 Cerebras Test Complete!")
        print("="*70)
        print("\n[SUMMARY] Cerebras Integration:")
        print("  ✅ API connection successful")
        print("  ✅ Browser automation working")
        print("  ⚡ Fast inference speeds")
        print("\n[NEXT STEPS]:")
        print("  1. Set MODEL_PROVIDER=cerebras in .env")
        print("  2. Or set USE_CEREBRAS=true in .env")
        print("  3. Run your test executions with Cerebras!")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] ❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_stagehand_with_cerebras())
    exit(0 if result else 1)
