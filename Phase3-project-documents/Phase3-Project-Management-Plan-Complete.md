# Phase 3: Project Management Plan

**Document Type:** Project Management Guide  
**Purpose:** Comprehensive governance, team structure, sprint planning, budget, security, and risk management  
**Scope:** Sprint 7-12 execution framework (Jan 23 - Apr 15, 2026)  
**Status:** ✅ In Execution - Sprint 7 Complete (7A.4-7A.12 All Complete), Ready for Sprint 8  
**Last Updated:** January 29, 2026  
**Version:** 2.4

> **📖 When to Use This Document:**
> - **Sprint Planning:** Task assignments, story point estimates, dependencies
> - **Status Tracking:** Current progress, completed tasks, sprint goals
> - **Team Coordination:** Developer A vs Developer B task breakdown
> - **Budget & Timeline:** Cost analysis, schedule, resource allocation
> - **For Code Details:** See [Implementation Guide](Phase3-Implementation-Guide-Complete.md)
> - **For Architecture:** See [Architecture Document](Phase3-Architecture-Design-Complete.md)

---

## 🎯 Executive Summary at a Glance

| Aspect | Details |
|--------|---------|
| **Timeline** | 12 weeks (Jan 23 - Apr 15, 2026) |
| **Budget** | $160/month (Phase 3 MVP), $1,061/month (Phase 4 production scale) |
| **Team** | 2 developers (Developer A lead, Developer B support) |
| **Effort** | 354 story points total |
| **Start Date** | Developer A: TODAY (Jan 20), Developer B: Sprint 7 (Jan 23) |
| **Strategy** | MVP first with simplified infrastructure, scale in Phase 4 |
| **Key Innovation** | Zero infrastructure dependencies - reuse Phase 2 PostgreSQL + Redis |
| **Immediate Action** | Developer A starts 6 tasks TODAY (26 points, no blockers) |

---

## 📚 Related Documentation

This document is part of the Phase 3 documentation suite. For complete context, refer to:

- **[Phase3-Architecture-Design-Complete.md](Phase3-Architecture-Design-Complete.md)** - Technical architecture, agent design, system components
  - **Use for:** Understanding system design, agent patterns, architecture decisions
  - **Key sections:** Section 6 (Agent Design Patterns), Section 7 (Architecture Diagrams), Section 9 (Performance Scoring)
- **[Phase3-Implementation-Guide-Complete.md](Phase3-Implementation-Guide-Complete.md)** - Detailed implementation tasks, code templates, testing strategy
  - **Use for:** Code examples, sprint task details, implementation reference
  - **Key sections:** Section 2 (Sprint Tasks), Section 3 (Code Examples), Section 6 (Performance Scoring)
- **[Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md)** - Agent performance metrics and scoring methodology
  - **Use for:** Understanding how agents measure their own performance, quality validation methods
  - **Key sections:** Section 2-4 (Agent-specific scoring), Section 6 (Implementation roadmap)

**Document Usage Guide:**
- **Project Management Plan (This Document):** Sprint planning, task assignments, status tracking, budget
- **Architecture Document:** System design, agent specifications, technology choices
- **Implementation Guide:** Code templates, detailed task breakdowns, testing strategies

**Cross-References:**
- Task details: See Implementation Guide Section 2
- Agent design: See Architecture Document Section 6
- Code examples: See Implementation Guide Section 3
- Performance scoring: See [Performance Scoring Framework](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) document

