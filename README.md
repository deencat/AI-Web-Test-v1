# AI Web Test v1.1
## Multi-Agent Test Automation Platform

**Status:** 🔄 Phase 3 In Progress - Multi-Agent System (Sprint 7-9)  
**Version:** 1.1.0  
**Last Updated:** July 3, 2026

---

## 🎯 Project Overview

AI Web Test is a multi-agent test automation platform that reduces test creation time from days to minutes. It combines AI-powered test generation with browser automation to create, execute, and monitor web application tests.

### Key Features (Current)
- ✅ **AI Test Generation** - Natural language to automated tests (3 providers)
  - ⚠️ **Note:** KB integration with test generation planned for Phase 2
- ✅ **Browser Automation** - Real browser execution with Stagehand + Playwright
- ✅ **Queue System** - Concurrent execution management (max 5 simultaneous)
- ✅ **Screenshot Capture** - Every test step documented with visual proof
- ✅ **Knowledge Base** - Document upload and categorization
  - ⚠️ **Limitation:** KB documents not yet used as context in test generation
- ✅ **Real-time Monitoring** - Live execution progress tracking
- ✅ **Stop Execution** - Cooperative cancel for queued/running 3-tier runs (ADR-009)
- ✅ **Test Suites** - Group and execute multiple tests together
- ✅ **Multi-Provider AI** - Google Gemini, Cerebras, OpenRouter support
- ✅ **Execution History** - Complete audit trail with filtering and search
- ✅ **Template System** - Pre-built templates for common test scenarios

### Planned for Phase 2 (Sprint 5)
- 🎯 **KB-Aware Test Generation** - Use uploaded documents as context
- 🎯 **Category-Filtered Generation** - Use only relevant KB docs per test type
- 🎯 **KB Citation in Tests** - Generated tests reference KB sources
- 🎯 **Requirements Agent** - Analyze PRDs automatically
- 🎯 **Analysis Agent** - Root cause analysis for failures
- 🎯 **Self-Healing Tests** - Automatic selector updates

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

### Production Ready ✅ �
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
- **Python 3.11** (matches `backend/Dockerfile`; 3.12+ may work locally)
- **Node.js 18.x or 20.x LTS**
- **Git**
- **Docker** (optional, for PostgreSQL 15 + Redis 7 via `docker-compose.yml`)
- **pytest 9.0.2+** (for Phase 3 agent testing)

### Backend Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1-1/backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies (includes Stagehand + Playwright + pytest)
pip install -r requirements.txt

# Install pytest for Phase 3 agent testing
pip install pytest pytest-asyncio

# Install Chromium browser for Playwright/Stagehand
playwright install chromium

# Configure environment
copy env.example .env
# Edit .env with your API keys (OpenRouter, Google AI Studio, Cerebras)

# Start server
python start_server.py
```

**Verify Backend:**
- Open API docs: http://127.0.0.1:8000/docs
- Default login: admin / admin123

### Phase 3 Development Setup (Additional)

```bash
# Verify pytest installation
python -m pytest --version  # Should show 9.0.2+

# Run Phase 3 agent tests (55 tests)
cd backend
python -m pytest tests/agents/ -v

# Run RequirementsAgent tests only (26 tests)
python -m pytest tests/agents/test_requirements_agent.py -v

# Run Three HK E2E tests (21 tests)
python -m pytest tests/agents/test_requirements_agent_three_hk.py -v

# Run E2E integration (8 tests)
python -m pytest tests/agents/test_requirements_integration.py -v

# Run 4-Agent E2E REAL test (live crawl + LLM + execution) - see tests/integration/E2E_REAL_RUN_GUIDE.md
python -u -m pytest tests/integration/test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

**Phase 3 Status:**
- ✅ EA.6 Complete: RequirementsAgent (55/55 tests passing)
- 🔄 Sprint 9: AnalysisAgent + EvolutionAgent (in planning)
- 📚 Documentation: Phase3-project-documents/ folder

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API defaults to `http://127.0.0.1:8000/api/v1` (set `VITE_API_BASE_URL` in `.env.local` if needed).

### Docker Infrastructure (PostgreSQL + Redis)

```bash
docker compose up -d db redis
# Set DATABASE_URL in backend/.env to postgresql://aiwebtest:aiwebtest123@localhost:5432/aiwebtest
```

---

## 📚 Documentation

