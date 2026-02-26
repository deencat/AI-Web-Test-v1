# Dual Stagehand Provider System - Decision & Implementation Plan

**Date:** December 24, 2025  
**Decision:** ✅ **Option A Selected** - Sprint 4 Extension (Week 11-14)  
**Status:** ⏳ **PLANNED** - Ready to start after Sprint 4 core features complete

---

## 🎯 Decision Summary

**Selected Option:** Option A - Sprint 4 Extension (Week 11-14)

**Rationale:**
- Completes execution engine enhancement before Phase 3
- Provides data for Phase 3 decision-making
- Keeps Phase 2 focused on execution capabilities
- Developer A has capacity after test editing feature completion

---

## 📅 Timeline

**Start Date:** Week 11 (after Sprint 4 core features complete)  
**Duration:** 3-4 weeks (92-136 hours)  
**Completion:** Week 14 (end of Phase 2)  
**Owner:** Developer A

**Prerequisites:**
- ✅ Sprint 4 core features complete (Test Editing & Versioning)
- ✅ Test editing feature ~95% complete (current status)
- ✅ All 4 frontend components integrated

---

## 📋 Implementation Phases

### **Week 1 (Week 11): Foundation & Adapter Pattern**

**Day 1-2: Configuration Setting (Phase 1)**
- Database schema: Add `users.stagehand_provider VARCHAR(20) DEFAULT 'python'`
- Backend API: `PUT /api/v1/settings/stagehand-provider` endpoint
- Basic settings page structure
- **Deliverables:**
  - Migration: `add_stagehand_provider_setting.py`
  - API endpoint: `settings.py` (new router)
  - Frontend: Basic `SettingsPage.tsx` skeleton

**Day 2-3: Adapter Pattern (Phase 2)**
- Create abstract base class: `StagehandAdapter`
- Implement Python adapter (wraps existing code, zero changes)
- Implement TypeScript adapter (HTTP client placeholder)
- **Deliverables:**
  - `backend/app/services/stagehand_adapter.py` (abstract base, ~80 lines)
  - `backend/app/services/python_stagehand_adapter.py` (wrapper, ~150 lines)
  - `backend/app/services/typescript_stagehand_adapter.py` (HTTP client, ~200 lines)
  - Unit tests for adapters

**Day 3-4: Factory Pattern (Phase 3)**
- Create factory to select adapter based on user preference
- Update all Stagehand usage to use factory
- Add error handling for provider selection
- **Deliverables:**
  - `backend/app/services/stagehand_factory.py` (~100 lines)
  - Update `TestExecutionService` to use factory
  - Update `DebugSessionService` to use factory

**Day 4-5: Node.js Microservice Setup (Phase 4 start)**
- Setup Node.js + TypeScript project structure
- Install @browserbasehq/stagehand + dependencies
- Begin Express server implementation
- **Deliverables:**
  - `stagehand-typescript-service/package.json`
  - Project structure initialized

---

### **Week 2 (Week 12): Node.js Service & Frontend**

**Day 1-3: Node.js Microservice Implementation (Phase 4 continue)**
- Implement Express server with session management
- Create API endpoints matching Python functionality
- Add error handling and logging
- Add health check endpoint
- **Deliverables:**
  - `stagehand-typescript-service/src/server.ts` (~300 lines)
  - `stagehand-typescript-service/src/session-manager.ts` (~150 lines)
  - API endpoints: /init, /execute, /screenshot, /cleanup, /debug
  - Dockerfile for containerization

**Day 3-4: Frontend Settings UI (Phase 5)**
- Complete Settings page with radio button selection
- Add comparison table (features, performance, status)
- Integrate with backend API
- **Deliverables:**
  - `frontend/src/pages/SettingsPage.tsx` (~250 lines)
  - Settings page route in router
  - Navigation menu item for settings

**Day 4-5: Integration Testing (Phase 6 start)**
- Integration testing (both providers)
- Performance benchmarking
- Error handling validation
- **Deliverables:**
  - Integration test suite
  - Performance comparison data

---

### **Week 3 (Week 13): Testing & Documentation**

**Day 1-2: Complete Testing (Phase 6 continue)**
- Cross-provider comparison testing
- Session management validation
- Performance optimization
- **Deliverables:**
  - Complete test suite
  - Performance benchmarks

