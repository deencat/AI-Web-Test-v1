# Shared Browser Session - Windows Limitation

## ❌ **Issue Encountered**

When attempting to implement shared browser sessions for test suites (where all tests in a suite use the same browser), we encountered a **Windows + Python 3.13 + asyncio limitation**:

```
NotImplementedError
  File "C:\Python313\Lib\asyncio\base_events.py", line 533, in _make_subprocess_transport
    raise NotImplementedError
```

## 🔍 **Root Cause**

1. **Playwright requires subprocess** to launch browser
2. **Windows requires ProactorEventLoop** for subprocess operations
3. **FastAPI uses a different event loop** in the main thread
4. **Python 3.13 has stricter** event loop policies
5. **Cannot start Playwright browser** in FastAPI request handler thread

## 🚫 **What Doesn't Work**

```python
# THIS FAILS ON WINDOWS:
async def _execute_sequential(...):
    # Create shared browser in main FastAPI thread
    stagehand_service = StagehandExecutionService()
    await stagehand_service.initialize()  # ❌ NotImplementedError!
    
    for test_id in test_ids:
        await stagehand_service.execute_test(...)  # Would share browser
```

**Error**: `NotImplementedError` when trying to create subprocess for Playwright

## ✅ **Current Implementation (Queue-Based)**

```python
async def _execute_sequential(...):
    queue = get_execution_queue()
    
    for test_id in test_ids:
        # Queue each test (worker thread will execute with new browser)
        execution = create_execution(...)
        queue.add_to_queue(execution.id)
        
        # Wait for completion before queuing next
        while execution.status != COMPLETED:
            await asyncio.sleep(2)
```

**How it works**:
- ✅ Each test is queued individually
- ✅ Worker thread (with correct event loop) executes test
- ✅ Each test gets **NEW browser session**
- ✅ Tests run **sequentially** (waits for previous to complete)
- ❌ Browser state **NOT shared** between tests

## 📊 **Comparison**

| Feature | Shared Browser (Attempted) | Queue-Based (Current) |
|---------|---------------------------|----------------------|
| **Browser per suite** | 1 browser for all tests | 1 browser per test |
| **Browser state** | Preserved between tests | Lost between tests |
| **Works on Windows** | ❌ No (subprocess error) | ✅ Yes |
| **Sequential execution** | ✅ Yes | ✅ Yes |
| **Speed** | Faster (no browser restarts) | Slower (browser restarts) |

## 🔧 **Workarounds Considered**

### **1. Background Thread** ❌
```python
def run_suite_in_thread():
    # Set event loop policy in thread
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    # Run tests with shared browser
```
**Issue**: Complex, adds threading overhead, difficult to track progress

### **2. Separate Process** ❌
```python
import multiprocessing
p = multiprocessing.Process(target=run_suite)
p.start()
```
**Issue**: Cannot share database session, complex IPC needed

### **3. Use Celery/Redis** ❌
```python
@celery.task
def run_suite_task(suite_id):
    # Run in Celery worker with proper event loop
```
**Issue**: Adds infrastructure complexity, overkill for MVP

### **4. Downgrade Python** ❌
Python 3.10 or 3.11 might be more forgiving
**Issue**: Don't want to downgrade, Python 3.13 is stable

## 💡 **Recommended Solution for Sequential Flows**

For tests that need to build on each other (like #62-#66), **design tests to be self-contained**:

### **Bad Approach** ❌
```
Test #62: Navigate to plan page
Test #63: Click "30 months" (assumes already on page from #62)
Test #64: Verify pricing (assumes 30 months selected from #63)
```

### **Good Approach** ✅
```
Test #62: Navigate to plan page
Test #63: 
  - Navigate to plan page
  - Click "30 months"
Test #64:
  - Navigate to plan page
  - Click "30 months"
  - Verify pricing
```

Each test is **self-contained** and can run independently.

## 🎯 **Alternative: Single "Flow" Test**

Instead of 5 separate tests, create **ONE test with multiple steps**:

```json
{
  "title": "Three.com.hk Complete Flow (#62-#66)",
  "steps": [
    "Navigate to https://web.three.com.hk/5gbroadband/plan-hsbc-en.html",
    "Click on '30 months' contract option",
    "Verify pricing shows correct amount for 30-month plan",
    "Click 'Proceed to checkout'",
    "Fill in login details",
    "Click 'Confirm order'"
  ]
}
```

**Benefits**:
- ✅ Single browser session (one test = one browser)
- ✅ All steps share browser state
- ✅ Easier to debug (one execution to review)
- ✅ Faster execution (no browser restarts)

## 📝 **Summary**

**Current Status**:
- Test suites work on Windows ✅
- Tests run sequentially (one at a time) ✅
- Each test gets fresh browser ⚠️
- Browser state NOT shared between tests ❌

**Recommendation**:
Use **single tests with multiple steps** for flows that need shared browser state, rather than multiple tests in a suite.

**Future Work**:
- Investigate running suite execution in background worker process
- Add "flow test" type that explicitly supports multi-step flows
- Consider migration to Celery for complex execution scenarios

---

**Last Updated**: December 5, 2025  
**Issue**: Windows subprocess limitation with Playwright in FastAPI thread  
**Status**: Reverted to queue-based approach (each test = new browser)
