# Quick Testing Guide - Component 2

## 🎯 Temporary Solution (For Testing Now)

### To Avoid Multiple Versions:
**Use MANUAL SAVE only:**
1. Type your changes
2. **Immediately click "Save Now"** button
3. This creates only 1 version (not 11!)

**Why:** Auto-save compares with initial content that never updates, so it saves on every keystroke. We'll fix this properly later.

---

### To Test "View" Button:
**Check the browser console:**
1. Open DevTools (F12)
2. Click on **Console** tab
3. Click "View" button on a version
4. You'll see the version data logged: `View version: {id: 456, ...}`

**Why:** The "View" dialog (Component 3) hasn't been built yet - that's the next task!

---

## ✅ What You Can Test Now

1. ✅ **History Panel** - Opens/closes smoothly
2. ✅ **Versions List** - Shows all versions correctly (just too many 😅)
3. ✅ **Current Version** - Highlighted in blue
4. ✅ **Date Display** - Shows "11 hours ago", etc.
5. ✅ **Checkboxes** - Select max 2 versions
6. ✅ **Compare Button** - Appears when 2 selected
7. ✅ **Console Logs** - View/Compare buttons log data

---

## 🔧 What Needs Fixing

1. 🐛 **Multiple saves** - Use manual save for now
2. 🐛 **View button** - Build Component 3 (VersionViewDialog) next
3. 🐛 **Rollback button** - Build Component 4 (RollbackConfirmDialog) next

---

## 📝 Testing Instructions

```
1. Refresh browser (http://localhost:5173/tests/99)
2. Edit test steps
3. Click "Save Now" immediately (don't wait!)
4. Open Console (F12)
5. Click "View History"
6. See your versions listed
7. Click "View" - check console for data
8. Select 2 versions - see compare button
9. Click compare - check console

✅ If you see data in console, Component 2 is working!
```

---

**Next:** Fix auto-save + Build Component 3 (View Dialog)  
**Time Needed:** ~3-4 hours

**Want to proceed? Options:**
1. Fix the auto-save bug now (30 mins)
2. Build Component 3 with current workaround (2-3 hrs)
3. Take a break and continue later