### For New Developers
- **[NEW-PC-SETUP.md](documentation/archive/NEW-PC-SETUP.md)** - Complete setup guide for new PC (archived)
- **[API-CHANGELOG.md](API-CHANGELOG.md)** - API version history

### Phase 3 Documentation (Current)
- **[Phase 3 Architecture](Phase3-project-documents/Phase3-Architecture-Design-Complete.md)** - Multi-agent system design (845 lines)
- **[Phase 3 Implementation Guide](Phase3-project-documents/Phase3-Implementation-Guide-Complete.md)** - Sprint 7-12 tasks (2201 lines)
- **[Phase 3 Project Plan](Phase3-project-documents/Phase3-Project-Management-Plan-Complete.md)** - Timeline and deliverables

### Project Documentation (Phase 1-2)
- **[Project Management Plan](project-documents/AI-Web-Test-v1-Project-Management-Plan.md)** - Complete project plan
- **[Sprint 3 Frontend Guide](project-documents/SPRINT-3-FRONTEND-GUIDE.md)** - Frontend development guide (900+ lines)
- **[API Quick Reference](project-documents/SPRINT-3-API-QUICK-REFERENCE.md)** - API endpoint reference

### Technical Documentation
- **[ADRs](documentation/)** - Architecture decision records (ADR-002 through ADR-009)
- **[API Agentic Workflow Reference](documentation/API-Agentic-Workflow-Reference.md)** - Agent/crawl/execution API quick reference
- **[GAN Harness](gan-harness/spec.md)** - Stop Execution spec and evaluation rubric
- **[Product Requirements](project-documents/AI-Web-Test-v1-PRD.md)** - Full PRD
- **[Software Requirements](project-documents/AI-Web-Test-v1-SRS.md)** - Technical specs
- **[UI Design Document](project-documents/ai-web-test-ui-design-document.md)** - UI/UX specifications

### Codemaps (Refreshed)
- **[Codemap Index](docs/CODEMAPS/INDEX.md)** - High-level architecture map directory
- **[Backend Codemap](docs/CODEMAPS/backend.md)** - API and service architecture
- **[Frontend Codemap](docs/CODEMAPS/frontend.md)** - Routes and UI module map
- **[Database Codemap](docs/CODEMAPS/database.md)** - ORM entities and relationships
- **[Integrations Codemap](docs/CODEMAPS/integrations.md)** - External service/provider dependencies
- **[Workers Codemap](docs/CODEMAPS/workers.md)** - Background processing model

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI >=0.115.0
- SQLAlchemy 2.0.23
- Pydantic 2.5.0+
- Playwright 1.56.0
- Stagehand 0.5.6
- browser-use >=0.12.1 (crawl-and-save)
- Python 3.11 (Docker base image)
- Cerebras Cloud SDK 1.0.0+ (Phase 3 agents)

**Frontend:**
- React ^19.2.0, Vite ^7.1.7, TypeScript ~5.9.3

**Database & Cache:**
- PostgreSQL 15 (`postgres:15-alpine` via docker-compose)
- Redis 7 (`redis:7-alpine` via docker-compose)
- SQLite supported for local development (`DATABASE_URL=sqlite:///./aiwebtest.db`)

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

### Current APIs (200+ endpoints across v1 and v2)

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

**Test Execution**
- POST `/api/v1/executions/tests/{id}/run` - Queue test execution
- GET `/api/v1/executions/{id}` - Get execution details
- DELETE `/api/v1/executions/{id}/cancel` - Cooperative cancel (ADR-009)
- GET `/api/v1/executions` - List executions
- GET `/api/v1/executions/stats` - Execution statistics
- DELETE `/api/v1/executions/{id}` - Delete execution record
- + queue management endpoints

