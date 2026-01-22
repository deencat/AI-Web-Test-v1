# Loop Block UI Editor - Visual User Guide 🎨

**For:** End Users & Testers  
**Feature:** Visual Loop Block Creation  
**Date:** January 22, 2026

---

## 🎯 What Is This?

A visual interface to create **loop blocks** that repeat test steps multiple times **without duplicating** them.

### Use Cases:
- 📁 Upload 5 different files
- 📝 Fill 3 forms with different data
- ✅ Check 10 items in a list
- 🔄 Any repetitive action

---

## 📍 Where to Find It

```
1. Login to http://localhost:3000
2. Click "Tests" in sidebar
3. Click on any test with 2+ steps
4. Scroll to "Test Steps" section
5. You'll see "🔁 Loop Blocks" panel at the top
```

---

## 🎨 Visual Walkthrough

### Step 1: Initial View (No Loops)

```
┌────────────────────────────────────────────────────┐
│ 🔁 Loop Blocks                    [+ Create Loop]  │
├────────────────────────────────────────────────────┤
│ 💡 Tip: Use loops to repeat step sequences        │
│    (e.g., upload 5 files, fill 3 forms)           │
└────────────────────────────────────────────────────┘
```

**What you see:**
- Empty loop blocks section
- "Create Loop" button (enabled if 2+ steps exist)
- Helpful tip text

---

### Step 2: Click "Create Loop"

```
┌────────────────────────────────────────────────────┐
│ 🔁 Loop Blocks                                     │
├────────────────────────────────────────────────────┤
│ Create New Loop Block                              │
│                                                    │
│ ┌──────────────────┐  ┌──────────────────┐       │
│ │ Start Step       │  │ End Step         │       │
│ │ [2  ]            │  │ [4  ]            │       │
│ └──────────────────┘  └──────────────────┘       │
│                                                    │
│ ┌──────────────────┐  ┌──────────────────┐       │
│ │ Iterations (1-100)│  │ Description     │       │
│ │ [5  ]            │  │ [Upload files   ]│       │
│ └──────────────────┘  └──────────────────┘       │
│                                                    │
│ 📊 Execution Preview:                              │
│ • Loop steps: 3 (steps 2-4)                       │
│ • Loop executions: 15 (3 steps × 5 iterations)    │
│ • Non-loop steps: 2                               │
│ • Total executions: 17 steps                      │
│                                                    │
│            [Cancel]  [Create Loop Block]          │
└────────────────────────────────────────────────────┘
```

**What you see:**
- Form with 4 inputs
- Real-time execution preview
- Cancel and Create buttons

---

### Step 3: Fill in Loop Details

**Example Scenario: Upload 5 files**

Assume your test has these steps:
```
1. Navigate to upload page
2. Click "Choose File" button       ← Start here
3. Select file from dialog          │ These 3 steps
4. Click "Upload" button            ← End here
5. Verify success message
```

**Fill the form:**
- **Start Step:** `2` (Click Choose File)
- **End Step:** `4` (Click Upload)
- **Iterations:** `5` (Upload 5 files)
- **Description:** `Upload 5 files` (optional)

**Execution Preview Shows:**
```
📊 Execution Preview:
• Loop steps: 3 (steps 2-4)
• Loop executions: 15 (3 steps × 5 iterations)
• Non-loop steps: 2 (steps 1 and 5)
• Total executions: 17 steps
```

**What this means:**
- Your test has 5 steps originally
- Steps 2-4 will repeat 5 times
- Total execution: Step 1 (once) + Steps 2-4 (5 times) + Step 5 (once) = **17 actions**

---

### Step 4: Validation Examples

#### ✅ Valid Loop
```
Test Steps: 10
Start: 3, End: 5, Iterations: 4
→ ✅ Creates loop for steps 3-5, repeated 4 times
```

#### ❌ Invalid - Overlapping Loop
```
Existing: Steps 2-4
New: Steps 3-6
```

**Error displayed:**
```
┌────────────────────────────────────────────┐
│ ⚠️ This loop overlaps with existing loop  │
│    "Upload files" (steps 2-4)             │
└────────────────────────────────────────────┘
```

#### ❌ Invalid - Wrong Range
```
Start: 5, End: 3
```

**Error displayed:**
```
┌────────────────────────────────────────────┐
│ ⚠️ End step must be greater than or equal │
│    to start step                          │
└────────────────────────────────────────────┘
```

