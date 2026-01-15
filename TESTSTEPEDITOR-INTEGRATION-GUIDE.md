# TestStepEditor Integration Guide

## ✅ Component Created Successfully

**File:** `frontend/src/components/TestStepEditor.tsx`  
**Lines:** 215 lines  
**Status:** Ready to integrate

---

## 🎯 Features Implemented

- ✅ Auto-save with 2-second debounce
- ✅ Manual "Save Now" button
- ✅ "Saving..." indicator
- ✅ "Saved X ago" timestamp (updates every 10 seconds)
- ✅ Version number display (e.g., "v5")
- ✅ Error handling with red error messages
- ✅ Tailwind CSS styling
- ✅ Placeholder text with example format
- ✅ Disabled button when no changes

---

## 📥 How to Integrate

### Step 1: Import the Component

In `frontend/src/pages/TestDetailPage.tsx`, add:

```typescript
import { TestStepEditor } from '../components/TestStepEditor';
```

### Step 2: Replace Existing Steps Textarea

Find the existing textarea for test steps (search for "steps" or "Test Steps"):

**BEFORE:**
```typescript
<textarea
  value={testCase.steps}
  onChange={(e) => handleChange('steps', e.target.value)}
  className="..."
/>
```

**AFTER:**
```typescript
<TestStepEditor
  testId={testCase.id}
  initialSteps={testCase.steps}
  initialVersion={testCase.current_version || 1}
  onSave={(versionNumber) => {
    console.log('New version saved:', versionNumber);
    // Optionally refresh test case data
  }}
/>
```

---

## 🔧 Component Props

```typescript
interface TestStepEditorProps {
  testId: number;              // Required: Test case ID
  initialSteps: string;        // Required: Initial content
  initialVersion?: number;     // Optional: Current version (default: 1)
  onSave?: (versionNumber: number) => void;  // Optional: Callback after save
}
```

### Example Usage:

```typescript
<TestStepEditor
  testId={123}
  initialSteps="1. Login\n2. Navigate\n3. Verify"
  initialVersion={5}
  onSave={(version) => {
    // Update parent component state
    setTestCase({ ...testCase, current_version: version });
  }}
/>
```

---

## 🧪 Testing Steps

### 1. Open Test Detail Page
- Navigate to: http://localhost:3000/tests/1 (or any test ID)
- You should see the new TestStepEditor component

### 2. Test Auto-Save
1. Type something in the textarea
2. Wait 2 seconds
3. Should see "💾 Saving..." appear
4. Then see "✓ Saved X seconds ago"

### 3. Test Manual Save
1. Type something
2. Click "Save Now" button immediately
3. Should save without waiting 2 seconds

### 4. Test Version Display
1. After saving, version number should update
2. Example: "(v1)" becomes "(v2)"

### 5. Check Console
- Open browser DevTools (F12)
- Check Console tab for any errors
- Should see network request to: PUT `/api/v1/tests/{id}/steps`

### 6. Check Network Tab
- Open DevTools → Network tab
- Make a change
- Wait 2 seconds
- Should see PUT request with:
  - URL: `http://localhost:8000/api/v1/tests/{id}/steps`
  - Method: PUT
  - Body: `{"steps": "...", "change_reason": "Auto-save edit"}`

---

## 🎨 Styling

Component uses **Tailwind CSS** classes:

- `bg-blue-600` - Blue save button
- `text-gray-700` - Dark gray labels
- `border-gray-300` - Light gray borders
- `focus:ring-2 focus:ring-blue-500` - Blue focus ring
- `disabled:bg-gray-400` - Gray disabled state

**Customization:**
Change colors in the JSX by modifying Tailwind classes.

---

## 🔌 API Integration

### Endpoint Used:
```
PUT /api/v1/tests/{testId}/steps
```

### Request:
```json
{
  "steps": "1. Login\n2. Navigate\n3. Verify",
  "change_reason": "Auto-save edit"
}
```

### Response (Success):
```json
{
  "id": 123,
  "version_number": 5,
  "message": "Test steps updated and version created"
}
```

### Response (Error):
```json
{
  "detail": "Test not found"
}
```

---

## 🐛 Troubleshooting

### Issue: Component doesn't render
**Check:**
1. Import statement correct?
2. TypeScript errors in component?
3. Browser console for errors?

### Issue: Auto-save not working
**Check:**
1. Wait full 2 seconds after typing
2. Backend server running? (http://localhost:8000)
3. Network tab shows PUT request?
4. Token in localStorage?

### Issue: "Failed to save" error
**Check:**
1. Backend API endpoint working? (Test in Swagger: http://localhost:8000/docs)
2. CORS enabled on backend?
3. Valid authentication token?
4. Test ID exists in database?

### Issue: Version number doesn't update
**Check:**
1. API response contains `version_number`?
2. `setCurrentVersion()` being called?
3. Console logs for response data?

---

## 💡 Next Steps

### After Testing TestStepEditor:

**Component 2: VersionHistoryPanel** (3-4 hours)
- Shows list of all versions
- Displays version metadata (number, date, author, reason)
- Buttons to view, compare, rollback

**Component 3: VersionCompareDialog** (2-3 hours)
- Side-by-side comparison of two versions
- Highlights differences
- Shows what changed

**Component 4: RollbackConfirmDialog** (1-2 hours)
- Confirmation before rollback
- Warning message
- Rollback action

---

## 📊 Progress Tracking

### Sprint 4 - Test Versioning Frontend

| Component | Status | Time | Notes |
|-----------|--------|------|-------|
| TestStepEditor | ✅ Complete | ~1 hour | Created & ready |
| Integration | ⏳ Next | 30 min | Add to TestDetailPage |
| VersionHistoryPanel | ⏳ Pending | 3-4 hours | Start after integration |
| VersionCompareDialog | ⏳ Pending | 2-3 hours | Day 2 |
| RollbackConfirmDialog | ⏳ Pending | 1-2 hours | Day 2 |

---

## 📝 Code Quality

### What's Good:
- ✅ TypeScript interfaces defined
- ✅ Error handling implemented
- ✅ Loading states (isSaving)
- ✅ Debounce prevents excessive API calls
- ✅ Visual feedback (saving/saved/error)
- ✅ Accessible (proper labels, disabled states)
- ✅ Responsive design

### Potential Improvements (Later):
- Add keyboard shortcuts (Ctrl+S to save)
- Add undo/redo functionality
- Add confirmation before losing unsaved changes
- Add rich text editor (Markdown support)
- Add syntax highlighting for steps

---

## 🚀 Quick Start

**Right now, you can:**

1. **Test the component standalone:**
   - Open: http://localhost:3000
   - Find test detail page
   - Look for TestStepEditor

2. **Integrate into TestDetailPage:**
   - Edit: `frontend/src/pages/TestDetailPage.tsx`
   - Import: `import { TestStepEditor } from '../components/TestStepEditor';`
   - Replace existing steps textarea with `<TestStepEditor ... />`

3. **Verify it works:**
   - Type in textarea
   - Wait 2 seconds
   - Check "Saved X ago" message
   - Check version number updates

---

**🎉 Congratulations! Component 1 of 4 is complete!**

**Estimated remaining time:** 13-20 hours for other 3 components + integration

---

## 📚 Related Files

- `TestStepEditor.tsx` - The component (just created)
- `FRONTEND-COMPONENT-1-GUIDE.md` - Detailed component guide
- `SPRINT-4-FRONTEND-START.md` - Overall frontend plan
- `backend/app/api/v1/endpoints/versions.py` - Backend API
- `NEXT-STEPS-SPRINT-4.md` - Sprint 4 complete plan
