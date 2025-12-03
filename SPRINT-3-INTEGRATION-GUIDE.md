# Sprint 3 Integration Guide - Backend + Frontend
## Complete Integration Testing & Merge Workflow

**Date:** December 3, 2025  
**Status:** Ready for Integration  
**Backend:** Sprint 3 Complete (100%) on `main`  
**Frontend:** Sprint 3 Complete (100%) on `frontend-dev-sprint-3`

---

## 🎯 Integration Strategy

### Recommended Workflow: Feature Branch Integration

```
main (backend complete)
  └── integration/sprint-3 (NEW - merge both here)
        ├── backend code (from main)
        └── frontend code (from frontend-dev-sprint-3)
              └── Test & fix issues
                    └── Merge back to main when ready
```

---

## 📋 Step-by-Step Integration Process

### Phase 1: Create Integration Branch (5 minutes)

**Step 1.1: Ensure main is up to date**
```bash
git checkout main
git pull origin main
```

**Step 1.2: Create integration branch from main**
```bash
git checkout -b integration/sprint-3
```

This branch now has:
- ✅ Backend Sprint 3 complete (Stagehand, Queue, 11 endpoints)
- ✅ Backend Sprint 2 complete (Test gen, KB, Auth)
- ✅ Backend Sprint 1 complete (Auth MVP)

**Step 1.3: Push integration branch to GitHub**
```bash
git push -u origin integration/sprint-3
```

---

### Phase 2: Merge Frontend Code (10 minutes)

**Step 2.1: Fetch frontend branch**
```bash
git fetch origin frontend-dev-sprint-3
```

**Step 2.2: Merge frontend into integration branch**
```bash
git merge origin/frontend-dev-sprint-3 -m "feat: Merge Sprint 3 frontend for integration testing"
```

**Expected:** Merge conflicts are normal! Common conflicts:
- `package.json` (both branches may have different dependencies)
- `README.md` (both may have updated docs)
- `.gitignore` (may have different entries)
- Environment files (backend vs frontend configs)

**Step 2.3: Resolve conflicts**

For each conflict, open the file and look for:
```
<<<<<<< HEAD (your backend code)
... backend version ...
=======
... frontend version ...
>>>>>>> origin/frontend-dev-sprint-3
```

**How to resolve:**
- **package.json**: Keep BOTH sets of dependencies (merge them)
- **README.md**: Keep BOTH sections (combine documentation)
- **.gitignore**: Keep BOTH entries (merge ignore rules)
- **Code files**: Usually no conflicts (backend/frontend separate)

**Step 2.4: After resolving conflicts**
```bash
git add .
git commit -m "fix: Resolve merge conflicts between backend and frontend Sprint 3"
git push origin integration/sprint-3
```

---

### Phase 3: Verify Integration (15 minutes)

**Step 3.1: Check directory structure**
```bash
# You should see both:
ls frontend/  # Frontend React app
ls backend/   # Backend FastAPI app
```

**Step 3.2: Install dependencies**

**Backend:**
```bash
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

**Step 3.3: Verify environment files**

**Backend `.env`:**
```bash
cd backend
cat .env  # Should have your NEW OpenRouter key
```

**Frontend `.env`:**
```bash
cd frontend
cat .env  # Should have VITE_API_URL=http://localhost:8000
```

If frontend `.env` is missing, create it:
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

---

### Phase 4: Integration Testing (30-60 minutes)

**Step 4.1: Start Backend Server**

```bash
# Terminal 1
cd backend
.\venv\Scripts\activate
python start_server.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify backend:**
- Open: http://127.0.0.1:8000/docs
- Check: All 60+ endpoints visible
- Test: Login with `admin@aiwebtest.com` / `admin123`

**Step 4.2: Start Frontend Development Server**

