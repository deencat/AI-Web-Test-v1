# Tests Page - Complete UI Testing Guide

## 🎯 Overview

The Tests Page supports the complete CRUD workflow for test cases:
- **CREATE**: Generate tests with AI OR manually create
- **READ**: View generated tests and saved tests
- **UPDATE**: Edit test details (title, description, steps, priority)
- **DELETE**: Remove tests from database
- **EXECUTE**: Run tests with Stagehand/Playwright

---

## 📋 UI Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tests Page - Main View                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴──────────────┐
                │                            │
        [Generate New Tests]          [Saved Tests Section]
                │                            │
                ▼                            ▼
┌───────────────────────────┐    ┌──────────────────────────┐
│   Test Generation Form    │    │  Saved Tests List View   │
│                           │    │                          │
│  Text Area:               │    │  Filter Buttons:         │
│  "Describe test..."       │    │  [All] [Passed] [Failed] │
│                           │    │  [Pending]               │
│  [Generate Test Cases]    │    │                          │
└─────────────┬─────────────┘    │  Test Cards:             │
              │                  │  ┌──────────────────┐    │
              │ AI generates     │  │ 🟢 Test #123     │    │
              ▼                  │  │ Title: Three.hk  │    │
┌───────────────────────────┐    │  │ Status: Pending  │    │
│  Generated Tests Display  │    │  │ Priority: High   │    │
│                           │    │  │                  │    │
│  ┌─────────────────────┐  │    │  │ [Run] [View]     │    │
│  │ Test Case #1        │  │    │  │ [Edit] [Delete]  │    │
│  │ Title: ...          │  │    │  └──────────────────┘    │
│  │ Steps: 24           │  │    └──────────────────────────┘
│  │ Priority: High      │  │
│  │                     │  │
│  │ [Edit] [Save] [X]   │  │
│  └─────────────────────┘  │
└─────────────┬─────────────┘
              │
              │ User clicks [Save]
              ▼
┌───────────────────────────┐
│   Saved to Database       │
│   → Redirects to Saved    │
│      Tests Section        │
└───────────────────────────┘
```

---

## 🧪 Manual Testing Steps

### Test 1: AI Test Generation

**Steps:**
1. Open browser: `http://localhost:5173/tests`
2. You should see "Generate test cases using natural language"
3. In the text area, enter:
   ```
   Test the Three.com.hk 5G Broadband subscription flow at https://web.three.com.hk/5gbroadband/plan-hsbc-en.html
   
   The test should select the 30 months contract period, verify pricing ($135/month), 
   click Subscribe Now, handle popups, proceed through checkout, and complete login.
   ```
4. Click **"Generate Test Cases"** button
5. Wait 2-5 seconds for AI to generate tests
6. You should see generated test(s) displayed below

**Expected Results:**
- ✅ Loading spinner appears while generating
- ✅ Generated test appears with title, description, steps
- ✅ Test shows priority (high/medium/low)
- ✅ Step count displayed (should be ~15-25 steps)
- ✅ Buttons visible: [Edit] [Save to Tests] [Discard]

---

### Test 2: View Generated Test

**Steps:**
1. After generation, review the test card
2. Check the test details:
   - Title
   - Description
   - Number of steps
   - Priority level
3. Expand to see all steps (if collapsible)

**Expected Results:**
- ✅ All test details visible
- ✅ Steps are logical and in correct order
- ✅ Expected result is clear

---

### Test 3: Edit Generated Test

**Steps:**
1. Click **"Edit"** button on a generated test
2. Modal or inline form should appear
3. Modify the title (add " - Edited" to the end)
4. Modify a step (change wording)
5. Change priority (High → Medium)
6. Click **"Save Changes"**

**Expected Results:**
- ✅ Edit form appears with all fields
- ✅ Fields are pre-filled with current values
- ✅ Changes are applied immediately
- ✅ Test card updates with new values

---

### Test 4: Save Test to Database

**Steps:**
1. On a generated test, click **"Save to Tests"** button
2. Test should be saved to database
3. UI should show success message or redirect
4. Generated tests section should clear
5. UI should switch to "Saved Tests" section

**Expected Results:**
- ✅ Success message appears
- ✅ Test appears in "Saved Tests" section
- ✅ Test has a unique ID number
- ✅ Status is "Pending"

---

### Test 5: View Saved Tests List

**Steps:**
1. Ensure you're in "Saved Tests" section
2. Click filter buttons: [All] [Passed] [Failed] [Pending]
3. Tests should filter based on status
4. Scroll through the list

**Expected Results:**
- ✅ All saved tests visible
- ✅ Each test shows: ID, Title, Status, Priority
- ✅ Filters work correctly
- ✅ Status indicators use correct colors:
  - 🟢 Passed = Green
  - 🔴 Failed = Red
  - 🟡 Pending = Yellow

---

### Test 6: View Test Details

**Steps:**
1. Click **"View"** or **"View Details"** button on a saved test
2. Modal or new page should show full test details
3. Review all steps, expected results, test data

**Expected Results:**
- ✅ Full test details displayed
- ✅ All steps listed in order
- ✅ Test data/parameters shown
- ✅ Expected results visible
- ✅ Close/Back button works

---

### Test 7: Edit Saved Test

**Steps:**
1. Click **"Edit"** button on a saved test
2. Edit form should appear
3. Modify title: "Three.com.hk - 5G Broadband Flow - UPDATED"
4. Add a new step at the end
5. Change priority
6. Click **"Save Changes"**
7. Refresh page and verify changes persist

