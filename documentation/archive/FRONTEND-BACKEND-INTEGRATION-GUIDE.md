# 🔗 Frontend-Backend Integration Guide

## ✅ **Step 1: Create Frontend .env File**

The `.env` file is ignored by git (for security), so you need to create it manually:

```powershell
cd frontend
```

Create a file named `.env` with this content:

```env
# API Configuration
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_USE_MOCK=false
```

**How to create it:**

**Option A: Using PowerShell**
```powershell
@"
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_USE_MOCK=false
"@ | Out-File -FilePath .env -Encoding utf8
```

**Option B: Using Notepad**
1. Create new file: `frontend/.env`
2. Copy the content above
3. Save as `.env` (make sure it's not `.env.txt`)

---

## ✅ **Step 2: Update authService.ts** ✅ DONE

The `authService.ts` has been updated to send form data correctly for FastAPI's OAuth2.

**What Changed:**
- ✅ Login now sends `application/x-www-form-urlencoded` data (not JSON)
- ✅ After login, fetches user data from `/auth/me`
- ✅ Stores both token and user data in localStorage

---

## 🧪 **Step 3: Test the Integration**

### **3.1: Start the Backend Server**

```powershell
cd backend
.\run_server.ps1
```

**Expected output:**
```
[OK] Virtual environment activated
[OK] All dependencies installed
INFO:     Will watch for changes in these directories: ['...']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify backend is running:**
Open browser: http://127.0.0.1:8000/docs

---

### **3.2: Create Frontend .env File**

```powershell
cd frontend
```

Create `.env` file:

```powershell
@"
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_USE_MOCK=false
"@ | Out-File -FilePath .env -Encoding utf8
```

---

### **3.3: Start the Frontend Dev Server**

```powershell
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

---

### **3.4: Test Login Flow**

1. **Open browser:** http://localhost:5173

2. **Try to login:**
   - Username: `admin`
   - Password: `admin123`

3. **Expected behavior:**
   - ✅ Login successful
   - ✅ Redirects to `/dashboard`
   - ✅ User info displayed in header
   - ✅ No console errors

4. **Check browser DevTools:**
   - **Network tab:** Should see:
     - `POST /api/v1/auth/login` → 200 OK
     - `GET /api/v1/auth/me` → 200 OK
   - **Console:** No errors
   - **Application → Local Storage:** Should see `token` and `user`

5. **Test page refresh:**
   - Press F5 to refresh page
   - ✅ Should stay logged in
   - ✅ User info still displayed

6. **Test logout:**
   - Click logout button
   - ✅ Redirects to `/login`
   - ✅ Token and user cleared from localStorage

---

### **3.5: Test Error Handling**

1. **Wrong password:**
   - Username: `admin`
   - Password: `wrong`
   - ✅ Should show error: "Invalid credentials"

2. **Backend not running:**
   - Stop backend server (CTRL+C)
   - Try to login
   - ✅ Should show error: "Network Error"

---

## 🐛 **Troubleshooting**

### **Issue 1: CORS Error**

**Error in console:**
```
Access to XMLHttpRequest at 'http://127.0.0.1:8000/api/v1/auth/login' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Fix:** Backend CORS is already configured correctly. If you see this:
- Restart backend server
- Make sure `BACKEND_CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`

---

### **Issue 2: 401 Unauthorized**

**Error:** All requests return 401

**Possible causes:**
1. Token not being sent
2. Token expired
3. Backend SECRET_KEY changed

**Fix:**
1. Clear localStorage: Open DevTools → Application → Local Storage → Clear
2. Login again
3. Check backend logs for JWT errors

---

### **Issue 3: .env Not Working**

**Symptom:** Frontend still using mock data

**Fix:**
1. Make sure `.env` file is in `frontend/` directory (not `frontend/src/`)
2. Restart Vite dev server (`npm run dev`)
3. Check in browser console: Network tab should show calls to `http://127.0.0.1:8000`

---

### **Issue 4: Backend Not Responding**

**Error:** `ERR_CONNECTION_REFUSED`

**Fix:**
1. Check backend is running: `Get-Process | Where-Object {$_.ProcessName -like "*python*"}`
2. Restart backend: `cd backend ; .\run_server.ps1`
3. Verify: http://127.0.0.1:8000/api/v1/health

---

## ✅ **Success Checklist**

- ✅ Backend server running on port 8000
- ✅ Frontend dev server running on port 5173
- ✅ `.env` file created with `VITE_USE_MOCK=false`
- ✅ Login with admin/admin123 works
- ✅ Redirects to dashboard after login
- ✅ User info displayed in header
- ✅ Token persists on page refresh
- ✅ Logout clears token and redirects
- ✅ No console errors
- ✅ Network tab shows API calls to backend

---

## 🎉 **What's Next?**

After successful integration:

1. **Run Playwright Tests:**
   ```powershell
   cd frontend
   npm test
   ```

2. **Update Sprint 1 Documentation**

3. **Commit Changes:**
   ```powershell
   git add .
   git commit -m "feat: Frontend-backend authentication integration

   - Frontend now connects to real FastAPI backend
   - Login flow working end-to-end
   - JWT authentication fully integrated
   - Updated authService to use form data for OAuth2
   - Created .env for API configuration
   "
   ```

4. **Continue with remaining Sprint 1 features!**

---

**🚀 Ready to test? Follow Steps 3.1-3.5 above!**