#### ❌ Invalid - Too Many Iterations
```
Iterations: 150
```

**Error displayed:**
```
┌────────────────────────────────────────────┐
│ ⚠️ Maximum 100 iterations allowed          │
└────────────────────────────────────────────┘
```

---

### Step 5: Created Loop View

```
┌────────────────────────────────────────────────────┐
│ 🔁 Loop Blocks (1)                [+ Create Loop]  │
├────────────────────────────────────────────────────┤
│ Active Loops (1):                                  │
│                                                    │
│ ┌────────────────────────────────────────────────┐│
│ │ Upload 5 files                      [✕ Delete] ││
│ │ 📍 Steps: 2-4 (3 steps)                        ││
│ │ 🔢 Iterations: 5                                ││
│ │ ⚡ Total: 15 executions                         ││
│ └────────────────────────────────────────────────┘│
│                                                    │
│ ℹ️ Loop blocks repeat step sequences automatically│
│   without duplication.                             │
└────────────────────────────────────────────────────┘
```

**What you see:**
- Loop count in header (1 loop)
- Loop card with details
- Delete button to remove loop
- Informational note at bottom

---

### Step 6: Multiple Loops (Non-Overlapping)

```
┌────────────────────────────────────────────────────┐
│ 🔁 Loop Blocks (2)                [+ Create Loop]  │
├────────────────────────────────────────────────────┤
│ Active Loops (2):                                  │
│                                                    │
│ ┌────────────────────────────────────────────────┐│
│ │ Upload 5 files                      [✕ Delete] ││
│ │ 📍 Steps: 2-4 (3 steps)                        ││
│ │ 🔢 Iterations: 5                                ││
│ │ ⚡ Total: 15 executions                         ││
│ └────────────────────────────────────────────────┘│
│                                                    │
│ ┌────────────────────────────────────────────────┐│
│ │ Fill 3 forms                        [✕ Delete] ││
│ │ 📍 Steps: 6-8 (3 steps)                        ││
│ │ 🔢 Iterations: 3                                ││
│ │ ⚡ Total: 9 executions                          ││
│ └────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────┘
```

**What you see:**
- Two separate loop blocks
- Each with their own metadata
- No overlap (steps 2-4 and 6-8 are separate)

---

## 🎬 Complete Example

### Scenario: Upload 3 Documents to a Form

**Test Steps:**
```
1. Navigate to document submission page
2. Click "Add Document" button
3. Select file type from dropdown
4. Choose file from file picker
5. Enter document description
6. Click "Upload" button
7. Verify success notification
8. Click "Submit All Documents"
```

### Create Loop Block:

**Settings:**
- Start Step: `2` (Add Document)
- End Step: `6` (Upload button)
- Iterations: `3` (3 documents)
- Description: `Upload 3 documents`

### What Happens During Execution:

```
Execution Flow:
─────────────────────────────────────────
Step 1: Navigate to document submission page (1 time)

LOOP START (3 iterations):
  Iteration 1/3:
    Step 2: Click "Add Document" button
    Step 3: Select file type from dropdown
    Step 4: Choose file from file picker
    Step 5: Enter document description
    Step 6: Click "Upload" button
  
  Iteration 2/3:
    Step 2: Click "Add Document" button (iter 2/3)
    Step 3: Select file type from dropdown (iter 2/3)
    Step 4: Choose file from file picker (iter 2/3)
    Step 5: Enter document description (iter 2/3)
    Step 6: Click "Upload" button (iter 2/3)
  
  Iteration 3/3:
    Step 2: Click "Add Document" button (iter 3/3)
    Step 3: Select file type from dropdown (iter 3/3)
    Step 4: Choose file from file picker (iter 3/3)
    Step 5: Enter document description (iter 3/3)
    Step 6: Click "Upload" button (iter 3/3)
LOOP END

Step 7: Verify success notification (1 time)
Step 8: Click "Submit All Documents" (1 time)
─────────────────────────────────────────
Total Executions: 1 + (5 × 3) + 2 = 18 steps
```

### What You'll See in Logs:

