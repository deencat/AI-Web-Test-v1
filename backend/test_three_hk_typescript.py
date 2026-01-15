"""
Test Three.com.hk subscription flow using TypeScript Stagehand adapter.
This test focuses on the problematic login steps (15-18) where Python Stagehand failed.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter


# Test steps from the Three.com.hk flow
TEST_STEPS = [
    "Navigate to: https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc",
    "Scroll down until the plan section with pricing cards is visible",
    "Locate the $154/month plan card by finding the plan showing '平均月費 $154' with '$198' crossed out",
    "Verify pricing: $154/月 with $198 struck out (per Document 1)",
    "Verify plan details: 5G寬頻Wi-Fi 6 月費計劃, 5G寬頻任用",
    "Click the '48個月' button in the contract period selection area (per [Document 1] Section: Application Interface)",
    "Verify the '48個月' button changes to selected state",
    "Click '立即上台' within the $154 plan card",
    "Verify navigation to 'Your Selection' page showing plan details and promotional offer (ref: [Document 1] Section: Service Details)",
    "Scroll down until '下一步' (Next) button are visible",
    "Click '下一步' (Next)",
    "Verify payment breakdown: SIM卡收費: $100, 按金: $0, 總額: $100",
    "Tick checkbox: '本人已經同意及確認已經已選擇服務的條款及細則'",
    "Click '立即上台' (Subscribe Now)",
    # CRITICAL LOGIN STEPS - Where Python Stagehand failed
    "Fill in Email field with: pmo.andrewchan+010@gmail.com",
    "Click '登入' button below email",
    "Wait 2 seconds for password field to appear, then fill Password field with: cA8mn49&",
    "Click '登入' button below password, wait 3 seconds",
    "Verify URL changed or page shows success",
    "Select date: January 11, 2026",
    "Click 'Confirm' button"
]


async def test_three_hk_typescript():
    """Test Three.com.hk subscription flow with TypeScript Stagehand."""
    
    print("="*80)
    print("Testing Three.com.hk with TypeScript Stagehand Adapter")
    print("="*80)
    print(f"Total steps: {len(TEST_STEPS)}")
    print("Focusing on steps 15-18 where Python Stagehand failed")
    print("="*80)
    
    adapter = TypeScriptStagehandAdapter()
    
    try:
        # Initialize adapter
        print("\n[Initialization] Connecting to TypeScript Stagehand service...")
        await adapter.initialize({
            "model": "gpt-4o",
            "temperature": 0.7
        })
        print("✅ Service connected")
        
        # Initialize persistent session
        print("\n[Session] Creating browser session...")
        import uuid
        from unittest.mock import MagicMock
        
        session_id = f"three-hk-test-{uuid.uuid4()}"
        mock_db = MagicMock()
        
        await adapter.initialize_persistent(
            session_id=session_id,
            test_id=103,
            user_id=1,
            db=mock_db
        )
        print(f"✅ Browser session created: {adapter._browser_session_id}")
        
        # Navigate to the starting URL (required before executing steps)
        print("\n[Navigation] Loading Three.com.hk page...")
        start_url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
        
        session = await adapter._get_session()
        nav_response = await session.post(
            f"{adapter.service_url}/api/sessions/{adapter._browser_session_id}/navigate",
            json={"url": start_url}
        )
        nav_result = await nav_response.json()
        print(f"✅ Page loaded: {nav_result.get('message', 'Success')}")
        
        # Wait for Stagehand act handler to fully initialize
        print("\n⏳ Waiting for act handler to initialize...")
        await asyncio.sleep(3)
        print("✅ Act handler ready")
        
        # Execute steps
        print("\n" + "="*80)
        print("EXECUTING TEST STEPS")
        print("="*80)
        
        successful_steps = 0
        failed_at_step = None
        
        for i, step in enumerate(TEST_STEPS, 1):
            step_display = step[:80] + "..." if len(step) > 80 else step
            print(f"\n[Step {i}/{len(TEST_STEPS)}] {step_display}")
            
            # Handle navigation steps differently
            if step.startswith("Navigate to:"):
                url = step.replace("Navigate to:", "").strip()
                # Skip the initial navigation since we already did it
                if i == 1:
                    print(f"⏭️  SKIPPED (already navigated)")
                    successful_steps += 1
                    continue
                
                # Use the navigate endpoint for step 9 (navigation to selection page)
                try:
                    session = await adapter._get_session()
                    response = await session.post(
                        f"{adapter.service_url}/api/sessions/{adapter._browser_session_id}/navigate",
                        json={"url": url}
                    )
                    nav_result = await response.json()
                    
                    if nav_result.get('success'):
                        print(f"✅ SUCCESS")
                        print(f"   Navigated to new page")
                        successful_steps += 1
                    else:
                        print(f"❌ FAILED")
                        print(f"   Error: {nav_result.get('message', 'Navigation failed')}")
                        failed_at_step = i
                        break
                except Exception as e:
                    print(f"❌ EXCEPTION")
                    print(f"   Error: {str(e)}")
                    failed_at_step = i
                    break
            else:
                # Use execute_single_step for all interaction actions
                result = await adapter.execute_single_step(
                    step_description=step,
                    step_number=i,
                    execution_id=103
                )
                
                success = result.get('success', False)
                duration = result.get('duration_ms', 0)
                
                if success:
                    print(f"✅ SUCCESS ({duration}ms)")
                    successful_steps += 1
                    
                    # Highlight critical login steps
                    if i >= 15 and i <= 18:
                        print(f"   🎯 CRITICAL STEP PASSED (Python Stagehand failed here)")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"❌ FAILED ({duration}ms)")
                    print(f"   Error: {error}")
                    failed_at_step = i
                    
                    # If we fail at the critical login steps, note it
                    if i >= 15 and i <= 18:
                        print(f"   ⚠️  FAILED AT SAME STEP AS PYTHON STAGEHAND")
                
                break
            
            # Small delay between steps
            await asyncio.sleep(0.5)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Steps: {len(TEST_STEPS)}")
        print(f"Successful: {successful_steps}")
        print(f"Failed: {0 if failed_at_step is None else 1}")
        
        if failed_at_step:
            print(f"\n❌ Test failed at step {failed_at_step}")
            if failed_at_step >= 15 and failed_at_step <= 18:
                print(f"   TypeScript Stagehand also failed at the login steps")
                print(f"   This suggests the issue is with:")
                print(f"   - Overlay/modal element detection")
                print(f"   - Chinese text recognition ('登入')")
                print(f"   - Two-stage login form complexity")
            else:
                print(f"   TypeScript Stagehand failed earlier than Python")
        else:
            print(f"\n✅ ALL STEPS PASSED!")
            print(f"   TypeScript Stagehand successfully completed where Python failed")
            print(f"   Critical login steps (15-18) executed successfully")
        
        # Cleanup
        print("\n[Cleanup] Closing browser session...")
        await adapter.cleanup()
        print("✅ Session closed")
        
        return failed_at_step is None
        
    except Exception as e:
        print(f"\n❌ Test crashed with error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await adapter.cleanup()
        except:
            pass
        
        return False


if __name__ == "__main__":
    print("\n🚀 Three.com.hk TypeScript Stagehand Test")
    print("Testing the problematic login flow (steps 15-18)\n")
    
    result = asyncio.run(test_three_hk_typescript())
    
    print("\n" + "="*80)
    if result:
        print("🎉 TypeScript Stagehand PASSED where Python Stagehand failed!")
    else:
        print("⚠️  TypeScript Stagehand encountered issues")
    print("="*80)
    
    sys.exit(0 if result else 1)
