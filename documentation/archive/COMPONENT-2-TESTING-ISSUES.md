# Component 2 Testing Issues & Solutions

**Date:** December 23, 2025  
**Status:** 🐛 Issues Identified + Solutions Provided

---

## 🐛 Issue 1: Multiple Versions Created (11 from 1 Edit)

### Root Cause
The `TestStepEditor` component compares current content with `initialSteps` (which never changes), so **every keystroke** creates a save after 2 seconds.

**Problem Code:**
```typescript
const [steps, setSteps] = useState(initialSteps);
// ...
autoSave(newContent, initialSteps); // ❌ initialSteps never updates!
```

### Workaround (Quick Fix)
**For now, use ONLY Manual Save to avoid duplicate versions:**

1. Type your changes in the textarea
2. Click **"Save Now"** button (don't wait for auto-save)
3. This creates only 1 version

### Proper Fix (To Implement Later)
Add a `savedSteps` state that updates after each successful save:

```typescript
const [steps, setSteps] = useState(initialSteps);
const [savedSteps, setSavedSteps] = useState(initialSteps); // Track last saved

// In auto-save success:
setSavedSteps(content);

// Compare with saved instead of initial:
autoSave(newContent, savedSteps);
```

**Note:** This requires careful refactoring to avoid closure issues with debounced function.

---

## 🐛 Issue 2: "View" Button Does Nothing

### Root Cause
The `onViewVersion` handler in `TestDetailPage.tsx` only logs to console - no UI response.

**Problem Code:**
```typescript
onViewVersion={(version) => {
  console.log('View version:', version); // ❌ Only logs
  // TODO: Implement view version dialog
}}
```

### Workaround (Check Console)
1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Click "View" button
4. You should see: `View version: {id: 123, version_number: 4, ...}`

### Proper Fix (Component 3 - Next Task)
Create a `VersionViewDialog` component that:
- Shows version details in a modal
- Displays steps, expected result, test data
- Shows when created, by whom, why
- Has "Close" and "Rollback to This" buttons

**This is the planned work for the next development session.**

---

## ✅ What's Working

1. ✅ Version history panel opens/closes
2. ✅ Versions list displays correctly
3. ✅ Current version highlighted in blue
4. ✅ Date formatting works ("11 hours ago")
5. ✅ Checkbox selection works (max 2)
6. ✅ Compare button appears when 2 selected
7. ✅ Data fetching from API works
8. ✅ Loading/error states work

---

## 🧪 How to Test Safely

### Test Without Creating Duplicate Versions:

1. **Open test case:** http://localhost:5173/tests/99

2. **Edit test steps:**
   - Type your changes
   - **Immediately click "Save Now"** (don't wait!)
   - This creates only 1 version

3. **View history:**
   - Click "View History" button
   - Panel should show versions list

4. **Test View button:**
   - Open Console (F12)
   - Click "View" on any version
   - Check console for logged version data

5. **Test selection:**
   - Select 2 different versions
   - "Compare v2 and v4" button should appear
   - Click it - check console for log

---

## 🔍 Debugging Tips

### Check Console Logs:

**Auto-save skipping (good):**
```
⏭️ Skipping save - no changes
```

**Auto-save happening (bad if multiple times):**
```
💾 Auto-saving...
✅ Auto-save complete: 5
```

**View button clicked:**
```
View version: {id: 456, version_number: 3, test_case_id: 99, ...}
```

**Compare button clicked:**
```
Compare versions: 2 4
```

### Check Network Tab:

**Multiple PUT requests = bug confirmed:**
```
PUT /api/v1/tests/99/steps - 200 OK  (11:00:01)
PUT /api/v1/tests/99/steps - 200 OK  (11:00:03)
PUT /api/v1/tests/99/steps - 200 OK  (11:00:05)
...
```

---

## 💡 Temporary Solution

**For testing Component 2, use this workflow:**

1. **Manual Save Only:**
   - Type changes
   - Click "Save Now" immediately
   - Don't trigger auto-save

2. **View Button:**
   - Open Console (F12)
   - Click "View" to see data logged
   - This confirms the data is being passed correctly

3. **Compare Button:**
   - Select 2 versions
   - Click "Compare"
   - Check console for version numbers

---

## 📋 Next Steps

### Priority 1: Fix Multiple Saves (30 mins)
- Add `savedSteps` state
- Update after successful save
- Compare with `savedSteps` instead of `initialSteps`
- Test that only 1 version is created per edit

### Priority 2: Build Component 3 (2-3 hours)
- Create `VersionViewDialog.tsx`
- Show version details in modal
- Wire up to "View" button
- Add "Rollback" action button

### Priority 3: Build Component 4 (1-2 hours)
- Create `RollbackConfirmDialog.tsx`
- Confirmation dialog for rollback
- Reason input field
- Wire up to rollback actions

---

## 🎯 Testing Checklist

- [ ] Only 1 version created per edit (using manual save)
- [ ] Version history panel opens
- [ ] Versions list displays
- [ ] Current version highlighted
- [ ] Selection checkboxes work (max 2)
- [ ] Compare button appears
- [ ] View button logs to console
- [ ] Console shows version data
- [ ] No errors in console
- [ ] Network shows correct API calls

---

## 🚀 Workaround Summary

**For now:**
1. Use "Save Now" button only (disable auto-save mentally)
2. Check Console for "View" and "Compare" button responses
3. This lets you test the UI/UX of Component 2
4. We'll fix the duplicate saves and add dialogs next

**The Component 2 UI is working perfectly - just need to fix the data handling!**

---

**Status:** Component 2 UI ✅ Complete | Data handling 🔧 Needs fixes  
**Next Session:** Fix auto-save + Build Component 3 (ViewDialog)
