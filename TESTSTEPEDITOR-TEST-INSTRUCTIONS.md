# TestStepEditor - Testing Instructions

## ✅ Integration Complete!

**Status:** TestStepEditor component successfully integrated into TestDetailPage  
**Time:** December 23, 2025  
**Developer:** Developer A

---

## 🎯 What Was Done

### 1. Component Created
- ✅ `frontend/src/components/TestStepEditor.tsx` (215 lines)
- ✅ Features: Auto-save, manual save, version tracking, error handling
- ✅ Styling: Tailwind CSS with beautiful UI

### 2. Integration Complete
- ✅ Imported into TestDetailPage.tsx
- ✅ Replaced static test steps display
- ✅ Connected to backend API: `PUT /api/v1/tests/{id}/steps`
- ✅ TypeScript: No errors ✅

### 3. Dependencies Installed
- ✅ lodash (for debounce)
- ✅ @types/lodash (TypeScript types)

---

## 🧪 Testing Steps

### Step 1: Navigate to Test Detail Page

1. **Open browser:** http://localhost:3000
2. **Login** (if not already logged in):
   - Username: `admin`
   - Password: `admin123`
3. **Click on any test** from the Tests page
4. **Or navigate directly:** http://localhost:3000/tests/1

---

### Step 2: Find the TestStepEditor

Look for the **"Test Steps"** section on the test detail page.

You should see:
- ✅ A large textarea for editing
- ✅ Version number in the header (e.g., "Test Steps (v1)")
- ✅ "Save Now" button on the right
- ✅ Helper text at bottom: "ⓘ Changes auto-saved 2 seconds after typing"

---

### Step 3: Test Auto-Save Feature

1. **Click in the textarea**
2. **Type something** (e.g., add a new step):
   ```
   1. Navigate to https://example.com
   2. Click login button
   3. Enter credentials
   ```
3. **Stop typing and wait 2 seconds**
4. **Watch for indicators:**
   - "💾 Saving..." (appears briefly)
   - Then "✓ Saved X seconds ago" (appears after save)
5. **Check version number:**
   - Should update (e.g., v1 → v2)

---

### Step 4: Test Manual Save