**Expected Results:**
- ✅ Edit form opens with current values
- ✅ All fields are editable
- ✅ Changes save to database
- ✅ Changes persist after page refresh
- ✅ Updated timestamp changes

---

### Test 8: Execute Test (Run Test Button)

**Steps:**
1. Find a saved test (preferably the Three.com.hk test)
2. Click **"Run Test"** button
3. Modal may appear asking for execution parameters:
   - Browser: Chromium
   - Environment: Production
   - Base URL: https://web.three.com.hk/5gbroadband/plan-hsbc-en.html
4. Click **"Execute"** or **"Run"**
5. Should redirect to Executions page or show execution ID

**Expected Results:**
- ✅ Run button is visible and clickable
- ✅ Execution parameters modal appears (if implemented)
- ✅ Execution starts (API call successful)
- ✅ Redirects to `/executions/{execution_id}`
- ✅ Execution status is visible on Executions page

---

### Test 9: Delete Test

**Steps:**
1. Click **"Delete"** button on a test
2. Confirmation dialog should appear:
   "Delete test: [Test Title]?"
3. Click **"Cancel"** - test should remain
4. Click **"Delete"** again
5. Click **"Confirm"** or **"Delete"** - test should be removed

**Expected Results:**
- ✅ Confirmation dialog appears
- ✅ Cancel button works (test remains)
- ✅ Confirm button works (test deleted)
- ✅ Test disappears from list
- ✅ Success message appears
- ✅ Test removed from database (verify by refreshing)

---

### Test 10: Generate More Tests Button

**Steps:**
1. While in "Saved Tests" section
2. Click **"Generate New Tests"** button (top right)
3. Should return to test generation form
4. Generated tests section should be cleared
5. Form should be empty

**Expected Results:**
- ✅ Returns to generation form
- ✅ Previous generated tests cleared
- ✅ Text area is empty
- ✅ Ready for new test generation

---

## 🎨 UI Elements to Verify

### Test Generation Section
- [ ] Text area for requirement input
- [ ] "Generate Test Cases" button with spinner icon
- [ ] Loading spinner during generation
- [ ] Error message display for failures
- [ ] Character count (optional)

### Generated Tests Display
- [ ] Test card with all details
- [ ] Edit button
- [ ] Save to Tests button
- [ ] Discard/Delete button
- [ ] Step count indicator
- [ ] Priority badge (colored)

### Saved Tests Section
- [ ] Filter buttons (All, Passed, Failed, Pending)
- [ ] Test list with cards
- [ ] Status indicator dots/icons
- [ ] Test ID number (e.g., #123)
- [ ] Run Test button
- [ ] View button
- [ ] Edit button
- [ ] Delete button
- [ ] Empty state message if no tests

### Modals/Dialogs
- [ ] Edit test modal with form
- [ ] View test details modal
- [ ] Delete confirmation dialog
- [ ] Execution parameters modal (if applicable)

---

## 🔗 Navigation Flow

```
Tests Page (/tests)
  │
  ├─ Generate Tests
  │   └─ [Save] → Saved Tests Section
  │
  ├─ Saved Tests
  │   ├─ [View] → Test Details Modal
  │   ├─ [Edit] → Edit Form Modal
  │   ├─ [Delete] → Confirmation → Remove
  │   └─ [Run] → Executions Page (/executions/{id})
  │
  └─ [Generate New Tests] → Back to Generate Section
```

---

## 🐛 Common Issues to Check

### Generation Issues
- [ ] Error if text area is empty
- [ ] Error if requirement too short (<10 chars)
- [ ] Timeout if AI takes too long (>30s)
- [ ] Network error handling

### Save Issues
- [ ] Duplicate test prevention
- [ ] Validation (required fields)
- [ ] Database connection errors

### Display Issues
- [ ] Loading states
- [ ] Empty states
- [ ] Long test titles (truncation)
- [ ] Large step counts (scrolling)

### Execution Issues
- [ ] Invalid test ID
- [ ] Missing base_url
- [ ] Backend not running
- [ ] Execution API errors

---

## ✅ Success Criteria

All of the following should work:
1. ✅ Generate tests with AI (LLM)
2. ✅ View generated tests before saving
3. ✅ Edit test details (title, steps, priority)
4. ✅ Save generated tests to database
5. ✅ View list of all saved tests
6. ✅ Filter saved tests by status
7. ✅ View individual test details
8. ✅ Edit saved tests (persist changes)
9. ✅ Delete tests (with confirmation)
10. ✅ Execute tests (navigate to Executions)
11. ✅ Navigate between sections smoothly
12. ✅ All error states handled gracefully

---

## 📊 API Endpoints Used

| Action | Method | Endpoint | Status |
|--------|--------|----------|--------|
| Generate Tests | POST | `/api/v1/tests/generate` | ✅ Working |
| Create Test | POST | `/api/v1/tests` | ✅ Working |
| List Tests | GET | `/api/v1/tests` | ✅ Working |
| Get Test | GET | `/api/v1/tests/{id}` | ✅ Working |
| Update Test | PUT | `/api/v1/tests/{id}` | ✅ Working |
| Delete Test | DELETE | `/api/v1/tests/{id}` | ✅ Working |
| Execute Test | POST | `/api/v1/executions/tests/{id}/run` | ✅ Working |
| Get Stats | GET | `/api/v1/tests/stats` | ✅ Working |

---

## 🚀 Ready for Testing!

Open your browser and start testing:
```
http://localhost:5173/tests
```

Follow the test cases above and verify all functionality works! 🎉
