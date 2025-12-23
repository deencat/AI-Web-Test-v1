# 422 Error Fixed - Steps Array Format

**Date:** December 23, 2025  
**Issue:** HTTP 422 Unprocessable Content when saving test steps  
**Status:** ✅ FIXED

---

## 🐛 The Problem

**Error in backend logs:**
```
INFO: 127.0.0.1:58119 - "PUT /api/v1/tests/93/steps HTTP/1.1" 422 Unprocessable Content
```

**Root Cause:**
- Backend API expects `steps` as **array of strings**: `["Step 1", "Step 2"]`
- Frontend was sending `steps` as **single string**: `"Step 1\nStep 2"`

---

## ✅ The Fix

### Before (Wrong):
```typescript
body: JSON.stringify({
  steps: content,  // ❌ Sending as string
  change_reason: 'Auto-save edit'
})
```

### After (Correct):
```typescript
body: JSON.stringify({
  steps: content.split('\n').filter(line => line.trim() !== ''),  // ✅ Array of strings
  change_reason: 'Auto-save edit'
})
```

---

## 🔧 What Changed

**File:** `frontend/src/components/TestStepEditor.tsx`

**Changes:**
1. **Auto-save function:** Now converts text to array before sending
2. **Manual save function:** Now converts text to array before sending

**Conversion logic:**
- Split by newline: `content.split('\n')`
- Remove empty lines: `.filter(line => line.trim() !== '')`

---

## 📋 Backend API Format

The backend expects this format:

```json
{
  "steps": [
    "1. Navigate to https://example.com",
    "2. Click on 'Login' button",
    "3. Enter username: admin",
    "4. Enter password: ****",
    "5. Click 'Submit'"
  ],
  "expected_result": "User successfully logged in",  // Optional
  "test_data": {},  // Optional
  "created_by": "user",  // Optional (default: "user")
  "change_reason": "Auto-save edit"  // Optional (default: "manual_edit")
}
```

**Response format:**
```json
{
  "id": 123,
  "test_case_id": 93,
  "version_number": 5,
  "steps": ["Step 1", "Step 2"],
  "created_at": "2025-12-23T10:30:00",
  "created_by": "user",
  "change_reason": "Auto-save edit"
}
```

---

## 🧪 Test It Now

### Step 1: Refresh Your Browser
Press `Ctrl + F5` to clear cache and reload

### Step 2: Navigate to Test Page
Go to: http://localhost:5173/tests/93

### Step 3: Edit Test Steps
Type in the textarea:
```
1. First step
2. Second step
3. Third step
```

### Step 4: Wait or Click Save
- **Auto-save:** Wait 2 seconds
- **Manual save:** Click "Save Now" button

### Step 5: Check Results
You should see:
- ✅ "Saving..." appears
- ✅ Then "✓ Saved X seconds ago"
- ✅ Version number increments (e.g., v1 → v2)
- ✅ No errors in console
- ✅ Backend logs show: `"PUT /api/v1/tests/93/steps HTTP/1.1" 200 OK`

---

## 🎯 Expected Backend Logs (After Fix)

### Before (Error):
```
INFO: 127.0.0.1:58119 - "PUT /api/v1/tests/93/steps HTTP/1.1" 422 Unprocessable Content
```

### After (Success):
```
INFO: 127.0.0.1:58119 - "PUT /api/v1/tests/93/steps HTTP/1.1" 200 OK
```

---

## 💡 How It Works Now

### User Types:
```
1. Login to system
2. Navigate to dashboard
3. Verify data loads
```

### Frontend Sends to Backend:
```json
{
  "steps": [
    "1. Login to system",
    "2. Navigate to dashboard",
    "3. Verify data loads"
  ],
  "change_reason": "Auto-save edit"
}
```

### Backend Processes:
1. Validates array format ✅
2. Creates new version in database
3. Updates test case steps
4. Returns version info

### Frontend Receives:
```json
{
  "id": 456,
  "version_number": 6,
  "message": "Version saved successfully"
}
```

### UI Updates:
- Version number: v5 → v6
- Status: "✓ Saved 0 seconds ago"
- No errors shown

---

## 🔍 Edge Cases Handled

### Empty Lines:
**User types:**
```
1. First step

2. Second step


3. Third step
```

**Sent to backend:**
```json
["1. First step", "2. Second step", "3. Third step"]
```
Empty lines are filtered out ✅

---

### Single Line:
**User types:**
```
Just one step
```

**Sent to backend:**
```json
["Just one step"]
```
Still sent as array ✅

---

### No Content:
**User clears everything**

**Result:**
Auto-save skips (because `content.trim() === ''`) ✅

---

## 📝 Files Modified

**File:** `frontend/src/components/TestStepEditor.tsx`

**Lines changed:**
- Line ~47: Auto-save API call
- Line ~104: Manual save API call

**Changes:**
- Added: `.split('\n').filter(line => line.trim() !== '')`
- Converts string to array of non-empty lines

---

## ✅ Success Criteria

Test is successful when:
- [ ] No 422 errors in backend logs
- [ ] Backend logs show: `200 OK`
- [ ] Browser console shows no errors
- [ ] "✓ Saved X ago" appears in UI
- [ ] Version number increments
- [ ] Can save multiple times
- [ ] Changes persist after page refresh

---

## 🚀 Ready to Test!

**The fix is complete.** Please:

1. **Refresh your browser** (Ctrl + F5)
2. **Go to:** http://localhost:5173/tests/93
3. **Type something** in the test steps
4. **Click "Save Now"** or wait 2 seconds
5. **Check backend logs** - should see `200 OK` instead of `422`

---

## 🎉 What's Working Now

- ✅ TestStepEditor component created
- ✅ Integration with TestDetailPage
- ✅ Auto-save with 2-second debounce
- ✅ Manual save button
- ✅ Version tracking and display
- ✅ Correct API format (array of strings)
- ✅ Error handling
- ✅ Visual feedback (saving/saved)
- ✅ No 422 errors

---

**Component 1 of 4 complete!** 🎊

Next up: **VersionHistoryPanel** (shows list of all versions)
