# Manual Testing Guide: Loop Execution Enhancement 2

**Feature:** Step Group Loop Support  
**Date:** January 22, 2026  
**Status:** Ready for Testing

---

## Overview

This guide shows you how to manually test the new loop execution feature. Since loop blocks are stored in `test_data`, you won't see them in your existing tests unless you add loop_blocks to them.

---

## Testing Methods (Choose One)

### ✅ Method 1: Python Script (EASIEST - RECOMMENDED)

**Step 1:** Run the automated test script:

```bash
cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main
python test_loop_manual.py
```

**What it does:**
- Logs in automatically
- Creates a test case with loop blocks
- Executes the test
- Monitors execution status
- Shows you where to find results

**Expected Output:**
```
==========================================================
LOOP EXECUTION MANUAL TEST
Sprint 5.5 Enhancement 2: Step Group Loop Support
==========================================================

🔐 Logging in...
✅ Login successful!

📝 Creating test case with loop blocks...
✅ Test case created successfully!
   Test ID: 123
   Title: Manual Test: Upload 3 HKID Documents (Loop)
   Steps: 5

🔁 Loop Block Details:
   ID: file_upload_loop
   Steps: 2-4
   Iterations: 3
   Description: Upload 3 HKID documents

▶️  Executing test case 123...
✅ Execution started!

⏳ Monitoring execution...
✅ Execution finished!
   Status: completed
   Result: pass
   Total Steps: 11
   Passed Steps: 11

📊 TEST RESULTS
📁 Check these locations for detailed results:
   1. Backend logs: Look for lines containing '[LOOP]'
   2. Screenshots: backend/screenshots/
   3. Execution details: execution_id = 456
```

---

### Method 2: Import JSON File via UI

**Step 1:** Open the frontend in your browser:
```
http://localhost:3000
```

**Step 2:** Navigate to Test Cases section

**Step 3:** Click "Import Test" or "Create Test" button

**Step 4:** Copy/paste this JSON:

```json
{
  "title": "DEMO: Upload 5 Documents with Loop",
  "description": "Demonstrates loop execution",
  "test_type": "e2e",
  "priority": "medium",
  "steps": [
    "Navigate to document upload page",
    "Click upload button",
    "Select file from dialog",
    "Click confirm button",
    "Verify success message appears"
  ],
  "expected_result": "All 5 documents uploaded successfully",
  "test_data": {
    "detailed_steps": [
      {"action": "navigate", "value": "http://localhost:3000/upload"},
      {"action": "click", "selector": "#upload-btn"},
      {"action": "upload_file", "selector": "input[type='file']", "file_path": "/home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/test_files/hkid_sample.pdf"},
      {"action": "click", "selector": "#confirm-btn"},
      {"action": "verify", "selector": ".success-message"}
    ],
    "loop_blocks": [
      {
        "id": "file_upload_loop",
        "start_step": 2,
        "end_step": 4,
        "iterations": 5,
        "description": "Upload 5 HKID documents"
      }
    ]
  }
}
```

**Step 5:** Save the test

**Step 6:** You should see the **Loop Blocks panel** appear at the top of the test editor showing:
- 🔁 Loop Blocks (1)
- Loop details with step range, iterations, description

**Step 7:** Click "Execute Test"

**Step 8:** Watch the execution progress

---

### Method 3: Direct API Call with cURL

**Step 1:** Get your auth token:

```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@example.com" \
  -d "password=admin123" | jq -r .access_token)

echo "Token: $TOKEN"
```

**Step 2:** Create test with loop blocks:

```bash
TEST_ID=$(curl -X POST http://localhost:8000/api/v1/tests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @demo_loop_test.json | jq -r .id)

echo "Test ID: $TEST_ID"
```

**Step 3:** Execute the test:

```bash
EXEC_ID=$(curl -X POST http://localhost:8000/api/v1/executions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"test_case_id\": $TEST_ID}" | jq -r .id)

echo "Execution ID: $EXEC_ID"
```

**Step 4:** Check execution status:

```bash
curl http://localhost:8000/api/v1/executions/$EXEC_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## What to Look For

### 1. Backend Logs (Terminal)

Look for these log messages in your backend terminal:

```
[LOOP] Found 1 loop block(s): [{'id': 'file_upload_loop', ...}]
[LOOP] Starting loop block 'file_upload_loop' at step 2 for 5 iterations

