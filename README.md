# AI Web Test v1.0
## Multi-Agent Test Automation Platform

**Status:** ✅ Sprint 3 Complete | � Production Ready MVP  
**Version:** 1.0.0  
**Last Updated:** December 9, 2025

---

## 🎯 Project Overview

AI Web Test is a multi-agent test automation platform that reduces test creation time from days to minutes. It combines AI-powered test generation with browser automation to create, execute, and monitor web application tests.

### Key Features (Current)
- ✅ **AI Test Generation** - Natural language to automated tests (3 providers)
- ✅ **Browser Automation** - Real browser execution with Stagehand + Playwright
- ✅ **Queue System** - Concurrent execution management (max 5 simultaneous)
- ✅ **Screenshot Capture** - Every test step documented with visual proof
- ✅ **Knowledge Base** - Document upload and categorization
- ✅ **Real-time Monitoring** - Live execution progress tracking
- ✅ **Test Suites** - Group and execute multiple tests together
- ✅ **Multi-Provider AI** - Google Gemini, Cerebras, OpenRouter support
- ✅ **Execution History** - Complete audit trail with filtering and search
- ✅ **Template System** - Pre-built templates for common test scenarios

---

## 📊 Current Status

### Sprint 3 Complete ✅
- **Backend:** 100% complete and tested (68+ endpoints)
- **Frontend:** 100% complete and tested (10 pages)
- **API Endpoints:** 68+ endpoints operational
- **Test Coverage:** 100% (111+ tests passing)
- **Queue System:** Production-ready (5 concurrent executions)
- **Test Suites:** Fully implemented and tested
- **Multi-Provider AI:** Google, Cerebras, OpenRouter integrated
- **Documentation:** 25+ comprehensive guides
- **Production Readiness:** ✅ Ready for deployment

### Production Ready �
- **Test Generation:** 5-90 seconds with 3 AI providers
- **Test Execution:** Real browsers with full automation
- **Test Management:** Complete CRUD with search/filter
- **Test Suites:** Group testing with sequential/parallel execution
- **Knowledge Base:** Multi-format upload with text extraction
- **Authentication:** JWT + session management + password reset
- **Security:** Rate limiting + security headers + input validation
- **Performance:** Queue <50ms, API <200ms response times

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12.x
- Node.js 18.x or 20.x LTS
- Git

### Backend Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1/backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies (includes Stagehand + Playwright)
pip install -r requirements.txt

# Install Chromium browser for Playwright/Stagehand
playwright install chromium

# Configure environment
copy .env.example .env
# Edit .env with your OpenRouter API key

# Start server
python start_server.py
```

**Verify:**
- Open: http://127.0.0.1:8000/docs
- Login: admin@aiwebtest.com / admin123

### Frontend Setup (Coming Soon)

```bash
cd frontend
npm install
npm run dev
```

---

## 📚 Documentation

### For New Developers
- **[NEW-PC-SETUP.md](NEW-PC-SETUP.md)** - Complete setup guide for new PC
- **[API-CHANGELOG.md](API-CHANGELOG.md)** - API version history

### Project Documentation
- **[Project Management Plan](project-documents/AI-Web-Test-v1-Project-Management-Plan.md)** - Complete project plan
- **[Sprint 3 Frontend Guide](project-documents/SPRINT-3-FRONTEND-GUIDE.md)** - Frontend development guide (900+ lines)
- **[API Quick Reference](project-documents/SPRINT-3-API-QUICK-REFERENCE.md)** - API endpoint reference

### Technical Documentation
- **[Product Requirements](project-documents/AI-Web-Test-v1-PRD.md)** - Full PRD
- **[Software Requirements](project-documents/AI-Web-Test-v1-SRS.md)** - Technical specs
- **[UI Design Document](project-documents/ai-web-test-ui-design-document.md)** - UI/UX specifications

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Pydantic 2.5.0
- Playwright 1.56.0
- Stagehand 0.5.6
- Python 3.12.10

**Database:**
- SQLite (development)
- PostgreSQL (production - planned)

**Authentication:**
- JWT tokens
- Role-based access control

**AI/LLM:**
- Multiple providers supported:
  - **Google Gemini** (FREE with AI Studio)
  - **Cerebras** (Ultra-fast inference)
  - **OpenRouter** (50+ models including Claude, GPT-4)
- Configurable model selection
- See [Model Provider Comparison](./MODEL-PROVIDER-COMPARISON.md)

---

## 🔌 API Endpoints

### Current APIs (47 endpoints)

**Authentication (2)**
- POST `/api/v1/auth/login` - User login
- POST `/api/v1/auth/register` - User registration

**Test Management (6)**
- POST `/api/v1/tests` - Create test
- GET `/api/v1/tests` - List tests
- GET `/api/v1/tests/{id}` - Get test details
- PUT `/api/v1/tests/{id}` - Update test
- DELETE `/api/v1/tests/{id}` - Delete test
- POST `/api/v1/tests/generate` - AI test generation

**Test Execution (9)** ✨ New in Sprint 3
- POST `/api/v1/tests/{id}/run` - Execute test
- GET `/api/v1/executions/{id}` - Get execution details
- GET `/api/v1/executions` - List executions
- GET `/api/v1/executions/stats` - Execution statistics
- DELETE `/api/v1/executions/{id}` - Delete execution
- + 4 queue management endpoints

**Knowledge Base (13)**
- POST `/api/v1/kb/upload` - Upload document
- GET `/api/v1/kb/documents` - List documents
- GET `/api/v1/kb/categories` - List categories
- + 10 more endpoints

**Health (2)**
- GET `/api/v1/health` - Health check
- GET `/api/v1/health/db` - Database health

---

## 🧪 Testing

### Run Tests

```bash
cd backend
.\venv\Scripts\activate