**Supporting Documents:**
For detailed analysis, strategies, and agent-specific documentation, see the [Supporting Documents](#supporting-documents) section at the end of this document.

---

## 📋 Table of Contents

### 1. [Project Governance](#1-project-governance)
   - 1.1 [Executive Summary](#11-executive-summary)
   - 1.2 [Quick Start: What to Do RIGHT NOW](#12-quick-start-what-to-do-right-now)
   - 1.3 [Project Sponsor](#13-project-sponsor)
   - 1.4 [Project Manager / Technical Lead](#14-project-manager--technical-lead)
   - 1.5 [Steering Committee](#15-steering-committee)

### 2. [Team Structure & Roles](#2-team-structure--roles)
   - 2.1 [Developer A (Lead Developer)](#21-developer-a-lead-developer)
   - 2.2 [Developer B (Support Developer)](#22-developer-b-support-developer)
   - 2.3 [External Dependencies](#23-external-dependencies)
   - 2.4 [Sprint 7-12 Task Breakdown](#24-sprint-7-12-task-breakdown-developer-a-vs-developer-b)
      - Pre-Sprint 7: Developer A Early Start
      - Sprint 7: Integration with Real Infrastructure
      - Sprint 8: Analysis & Evolution Agents
      - Sprint 9: Orchestration & Reporting
      - Sprint 10: Phase 2 Integration & API
      - Sprint 11: Learning System Activation
      - Sprint 12: Security & Production Readiness

### 3. [Sprint Framework](#3-sprint-framework)
   - 3.1 [Sprint Cycle](#31-sprint-cycle-2-weeks-each)
   - 3.2 [Sprint Planning Agenda](#32-sprint-planning-agenda)
   - 3.3 [Daily Standup Format](#33-daily-standup-format)
   - 3.4 [Sprint Review (Demo)](#34-sprint-review-demo)
   - 3.5 [Sprint Retrospective](#35-sprint-retrospective)

### 4. [Budget & Cost Analysis](#4-budget--cost-analysis)
   - 4.1 [Infrastructure Costs](#41-infrastructure-costs-monthly)
   - 4.2 [LLM API Costs](#42-llm-api-costs-monthly)
   - 4.3 [Learning System Costs](#43-learning-system-costs)
   - 4.4 [Total Monthly Budget](#44-total-monthly-budget)
   - 4.5 [Cost Optimization Strategies](#45-cost-optimization-strategies)
   - 4.6 [Scaling Projections](#46-scaling-projections)
   - 4.7 [ROI Justification](#47-roi-justification)

### 5. [Security Design](#5-security-design)
   - 5.1 [Security Layers](#51-security-layers)
   - 5.2 [Authentication](#52-authentication)
   - 5.3 [Authorization (RBAC)](#53-authorization-rbac)
   - 5.4 [Network Security (TLS 1.3)](#54-network-security-tls-13)
   - 5.5 [Audit Logging](#55-audit-logging)
   - 5.6 [Secrets Management](#56-secrets-management)
   - 5.7 [Security Audit Checklist](#57-security-audit-checklist)

### 6. [Risk Management](#6-risk-management)
   - 6.1 [Risk Register](#61-risk-register)
   - 6.2 [Risk Mitigation Plans](#62-risk-mitigation-plans)
   - 6.3 [Issue Escalation Matrix](#63-issue-escalation-matrix)

### 7. [Stakeholder Communication](#7-stakeholder-communication)
   - 7.1 [Weekly Status Report](#71-weekly-status-report-email)
   - 7.2 [Sprint Review (Demo)](#72-sprint-review-demo)
   - 7.3 [Monthly Executive Summary](#73-monthly-executive-summary)

---

## 1. Project Governance

### 1.1 Executive Summary

**Project:** Multi-Agent Test Generation System (Phase 3)  
**Budget:** $160/month operational costs (simplified infrastructure)  
**Timeline:** 12 weeks (Jan 23 - Apr 15, 2026)  
**Team Size:** 2 developers (Developer A lead, Developer B support)  
**Total Effort:** 354 story points  
**Target Launch:** April 15, 2026

**Phase 3 Strategy: MVP First, Scale Later**
- Use existing Phase 2 infrastructure (PostgreSQL, Redis)
- No Kubernetes/complex deployment (Docker Compose or direct Python)
- No DevOps dependencies (removes 2-3 week blocker)
- Defer production infrastructure to Phase 4 (when we have >50 users)

**Current Status (Updated Jan 29, 2026):**
- ✅ Developer A: **Sprint 7 work COMPLETE** - All 9 tasks done (7A.4-7A.12, 46 story points)
  - ✅ **Pre-Sprint 7 work COMPLETE** - All 6 tasks done (EA.1-EA.6, 26 story points)
    - ✅ BaseAgent abstract class complete (446 lines)
    - ✅ Message bus stub complete (315 lines)
    - ✅ Agent registry stub complete (377 lines)
    - ✅ **ObservationAgent complete with Azure OpenAI integration** (641 lines)
      - Successfully tested with Three HK website
      - 262 elements detected (259 Playwright + 3 LLM-enhanced)
      - Multi-tier caching strategy implemented
    - ✅ **RequirementsAgent complete** (800+ lines)
      - E2E Tested: Three HK (261 elements → 18 scenarios, conf: 0.90, 20.9s)
      - Industry best practices: BDD, WCAG 2.1, OWASP, ISTQB
    - ✅ Unit tests complete (55/55 passing - 100% coverage)
  - ✅ **AnalysisAgent complete** (1,200+ lines)
    - FMEA risk scoring (RPN calculation) with RiskScore class
    - LLM integration with Azure OpenAI (GPT-4o) for structured risk analysis
    - Historical data integration (uses existing Phase 2 database)
    - ROI calculation and execution time estimation
    - Dependency analysis with topological sort (cycle detection, parallel groups)
    - Business value scoring (revenue, user impact, compliance)
    - Coverage impact analysis and regression risk assessment
    - Real-time test execution integration (3-tier strategy: Playwright → observe+XPath → Stagehand AI)
    - Adaptive scoring based on execution success rates (Detection score adjustment)
    - Unit tests complete (44/44 passing)
    - Integration tests complete (13/13 passing, including E2E with real Three HK page)
    - Browser visibility control via HEADLESS_BROWSER env var
- 🔄 Developer B: Completing Phase 2 work, joins Phase 3 in Sprint 8 (Feb 6)
- 🚀 **Sprint 8 ready to start** - EvolutionAgent implementation (52 points)

**Success Criteria:**
- ✅ All 6 agents deployed and operational
- ✅ 95%+ code coverage achieved
- ✅ <$0.20 per test cycle cost (simplified infrastructure)
- ✅ 85%+ test generation accuracy
- ✅ Learning system operational with 10+ patterns by Sprint 12
- ✅ Ready to scale to Phase 4 when proven

---

### 1.2 Quick Start: What to Do RIGHT NOW

**✅ Pre-Sprint 7 Work COMPLETE (Jan 20-27):**
- ✅ All 6 pre-sprint tasks done (EA.1-EA.6, 26 story points)
- ✅ BaseAgent, ObservationAgent, RequirementsAgent operational
- ✅ 55/55 unit tests passing (100% coverage)

**👨‍💻 Developer A (Sprint 8 - Starting Now - INDEPENDENT WORK):**
1. **EvolutionAgent Implementation (Recommended):** Start EvolutionAgent implementation
   - Task 8A.5: Implement EvolutionAgent class (BDD → Test steps, database storage)
   - Task 8A.6: LLM integration (OpenAI API client)
   - Task 8A.7: Prompt engineering (3 variants for A/B testing)
   - Task 8A.9: Database integration (store test cases, link to frontend)
   - Task 8A.10: Feedback loop (execution results → RequirementsAgent improvement)
   
   **Key Focus:** EvolutionAgent generates test steps (not just Playwright files), stores in database, visible in frontend. Execution results feed back to RequirementsAgent for continuous improvement.
   - Task 8A.8: Caching layer (30% cost reduction)
2. **Integration Tests:** Complete 4-agent workflow tests
   - Task 8A.4: Integration tests (4-agent workflow: Observe → Requirements → Analyze → Evolve)

**👨‍💻 Developer B (Sprint 8 - Still on Phase 2):**
- Currently completing Phase 2 enhancements
- Will join Phase 3 when Phase 2 is complete
- **Developer A can proceed independently without waiting**

**📊 Sprint 7 Goals (COMPLETE):**
- ✅ AnalysisAgent implementation complete (FMEA risk scoring, ROI, dependencies)
- ✅ Real-time test execution integration (3-tier strategy from Phase 2)
- ✅ E2E testing with real page execution (Three HK 5G Broadband page tested)
- ✅ Use existing database (SQLite for local dev, PostgreSQL in production - no changes needed)
- ✅ Integration test: ObservationAgent → RequirementsAgent → AnalysisAgent workflow end-to-end
- ✅ 99+ unit tests passing (55 from pre-sprint + 44 new for AnalysisAgent)
- ✅ 13 integration tests passing (including real page E2E workflow)
- ✅ Browser visibility control implemented (HEADLESS_BROWSER env var)

---

### 1.3 Project Sponsor

**Name:** CTO  
**Role:** Final decision authority, budget approval, strategic direction  
**Availability:** Weekly status reviews (30 minutes, Fridays 3:00 PM)

**Responsibilities:**
- Approve budget and resource allocation
- Remove organizational blockers
- Final decision on scope changes
- Strategic alignment with company goals

---

### 1.4 Project Manager / Technical Lead

**Name:** Developer A  
**Responsibilities:**
- Sprint planning and execution (bi-weekly cycles)
- Risk management and mitigation (weekly reviews)
- Stakeholder communication (weekly status reports)
- Technical architecture decisions (ADR documentation)
- Code review and quality assurance (daily)
- Budget tracking (monthly burn rate analysis)
- Learning system implementation oversight

**Backup:** Developer B (if Developer A unavailable)

---

### 1.5 Steering Committee

**Members:**
- CTO (Sponsor)
- VP Engineering
- Developer A (Project Manager)
- Developer B (Technical Contributor)

**Meeting Frequency:** Bi-weekly (Sprint reviews, Fridays 2:00 PM)  
**Duration:** 1 hour  
**Purpose:** Progress review, roadblock escalation, scope changes, risk assessment

**Agenda Template:**
1. Sprint accomplishments (15 min)
2. Demo of new features (20 min)
3. Risks and issues (15 min)
4. Budget status (5 min)
5. Next sprint preview (5 min)

---

## 2. Team Structure & Roles

### 2.1 Developer A (Lead Developer)

**Primary Responsibilities:**
- ✅ **Pre-Sprint 7: BaseAgent, ObservationAgent, RequirementsAgent (COMPLETE)**
- ✅ **AnalysisAgent (Sprint 7) - COMPLETE** - FMEA risk scoring, real-time execution, E2E testing
- Infrastructure integration (Sprint 8-9) - Replace stubs with real Redis/PostgreSQL (when Developer B ready)
- Evolution Agent (Sprint 8-9)
- Orchestration Agent (Sprint 10)
- Enterprise features (Sprint 12)
- Critical path ownership (4/6 sprints)
- Learning system foundation (Sprint 7)

**✅ Pre-Sprint 7 Tasks (COMPLETE):**
- ✅ EA.1: BaseAgent abstract class (8 pts) - See [Section 2.4 Pre-Sprint 7](#pre-sprint-7-developer-a-early-start-jan-20-23-while-developer-b-on-phase-2) for details
- ✅ EA.2: MessageBus interface stub (5 pts)
- ✅ EA.3: AgentRegistry in-memory (3 pts)
- ✅ EA.4: ObservationAgent implementation (5 pts)
- ✅ EA.5: RequirementsAgent implementation (5 pts)
- ✅ EA.6: Unit tests (55/55 passing)
- **Total: 26 points completed** - See [Implementation Guide Section 3.4](Phase3-Implementation-Guide-Complete.md#34-requirements-agent-test-scenario-extraction) for RequirementsAgent code

**✅ Sprint 7 Tasks (COMPLETE - Jan 23-29, 2026):**
- ✅ 7A.4: AnalysisAgent class with FMEA risk scoring (13 pts) - RiskScore class, RPN calculation
- ✅ 7A.5: LLM integration for structured risk analysis (8 pts) - Azure OpenAI GPT-4o integration
- ✅ 7A.6: Historical data integration (5 pts) - Uses existing Phase 2 database
- ✅ 7A.7: ROI calculation and execution time estimation (5 pts)
- ✅ 7A.8: Dependency analysis with topological sort (5 pts) - Cycle detection, parallel groups
- ✅ 7A.9: Business value scoring (3 pts) - Revenue, user impact, compliance
- ✅ 7A.10: Coverage impact analysis and regression risk assessment (5 pts)
- ✅ 7A.11: Unit tests for AnalysisAgent (3 pts) - 44/44 passing
- ✅ 7A.12: Integration tests (5 pts) - 13/13 passing, including E2E with real Three HK page
- **Total: 46 points completed** - See [Implementation Guide Section 3.3](Phase3-Implementation-Guide-Complete.md#33-analysisagent-implementation-enhanced---fmea-based-risk-analysis) for AnalysisAgent code

**✅ Sprint 7 Enhancements (COMPLETE):**
- ✅ Real-time test execution integration (3-tier strategy: Playwright → observe+XPath → Stagehand AI)
- ✅ Adaptive scoring based on execution success rates (Detection score adjustment)
- ✅ E2E testing with real page execution (Three HK 5G Broadband page)
- ✅ Browser visibility control (HEADLESS_BROWSER env var)

**Time Allocation:**
- Development: 70% (28 hours/week)
- Code review: 15% (6 hours/week)
- Documentation: 10% (4 hours/week)
- Meetings: 5% (2 hours/week)

**Skills Required:**
- Python 3.11+ (async/await, type hints)
- Redis Streams (exactly-once delivery)
- LangGraph (multi-agent orchestration)
- Docker/Kubernetes (containerization, deployment)
- OpenAI API (LLM integration)

### 2.2 Developer B (Support Developer)

**Primary Responsibilities:**
- Currently: Completing Phase 2 enhancements
- ✅ **ObservationAgent and RequirementsAgent already implemented by Developer A**
- ✅ **AnalysisAgent implementation details prepared by Developer A** - Developer A will implement independently
- Infrastructure setup (Sprint 7) - PostgreSQL tables, Redis pub/sub, memory system (when Phase 2 complete)
- Reporting Agent (Sprint 10)
- CI/CD integration (Sprint 11)
- Testing and quality assurance (all sprints)
- Learning system data collection (Sprint 7-12)

**Time Allocation:**
- Development: 75% (30 hours/week)
- Testing: 15% (6 hours/week)
- Documentation: 5% (2 hours/week)
- Meetings: 5% (2 hours/week)

**Skills Required:**
- Python 3.11+ (testing, pytest)
- PostgreSQL (database design, queries)
- GitHub Actions (CI/CD pipelines)
- Locust (load testing)
- Grafana (monitoring dashboards)

### 2.3 External Dependencies

**Phase 3 (MVP - Simple Infrastructure):**
- **NONE** - Use existing Phase 2 infrastructure
- **Database: Use existing database as-is** (SQLite for local dev, PostgreSQL in production - no schema changes needed)
- **Redis: Simple pub/sub** (optional in Sprint 7, can use stub if not installed)
- **PostgreSQL optimizations: Deferred to Sprint 10+** (when Developer B ready or when we need scale)
- Deployment: Docker Compose locally or direct Python processes
- Monitoring: Python logging + basic metrics endpoint

**Phase 4 (Production-Ready - Complex Infrastructure):**
- Kubernetes cluster for auto-scaling (when we have >100 users)
- Redis Streams upgrade (when we need >1000 messages/sec)
- Prometheus/Grafana monitoring stack (when we need dashboards)
- Load balancers and HA setup (when we need 99.9% uptime)

**Rationale:** Phase 3 focuses on **agent functionality**, not infrastructure. Use simplest tools that work, defer complexity to Phase 4 when we have proven value and need scale.

---

## 2.4 Sprint 7-12 Task Breakdown (Developer A vs Developer B)

### Pre-Sprint 7: Developer A Early Start (Jan 20-23, WHILE Developer B on Phase 2)

**Developer A can start TODAY without waiting for Developer B:**

| Task | Status | Description | Duration | Deliverable |
|------|--------|-------------|----------|-------------|
| **EA.1** | ✅ | Create `backend/agents/base_agent.py` | 3 days | BaseAgent abstract class (200+ lines) |
| **EA.2** | ✅ | Create `backend/messaging/message_bus_stub.py` | 2 days | In-memory message bus stub (80+ lines) |
| **EA.3** | ✅ | Create `backend/agents/agent_registry_stub.py` | 1 day | In-memory agent registry (60+ lines) |
| **EA.4** | ✅ | Create `backend/agents/observation_agent.py` with **Azure OpenAI LLM** | 2 days | ObservationAgent with Playwright + Azure GPT-4o (250+ lines) - Tested with Three HK website ✅ |
| **EA.5** | ✅ | Create `backend/agents/requirements_agent.py` following **industry best practices** (BDD, WCAG 2.1, OWASP, ISTQB) | 2 days | RequirementsAgent: 800+ lines with Azure GPT-4o LLM integration - **E2E Tested:** Three HK (261 elements → 18 scenarios, conf: 0.90, 20.9s) ✅ |
| **EA.6** | ✅ | Write unit tests (`tests/agents/`) | 1 day | 55/55 unit tests passing (100% coverage) ✅ |

**Total: 11 days, 26 story points, ZERO dependencies on Developer B or Phase 2**

**Key Design:**
- Use **stub implementations** for Redis/PostgreSQL (in-memory, no external dependencies)
- Agents work with stubs, can be swapped for real infrastructure later (dependency injection)
- All code runs on Developer A's laptop with `pytest` (no Docker/Redis/PostgreSQL needed)

**RequirementsAgent Specification (EA.5):**
- **Industry Standards:** BDD (Gherkin Given/When/Then), WCAG 2.1 (accessibility), OWASP Top 10 (security), ISTQB (test design), ISO 29119 (testing standard)
- **Input:** UI elements from ObservationAgent (262+ elements)
- **Processing Pipeline:**
  1. Element grouping by page/component (Page Object Model)
  2. User journey mapping (login flow, checkout flow, etc.)
  3. Functional scenario generation (LLM + pattern-based)
  4. Accessibility scenario generation (keyboard nav, screen reader, contrast)
  5. Security scenario generation (XSS, SQL injection, CSRF, input validation)
  6. Edge case scenario generation (boundary value analysis, negative tests)
  7. Test data extraction with validation rules
  8. Coverage metrics calculation
- **Output:** 18 test scenarios per page (functional: 3, accessibility: 8, security: 4, edge cases: 3) with Given/When/Then format, priority (critical/high/medium/low), confidence scores (0.90), test data patterns
- **LLM Integration:** Azure GPT-4o for complex scenario generation (~12,500 tokens), pattern-based fallback for reliability
- **E2E Verified:** Three HK website (261 UI elements → 18 BDD scenarios in 20.9s, confidence: 0.90) ✅
- **Quality Metrics:** 100% UI coverage, 0.85+ confidence, traceability to UI elements
- **Performance Scoring:** See [Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) for detailed scoring methodology (selector accuracy, detection completeness, classification accuracy, LLM enhancement)

**Status Update (Jan 27, 2026):** ✅ **ALL Pre-Sprint 7 tasks COMPLETE** (EA.1-EA.6, 26 points). ObservationAgent and RequirementsAgent fully implemented and tested. Ready for Sprint 7 infrastructure integration. See [Implementation Guide Section 3.4](Phase3-Implementation-Guide-Complete.md#34-requirements-agent-test-scenario-extraction) for RequirementsAgent implementation details.

---

### Sprint 7: AnalysisAgent Implementation (Independent - Jan 23 - Feb 5, 2026) ✅ **COMPLETE**

**Status:** All Sprint 7 tasks completed (Jan 23-29, 2026) - 46 story points delivered

**Developer A works independently while Developer B completes Phase 2:**

#### Developer A Tasks (46 points - INDEPENDENT, NO DEPENDENCIES ON DEVELOPER B)

**Option 1: AnalysisAgent Implementation (Recommended - Can Start Immediately)**

| Task | Description | Duration | Dependencies | Points |
|------|-------------|----------|--------------|--------|
| **7A.4** | ✅ Implement AnalysisAgent class with FMEA risk scoring (RPN calculation) | 5 days | Pre-Sprint 7 (EA.1-EA.6) | 13 | **COMPLETE** |
| **7A.5** | ✅ LLM integration for structured risk analysis (severity/occurrence/detection) | 3 days | 7A.4 | 8 | **COMPLETE** |
| **7A.6** | ✅ Historical data integration (use existing database - SQLite/PostgreSQL) | 2 days | 7A.4 | 5 | **COMPLETE** |
| **7A.7** | ✅ ROI calculation and execution time estimation | 2 days | 7A.5 | 5 | **COMPLETE** |
| **7A.8** | ✅ Dependency analysis with topological sort (cycle detection) | 2 days | 7A.4 | 5 | **COMPLETE** |
| **7A.9** | ✅ Business value scoring (revenue, users, compliance) | 1 day | 7A.5 | 3 | **COMPLETE** |
| **7A.10** | ✅ Coverage impact analysis and regression risk assessment | 2 days | 7A.5 | 5 | **COMPLETE** |
| **7A.11** | ✅ Unit tests for AnalysisAgent (44 tests, LLM mocking) | 1 day | 7A.7, 7A.8 | 3 | **COMPLETE** |
| **7A.12** | ✅ Integration tests (3-agent workflow: Observe → Requirements → Analyze) | 2 days | 7A.11 | 5 | **COMPLETE** |

**Total: 46 points, 13 days - ZERO dependencies on Developer B or Phase 2**

**Option 2: Simple Redis Pub/Sub Setup (Optional - If Developer A Has Time)**

| Task | Description | Duration | Dependencies | Points |
|------|-------------|----------|--------------|--------|
| **7A.13** | Install Redis locally (or use Docker) | 0.5 day | None | 1 |
| **7A.14** | Replace message bus stub with simple Redis pub/sub | 1 day | 7A.13 | 2 |
| **7A.15** | Replace agent registry stub with Redis-backed version | 1 day | 7A.14 | 2 |
| **7A.16** | Integration tests (agents + real Redis) | 0.5 day | 7A.15 | 1 |

**Total: 6 points, 3 days - OPTIONAL, SIMPLE SETUP**

**Note:** Redis pub/sub is simple (just `publish`/`subscribe` commands). No need for Redis Streams or complex setup. Can use existing database (SQLite for local dev) - no PostgreSQL changes needed until later.

#### Developer B Tasks (When Phase 2 Complete - DEFERRED TO LATER SPRINT)

**PostgreSQL Setup Deferred:** No need to add agent tables now. Use existing database (SQLite for local dev, PostgreSQL in production) as-is. PostgreSQL-specific optimizations can be added later when needed.

| Task | Description | Duration | Dependencies | Points | Sprint |
|------|-------------|----------|--------------|--------|--------|
| **7B.1** | Add agent-related tables to existing database (PostgreSQL) | 2 days | Phase 2 DB | 5 | Sprint 10+ |
| **7B.2** | Implement three-layer memory system (working memory + database) | 3 days | 7B.1 | 5 | Sprint 10+ |
| **7B.3** | Add 8 learning system tables to database | 1 day | 7B.1 | 3 | Sprint 10+ |
| **7B.4** | Implement FeedbackCollector class | 2 days | 7B.3 | 3 | Sprint 10+ |
| **7B.5** | Unit tests for infrastructure (30+ tests) | 1 day | 7B.1-7B.4 | 3 | Sprint 10+ |

**Total: 19 points, 6 days - DEFERRED TO SPRINT 10+ (When Developer B Ready)**

**Rationale:** 
- Use existing database (SQLite/PostgreSQL) as-is - no schema changes needed for AnalysisAgent
- Historical data queries work with existing `test_executions` table
- PostgreSQL optimizations can wait until we need scale or Developer B is available
- Focus on agent functionality first, infrastructure later

**Sprint 7 Success Criteria (Developer A Independent Path) - ✅ ALL COMPLETE:**
- ✅ AnalysisAgent class implemented with FMEA risk scoring (RPN calculation) - **COMPLETE**
- ✅ LLM integration with Azure GPT-4o operational (structured risk analysis output) - **COMPLETE**
- ✅ AnalysisAgent calculates ROI for each scenario (explicit formula with effort estimation) - **COMPLETE**
- ✅ AnalysisAgent estimates execution times (heuristics-based, categorized as fast/medium/slow) - **COMPLETE**
- ✅ AnalysisAgent performs dependency analysis (topological sort, cycle detection, parallel groups) - **COMPLETE**
- ✅ AnalysisAgent calculates business value (revenue impact, user impact, compliance) - **COMPLETE**
- ✅ AnalysisAgent uses existing database (SQLite/PostgreSQL) for historical data queries - **COMPLETE**
- ✅ Real-time test execution integration (3-tier strategy: Playwright → observe+XPath → Stagehand AI) - **COMPLETE**
- ✅ Adaptive scoring based on execution success rates (Detection score adjustment) - **COMPLETE**
- ✅ 3-agent workflow operational: Observe → Requirements → Analyze (using stubs) - **COMPLETE**
- ✅ 99+ unit tests passing (55 from pre-sprint + 44 new for AnalysisAgent) - **COMPLETE**
- ✅ 13 integration tests passing (including E2E with real Three HK page) - **COMPLETE**
- ✅ Browser visibility control (HEADLESS_BROWSER env var) - **COMPLETE**
- ✅ E2E testing with real page execution (Three HK 5G Broadband page) - **COMPLETE**

**Note:** 
- AnalysisAgent implementation details are already prepared and documented in [Implementation Guide Section 3.3](Phase3-Implementation-Guide-Complete.md#33-analysisagent-implementation-enhanced---fmea-based-risk-analysis)
- Developer A can start immediately using stub infrastructure (message bus stub, agent registry stub)
- **Use existing database as-is** (SQLite for local dev, PostgreSQL in production) - no schema changes needed
- Historical data queries work with existing `test_executions` table
- **Redis pub/sub is optional** - can be added in Sprint 7 if Developer A has time (simple setup), or deferred to later
- **PostgreSQL optimizations deferred** to Sprint 10+ when Developer B is ready or when we need scale

---

### Sprint 8: AnalysisAgent Enhancement & EvolutionAgent Start (Feb 6 - Feb 19, 2026)

**Developer A continues independently, Developer B may join if Phase 2 complete:**

#### Developer A Tasks (52 points - CONTINUES FROM SPRINT 7)

**AnalysisAgent Enhancement (✅ COMPLETE from Sprint 7):**

| Task | Description | Duration | Dependencies | Points | Status |
|------|-------------|----------|--------------|--------|--------|
| **8A.1** | ✅ Real-time test execution integration (Phase 2 execution engine) | 3 days | Sprint 7 (7A.4-7A.12) | 8 | **COMPLETE** |
| **8A.2** | ✅ Execution success rate analysis and Detection score adjustment | 2 days | 8A.1 | 5 | **COMPLETE** |
| **8A.3** | ✅ Final prioritization algorithm enhancement (with execution success) | 2 days | 8A.2 | 5 | **COMPLETE** |
| **8A.4** | Integration tests (4-agent workflow: Observe → Requirements → Analyze → Evolve) | 2 days | 8A.3 | 5 | **PENDING** (needs EvolutionAgent) |

**EvolutionAgent Start (New Agent - Test Code Generator):**

**Note:** EvolutionAgent is a **test code generator** that converts BDD scenarios (Given/When/Then) into executable test steps and stores them in the database. Test cases are visible in the frontend and executable via "Run Test" button. Execution results feed back to RequirementsAgent to improve future scenario generation, creating a continuous improvement feedback loop. The **Learning System** (Sprint 11, Section 8 of Architecture document) coordinates learning across all agents at a meta-level.

**Continuous Improvement Feedback Loop:**
- EvolutionAgent generates test steps → Stores in database → Visible in frontend
- Tests executed via Phase 2 engine → Results collected
- Execution results analyzed → Success/failure patterns identified
- Feedback provided to RequirementsAgent → Improves next scenario generation
- **Result:** Agents collaborate for continuous improvement, not standalone

| Task | Description | Duration | Dependencies | Points |
|------|-------------|----------|--------------|--------|
| **8A.5** | Implement EvolutionAgent class (BDD → Test steps, database storage) | 5 days | Sprint 7 | 13 |
| **8A.6** | LLM integration (OpenAI API client) | 2 days | 8A.5 | 8 |
| **8A.7** | Prompt engineering (3 variants for A/B testing) | 2 days | 8A.6 | 3 |
| **8A.8** | Caching layer (30% cost reduction) | 1 day | 8A.6 | 3 |
| **8A.9** | Database integration (store test cases, link to frontend) | 2 days | 8A.5 | 5 |
| **8A.10** | Feedback loop implementation (execution results → RequirementsAgent) | 2 days | 8A.9 | 5 |

**Total: 52 points, 13 days**

#### Developer B Tasks (When Phase 2 Complete - Optional)

| Task | Description | Duration | Dependencies | Points |
|------|-------------|----------|--------------|--------|
| **8B.1** | Infrastructure integration (if not done in Sprint 7) | 3 days | Phase 2 complete | 8 |
| **8B.2** | Collect 100+ user feedback samples (manual) | Continuous | Sprint 7 | 3 |
| **8B.3** | Unit tests for infrastructure (if needed) | 1 day | 8B.1 | 3 |

**Total: 14 points (optional, depends on Phase 2 completion)**

**Sprint 8 Success Criteria:**
- ✅ AnalysisAgent enhanced with real-time test execution (Phase 2 engine integration) - **COMPLETE (Sprint 7)**
- ✅ AnalysisAgent refines scores based on actual execution results - **COMPLETE (Sprint 7)**
- 🔄 EvolutionAgent generates test steps and stores in database (10+ test cases) - **IN PROGRESS**
- 🔄 Test cases visible in frontend, executable via "Run Test" button - **IN PROGRESS**
- 🔄 Feedback loop operational: Execution results → RequirementsAgent improvement - **IN PROGRESS**
- 🔄 4-agent workflow operational: Observe → Requirements → Analyze → Evolve - **PENDING (needs EvolutionAgent)**
- 🔄 LLM costs <$0.20 per test cycle (with caching) - **IN PROGRESS**
- 🔄 100+ feedback samples collected for learning system (if Developer B available) - **PENDING**

---

### Sprint 9: EvolutionAgent Completion & Infrastructure Integration (Feb 20 - Mar 5, 2026)

**Goal:** Complete EvolutionAgent (test code generator: BDD → Test steps, database storage) and integrate AnalysisAgent with real infrastructure (when Developer B ready)

**Note:** EvolutionAgent generates executable test steps from BDD scenarios and stores them in the database. Test cases are visible in the frontend and executable via "Run Test" button. Execution results feed back to RequirementsAgent to improve future scenario generation, creating a continuous improvement feedback loop. The Learning System (Sprint 11) coordinates learning across all agents at a meta-level.

**Story Points:** 30 (12 days duration)

#### Developer A Tasks (30 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 9A.1 | Complete EvolutionAgent implementation (from Sprint 8) | Sprint 8 (8A.5-8A.8) | 5 | 2 days | 0 (START) |
| 9A.2 | LLM integration with Cerebras (test code generation) | 9A.1 | 8 | 3 days | 2 |
| 9A.3 | Test generation prompt templates (Playwright/Stagehand, 3 variants) | 9A.2 | 5 | 2 days | 5 |
| 9A.4 | Caching layer with pattern storage (90% cost reduction after Sprint 10) | 9A.3 | 3 | 1 day | 7 |
| 9A.5 | Unit tests for EvolutionAgent (30+ tests, LLM mocking) | 9A.4 | 1 | 1 day | 8 |
| 9A.6 | Integration tests (4-agent coordination: Observe → Requirements → Analyze → Evolve) | 9A.5, Sprint 8 (8A.4) | 5 | 2 days | 9 |
| 9A.7 | Replace AnalysisAgent stubs with real infrastructure (when Developer B ready) | 9B.1 (optional) | 3 | 1 day | 10 |

**Total: 30 points, 12 days**

#### Developer B Tasks (When Phase 2 Complete - Optional)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 9B.1 | Complete infrastructure setup (if not done in Sprint 7-8) | Phase 2 complete | 8 | 3 days |
| 9B.2 | Replace AnalysisAgent stubs with real PostgreSQL/Redis | 9B.1 | 5 | 2 days |
| 9B.3 | Integration tests with real infrastructure | 9B.2 | 3 | 1 day |

**Total: 16 points, 6 days (optional, depends on Phase 2 completion)**

**Sprint 9 Success Criteria:**
- ✅ EvolutionAgent generates 10+ test cases with test steps, stored in database
- ✅ Test cases visible in frontend, executable via "Run Test" button
- ✅ Feedback loop operational: Execution results improve RequirementsAgent scenario generation
- ✅ LLM generates executable test steps (navigate, click, type, verify actions)
- ✅ AnalysisAgent fully operational (completed in Sprint 7-8)
- ✅ Analysis Agent produces FMEA-based risk scores (RPN = Severity × Occurrence × Detection)
- ✅ Analysis Agent calculates ROI for each scenario (explicit formula with effort estimation)
- ✅ Analysis Agent estimates execution times (heuristics-based, categorized as fast/medium/slow)
- ✅ Analysis Agent performs dependency analysis (topological sort, cycle detection, parallel groups)
- ✅ Analysis Agent integrates historical data (Phase 2 execution history, failure rates - stub or real)
- ✅ Analysis Agent calculates business value (revenue impact, user impact, compliance)
- ✅ LLM integration with Azure GPT-4o operational (structured risk analysis output)
- ✅ Caching reduces LLM calls by 30% (pattern reuse for similar pages)
- ✅ 4-agent workflow: Observe Web App → Extract Requirements → Analyze Risks/ROI/Dependencies → Generate Test Code
- ✅ First optimized prompt variant deployed (A/B tested for accuracy)
- ✅ Token usage <12,000 per test cycle (with caching, enhanced analysis)
- ✅ Real infrastructure integration (when Developer B ready) - optional

---

### Sprint 10: Phase 2 Integration & API (Mar 6 - Mar 19, 2026)

#### Developer A Tasks (24 points)

| Task | Description | Duration | Dependencies |
|------|-------------|----------|--------------|
| **10A.1** | Create `/api/v2/generate-tests` endpoint | 2 days | Sprint 9 |
| **10A.2** | Wrap Phase 2 execution engine (zero-downtime migration) | 3 days | 10A.1 |
| **10A.3** | Feature flag (AGENTS_ENABLED env var) | 1 day | 10A.2 |
| **10A.4** | API versioning (/api/v1 vs /api/v2) | 1 day | 10A.1 |
| **10A.5** | Rollout strategy (5% → 25% → 50% → 100%) | 2 days | 10A.3 |

**Total: 24 points, 9 days**

#### Developer B Tasks (18 points)

| Task | Description | Duration | Dependencies |
|------|-------------|----------|--------------|
| **10B.1** | GitHub Actions workflow (test on every PR) | 2 days | Sprint 9 |
| **10B.2** | Automated deployment to staging | 2 days | 10B.1 |
| **10B.3** | Load testing with Locust (100 concurrent users) | 2 days | Sprint 9 |
| **10B.4** | System tests (15+ scenarios: happy path + edge cases) | 2 days | 10A.5, 10B.3 |

**Total: 18 points, 8 days**

**Sprint 10 Success Criteria:**
- ✅ `/api/v2/generate-tests` operational (multi-agent)
- ✅ Feature flag allows gradual rollout (5%→100%)
- ✅ CI/CD pipeline runs tests on every PR
- ✅ Load test passes: 100 users, <5s latency
- ✅ Phase 2 + Phase 3 integration complete

---

### Sprint 11: Learning System Activation (Mar 20 - Apr 2, 2026)

**Important:** The **Learning System** (this sprint) is the **core of continuous improvement**, not any individual agent. It operates at a meta-level above all agents, coordinating:
- Prompt optimization for all agents (including EvolutionAgent)
- Pattern learning and reuse across agents
- A/B testing and automatic winner promotion
- Performance monitoring and auto-recovery

**Agent Roles:**
- **EvolutionAgent:** Generates test code, participates in learning loop via Learning System
- **All Agents:** Contribute execution results, metrics, patterns to Learning System
- **Learning System:** Coordinates optimization, A/B testing, pattern extraction across all agents

#### Developer A Tasks (22 points)

| Task | Description | Duration | Dependencies |
|------|-------------|----------|--------------|
| **11A.1** | Implement PromptOptimizer (manual variant testing) | 3 days | Sprint 10 |
| **11A.2** | Create 3 prompt variants for Evolution Agent | 2 days | 11A.1 |
| **11A.3** | Manual A/B testing (100 samples per variant) | 3 days | 11A.2 |
| **11A.4** | Pattern library (store + retrieve learned patterns) | 2 days | Sprint 10 |

**Total: 22 points, 10 days**

#### Developer B Tasks (18 points)

| Task | Description | Duration | Dependencies |
|------|-------------|----------|--------------|
| **11B.1** | Implement ExperimentManager (10% exploration traffic) | 3 days | Sprint 10 |
| **11B.2** | Activate automated feedback collection | 1 day | Sprint 10 |
| **11B.3** | Weekly performance review dashboard (simple metrics) | 2 days | 11B.1 |
| **11B.4** | Rollback mechanism (revert prompt <1 min) | 2 days | 11A.3 |

**Total: 18 points, 8 days**

**Sprint 11 Success Criteria:**
- ✅ PromptOptimizer generates 3+ variants
- ✅ A/B testing identifies best variant (manual analysis)
- ✅ ExperimentManager allocates 10% traffic to experiments
- ✅ Pattern library stores 10+ learned patterns
- ✅ Rollback tested: reverts bad prompt in <1 minute

---

### Sprint 12: Security & Production Readiness (Apr 3 - Apr 15, 2026)

#### Developer A Tasks (24 points)

| Task | Description | Duration | Dependencies |
|------|-------------|----------|--------------|
| **12A.1** | Implement JWT authentication (agent-to-agent) | 2 days | Sprint 11 |
| **12A.2** | Implement RBAC (4 roles: Admin, Developer, Viewer, Service) | 3 days | 12A.1 |
| **12A.3** | TLS 1.3 enforcement (nginx config) | 1 day | Sprint 11 |
| **12A.4** | Security audit (OWASP ZAP + manual testing) | 2 days | 12A.1-12A.3 |
| **12A.5** | Production runbook (deployment, troubleshooting) | 1 day | Sprint 11 |

**Total: 24 points, 9 days**

#### Developer B Tasks (18 points)

| Task | Description | Duration | Dependencies |
|------|-------------|----------|--------------|
| **12B.1** | Audit logging (all API calls logged) | 2 days | Sprint 11 |
| **12B.2** | Rate limiting (per-user limits) | 2 days | Sprint 11 |
| **12B.3** | User documentation (user guide + API reference) | 2 days | Sprint 11 |
| **12B.4** | Final regression testing (all features) | 2 days | 12A.5, 12B.3 |

**Total: 18 points, 8 days**

**Sprint 12 Success Criteria:**
- ✅ JWT authentication operational
- ✅ RBAC with 4 roles enforced at API level
- ✅ Security audit passed (no critical/high issues)
- ✅ Audit log records all actions (90-day retention)
- ✅ Rate limiting prevents abuse (1000 req/hour per user)
- ✅ User documentation complete
- ✅ **PHASE 3 LAUNCH READY** 🚀

---

## 3. Sprint Framework

### 3.1 Sprint Cycle (2 weeks each)

**Week 1:**
- Monday: Sprint Planning (2 hours, 10:00 AM)
- Daily: Standup (15 minutes @ 9:00 AM)
- Friday: Sprint Review (internal checkpoint, 30 minutes)

**Week 2:**
- Monday-Thursday: Standup (15 minutes @ 9:00 AM)
- Friday: Sprint Review + Retrospective (2 hours, 2:00 PM)
  - Review: 1 hour (demo to stakeholders)
  - Retrospective: 1 hour (team only)

### 3.2 Sprint Planning Agenda

1. **Review Previous Sprint** (15 min)
   - What was completed
   - What was carried over
   - Blockers encountered

2. **Define Sprint Goal** (15 min)
   - One-sentence objective
   - Measurable success criteria

3. **Task Breakdown** (60 min)
   - Review backlog
   - Estimate story points (Fibonacci: 1, 2, 3, 5, 8, 13)
   - Assign tasks to Developer A/B

4. **Identify Dependencies** (15 min)
   - External dependencies (DevOps)
   - Inter-task dependencies
   - Critical path items

5. **Define Definition of Done** (15 min)
   - Acceptance criteria per task
   - Testing requirements (unit + integration)
   - Documentation requirements

### 3.3 Daily Standup Format

**3 Questions (5 minutes per person):**
1. What did you complete yesterday?
2. What will you work on today?
3. Any blockers or impediments?

**Rules:**
- Max 15 minutes total
- Standing meeting (not sitting)
- No problem-solving (take offline)
- Update Jira board during standup

### 3.4 Sprint Review (Demo)

**Attendees:** CTO, VP Engineering, Developer A, Developer B  
**Duration:** 1 hour  
**Format:**
1. Sprint goal review (5 min)
2. Live demo of new features (30 min)
3. Metrics review (10 min)
   - Code coverage
   - Test generation accuracy
   - Performance benchmarks
4. Stakeholder feedback (10 min)
5. Next sprint preview (5 min)

### 3.5 Sprint Retrospective

**Attendees:** Developer A, Developer B (team only)  
**Duration:** 1 hour  
**Format:**
1. What went well? (15 min)
2. What didn't go well? (15 min)
3. What should we try next sprint? (20 min)
4. Action items (10 min)

**Output:** 3-5 action items for next sprint improvement

---

## 4. Budget & Cost Analysis

### 4.1 Infrastructure Costs (Monthly)

**Phase 3 (MVP - Simplified):**

| Component | Cost | Notes |
|-----------|------|-------|
| **PostgreSQL** | $0 | Reuse existing Phase 2 database |
| **Redis** | $0 | Reuse existing Phase 2 Redis (simple pub/sub) |
| **Qdrant Vector DB** | $0 | Free tier (1GB) |
| **Hosting** | $0 | Run locally or use existing server |
| **Monitoring** | $0 | Python logging (console output) |
| **Subtotal Infrastructure** | **$0** ✅ |

**Phase 4 (Production - When We Need Scale):**

| Component | Cost | When to Upgrade |
|-----------|------|-----------------|
| **Kubernetes (EKS)** | $431 | >100 concurrent users |
| **Redis Streams (3 nodes)** | $240 | >1000 messages/sec |
| **PostgreSQL HA** | $150 | Need 99.9% uptime |
| **Load Balancer** | $25 | Multiple backend instances |
| **Prometheus/Grafana** | $5 | Need metrics dashboard |
| **Subtotal Phase 4** | **$851** | Deferred |

**Key Insight:** Phase 3 costs **$0 infrastructure** by reusing existing Phase 2 setup!

### 4.2 LLM API Costs (Monthly)

**Assumptions:**
- 10 developers using system
- 5 test cycles/day per developer
- 20 working days/month
- **Total: 1,000 test cycles/month**

**Per Test Cycle Token Usage:**
- Observation Agent: 2,500 tokens
- Requirements Agent: 1,800 tokens
- Analysis Agent: 4,000 tokens
- **Evolution Agent: 8,000 tokens** (most expensive)
- Orchestration Agent: 700 tokens
- Reporting Agent: 3,000 tokens
- **Total: ~20,000 tokens per cycle**

**Strategy Options:**

| Strategy | Cost/Cycle | Monthly Cost (1K cycles) | Quality | Recommendation |
|----------|-----------|-------------------------|---------|----------------|
| All GPT-4 | $0.33 | $330 | 100% | Not cost-effective |
| **Hybrid Azure OpenAI** (GPT-4o for Observation/Evolution, GPT-4-mini for others) | **$0.16** | **$160** | 95% | **✅ Recommended** |
| All GPT-4-mini | $0.006 | $6 | 80% | Too low quality |
| **With 90% caching** (after Sprint 10) | **$0.016** | **$16** | 95% | **Future optimization** |

**Hybrid Azure OpenAI Strategy Details:**
- **Primary Provider:** Azure OpenAI (enterprise SLA, no Cloudflare blocks)
  - ObservationAgent: GPT-4o ($0.015 per page)
  - EvolutionAgent: GPT-4o (complex reasoning): $0.16/cycle
  - Other agents: GPT-4-mini (simple parsing): $0.004/cycle
- **Backup Provider:** Cerebras llama3.1-8b (free, 10x faster, fallback)
- **Caching Strategy:** Multi-tier (Hot: Redis 1h, Warm: PostgreSQL 7d, Cold: 30d)
- **Without caching:** $160/month
- **With 90% caching (Sprint 10+):** $16/month (90% cost reduction)
- **Current status:** Azure OpenAI tested successfully with Three HK website (262 elements detected)

### 4.3 Learning System Costs

**Phase 3 (Start Simple):**
- PostgreSQL storage: $0 (reuse existing database, add 8 tables)
- Perplexity AI API: $0 (defer to Phase 4, use manual prompt optimization)
- A/B testing: $0 (manual testing initially)
- Pattern mining: $0 (Python scripts on existing infrastructure)
- **Total Learning System: $0/month**

**Phase 4 (Automated Learning):**
- PostgreSQL storage expansion: $10/month
- Perplexity AI API (automated prompt optimization): $20/month
- A/B testing infrastructure: $10/month
- Pattern mining compute: $10/month
- **Total Learning System: $50/month** (when we need automation)

### 4.4 Total Monthly Budget

**Phase 3 (MVP):**

| Category | Cost |
|----------|------|
| **Infrastructure** | $0 (reuse Phase 2) |
| **LLM API (Hybrid)** | $160 |
| **Learning System** | $0 (manual initially) |
| **TOTAL** | **$160/month** ✅ |

**Cost per Test Cycle:** $160 / 1,000 = **$0.16/cycle** (84% cheaper than original!)

**Phase 4 (Production Scale):**

| Category | Cost |
|----------|------|
| **Infrastructure** | $851 |
| **LLM API (Hybrid)** | $160 |
| **Learning System** | $50 |
| **TOTAL** | **$1,061/month** |

### 4.5 Cost Optimization Strategies

**1. Caching (30% LLM savings)**
```python
@lru_cache(maxsize=1000)
async def generate_test_cached(code_hash: str, requirements: str):
    if code_hash in cache:
        return cache[code_hash]  # Cache hit
    result = await generate_test(code_hash, requirements)
    cache[code_hash] = result
    return result
```
**Savings:** $160 × 0.30 = **$48/month**

**2. Compression (40% Redis memory savings)**
```python
import zlib
def compress_message(message: dict) -> bytes:
    return zlib.compress(json.dumps(message).encode())
```
**Savings:** $240 × 0.40 = **$96/month**

**3. Token Limit Enforcement (prevent runaway costs)**
```python
MAX_TOKENS_PER_REQUEST = 10000
if len(input_tokens) > MAX_TOKENS_PER_REQUEST:
    raise ValueError(f"Input exceeds {MAX_TOKENS_PER_REQUEST} tokens")
```
**Savings:** Prevents unexpected $1000+ bills

**Optimized Monthly Cost:** $160 - $48 = **$112/month** (with caching)

**Phase 3 is 89% cheaper than original plan ($112 vs $1,061) while delivering same functionality!**

### 4.6 Scaling Projections

**When do we need Phase 4 infrastructure upgrade?**

| Metric | Phase 3 Limit | Upgrade Trigger | Phase 4 Capacity |
|--------|---------------|-----------------|------------------|
| **Concurrent Users** | 10-20 | >50 users | 1000+ users |
| **Messages/sec** | 100 | >500 msg/sec | 10,000 msg/sec |
| **Test Cycles/month** | 1,000-5,000 | >10,000 cycles | 100,000 cycles |
| **Uptime Required** | 95% (dev/test) | Need 99.9% | 99.99% |

**Phase 3 handles 10 developers comfortably. Upgrade to Phase 4 when product-market fit proven.**

### 4.7 ROI Justification

**Current Manual Testing:**
- QA engineer salary: $80,000/year = $6,667/month
- Time spent writing tests: 50% = $3,333/month

**Automated Testing (Phase 3 - Simplified):**
- Infrastructure + LLM: $112/month (with caching)
- Developer time saved: 10 developers × 1 hour/day × $50/hour × 20 days = $10,000/month

**Net Savings:** $10,000 - $112 = **$9,888/month** (~**89x ROI!**)

**Break-Even:** 0.1 developers using system (nearly instant ROI)

---

## 5. Security Design

### 5.1 Security Layers

```
┌─────────────────────────────────────────┐
│   Layer 5: Audit & Compliance           │ ← All actions logged
├─────────────────────────────────────────┤
│   Layer 4: Network Security             │ ← TLS 1.3, VPC isolation
├─────────────────────────────────────────┤
│   Layer 3: Authorization (RBAC)         │ ← 4 roles: Admin, Dev, Viewer, Service
├─────────────────────────────────────────┤
│   Layer 2: Authentication (JWT)         │ ← API keys + JWT tokens
├─────────────────────────────────────────┤
│   Layer 1: Input Validation             │ ← Schema validation, rate limiting
└─────────────────────────────────────────┘
```

### 5.2 Authentication

**Method:** JWT-based with API keys

**Implementation:**
```python
# backend/agents/security/agent_auth.py

import jwt
from datetime import datetime, timedelta

class AgentAuthenticator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    def issue_token(self, agent_id: str, agent_type: str) -> str:
        """Issue JWT for agent"""
        payload = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT from agent message"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                raise ValueError("Token expired")
            return payload
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")
```

**Storage:**
- API keys stored in database with bcrypt hashing
- JWT secret in Kubernetes Secrets (not environment variables)
- Auto-rotation every 90 days

### 5.3 Authorization (RBAC)

**4 Roles:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | All permissions (CRUD tests, settings, agents) | CTO, VP Engineering |
| **Developer** | Create/read tests, read settings | Development team |
| **Viewer** | Read-only access to tests and settings | Stakeholders, QA |
| **Service Account** | Create/read tests (no settings) | CI/CD pipelines |

**Database Schema:**
```sql
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB NOT NULL
);

INSERT INTO roles (role_name, permissions) VALUES
('admin', '{"tests": ["create", "read", "update", "delete"], "settings": ["read", "update"], "agents": ["read", "restart"]}'),
('developer', '{"tests": ["create", "read"], "settings": ["read"]}'),
('viewer', '{"tests": ["read"], "settings": ["read"]}'),
('service_account', '{"tests": ["create", "read"]}');
```

**Middleware:**
```python
# backend/api/auth.py

from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials = Security(security)):
    """Verify API key and return user with permissions"""
    api_key = credentials.credentials
    
    user = await db.fetchrow("""
        SELECT u.user_id, r.permissions
        FROM api_keys ak
        JOIN users u ON ak.user_id = u.user_id
        JOIN roles r ON u.role_id = r.role_id
        WHERE ak.key_hash = $1
    """, hash(api_key))
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user

def require_permission(resource: str, action: str):
    """Decorator to check permissions"""
    async def checker(user = Depends(verify_api_key)):
        perms = user["permissions"]
        if resource not in perms or action not in perms[resource]:
            raise HTTPException(status_code=403, detail="Permission denied")
        return user
    return checker

# Usage
@app.post("/api/v2/tests/generate")
async def generate_tests(
    request: TestGenerationRequest,
    user = Depends(require_permission("tests", "create"))
):
    # User has permission to create tests
    ...
```

### 5.4 Network Security (TLS 1.3)

**nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.aitest.example.com;
    
    # TLS certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.aitest.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.aitest.example.com/privkey.pem;
    
    # TLS 1.3 only (most secure)
    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384';
    ssl_prefer_server_ciphers off;
    
    # HSTS (force HTTPS for 1 year)
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Certificate Renewal:**
- Let's Encrypt (free, auto-renews every 90 days)
- Certbot cron job: `0 0 * * 0 certbot renew --quiet`

### 5.5 Audit Logging

**Database Schema:**
```sql
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    request_body JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
```

**Middleware:**
```python
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API requests"""
    user_id = request.state.user.get("user_id") if hasattr(request.state, "user") else None
    
    response = await call_next(request)
    
    await db.execute("""
        INSERT INTO audit_log (user_id, action, ip_address, user_agent)
        VALUES ($1, $2, $3, $4)
    """, user_id, request.url.path, request.client.host, request.headers.get("user-agent"))
    
    return response
```

**Retention:** 90 days (GDPR compliance)

### 5.6 Secrets Management

**Kubernetes Secrets (not environment variables):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aitest-secrets
type: Opaque
data:
  jwt-secret: <base64-encoded-secret>
  openai-api-key: <base64-encoded-key>
  postgres-password: <base64-encoded-password>
```

**Access Control:**
- Only pods with `serviceAccountName: aitest-backend` can read secrets
- Secrets mounted as read-only volumes (not env vars)
- Auto-rotation every 90 days via external-secrets-operator

### 5.7 Security Audit Checklist

**Sprint 12 Security Audit:**

| Check | Tool | Target | Status |
|-------|------|--------|--------|
| **OWASP Top 10** | OWASP ZAP | API endpoints | Pending |
| **SQL Injection** | SQLMap | Database queries | Pending |
| **XSS/CSRF** | Burp Suite | Frontend forms | Pending |
| **Authentication Bypass** | Manual testing | JWT validation | Pending |
| **Authorization Escalation** | Manual testing | RBAC rules | Pending |
| **Secrets Exposure** | git-secrets | Codebase | Pending |
| **Dependency Vulnerabilities** | Snyk | npm/pip packages | Pending |

**Acceptance Criteria:** No critical or high severity issues

---

## 6. Risk Management

### 6.1 Risk Register

| Risk ID | Description | Probability | Impact | Mitigation | Owner |
|---------|-------------|------------|--------|------------|-------|
| **R1** | DevOps delays infrastructure (N/A for Phase 3) | Low | Low | Using existing Phase 2 infrastructure, no external dependencies | Developer A |
| **R2** | LLM API cost overrun (>$300/month) | Medium | High | Token limit enforcement, caching, alerts at $200 | Developer A |
| **R3** | Developer A sick/unavailable for >3 days | Low | High | Developer B trained on critical path tasks | Developer B |
| **R4** | Test generation accuracy <80% | Medium | High | A/B testing with multiple prompt variants | Developer A |
| **R5** | Performance degradation (>10s latency) | Low | Medium | Load testing every sprint, optimize agent coordination | Developer B |
| **R6** | Security breach (API key leaked) | Low | Critical | API key rotation, rate limiting, audit logging | Developer A |
| **R7** | Deadlock in Contract Net Protocol | Medium | Medium | 5-minute timeout, deadlock detection algorithm | Developer A |
| **R8** | Learning system degrades quality instead of improving | Medium | High | Weekly performance reviews, rollback mechanism | Developer A |
| **R9** | Phase 2 integration breaks existing functionality | Medium | High | Feature flags, gradual rollout (5%→100%), A/B testing | Developer A |

### 6.2 Risk Mitigation Plans

**R1: Infrastructure Delays (Low Risk in Phase 3)**
- **Trigger:** N/A - no external infrastructure dependencies
- **Action:** Continue using existing Phase 2 PostgreSQL + Redis
- **Cost:** Zero impact
- **Decision Maker:** N/A

**R2: LLM Cost Overrun**
- **Trigger:** Monthly cost exceeds $200 (125% of Phase 3 budget)
- **Action:** 
  1. Enable caching (30% savings) - immediate
  2. Review token usage by agent, optimize prompts
  3. Switch Evolution Agent to GPT-4-mini if needed
- **Cost:** Potential quality degradation from 95% to 85%
- **Decision Maker:** Developer A (escalate to CTO if exceeds $300)

**R4: Low Test Generation Accuracy**
- **Trigger:** Test generation accuracy <80% for 2 consecutive sprints
- **Action:**
  1. A/B test 5 prompt variants
  2. Increase Evolution Agent to GPT-4 (from GPT-4-mini)
  3. Add human-in-the-loop feedback for 100 samples
- **Cost:** $50 additional LLM costs + 2 days effort
- **Decision Maker:** Developer A

**R8: Learning System Degrades Quality**
- **Trigger:** Test pass rate drops >20% after prompt optimization
- **Action:**
  1. Immediately rollback to previous prompt variant (< 1 min)
  2. Review experiment logs for root cause
  3. Mark failed variant as "do_not_use"
  4. Increase exploration rate from 10% to 20% for 1 week
- **Cost:** 1 day investigation
- **Decision Maker:** Developer A

### 6.3 Issue Escalation Matrix

| Severity | Response Time | Escalation Path | Example |
|----------|--------------|----------------|---------|
| **P0 (Critical)** | Immediate | Developer A → CTO | Production outage, data breach |
| **P1 (High)** | <4 hours | Developer A → VP Eng | Sprint goal at risk, budget overrun |
| **P2 (Medium)** | <24 hours | Developer A → Team | Minor delays, test failures |
| **P3 (Low)** | <72 hours | Developer A | Documentation gaps, UI bugs |

---

## 7. Stakeholder Communication

### 7.1 Weekly Status Report (Email)

**To:** CTO, VP Engineering  
**From:** Developer A  
**Frequency:** Every Friday 5:00 PM  
**Format:**

```
Subject: [Phase 3] Sprint X Status - [On Track | At Risk | Blocked]

Summary:
- Sprint goal: [One-sentence goal]
- Completion: [X%] (Y/Z story points)
- Status: [On Track | At Risk | Blocked]

Accomplishments This Week:
- [Bullet points]

Risks & Issues:
- [Risks from register with probability/impact]

Budget Status:
- Spent this month: $X / $160 (Phase 3 MVP) (Y%)
- Forecast: [On budget | Over budget by $Z]
- Note: Phase 4 production scale budget is $1,061/month

Next Week:
- [Preview of next sprint]

Blockers Requiring CTO Decision:
- [None | List blockers]
```

### 7.2 Sprint Review (Demo)

**Attendees:** CTO, VP Engineering, Developer A, Developer B  
**Duration:** 1 hour  
**Frequency:** Bi-weekly (end of each sprint)  
**Format:** Live demo + metrics review

**Metrics Dashboard:**
- Code coverage: [X%] (target: 95%)
- Test generation accuracy: [X%] (target: 85%)
- API latency P95: [X ms] (target: <5000 ms)
- Cost per test cycle: [$X] (target: <$1.00)
- Learning metrics: Test pass rate trend, prompt optimization impact

### 7.3 Monthly Executive Summary

**To:** CTO, CFO, VP Engineering  
**From:** Developer A  
**Frequency:** Last Friday of each month  
**Format:** 1-page PDF with charts

**Content:**
1. **Progress Summary**
   - Sprints completed: X/6
   - Story points completed: X/354 (Y%)
   - Timeline: [On track | X weeks delayed]

2. **Budget Analysis**
   - Spent this month: $X
   - Year-to-date: $Y
   - Forecast to completion: $Z
   - ROI: [XX]x return on investment

3. **Quality Metrics & Agent Performance**
   - Code coverage: [X%]
   - Test accuracy: [X%]
   - User satisfaction: [X/5 stars]
   - Learning system impact: [+X% quality improvement]
   - **Agent Performance Scores:**
     - ObservationAgent: [Overall score: X.XX (Grade: A/B/C/D/F)]
     - RequirementsAgent: [Overall score: X.XX (Grade: A/B/C/D/F)]
     - AnalysisAgent: [Overall score: X.XX (Grade: A/B/C/D/F)]
   - See [Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) for detailed metrics

4. **Risks & Mitigation**
   - Active risks: [List top 3]
   - Mitigations in place: [Actions taken]

5. **Next Month Preview**
   - Upcoming sprints: [Sprint X-Y]
   - Key milestones: [Bullet points]

---

## 📚 Document Control

**Document Version:** 2.4  
**Last Updated:** January 29, 2026  
**Next Review:** Sprint 8 completion (Feb 19, 2026)  
**Document Owner:** Developer A (Project Manager)  
**Approval:** CTO (Sponsor)

**Change Log:**
- v2.4 (Jan 29, 2026): Sprint 7 completion - AnalysisAgent fully implemented (46 points), real-time execution integrated, E2E testing validated, Agent Performance Scoring Framework designed
- v2.3 (Jan 27, 2026): Pre-Sprint 7 completion - ObservationAgent and RequirementsAgent operational
- v2.0 (Jan 20, 2026): Simplified infrastructure, added detailed Sprint 7-12 breakdown, reorganized sections
- v1.0 (Jan 19, 2026): Initial version

**Related Documents:**
- [Phase3-Architecture-Design-Complete.md](Phase3-Architecture-Design-Complete.md) - Technical architecture
- [Phase3-Implementation-Guide-Complete.md](Phase3-Implementation-Guide-Complete.md) - Implementation details
- [Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) - Agent performance metrics and scoring methodology

---

## Supporting Documents

This document provides sprint planning, task breakdown, and project management. For detailed analysis, strategies, and agent-specific documentation, see the following supporting documents:

### Detailed Analysis & Strategies

- **[Multi-Agent Continuous Improvement Strategy](supporting-documents/MULTI-AGENT-CONTINUOUS-IMPROVEMENT-STRATEGY.md)** - Complete feedback loop architecture, agent collaboration patterns, and continuous improvement mechanisms
- **[EvolutionAgent Frontend Integration Solution](supporting-documents/EVOLUTION-AGENT-FRONTEND-INTEGRATION-SOLUTION.md)** - Solution for integrating EvolutionAgent's generated tests with Phase 1/2 frontend system
- **[4-Agent Workflow Purpose and Value](supporting-documents/4-AGENT-WORKFLOW-PURPOSE-AND-VALUE.md)** - Complete value chain explanation, use cases, and real-world workflow examples

### Agent-Specific Documentation

- **[EvolutionAgent Review and Gap Analysis](supporting-documents/EvolutionAgent-Review-and-Gap-Analysis.md)** - Comprehensive review of EvolutionAgent implementation against industrial best practices, identifying gaps and recommendations
- **[Agent Performance Scoring Framework](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md)** - Detailed performance metrics, scoring formulas, validation methods, and industry best practices for all agents

### Document Organization

**Main Documents (Root Folder):**
- `Phase3-Architecture-Design-Complete.md` - High-level architecture and design decisions
- `Phase3-Implementation-Guide-Complete.md` - Detailed implementation tasks and code examples
- `Phase3-Project-Management-Plan-Complete.md` - This document (sprint planning, task breakdown, budget, timeline)

**Supporting Documents (supporting-documents/ folder):**
- Detailed analysis documents
- Agent-specific reviews
- Strategy documents
- Performance frameworks

---

**END OF PROJECT MANAGEMENT PLAN**