**Day 2-3: Documentation (Phase 6)**
- User documentation (setup, switching providers)
- Developer documentation (architecture, extending)
- Video demo (optional)
- **Deliverables:**
  - `DUAL-STAGEHAND-PROVIDER-SETUP.md`
  - `STAGEHAND-PROVIDER-COMPARISON.md`
  - `STAGEHAND-ARCHITECTURE.md`

**Day 3-4: Final Integration**
- Fix any reported issues
- Performance tuning
- UI/UX improvements
- **Deliverables:**
  - Bug fixes
  - Performance optimizations

**Day 4-5: Production Readiness**
- Docker containerization
- Deployment scripts
- Production testing
- **Deliverables:**
  - Docker setup
  - Deployment documentation

---

### **Week 4 (Week 14): Final Testing & Demo**

**Day 1-2: End-to-End Validation**
- Complete workflow testing
- Performance comparison data collection
- User acceptance testing
- **Deliverables:**
  - E2E test results
  - Performance comparison report

**Day 2-3: Finalize Documentation**
- Complete all documentation
- Create comparison report
- Prepare demo
- **Deliverables:**
  - Final documentation
  - Comparison report

**Day 3-4: Code Review & Merge**
- Code review and refactoring
- Security review
- Final bug fixes
- **Deliverables:**
  - Code review complete
  - Ready for merge

**Day 4-5: Sprint Review**
- Demo Dual Stagehand Provider System
- Collect feedback
- Phase 2 completion celebration 🎉
- **Deliverables:**
  - Demo presentation
  - Feedback collection

---

## 🏗️ Architecture Overview

```
Backend (FastAPI)
├── Adapter Pattern (Abstract Base Class)
│   ├── PythonStagehandAdapter (wraps existing code)
│   └── TypeScriptStagehandAdapter (HTTP client to Node.js)
├── Factory Pattern (selects provider based on user setting)
└── User Setting: stagehand_provider ('python' | 'typescript')

Node.js Microservice (Port 3001)
├── Express server wrapping @browserbasehq/stagehand
├── Session management (UUID-based)
└── API endpoints: /init, /execute, /screenshot, /cleanup, /debug

Frontend
└── Settings Page: Radio button selection with comparison table
```

---

## ✅ Success Criteria

- ✅ Both Python and TypeScript Stagehand work independently
- ✅ User can switch providers via settings page
- ✅ Zero breaking changes to existing Python implementation
- ✅ Session management handles concurrent executions
- ✅ Error handling gracefully falls back or reports issues
- ✅ Documentation enables smooth setup and switching
- ✅ Performance comparison data collected

---

## ⚠️ Impact on Other Features

**Developer A Reassignment:**
- **Sprint 5 (Week 11-12):** Pattern Recognition feature deferred to Phase 3 or handled by Developer B
- **Sprint 6 (Week 13-14):** Learning Insights Dashboard deferred to Phase 3

**Developer B:**
- Continues with Sprint 5-6 features (KB Enhancement, Prompt A/B Testing)
- May take on Pattern Recognition if capacity allows

**Phase 2 Scope:**
- Phase 2 still completes on time (Week 14)
- Dual Stagehand Provider adds execution engine capability
- Learning features (Pattern Recognition, Dashboard) deferred but not critical for Phase 2 success

---

## 📊 Effort Estimate

**Total Time:** 92-136 hours (12-17 days)  
**With Buffer:** 3-4 weeks  
**Owner:** Developer A  
**Parallel Work:** Developer B continues Sprint 5-6 features

---

## 🚀 Next Steps

1. **Complete Sprint 4 Core Features** (Week 10)
   - Finish test editing E2E testing
   - Complete documentation
   - Code review and merge

2. **Start Sprint 4 Extension** (Week 11)
   - Begin Phase 1: Configuration Setting
   - Set up database migration
   - Create settings API endpoint

3. **Monitor Progress** (Week 11-14)
   - Daily standups to track progress
   - Weekly checkpoints
   - Adjust timeline if needed

---

**Status:** ⏳ **PLANNED** - Ready to start Week 11  
**Last Updated:** December 24, 2025

