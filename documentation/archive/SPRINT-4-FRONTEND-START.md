# Sprint 4 Frontend Development - Getting Started

**Developer:** Developer A  
**Date:** December 22, 2025  
**Sprint:** Sprint 4 - Test Versioning Frontend  
**Status:** 🚀 Ready to Start

---

## ✅ Prerequisites Complete

- ✅ Frontend dev server running (`npm run dev`)
- ✅ Backend API ready (http://localhost:8000)
- ✅ Version control backend complete (5 endpoints)
- ✅ Database with test_versions table
- ✅ Current directory: `frontend/`

---

## 🎯 Today's Goal: Build TestStepEditor Component

**Component 1 of 4:** TestStepEditor.tsx  
**Estimated Time:** 4-6 hours  
**Purpose:** Allow editing test steps with auto-save and version tracking

---

## 📋 Step-by-Step Implementation

### Step 1: Install Dependencies (5 minutes)

```powershell
# You're in: C:\Users\andrechw\Documents\AI-Web-Test-v1-1\frontend

# Install lodash for debounce function
npm install lodash
npm install --save-dev @types/lodash

# Wait for installation to complete
```

**Why lodash?** 
- Provides `debounce` function for auto-save
- Delays API calls until user stops typing
- Prevents excessive API requests

---

### Step 2: Create Component File (10 minutes)

**File Location:** `frontend/src/components/TestStepEditor.tsx`

I'll create this file for you with the complete implementation.

---

### Step 3: Test the Component (15 minutes)

1. **Open browser:** http://localhost:3000
2. **Navigate to:** Test Detail page (any test)
3. **Find:** TestStepEditor component
4. **Test typing:** Edit test steps
5. **Wait 2 seconds:** Auto-save should trigger
6. **Check console:** Look for API calls

---

### Step 4: Verify Backend Integration (10 minutes)

```powershell
# Open Swagger UI in browser
http://localhost:8000/docs

# Test endpoint manually:
PUT /api/v1/tests/{id}/steps

# Request body:
{
  "steps": "Test content",
  "change_reason": "Testing"
}

# Should return:
{
  "id": 123,
  "version_number": 2,
  "message": "Test steps updated and version created"
}
```

---

## 🛠️ Development Workflow

### Terminal Setup

**Terminal 1 - Frontend (Already Running):**
```powershell
# C:\Users\andrechw\Documents\AI-Web-Test-v1-1\frontend
npm run dev
# Server at: http://localhost:3000
```

**Terminal 2 - Backend (Need to Start):**
```powershell
# Open new terminal
cd C:\Users\andrechw\Documents\AI-Web-Test-v1-1\backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload
# Server at: http://localhost:8000
```

---

## 📁 File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── TestStepEditor.tsx          ← CREATE THIS (Step 2)
│   │   ├── VersionHistoryPanel.tsx     ← Later today
│   │   ├── VersionCompareDialog.tsx    ← Tomorrow
│   │   └── RollbackConfirmDialog.tsx   ← Tomorrow
│   ├── pages/
│   │   └── TestDetailPage.tsx          ← UPDATE THIS (Step 5)
│   └── types/
│       └── test.ts                     ← CHECK THIS (optional)
```

---

## 🎨 Component Features

### TestStepEditor Features:
1. ✅ Textarea for editing test steps
2. ✅ Auto-save (2-second debounce)
3. ✅ Manual save button
4. ✅ "Saving..." indicator
5. ✅ "Last saved X ago" timestamp
6. ✅ Version number display (e.g., "v5")
7. ✅ Error handling

### Visual Design:
```
┌─────────────────────────────────────────────┐
│ Test Steps (v5)              [Save Now]     │
├─────────────────────────────────────────────┤
│                                             │
│ [Large textarea for editing steps]         │
│                                             │
│ Placeholder text showing example format    │
│                                             │
├─────────────────────────────────────────────┤
│ ⓘ Changes auto-saved 2 sec after typing   │
│ ✓ Saved 30 seconds ago                     │
└─────────────────────────────────────────────┘
```

---

## 🧪 Testing Checklist

### Basic Tests (Must Pass):
- [ ] Component renders without errors
- [ ] Can type in textarea
- [ ] Auto-save triggers after 2 seconds
- [ ] Manual save button works
- [ ] "Saving..." indicator appears
- [ ] "Saved X ago" appears after save
- [ ] Version number displays
- [ ] Version number updates after save

### Edge Cases (Test Later):
- [ ] Empty content (should still save)
- [ ] Very long content (10,000+ chars)
- [ ] Rapid typing (debounce works)
- [ ] Network error (shows error message)
- [ ] Multiple rapid saves

---

## 🔌 API Integration

### Endpoint Used:
```
PUT /api/v1/tests/{testId}/steps
```

### Request Format:
```json
{
  "steps": "1. Navigate to...\n2. Click...\n3. Verify...",
  "change_reason": "Auto-save edit"
}
```

### Response Format:
```json
{
  "id": 123,
  "version_number": 5,
  "message": "Test steps updated and version created"
}
```

### Error Response:
```json
{
  "detail": "Test not found"
}
```

---

## 🎯 Success Criteria

### Minimum Working Version:
- ✅ Can edit test steps
- ✅ Auto-save works
- ✅ Shows version number
- ✅ No crashes or errors

### Full Version (Aim For):
- ✅ All above +
- ✅ Manual save button
- ✅ Visual feedback (saving/saved)
- ✅ Error handling
- ✅ Last saved timestamp

---

## ⏱️ Time Breakdown

| Task | Time | Status |
|------|------|--------|
| Install lodash | 5 min | ⏳ Next |
| Create component file | 10 min | ⏳ Next |
| Test rendering | 15 min | ⏳ Later |
| Implement auto-save | 1 hour | ⏳ Later |
| Add manual save | 30 min | ⏳ Later |
| Add visual feedback | 45 min | ⏳ Later |
| Styling | 45 min | ⏳ Later |
| Integration | 30 min | ⏳ Later |
| Testing | 1 hour | ⏳ Later |
| **Total** | **4-6 hours** | |

---

## 🚀 Let's Start!

### Immediate Next Steps:

**Step 1:** Install lodash
```powershell
npm install lodash @types/lodash
```

**Step 2:** I'll create the TestStepEditor.tsx component file

**Step 3:** Start the backend server (if not running)

**Step 4:** Test the component

---

## 📚 Resources

### Documentation:
- `FRONTEND-COMPONENT-1-GUIDE.md` - Detailed component guide
- `NEXT-STEPS-SPRINT-4.md` - Overall Sprint 4 plan
- Backend API: http://localhost:8000/docs

### Code Examples:
- Existing components in `frontend/src/components/`
- API client in `frontend/src/api/client.ts`
- TypeScript types in `frontend/src/types/`

---

## 💡 Tips

1. **Save frequently:** Use Ctrl+S in your editor
2. **Check console:** Browser DevTools for errors
3. **Use Swagger:** Test API endpoints manually
4. **Start simple:** Get basic version working first
5. **Iterate:** Add features one at a time

---

## 🆘 Troubleshooting

### Issue: "Cannot find module 'lodash'"
**Solution:** `npm install lodash @types/lodash`

### Issue: "Frontend won't connect to backend"
**Check:**
1. Backend server running? (http://localhost:8000)
2. Correct API URL in frontend config
3. CORS enabled on backend
4. Network tab in DevTools

### Issue: "Auto-save not working"
**Check:**
1. Debounce delay (2 seconds)
2. Network tab for API calls
3. Backend logs for errors
4. Token in localStorage

---

**Ready to build?** Let's start with Step 1! 🚀