**Agent Workflow (v2)**
- POST `/api/v2/generate-tests`, `/observation`, `/requirements`, `/analysis`, `/evolution`
- POST `/api/v2/crawl-and-save-test`
- GET/DELETE `/api/v2/workflows/{id}` — status, results, cancel

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
AI-Web-Test-v1-1/
├── backend/                    # FastAPI backend
│   ├── agents/                # Phase 3: Multi-agent system
│   │   ├── requirements_agent.py  # EA.6 Complete (815 lines)
│   │   └── ... (AnalysisAgent, EvolutionAgent coming)
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Configuration
│   │   ├── crud/              # Database operations
│   │   ├── db/                # Database models
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── tests/
│   │   └── agents/            # Phase 3: Agent unit tests
│   │       ├── test_requirements_agent.py  # 26 tests
│   │       ├── test_requirements_agent_three_hk.py  # 21 tests
│   │       └── test_requirements_integration.py  # 8 tests
│   ├── artifacts/
│   │   └── screenshots/       # Test screenshots
│   ├── venv/                  # Virtual environment
│   ├── requirements.txt       # Python dependencies
│   ├── env.example            # Environment template
│   ├── .env                   # Environment config (gitignored)
│   ├── start_server.py        # Server startup
│   └── test_*.py              # Integration test files
├── frontend/                   # React frontend (in progress)
│   ├── src/
│   ├── package.json
│   └── ... (to be developed)
├── Phase3-project-documents/   # Phase 3 Documentation
│   ├── Phase3-Architecture-Design-Complete.md  # 845 lines
│   ├── Phase3-Implementation-Guide-Complete.md # 2201 lines
│   └── Phase3-Project-Management-Plan-Complete.md
├── project-documents/          # Phase 1-2 Documentation
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

### Phase 3 (Current - January 2026)
- ✅ Sprint 7 (EA.4-EA.5): ObservationAgent + Communication infrastructure
- ✅ Sprint 8 (EA.6): RequirementsAgent implementation (55/55 tests passing)
- 🔄 Sprint 9 (EA.7-EA.8): AnalysisAgent + EvolutionAgent (in planning)
- 📅 Sprint 10: Integration + E2E testing
- 📅 Sprint 11: Performance optimization
- 📅 Sprint 12: Production deployment

### Completed Sprints
- ✅ Sprint 1-3 (Nov 2025): Core API + Authentication + Knowledge Base
- ✅ Sprint 4 (Dec 2025): Browser automation + Queue system + Execution feedback
- ✅ Sprint 5 (Dec 2025): 3-tier execution (Playwright → XPath → Stagehand AI)
- ✅ Sprint 6 (Jan 2026): Self-healing tests + Learning mechanism

### Phase 4 (Planned - Q2 2026)
- CI/CD integration
- Advanced ML features
- Enterprise deployment
- Production monitoring

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
- **Setup Guide:** documentation/archive/NEW-PC-SETUP.md
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
- **API Endpoints:** 200+ (v1 + v2)
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
OPENROUTER_API_KEY=sk-or-v1-...          # Get from https://openrouter.ai/keys
GOOGLE_API_KEY=...                       # Get from https://aistudio.google.com/app/apikey
CEREBRAS_API_KEY=...                     # Get from https://cloud.cerebras.ai/ (Phase 3)
AZURE_OPENAI_API_KEY=...                 # Azure OpenAI for 4-agent E2E (ObservationAgent, RequirementsAgent, etc.)
AZURE_OPENAI_ENDPOINT=...                # Azure OpenAI endpoint (e.g. https://your-resource.openai.azure.com)
DATABASE_URL=sqlite:///./aiwebtest.db
SECRET_KEY=your-secret-key-here          # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

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
python --version  # Should be 3.11.x (Docker) or 3.11+

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

**Last Updated:** July 3, 2026  
**Status:** Phase 3 — multi-agent system operational; Stop Execution shipped (ADR-009)  
**ADRs:** `documentation/ADR-001` through `ADR-009` (see `documentation/` folder)  
**GAN Harness:** `gan-harness/spec.md`, `gan-harness/eval-report.md`

---

## 🚀 Quick Resume Development (Cursor IDE)

```bash
# 1. Activate Python environment
cd backend
.\venv\Scripts\activate

# 2. Verify Python & pytest
python --version  # Should be 3.11.x
python -m pytest --version  # Should be 9.0.2+

# 3. Run Phase 3 tests to verify setup
python -m pytest tests/agents/ -v  # Should see 55/55 passing

# 5. Review Phase 3 documentation
# - Phase3-project-documents/Phase3-Architecture-Design-Complete.md
# - Phase3-project-documents/Phase3-Implementation-Guide-Complete.md

# 6. Check current agent implementation
# - backend/agents/requirements_agent.py (815 lines - EA.6 Complete)

# 7. Start server (if needed)
python start_server.py  # API: http://127.0.0.1:8000/docs
```

**✅ You're ready to continue Sprint 9 development!**

