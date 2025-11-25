# Quick Start - New PC Setup
## AI Web Test v1.0 (5-Minute Reference)

**Full Guide:** [NEW-PC-SETUP.md](NEW-PC-SETUP.md) (850 lines)  
**This File:** Quick reference only

---

## ⚡ Prerequisites (Install First)

1. **Python 3.12.10** - https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH"
2. **Node.js 20.x LTS** - https://nodejs.org/
3. **Git** - https://git-scm.com/download/win
4. **VS Code + Copilot** - https://code.visualstudio.com/

---

## 🚀 Setup (Copy & Paste)

### 1. Clone Project
```powershell
cd ~\Projects
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1
```

### 2. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
```

### 3. Configure .env
```powershell
notepad .env
```

**Add your OpenRouter API key:**
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get key at: https://openrouter.ai/

### 4. Start Server
```powershell
python start_server.py
```

### 5. Verify
```powershell
# Open: http://127.0.0.1:8000/docs
# Login: admin@aiwebtest.com / admin123

# Run test:
python test_final_verification.py
```

**Expected:** `[OK] ALL SYSTEMS GO!`

---

## 📦 What's Installed

**From requirements.txt:**
- FastAPI 0.104.1 (API server)
- SQLAlchemy 2.0.23 (Database)
- Playwright 1.56.0 (Browser automation)
- **Stagehand 0.5.6** ← Browser automation wrapper
- Pydantic 2.5.0 (Data validation)
- + 45 other packages

**From playwright install:**
- Chromium browser binaries (~150MB)

---

## ✅ Verification Checklist

- [ ] Python 3.12 installed (`python --version`)
- [ ] Virtual env activated (prompt shows `(venv)`)
- [ ] Requirements installed (`pip show stagehand` → 0.5.6)
- [ ] Playwright browser installed (`playwright --version`)
- [ ] .env file configured with OpenRouter API key
- [ ] Server starts without errors
- [ ] Swagger UI loads at http://127.0.0.1:8000/docs
- [ ] Can login with admin credentials
- [ ] test_final_verification.py passes

---

## 🆘 Troubleshooting

### Backend won't start?
```powershell
# Check venv is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Check .env exists
ls .env
```

### Playwright errors?
```powershell
playwright install chromium --with-deps
```

### Database errors?
```powershell
python add_queue_fields.py
python verify_queue_fields.py
```

### More help?
See [NEW-PC-SETUP.md](NEW-PC-SETUP.md) section "Troubleshooting"

---

## 📚 Documentation

**Essential:**
- [NEW-PC-SETUP.md](NEW-PC-SETUP.md) - Complete setup guide (850 lines)
- [README.md](README.md) - Project overview (420 lines)
- [TRANSITION-SUMMARY.md](TRANSITION-SUMMARY.md) - Transition details

**API:**
- Swagger UI: http://127.0.0.1:8000/docs
- [API-CHANGELOG.md](API-CHANGELOG.md) - Version history
- Postman: Import `backend/AI-Web-Test-Postman-Collection.json`

**Project:**
- [Project Management Plan](project-documents/AI-Web-Test-v1-Project-Management-Plan.md)
- [Frontend Guide](project-documents/SPRINT-3-FRONTEND-GUIDE.md)
- [API Reference](project-documents/SPRINT-3-API-QUICK-REFERENCE.md)

---

## 🎯 Daily Commands

**Start Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python start_server.py
```

**Run Tests:**
```powershell
python test_final_verification.py      # Quick (5 tests)
python test_integration_e2e.py         # Full (13 tests)
```

**Generate Sample Data:**
```powershell
python generate_sample_data.py
```

---

## 📊 Current Status

- ✅ Sprint 3 Backend: Complete
- 🎯 Sprint 3 Frontend: Ready
- 📦 API Endpoints: 47
- ✅ Test Coverage: 100%
- 📝 Documentation: 6,000+ lines

---

**Setup Time:** 30-45 minutes  
**Last Updated:** November 25, 2025  
**Git Branch:** main  

**Start here → [NEW-PC-SETUP.md](NEW-PC-SETUP.md)**