# Quick verification
python test_final_verification.py

# Integration tests
python test_integration_e2e.py

# Generate sample data
python generate_sample_data.py
```

### Postman Collection

Import `backend/AI-Web-Test-Postman-Collection.json` to test all API endpoints.

---

## 📦 Project Structure

```
AI-Web-Test-v1/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Configuration
│   │   ├── crud/              # Database operations
│   │   ├── db/                # Database models
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── artifacts/
│   │   └── screenshots/       # Test screenshots
│   ├── venv/                  # Virtual environment
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment config
│   ├── start_server.py        # Server startup
│   └── test_*.py             # Test files
├── frontend/                   # React frontend (in progress)
│   ├── src/
│   ├── package.json
│   └── ... (to be developed)
├── project-documents/          # Documentation
│   ├── AI-Web-Test-v1-Project-Management-Plan.md
│   ├── SPRINT-3-FRONTEND-GUIDE.md
│   ├── SPRINT-3-API-QUICK-REFERENCE.md
│   └── ... (other docs)
├── API-CHANGELOG.md           # API version history
├── NEW-PC-SETUP.md            # Setup guide
└── README.md                  # This file
```

---

## 🎯 Roadmap

### Sprint 3 (Current)
- ✅ Backend: Browser automation + queue system
- 🎯 Frontend: Execution UI + history

### Sprint 4 (Next)
- Scheduled test execution
- Webhook notifications
- Advanced analytics
- Email notifications

### Phase 2 (Weeks 9-16)
- Self-healing tests
- Advanced agents
- KB full-text search
- Scheduled runs

### Phase 3 (Weeks 17-24)
- CI/CD integration
- Enterprise features
- Production monitoring

### Phase 4 (Weeks 25-32)
- Reinforcement Learning
- Continuous improvement
- Advanced ML features

---

## 🤝 Contributing

### For Backend Developers
1. Clone repository
2. Create feature branch
3. Follow code style (Black formatter)
4. Write tests
5. Submit PR

### For Frontend Developers
1. Read `SPRINT-3-FRONTEND-GUIDE.md`
2. Import Postman collection
3. Generate sample data
4. Start building!

---

## 📄 License

Proprietary - All rights reserved

---

## 👥 Team

**Backend Developer:** [Your name]  
**Frontend Developer:** [Friend's name]  
**Project Manager:** [Your name]

---

## 📞 Support

### Documentation
- **Setup Guide:** NEW-PC-SETUP.md
- **API Docs:** http://127.0.0.1:8000/docs (when running)
- **Frontend Guide:** project-documents/SPRINT-3-FRONTEND-GUIDE.md

### Resources
- **GitHub:** https://github.com/deencat/AI-Web-Test-v1
- **OpenRouter:** https://openrouter.ai/
- **Playwright:** https://playwright.dev/

---

## 🎉 Recent Achievements

### Sprint 3 Day 2 (Nov 25, 2025)
- ✅ Queue system implemented
- ✅ 5 concurrent execution management
- ✅ Priority-based queuing
- ✅ 9 new API endpoints
- ✅ 100% test coverage
- ✅ Complete frontend documentation

### Sprint 3 Day 1 (Nov 24, 2025)
- ✅ Stagehand + Playwright integration
- ✅ Real browser automation
- ✅ Screenshot capture
- ✅ Windows compatibility

### Sprint 2 Complete (Nov 23, 2025)
- ✅ Knowledge Base system
- ✅ Test management
- ✅ Execution tracking
- ✅ 38 API endpoints

---

## 📊 Statistics

**Current Metrics:**
- **API Endpoints:** 47
- **Test Coverage:** 100%
- **Code Lines:** 10,000+
- **Documentation:** 5,000+ lines
- **Success Rate:** 100% (19/19 tests)
- **Response Time:** < 100ms average

---

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...
DATABASE_URL=sqlite:///./aiwebtest.db
SECRET_KEY=your-secret-key-here

# Optional
MAX_CONCURRENT_EXECUTIONS=5
QUEUE_CHECK_INTERVAL=2
LOG_LEVEL=INFO
```

**Frontend (.env.local):**
```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

---

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check Python version
python --version  # Should be 3.12.x

# Reinstall dependencies
pip install -r requirements.txt

# Check .env file exists
ls .env
```

**Database errors:**
```bash
# Run migration
python add_queue_fields.py

# Verify migration
python verify_queue_fields.py
```

**Playwright errors:**
```bash
# Reinstall browser
playwright install chromium --with-deps
```

---

## 📝 Version History

### v0.3.0 - Sprint 3 (Nov 24-25, 2025)
- Queue system
- Browser automation
- 9 new API endpoints

### v0.2.0 - Sprint 2 (Nov 14-23, 2025)
- Knowledge Base system
- Test execution tracking
- 19 new API endpoints

### v0.1.0 - Sprint 1 (Nov 1-13, 2025)
- Initial release
- Authentication
- Test generation
- Basic API

---

**Last Updated:** November 25, 2025  
**Status:** Production-ready backend, frontend in development  
**Next Sprint:** Sprint 3 Frontend + Sprint 4 Planning

---

**🚀 Ready to automate your testing! Start with [NEW-PC-SETUP.md](NEW-PC-SETUP.md)**

