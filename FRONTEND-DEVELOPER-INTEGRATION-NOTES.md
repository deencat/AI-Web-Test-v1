# Frontend Developer - Integration Testing Setup

## 🎉 Latest Updates (December 4, 2025)

**Branch:** `integration/sprint-3`  
**Status:** Login Fixed ✅ - Ready for Sprint 3 Testing

---

## 🔧 Recent Fixes (Commit: 3c38abc)

### 1. **Frontend Login Connected to Real API** ✅
- **File:** `frontend/src/pages/LoginPage.tsx`
- **Change:** Replaced hardcoded `mockLogin()` with `authService.login()`
- **Impact:** Login now sends real POST requests to backend `/api/v1/auth/login`
- **Credentials:** 
  - Username: `admin`
  - Password: `admin123`

### 2. **Swagger UI Fixed** ✅
- **File:** `backend/app/middleware/security.py`
- **Change:** Updated Content Security Policy to allow `cdn.jsdelivr.net`
- **Impact:** Swagger UI now loads correctly at http://127.0.0.1:8000/api/v1/docs

### 3. **Environment Configuration** ✅
- **File:** `frontend/.env`
- **Settings:**
  ```properties
  VITE_API_URL=http://localhost:8000/api/v1
  VITE_USE_MOCK=false
  ```
- **Impact:** Frontend uses real backend API instead of mock data

---

## 🚀 Quick Start for Frontend Developer

### Pull Latest Code
```bash
git checkout integration/sprint-3
git pull origin integration/sprint-3
```

### Setup Frontend
```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Verify .env file exists with correct settings
cat .env
# Should show:
# VITE_API_URL=http://localhost:8000/api/v1
# VITE_USE_MOCK=false

# Start frontend dev server
npm run dev
```

### Verify Backend is Running
The backend developer should have the backend running. Verify:
```bash
# Check if backend is accessible
curl http://127.0.0.1:8000/api/v1/health
```

If backend is not running, ask backend developer to start it:
```bash
cd backend
.\venv\Scripts\activate  # Windows
python start_server.py
```

---

## ✅ Testing Checklist

### 1. Login Test
- [ ] Open http://localhost:5173
- [ ] Enter username: `admin`, password: `admin123`
- [ ] Click "Sign In"
- [ ] Should redirect to dashboard
- [ ] Check backend logs - should see: `POST /api/v1/auth/login 200 OK`
- [ ] Check browser DevTools → Application → Local Storage
  - Should have `token` and `user` stored

### 2. Dashboard Test (Sprint 2)
**⚠️ Known Issue:** Dashboard is still using mock data (needs fixing)
- [ ] Navigate to Dashboard
- [ ] Stats widgets display (may show mock data)
- [ ] Recent tests list appears (may show mock data)
- [ ] Navigation works

### 3. Tests Page (Sprint 2)
**⚠️ Known Issue:** Tests page is still using mock data (needs fixing)
- [ ] Click "Tests" in sidebar
- [ ] List of tests displays (may show mock data)
- [ ] Can view test details

### 4. Knowledge Base (Sprint 2)
**⚠️ Known Issue:** KB page is still using mock data (needs fixing)
- [ ] Click "Knowledge Base" in sidebar
- [ ] Documents list displays (may show mock data)
- [ ] Categories visible

### 5. **Execution Progress (Sprint 3 - CRITICAL)** ✨
**✅ Should use real API** (uses executionService)
- [ ] Run a test
- [ ] Navigate to execution detail page
- [ ] Status badge shows "Running" or "Pending"
- [ ] Progress indicator displays
- [ ] Step list shows all test steps
- [ ] Steps update in real-time
- [ ] Screenshot thumbnails appear
- [ ] Check backend logs for API calls

### 6. **Execution History (Sprint 3 - CRITICAL)** ✨
**✅ Should use real API** (uses executionService)
- [ ] Click "Executions" in sidebar
- [ ] List of executions displays (from real API)
- [ ] Can filter by status
- [ ] Can sort by date
- [ ] Click execution → navigates to detail page
- [ ] Check Network tab for API requests

---

## 🐛 Known Issues to Fix