[LOOP] Iteration 1/5 of loop 'file_upload_loop'
[DEBUG _execute_step] Step 2: Click upload button
[DEBUG] 3-Tier result: {'success': True, 'tier': 1}
[DEBUG _execute_step] Step 3: Select file from dialog (iter 1)
[DEBUG] Calling 3-Tier with: {'action': 'upload_file', ...}

[LOOP] Iteration 2/5 of loop 'file_upload_loop'
[DEBUG _execute_step] Step 3: Select file from dialog (iter 2)
...

[LOOP] Completed loop 'file_upload_loop': 15 passed, 0 failed
```

**✅ Success Indicators:**
- `[LOOP] Found 1 loop block(s)` appears
- `[LOOP] Starting loop block` shows correct iteration count
- `[LOOP] Iteration X/Y` appears for each iteration
- Step descriptions include `(iter X/Y)`
- `[LOOP] Completed loop` shows final results

---

### 2. Screenshot Files

Check the screenshots directory:

```bash
ls -la /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/screenshots/
```

**Look for files like:**
```
exec_123_step_2_iter_1_pass.png
exec_123_step_3_iter_1_pass.png
exec_123_step_4_iter_1_pass.png
exec_123_step_2_iter_2_pass.png
exec_123_step_3_iter_2_pass.png
exec_123_step_4_iter_2_pass.png
...
```

**✅ Success Indicators:**
- Filenames contain `_iter_N_` pattern
- One screenshot per step per iteration
- For 3 steps × 5 iterations = 15 screenshots (plus non-loop steps)

---

### 3. Execution Steps in Database

Query the execution steps:

```bash
# Using Python script
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///./test.db')
Session = sessionmaker(bind=engine)
session = Session()

from app.models.test_execution import TestExecutionStep

steps = session.query(TestExecutionStep).filter(
    TestExecutionStep.execution_id == YOUR_EXECUTION_ID
).order_by(TestExecutionStep.step_number).all()

for step in steps:
    print(f'Step {step.step_number}: {step.step_description} - {step.result}')
"
```

**✅ Success Indicators:**
- Step descriptions contain `(iter X/Y)`
- Total steps = original steps + (loop steps × iterations)
- Example: 5 logical steps → 11 actual executions (1 + 3×3 + 1)

---

### 4. Frontend Display

When viewing the test case in the UI:

**✅ Success Indicators:**
- **Loop Blocks panel** appears above the step editor
- Shows loop metadata:
  - 🔁 Loop Blocks (1)
  - 📍 Steps: 2-4
  - 🔢 Iterations: 5
  - Loop ID and description
- Can collapse/expand the panel
- Variables section shows {iteration} placeholders

---

## Expected Test Results

### Test Case Structure

**Logical Steps:** 5
1. Navigate to upload page
2. Click upload button (START LOOP)
3. Select file from dialog
4. Click confirm button (END LOOP)
5. Verify success message

**Loop Configuration:**
- Start: Step 2
- End: Step 4
- Iterations: 5
- Steps per iteration: 3 (steps 2, 3, 4)

**Actual Execution:**
- Step 1: Navigate (1 time)
- Steps 2-4: Loop (3 steps × 5 iterations = 15 executions)
- Step 5: Verify (1 time)
- **Total:** 17 step executions

### Execution Flow

```
Step 1: Navigate to upload page

Loop Iteration 1/5:
  Step 2 (iter 1/5): Click upload button
  Step 3 (iter 1/5): Select file from dialog
  Step 4 (iter 1/5): Click confirm button

Loop Iteration 2/5:
  Step 2 (iter 2/5): Click upload button
  Step 3 (iter 2/5): Select file from dialog
  Step 4 (iter 2/5): Click confirm button

Loop Iteration 3/5:
  Step 2 (iter 3/5): Click upload button
  Step 3 (iter 3/5): Select file from dialog
  Step 4 (iter 3/5): Click confirm button

Loop Iteration 4/5:
  Step 2 (iter 4/5): Click upload button
  Step 3 (iter 4/5): Select file from dialog
  Step 4 (iter 4/5): Click confirm button

Loop Iteration 5/5:
  Step 2 (iter 5/5): Click upload button
  Step 3 (iter 5/5): Select file from dialog
  Step 4 (iter 5/5): Click confirm button

Step 5: Verify success message

