# ⚡ Quick Test Instructions - Frontend-Backend Integration

## 🎯 **3-Step Quick Start**

### **Step 1: Create `.env`** (30 seconds)

```powershell
cd frontend
@"
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_USE_MOCK=false
"@ | Out-File -FilePath .env -Encoding utf8
```

---

### **Step 2: Start Backend** (1 minute)

```powershell
cd backend
.\run_server.ps1
```

**Wait for:** `Application startup complete.`

---

### **Step 3: Start Frontend** (1 minute)

```powershell
cd frontend
npm run dev
```

**Open:** http://localhost:5173

**Login:**
- Username: `admin`
- Password: `admin123`

---

## ✅ **Expected: Working!**

- ✅ Login successful
- ✅ Redirects to dashboard
- ✅ User "admin" shown in header
- ✅ No console errors

---

## ❌ **If Something's Wrong:**

### **Backend won't start?**
```powershell
cd backend
.\venv\Scripts\activate
python start_server.py
```

### **Frontend still using mock data?**
1. Check `.env` exists: `cd frontend ; ls .env`
2. Restart Vite: Stop (Ctrl+C) and run `npm run dev` again

### **Login fails?**
- Check backend is running: http://127.0.0.1:8000/docs
- Try in Swagger UI first (see `backend/SWAGGER-UI-AUTH-GUIDE.md`)

---

## 📚 **Full Guides:**

- **Complete Tutorial:** `FRONTEND-BACKEND-INTEGRATION-GUIDE.md`
- **Overview:** `INTEGRATION-READY.md`
- **Summary:** `SPRINT-1-INTEGRATION-COMPLETE-SUMMARY.md`

---

**🚀 Total time: ~3 minutes to test!**

