# Blank Screen Debugging Guide

## Issue: Blank Screen on http://localhost:5173/tests/94

**Date:** December 23, 2025  
**Status:** Investigating

---

## ✅ Fixes Applied

1. **Port corrected:** Application runs on **5173** (Vite default), not 3000
2. **TestStepEditor updated:** Better error handling and authentication checks
3. **TestDetailPage updated:** Added conditional rendering for TestStepEditor
4. **Initial version default:** Set to 1 if not provided

---

## 🔍 Debugging Steps

### Step 1: Check Browser Console

**Open DevTools (F12) → Console Tab**

Look for errors like:
- ❌ "Cannot read property '...' of null/undefined"
- ❌ "Failed to fetch"
- ❌ "404 Not Found"
- ❌ "401 Unauthorized"
- ❌ Component rendering errors

**Copy the full error message if you see one.**

---

### Step 2: Check Network Tab

**Open DevTools (F12) → Network Tab**

1. Refresh the page
2. Look for the request to: `http://localhost:8000/api/v1/tests/94`
3. **Check status code:**
   - ✅ 200 OK = Test exists
   - ❌ 404 Not Found = Test ID 94 doesn't exist
   - ❌ 401 Unauthorized = Not logged in
   - ❌ 500 Server Error = Backend issue

4. **Click on the request** and check the Response tab

---

### Step 3: Verify Test ID Exists

**Option A: Check via Swagger UI**

1. Open: http://localhost:8000/docs
2. Find: `GET /api/v1/tests/{test_id}`
3. Click "Try it out"
4. Enter test_id: `94`
5. Click "Execute"
6. **Check response:**
   - If 200: Test exists
   - If 404: Test doesn't exist - try a different ID

**Option B: Check via Tests Page**

1. Go to: http://localhost:5173/tests
2. Look for test ID 94 in the list
3. If not found, click on any other test

---

### Step 4: Check Authentication

**Open DevTools → Application Tab → Local Storage**

1. Find: `http://localhost:5173`
2. Look for key: `token`
3. **If missing:**
   - You need to login first
   - Go to: http://localhost:5173/login
   - Login with: `admin` / `admin123`

---

### Step 5: Temporary Fallback (Test Without TestStepEditor)

If the issue persists, let's temporarily comment out the TestStepEditor to isolate the problem.

**Edit: `frontend/src/pages/TestDetailPage.tsx`**

Comment out the TestStepEditor section:

```tsx
{/* Test Steps */}
<Card>
  <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Steps</h2>
  {/* TEMPORARILY DISABLED FOR DEBUGGING */}
  {/*
  <TestStepEditor
    testId={typeof test.id === 'string' ? parseInt(test.id) : test.id}
    initialSteps={Array.isArray(test.steps) ? test.steps.join('\n') : (test.steps || '')}
    initialVersion={test.current_version || 1}
    onSave={(versionNumber) => {
      console.log('New version saved:', versionNumber);
      setTest({ ...test, current_version: versionNumber });
    }}
  />
  */}
  
  {/* TEMPORARY: Show raw steps */}
  <pre className="p-4 bg-gray-50 rounded">
    {Array.isArray(test.steps) ? test.steps.join('\n') : test.steps}
  </pre>
</Card>
```

**Then refresh the page.** If the page loads now, the issue is with TestStepEditor.

---

## 🐛 Common Causes & Solutions

### Cause 1: Test ID 94 Doesn't Exist

**Solution:**
1. Go to: http://localhost:5173/tests
2. Pick an existing test ID
3. Or create a new test first

---

### Cause 2: Not Logged In

**Solution:**
1. Go to: http://localhost:5173/login
2. Login: `admin` / `admin123`
3. Try accessing test page again

---

### Cause 3: Backend Not Running

**Solution:**
1. Open terminal in `backend` directory
2. Activate venv: `.\venv\Scripts\activate`
3. Start server: `python -m uvicorn app.main:app --reload`
4. Verify: http://localhost:8000/docs should load

---

### Cause 4: CORS Issue

**Symptoms:**
- Console shows: "CORS policy blocked"
- Network tab shows failed requests

**Solution:**
- Backend should have CORS enabled
- Check `backend/app/main.py` for CORS middleware

---

### Cause 5: TestStepEditor Component Error

**Symptoms:**
- Page was working before adding TestStepEditor
- Console shows component-related error

**Solution:**
- Check console for specific error
- Try the temporary fallback (Step 5 above)
- Check if lodash is installed: `npm list lodash`

---

## 🔧 Quick Fixes

### Fix 1: Reinstall Dependencies

```powershell
cd frontend
npm install
```

---

### Fix 2: Clear Browser Cache

1. Press F12 (DevTools)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

---

### Fix 3: Check Backend Database

```powershell
cd backend
.\venv\Scripts\activate
python -c "from app.database import SessionLocal; from app.models.test_case import TestCase; db = SessionLocal(); tests = db.query(TestCase).all(); print(f'Total tests: {len(tests)}'); print('Test IDs:', [t.id for t in tests[:10]]); db.close()"
```

This will show you which test IDs actually exist.

---

## 📊 Diagnostic Checklist

Run through this checklist:

- [ ] Backend server running (http://localhost:8000/docs loads)
- [ ] Frontend server running (http://localhost:5173 loads)
- [ ] Logged in (token in localStorage)
- [ ] Test ID exists (verified in Swagger or tests page)
- [ ] No console errors in browser
- [ ] Network requests successful (200 OK)
- [ ] lodash installed (`npm list lodash`)
- [ ] No TypeScript errors

---

## 🚀 Next Steps Based on Results

### If Console Shows Error:
**→ Copy the exact error message and we'll fix it**

### If Network Shows 404:
**→ Test ID 94 doesn't exist, try a different ID**

### If Network Shows 401:
**→ Need to login first**

### If Page Still Blank:
**→ Try the temporary fallback (comment out TestStepEditor)**

### If Fallback Works:
**→ Issue is with TestStepEditor component, we'll debug that**

---

## 📝 What to Share for Help

Please provide:

1. **Console errors** (screenshot or copy text)
2. **Network tab** for the /tests/94 request (status code + response)
3. **Result of this command:**
   ```powershell
   cd frontend
   npm list lodash
   ```
4. **Does test ID 94 exist?** (check in tests page or Swagger)

---

## 🔄 Rollback Option

If you want to go back to the old version temporarily:

```powershell
cd frontend/src/pages
git checkout HEAD~1 TestDetailPage.tsx
```

This will restore the previous version without TestStepEditor.

---

**Let's find out what's causing the blank screen!** 🔍

Check the console first and let me know what you see.