```bash
# Terminal 2 (new terminal)
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

**Step 4.3: Run Integration Tests**

**Test Checklist:**
- [ ] **Login Flow**
  - Navigate to http://localhost:5173
  - Login with `admin@aiwebtest.com` / `admin123`
  - Should redirect to dashboard
  - Token should persist

- [ ] **Dashboard**
  - Stats widgets load
  - Recent tests display
  - Navigation works

- [ ] **Test Generation** (Sprint 2 Frontend)
  - Click "Tests" → "Generate New Test"
  - Enter URL (e.g., www.three.com.hk)
  - Click "Generate"
  - Should show generated tests (5-8 seconds)

- [ ] **Test Execution** (Sprint 3 Frontend)
  - Click on a test case
  - Click "Run Test" button
  - Should see "Test queued for execution"
  - Queue status widget shows active count

- [ ] **Execution Progress** (Sprint 3 Frontend)
  - Navigate to execution detail page
  - Should see step-by-step progress
  - Steps update in real-time (polling every 2 seconds)
  - Screenshots display as thumbnails

- [ ] **Execution History** (Sprint 3 Frontend)
  - Click "Executions" menu
  - Should see list of executions
  - Filter by status works
  - Click execution → see details

- [ ] **Knowledge Base Upload** (Sprint 2 Frontend)
  - Click "Knowledge Base"
  - Upload a PDF/DOCX file
  - Select category
  - File should upload successfully

---

### Phase 5: Bug Tracking & Fixes (Ongoing)

**Step 5.1: Create issue log**

Create a file to track integration issues:
```bash
# Create INTEGRATION-ISSUES.md
```

**Common Issues & Fixes:**

**Issue 1: CORS Errors**
```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Fix:**
```bash
# backend/.env
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

Restart backend server.

**Issue 2: API URL Wrong**
```
Failed to fetch: http://localhost:3000/api/v1/...
```

**Fix:**
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

Restart frontend dev server.

**Issue 3: Authentication Fails**
```
401 Unauthorized
```

**Fix:** Check token handling in frontend:
- Token stored in localStorage?
- Token included in Authorization header?
- Token format: `Bearer <token>`

**Issue 4: Queue Not Starting**
```
Tests queue but never execute
```

**Fix:** Check backend queue manager:
```bash
cd backend
python -c "from app.services.queue_manager import queue_manager; print(queue_manager.is_running())"
```

Should return `True`.

**Step 5.2: Fix and commit**

For each bug:
```bash
# Fix the code
# Test the fix
git add <fixed-files>
git commit -m "fix: [describe the fix]"
git push origin integration/sprint-3
```

---

### Phase 6: Final Validation (30 minutes)

**Step 6.1: Run automated tests**

**Backend tests:**
```bash
cd backend
pytest tests/ -v
```

**Frontend tests:**
```bash
cd frontend
npm run test
# or
npm run test:e2e  # Playwright tests
```

**Step 6.2: Manual end-to-end test**

Run complete user journey:
1. Login
2. Generate test from URL
3. Run the generated test
4. Watch execution progress
5. View execution history
6. Upload KB document
7. Logout

**All steps should work!**

**Step 6.3: Performance check**

- [ ] Backend responds in < 500ms
- [ ] Frontend loads in < 2 seconds
- [ ] Test generation completes in < 30 seconds
- [ ] Test execution completes in < 5 minutes
- [ ] No console errors in browser
- [ ] No 500 errors in backend logs

---

### Phase 7: Merge to Main (10 minutes)

**Only proceed if ALL tests pass!**

**Step 7.1: Update integration branch**
```bash
git checkout integration/sprint-3
git pull origin integration/sprint-3
```

**Step 7.2: Merge main into integration (get latest changes)**
```bash
git merge origin/main -m "chore: Sync with main before final merge"
```

**Step 7.3: Push final integration branch**
```bash
git push origin integration/sprint-3
```

**Step 7.4: Create Pull Request (Recommended)**

**On GitHub:**
1. Go to: https://github.com/deencat/AI-Web-Test-v1/pulls
2. Click "New Pull Request"
3. Base: `main` ← Compare: `integration/sprint-3`
4. Title: `Sprint 3 Integration - Backend + Frontend Complete`
5. Description:
   ```
   ## Sprint 3 Integration Complete
   
   ### Backend Features (100%)
   - ✅ Stagehand + Playwright integration
   - ✅ Queue system (5 concurrent executions)
   - ✅ 11 execution endpoints
   - ✅ Screenshot capture
   - ✅ Real website testing
   
   ### Frontend Features (100%)
   - ✅ Test execution UI
   - ✅ Queue status indicator
   - ✅ Execution progress page
   - ✅ Step-by-step progress display
   - ✅ Execution history list
   - ✅ Screenshot gallery
   - ✅ Statistics dashboard
   
   ### Testing
   - ✅ All backend tests passing
   - ✅ All frontend tests passing
   - ✅ Integration tests passing
   - ✅ Manual end-to-end testing complete
   
   ### Breaking Changes
   None
   
   ### Migration Required
   None
   ```
6. Request review from team
7. After approval, click "Merge Pull Request"

**Step 7.5: Alternative - Direct merge (if working solo)**
```bash
git checkout main
git merge integration/sprint-3 -m "feat: Sprint 3 Integration Complete - Backend + Frontend"
git push origin main
```

**Step 7.6: Tag the release**
```bash
git tag -a v1.0.0-sprint3 -m "Sprint 3 Complete: Test Execution Engine + UI"
git push origin v1.0.0-sprint3
```

**Step 7.7: Cleanup (optional)**
```bash
# Delete integration branch after successful merge
git branch -d integration/sprint-3
git push origin --delete integration/sprint-3
```

---

## 🔍 Quick Commands Reference

### Check Integration Status
```bash
# Current branch
git branch

