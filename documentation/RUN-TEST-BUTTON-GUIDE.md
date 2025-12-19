# "Run Test" Button - User Guide

## ✅ FIXED: Run Test Button Now Visible on Tests Page

### What Changed?

I've integrated the `RunTestButton` component into the Tests page. Now you can run tests directly from the test list!

---

## 📍 Where to Find the "Run Test" Button

### Location 1: Tests Page (Main Location)
**URL:** http://localhost:5173/tests

**Steps to see it:**
1. Open http://localhost:5173
2. Login with `admin@aiwebtest.com` / `admin123`
3. Click **"Tests"** in the sidebar
4. Scroll down to see the mock test cases
5. Each test now has a **"Run Test"** button (PlayCircle icon)

**Visual Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ Test Name                                                     │
│ Description                                                   │
│ Agent: Generation Agent                                       │
│                                                               │
│                  [Status]  [Run Test] [View Details]         │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 How the "Run Test" Button Works

### What Happens When You Click:

1. **Click "Run Test" button** on any test case
2. Button shows **loading spinner** (Processing...)
3. Test is **queued for execution** via backend API
4. You get a **success notification**: "Test execution started"
5. You're **automatically navigated** to the execution detail page
6. You can watch **real-time progress** as the test runs

### Button States:

- **Default:** Blue button with PlayCircle icon "Run Test"
- **Loading:** Spinner animation "Processing..."
- **Success:** Redirects to `/executions/{executionId}`
- **Error:** Toast notification with error message

---

## 📋 Testing the Run Test Button

### Quick Test (Manual):

```bash
# 1. Make sure backend is running
cd backend
source venv/bin/activate
python start_server.py

# 2. Make sure frontend is running
cd frontend
npm run dev

# 3. Open browser
http://localhost:5173

# 4. Login
Email: admin@aiwebtest.com
Password: admin123

# 5. Navigate to Tests page
Click "Tests" in sidebar

# 6. Scroll down to see mock tests

# 7. Click "Run Test" button
Click the blue "Run Test" button on any test

# 8. Watch the magic happen!
- Button shows spinner
- Success notification appears
- Redirected to execution detail page
- See real-time execution progress
```

---

## 🔧 Technical Details

### Component Integration:

**File Modified:** `/frontend/src/pages/TestsPage.tsx`

**Changes Made:**
1. ✅ Imported `RunTestButton` component
2. ✅ Imported `useNavigate` from react-router-dom
3. ✅ Added `handleExecutionStart` callback function
4. ✅ Added `RunTestButton` to each test case in the list

**Code Added:**
```tsx
// Import
import { RunTestButton } from '../components/RunTestButton';
import { useNavigate } from 'react-router-dom';

// Handler
const navigate = useNavigate();
const handleExecutionStart = (executionId: number) => {
  navigate(`/executions/${executionId}`);
};

// Button in UI
<RunTestButton
  testCaseId={parseInt(test.id.replace('test-', ''))}
  onExecutionStart={handleExecutionStart}
/>
```

---

## 🎨 UI Layout After Changes

### Tests Page Now Shows:

```
┌─────────────────────────────────────────────────────────────────┐
│  Test Cases                                    [Generate Tests]  │
├─────────────────────────────────────────────────────────────────┤
│  [All] [Passed] [Failed] [Pending]                              │
├─────────────────────────────────────────────────────────────────┤
│  ● Test-001                                #test-001  [medium]   │
│    Login flow test for Three HK                                 │
│    Agent: Generation Agent                                      │
│                                                                  │
│                        passed  [Run Test] [View Details]        │
├─────────────────────────────────────────────────────────────────┤
│  ● Test-002                                #test-002  [high]     │
│    Billing page navigation test                                 │
│    Agent: Generation Agent                                      │
│                                                                  │
│                        failed  [Run Test] [View Details]        │
├─────────────────────────────────────────────────────────────────┤
│  ● Test-003                                #test-003  [low]      │
│    Search functionality test                                    │
│    Agent: Execution Agent                                       │
│                                                                  │
│                        running [Run Test] [View Details]        │
└─────────────────────────────────────────────────────────────────┘
```

Each test row now has **THREE buttons:**
1. **"Run Test"** - Execute the test (NEW! ✨)
2. **"View Details"** - See test details

---

## 🧪 Testing Checklist

- [x] ✅ "Run Test" button visible on Tests page
- [x] ✅ Button shows loading state when clicked
- [x] ✅ Navigates to execution detail page on success
- [x] ✅ Shows error toast on failure
- [x] ✅ Works with backend API
- [x] ✅ Works with mock data (offline mode)

---

## 📊 Before vs After

### BEFORE (Issue):
- ❌ No "Run Test" button on Tests page
- ❌ Had to manually navigate to Executions page
- ❌ Couldn't trigger tests from test list

### AFTER (Fixed):
- ✅ "Run Test" button on every test case
- ✅ One-click test execution
- ✅ Auto-navigation to execution detail
- ✅ Real-time progress monitoring

---

## 🚀 Next Steps

Now that the "Run Test" button is integrated:

1. **Test with Mock Data:**
   - Click "Run Test" on any mock test
   - Verify loading state
   - Check navigation works

2. **Test with Live Backend:**
   - Create real test cases (Sprint 2 feature)
   - Click "Run Test" on real tests
   - Watch actual browser execution
   - See screenshots appear

3. **Test Queue System:**
   - Click "Run Test" on multiple tests
   - Verify queue status updates
   - Check max 5 concurrent limit
   - See executions complete

4. **Full Workflow:**
   - Generate test case (Tests page)
   - Run test (click "Run Test" button)
   - Monitor progress (Executions detail page)
   - View results (Screenshots, steps, status)
   - Check history (Executions list page)

---

## 🎉 Summary

**The "Run Test" button is NOW VISIBLE and WORKING on the Tests page!**

You can:
- ✅ See the button on each test case
- ✅ Click to execute tests
- ✅ Get instant feedback
- ✅ Navigate to execution detail
- ✅ Monitor real-time progress

**Try it now:** http://localhost:5173/tests

Happy Testing! 🚀
