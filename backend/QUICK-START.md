# Quick Start Guide - Backend Server

## Prerequisites Check

Before starting, verify:
- ✅ Python 3.11+ installed
- ✅ In the `backend` directory

---

## Option 1: Using PowerShell Script (Recommended)

```powershell
# From the backend directory:
.\run_server.ps1
```

This script will:
1. Activate the virtual environment automatically
2. Check dependencies
3. Start the server

---

## Option 2: Manual Step-by-Step

### Step 1: Activate Virtual Environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
venv\Scripts\activate.bat
```

**You'll see `(venv)` appear in your prompt when activated.**

### Step 2: Verify Environment

```powershell
# Check Python version (should be from venv)
python --version

# Check where Python is (should be in venv folder)
Get-Command python | Select-Object -ExpandProperty Source

# Test imports
python -c "import uvicorn; import fastapi; print('Dependencies OK')"
```

### Step 3: Start Server

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Verification

Once the server starts, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
Created admin user: admin
```

### Test the Server

Open your browser and visit:
- **API Docs:** http://127.0.0.1:8000/docs
- **Root:** http://127.0.0.1:8000/
- **Health Check:** http://127.0.0.1:8000/api/v1/health

---

## Common Issues & Solutions

### ❌ Issue: "ModuleNotFoundError: No module named 'uvicorn'"

**Cause:** Virtual environment not activated

**Solution:**
```powershell
# Make sure you see (venv) in your prompt
.\venv\Scripts\Activate.ps1

# Then try again
python -m uvicorn app.main:app --reload
```

---

### ❌ Issue: "No module named 'sqlalchemy'"

**Cause:** Dependencies not installed in the virtual environment

**Solution:**
```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify
pip list
```

---

### ❌ Issue: Wrong Python version

**Cause:** Using system Python instead of venv Python

**Solution:**
```powershell
# Check which Python you're using
Get-Command python | Select-Object -ExpandProperty Source

# Should output something like:
# C:\...\backend\venv\Scripts\python.exe

# If not, make sure venv is activated:
.\venv\Scripts\Activate.ps1
```

---

### ❌ Issue: "Address already in use"

**Cause:** Port 8000 is already in use

**Solution:**
```powershell
# Stop any existing uvicorn processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Or use a different port:
python -m uvicorn app.main:app --reload --port 8001
```

---

## Test User Credentials

After server starts, use these credentials to test:

- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@aiwebtest.com`
- **Role:** `admin`

---

## Stopping the Server

Press **CTRL+C** in the terminal running the server.

---

## Next Steps

Once the server is running successfully:

1. ✅ Visit http://127.0.0.1:8000/docs
2. ✅ Click "Authorize" button
3. ✅ Login with `admin` / `admin123`
4. ✅ Try the `/api/v1/auth/me` endpoint
5. ✅ Explore other endpoints

---

## Still Having Issues?

Check:
1. You're in the `backend` directory
2. Virtual environment exists: `Test-Path venv`
3. Dependencies installed: `pip list` (after activating venv)
4. Python version: `python --version` (should be 3.11+)

If problems persist, try recreating the virtual environment:
```powershell
# Remove old venv
Remove-Item -Recurse -Force venv

# Create new venv
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --reload
```

