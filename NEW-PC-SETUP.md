# New PC Setup Guide - AI Web Test v1.0
## Complete Installation & Configuration Instructions

**Version:** 1.0  
**Date:** November 25, 2025  
**Target:** New PC with Copilot IDE  
**OS:** Windows 11

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Software Installation](#software-installation)
3. [Project Setup](#project-setup)
4. [Backend Configuration](#backend-configuration)
5. [Frontend Configuration](#frontend-configuration)
6. [IDE Setup (Copilot)](#ide-setup-copilot)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software Versions
- **Python:** 3.12.x (tested on 3.12.10)
- **Node.js:** 18.x or 20.x LTS
- **Git:** Latest version
- **IDE:** GitHub Copilot (VS Code with Copilot extension)

### System Requirements
- **OS:** Windows 11
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 5GB free space
- **Internet:** Required for API calls and package downloads

---

## Software Installation

### 1. Install Python 3.12

**Download:**
```
https://www.python.org/downloads/windows/
```

**Installation Steps:**
1. Run installer
2. ✅ Check "Add Python 3.12 to PATH"
3. Click "Install Now"
4. Verify installation:
```powershell
python --version
# Should show: Python 3.12.x
```

---

### 2. Install Node.js

**Download:**
```
https://nodejs.org/en/download/
```

**Installation Steps:**
1. Download LTS version (20.x)
2. Run installer with default settings
3. Verify installation:
```powershell
node --version
# Should show: v20.x.x

npm --version
# Should show: 10.x.x
```

---

### 3. Install Git

**Download:**
```
https://git-scm.com/download/win
```

**Installation Steps:**
1. Run installer
2. Use default settings
3. Verify installation:
```powershell
git --version
# Should show: git version 2.x.x
```

---

### 4. Install VS Code with Copilot

**Download VS Code:**
```
https://code.visualstudio.com/download
```

**Install Copilot Extensions:**
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Install:
   - **GitHub Copilot** (by GitHub)
   - **GitHub Copilot Chat** (by GitHub)
4. Sign in with GitHub account
5. Verify Copilot is active (check status bar)

**Recommended Extensions:**
- Python (by Microsoft)
- Pylance (by Microsoft)
- ESLint (by Microsoft)
- Prettier (by Prettier)
- GitLens (by GitKraken)
- Thunder Client (for API testing)

---

## Project Setup

### 1. Clone Repository

```powershell
# Create projects folder
cd ~
mkdir Projects
cd Projects

# Clone repository
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1

# Check branch
git branch -a
# Should show: * main

# Verify you're on latest
git pull origin main
```

---

### 2. Project Structure

```
AI-Web-Test-v1/
├── backend/                    # FastAPI backend
│   ├── app/                    # Application code
│   ├── venv/                   # Virtual environment (create this)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (create from .env.example)
│   └── aiwebtest.db           # SQLite database
├── frontend/                   # React frontend (future)
├── project-documents/          # Documentation
│   ├── AI-Web-Test-v1-Project-Management-Plan.md
│   ├── SPRINT-3-FRONTEND-GUIDE.md
│   └── ... (other docs)
├── API-CHANGELOG.md           # API version history
├── NEW-PC-SETUP.md            # This file
└── README.md                  # Project README
```

---

## Backend Configuration

### 1. Create Virtual Environment

```powershell
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Verify activation (venv should show in prompt)
# (venv) PS C:\Users\...\backend>
```

---

### 2. Install Python Dependencies

```powershell
# Ensure venv is activated
pip install --upgrade pip

# Install all dependencies (including Stagehand)
pip install -r requirements.txt

# This installs:
# - FastAPI, Uvicorn (API server)
# - SQLAlchemy, Alembic (Database)
# - Pydantic (Data validation)
# - python-jose, passlib (Authentication)
# - PyPDF2, python-docx (File handling)
# - Playwright 1.56.0 (Browser automation)
# - Stagehand 0.5.6 (Browser automation wrapper)
# - websockets 15.0.1 (WebSocket support)
# + all other dependencies (50+ packages total)
```

**Expected Output:**
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 playwright-1.56.0 stagehand-0.5.6 ...
(50+ packages)
```

**Note:** Stagehand is included in requirements.txt and will be installed automatically with the above command.

---

### 3. Install Playwright Browsers

**Important:** Playwright and Stagehand are already installed from requirements.txt in step 2, but you need to download the actual browser binaries.

```powershell
# Install Chromium browser for Playwright/Stagehand
playwright install chromium

# This downloads Chromium browser (~150MB)
```

**Expected Output:**
```
Downloading Chromium 125.0.6422.14 (playwright build v1124)
100% [================================] 150 MB
Chromium 125.0.6422.14 (playwright build v1124) downloaded to C:\Users\...
```

**What This Does:**
- Downloads Chromium browser binary
- Stagehand uses this browser for test execution
- Required for Sprint 3 browser automation features

**Verify Installation:**
```powershell
# Check Stagehand is installed
pip show stagehand

# Should show:
# Name: stagehand
# Version: 0.5.6
# Summary: Browser automation library
# ...

# Check Playwright is installed
pip show playwright

# Should show:
# Name: playwright
# Version: 1.56.0
# ...
```

---

### 4. Configure Environment Variables

```powershell
# Copy example env file
copy .env.example .env

# Edit .env file
notepad .env
```

**Required Configuration (.env):**
```bash
# Database (SQLite - default, no changes needed)
DATABASE_URL=sqlite:///./aiwebtest.db

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (adjust if frontend on different port)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:3000","http://127.0.0.1:5173"]

# OpenRouter API (for AI test generation)
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# LLM Model Selection
OPENROUTER_MODEL=qwen/qwen-2.5-7b-instruct  # Free model

# Browser Automation
STAGEHAND_ENV=LOCAL  # Use LOCAL for development

# Queue Configuration
MAX_CONCURRENT_EXECUTIONS=5
QUEUE_CHECK_INTERVAL=2
EXECUTION_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

**Get OpenRouter API Key:**
1. Go to: https://openrouter.ai/
2. Sign up / Log in
3. Go to Keys section
4. Create new API key
5. Copy and paste into .env

---

### 5. Initialize Database

```powershell
# Database is auto-created on first run
# Just start the server (see next section)
```

---

### 6. Start Backend Server

```powershell
# Ensure you're in backend folder with venv activated
python start_server.py

# Alternative:
# uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['F:\AI-Web-Test v1\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
[KB] Initializing predefined categories...
[=] Category exists: System Guide
...
INFO:     Application startup complete.
```

---

### 7. Verify Backend is Running

**Open in Browser:**
```
http://127.0.0.1:8000/docs
```

**You should see:**
- Swagger UI with all API endpoints
- 47 endpoints across multiple categories
- Login, Test Execution, Queue Management, etc.

**Test Login:**
```
POST /api/v1/auth/login
username: admin@aiwebtest.com
password: admin123

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1...",
  "token_type": "bearer"
}
```

---

## Frontend Configuration

### 1. Navigate to Frontend Folder

```powershell
cd ..\frontend
# or: cd F:\AI-Web-Test-v1\frontend
```

---

### 2. Install Node Dependencies

```powershell
# Install all packages
npm install

# This may take 2-3 minutes
```

**Expected Output:**
```
added 1500+ packages in 2m
```

---

### 3. Configure Frontend Environment

```powershell
# Create .env file
notepad .env.local
```

**Add Configuration:**
```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

---

### 4. Start Frontend Development Server

```powershell
npm run dev
```

**Expected Output:**
```
VITE v5.x.x ready in 1000 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

---

## IDE Setup (Copilot)

### 1. Open Project in VS Code

```powershell
# From project root
code .
```

---

### 2. Configure Workspace Settings

**Create .vscode/settings.json:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/venv": false,
    "**/node_modules": true
  },
  "github.copilot.enable": {
    "*": true,
    "python": true,
    "javascript": true,
    "typescript": true,
    "markdown": true
  }
}
```

---

### 3. Copilot Configuration

**Enable Copilot Suggestions:**
1. Open Command Palette (Ctrl+Shift+P)
2. Type: "Copilot: Enable"
3. Verify Copilot icon in status bar shows checkmark

**Copilot Chat:**
- Press Ctrl+I for inline chat
- Press Ctrl+Shift+I for sidebar chat
- Use @workspace to ask about entire project

---

### 4. Recommended Keyboard Shortcuts

**Copilot:**
- `Tab` - Accept suggestion
- `Alt+]` - Next suggestion
- `Alt+[` - Previous suggestion
- `Ctrl+I` - Open inline chat
- `Ctrl+Shift+I` - Open chat panel

**VS Code:**
- `Ctrl+Shift+P` - Command palette
- `Ctrl+`` - Toggle terminal
- `Ctrl+B` - Toggle sidebar
- `Ctrl+P` - Quick file open

---

## Verification

### 1. Backend Verification

```powershell
cd backend
.\venv\Scripts\activate
python test_final_verification.py
```

**Expected Output:**
```
[OK] Login successful
[OK] Test case retrieved
[OK] 5 tests queued successfully
[OK] Queue status operational
[OK] 3/5 completed in 20 seconds
[OK] 3/3 passed (100%)

[OK] ALL SYSTEMS GO!
```

---

### 2. Integration Test

```powershell
python test_integration_e2e.py
```

**Expected Output:**
```
[✓] ALL TESTS PASSED!
13/13 tests succeeded
```

---

### 3. Generate Sample Data

```powershell
python generate_sample_data.py
```

**Expected Output:**
```
[OK] Created 10 test cases
[OK] Queued 30 executions
[OK] System now has rich sample data
```

---

### 4. Import Postman Collection

**In Postman:**
1. Open Postman
2. Click "Import"
3. Select: `backend/AI-Web-Test-Postman-Collection.json`
4. Run "Authentication > Login"
5. All other endpoints now work with saved token

---

## Troubleshooting

### Issue 1: Python not found

**Error:** `'python' is not recognized...`

**Solution:**
```powershell
# Check if Python is in PATH
python --version

# If not found, add to PATH:
# 1. Search "Environment Variables" in Windows
# 2. Edit "Path" under User variables
# 3. Add: C:\Users\YourName\AppData\Local\Programs\Python\Python312
# 4. Restart PowerShell
```

---

### Issue 2: pip install fails

**Error:** `pip install -r requirements.txt` fails

**Solutions:**
```powershell
# Update pip first
python -m pip install --upgrade pip

# If specific package fails, install separately:
pip install fastapi uvicorn
pip install sqlalchemy pydantic
pip install playwright stagehand

# Then try requirements.txt again
pip install -r requirements.txt
```

---

### Issue 3: Playwright install fails

**Error:** `playwright install chromium` fails

**Solution:**
```powershell
# Install Playwright with all dependencies
pip install playwright
playwright install chromium --with-deps

# If still fails on Windows:
# Run PowerShell as Administrator
playwright install-deps chromium
```

---

### Issue 4: Backend won't start

**Error:** Server fails to start

**Solutions:**
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <process_id> /F

# Check database
# Delete aiwebtest.db if corrupted, will recreate

# Check .env file exists and is configured

# Check venv is activated
# Prompt should show (venv)
```

---

### Issue 5: Database migration needed

**Error:** Database errors after git pull

**Solution:**
```powershell
cd backend
.\venv\Scripts\activate

# Run migration scripts
python add_queue_fields.py

# Verify migration
python verify_queue_fields.py
```

---

### Issue 6: CORS errors in frontend

**Error:** Frontend can't connect to backend

**Solution:**
1. Check backend .env has correct CORS_ORIGINS
2. Ensure frontend URL matches (http://localhost:5173)
3. Restart backend server after .env changes

---

### Issue 7: OpenRouter API errors

**Error:** Test generation fails

**Solution:**
```powershell
# Verify API key in .env
notepad .env
# Check OPENROUTER_API_KEY is set

# Test API key:
curl -H "Authorization: Bearer YOUR_API_KEY" https://openrouter.ai/api/v1/models

# Try free model:
OPENROUTER_MODEL=qwen/qwen-2.5-7b-instruct
```

---

## Quick Reference

### Daily Workflow

**Start Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python start_server.py
```

**Start Frontend:**
```powershell
cd frontend
npm run dev
```

**Run Tests:**
```powershell
cd backend
.\venv\Scripts\activate
python test_final_verification.py
```

---

### Common Commands

**Backend:**
```powershell
# Activate venv
.\venv\Scripts\activate

# Start server
python start_server.py

# Run tests
python test_integration_e2e.py

# Generate sample data
python generate_sample_data.py

# Check database
python verify_queue_fields.py
```

**Git:**
```powershell
# Pull latest
git pull origin main

# Check status
git status

# Create branch
git checkout -b feature/my-feature

# Commit changes
git add .
git commit -m "feat: description"
git push origin feature/my-feature
```

---

## Environment Variables Reference

### Backend (.env)

```bash
# Database
DATABASE_URL=sqlite:///./aiwebtest.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=qwen/qwen-2.5-7b-instruct

# Browser
STAGEHAND_ENV=LOCAL

# Queue
MAX_CONCURRENT_EXECUTIONS=5
QUEUE_CHECK_INTERVAL=2

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

---

## File Checklist

**Must Have:**
- [x] `.env` file in backend/ (created from .env.example)
- [x] `venv/` folder in backend/ (python virtual environment)
- [x] `node_modules/` in frontend/ (npm packages)
- [x] `aiwebtest.db` in backend/ (auto-created on first run)

**Should Not Commit:**
- [ ] `.env` file (contains secrets)
- [ ] `venv/` folder (too large)
- [ ] `node_modules/` folder (too large)
- [ ] `*.pyc` files (Python cache)
- [ ] `__pycache__/` folders (Python cache)
- [ ] `aiwebtest.db` (local database)

---

## Documentation Links

**Essential Reading:**
- `README.md` - Project overview
- `API-CHANGELOG.md` - API version history
- `project-documents/AI-Web-Test-v1-Project-Management-Plan.md` - Complete project plan
- `project-documents/SPRINT-3-FRONTEND-GUIDE.md` - Frontend development guide
- `project-documents/SPRINT-3-API-QUICK-REFERENCE.md` - API quick reference

**For Frontend Developer:**
- `SPRINT-3-FRONTEND-HANDOFF.md` - Frontend handoff guide
- `backend/AI-Web-Test-Postman-Collection.json` - Postman collection

---

## Success Checklist

After completing this setup, you should have:

- [x] Python 3.12 installed
- [x] Node.js 20.x installed
- [x] Git installed
- [x] VS Code with Copilot installed
- [x] Project cloned from GitHub
- [x] Backend venv created and activated
- [x] Python dependencies installed (requirements.txt)
- [x] Playwright chromium installed
- [x] Backend .env file configured
- [x] Backend server starts successfully
- [x] Can access Swagger UI at http://127.0.0.1:8000/docs
- [x] Can login with admin@aiwebtest.com / admin123
- [x] Frontend dependencies installed (npm install)
- [x] Frontend starts on http://localhost:5173
- [x] Postman collection imported
- [x] All verification tests pass

---

## Getting Help

### Resources
- **API Documentation:** http://127.0.0.1:8000/docs (when server running)
- **Project Docs:** `project-documents/` folder
- **Issues:** Check `TROUBLESHOOTING.md` (if exists)
- **GitHub:** https://github.com/deencat/AI-Web-Test-v1

### Contact
- **Backend Developer:** [Your contact info]
- **Frontend Developer:** [Friend's contact info]

---

**Document Version:** 1.0  
**Last Updated:** November 25, 2025  
**Next Review:** After Sprint 4  
**Status:** Complete and tested ✅

