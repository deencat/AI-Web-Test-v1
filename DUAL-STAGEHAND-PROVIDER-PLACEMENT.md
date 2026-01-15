# Dual Stagehand Provider System - Phase & Sprint Placement

**Date:** December 24, 2025  
**Feature:** Dual Stagehand Provider System (Python/TypeScript switching)  
**Status:** ⏳ Planned - Placement Decision Needed

---

## 🎯 Current Status

The **Dual Stagehand Provider System** is **NOT currently in the REVISED Phase 2 plan**. It was mentioned in the original project plan as a Sprint 4 extension task, but needs to be properly placed in the REVISED plan structure.

---

## 📍 Recommended Placement Options

### **Option A: Sprint 4 Extension (Week 11-14)** ⭐ RECOMMENDED IF TIME PERMITS

**Timeline:**
- Start: After Sprint 4 completes (Week 10)
- Duration: 3-4 weeks (92-136 hours)
- Completion: Week 14 (end of Phase 2)

**Pros:**
- ✅ Completes execution engine enhancement before Phase 3
- ✅ Provides data for Phase 3 decision-making
- ✅ Keeps Phase 2 focused on execution capabilities
- ✅ Can be done in parallel with Sprint 5-6 if Developer A has capacity

**Cons:**
- ⚠️ Extends Sprint 4 beyond original 2-week scope
- ⚠️ May delay Phase 2 completion if not managed carefully
- ⚠️ Requires 3-4 weeks of dedicated effort

**When to Choose:**
- If Sprint 4 completes early (by Week 10)
- If Developer A has capacity after test editing feature
- If execution engine comparison is high priority

---

### **Option B: Phase 3 Sprint 7-8 (Week 15-18)** ⭐ RECOMMENDED DEFAULT

**Timeline:**
- Start: Week 15 (Phase 3 Sprint 7)
- Duration: 3-4 weeks
- Completion: Week 18

**Pros:**
- ✅ Fits naturally with Phase 3 execution engine enhancements
- ✅ Doesn't delay Phase 2 completion
- ✅ Can leverage Phase 2 feedback data for comparison
- ✅ Part of broader execution engine improvements

**Cons:**
- ⚠️ Delays feature by 4-8 weeks
- ⚠️ May conflict with Observation Agent work in Sprint 7

**When to Choose:**
- If Sprint 4 takes full 2 weeks
- If Phase 2 needs to complete on time (Week 14)
- If execution engine enhancements are better grouped in Phase 3

---

## 🏗️ Feature Overview

**What It Does:**
- Enables users to switch between Python and TypeScript Stagehand implementations
- Runtime switching via settings page (no code changes needed)
- Side-by-side comparison of both implementations
- Data-driven decision making for future migration

**Architecture:**
```
Backend (FastAPI)
├── Adapter Pattern
│   ├── PythonStagehandAdapter (wraps existing)
│   └── TypeScriptStagehandAdapter (HTTP to Node.js)
├── Factory Pattern (selects based on user setting)
└── User Setting: stagehand_provider ('python' | 'typescript')

Node.js Microservice (Port 3001)
├── Express server
├── @browserbasehq/stagehand wrapper
└── Session management

Frontend
└── Settings Page: Provider selection UI
```

**Effort:** 92-136 hours (12-17 days, 3-4 weeks with buffer)

---

## 📊 Comparison: Option A vs Option B

| Factor | Option A (Sprint 4 Extension) | Option B (Phase 3) |
|--------|-------------------------------|-------------------|
| **Start Date** | Week 11 | Week 15 |
| **Completion** | Week 14 | Week 18 |
| **Phase 2 Impact** | Extends Phase 2 | No impact |
| **Phase 3 Impact** | None | Part of execution enhancements |
| **Priority** | High (if time permits) | Medium (can defer) |
| **Dependencies** | Sprint 4 complete | Phase 2 complete |
| **Team Capacity** | Developer A only | Can share with Phase 3 team |

---

## 💡 Recommendation

**Default Recommendation: Option B (Phase 3 Sprint 7-8)**

**Rationale:**
1. Phase 2 is focused on "Learning Foundations" - test editing, feedback, patterns
2. Dual Stagehand Provider is an execution engine enhancement, not a learning feature
3. Phase 3 already includes execution engine improvements (Observation Agent, etc.)
4. Keeps Phase 2 scope clean and on-time (6 weeks)
5. Can leverage Phase 2 feedback data for better comparison

**Exception: Option A if:**
- Sprint 4 completes early (by Week 10)
- Developer A has 3-4 weeks available
- Execution engine comparison is critical for Phase 3 planning
- Stakeholders prioritize this feature highly

---

## 📋 Implementation Phases (When Started)

**Phase 1: Configuration Setting** (1 day, 6-8 hours)
- Database schema: `users.stagehand_provider`
- Backend API: `PUT /api/v1/settings/stagehand-provider`
- Basic settings page

**Phase 2: Adapter Pattern** (2-3 days, 16-24 hours)
- Abstract base class: `StagehandAdapter`
- Python adapter (wrapper)
- TypeScript adapter (HTTP client)

**Phase 3: Factory Pattern** (1 day, 6-8 hours)
- Factory to select adapter
- Update all Stagehand usage
- Error handling

**Phase 4: Node.js Microservice** (5-7 days, 40-56 hours)
- Node.js + TypeScript setup
- Express server
- Session management
- API endpoints

**Phase 5: Frontend Settings UI** (1-2 days, 8-16 hours)
- Settings page with provider selection
- Comparison table
- Integration

**Phase 6: Testing & Documentation** (2-3 days, 16-24 hours)
- Integration testing
- Performance benchmarking
- Documentation

**Total: 92-136 hours (3-4 weeks)**

---

## ✅ Decision Framework

**Choose Option A (Sprint 4 Extension) if:**
- [ ] Sprint 4 completes by Week 10
- [ ] Developer A has 3-4 weeks available
- [ ] Feature is high priority for stakeholders
- [ ] Execution comparison needed before Phase 3

**Choose Option B (Phase 3) if:**
- [ ] Sprint 4 takes full 2 weeks
- [ ] Phase 2 must complete on time (Week 14)
- [ ] Feature can wait until Phase 3
- [ ] Execution engine enhancements better grouped together

---

## 📝 Updated Project Plan Status

**REVISED Plan Updated:**
- ✅ Added to "Scope: What's STILL OUT of Phase 2" (deferred)
- ✅ Added to Phase 3 scope (execution engine enhancements)
- ✅ Added Sprint 4 Extension section (optional)
- ✅ Added to Sprint 7 tasks (optional)

**Current Placement:** 
- **Primary:** Phase 3 Sprint 7-8 (Week 15-18)
- **Alternative:** Sprint 4 Extension (Week 11-14) if time permits

---

**Status:** ⏳ **AWAITING DECISION** - Choose Option A or B based on Sprint 4 completion timeline  
**Next Action:** Monitor Sprint 4 progress and decide by end of Week 10