### Pages Still Using Mock Data:
1. **DashboardPage.tsx** - Uses `mockTests` directly
2. **TestsPage.tsx** - Uses `mockTests` directly
3. **KnowledgeBasePage.tsx** - Uses `mockKBDocuments`, `mockKBCategories` directly

### Recommendation:
**Test Sprint 3 features first** (Execution Progress & History), then we'll fix the other pages together.

---

## 🔍 How to Verify Real API vs Mock Data

### Method 1: Check Browser Network Tab
1. Open DevTools (F12) → Network tab
2. Perform an action (e.g., view executions)
3. **Real API:** You'll see requests to `localhost:8000/api/v1/...`
4. **Mock data:** No network requests (instant response)

### Method 2: Check Backend Logs
1. Watch the backend terminal
2. Perform an action
3. **Real API:** You'll see log entries like `GET /api/v1/executions 200 OK`
4. **Mock data:** No log entries

### Method 3: Check Response Time
1. Perform an action
2. **Real API:** Takes 50-500ms (network + database)
3. **Mock data:** Instant (< 10ms)

---

## 📊 API Endpoints Available

### Authentication
- `POST /api/v1/auth/login` - Login (✅ Working)
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Test Management (Sprint 2)
- `GET /api/v1/tests` - List tests
- `GET /api/v1/tests/{id}` - Get test details
- `POST /api/v1/tests` - Create test
- `POST /api/v1/tests/generate` - AI test generation

### Test Execution (Sprint 3) ✨
- `POST /api/v1/tests/{id}/run` - Execute test
- `GET /api/v1/executions/{id}` - Get execution details
- `GET /api/v1/executions` - List executions
- `GET /api/v1/executions/stats` - Statistics
- `GET /api/v1/executions/queue/status` - Queue status
- `GET /api/v1/executions/queue/active` - Active executions

### Knowledge Base (Sprint 2)
- `GET /api/v1/kb/documents` - List documents
- `POST /api/v1/kb/upload` - Upload document
- `GET /api/v1/kb/categories` - List categories

**Full API Documentation:** http://127.0.0.1:8000/api/v1/docs

---

## 🆘 Troubleshooting

### Issue: Login returns 401 Unauthorized
**Cause:** Wrong credentials  
**Fix:** Use username `admin` (not email), password `admin123`

### Issue: "Network Error" or "Failed to fetch"
**Cause:** Backend not running  
**Fix:** Ask backend developer to start backend server

### Issue: CORS Error
**Cause:** Backend CORS not configured  
**Fix:** Backend `.env` should have:
```
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Issue: Still seeing mock data
**Cause:** Frontend not restarted after `.env` change  
**Fix:** 
1. Stop frontend (`Ctrl+C`)
2. Restart: `npm run dev`
3. Hard refresh browser: `Ctrl+Shift+R`

### Issue: Blank Swagger UI page
**Cause:** CSP blocking CDN (should be fixed now)  
**Fix:** Already fixed in commit 3c38abc, pull latest code

---

## 📞 Communication

**Questions for Backend Developer:**
- Is backend server running?
- What port is backend on? (should be 8000)
- Are there any errors in backend logs?
- Can you see my API requests in backend logs?

**Questions for Frontend Developer:**
- Can you see network requests to localhost:8000 in DevTools?
- Any console errors in browser DevTools?
- Did you pull the latest code from integration/sprint-3?
- Did you restart frontend server after pulling?

---

## 🎯 Sprint 3 Testing Priority

**High Priority (Test These First):**
1. ✅ Login (FIXED - test now)
2. ✨ Run Test Button (Sprint 3 feature)
3. ✨ Execution Progress Page (Sprint 3 feature)
4. ✨ Execution History Page (Sprint 3 feature)
5. ✨ Queue Status Widget (Sprint 3 feature)
6. ✨ Screenshot Gallery (Sprint 3 feature)

**Medium Priority (Can fix after Sprint 3):**
7. Dashboard Page (Sprint 2 - needs fixing)
8. Tests Page (Sprint 2 - needs fixing)
9. Knowledge Base Page (Sprint 2 - needs fixing)

---

**Last Updated:** December 4, 2025  
**Commit:** 3c38abc  
**Branch:** integration/sprint-3  
**Status:** ✅ Login working, ready for Sprint 3 testing
