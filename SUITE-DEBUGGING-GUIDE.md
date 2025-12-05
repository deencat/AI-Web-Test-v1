# Test Suite Debugging Guide

## Issue: Suite Only Ran First Test (#62), Stopped Without Running #63

### What Should Happen:

When you run a test suite with tests #62 and #63, you should see these log messages:

```
[SUITE] Test 1/2: #62 - Navigate to plan page
[SUITE] Waiting for execution X (test 1/2) to complete...
[SUITE] Execution X finished with status: COMPLETED
[SUITE] Test 2/2: #63 - Second test title
```

### What Actually Happened:

Based on your logs, NO `[SUITE]` messages appeared, which means:
- ❌ The suite execution function was NOT called
- ✅ Only a single test execution happened (execution #49 for test #62)

### Possible Causes:

#### **1. Wrong Button Clicked**
- You may have clicked "Run Test #62" instead of "Run Suite"
- Check: Did you click the "Run" button on the **Test Suites page** or the **Tests page**?

#### **2. Frontend Not Calling Suite Endpoint**
- The "Run Suite" button might be calling the wrong API endpoint
- Should call: `POST /api/v1/suites/{suite_id}/run`
- Might be calling: `POST /api/v1/executions/tests/{test_id}/run`

#### **3. Suite Not Created Properly**
- The suite might only have test #62, not both #62 and #63
- Check suite configuration in database

---

## How to Debug:

### Step 1: Verify Suite Contents

Run this in your backend directory:

```powershell
cd backend
python -c "from app.db.session import SessionLocal; from app.models.test_suite import TestSuite, TestSuiteItem; db = SessionLocal(); suite = db.query(TestSuite).filter(TestSuite.id == 2).first(); print(f'Suite #{suite.id}: {suite.name}'); items = db.query(TestSuiteItem).filter(TestSuiteItem.suite_id == 2).order_by(TestSuiteItem.execution_order).all(); [print(f'  {i.execution_order}. Test Case #{i.test_case_id}') for i in items]; db.close()"
```

**Expected Output:**
```
Suite #2: Your Suite Name
  1. Test Case #62
  2. Test Case #63
```

**If you only see test #62**, the suite wasn't created with both tests!

---

### Step 2: Check Frontend Network Request

1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Run Suite" button
4. Look for the API request

**What to check:**
- ✅ **Correct**: `POST http://localhost:8000/api/v1/suites/2/run`
- ❌ **Wrong**: `POST http://localhost:8000/api/v1/executions/tests/62/run`

If you see the wrong endpoint, the frontend button is misconfigured.

---

### Step 3: Check Backend Logs

When you click "Run Suite", you should immediately see:

```
INFO:     127.0.0.1:XXXXX - "POST /api/v1/suites/2/run HTTP/1.1" 200 OK
[SUITE] Test 1/2: #62 - ...
```

**If you see:**
```
INFO:     127.0.0.1:XXXXX - "POST /api/v1/executions/tests/62/run HTTP/1.1" 200 OK
[DEBUG] Initializing Stagehand...
```

Then the **wrong endpoint was called** (single test, not suite).

---

## Quick Fix Steps:

### If Suite Wasn't Created with Both Tests:

1. Go to Test Suites page
2. Delete Suite #2
3. Create new suite:
   - Name: "Three.com.hk Flow"
   - Search for test #62 → Add to suite
   - Search for test #63 → Add to suite
   - Verify: "Selected Tests" shows both tests in order
4. Save suite
5. Click "Run Suite"

### If Wrong Endpoint Is Being Called:

The issue is in `TestSuitesPage.tsx`. Let me check that file...

---

## What to Look For in Server Logs:

### ✅ **CORRECT (Suite Execution)**:
```
INFO: POST /api/v1/suites/2/run HTTP/1.1
[SUITE] Test 1/2: #62 - Navigate to plan page
[SUITE] Waiting for execution 49 (test 1/2) to complete...
[DEBUG] Initializing Stagehand in thread Thread-XX
[DEBUG] Navigating to https://web.three.com.hk/...
[DEBUG] Execution complete: 2/2 passed
[SUITE] Execution 49 finished with status: COMPLETED
[SUITE] Test 2/2: #63 - Select 30 months contract
[SUITE] Waiting for execution 50 (test 2/2) to complete...
[DEBUG] Initializing Stagehand in thread Thread-YY
...
```

### ❌ **WRONG (Single Test Execution)**:
```
INFO: POST /api/v1/executions/tests/62/run HTTP/1.1
[DEBUG] Initializing Stagehand in thread Thread-XX
[DEBUG] Navigating to https://web.three.com.hk/...
[DEBUG] Execution complete: 2/2 passed
(NO [SUITE] messages)
(NO second test)
```

---

## Next Steps:

1. **First**: Run the database query in Step 1 to verify suite has both tests
2. **Second**: Check browser Network tab to see which API endpoint is being called
3. **Third**: Based on findings, either:
   - Recreate the suite (if it only has test #62)
   - OR fix the frontend button (if wrong endpoint is called)

---

## Expected vs Actual:

| Step | Expected | Actual (Your Case) |
|------|----------|-------------------|
| Click "Run Suite" | POST `/api/v1/suites/2/run` | ??? (check Network tab) |
| Backend logs | `[SUITE] Test 1/2...` | No [SUITE] messages |
| First test runs | ✅ Execution #49 runs | ✅ Execution #49 runs |
| Second test runs | ✅ Execution #50 starts | ❌ Nothing happens |
| Suite status | Shows "2 tests queued" | Shows only 1 test? |

The fact that you see **NO `[SUITE]` logs** means the suite execution code never ran!

---

##  Most Likely Issue:

**The suite might only contain test #62!**

When you created the suite, you may have:
1. Added test #62 to "Selected Tests"
2. Forgot to add test #63
3. Saved the suite

**Solution**: Delete and recreate the suite, making sure BOTH tests are in the "Selected Tests" column before saving.

---

Let me know what you find from the database query in Step 1!
