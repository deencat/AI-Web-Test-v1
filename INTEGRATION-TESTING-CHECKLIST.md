# Integration Testing Checklist - Sprint 3
## Backend + Frontend Integration

**Date Started:** December 3, 2025  
**Branch:** `integration/sprint-3`  
**Status:** Merge Complete ✅ - Ready for Testing

---

## ✅ Merge Status

### Files Merged from Frontend:
- [x] `RUN-TEST-BUTTON-GUIDE.md`
- [x] `SPRINT-3-FRONTEND-COMPLETION-REPORT.md`
- [x] `SPRINT-3-TESTING-GUIDE.md`
- [x] `frontend/src/components/QueueStatusWidget.tsx`
- [x] `frontend/src/components/RunTestButton.tsx`
- [x] `frontend/src/components/dashboard/ExecutionStatsWidget.tsx`
- [x] `frontend/src/components/execution/ScreenshotGallery.tsx`
- [x] `frontend/src/components/execution/ScreenshotModal.tsx`
- [x] `frontend/src/pages/ExecutionHistoryPage.tsx`
- [x] `frontend/src/pages/ExecutionProgressPage.tsx`
- [x] `frontend/src/services/executionService.ts`
- [x] `frontend/src/types/execution.ts`
- [x] `tests/e2e/08-sprint3-executions.spec.ts`
- [x] Modified: `App.tsx`, `Sidebar.tsx`, `TestCaseCard.tsx`, `api.ts`, etc.

### Conflict Resolution:
- [x] Project Management Plan conflict resolved (kept backend version)
- [x] All changes committed
- [x] Integration branch pushed to GitHub

---

## 🧪 Testing Checklist

### Pre-Test Setup
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend `.env` has new OpenRouter API key
- [ ] Frontend `.env` created with `VITE_API_URL=http://localhost:8000`

### Backend Verification
- [ ] Backend server starts: `cd backend && python start_server.py`
- [ ] API docs accessible: http://127.0.0.1:8000/docs
- [ ] Can login with `admin@aiwebtest.com` / `admin123`
- [ ] 11 execution endpoints visible in Swagger UI

### Frontend Verification  
- [ ] Frontend server starts: `cd frontend && npm run dev`
- [ ] App accessible: http://localhost:5173
- [ ] No console errors on load
- [ ] No build errors

### Integration Tests

#### Test 1: Login Flow
- [ ] Navigate to http://localhost:5173
- [ ] Login with admin credentials
- [ ] Redirects to dashboard
- [ ] Token stored in localStorage
- [ ] Dashboard loads successfully

#### Test 2: Dashboard (Sprint 2 + Sprint 3)
- [ ] Stats widgets display (total tests, executions, pass rate)
- [ ] Recent tests list appears
- [ ] Recent executions list appears (Sprint 3)
- [ ] Queue status widget shows "0/5 active" (Sprint 3)
- [ ] All navigation links work

#### Test 3: Test Generation (Sprint 2)
- [ ] Click "Tests" → "Generate New Test"
- [ ] Enter URL: `www.three.com.hk`
- [ ] Click "Generate" button
- [ ] Loading indicator appears
- [ ] Tests generate in 5-10 seconds
- [ ] Generated tests display in list
- [ ] Can view test details

#### Test 4: Run Test (Sprint 3 - NEW)
- [ ] Click on a generated test
- [ ] "Run Test" button visible
- [ ] Click "Run Test"
- [ ] Toast notification: "Test queued for execution"
- [ ] Queue status updates to "1/5 active"
- [ ] Execution ID returned

#### Test 5: Execution Progress (Sprint 3 - NEW)
- [ ] Navigate to execution detail page
- [ ] Status badge shows "Running" or "Pending"
- [ ] Progress indicator displays (e.g., "2/5 steps completed")
- [ ] Step list shows all test steps
- [ ] Steps update in real-time (polling every 2 seconds)
- [ ] Step statuses change: Pending → Running → Passed/Failed
- [ ] Green checkmarks for passed steps
- [ ] Red X for failed steps (if any)
- [ ] Screenshot thumbnails appear for completed steps

#### Test 6: Screenshot Gallery (Sprint 3 - NEW)
- [ ] Click on screenshot thumbnail
- [ ] Modal opens with full-size image
- [ ] Can navigate between screenshots (previous/next arrows)
- [ ] Shows step context (action, expected result)
- [ ] Download button works
- [ ] Close modal button works