Total: 17 steps executed (5 logical → 17 actual)
Result: All passed ✅
```

---

## Troubleshooting

### Issue: "I don't see loop blocks in my existing tests"

**Solution:** Loop blocks are **new metadata** in `test_data`. Your existing tests don't have them. You need to:
1. Create a NEW test with loop_blocks in test_data, OR
2. Edit an existing test and add loop_blocks to its test_data field

### Issue: "Backend logs don't show [LOOP] messages"

**Possible Causes:**
1. Test doesn't have loop_blocks in test_data → Add them
2. Loop block structure is invalid → Check required fields (id, start_step, end_step, iterations)
3. Backend not running latest code → Restart backend server

### Issue: "Screenshots don't have iteration numbers"

**Possible Causes:**
1. Loop execution didn't trigger → Check backend logs
2. Old screenshots from previous runs → Delete screenshots folder and re-run
3. Screenshot capture failed → Check backend logs for errors

### Issue: "Frontend doesn't show Loop Blocks panel"

**Possible Causes:**
1. Frontend not rebuilt → Run `npm run build` or restart dev server
2. Test data doesn't include loop_blocks → Verify test_data.loop_blocks exists
3. Browser cache → Hard refresh (Ctrl+Shift+R)

---

## Quick Verification Commands

```bash
# 1. Check if backend is running with loop support
curl http://localhost:8000/api/v1/health

# 2. Count screenshots with iteration numbers
ls backend/screenshots/ | grep "_iter_" | wc -l

# 3. Search backend logs for loop messages
# (Run this in a separate terminal while executing test)
tail -f backend/logs/app.log | grep "\[LOOP\]"

# 4. Verify test data has loop_blocks
curl http://localhost:8000/api/v1/tests/YOUR_TEST_ID \
  -H "Authorization: Bearer $TOKEN" | jq .test_data.loop_blocks
```

---

## Success Checklist

After running the manual test, verify:

- [ ] Backend logs show `[LOOP]` messages
- [ ] Iteration numbers appear in logs (1/5, 2/5, etc.)
- [ ] Step descriptions include `(iter X/Y)`
- [ ] Screenshots have `_iter_N_` in filenames
- [ ] Total steps executed = expected count (e.g., 17 for 5-iteration example)
- [ ] Frontend displays Loop Blocks panel
- [ ] Loop metadata shows correct step range and iterations
- [ ] All loop iterations completed successfully
- [ ] No errors in backend logs
- [ ] Execution result is "pass"

---

## Additional Test Scenarios

### Scenario 1: Variable Substitution

Test if {iteration} placeholder works:

```json
"loop_blocks": [{
  "id": "test_loop",
  "start_step": 2,
  "end_step": 3,
  "iterations": 3,
  "variables": {
    "file_path": "/app/test_files/document_{iteration}.pdf",
    "username": "user{iteration}@example.com"
  }
}]
```

**Verify:** Logs show `document_1.pdf`, `document_2.pdf`, `document_3.pdf`

### Scenario 2: Multiple Sequential Loops

Test two loops in the same test:

```json
"loop_blocks": [
  {
    "id": "loop1",
    "start_step": 2,
    "end_step": 3,
    "iterations": 2,
    "description": "First loop"
  },
  {
    "id": "loop2",
    "start_step": 5,
    "end_step": 6,
    "iterations": 3,
    "description": "Second loop"
  }
]
```

**Verify:** Both loops execute in sequence

### Scenario 3: Single Iteration Loop

Test edge case with 1 iteration:

```json
"loop_blocks": [{
  "id": "single_loop",
  "start_step": 2,
  "end_step": 4,
  "iterations": 1,
  "description": "Single iteration test"
}]
```

**Verify:** Loop executes once, no errors

---

## Need Help?

**Check Documentation:**
- Full implementation guide: `SPRINT-5.5-ENHANCEMENT-2-COMPLETE.md`
- Quick summary: `SPRINT-5.5-ENHANCEMENT-2-SUMMARY.md`
- Implementation checklist: `SPRINT-5.5-ENHANCEMENT-2-CHECKLIST.md`

**Run Automated Tests:**
```bash
# Unit tests
pytest backend/tests/test_loop_execution.py -v

# Integration tests
PYTHONPATH=/home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend \
python backend/tests/test_loop_integration.py
```

**Contact Developer B for support**

---

## Conclusion

The loop execution feature is production-ready and can be tested using any of the methods above. The Python script (`test_loop_manual.py`) is the easiest way to get started.

**Remember:** Loop blocks are stored in `test_data.loop_blocks`, so you won't see them in existing tests unless you add them manually.

Good luck with testing! 🚀