# View all branches
git branch -a

# Check for uncommitted changes
git status

# View recent commits
git log --oneline -10

# View branch differences
git diff main integration/sprint-3
```

### Update from Remote
```bash
# Fetch latest changes
git fetch origin

# Pull latest main
git checkout main
git pull origin main

# Pull latest frontend
git fetch origin frontend-dev-sprint-3
```

### Integration Testing
```bash
# Start backend (Terminal 1)
cd backend && .\venv\Scripts\activate && python start_server.py

# Start frontend (Terminal 2)
cd frontend && npm run dev

# Run backend tests (Terminal 3)
cd backend && pytest tests/ -v

# Run frontend tests (Terminal 4)
cd frontend && npm run test
```

---

## 📊 Integration Checklist

### Pre-Integration
- [x] Backend Sprint 3 complete on `main`
- [ ] Frontend Sprint 3 complete on `frontend-dev-sprint-3`
- [ ] Integration branch created
- [ ] Frontend code merged into integration branch
- [ ] Merge conflicts resolved

### During Integration
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend server starts successfully
- [ ] Frontend dev server starts successfully
- [ ] Backend API accessible at http://localhost:8000
- [ ] Frontend accessible at http://localhost:5173
- [ ] CORS configured correctly
- [ ] Environment variables set

### Testing
- [ ] Login flow works
- [ ] Test generation works
- [ ] Test execution works
- [ ] Queue system works
- [ ] Real-time progress updates work
- [ ] Screenshots display correctly
- [ ] Execution history displays
- [ ] KB upload works
- [ ] All automated tests pass
- [ ] No console errors
- [ ] No backend errors

### Post-Integration
- [ ] All bugs fixed
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Merged to main
- [ ] Release tagged
- [ ] Integration branch deleted (optional)
- [ ] Team notified

---

## 🚀 Next Steps After Integration

1. **Sprint 4 Planning**
   - KB Categorization UI
   - Observation Agent
   - Polish and refinements

2. **Production Deployment**
   - Docker setup
   - PostgreSQL migration
   - Environment configuration
   - Monitoring setup

3. **User Acceptance Testing**
   - QA team testing
   - Feedback collection
   - Bug fixes

---

## 📞 Need Help?

**Common Questions:**

**Q: Merge conflicts are scary, what do I do?**
A: Don't worry! Most conflicts are in `package.json` or `README.md`. Just keep both versions' content. For code conflicts, pick the newer version or ask your frontend dev.

**Q: Tests are failing, should I still merge?**
A: NO! Fix all failing tests first. Integration branch is for fixing issues before merging to main.

**Q: Frontend code broke my backend, help!**
A: Frontend code is in `frontend/` folder, it shouldn't affect backend. Check if frontend changed any shared config files.

**Q: How long should integration take?**
A: First time: 2-3 hours. With practice: 30-60 minutes.

---

**Ready to start? Run the commands in Phase 1!** 🚀
