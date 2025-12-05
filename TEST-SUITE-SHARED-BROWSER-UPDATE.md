# Test Suite Shared Browser Session - Implementation Summary

## 🎯 **Problem Solved**

**Before**: Each test in a suite opened a **new browser session**, making sequential tests fail because later tests couldn't continue from the browser state of earlier tests.

**After**: All tests in a suite now **share the same browser session**, allowing tests like #62-#66 to run sequentially where each test builds on the previous one's browser state.

---

## 🔧 **Changes Made**

### **1. Suite Execution Service** (`backend/app/services/suite_execution_service.py`)

#### **Before (Old Approach - WRONG)**
```python
async def _execute_sequential(...):
    queue = get_execution_queue()
    
    for test_case_id in test_case_ids:
        # Create execution record
        execution = crud_executions.create_execution(...)
        
        # Add to queue (worker will create NEW browser for each test)
        queue.add_to_queue(execution.id, ...)
        
        # Wait for test to complete
        while status != COMPLETED:
            await asyncio.sleep(2)
```

**Problem**: Each test was queued separately, and the queue worker created a **new StagehandExecutionService** (new browser) for each test.

#### **After (New Approach - CORRECT)**
```python
async def _execute_sequential(...):
    # Create ONE shared Stagehand service for ALL tests
    stagehand_service = StagehandExecutionService(
        browser=browser,
        headless=True
    )
    
    try:
        # Initialize browser ONCE for entire suite
        await stagehand_service.initialize()
        print(f"[SUITE] Initialized shared {browser} browser for {len(test_case_ids)} tests")
        
        for index, test_case_id in enumerate(test_case_ids):
            # Create execution record
            execution = crud_executions.create_execution(...)
            
            # Execute test DIRECTLY with shared browser
            # Skip navigation for tests after first one
            skip_navigation = (index > 0)
            
            await stagehand_service.execute_test(
                db=db,
                test_case=test_case,
                execution_id=execution.id,
                skip_navigation=skip_navigation  # NEW!
            )
            
            # Check if we should stop on failure
            if stop_on_failure and execution.status != COMPLETED:
                break
    
    finally:
        # Clean up shared browser at the end
        await stagehand_service.cleanup()
```

**Benefits**:
- ✅ **Single browser session** shared across all tests
- ✅ **No queue delays** - tests run immediately after each other
- ✅ **Browser state preserved** - cookies, localStorage, page state carry over
- ✅ **Navigation skipped** for tests after the first one (they continue from current page)

---

### **2. Stagehand Service** (`backend/app/services/stagehand_service.py`)

#### **Added `skip_navigation` Parameter**

```python
async def execute_test(
    self,
    db: Session,
    test_case: TestCase,
    execution_id: int,
    user_id: int,
    base_url: str,
    environment: str = "dev",
    progress_callback: Optional[Callable] = None,
    skip_navigation: bool = False  # NEW!
):
    """Execute a test case."""
    
    # Initialize browser (reuses existing if already initialized)
    await self.initialize()
    
    # Navigate to base URL (or skip if continuing from suite)
    if not skip_navigation:
        print(f"[DEBUG] Navigating to {base_url}")
        await self.page.goto(base_url)
    else:
        print(f"[DEBUG] Skipping navigation (continuing from previous test)")
        print(f"[DEBUG] Current URL: {self.page.url}")
    
    # Execute steps...
```

**Why This Works**:
- First test: `skip_navigation=False` → Navigates to base URL
- Later tests: `skip_navigation=True` → Continue from current page
- Browser state (cookies, localStorage, DOM) is **preserved** between tests

#### **Added `browser` Parameter**

```python
def __init__(
    self,
    browser: str = "chromium",  # NEW!
    headless: bool = True,
    screenshot_dir: str = "artifacts/screenshots",
    video_dir: str = "artifacts/videos"
):
    self.browser = browser
    # ...
```

**Why**: Suite execution can specify which browser to use (chromium, firefox, webkit).

---

## 📊 **How It Works Now**

### **Example: Suite with Tests #62, #63, #64**

```
User clicks "Run Suite" (3 tests)
    ↓
[SUITE] Create shared StagehandExecutionService(browser="chromium")
    ↓
[SUITE] Initialize browser ONCE → Opens Chromium
    ↓
┌─────────────────────────────────────────────────────────┐
│ Test #62 (index=0):                                     │
│   - skip_navigation = False (first test)                │
│   - Navigate to: https://web.three.com.hk/...           │
│   - Execute steps: ["Navigate to plan page"]           │
│   - Browser state: Plan page loaded                     │
│   - Status: COMPLETED ✅                                │
└─────────────────────────────────────────────────────────┘
    ↓ (same browser continues)
┌─────────────────────────────────────────────────────────┐
│ Test #63 (index=1):                                     │
│   - skip_navigation = True (continue from #62)          │
│   - Current URL: https://web.three.com.hk/...           │
│   - Execute steps: ["Select 30 months contract"]       │
│   - Browser state: Contract selected                    │
│   - Status: COMPLETED ✅                                │
└─────────────────────────────────────────────────────────┘
    ↓ (same browser continues)
┌─────────────────────────────────────────────────────────┐
│ Test #64 (index=2):                                     │
│   - skip_navigation = True (continue from #63)          │
│   - Current URL: https://web.three.com.hk/...           │
│   - Execute steps: ["Verify pricing"]                  │
│   - Browser state: Pricing verified                     │
│   - Status: COMPLETED ✅                                │
└─────────────────────────────────────────────────────────┘
    ↓
[SUITE] Cleanup: Close browser
    ↓
Suite execution complete! All 3 tests shared the same browser.
```