1. **Type something new**
2. **Click "Save Now" button immediately** (don't wait)
3. **Should see:**
   - Button text changes to "Saving..."
   - Then back to "Save Now"
   - "✓ Saved X seconds ago" appears
   - Version number increments

---

### Step 5: Verify Backend Integration

**Open Browser DevTools (F12)**

1. **Console Tab:**
   - Look for: `"New version saved: 2"` (or higher number)
   - No errors should appear

2. **Network Tab:**
   - Filter by "steps"
   - Make an edit
   - Wait 2 seconds
   - **You should see:**
     - Request: `PUT http://localhost:8000/api/v1/tests/1/steps`
     - Status: 200 OK
     - Response: `{"id": 1, "version_number": 2, "message": "..."}`

---

### Step 6: Test Backend API Directly

**Open Swagger UI:** http://localhost:8000/docs

1. **Find endpoint:** `PUT /api/v1/tests/{test_id}/steps`
2. **Click "Try it out"**
3. **Enter:**
   - `test_id`: 1
   - Request body:
     ```json
     {
       "steps": "1. Test step\n2. Another step",
       "change_reason": "Manual test"
     }
     ```
4. **Click "Execute"**
5. **Check response:**
   ```json
   {
     "id": 1,
     "version_number": 3,
     "message": "Test steps updated and version created"
   }
   ```

---

## 🎨 Visual Verification

### Component Should Look Like This:

```
┌─────────────────────────────────────────────────────┐
│ Test Steps (v5)                    [Save Now]       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Large editable textarea]                          │
│  1. Navigate to https://example.com                 │
│  2. Click on 'Login' button                         │
│  3. Enter username and password                     │
│  4. Click Submit                                    │
│                                                     │
├─────────────────────────────────────────────────────┤
│ ✓ Saved 30 seconds ago                             │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Success Criteria

### Must Pass:
- [ ] Component renders without errors
- [ ] Can type in textarea
- [ ] Auto-save triggers after 2 seconds of inactivity
- [ ] "Saving..." indicator appears during save
- [ ] "Saved X ago" appears after successful save
- [ ] Version number displays in header
- [ ] Version number increments after save
- [ ] Manual "Save Now" button works
- [ ] Network request shows in DevTools
- [ ] Backend API responds with success

### Bonus (Nice to Have):
- [ ] Timestamp updates every 10 seconds
- [ ] "Save Now" button disabled when no changes
- [ ] Error message appears if save fails
- [ ] Placeholder text shows example format

---

## 🐛 Common Issues & Solutions

### Issue 1: Component doesn't appear
**Possible causes:**
- Frontend server not running
- Import statement incorrect
- TypeScript errors

**Solution:**
- Check: http://localhost:3000 is accessible
- Check browser console for errors
- Run: `npm run dev` in frontend directory

---

### Issue 2: "Failed to save" error
**Possible causes:**
- Backend server not running
- Authentication token expired
- Test doesn't exist

**Solution:**
- Check: http://localhost:8000/docs is accessible
- Clear localStorage and login again
- Verify test ID exists in database

---

### Issue 3: Auto-save not triggering
**Possible causes:**
- Debounce delay not complete (need to wait 2 seconds)
- Network request blocked by CORS
- Backend endpoint not working

**Solution:**
- Wait full 2 seconds after typing
- Check Network tab in DevTools
- Test endpoint manually in Swagger UI

---

### Issue 4: Version number not updating
**Possible causes:**
- API response missing version_number
- State not updating correctly

**Solution:**
- Check API response in Network tab
- Check console logs for response data
- Refresh page to see latest version

---

## 📊 Testing Checklist

### Basic Functionality
- [ ] Page loads without errors
- [ ] Textarea is editable
- [ ] Can type and delete text
- [ ] Placeholder text shows when empty

### Auto-Save
- [ ] Typing starts auto-save timer
- [ ] Timer resets if keep typing
- [ ] Saves after 2 seconds of inactivity
- [ ] "Saving..." indicator appears
- [ ] Success message appears after save

### Manual Save
- [ ] Button is clickable
- [ ] Button shows "Saving..." during save
- [ ] Saves immediately without delay
- [ ] Version number updates

### Version Tracking
- [ ] Version number displays in header
- [ ] Version increments after each save
- [ ] Version persists after page refresh

### Error Handling
- [ ] Network errors show error message
- [ ] 404 errors handled gracefully
- [ ] Authentication errors handled

---

## 📈 Next Steps After Testing

### If Everything Works ✅
1. **Celebrate!** 🎉 Component 1 of 4 complete
2. **Commit the changes:**
   ```powershell
   git add frontend/src/components/TestStepEditor.tsx
   git add frontend/src/pages/TestDetailPage.tsx
   git commit -m "feat: Add TestStepEditor component with auto-save and version tracking"
   ```
3. **Move to Component 2:** VersionHistoryPanel (3-4 hours)

### If Issues Found ❌
1. **Document the issue** (what, when, how to reproduce)
2. **Check console errors**
3. **Check network requests**
4. **Ask for help or debug step by step**

---

## 🎯 Performance Notes

### What to Watch:
- **Network Requests:** Should only trigger after 2-second delay
- **Re-renders:** Component should not re-render excessively
- **Memory:** Debounce should clean up properly

### Expected Behavior:
- Typing 10 characters quickly = **1 API call** (not 10)
- Manual save = **1 immediate API call**
- No memory leaks after component unmounts

---

## 🚀 Sprint 4 Progress

| Component | Status | Time Spent | Notes |
|-----------|--------|------------|-------|
| TestStepEditor | ✅ Complete | ~2 hours | Integrated & ready to test |
| VersionHistoryPanel | ⏳ Next | - | Shows version list |
| VersionCompareDialog | ⏳ Pending | - | Compare 2 versions |
| RollbackConfirmDialog | ⏳ Pending | - | Confirm rollback |

**Total Progress:** 25% complete (1 of 4 components)

---

## 📝 Quick Reference

### Component Props:
```typescript
<TestStepEditor
  testId={number}              // Required: Test case ID
  initialSteps={string}        // Required: Initial content
  initialVersion={number}      // Optional: Current version
  onSave={(version) => {...}}  // Optional: Callback after save
/>
```

### API Endpoint:
```
PUT /api/v1/tests/{test_id}/steps

Request:
{
  "steps": "1. Step one\n2. Step two",
  "change_reason": "Auto-save edit"
}

Response:
{
  "id": 1,
  "version_number": 5,
  "message": "Test steps updated and version created"
}
```

---

**Ready to test?** Open http://localhost:3000/tests/1 and try it out! 🚀

---

## 📚 Related Files

- `TestStepEditor.tsx` - The component
- `TestDetailPage.tsx` - Integration point
- `TESTSTEPEDITOR-INTEGRATION-GUIDE.md` - Integration details
- `SPRINT-4-FRONTEND-START.md` - Overall plan
- `backend/app/api/v1/endpoints/versions.py` - Backend API