#### Test 7: Execution History (Sprint 3 - NEW)
- [ ] Click "Executions" in sidebar
- [ ] List of executions displays
- [ ] Shows execution ID, test name, status, result, duration
- [ ] Can filter by status (pending/running/completed/failed)
- [ ] Can filter by result (passed/failed/error)
- [ ] Can sort by date (newest first)
- [ ] Pagination works (if > 20 executions)
- [ ] Click on execution → navigates to detail page

#### Test 8: Queue Management (Sprint 3 - NEW)
- [ ] Queue status widget updates in real-time
- [ ] Shows "X/5 active executions"
- [ ] Shows "Y pending in queue"
- [ ] Can run multiple tests simultaneously (up to 5)
- [ ] 6th test queues correctly
- [ ] Queue processes tests in order

#### Test 9: Statistics Dashboard (Sprint 3 - NEW)
- [ ] Execution stats widget on dashboard
- [ ] Shows total executions count
- [ ] Shows pass rate percentage
- [ ] Shows average duration
- [ ] Stats update after test execution

#### Test 10: Knowledge Base Upload (Sprint 2)
- [ ] Click "Knowledge Base"
- [ ] Click "Upload Document"
- [ ] Select PDF/DOCX file
- [ ] Choose category (e.g., "CRM")
- [ ] Upload succeeds
- [ ] Document appears in list
- [ ] Can view document details

---

## 🐛 Issue Tracking

### Issues Found:
| # | Component | Issue | Severity | Status | Fix |
|---|-----------|-------|----------|--------|-----|
| 1 | Example | CORS error on API call | High | 🔴 Open | Add localhost:5173 to CORS |
| 2 | | | | | |
| 3 | | | | | |

### Common Issues & Fixes:

**Issue:** CORS Error
```
Access to fetch at 'http://localhost:8000/api/v1/...' blocked by CORS
```
**Fix:**
```bash
# backend/.env
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```
Restart backend server.

**Issue:** API URL Wrong
```
Failed to fetch: Cannot connect to localhost:3000
```
**Fix:**
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```
Restart frontend server.

**Issue:** Tests don't execute
```
Tests queue but never run
```
**Fix:** Check queue manager is running:
```python
from app.services.queue_manager import queue_manager
print(queue_manager.is_running())  # Should be True
```

**Issue:** Screenshots don't display
```
404 on screenshot URL
```
**Fix:** Check backend artifacts folder exists:
```bash
ls backend/artifacts/screenshots/
```

---

## ✅ Sign-Off

### Backend Developer
- [ ] All backend features working
- [ ] All backend tests passing
- [ ] APIs responding correctly
- [ ] Queue system operational
- [ ] Screenshots captured
- **Signed:** ________________ **Date:** ________

### Frontend Developer  
- [ ] All frontend features working
- [ ] All frontend tests passing (36/36)
- [ ] UI components rendering
- [ ] Real-time updates working
- [ ] No console errors
- **Signed:** ________________ **Date:** ________

### Integration Complete
- [ ] All integration tests passed
- [ ] No critical bugs remaining
- [ ] Documentation updated
- [ ] Ready to merge to main
- **Approved:** ________________ **Date:** ________

---

## 📊 Test Results Summary

**Backend Tests:**
- Total: _____ / _____
- Passed: _____
- Failed: _____
- Skipped: _____

**Frontend Tests:**
- Total: 36 / 36
- Passed: _____
- Failed: _____
- Skipped: _____

**Integration Tests:**
- Manual: _____ / 10
- Automated: _____ / _____
- E2E: _____ / _____

**Overall Status:** 🟢 Pass | 🟡 Partial | 🔴 Fail

---

## 🚀 Next Steps

1. [ ] Fix all critical bugs
2. [ ] Run full automated test suite
3. [ ] Performance testing
4. [ ] Create Pull Request
5. [ ] Code review
6. [ ] Merge to main
7. [ ] Deploy to staging
8. [ ] User acceptance testing

---

**Last Updated:** December 3, 2025  
**Branch:** `integration/sprint-3`  
**GitHub:** https://github.com/deencat/AI-Web-Test-v1/tree/integration/sprint-3