---

## 🎯 **Your Use Case: Tests #62-#66**

### **Before This Fix**
```
Test #62: Open browser → Navigate to plan page → Close browser
Test #63: Open NEW browser → Navigate somewhere → FAILS (no context from #62)
```

### **After This Fix**
```
Suite "Three.com.hk Complete Flow":
  Browser opens once
    → Test #62: Navigate to plan page (browser stays open)
    → Test #63: Select contract (continues from #62's page)
    → Test #64: Verify pricing (continues from #63's page)
    → Test #65: Complete checkout (continues from #64's page)
    → Test #66: Login and confirm (continues from #65's page)
  Browser closes
```

**Each test builds on the previous one's browser state!** ✅

---

## 🚀 **Testing Instructions**

### **1. Restart Backend**
```bash
cd backend
python -m app.main
```

### **2. Create Test Suite**
- Go to Test Suites page
- Click "New Suite"
- Name: "Three.com.hk Complete Flow"
- Add tests: #62, #63, #64, #65, #66 (in order)
- Save

### **3. Run Suite**
- Click "Run Suite"
- Browser: Chromium
- Environment: Development
- Watch the logs

### **4. Expected Logs**
```
[SUITE] Initialized shared chromium browser session for 5 tests
[SUITE] Test 1/5: #62 - Navigate to plan page
[SUITE] Base URL: https://web.three.com.hk/5gbroadband/plan-hsbc-en.html
[SUITE] Executing test #62 with shared browser session...
[DEBUG] Navigating to https://web.three.com.hk/...
[DEBUG] Executing 1 steps
[DEBUG] Step 1 PASSED
[SUITE] Test #62 finished with status: COMPLETED

[SUITE] Test 2/5: #63 - Select 30 months contract
[SUITE] This test will continue from the browser state left by test #62
[SUITE] Executing test #63 with shared browser session...
[DEBUG] Skipping navigation (continuing from previous test)
[DEBUG] Current URL: https://web.three.com.hk/5gbroadband/plan-hsbc-en.html
[DEBUG] Executing 1 steps
[DEBUG] Step 1 PASSED
[SUITE] Test #63 finished with status: COMPLETED

... (same for #64, #65, #66)

[SUITE] Cleaning up shared browser session...
```

---

## 💡 **Key Differences**

| Aspect | Before | After |
|--------|--------|-------|
| **Browser per suite** | 5 browsers (one per test) | 1 browser (shared) |
| **Navigation** | Every test navigates to base_url | Only first test navigates |
| **Browser state** | Lost between tests | Preserved between tests |
| **Execution method** | Queued (async, separate workers) | Direct (synchronous in suite) |
| **Speed** | Slower (browser startup overhead) | Faster (no browser restarts) |
| **Use case** | Independent tests | Sequential flow tests ✅ |

---

## 🔍 **Debugging Tips**

### **View Browser (Non-Headless Mode)**

Change in `suite_execution_service.py`:
```python
stagehand_service = StagehandExecutionService(
    browser=browser,
    headless=False  # Change to False to see browser
)
```

Then you can **watch the browser** execute all tests in the same window!

### **Check Logs**

Look for these key messages:
- `[SUITE] Initialized shared chromium browser session for X tests` - Browser opened
- `[SUITE] This test will continue from the browser state left by test #Y` - Reusing browser
- `[DEBUG] Skipping navigation (continuing from previous test)` - No navigation
- `[DEBUG] Current URL: ...` - Shows where browser is currently at
- `[SUITE] Cleaning up shared browser session...` - Browser closed

---

## ✅ **Summary**

**What Changed**:
1. Suite execution now creates ONE shared browser for all tests
2. Tests execute directly (not queued)
3. Navigation is skipped for tests after the first one
4. Browser state is preserved across all tests in suite

**Why It Matters**:
- Tests #62-#66 can now run as a continuous flow
- Each test builds on the previous test's browser state
- Cookies, localStorage, and page state carry over
- This is exactly what you need for sequential E2E flows!

**Ready to Test**: Restart backend and run your Suite 2 (tests #62 + #63) to see them execute in the same browser! 🚀