```
[INFO] Executing step 1: Navigate to document submission page
[INFO] Executing step 2 (iter 1/3): Click "Add Document" button
[INFO] Executing step 3 (iter 1/3): Select file type from dropdown
[INFO] Executing step 4 (iter 1/3): Choose file from file picker
[INFO] Executing step 5 (iter 1/3): Enter document description
[INFO] Executing step 6 (iter 1/3): Click "Upload" button
[INFO] Executing step 2 (iter 2/3): Click "Add Document" button
[INFO] Executing step 3 (iter 2/3): Select file type from dropdown
...
[INFO] Executing step 7: Verify success notification
[INFO] Executing step 8: Click "Submit All Documents"
[INFO] Test execution completed successfully
```

### Screenshots Saved:

```
execution_123/
├── step_1.png
├── step_2_iter_1.png
├── step_3_iter_1.png
├── step_4_iter_1.png
├── step_5_iter_1.png
├── step_6_iter_1.png
├── step_2_iter_2.png
├── step_3_iter_2.png
...
├── step_7.png
└── step_8.png
```

---

## 🎯 Quick Tips

### ✅ DO:
- Use loops for repetitive sequences (3+ repetitions)
- Keep loop ranges clear and non-overlapping
- Add descriptive names to loops
- Verify execution preview before creating
- Test with 2-3 iterations first, then scale up

### ❌ DON'T:
- Create overlapping loop blocks
- Set iterations > 100 (system limit)
- Loop single steps (just duplicate the step instead)
- Forget to verify loop blocks before execution

---

## 🧪 How to Test Your Loop

### After Creating a Loop:

1. **Save Changes**
   - Loop blocks auto-save with test steps
   - Watch for "Saved" indicator

2. **Execute Test**
   - Click "Run Test" button in test detail page
   - Monitor execution status

3. **Check Logs**
   - Look for "(iter X/Y)" in step descriptions
   - Verify correct number of iterations

4. **View Screenshots**
   - Check execution detail page
   - Screenshots named with iteration numbers

5. **Verify Results**
   - Check all iterations completed
   - Verify final test status (passed/failed)

---

## 🔧 Troubleshooting

### Problem: "Create Loop" button is disabled

**Cause:** Test has fewer than 2 steps  
**Solution:** Add more test steps (minimum 2 required)

---

### Problem: Can't create loop - validation error

**Cause:** Invalid range or overlap  
**Solution:** 
- Check error message details
- Adjust step range to avoid overlap
- Ensure end step ≥ start step

---

### Problem: Loop doesn't execute as expected

**Cause:** Loop blocks not saved  
**Solution:**
- Check test detail page shows loop blocks
- Re-save test if needed
- Verify loop blocks in database (test_data field)

---

### Problem: Too many executions

**Cause:** Loop iterations set too high  
**Solution:**
- Delete existing loop
- Create new loop with fewer iterations
- Test with 2-3 iterations first

---

## 📊 Execution Time Estimates

### Approximate time per loop iteration:

| Loop Type | Steps | Time/Iter | 5 Iterations | 10 Iterations |
|-----------|-------|-----------|--------------|---------------|
| Upload file | 3 | 5 sec | 25 sec | 50 sec |
| Fill form | 5 | 8 sec | 40 sec | 1.5 min |
| Check item | 2 | 3 sec | 15 sec | 30 sec |
| Navigate | 4 | 6 sec | 30 sec | 1 min |

**Note:** Times vary based on page load speed and browser automation

---

## ✅ Success Checklist

After creating a loop block, verify:

- [ ] Loop appears in "Active Loops" list
- [ ] Loop metadata is correct (steps, iterations)
- [ ] Execution preview matches expectations
- [ ] Can delete and recreate loop
- [ ] Test saves successfully
- [ ] Test executes with loop iterations
- [ ] Logs show "(iter X/Y)" markers
- [ ] Screenshots captured for each iteration
- [ ] Final test status is correct

---

## 🎉 You're Ready!

You now know how to:
- ✅ Create loop blocks visually
- ✅ Understand execution previews
- ✅ Validate loop configurations
- ✅ Execute tests with loops
- ✅ Troubleshoot common issues

**Start creating loops to make your tests more efficient!**

---

## 📚 Additional Resources

- **Full Documentation:** `LOOP-UI-EDITOR-COMPLETE.md`
- **Quick Summary:** `LOOP-UI-EDITOR-SUMMARY.md`
- **Implementation Checklist:** `LOOP-UI-EDITOR-CHECKLIST.md`
- **Backend Documentation:** `SPRINT-5.5-ENHANCEMENT-2-COMPLETE.md`

---

**Created:** January 22, 2026  
**For:** End Users & Testers  
**Status:** Production Ready ✅
