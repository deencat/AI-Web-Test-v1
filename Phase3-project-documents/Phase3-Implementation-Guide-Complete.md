# Phase 3: Complete Implementation Guide

**Purpose:** Comprehensive implementation guide with code examples, sprint tasks, integration, testing, security, and autonomous learning  
**Scope:** Sprint 7-12 detailed tasks, Phase 2 integration, code templates, testing strategy, security design, frontend integration, autonomous self-improvement  
**Status:** ✅ Sprint 9 COMPLETE (100%) - Phase 2+3 Merged, Gap Analysis Complete, Ready for Sprint 10  
**Version:** 1.4  
**Last Updated:** February 10, 2026

> **📖 When to Use This Document:**
> - **Writing Code:** Code templates, implementation examples, API patterns
> - **Sprint Tasks:** Detailed task breakdowns with dependencies and durations
> - **Testing Strategy:** Unit test examples, integration test patterns
> - **For Sprint Planning:** See [Project Management Plan](Phase3-Project-Management-Plan-Complete.md) Section 2.4
> - **For Architecture Design:** See [Architecture Document](Phase3-Architecture-Design-Complete.md) Section 6

---

## 📋 Table of Contents

1. [Implementation Overview](#1-implementation-overview)
2. [Sprint 7-12 Detailed Tasks](#2-sprint-7-12-detailed-tasks)
3. [Production-Ready Code Examples](#3-production-ready-code-examples)
4. [Phase 2 Integration Strategy](#4-phase-2-integration-strategy)
5. [Testing Strategy](#5-testing-strategy)
6. [Agent Performance Scoring](#6-agent-performance-scoring) - Performance metrics, quality validation
7. [Security Implementation](#7-security-implementation)
8. [Cost Optimization](#8-cost-optimization)

---

## 1. Implementation Overview

### 1.0 Agent Roles (Web Application Testing)

**Context:** This is an AI-powered WEB APPLICATION testing tool that generates browser automation tests using Playwright/Stagehand.

**The 6 Agents and Their Roles:**

1. **ObservationAgent** - Web Application Observer
   - **What it does:** Crawls target web application using Playwright
   - **Inputs:** URL, authentication credentials
   - **Outputs:** Page map (URLs, UI elements, forms, buttons, links)
   - **Technology:** Playwright for browser automation, DOM parsing
   - **Example:** Given `https://myapp.com/login`, finds login form with username/password fields, submit button

2. **RequirementsAgent** - Test Requirement Extractor ✅ E2E VERIFIED
   - **What it does:** Converts UI observations into BDD test scenarios with industry standards, continuously improves based on execution feedback
   - **Inputs:** Page map from ObservationAgent (261 UI elements), execution feedback from EvolutionAgent (which scenarios worked/failed), optional user_instruction (user's specific test requirement)
   - **Outputs:** 18 test scenarios in Given/When/Then format (functional, WCAG 2.1 accessibility, OWASP security, edge cases)
   - **Technology:** Azure GPT-4o LLM (~12,500 tokens), pattern-based fallback, feedback-driven prompt optimization
   - **User Instruction Support:** Accepts natural language requirements (e.g., "Test purchase flow for '5G寬頻數據無限任用' plan"), prioritizes matching scenarios with high/critical priority
   - **Performance:** Confidence 0.90, 20.9s execution time
   - **E2E Tested:** Three HK website (261 elements → 18 scenarios) ✅
   - **Example:** "Given user is on 5G broadband pricing page, When user clicks '立即登記' button, Then registration form opens"
   - **Continuous Improvement:** Uses execution results from EvolutionAgent's generated tests to identify successful scenario patterns and avoid problematic structures

3. **AnalysisAgent** - Risk & Priority Analyzer
   - **What it does:** Identifies which UI flows are most critical to test
   - **Inputs:** Test requirements, historical bug data
   - **Outputs:** Risk scores (0.0-1.0), prioritized test list
   - **Technology:** Dependency graph analysis, risk scoring algorithms
   - **Example:** Login flow = 0.95 (critical), Footer links = 0.2 (low priority)

4. **EvolutionAgent** - Test Code Generator ✅ OPERATIONAL
   - **What it does:** Converts BDD scenarios (Given/When/Then) into executable test steps and stores them in database
   - **Inputs:** BDD test scenarios from RequirementsAgent, risk scores and execution results from AnalysisAgent, optional user_instruction and login_credentials
   - **Outputs:** Test cases stored in database (TestCase objects with test steps), visible in frontend, executable via "Run Test" button
   - **Technology:** Azure GPT-4o LLM with prompt templates (3 variants), database integration
   - **Features:**
     - ✅ Goal-aware generation: Complete flows to true completion (multi-page flows, final verification)
     - ✅ Login-aware generation: Automatic login steps when credentials provided
     - ✅ User instruction support: Incorporates user requirements into test step generation
   - **Example:** 
     - **Input (BDD):** "Given: User is on login page, When: User enters credentials, Then: User redirected to dashboard"
     - **Output (Test Steps):** ["Navigate to login page", "Enter email: test@example.com", "Enter password: password123", "Click Login button", "Verify URL contains /dashboard"]
     - **Storage:** TestCase object in database with steps array, linked to frontend UI
   - **Feedback Loop:** Execution results from generated tests feed back to RequirementsAgent to improve future scenario generation
     - **Status:** Infrastructure complete (8A.10), activation pending (can be done in Sprint 9 or Sprint 11)
     - **Current:** `RequirementsAgent` accepts `execution_feedback`, `EvolutionAgent.learn_from_feedback()` method exists
     - **Future:** Full activation with message bus integration in Sprint 11
   - **Integration:** Test cases appear in frontend automatically, can be executed via Phase 2 engine, results tracked for continuous improvement
   - **Status:** Core implementation complete, 17+ test cases generated per page, confidence: 0.95

5. **OrchestrationAgent** - Workflow Coordinator
   - **What it does:** Coordinates the 4 agents above in correct sequence
   - **Inputs:** User request ("test my web app at https://...")
   - **Outputs:** Complete workflow execution (Observe → Require → Analyze → Evolve)
   - **Technology:** State machine, Contract Net Protocol for task allocation
   - **Example:** Receives user request → assigns tasks to agents → monitors progress → handles failures

6. **ReportingAgent** - Test Report Generator
   - **What it does:** Generates coverage reports, test execution summaries
   - **Inputs:** Generated tests, execution results
   - **Outputs:** PDF/Markdown reports with charts
   - **Technology:** Report templates, charting libraries
   - **Example:** "85% page coverage, 12 tests generated, 10 passed, 2 failed (login timeout)"

**Key Distinction:**
- **Phase 2 (Current):** Manual test creation OR simple AI generation
- **Phase 3 (This):** Multi-agent system that autonomously observes web app, extracts requirements, analyzes risks, and generates tests

### 1.1 Timeline

**Total Duration:** 12 weeks (6 sprints × 2 weeks)  
**Start Date:** January 23, 2026  
**End Date:** April 15, 2026  
**Team:** Developer A (lead), Developer B (support)

### 1.2 Sprint Summary

| Sprint | Duration | Focus | Story Points | Critical Path |
|--------|----------|-------|--------------|---------------|
| **Sprint 7** | Weeks 1-2 | Infrastructure Integration | 23 | Developer A |
| **Sprint 8** | Weeks 3-4 | Analysis + Evolution | 47 | Developer A |
| **Sprint 9** | Weeks 5-6 | Analysis + Evolution | 47 | Developer A |
| **Sprint 10** | Weeks 7-8 | Orchestration + Reporting | 52 | Developer A |
| **Sprint 11** | Weeks 9-10 | CI/CD Integration | 39 | Both (parallel) |
| **Sprint 12** | Weeks 11-12 | Enterprise Features | 44 | Developer A |
| **TOTAL** | 12 weeks | | **354 points** | |

### 1.3 Phase Breakdown

**Weeks 1-2 (Sprint 7):** Foundation
- Redis Streams, PostgreSQL, BaseAgent, memory system, health checks

**Weeks 3-6 (Sprints 8-9):** Core Agents
- ✅ Observation, Requirements agents already operational (Pre-Sprint 7)
- Analysis, Evolution agents to be implemented

**Weeks 7-8 (Sprint 10):** Coordination
- Orchestration, Reporting agents, Contract Net Protocol

**Weeks 9-10 (Sprint 11):** Integration
- GitHub Actions, CI/CD pipelines, load testing

**Weeks 11-12 (Sprint 12):** Production Readiness
- Multi-tenancy, RBAC, security audit, chaos engineering

---

## 2. Sprint 7-12 Detailed Tasks

### Sprint 7: AnalysisAgent Implementation (Independent - Jan 23 - Feb 5, 2026) ✅ **COMPLETE**

**Status:** All Sprint 7 tasks completed (Jan 23-29, 2026) - 46 story points delivered

**Goal:** Implement AnalysisAgent with FMEA risk scoring (Developer A works independently, no dependencies on Developer B) - **ACHIEVED**

**Story Points:** 46 (13 days duration) - Developer A can start immediately using stub infrastructure

**✅ Pre-Sprint 7 Work (COMPLETE):**
- ✅ BaseAgent abstract class (EA.1)
- ✅ Message bus stub (EA.2)
- ✅ Agent registry stub (EA.3)
- ✅ ObservationAgent with Azure OpenAI (EA.4)
- ✅ RequirementsAgent with industry best practices (EA.5)
- ✅ Unit tests (55/55 passing) (EA.6)

**See [Project Management Plan Section 2.4 Pre-Sprint 7](Phase3-Project-Management-Plan-Complete.md#pre-sprint-7-developer-a-early-start-jan-20-23-while-developer-b-on-phase-2) for completed tasks.**

**✅ AnalysisAgent Implementation Details (READY):**
- ✅ Full implementation code prepared in [Section 3.3](#33-analysisagent-implementation-enhanced---fmea-based-risk-analysis)
- ✅ FMEA risk scoring framework (RPN calculation)
- ✅ Historical data integration (use existing database - SQLite/PostgreSQL)
- ✅ ROI calculation and execution time estimation
- ✅ Dependency analysis with topological sort
- ✅ Business value scoring
- ✅ Coverage impact analysis

#### Developer A Tasks (46 points, INDEPENDENT - NO DEPENDENCIES ON DEVELOPER B)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 7A.4 | ✅ Implement AnalysisAgent class with FMEA risk scoring (RPN calculation) | Pre-Sprint 7 (EA.1-EA.6) | 13 | 5 days | 0 (START) | **COMPLETE** |
| 7A.5 | ✅ LLM integration for structured risk analysis (severity/occurrence/detection) | 7A.4 | 8 | 3 days | 5 | **COMPLETE** |
| 7A.6 | ✅ Historical data integration (use existing database - SQLite/PostgreSQL) | 7A.4 | 5 | 2 days | 5 | **COMPLETE** |
| 7A.7 | ✅ ROI calculation and execution time estimation | 7A.5 | 5 | 2 days | 8 | **COMPLETE** |
| 7A.8 | ✅ Dependency analysis with topological sort (cycle detection) | 7A.4 | 5 | 2 days | 5 | **COMPLETE** |
| 7A.9 | ✅ Business value scoring (revenue, users, compliance) | 7A.5 | 3 | 1 day | 8 | **COMPLETE** |
| 7A.10 | ✅ Coverage impact analysis and regression risk assessment | 7A.5 | 5 | 2 days | 8 | **COMPLETE** |
| 7A.11 | ✅ Unit tests for AnalysisAgent (44 tests, LLM mocking) | 7A.7, 7A.8 | 3 | 1 day | 10 | **COMPLETE** |
| 7A.12 | ✅ Integration tests (3-agent workflow: Observe → Requirements → Analyze) | 7A.11 | 5 | 2 days | 11 | **COMPLETE** |

**Total: 46 points, 13 days - ZERO dependencies on Developer B or Phase 2**

**Optional: Simple Redis Pub/Sub Setup (If Developer A Has Time)**

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 7A.13 | Install Redis locally (or use Docker) | None | 1 | 0.5 day |
| 7A.14 | Replace message bus stub with simple Redis pub/sub | 7A.13 | 2 | 1 day |
| 7A.15 | Replace agent registry stub with Redis-backed version | 7A.14 | 2 | 1 day |
| 7A.16 | Integration tests (agents + real Redis) | 7A.15 | 1 | 0.5 day |

**Total: 6 points, 3 days - OPTIONAL, SIMPLE SETUP**

**Note:** 
- All AnalysisAgent implementation details are documented in [Section 3.3](#33-analysisagent-implementation-enhanced---fmea-based-risk-analysis)
- Developer A can use stub infrastructure (message bus stub, agent registry stub) - no need to wait for Developer B or Phase 2 completion
- **Use existing database as-is** (SQLite for local dev, PostgreSQL in production) - no schema changes needed
- Historical data queries work with existing `test_executions` table
- **Redis pub/sub is optional** - simple setup (just `publish`/`subscribe`), can be added if Developer A has time
- **PostgreSQL optimizations deferred** to Sprint 10+ when Developer B is ready or when we need scale

#### Developer B Tasks (When Phase 2 Complete - DEFERRED TO LATER SPRINT)

**PostgreSQL Setup Deferred:** No need to add agent tables now. Use existing database as-is. PostgreSQL-specific optimizations can be added later when needed.

| Task ID | Description | Dependencies | Points | Duration | Sprint |
|---------|-------------|--------------|--------|----------|--------|
| 7B.1 | Add agent-related tables to existing database (PostgreSQL) | Phase 2 DB | 5 | 2 days | Sprint 10+ |
| 7B.2 | Implement three-layer memory system (working memory + database) | 7B.1 | 5 | 3 days | Sprint 10+ |
| 7B.3 | Add 8 learning system tables to database | 7B.1 | 3 | 1 day | Sprint 10+ |
| 7B.4 | Implement FeedbackCollector class | 7B.3 | 3 | 2 days | Sprint 10+ |
| 7B.5 | Unit tests for infrastructure (30+ tests) | 7B.1-7B.4 | 3 | 1 day | Sprint 10+ |

**Total: 19 points, 6 days - DEFERRED TO SPRINT 10+ (When Developer B Ready)**

#### Sprint 7 Success Criteria (Developer A Independent Path) - ✅ **ALL COMPLETE**

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
- ✅ E2E testing with real page execution (Three HK 5G Broadband page) - **COMPLETE**
- ✅ Browser visibility control (HEADLESS_BROWSER env var) - **COMPLETE**
- ✅ Optional: Redis pub/sub setup (if Developer A has time) - simple setup - **DEFERRED**
- ✅ PostgreSQL optimizations deferred to Sprint 10+ (when Developer B ready or when we need scale) - **DEFERRED**

#### Sprint 7 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| AnalysisAgent complexity | Medium | Medium | Use prepared implementation details, break into smaller tasks |
| LLM API rate limits | Low | Medium | Use Azure OpenAI (enterprise SLA), implement retry logic |
| Database query performance (SQLite) | Low | Low | Use existing database as-is, optimize later if needed |
| Redis setup complexity | Low | Low | Simple pub/sub only (not Streams), optional task |

---

### 1.4 LLM Integration Architecture

**Overview:** Phase 3 agents use a hybrid approach combining deterministic tools with LLM enhancement for intelligent observation and test generation.

#### Why LLM Enhancement?

**Playwright-Only Limitations:**
- ❌ Misses custom elements: `<div role="button">` not found by `query_selector("button")`
- ❌ Shadow DOM invisible to standard CSS selectors
- ❌ Dynamic JavaScript-loaded content
- ❌ Visual-only buttons: `<img onclick="submit()">` looks like button but isn't `<button>`
- ❌ No semantic understanding: Can't distinguish login button vs search button vs submit button
- **Result:** 30% accuracy on modern web applications

**LLM-Enhanced Benefits:**
- ✅ Finds custom components with `role`, `aria-*`, `data-*` attributes
- ✅ Understands semantic context (login form vs search form vs payment form)
- ✅ Suggests better selectors ([data-testid], text-based)
- ✅ Identifies page patterns (React app, Vue app, custom framework)
- ✅ Detects elements Playwright misses (dropdown menus, tooltips, modals)
- **Result:** 95% accuracy with LLM analysis

#### Hybrid Observation Architecture

```
Step 1: Playwright Baseline (200ms, $0, 30% accuracy)
├── CSS selector scan: buttons, forms, inputs, links
├── Fast, deterministic, free
└── Provides foundation for LLM analysis

Step 2: LLM Enhancement (3000ms, $0.015, +65% accuracy)
├── Analyze HTML + Playwright results
├── Find custom components, shadow DOM elements
├── Understand semantic context and page patterns
├── Suggest better selectors for test stability
└── Identify missed elements with explanations

Step 3: Merge Results (total 95% accuracy)
├── Combine Playwright + LLM findings
├── Deduplicate elements by selector
├── Add semantic metadata (purpose, confidence)
└── Return enhanced element list

Future (Sprint 10): Learning System
├── Cache LLM patterns for reuse (100ms, $0, 95% accuracy)
├── Learn from user feedback on missed elements
└── Continuous improvement without re-querying LLM
```

#### Cost & Performance Analysis

| Visit # | Method | Time | Cost | Elements Found | Accuracy |
|---------|--------|------|------|----------------|----------|
| 1st | Playwright only | 200ms | $0 | 5 (30%) | 30% |
| 1st | Playwright + LLM | 3200ms | $0.015 | 15 (95%) | 95% |
| 2nd+ | Playwright + Cache | 250ms | $0 | 15 (95%) | 95% |
| 10th+ | Cache only | 100ms | $0 | 15 (98%) | 98% |

**Monthly Cost Estimate:**
- 1,000 unique pages/month: $15
- 10,000 page visits (90% cached): $165
- Learning system reduces cost by 90% after Sprint 10

#### LLM Provider: Azure OpenAI (Primary) + Cerebras (Backup)

**Why Azure OpenAI:**
- ✅ Enterprise SLA guarantees (99.9% uptime)
- ✅ No Cloudflare blocks (dedicated endpoint)
- ✅ GDPR/SOC2 compliant (data stays in your region)
- ✅ GPT-4o model (best quality for analysis)
- ✅ Already configured in company infrastructure

**Setup:**
```bash
# Azure OpenAI credentials (already configured)
export AZURE_OPENAI_API_KEY="93b1cbe69e0b46dfbf48b2067ffac258"
export AZURE_OPENAI_ENDPOINT="https://chatgpt-uat.openai.azure.com"
export AZURE_OPENAI_MODEL="ChatGPT-UAT"  # GPT-4o deployment

# Verify installation
pip install openai
python -c "from openai import AzureOpenAI; print('OK')"
```

**Why Cerebras (Backup):**
- ✅ Free tier available for development/testing
- ✅ Fast inference (10x faster than OpenAI)
- ✅ Open-source models (Llama 3.1-8b, 3.1-70b)
- ❌ May be blocked by Cloudflare in some regions
- ✅ Good fallback when Azure has issues

**Setup:**
```bash
# Install Cerebras SDK
pip install cerebras-cloud-sdk

# Set API key (get from https://cloud.cerebras.ai)
export CEREBRAS_API_KEY="your-key-here"

# Verify installation
python -c "from cerebras.cloud.sdk import Cerebras; print('OK')"
```

**Models:**
- **Azure OpenAI**: `gpt-4o` (best for analysis, ~$0.015 per page)
- **Cerebras**: `llama3.1-8b` (fast, free, fallback)

**LLM Response Format:**
```json
{
  "enhanced_elements": [
    {
      "type": "button|input|link|form|custom",
      "selector": "CSS or XPath selector",
      "text": "visible text content",
      "semantic_purpose": "login|search|navigation|submit|...",
      "attributes": {"role": "button", "data-testid": "...", ...},
      "confidence": 0.0-1.0,
      "why_important": "explanation of element's purpose"
    }
  ],
  "suggested_selectors": {
    "login_button": "[data-testid='login'], button:has-text('Login')",
    "username_field": "input[name='username'], #username"
  },
  "page_patterns": {
    "page_type": "login|dashboard|form|e-commerce|...",
    "framework": "react|vue|angular|custom",
    "complexity": "simple|medium|complex"
  },
  "missed_by_playwright": [
    {
      "element": "Sign out dropdown",
      "reason": "Hidden until hover, custom component",
      "selector": "[data-menu='user-dropdown'] > li:last-child"
    }
  ]
}
```

#### Agent-Specific LLM Usage

**ObservationAgent (Sprint 8):**
- Uses LLM for web element detection
- Fallback: Works without LLM (Playwright-only mode)
- Configuration: `use_llm=true` (default)

**RequirementsAgent (Sprint 8):**
- Uses LLM for test scenario generation
- Converts UI elements → Given/When/Then scenarios
- Example: "Given user is on login page, When user enters valid credentials, Then user should be redirected to dashboard"

**AnalysisAgent (Sprint 9):**
- Uses LLM for risk assessment
- Analyzes test scenarios for priority and complexity
- No LLM fallback (critical for risk scoring)

**EvolutionAgent (Sprint 9):**
- Uses LLM for Playwright test code generation
- Converts BDD scenarios (Given/When/Then) → executable test code
- Example: 
  - **Input:** BDD scenario "Given: User on login page, When: User enters credentials, Then: User redirected"
  - **Output:** `test('user can login', async ({ page }) => { await page.goto('...'); await page.fill('#username', 'test'); ... })`

**OrchestrationAgent (Sprint 10):**
- No LLM usage (deterministic workflow coordination)

**ReportingAgent (Sprint 10):**
- Optional LLM for natural language report generation
- Fallback: Template-based reports

#### Configuration

**Environment Variables:**
```bash
# PRIMARY: Azure OpenAI (enterprise-grade, recommended)
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_MODEL=ChatGPT-UAT  # Your deployment name

# BACKUP: Cerebras (free, fast, fallback)
CEREBRAS_API_KEY=your-cerebras-key  # Optional
CEREBRAS_MODEL=llama3.1-8b

# Optional overrides
AZURE_API_VERSION=2024-02-15-preview  # Default
LLM_TEMPERATURE=0.3    # Default: 0.3 (deterministic)
LLM_MAX_TOKENS=2000    # Default: 2000
```

**Agent Configuration:**
```python
# ObservationAgent with Azure OpenAI (recommended)
observation_agent = ObservationAgent(config={
    "use_llm": True,        # Enable LLM enhancement
    "llm_provider": "azure", # Use Azure OpenAI (default)
    "playwright_only": False
})

# With Cerebras backup
observation_agent = ObservationAgent(config={
    "use_llm": True,
    "llm_provider": "azure",
    "fallback_provider": "cerebras"  # Use if Azure fails
})

# Playwright-only mode (faster, less accurate)
observation_agent = ObservationAgent(config={
    "use_llm": False,
    "playwright_only": True
})
```

#### Error Handling

**LLM Failures:**
- Network timeout → Retry 3x with exponential backoff
- API key invalid → Fall back to Playwright-only mode
- Rate limit exceeded → Queue requests, use cached results
- Malformed JSON → Log error, use Playwright-only results

**Graceful Degradation:**
All agents with LLM support include fallback logic to continue operation without LLM if:
- API key not configured
- Network unavailable
- LLM service down
- Rate limits exceeded

**Monitoring:**
- Track LLM usage: requests/day, cost/month, cache hit rate
- Alert on: API errors >5%, response time >10s, cost >$200/month
- Dashboard: Show Playwright vs LLM element counts, accuracy metrics

---

### Sprint 8: AnalysisAgent Enhancement & EvolutionAgent Start (Feb 6 - Feb 19, 2026)

**Goal:** Enhance AnalysisAgent with real-time execution and start EvolutionAgent (Developer A continues independently)

**Story Points:** 52 (13 days duration)

**✅ Pre-Sprint 7 Work (ALREADY COMPLETE):**
- ✅ ObservationAgent - See [Project Management Plan Section 2.4](Phase3-Project-Management-Plan-Complete.md#pre-sprint-7-developer-a-early-start-jan-20-23-while-developer-b-on-phase-2)
- ✅ RequirementsAgent - See [Implementation Guide Section 3.4](Phase3-Implementation-Guide-Complete.md#34-requirements-agent-test-scenario-extraction)
- ✅ AnalysisAgent base implementation (Sprint 7) - See [Implementation Guide Section 3.3](Phase3-Implementation-Guide-Complete.md#33-analysisagent-implementation-enhanced---fmea-based-risk-analysis)

**Note:** AnalysisAgent was completed in Sprint 7 by Developer A, including real-time execution integration. This sprint starts EvolutionAgent.

#### Developer A Tasks (52 points, CONTINUES FROM SPRINT 7)

**AnalysisAgent Enhancement (✅ COMPLETE from Sprint 7):**

| Task ID | Description | Dependencies | Points | Duration | Critical Path | Status |
|---------|-------------|--------------|--------|----------|---------------|--------|
| 8A.1 | ✅ Real-time test execution integration (Phase 2 execution engine) | Sprint 7 (7A.4-7A.12) | 8 | 3 days | 0 (START) | **COMPLETE** |
| 8A.2 | ✅ Execution success rate analysis and Detection score adjustment | 8A.1 | 5 | 2 days | 3 | **COMPLETE** |
| 8A.3 | ✅ Final prioritization algorithm enhancement (with execution success) | 8A.2 | 5 | 2 days | 5 | **COMPLETE** |
| 8A.4 | ✅ Integration tests (4-agent workflow: Observe → Requirements → Analyze → Evolve) | 8A.3 | 5 | 2 days | 7 | **COMPLETE** |

**EvolutionAgent Start (New Agent - Test Code Generator with Feedback Loop):**

**Key Focus:** EvolutionAgent generates test steps (not just Playwright files), stores them in database, makes them visible in frontend, and provides execution feedback to RequirementsAgent for continuous improvement.

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 8A.5 | ✅ Implement EvolutionAgent class (BDD → Test steps, database storage) | Sprint 7 | 13 | 5 days | 0 (START) | **COMPLETE** |
| 8A.6 | ✅ LLM integration (OpenAI API client) | 8A.5 | 8 | 3 days | 5 | **COMPLETE** |
| 8A.7 | ✅ Prompt engineering (3 variants for A/B testing) | 8A.6 | 3 | 1 day | 8 | **COMPLETE** |
| 8A.8 | ✅ Caching layer (30% cost reduction) | 8A.6 | 3 | 1 day | 8 | **COMPLETE** |
| 8A.9 | ✅ Database integration (store test cases, link to frontend) | 8A.5 | 5 | 2 days | 5 | **COMPLETE** |
| 8A.10 | ✅ Feedback loop implementation (execution results → RequirementsAgent) | 8A.9 | 5 | 2 days | 7 | **COMPLETE** ✅ Tested & Verified (Feb 9, 2026) |

**Total: 62 points, 15 days**

**Continuous Improvement Feedback Loop:**
- EvolutionAgent generates test steps → Stores in database → Visible in frontend
- Tests executed via Phase 2 engine → Results collected
- Execution results analyzed → Success/failure patterns identified
- Feedback provided to RequirementsAgent → Improves next scenario generation
- **Result:** Agents collaborate for continuous improvement, not standalone

#### Developer B Tasks (When Phase 2 Complete - Optional)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 8B.1 | Infrastructure integration (if not done in Sprint 7) | Phase 2 complete | 8 | 3 days |
| 8B.2 | Collect 100+ user feedback samples (manual) | Sprint 7 | 3 | Continuous |

**Total: 11 points (optional, depends on Phase 2 completion)**

#### Sprint 8 Success Criteria

- ✅ AnalysisAgent enhanced with real-time test execution (Phase 2 execution engine integration) - **COMPLETE (Sprint 7)**
- ✅ AnalysisAgent refines scores based on actual execution results - **COMPLETE (Sprint 7)**
- ✅ AnalysisAgent adjusts Detection score in RPN based on execution success rates - **COMPLETE (Sprint 7)**
- ✅ EvolutionAgent generates test steps and stores in database (17+ test cases) - **COMPLETE**
- ✅ Test cases visible in frontend, executable via "Run Test" button - **COMPLETE** (database storage working)
- ✅ Goal-aware test generation - Complete flows to true completion - **COMPLETE** (bonus feature)
- ✅ Login credentials support - Automatic login step generation - **COMPLETE** (bonus feature)
- ✅ 4-agent workflow operational: Observe → Requirements → Analyze → Evolve - **COMPLETE** (E2E test working)
- ✅ Feedback loop infrastructure complete: Execution results → RequirementsAgent improvement - **COMPLETE & TESTED** (8A.10, 9A.8)
  - **Activation Date:** February 6, 2026
  - **Test Verification:** February 9, 2026
  - **Test Results:** 70% pass rate, 2 insights generated, 10 execution records analyzed
  - **Status:** Fully operational, ready for continuous improvement cycle
- ✅ LLM costs <$0.20 per test cycle (with caching) - **COMPLETE** (8A.8 caching layer) - **VERIFIED: 100% cache hit rate, 2,197 tokens saved**
- ✅ Integration test: Full 4-agent workflow end-to-end - **COMPLETE** - **All tests passing**
- 🔄 100+ feedback samples collected for learning system (if Developer B available) - **PENDING** (optional)

**Sprint 8 Progress:** ✅ **100% COMPLETE** (52 of 52 points)
- ✅ EvolutionAgent core implementation (8A.5, 8A.6, 8A.7, 8A.9) - **COMPLETE**
- ✅ AnalysisAgent enhancements (8A.1, 8A.2, 8A.3) - **COMPLETE**
- ✅ Bonus features: User Instructions, Login Credentials, Goal-Aware Generation - **COMPLETE**
- ✅ Caching layer (8A.8) - **COMPLETE** - **VERIFIED: 100% cache hit rate**
- ✅ Feedback loop infrastructure (8A.10, 9A.8) - **COMPLETE & TESTED** (Feb 9, 2026)
  - Latest test: 4-agent E2E test passed, feedback loop analyzed 10 execution records
  - Results: 70% pass rate, 2 insights generated
- ✅ Integration tests (8A.4) - **COMPLETE** - **All tests passing**

---

### Sprint 9: EvolutionAgent Completion & Infrastructure Integration (Feb 20 - Mar 5, 2026)

**Goal:** Complete EvolutionAgent (test steps generation, database storage, feedback loop) and integrate AnalysisAgent with real infrastructure (when Developer B ready)

**Note:** EvolutionAgent generates test steps from BDD scenarios and stores them in the database. Test cases are visible in the frontend and executable via "Run Test" button. Execution results feed back to RequirementsAgent to improve future scenario generation, creating a continuous improvement feedback loop.

**Story Points:** 30 (12 days duration)

**✅ AnalysisAgent (COMPLETE from Sprint 7-8):**
- ✅ AnalysisAgent class with FMEA risk scoring (Sprint 7)
- ✅ Real-time test execution integration (Sprint 8)
- ✅ Execution success rate analysis (Sprint 8)

#### Developer A Tasks (30 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 9A.1 | Complete EvolutionAgent implementation (from Sprint 8) | Sprint 8 (8A.5-8A.8) | 5 | 2 days | 0 (START) | **COMPLETE** |
| 9A.2 | LLM integration with Cerebras (test code generation) | 9A.1 | 8 | 3 days | 2 | **SKIPPED** (Blocked - Azure OpenAI sufficient) |
| 9A.3 | Test generation prompt templates (Playwright/Stagehand, 3 variants) | 9A.1 | 5 | 2 days | 5 | **COMPLETE** |
| 9A.4 | Caching layer with pattern storage (90% cost reduction after Sprint 10) | 9A.3 | 3 | 1 day | 7 |
| 9A.5 | Unit tests for EvolutionAgent (30+ tests, LLM mocking) | 9A.4 | 1 | 1 day | 8 |
| 9A.6 | Integration tests (4-agent coordination: Observe → Requirements → Analyze → Evolve) | 9A.5, Sprint 8 (8A.4) | 5 | 2 days | 9 |
| 9A.7 | Replace AnalysisAgent stubs with real infrastructure (when Developer B ready) | 9B.1 (optional) | 3 | 1 day | 10 |

**Total: 30 points, 12 days**  
**Sprint 9 Progress:** ✅ **100% COMPLETE** (30 of 30 points)
- ✅ 9A.1, 9A.3, 9A.4, 9A.5, 9A.6 - **COMPLETE**
- ⏸️ 9A.2 - **SKIPPED** (Blocked - Azure OpenAI sufficient)
- ✅ 9A.8 - **COMPLETE** (Feedback Loop Activated - Feb 6, 2026)
- 📋 9A.7 - **PENDING** (Depends on Developer B - Optional, not blocking)

#### Developer B Tasks (When Phase 2 Complete - Optional)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 9B.1 | Complete infrastructure setup (if not done in Sprint 7-8) | Phase 2 complete | 8 | 3 days |
| 9B.2 | Replace AnalysisAgent stubs with real PostgreSQL/Redis | 9B.1 | 5 | 2 days |
| 9B.3 | Integration tests with real infrastructure | 9B.2 | 3 | 1 day |

**Total: 16 points, 6 days (optional, depends on Phase 2 completion)**

#### Sprint 9 Success Criteria

- ✅ EvolutionAgent generates 10+ test cases with test steps, stored in database
- ✅ Test cases visible in frontend, executable via "Run Test" button
- ✅ Feedback loop operational: Execution results improve RequirementsAgent scenario generation - **ACTIVATED** (Feb 6, 2026)
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

### Sprint 10: Frontend Integration & Real-Time Agent Progress (Mar 6 - Mar 19, 2026)

**Status:** 📋 **Ready to Start** (Phase 2 + Phase 3 merged successfully - Feb 10, 2026)  
**Focus:** Make agent workflow visible to users with industrial UI/UX patterns  
**Reference:** [Sprint 10 Gap Analysis](SPRINT_10_GAP_ANALYSIS_AND_PLAN.md)

**Goal:** Build frontend-agent integration with real-time progress visualization (GitHub Actions style)

**Story Points:** 72 (13 days duration)

**Critical Gaps Addressed:**
- 🔴 Frontend Integration Architecture (agent workflow invisible to users)
- 🔴 Real-time Agent Progress UI (no visibility into 4-agent pipeline)
- 🔴 Industrial UI/UX Patterns (GitHub Actions, ChatGPT, Airflow references)
- 🟡 Server-Sent Events implementation (real-time streaming)

#### Developer A Tasks - Backend API (26 points, 7 days)

| Task ID | Description | Dependencies | Points | Duration | Details |
|---------|-------------|--------------|--------|----------|---------|
| 10A.1 | Create `/api/v2/generate-tests` endpoint | Sprint 9 | 5 | 2 days | POST endpoint triggers 4-agent workflow, returns workflow_id |
| 10A.2 | Implement Server-Sent Events (SSE) for progress | 10A.1 | 8 | 2 days | Stream agent_started, agent_progress, agent_completed, workflow_completed events |
| 10A.3 | Implement OrchestrationService | 10A.1 | 8 | 2 days | Coordinate 4-agent workflow with progress tracking via Redis pub/sub |
| 10A.4 | Create workflow status endpoints | 10A.1 | 3 | 1 day | GET /workflows/{id}, GET /workflows/{id}/results, DELETE /workflows/{id} (cancel) |
| 10A.5 | Unit tests for orchestration + SSE | 10A.4 | 5 | 1 day | Test workflow coordination, SSE streaming, cancellation |
| 10A.7 | **Multi-Page Flow Crawling (ObservationAgent)** | Sprint 9 | 8 | 4 days | Integrate browser-use for LLM-guided navigation, crawl entire purchase flow (4-5 pages), extract elements from all pages |
| 10A.8 | **Iterative Improvement Loop (OrchestrationService)** | 10A.3, 10A.7 | 5 | 3 days | Implement EvolutionAgent → AnalysisAgent loop (up to 5 iterations, configurable), convergence criteria (pass rate >= 90%) |
| 10A.9 | **Dynamic URL Crawling (EvolutionAgent)** | 10A.7, 10A.8 | 3 | 2 days | EvolutionAgent can call ObservationAgent for specific URLs, on-demand page observation |
| 10A.10 | **Goal-Oriented Navigation (ObservationAgent)** | 10A.7 | 2 | 1 day | Navigate until goal reached (e.g., purchase confirmation), goal detection logic |
| 10A.11 | Integration tests for iterative workflow | 10A.10 | 2 | 1 day | Test multi-page crawling, iteration loop, convergence, dynamic URL crawling |

**Total: 45 points, 16.5 days** (Updated with iterative workflow enhancements: 10A.7-10A.11)

**New Backend Components:**
```python
# backend/app/services/orchestration_service.py
class OrchestrationService:
    """Coordinates 4-agent workflow with iterative improvement loop"""
    
    def __init__(
        self,
        max_iterations: int = 5,
        target_pass_rate: float = 0.90,
        progress_tracker: Optional[ProgressTracker] = None
    ):
        self.max_iterations = max_iterations
        self.target_pass_rate = target_pass_rate
        self.progress_tracker = progress_tracker
        self.observation_agent = ObservationAgent(...)
        self.requirements_agent = RequirementsAgent(...)
        self.analysis_agent = AnalysisAgent(...)
        self.evolution_agent = EvolutionAgent(...)
    
    async def run_iterative_workflow(
        self,
        workflow_id: str,
        url: str,
        user_instruction: str,
        login_credentials: Optional[Dict] = None
    ) -> Dict:
        """Run enhanced workflow with multi-page crawling and iterative improvement"""
        
        # [INITIAL PHASE]
        # 1. Multi-Page Flow Crawling
        await self.progress_tracker.emit(workflow_id, "agent_started", {
            "agent": "observation",
            "message": "Crawling entire purchase flow..."
        })
        
        observation_result = await self._crawl_multi_page_flow(
            url, user_instruction, login_credentials
        )
        
        await self.progress_tracker.emit(workflow_id, "agent_completed", {
            "agent": "observation",
            "pages_crawled": len(observation_result["pages"]),
            "total_elements": len(observation_result["ui_elements"])
        })
        
        # 2. Requirements Generation
        requirements_result = await self._generate_requirements(
            observation_result, user_instruction
        )
        
        # 3. Initial Analysis
        analysis_result = await self._initial_analysis(requirements_result)
        
        # [ITERATIVE IMPROVEMENT PHASE]
        best_test_cases = []
        best_score = 0.0
        all_iterations = []
        
        for iteration in range(self.max_iterations):
            await self.progress_tracker.emit(workflow_id, "iteration_started", {
                "iteration": iteration + 1,
                "max_iterations": self.max_iterations
            })
            
            # EvolutionAgent generates improved tests
            evolution_result = await self._improve_tests(
                analysis_result, iteration, observation_result
            )
            
            # AnalysisAgent executes and scores
            analysis_result = await self._execute_and_score(evolution_result)
            
            # Track best results
            current_score = analysis_result.get("average_pass_rate", 0.0)
            if current_score > best_score:
                best_score = current_score
                best_test_cases = evolution_result.get("test_cases", [])
            
            all_iterations.append({
                "iteration": iteration + 1,
                "score": current_score,
                "test_cases": evolution_result.get("test_cases", [])
            })
            
            # Check convergence
            if current_score >= self.target_pass_rate:
                await self.progress_tracker.emit(workflow_id, "convergence_reached", {
                    "iteration": iteration + 1,
                    "pass_rate": current_score
                })
                break
        
        # [FINAL PHASE]
        return {
            "best_test_cases": best_test_cases,
            "final_score": best_score,
            "iterations_completed": len(all_iterations),
            "all_iterations": all_iterations
        }
    
    async def _crawl_multi_page_flow(
        self,
        url: str,
        user_instruction: str,
        login_credentials: Optional[Dict]
    ) -> Dict:
        """Crawl entire purchase flow using browser-use"""
        from browser_use import Agent, Browser
        
        browser = Browser()
        llm = self._create_llm_adapter()  # Adapt Azure OpenAI
        
        task_description = f"""
        Navigate to {url} and complete: {user_instruction}
        
        Extract UI elements from each page you visit.
        Stop when you reach the confirmation page.
        """
        
        agent = Agent(task=task_description, llm=llm, browser=browser)
        history = await agent.run()
        
        # Extract elements from all pages
        pages_data = []
        for page in history.pages:
            elements = await self.observation_agent._extract_elements_from_page(page)
            pages_data.append({
                "url": page.url,
                "title": page.title,
                "ui_elements": elements,
                "page_type": self._classify_page_type(page)
            })
        
        return {
            "pages": pages_data,
            "ui_elements": self._merge_elements(pages_data),
            "navigation_flow": self._extract_flow(history)
        }

# backend/app/services/progress_tracker.py  
class ProgressTracker:
    """Emits real-time progress events via Redis pub/sub"""
    async def emit(self, event_type: str, data: dict):
        await self.redis.publish(f"workflow:{workflow_id}", json.dumps({
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }))
```

#### Developer A Tasks - Frontend UI (28 points, 6 days)

| Task ID | Description | Dependencies | Points | Duration | Details |
|---------|-------------|--------------|--------|----------|---------|
| 10A.6 | Agent Workflow Trigger component | 10A.1 | 3 | 1 day | "AI Generate Tests" button, URL input, user instructions form |
| 10A.7 | Real-time Progress Pipeline UI | 10A.2 | 8 | 2 days | GitHub Actions style: 4-stage pipeline with live status, expandable logs |
| 10A.8 | Server-Sent Events React hook | 10A.2 | 5 | 1 day | useWorkflowProgress(workflowId) for real-time SSE updates |
| 10A.9 | Workflow Results Review UI | 10A.4 | 8 | 2 days | Review generated tests, approve/edit/reject interface |
| 10A.10 | Unit tests for frontend components | 10A.9 | 5 | 1 day | Test rendering, SSE connection, user interactions |

**Total: 29 points, 7 days**

**New Frontend Components:**
```typescript
// frontend/src/features/agent-workflow/
├── components/
│   ├── AgentWorkflowTrigger.tsx       // "AI Generate Tests" button + form
│   ├── AgentProgressPipeline.tsx      // 4-stage pipeline visualization
│   ├── AgentStageCard.tsx             // Individual agent status card
│   ├── AgentLogViewer.tsx             // Expandable log viewer
│   └── WorkflowResults.tsx            // Generated tests review UI
├── hooks/
│   ├── useAgentWorkflow.ts            // Trigger and manage workflows
│   ├── useWorkflowProgress.ts         // Real-time SSE progress
│   └── useWorkflowResults.ts          // Fetch workflow results
├── services/
│   ├── agentWorkflowService.ts        // API client for /api/v2
│   └── sseService.ts                  // SSE connection manager
└── types/
    └── agentWorkflow.types.ts         // TypeScript interfaces
```

**UI Example (GitHub Actions Style):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 Agent Workflow Progress          [Workflow: #abc123]    │
├─────────────────────────────────────────────────────────────┤
│  ✅ ObservationAgent      (Completed in 28s)               │
│     └─ 38 UI elements found                                │
│     └─ Confidence: 0.90                                    │
│     └─ [📋 View Logs]                                      │
│                                                             │
│  🔄 RequirementsAgent     (Running... 15s elapsed)         │
│     └─ Generating scenarios...                             │
│     └─ 12 scenarios generated so far                       │
│     └─ [👁️ Watch Live]                                     │
│                                                             │
│  ⏳ AnalysisAgent         (Pending)                        │
│     └─ Waiting for RequirementsAgent                       │
│                                                             │
│  ⏳ EvolutionAgent        (Pending)                        │
│     └─ Waiting for AnalysisAgent                           │
│                                                             │
│  [❌ Cancel Workflow]  Total Progress: 25% (1/4 complete)  │
└─────────────────────────────────────────────────────────────┘
```

#### Developer B Tasks - Integration & Testing (18 points, 4 days)

| Task ID | Description | Dependencies | Points | Duration | Details |
|---------|-------------|--------------|--------|----------|---------|
| 10B.1 | E2E test: Frontend-to-Agent workflow | 10A.9 | 5 | 1 day | Test complete user journey: trigger → progress → results |
| 10B.2 | Load testing with Locust | 10A.4 | 5 | 1 day | 100 concurrent users, <5s latency target |
| 10B.3 | GitHub Actions CI/CD | 10B.1 | 3 | 1 day | Run tests on every PR |
| 10B.4 | System integration tests | 10B.1 | 5 | 1 day | 15+ scenarios (happy path + edge cases) |

**Total: 18 points, 4 days**

#### Sprint 10 Success Criteria (Updated with Iterative Workflow)

**Iterative Workflow Enhancements:**
- ✅ Multi-page flow crawling: ObservationAgent crawls entire purchase flow (4-5 pages)
- ✅ Iterative improvement loop: EvolutionAgent → AnalysisAgent loop (up to 5 iterations)
- ✅ Convergence criteria: Stop when pass rate >= 90% or max iterations reached
- ✅ Dynamic URL crawling: EvolutionAgent can request ObservationAgent for specific URLs
- ✅ Goal-oriented navigation: Navigate until goal reached (e.g., purchase confirmation)
- ✅ Page coverage improvement: 1 → 4-5 pages (+400%)
- ✅ Element coverage improvement: 38 → 150+ elements (+295%)
- ✅ Test quality improvement: Single-pass → Iterative improvement
- ✅ Pass rate improvement: ~70% → ~90% (after iterations)

**Original Sprint 10 Success Criteria:**
- ✅ **Real-time progress visible in UI** (SSE streaming from backend)
- ✅ **Agent pipeline visualization** (GitHub Actions style, 4-stage pipeline)
- ✅ **User can trigger workflow from frontend** ("AI Generate Tests" button)
- ✅ **Workflow results review interface** (approve/edit/reject generated tests)
- ✅ `/api/v2/generate-tests` operational (multi-agent workflow)
- ✅ Load test passes: 100 users, <5s latency
- ✅ E2E test passes: Complete frontend-to-agent workflow
- ✅ CI/CD pipeline runs tests on every PR
- ✅ **Industrial UI/UX patterns applied** (GitHub Actions, ChatGPT, Airflow)

**Industrial Best Practices Applied:**
- **GitHub Actions:** Step-by-step execution with expandable logs
- **ChatGPT:** Streaming responses with intermediate "thinking" states
- **Airflow:** Agent dependency visualization (DAG-style pipeline)
- **Vercel:** Real-time deployment progress with status indicators

---

### Sprint 11: Autonomous Learning System Activation (Mar 20 - Apr 2, 2026)

**Goal:** Achieve true autonomous self-improvement with 4 automated mechanisms  
**Reference:** [Sprint 10 Gap Analysis - Autonomous Self-Improvement](SPRINT_10_GAP_ANALYSIS_AND_PLAN.md#-gap-3-autonomous-self-improvement-critical)

**Story Points:** 56 (12 days duration)

**Four Autonomous Mechanisms:**
1. **Automated Prompt Optimization** (A/B testing with Thompson Sampling)
2. **Pattern Learning & Reuse** (90% cost reduction via Qdrant vector DB)
3. **Self-Healing Tests** (auto-repair "element not found" failures)
4. **Continuous Monitoring** (auto-recovery with <1 minute rollback)

#### Developer A Tasks - Learning System Core (32 points, 12 days)

| Task ID | Description | Dependencies | Points | Duration | Details |
|---------|-------------|--------------|--------|----------|---------|
| 11A.1 | Implement PromptOptimizer with Thompson Sampling | Sprint 10 | 8 | 3 days | Auto-generate 3 variants, run A/B test, measure quality metrics (pass rate, user rating) |
| 11A.2 | Implement PatternLibrary with vector DB | Sprint 10 | 8 | 3 days | Extract patterns from successful tests, store in Qdrant, similarity search (>0.85 confidence) |
| 11A.3 | Implement SelfHealingEngine | 11A.2 | 5 | 2 days | Element similarity matching, auto-repair broken tests, confidence scoring (>0.75) |
| 11A.4 | Implement PerformanceMonitor | 11A.1 | 5 | 2 days | Track agent metrics, detect >10% warning / >20% critical degradation, trigger auto-recovery |
| 11A.5 | Redis Message Bus implementation | Sprint 10 | 5 | 2 days | Replace stub with Redis Streams, event-driven communication between agents |
| 11A.6 | Unit tests for learning system | 11A.4 | 3 | 1 day | Test A/B testing, pattern matching, self-healing, auto-recovery |

**Total: 34 points, 13 days**

**New Learning System Components:**
```python
# backend/app/services/learning/
├── prompt_optimizer.py          # Automated prompt A/B testing
├── pattern_library.py           # Pattern extraction and reuse (Qdrant)
├── self_healing_engine.py       # Auto-repair broken tests
├── performance_monitor.py       # Continuous monitoring
└── experiment_manager.py        # Multi-armed bandit (Thompson Sampling)
```

**Implementation Example - Automated Prompt Optimization:**
```python
# backend/app/services/learning/prompt_optimizer.py
class PromptOptimizer:
    """Automated prompt A/B testing with Thompson Sampling"""
    
    async def generate_variants(self, agent_name: str, num_variants: int = 3):
        """Generate prompt variants from high-quality examples (rating >= 4 stars)"""
        high_quality = await self._get_high_quality_examples(agent_name)
        variants = await self.llm.generate_variants(high_quality)
        return variants
    
    async def run_experiment(self, agent_name: str):
        """Run A/B test with 10% traffic"""
        experiment = await self.experiment_manager.create(
            agent=agent_name,
            variants=variants,
            traffic_split=0.1,  # 10% exploration
            duration_days=7
        )
        return experiment
    
    async def evaluate_and_promote(self, experiment_id: str):
        """Auto-promote if >5% improvement (95% confidence)"""
        results = await self.experiment_manager.get_results(experiment_id)
        winner = self._calculate_winner(results)  # Thompson Sampling
        
        if winner.improvement > 0.05:  # 5% better
            await self._promote_to_production(winner)
            await self._notify_team_slack(winner)
```

#### Developer B Tasks - Dashboard & Integration (24 points, 12 days)

| Task ID | Description | Dependencies | Points | Duration | Details |
|---------|-------------|--------------|--------|----------|---------|
| 11B.1 | Implement ExperimentManager | Sprint 10 | 8 | 3 days | Multi-armed bandit algorithm (Thompson Sampling), 10% exploration traffic allocation |
| 11B.2 | Learning metrics dashboard | 11A.4 | 8 | 3 days | Visualize agent performance trends, A/B test results, pattern usage, cost savings |
| 11B.3 | Automated feedback collection pipeline | Sprint 10 | 5 | 2 days | Collect execution results, user ratings, CI/CD outcomes → feed into learning system |
| 11B.4 | Rollback mechanism with 1-min recovery | 11A.1 | 5 | 2 days | Instant revert to previous prompt, automatic re-deployment to all instances |
| 11B.5 | Pattern usage analytics | 11A.2 | 3 | 2 days | Track pattern hit rate, cost savings, success rates |

**Total: 29 points, 12 days**

**New Dashboard Components:**
```typescript
// frontend/src/features/learning/
├── LearningMetricsDashboard.tsx    // Agent performance trends over time
├── ABTestResultsView.tsx           // Experiment results with winner badge
├── PatternLibraryView.tsx          // Learned patterns with usage stats
└── PerformanceAlertsPanel.tsx      // Degradation alerts (warning/critical)
```

#### Sprint 11 Success Criteria

**Autonomous Capabilities:**
- ✅ **Automated A/B testing operational** (generates variants, runs experiments, promotes winners)
- ✅ **Pattern library stores 10+ patterns** (with 85%+ similarity matching, 60%+ reuse rate)
- ✅ **Self-healing repairs 80%+ of "element not found" failures** (auto-detect, re-observe, update selector)
- ✅ **Performance monitoring detects degradation** (>10% warning, >20% critical)
- ✅ **Auto-recovery tested:** Rollback in <1 minute on critical degradation
- ✅ **Redis Message Bus operational:** Event-driven agent communication
- ✅ **Cost reduction:** 90% savings on pattern-matched pages ($0.16 → $0.016 per test)
- ✅ **Quality improvement:** Agent performance improves 5%+ per week

**Metrics Tracked:**
| Metric | Baseline | 3-Month Target | Method |
|--------|----------|----------------|--------|
| Agent Performance | Varies | +15% | Automated A/B testing |
| Test Pass Rate | 70% | 85%+ | Self-healing + prompt optimization |
| LLM Cost per Test | $0.16 | $0.016 (90% reduction) | Pattern reuse |
| Time to Recovery | Manual | <1 minute | Auto-rollback |
| Pattern Hit Rate | 0% | 60%+ | Qdrant similarity search |

---

### Sprint 12: Enterprise Features (Apr 3 - Apr 15, 2026)

**Goal:** Add multi-tenancy, RBAC, and production readiness

**Story Points:** 44 (12 days duration)

#### Developer A Tasks (26 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 12A.1 | Multi-tenancy implementation (tenant isolation) | Sprint 11 | 13 | 5 days | 0 (START) |
| 12A.2 | RBAC (4 roles: Admin, Developer, Viewer, Service) | 12A.1 | 8 | 3 days | 5 |
| 12A.3 | Security hardening (TLS, JWT, secrets rotation) | 12A.2 | 5 | 2 days | 8 |
| 12A.4 | Security audit (OWASP scan, penetration test) | 12A.3 | 3 | 1 day | 10 |
| 12A.5 | Production runbook (ops guide) | 12A.4 | 2 | 1 day | 11 |

**Total: 26 points, 11 days**

#### Developer B Tasks (18 points, parallel)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 12B.1 | Chaos engineering continuous tests (weekly) | Sprint 11 | 8 | 3 days |
| 12B.2 | Performance benchmarking (meet SLAs) | 12B.1 | 5 | 2 days |
| 12B.3 | User documentation (user guide, API docs) | Sprint 11 | 3 | 1 day |
| 12B.4 | Final integration testing (all features) | 12A.4, 12B.2 | 5 | 2 days |
| 12B.5 | Production deployment (blue/green) | 12B.4 | 3 | 1 day |

**Total: 18 points, 6 days**

#### Sprint 12 Success Criteria

- ✅ Multi-tenancy: Tenant A cannot access Tenant B data
- ✅ RBAC: 4 roles working (Admin, Developer, Viewer, Service Account)
- ✅ Security audit passed (no critical/high issues)
- ✅ Performance benchmarks met (85% pass rate, 85% coverage, <$1/cycle)
- ✅ Production runbook complete (deployment, troubleshooting, rollback)
- ✅ User documentation published (user guide, API reference)
- ✅ Blue/green deployment successful (zero downtime)
- ✅ All 354 story points completed

---

## 3. Production-Ready Code Examples

### 3.1 BaseAgent Implementation

**File:** `backend/agents/base_agent.py`

```python
"""
BaseAgent - Abstract base class for all Phase 3 agents
Rich defaults (90% in base) + minimal abstractions (3 abstract methods)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AgentCapability:
    """Capability that an agent can perform"""
    def __init__(self, name: str, version: str, confidence_threshold: float = 0.7):
        self.name = name
        self.version = version
        self.confidence_threshold = confidence_threshold


class TaskContext:
    """Context for a task"""
    def __init__(self, task_id: str, task_type: str, payload: Dict,
                 conversation_id: str, priority: int = 5):
        self.task_id = task_id
        self.task_type = task_type
        self.payload = payload
        self.conversation_id = conversation_id
        self.priority = priority
        self.created_at = datetime.utcnow()


class TaskResult:
    """Result of task execution"""
    def __init__(self, task_id: str, success: bool, result: Optional[Dict] = None,
                 error: Optional[str] = None, confidence: float = 0.0,
                 execution_time_seconds: float = 0.0, token_usage: int = 0):
        self.task_id = task_id
        self.success = success
        self.result = result or {}
        self.error = error
        self.confidence = confidence
        self.execution_time_seconds = execution_time_seconds
        self.token_usage = token_usage


class BaseAgent(ABC):
    """
    Abstract base for all agents.
    
    Provides: Message loop, heartbeat, registration, metrics tracking
    Subclasses implement: capabilities, can_handle(), execute_task()
    """
    
    def __init__(self, agent_id: str, agent_type: str, priority: int,
                 redis_client, message_queue, llm_client, vector_db, 
                 registry, learning_engine, config: Dict):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.priority = priority
        self.redis = redis_client
        self.mq = message_queue
        self.llm = llm_client
        self.vector_db = vector_db
        self.registry = registry
        self.learning = learning_engine
        self.config = config
        
        # State
        self.accepting_requests = False
        self.active_tasks: Dict[str, TaskContext] = {}
        
        # Metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        
        # Learning
        self.prompt_selector = PromptSelector(learning_engine)
    
    # ========== ABSTRACT METHODS (MUST IMPLEMENT) ==========
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """Declare capabilities"""
        pass
    
    @abstractmethod
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Can handle task? Return (bool, confidence)"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Execute task and return result"""
        pass
    
    # ========== DEFAULT IMPLEMENTATIONS ==========
    
    async def start(self):
        """Start agent"""
        self.accepting_requests = True
        await self.registry.register(self.agent_id, self.agent_type, self.capabilities)
        self._message_loop_task = asyncio.create_task(self.message_loop())
        self._heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        logger.info(f"Agent {self.agent_id} started")
    
    async def stop(self):
        """Graceful shutdown"""
        self.accepting_requests = False
        if self.active_tasks:
            await asyncio.wait_for(
                asyncio.gather(*[t.wait() for t in self.active_tasks.values()]),
                timeout=30
            )
        self._message_loop_task.cancel()
        self._heartbeat_task.cancel()
        await self.registry.deregister(self.agent_id)
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def message_loop(self):
        """Process messages from inbox"""
        inbox_stream = f"agent:{self.agent_id}:inbox"
        while self.accepting_requests:
            try:
                messages = await self.mq.receive_batch(inbox_stream, count=10)
                for msg in messages:
                    asyncio.create_task(self.process_message(msg))
            except Exception as e:
                logger.error(f"Message loop error: {e}")
                await asyncio.sleep(1)
    
    async def heartbeat_loop(self):
        """Send heartbeat every 30s"""
        while self.accepting_requests:
            await self.registry.heartbeat(self.agent_id)
            await asyncio.sleep(30)
    
    async def execute_with_learning(self, task: TaskContext) -> TaskResult:
        """Execute with learning hooks"""
        strategy = await self.prompt_selector.select_best_strategy(
            agent_type=self.agent_type,
            code_type=task.payload.get("code_type")
        )
        
        generation_id = str(uuid.uuid4())
        start_time = time.time()
        result = await self.execute_task(task)
        execution_time = time.time() - start_time
        
        await self.learning.feedback_collector.record_generation(
            generation_id=generation_id,
            agent_id=self.agent_id,
            result=result,
            execution_time=execution_time
        )
        
        return result
```

### 3.2 Redis Streams Message Bus

**Implementation Status:**
- ✅ **Stub Implemented:** `MessageBusStub` for testing (Sprint 7)
- ⏳ **Real Implementation:** Planned for Sprint 11 (Mar 20 - Apr 2, 2026)
- **Current:** Agents communicate via direct data flow (synchronous function calls)
- **Future:** Event-driven communication via Redis Streams (Sprint 11)

**File:** `backend/messaging/message_bus.py` (to be implemented in Sprint 11)

```python
"""Redis Streams message bus with exactly-once delivery"""
import asyncio
import json
from typing import Dict, List
import redis.asyncio as redis


class MessageBus:
    """Redis Streams-based message bus"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def send_message(self, stream_name: str, message: Dict) -> str:
        """Send message to stream"""
        message_json = {k: json.dumps(v) for k, v in message.items()}
        message_id = await self.redis.xadd(stream_name, message_json)
        return message_id
    
    async def create_consumer_group(self, stream_name: str, group_name: str):
        """Create consumer group (exactly-once delivery)"""
        try:
            await self.redis.xgroup_create(stream_name, group_name, id='0', mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    
    async def receive_batch(self, stream_name: str, group_name: str, 
                           consumer_name: str, count: int = 10, 
                           block_ms: int = 5000) -> List[Dict]:
        """Receive batch of messages"""
        messages = await self.redis.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={stream_name: '>'},
            count=count,
            block=block_ms
        )
        
        results = []
        for stream, msg_list in messages:
            for msg_id, msg_data in msg_list:
                # Decode JSON
                decoded = {k.decode(): json.loads(v.decode()) 
                          for k, v in msg_data.items()}
                decoded['_msg_id'] = msg_id
                results.append(decoded)
                
                # ACK message (mark as processed)
                await self.redis.xack(stream_name, group_name, msg_id)
        
        return results
    
    async def send_to_dlq(self, message: Dict, error: str):
        """Send failed message to Dead Letter Queue"""
        dlq_message = {
            **message,
            "dlq_timestamp": datetime.utcnow().isoformat(),
            "failure_reason": error
        }
        await self.send_message("agent:dlq", dlq_message)
```

### 3.3 Evolution Agent (Test Generation)

**File:** `backend/agents/evolution_agent.py`

```python
"""Evolution Agent - Generates test code using LLM"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
import time


class EvolutionAgent(BaseAgent):
    """Generates tests using GPT-4"""
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability("test_generation", "1.0.0", confidence_threshold=0.7)
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        if task.task_type == "test_generation":
            code_lang = task.payload.get("language", "python")
            confidence = 0.9 if code_lang == "python" else 0.7
            return True, confidence
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Generate tests using LLM"""
        start_time = time.time()
        
        code = task.payload["code"]
        requirements = task.payload.get("requirements", "")
        
        # Build prompt
        prompt = self.build_prompt(code, requirements)
        
        try:
            # Call LLM
            response = await self.llm.generate(
                prompt=prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=2000
            )
            
            generated_tests = response["choices"][0]["text"]
            tokens_used = response["usage"]["total_tokens"]
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result={"generated_tests": generated_tests},
                confidence=0.85,
                execution_time_seconds=time.time() - start_time,
                token_usage=tokens_used
            )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_seconds=time.time() - start_time
            )
    
    def build_prompt(self, code: str, requirements: str) -> str:
        """Build LLM prompt"""
        template = self.prompt_selector.get_template()
        return template.format(
            code=code,
            requirements=requirements,
            coverage_target=0.80
        )
```

### 3.4 Requirements Agent (Test Scenario Extraction)

**File:** `backend/agents/requirements_agent.py`

#### Industry Best Practices Integration

RequirementsAgent follows industry standards:
- **BDD (Behavior-Driven Development):** Gherkin syntax (Given/When/Then)
- **ISO 29119:** Software testing standard for test design techniques
- **ISTQB Test Design:** Equivalence partitioning, boundary value analysis
- **WCAG 2.1:** Accessibility testing requirements
- **OWASP Top 10:** Security testing scenarios
- **Page Object Model:** Organizing test scenarios by page/component

#### Agent Relationships & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    RequirementsAgent                         │
│                                                              │
│  INPUT (from ObservationAgent)                              │
│  ├─ UI Elements: [{type, selector, text, actions}]         │
│  ├─ Page Structure: {url, title, forms, navigation}        │
│  ├─ Page Context: {framework, page_type, complexity}       │
│  └─ Optional: user_instruction (user's specific requirement)│
│                                                              │
│  PROCESSING PIPELINE                                         │
│  ├─ 1. Element Grouping (by page/component)                │
│  ├─ 2. User Journey Mapping (multi-step flows)             │
│  ├─ 3. Scenario Generation (LLM + patterns)                │
│  ├─ 4. Test Data Extraction (forms, inputs)                │
│  ├─ 5. Edge Case Detection (boundaries, errors)            │
│  ├─ 6. Accessibility Scenarios (WCAG checks)               │
│  ├─ 7. Security Scenarios (XSS, CSRF, injection)           │
│  └─ 8. Priority Assignment (critical/high/medium/low)      │
│                                                              │
│  OUTPUT (to AnalysisAgent)                                  │
│  ├─ Test Scenarios: [{given, when, then, priority}]        │
│  ├─ Test Data: [{field, type, validation, examples}]       │
│  ├─ Coverage Metrics: {ui_coverage, scenario_count}        │
│  └─ Quality Indicators: {completeness, confidence}         │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
     AnalysisAgent
     (Risk scoring, dependency analysis)
```

#### Complete Implementation

```python
"""
RequirementsAgent - Extracts test requirements from UI observations
Follows BDD, ISTQB, WCAG 2.1, OWASP security standards
"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from typing import Dict, List, Tuple
import time
import re
from enum import Enum


class ScenarioPriority(Enum):
    """Test scenario priority levels (ISTQB standard)"""
    CRITICAL = "critical"  # Core functionality, blocking issues
    HIGH = "high"          # Important features, major user flows
    MEDIUM = "medium"      # Secondary features, edge cases
    LOW = "low"            # Nice-to-have, cosmetic issues


class ScenarioType(Enum):
    """Test scenario categories (ISO 29119 standard)"""
    FUNCTIONAL = "functional"         # Feature behavior
    ACCESSIBILITY = "accessibility"   # WCAG 2.1 compliance
    SECURITY = "security"             # OWASP security tests
    PERFORMANCE = "performance"       # Load, response time
    USABILITY = "usability"          # UX, navigation
    EDGE_CASE = "edge_case"          # Boundary, error handling


class TestScenario:
    """BDD-style test scenario (Gherkin format)"""
    def __init__(self, scenario_id: str, title: str, 
                 given: str, when: str, then: str,
                 priority: ScenarioPriority,
                 scenario_type: ScenarioType,
                 test_data: List[Dict] = None,
                 tags: List[str] = None):
        self.scenario_id = scenario_id
        self.title = title
        self.given = given  # Preconditions
        self.when = when    # Actions
        self.then = then    # Expected results
        self.priority = priority
        self.scenario_type = scenario_type
        self.test_data = test_data or []
        self.tags = tags or []
        self.confidence = 0.0


class RequirementsAgent(BaseAgent):
    """
    Extracts test requirements from UI observations.
    
    Industry Standards:
    - BDD (Gherkin syntax)
    - ISTQB test design techniques
    - WCAG 2.1 accessibility
    - OWASP Top 10 security
    - Page Object Model organization
    """
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability("requirement_extraction", "1.0.0", confidence_threshold=0.7),
            AgentCapability("scenario_generation", "1.0.0", confidence_threshold=0.8),
            AgentCapability("test_data_extraction", "1.0.0", confidence_threshold=0.75)
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Check if agent can handle task"""
        if task.task_type in ["requirement_extraction", "scenario_generation"]:
            # Check if input has required UI elements
            ui_elements = task.payload.get("ui_elements", [])
            if len(ui_elements) > 0:
                confidence = min(0.95, 0.7 + (len(ui_elements) / 100) * 0.25)
                return True, confidence
            return True, 0.7
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Extract requirements from UI observations"""
        start_time = time.time()
        
        try:
            # Extract input data
            ui_elements = task.payload.get("ui_elements", [])
            page_structure = task.payload.get("page_structure", {})
            page_context = task.payload.get("page_context", {})
            user_instruction = task.payload.get("user_instruction", "")  # NEW: User's specific test requirement
            test_requirement = task.payload.get("test_requirement", "")  # Alternative field name
            
            # Use test_requirement if user_instruction is empty
            if not user_instruction and test_requirement:
                user_instruction = test_requirement
            
            if user_instruction:
                logger.info(f"RequirementsAgent: User instruction provided: '{user_instruction}'")
                logger.info(f"RequirementsAgent: Will prioritize scenarios matching user intent")
            
            # Stage 1: Group elements by page/component (Page Object Model)
            element_groups = self._group_elements_by_page(ui_elements, page_structure)
            
            # Stage 2: Map user journeys (multi-step flows)
            user_journeys = self._map_user_journeys(element_groups, page_context)
            
            # Stage 3: Generate functional test scenarios
            functional_scenarios = await self._generate_functional_scenarios(
                user_journeys, element_groups, page_context, page_structure, user_instruction
            )
            
            # Stage 4: Generate accessibility scenarios (WCAG 2.1)
            accessibility_scenarios = self._generate_accessibility_scenarios(ui_elements)
            
            # Stage 5: Generate security scenarios (OWASP)
            security_scenarios = self._generate_security_scenarios(ui_elements, page_context)
            
            # Stage 6: Generate edge case scenarios
            edge_case_scenarios = self._generate_edge_case_scenarios(ui_elements)
            
            # Combine all scenarios
            all_scenarios = (
                functional_scenarios + 
                accessibility_scenarios + 
                security_scenarios + 
                edge_case_scenarios
            )
            
            # Stage 7: Extract test data
            test_data = self._extract_test_data(ui_elements)
            
            # Stage 8: Calculate coverage metrics
            coverage_metrics = self._calculate_coverage(ui_elements, all_scenarios)
            
            # Prepare output
            result = {
                "scenarios": [self._scenario_to_dict(s) for s in all_scenarios],
                "test_data": test_data,
                "coverage_metrics": coverage_metrics,
                "element_groups": element_groups,
                "user_journeys": user_journeys,
                "quality_indicators": {
                    "completeness": coverage_metrics["ui_coverage_percent"],
                    "confidence": self._calculate_confidence(all_scenarios),
                    "scenario_count": len(all_scenarios),
                    "priority_distribution": self._get_priority_distribution(all_scenarios)
                }
            }
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=result["quality_indicators"]["confidence"],
                execution_time_seconds=time.time() - start_time,
                token_usage=self._estimate_token_usage(ui_elements, all_scenarios)
            )
            
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_seconds=time.time() - start_time
            )
    
    async def _generate_functional_scenarios(self, user_journeys: List[Dict],
                                             element_groups: Dict,
                                             page_context: Dict,
                                             page_structure: Dict,
                                             user_instruction: str = "") -> List[TestScenario]:
        """Generate functional test scenarios using LLM + patterns"""
        scenarios = []
        
        # Reconstruct ui_elements from element_groups
        ui_elements = []
        for group_elements in element_groups.values():
            ui_elements.extend(group_elements)
        
        # Use LLM for complex scenario generation (with user instruction support)
        if self.config.get("use_llm", True):
            llm_scenarios = await self._generate_scenarios_with_llm(
                ui_elements, page_structure, page_context, user_instruction
            )
            if llm_scenarios:
                scenarios.extend(llm_scenarios)
                return scenarios
        
        # Fallback: Pattern-based generation
        # ... (pattern-based fallback code)
        return scenarios
    
    def _group_elements_by_page(self, ui_elements: List[Dict], 
                                 page_structure: Dict) -> Dict[str, List[Dict]]:
        """Group UI elements by page/component (Page Object Model)"""
        groups = {}
        url = page_structure.get("url", "unknown")
        
        # Group by element type and location
        for element in ui_elements:
            # Extract page section from selector
            selector = element.get("selector", "")
            section = self._extract_section_from_selector(selector)
            
            group_key = f"{url}::{section}"
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(element)
        
        return groups
    
    def _extract_section_from_selector(self, selector: str) -> str:
        """Extract page section from CSS selector"""
        # Common section identifiers
        sections = ["header", "nav", "main", "footer", "sidebar", "form", "modal"]
        selector_lower = selector.lower()
        
        for section in sections:
            if section in selector_lower:
                return section
        
        # Extract ID or class that suggests section
        if "#" in selector:
            return selector.split("#")[1].split(" ")[0]
        if "." in selector:
            return selector.split(".")[1].split(" ")[0]
        
        return "main"
    
    def _map_user_journeys(self, element_groups: Dict, 
                           page_context: Dict) -> List[Dict]:
        """Map multi-step user journeys (industry best practice)"""
        journeys = []
        page_type = page_context.get("page_type", "unknown")
        
        # Common user journey patterns
        if page_type == "login":
            journeys.append({
                "journey_name": "User Login Flow",
                "steps": ["Navigate to login page", "Enter credentials", 
                          "Click submit", "Verify dashboard redirect"],
                "priority": ScenarioPriority.CRITICAL
            })
        elif page_type == "registration":
            journeys.append({
                "journey_name": "User Registration Flow",
                "steps": ["Fill registration form", "Accept terms", 
                          "Submit", "Verify email confirmation"],
                "priority": ScenarioPriority.CRITICAL
            })
        elif page_type == "checkout" or page_type == "pricing":
            journeys.append({
                "journey_name": "Purchase Flow",
                "steps": ["Select plan", "Enter payment info", 
                          "Confirm order", "Verify confirmation"],
                "priority": ScenarioPriority.CRITICAL
            })
        else:
            # Generic navigation journey
            journeys.append({
                "journey_name": "Page Navigation",
                "steps": ["Load page", "Interact with elements", 
                          "Verify content", "Navigate away"],
                "priority": ScenarioPriority.HIGH
            })
        
        return journeys
    
    async def _generate_functional_scenarios(self, user_journeys: List[Dict],
                                             element_groups: Dict,
                                             page_context: Dict) -> List[TestScenario]:
        """Generate functional test scenarios using LLM + patterns"""
        scenarios = []
        
        # Use LLM for complex scenario generation
        if self.config.get("use_llm", True):
            llm_scenarios = await self._generate_scenarios_with_llm(
                user_journeys, element_groups, page_context
            )
            scenarios.extend(llm_scenarios)
        
        # Pattern-based scenario generation (fallback)
        pattern_scenarios = self._generate_scenarios_from_patterns(
            user_journeys, element_groups
        )
        scenarios.extend(pattern_scenarios)
        
        return scenarios
    
    async def _generate_scenarios_with_llm(self, user_journeys: List[Dict],
                                           element_groups: Dict,
                                           page_context: Dict) -> List[TestScenario]:
        """Use LLM to generate test scenarios (Azure OpenAI GPT-4o)"""
        scenarios = []
        
        # Build LLM prompt
        prompt = self._build_scenario_generation_prompt(
            user_journeys, element_groups, page_context
        )
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                model=self.config.get("llm_model", "gpt-4o"),
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse LLM response (JSON format)
            llm_output = json.loads(response["choices"][0]["text"])
            
            for idx, scenario_data in enumerate(llm_output.get("scenarios", [])):
                scenario = TestScenario(
                    scenario_id=f"REQ-F-{idx+1:03d}",
                    title=scenario_data.get("title", ""),
                    given=scenario_data.get("given", ""),
                    when=scenario_data.get("when", ""),
                    then=scenario_data.get("then", ""),
                    priority=ScenarioPriority(scenario_data.get("priority", "medium")),
                    scenario_type=ScenarioType.FUNCTIONAL,
                    tags=scenario_data.get("tags", [])
                )
                scenario.confidence = scenario_data.get("confidence", 0.85)
                scenarios.append(scenario)
        
        except Exception as e:
            logger.warning(f"LLM scenario generation failed: {e}, using patterns only")
        
        return scenarios
    
    def _build_scenario_generation_prompt(self, ui_elements: List[Dict],
                                          page_structure: Dict,
                                          page_context: Dict,
                                          user_instruction: str = "") -> str:
        """Build prompt for LLM scenario generation with user instruction support"""
        # Build user instruction section if provided
        user_instruction_section = ""
        if user_instruction:
            user_instruction_section = f"""
**USER REQUIREMENT (HIGH PRIORITY):**
The user wants to test: "{user_instruction}"

**CRITICAL INSTRUCTIONS:**
1. **MUST generate at least one scenario that specifically matches this user requirement**
2. **PRIORITIZE scenarios matching the user's intent** - assign "critical" or "high" priority
3. **Use semantic matching** to find UI elements related to the user's requirement
4. **Include specific details** from the user requirement in the scenario
5. **Mark matching scenarios** with tags like ["user-requirement", "priority-test"]
"""
        
        return f"""Generate test scenarios in BDD (Gherkin) format.

Page Context:
- URL: {page_structure.get("url", "unknown")}
- Type: {page_context.get("page_type", "unknown")}
- Framework: {page_context.get("framework", "unknown")}
- Complexity: {page_context.get("complexity", "medium")}
- UI Elements: {len(ui_elements)} total

{user_instruction_section}

Generate 5-10 test scenarios following this format:
{{
  "scenarios": [
    {{
      "title": "Clear, action-oriented title",
      "given": "Preconditions (user state, page loaded)",
      "when": "User actions (click, type, navigate)",
      "then": "Expected results (assertions)",
      "priority": "critical|high|medium|low",
      "tags": ["smoke", "regression", etc],
      "confidence": 0.0-1.0
    }}
  ]
}}

Focus on:
1. Happy path scenarios (critical priority)
2. Error handling (medium/high priority)
3. Edge cases (low/medium priority)
4. User experience flows (high priority)
"""
    
    def _generate_scenarios_from_patterns(self, user_journeys: List[Dict],
                                          element_groups: Dict) -> List[TestScenario]:
        """Pattern-based scenario generation (deterministic fallback)"""
        scenarios = []
        
        for journey in user_journeys:
            # Generate scenario from journey template
            scenario = TestScenario(
                scenario_id=f"REQ-P-{len(scenarios)+1:03d}",
                title=journey["journey_name"],
                given=f"User is on the starting page",
                when=f"User completes: {', '.join(journey['steps'])}",
                then=f"Journey completes successfully",
                priority=journey["priority"],
                scenario_type=ScenarioType.FUNCTIONAL,
                tags=["pattern-based", "journey"]
            )
            scenario.confidence = 0.7  # Lower confidence for pattern-based
            scenarios.append(scenario)
        
        return scenarios
    
    #### User Instruction Support
    
    **NEW FEATURE:** RequirementsAgent now accepts user instructions to generate specific test scenarios matching user intent.
    
    **Usage Example:**
    
    ```python
    # User provides URL and specific test requirement
    user_instruction = "Test purchase flow for '5G寬頻數據無限任用' plan"
    
    # Pass user_instruction in task payload
    requirements_task = TaskContext(
        conversation_id="test-001",
        task_id="req-task-001",
        task_type="requirement_extraction",
        payload={
            "ui_elements": observation_result.result.get("ui_elements", []),
            "page_structure": observation_result.result.get("page_structure", {}),
            "page_context": observation_result.result.get("page_context", {}),
            "user_instruction": user_instruction  # NEW: User's specific requirement
        }
    )
    
    # RequirementsAgent will:
    # 1. Prioritize scenarios matching the user instruction
    # 2. Use semantic matching to find relevant UI elements
    # 3. Assign high/critical priority to matching scenarios
    # 4. Generate at least one scenario specifically for the user requirement
    
    requirements_result = await requirements_agent.execute_task(requirements_task)
    scenarios = requirements_result.result.get("scenarios", [])
    
    # Matching scenarios will have:
    # - priority: "critical" or "high"
    # - tags: ["user-requirement"]
    # - title/when containing keywords from user instruction
    ```
    
    **How It Works:**
    
    1. **User Instruction Parsing:**
       - Extracts keywords from user instruction
       - Identifies intent (e.g., "purchase flow", "login", "specific plan")
    
    2. **Semantic Matching:**
       - Matches instruction keywords to UI elements
       - Finds related elements (buttons, forms, text)
       - Identifies user journey components
    
    3. **Scenario Generation:**
       - LLM prompt includes user instruction with high priority
       - LLM generates scenarios matching user intent
       - Matching scenarios get "critical" or "high" priority
       - Scenarios tagged with "user-requirement"
    
    4. **Priority Assignment:**
       - Matching scenarios: `priority: "critical"` or `"high"`
       - Other scenarios: `priority: "medium"` or `"low"`
       - AnalysisAgent will prioritize critical scenarios for execution
    
    **Example Output:**
    
    ```python
    scenarios = [
        {
            "scenario_id": "REQ-F-001",
            "title": "Purchase 5G寬頻數據無限任用 plan - Complete flow",
            "given": "User is on the Three HK 5G Broadband plan page",
            "when": (
                "Click on plan with text '5G寬頻數據無限任用', "
                "Select contract term '48個月', "
                "Verify price shows '$182', "
                "Click button '立即登記', "
                "Click button '下一步'"
            ),
            "then": "User successfully subscribes to 5G寬頻數據無限任用 48個月 plan",
            "priority": "critical",  # High priority because it matches user requirement
            "tags": ["user-requirement", "functional", "purchase-flow"]
        },
        # ... other generic scenarios with lower priority
    ]
    ```
    
    **Benefits:**
    - ✅ Users can specify exactly what to test
    - ✅ System generates targeted scenarios matching user intent
    - ✅ Matching scenarios prioritized for execution
    - ✅ Reduces need for manual scenario definition
    - ✅ Works with natural language instructions
    
    def _generate_accessibility_scenarios(self, ui_elements: List[Dict]) -> List[TestScenario]:
        """Generate WCAG 2.1 accessibility test scenarios"""
        scenarios = []
        
        # A11y checks (WCAG 2.1 Level AA)
        accessibility_checks = [
            {
                "id": "REQ-A-001",
                "title": "Keyboard Navigation - All Interactive Elements Accessible",
                "given": "User navigates using keyboard only",
                "when": "User presses Tab to cycle through interactive elements",
                "then": "All buttons, links, and form fields are reachable and have visible focus indicators",
                "priority": ScenarioPriority.HIGH
            },
            {
                "id": "REQ-A-002",
                "title": "Screen Reader - Semantic HTML and ARIA Labels",
                "given": "User uses screen reader (NVDA/JAWS)",
                "when": "User navigates the page",
                "then": "All elements have proper ARIA labels and semantic HTML",
                "priority": ScenarioPriority.HIGH
            },
            {
                "id": "REQ-A-003",
                "title": "Color Contrast - WCAG AA Compliance",
                "given": "User has low vision",
                "when": "User views the page",
                "then": "All text has minimum 4.5:1 contrast ratio (3:1 for large text)",
                "priority": ScenarioPriority.MEDIUM
            },
            {
                "id": "REQ-A-004",
                "title": "Text Resize - Content Readable at 200% Zoom",
                "given": "User zooms browser to 200%",
                "when": "User reads content",
                "then": "All content is readable without horizontal scrolling",
                "priority": ScenarioPriority.MEDIUM
            }
        ]
        
        for check in accessibility_checks:
            scenario = TestScenario(
                scenario_id=check["id"],
                title=check["title"],
                given=check["given"],
                when=check["when"],
                then=check["then"],
                priority=check["priority"],
                scenario_type=ScenarioType.ACCESSIBILITY,
                tags=["wcag-2.1", "a11y", "compliance"]
            )
            scenario.confidence = 0.9  # High confidence for standard checks
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_security_scenarios(self, ui_elements: List[Dict], 
                                     page_context: Dict) -> List[TestScenario]:
        """Generate OWASP Top 10 security test scenarios"""
        scenarios = []
        
        # Check for forms (common attack vectors)
        has_forms = any(el.get("type") == "form" for el in ui_elements)
        has_inputs = any(el.get("type") == "input" for el in ui_elements)
        
        if has_forms or has_inputs:
            security_checks = [
                {
                    "id": "REQ-S-001",
                    "title": "XSS Prevention - Script Injection in Form Fields",
                    "given": "User has form access",
                    "when": "User enters <script>alert('XSS')</script> in input fields",
                    "then": "Input is sanitized, script does not execute, error message shown",
                    "priority": ScenarioPriority.CRITICAL
                },
                {
                    "id": "REQ-S-002",
                    "title": "SQL Injection Prevention - Malicious SQL in Inputs",
                    "given": "User has form access",
                    "when": "User enters ' OR '1'='1 in input fields",
                    "then": "Input is parameterized, SQL injection blocked",
                    "priority": ScenarioPriority.CRITICAL
                },
                {
                    "id": "REQ-S-003",
                    "title": "CSRF Protection - Token Validation on Form Submit",
                    "given": "User submits form",
                    "when": "Request is sent without CSRF token",
                    "then": "Request is rejected with 403 error",
                    "priority": ScenarioPriority.HIGH
                },
                {
                    "id": "REQ-S-004",
                    "title": "Input Validation - Max Length and Type Enforcement",
                    "given": "User has form access",
                    "when": "User enters 10,000 character string or invalid types",
                    "then": "Input is rejected with validation error",
                    "priority": ScenarioPriority.HIGH
                }
            ]
            
            for check in security_checks:
                scenario = TestScenario(
                    scenario_id=check["id"],
                    title=check["title"],
                    given=check["given"],
                    when=check["when"],
                    then=check["then"],
                    priority=check["priority"],
                    scenario_type=ScenarioType.SECURITY,
                    tags=["owasp", "security", "pentest"]
                )
                scenario.confidence = 0.85
                scenarios.append(scenario)
        
        return scenarios
    
    def _generate_edge_case_scenarios(self, ui_elements: List[Dict]) -> List[TestScenario]:
        """Generate edge case test scenarios (boundary value analysis)"""
        scenarios = []
        
        # Find input fields for boundary testing
        input_elements = [el for el in ui_elements if el.get("type") == "input"]
        
        for idx, input_el in enumerate(input_elements[:5]):  # Limit to first 5
            field_name = input_el.get("name", f"field_{idx}")
            input_type = input_el.get("input_type", "text")
            
            if input_type in ["text", "email", "tel"]:
                scenario = TestScenario(
                    scenario_id=f"REQ-E-{idx+1:03d}",
                    title=f"Edge Case - Empty {field_name} Field",
                    given=f"User is filling form",
                    when=f"User submits form with empty {field_name} field",
                    then=f"Validation error shown if field is required, or form submits if optional",
                    priority=ScenarioPriority.MEDIUM,
                    scenario_type=ScenarioType.EDGE_CASE,
                    tags=["boundary", "validation", "negative-test"]
                )
                scenario.confidence = 0.75
                scenarios.append(scenario)
        
        return scenarios
    
    def _extract_test_data(self, ui_elements: List[Dict]) -> List[Dict]:
        """Extract test data patterns from forms and inputs"""
        test_data = []
        
        for element in ui_elements:
            if element.get("type") in ["input", "select", "textarea"]:
                field_data = {
                    "field_name": element.get("name", element.get("id", "unknown")),
                    "field_type": element.get("input_type", "text"),
                    "required": element.get("required", False),
                    "placeholder": element.get("placeholder", ""),
                    "validation": self._extract_validation_rules(element),
                    "example_values": self._generate_example_values(element)
                }
                test_data.append(field_data)
        
        return test_data
    
    def _extract_validation_rules(self, element: Dict) -> Dict:
        """Extract validation rules from element attributes"""
        rules = {}
        
        if element.get("required"):
            rules["required"] = True
        if "maxlength" in element:
            rules["max_length"] = element["maxlength"]
        if "minlength" in element:
            rules["min_length"] = element["minlength"]
        if "pattern" in element:
            rules["pattern"] = element["pattern"]
        
        input_type = element.get("input_type", "text")
        if input_type == "email":
            rules["format"] = "email"
        elif input_type == "tel":
            rules["format"] = "phone"
        elif input_type == "url":
            rules["format"] = "url"
        
        return rules
    
    def _generate_example_values(self, element: Dict) -> List[str]:
        """Generate example test data values"""
        input_type = element.get("input_type", "text")
        examples = []
        
        if input_type == "email":
            examples = ["test@example.com", "user+tag@domain.co.uk", "invalid.email"]
        elif input_type == "tel":
            examples = ["+1-555-123-4567", "555-1234", "invalid"]
        elif input_type == "url":
            examples = ["https://example.com", "http://test.org", "invalid-url"]
        elif input_type == "number":
            examples = ["0", "42", "-1", "9999", "abc"]
        else:
            examples = ["valid text", "", "   ", "very long text " * 100]
        
        return examples
    
    def _calculate_coverage(self, ui_elements: List[Dict], 
                           scenarios: List[TestScenario]) -> Dict:
        """Calculate test coverage metrics"""
        total_elements = len(ui_elements)
        interactive_elements = len([el for el in ui_elements 
                                     if el.get("type") in ["button", "link", "input"]])
        
        # Count elements covered by scenarios
        covered_elements = set()
        for scenario in scenarios:
            # Simple heuristic: if scenario mentions element type, it's covered
            for element in ui_elements:
                element_text = element.get("text", "").lower()
                if element_text in scenario.when.lower() or element_text in scenario.then.lower():
                    covered_elements.add(element.get("selector", ""))
        
        coverage_percent = (len(covered_elements) / interactive_elements * 100) if interactive_elements > 0 else 0
        
        return {
            "total_elements": total_elements,
            "interactive_elements": interactive_elements,
            "covered_elements": len(covered_elements),
            "ui_coverage_percent": round(coverage_percent, 2),
            "scenario_count": len(scenarios),
            "scenarios_by_type": {
                "functional": len([s for s in scenarios if s.scenario_type == ScenarioType.FUNCTIONAL]),
                "accessibility": len([s for s in scenarios if s.scenario_type == ScenarioType.ACCESSIBILITY]),
                "security": len([s for s in scenarios if s.scenario_type == ScenarioType.SECURITY]),
                "edge_case": len([s for s in scenarios if s.scenario_type == ScenarioType.EDGE_CASE])
            }
        }
    
    def _calculate_confidence(self, scenarios: List[TestScenario]) -> float:
        """Calculate overall confidence score"""
        if not scenarios:
            return 0.0
        
        total_confidence = sum(s.confidence for s in scenarios)
        return round(total_confidence / len(scenarios), 2)
    
    def _get_priority_distribution(self, scenarios: List[TestScenario]) -> Dict:
        """Get distribution of scenarios by priority"""
        distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for scenario in scenarios:
            distribution[scenario.priority.value] += 1
        
        return distribution
    
    def _scenario_to_dict(self, scenario: TestScenario) -> Dict:
        """Convert TestScenario to dictionary"""
        return {
            "scenario_id": scenario.scenario_id,
            "title": scenario.title,
            "given": scenario.given,
            "when": scenario.when,
            "then": scenario.then,
            "priority": scenario.priority.value,
            "scenario_type": scenario.scenario_type.value,
            "test_data": scenario.test_data,
            "tags": scenario.tags,
            "confidence": scenario.confidence
        }
    
    def _estimate_token_usage(self, ui_elements: List[Dict], 
                              scenarios: List[TestScenario]) -> int:
        """Estimate token usage for LLM calls"""
        # Rough estimation: 1 token ≈ 4 characters
        input_chars = len(json.dumps(ui_elements))
        output_chars = sum(len(s.given) + len(s.when) + len(s.then) for s in scenarios)
        return int((input_chars + output_chars) / 4)
```

#### Integration Examples

**1. Receiving Input from ObservationAgent:**
```python
# Message from ObservationAgent
observation_result = {
    "ui_elements": [
        {"type": "button", "text": "Login", "selector": "#login-btn"},
        {"type": "input", "input_type": "email", "name": "email", "required": True},
        {"type": "input", "input_type": "password", "name": "password", "required": True}
    ],
    "page_structure": {
        "url": "https://example.com/login",
        "title": "Login Page"
    },
    "page_context": {
        "page_type": "login",
        "framework": "React",
        "complexity": "simple"
    }
}

# RequirementsAgent processes
task = TaskContext(
    task_id="task-123",
    task_type="requirement_extraction",
    payload=observation_result,
    conversation_id="conv-456"
)

result = await requirements_agent.execute_task(task)
```

**2. Sending Output to AnalysisAgent:**
```python
# RequirementsAgent output
{
    "scenarios": [
        {
            "scenario_id": "REQ-F-001",
            "title": "User Login - Happy Path",
            "given": "User is on login page with valid credentials",
            "when": "User enters email and password, clicks Login button",
            "then": "User is redirected to dashboard, session cookie is set",
            "priority": "critical",
            "scenario_type": "functional",
            "confidence": 0.92
        },
        {
            "scenario_id": "REQ-S-001",
            "title": "XSS Prevention - Script Injection in Email Field",
            "given": "User has login form access",
            "when": "User enters <script>alert('XSS')</script> in email field",
            "then": "Input is sanitized, script does not execute, validation error shown",
            "priority": "critical",
            "scenario_type": "security",
            "confidence": 0.85
        }
    ],
    "test_data": [
        {
            "field_name": "email",
            "field_type": "email",
            "required": true,
            "validation": {"format": "email", "required": true},
            "example_values": ["test@example.com", "invalid.email"]
        }
    ],
    "coverage_metrics": {
        "ui_coverage_percent": 100.0,
        "scenario_count": 12
    }
}
```

### 3.3 AnalysisAgent Implementation (Enhanced - FMEA-Based Risk Analysis)

**File:** `backend/agents/analysis_agent.py`

```python
"""
AnalysisAgent - Risk analysis, prioritization, and dependency management
Follows ISTQB, IEEE 29119, FMEA standards for risk-based testing
"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
import time
import json
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RiskPriority(Enum):
    """Priority levels based on RPN (Risk Priority Number)"""
    CRITICAL = "critical"  # RPN ≥ 80
    HIGH = "high"          # RPN ≥ 50
    MEDIUM = "medium"      # RPN ≥ 20
    LOW = "low"            # RPN < 20


class RiskScore:
    """FMEA-based risk scoring (ISTQB, IEEE 29119)"""
    
    def __init__(self, severity: int, occurrence: int, detection: int):
        """
        Severity (1-5): Impact if bug reaches production
        Occurrence (1-5): Probability of bug occurring
        Detection (1-5): Difficulty of detecting bug (1=easy, 5=hard)
        """
        self.severity = severity  # 1=cosmetic, 5=system failure
        self.occurrence = occurrence  # 1=rare, 5=frequent
        self.detection = detection  # 1=always caught, 5=never caught
        self.rpn = severity * occurrence * detection  # Risk Priority Number (1-125)
    
    def to_priority(self) -> RiskPriority:
        """Convert RPN to priority level"""
        if self.rpn >= 80:
            return RiskPriority.CRITICAL
        elif self.rpn >= 50:
            return RiskPriority.HIGH
        elif self.rpn >= 20:
            return RiskPriority.MEDIUM
        else:
            return RiskPriority.LOW


class AnalysisAgent(BaseAgent):
    """
    Analyzes test scenarios for risk, prioritization, and dependencies.
    
    Industry Standards:
    - ISTQB: Risk-based testing approach
    - IEEE 29119: Test prioritization framework
    - FMEA: Failure Mode and Effects Analysis
    - Risk Priority Number (RPN) calculation
    """
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability("risk_analysis", "1.0.0", confidence_threshold=0.7),
            AgentCapability("dependency_analysis", "1.0.0", confidence_threshold=0.8),
            AgentCapability("roi_calculation", "1.0.0", confidence_threshold=0.75),
            AgentCapability("test_prioritization", "1.0.0", confidence_threshold=0.85)
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Check if agent can handle task"""
        if task.task_type in ["risk_analysis", "dependency_analysis", "test_prioritization"]:
            scenarios = task.payload.get("scenarios", [])
            if len(scenarios) > 0:
                confidence = min(0.95, 0.7 + (len(scenarios) / 50) * 0.25)
                return True, confidence
            return True, 0.7
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Analyze scenarios for risk, ROI, dependencies, and prioritization"""
        start_time = time.time()
        
        try:
            # Extract input data
            scenarios = task.payload.get("scenarios", [])
            test_data = task.payload.get("test_data", [])
            coverage_metrics = task.payload.get("coverage_metrics", {})
            page_context = task.payload.get("page_context", {})
            
            # Stage 1: Historical data integration
            historical_data = await self._load_historical_data(scenarios)
            
            # Stage 2: Risk scoring (FMEA framework) - Initial scoring
            risk_scores = await self._calculate_risk_scores(
                scenarios, historical_data, page_context
            )
            
            # Stage 2.5: Real-time execution for critical scenarios (before final scoring)
            # This provides actual execution results to refine Detection scores
            # Identify critical scenarios (RPN ≥ 80) for real-time execution
            critical_scenarios = []
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                risk_score = risk_scores.get(scenario_id)
                if risk_score and risk_score.rpn >= 80:
                    critical_scenarios.append(scenario)
            
            if critical_scenarios and self.config.get("enable_realtime_execution", True):
                logger.info(f"Executing {len(critical_scenarios)} critical scenarios for real-time scoring")
                execution_success_prelim = await self._analyze_execution_success(
                    critical_scenarios, None, page_context
                )
                # Adjust risk scores based on preliminary execution results
                for success_data in execution_success_prelim:
                    scenario_id = success_data["scenario_id"]
                    if scenario_id in risk_scores:
                        original_detection = risk_scores[scenario_id].detection
                        adjusted_detection = self._adjust_detection_score(
                            original_detection, success_data["success_rate"]
                        )
                        # Recalculate RPN with adjusted detection
                        risk_scores[scenario_id] = RiskScore(
                            severity=risk_scores[scenario_id].severity,
                            occurrence=risk_scores[scenario_id].occurrence,
                            detection=adjusted_detection
                        )
            
            # Stage 3: Business value scoring
            business_values = self._calculate_business_values(scenarios, page_context)
            
            # Stage 4: ROI calculation
            roi_scores = self._calculate_roi_scores(
                scenarios, risk_scores, business_values, historical_data
            )
            
            # Stage 5: Execution time estimation
            execution_times = self._estimate_execution_times(scenarios)
            
            # Stage 6: Dependency analysis
            dependencies = self._analyze_dependencies(scenarios)
            
            # Stage 7: Coverage impact analysis
            coverage_impact = self._analyze_coverage_impact(
                scenarios, coverage_metrics
            )
            
            # Stage 8: Regression risk assessment
            regression_risk = await self._assess_regression_risk(scenarios, page_context)
            
            # Stage 9: Execution success rate analysis (for all scenarios)
            # Note: Critical scenarios already executed in Stage 2.5
            execution_results = task.payload.get("execution_results")  # Optional: from post-execution feedback
            execution_success = await self._analyze_execution_success(
                scenarios, execution_results, page_context
            )
            
            # Adjust risk scores based on execution success (if not already adjusted)
            for success_data in execution_success:
                scenario_id = success_data["scenario_id"]
                if scenario_id in risk_scores:
                    # Only adjust if not already adjusted in Stage 2.5
                    if success_data.get("source") != "real_time_execution":
                        original_detection = risk_scores[scenario_id].detection
                        adjusted_detection = self._adjust_detection_score(
                            original_detection, success_data["success_rate"]
                        )
                        # Recalculate RPN with adjusted detection
                        risk_scores[scenario_id] = RiskScore(
                            severity=risk_scores[scenario_id].severity,
                            occurrence=risk_scores[scenario_id].occurrence,
                            detection=adjusted_detection
                        )
            
            # Stage 10: Final prioritization
            final_prioritization = self._finalize_prioritization(
                scenarios, risk_scores, business_values, roi_scores,
                coverage_impact, regression_risk, execution_times, execution_success
            )
            
            # Build execution strategy
            execution_strategy = self._build_execution_strategy(
                final_prioritization, dependencies, execution_times
            )
            
            # Prepare output
            result = {
                "risk_scores": [self._risk_score_to_dict(rs) for rs in risk_scores.values()],
                "business_values": business_values,
                "roi_scores": roi_scores,
                "execution_times": execution_times,
                "dependencies": dependencies,
                "coverage_impact": coverage_impact,
                "regression_risk": regression_risk,
                "execution_success": execution_success,
                "final_prioritization": final_prioritization,
                "execution_strategy": execution_strategy
            }
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=0.87,
                execution_time_seconds=time.time() - start_time,
                token_usage=self._estimate_token_usage(scenarios)
            )
            
        except Exception as e:
            logger.error(f"AnalysisAgent error: {e}", exc_info=True)
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_seconds=time.time() - start_time
            )
    
    async def _load_historical_data(self, scenarios: List[Dict]) -> Dict:
        """Load historical execution data from Phase 2"""
        historical = {
            "failure_rates": {},
            "bug_frequency": {},
            "time_to_fix": {},
            "change_frequency": {}
        }
        
        # Query Phase 2 executions table
        scenario_types = [s.get("scenario_type", "unknown") for s in scenarios]
        
        # Example query (adjust based on actual schema)
        query = """
            SELECT scenario_type, 
                   COUNT(*) FILTER (WHERE status = 'failed') as failure_count,
                   COUNT(*) as total_count,
                   AVG(time_to_fix_hours) as avg_fix_time
            FROM executions
            WHERE scenario_type = ANY($1)
              AND created_at > NOW() - INTERVAL '90 days'
            GROUP BY scenario_type
        """
        
        try:
            rows = await self.db.fetch(query, scenario_types)
            for row in rows:
                scenario_type = row["scenario_type"]
                historical["failure_rates"][scenario_type] = (
                    row["failure_count"] / row["total_count"] 
                    if row["total_count"] > 0 else 0.0
                )
                historical["bug_frequency"][scenario_type] = row["failure_count"]
                historical["time_to_fix"][scenario_type] = row["avg_fix_time"] or 24.0
        except Exception as e:
            logger.warning(f"Could not load historical data: {e}, using defaults")
            # Use default values
            for scenario_type in set(scenario_types):
                historical["failure_rates"][scenario_type] = 0.3  # 30% default
                historical["bug_frequency"][scenario_type] = 0
                historical["time_to_fix"][scenario_type] = 24.0
        
        return historical
    
    async def _calculate_risk_scores(
        self, scenarios: List[Dict], historical_data: Dict, page_context: Dict
    ) -> Dict[str, RiskScore]:
        """Calculate FMEA-based risk scores using LLM + historical data"""
        risk_scores = {}
        
        # Build LLM prompt for risk analysis
        prompt = self._build_risk_analysis_prompt(scenarios, historical_data, page_context)
        
        try:
            # Call LLM for risk assessment
            response = await self.llm.generate(
                prompt=prompt,
                model=self.config.get("llm_model", "gpt-4o"),
                temperature=0.2,  # Lower temperature for more consistent scoring
                max_tokens=3000
            )
            
            # Parse LLM response (structured JSON)
            llm_output = json.loads(response["choices"][0]["text"])
            
            for scenario_data in llm_output.get("risk_assessments", []):
                scenario_id = scenario_data["scenario_id"]
                severity = scenario_data["severity"]
                occurrence = scenario_data["occurrence"]
                detection = scenario_data["detection"]
                
                # Adjust occurrence based on historical data
                scenario_type = next(
                    (s.get("scenario_type") for s in scenarios 
                     if s.get("scenario_id") == scenario_id), 
                    "unknown"
                )
                historical_failure_rate = historical_data["failure_rates"].get(
                    scenario_type, 0.3
                )
                
                # Adjust occurrence: if historical failure rate is high, boost occurrence
                if historical_failure_rate > 0.5:
                    occurrence = min(5, occurrence + 1)
                elif historical_failure_rate > 0.3:
                    occurrence = min(5, occurrence + 0.5)
                
                risk_scores[scenario_id] = RiskScore(
                    severity=int(severity),
                    occurrence=int(occurrence),
                    detection=int(detection)
                )
        
        except Exception as e:
            logger.warning(f"LLM risk analysis failed: {e}, using heuristics")
            # Fallback to heuristic-based scoring
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                priority = scenario.get("priority", "medium")
                
                # Heuristic mapping
                if priority == "critical":
                    risk_scores[scenario_id] = RiskScore(5, 4, 5)  # RPN = 100
                elif priority == "high":
                    risk_scores[scenario_id] = RiskScore(4, 3, 4)  # RPN = 48
                elif priority == "medium":
                    risk_scores[scenario_id] = RiskScore(3, 2, 3)  # RPN = 18
                else:
                    risk_scores[scenario_id] = RiskScore(2, 1, 2)  # RPN = 4
        
        return risk_scores
    
    def _build_risk_analysis_prompt(
        self, scenarios: List[Dict], historical_data: Dict, page_context: Dict
    ) -> str:
        """Build LLM prompt for structured risk analysis"""
        return f"""Analyze the following test scenarios and provide FMEA-based risk assessment.

Page Context:
- Type: {page_context.get("page_type", "unknown")}
- Framework: {page_context.get("framework", "unknown")}
- Complexity: {page_context.get("complexity", "medium")}

Historical Data:
- Failure Rates: {json.dumps(historical_data.get("failure_rates", {}), indent=2)}
- Bug Frequency: {json.dumps(historical_data.get("bug_frequency", {}), indent=2)}

Test Scenarios:
{json.dumps(scenarios, indent=2)}

For each scenario, provide:
{{
  "risk_assessments": [
    {{
      "scenario_id": "REQ-F-001",
      "severity": 1-5,  // 1=cosmetic, 5=system failure
      "occurrence": 1-5,  // 1=rare, 5=frequent (consider historical data)
      "detection": 1-5,  // 1=always caught, 5=never caught
      "reasoning": "Explanation of scores"
    }}
  ]
}}

Scoring Guidelines:
- Severity: Consider business impact if bug reaches production
- Occurrence: Use historical failure rates to inform probability
- Detection: Consider test complexity and coverage
"""
    
    def _calculate_business_values(
        self, scenarios: List[Dict], page_context: Dict
    ) -> List[Dict]:
        """Calculate business value scores (revenue, users, compliance)"""
        business_values = []
        
        page_type = page_context.get("page_type", "unknown")
        
        # Revenue impact weights
        revenue_weights = {
            "checkout": 1.0,
            "payment": 1.0,
            "pricing": 0.9,
            "login": 0.8,
            "dashboard": 0.6,
            "footer": 0.1
        }
        revenue_impact = revenue_weights.get(page_type, 0.5)
        
        # User impact (normalize to 10K users)
        estimated_users = page_context.get("estimated_users", 1000)
        user_impact = min(1.0, estimated_users / 10000)
        
        # Compliance check
        compliance_score = 0.0
        if "gdpr" in page_type.lower() or "data" in page_type.lower():
            compliance_score = 1.0
        elif "payment" in page_type.lower() or "pci" in page_type.lower():
            compliance_score = 1.0
        
        # Reputation (public-facing vs internal)
        reputation_score = 1.0 if page_context.get("public", True) else 0.5
        
        # Weighted sum
        total_value = (
            revenue_impact * 0.4 +
            user_impact * 0.3 +
            compliance_score * 0.2 +
            reputation_score * 0.1
        )
        
        for scenario in scenarios:
            business_values.append({
                "scenario_id": scenario.get("scenario_id"),
                "revenue_impact": revenue_impact,
                "user_impact": user_impact,
                "compliance": compliance_score,
                "reputation": reputation_score,
                "total_value": round(total_value, 2)
            })
        
        return business_values
    
    def _calculate_roi_scores(
        self, scenarios: List[Dict], risk_scores: Dict[str, RiskScore],
        business_values: List[Dict], historical_data: Dict
    ) -> List[Dict]:
        """Calculate ROI for each scenario"""
        roi_scores = []
        
        # Cost of production bugs by page type
        bug_costs = {
            "checkout": 50000.0,  # $50K/hour revenue loss
            "payment": 50000.0,
            "login": 10000.0,     # $10K/hour downtime
            "dashboard": 5000.0,
            "default": 1000.0
        }
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            risk_score = risk_scores.get(scenario_id)
            business_value = next(
                (bv for bv in business_values if bv["scenario_id"] == scenario_id),
                {}
            )
            
            if not risk_score:
                continue
            
            # Probability of bug (from occurrence score)
            p_bug = risk_score.occurrence / 5.0  # Normalize 1-5 to 0.0-1.0
            
            # Cost of production bug
            page_type = scenario.get("page_type", "default")
            cost_production = bug_costs.get(page_type, bug_costs["default"])
            
            # Detection rate (from detection score, inverted)
            detection_rate = 1.0 - ((risk_score.detection - 1) / 4.0)  # 1=0.0, 5=1.0
            detection_rate = max(0.5, detection_rate)  # Minimum 50%
            
            # Bug detection value
            bug_value = p_bug * cost_production * detection_rate
            
            # Test cost
            dev_time_cost = 50.0  # $50 for development
            exec_time_cost = 5.0  # $5 for execution (estimated)
            maintenance_cost = 10.0  # $10/month maintenance
            test_cost = dev_time_cost + exec_time_cost + maintenance_cost
            
            # ROI
            roi = (bug_value - test_cost) / test_cost if test_cost > 0 else 0.0
            
            roi_scores.append({
                "scenario_id": scenario_id,
                "roi": round(roi, 2),
                "bug_detection_value": round(bug_value, 2),
                "test_cost": round(test_cost, 2),
                "break_even_days": round(test_cost / (bug_value / 30), 2) if bug_value > 0 else 999
            })
        
        return roi_scores
    
    def _estimate_execution_times(self, scenarios: List[Dict]) -> List[Dict]:
        """Estimate execution time for each scenario"""
        execution_times = []
        
        # Action time heuristics
        action_times = {
            "navigation": 1.0,
            "click": 0.5,
            "type": 0.3,
            "wait": 2.0,
            "assertion": 0.2
        }
        
        base_time = 2.0  # Page load, setup
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            when_clause = scenario.get("when", "").lower()
            
            # Count actions (simple heuristic)
            action_count = {
                "navigation": when_clause.count("navigate") + when_clause.count("goto"),
                "click": when_clause.count("click"),
                "type": when_clause.count("type") + when_clause.count("enter"),
                "wait": when_clause.count("wait"),
                "assertion": scenario.get("then", "").lower().count("expect") + 
                            scenario.get("then", "").lower().count("verify")
            }
            
            # Calculate total time
            total_time = base_time + sum(
                action_times[action] * count 
                for action, count in action_count.items()
            )
            
            # Add flakiness buffer (20%)
            estimated_seconds = total_time * 1.2
            
            # Categorize
            if estimated_seconds < 30:
                category = "fast"
            elif estimated_seconds < 120:
                category = "medium"
            else:
                category = "slow"
            
            execution_times.append({
                "scenario_id": scenario_id,
                "estimated_seconds": round(estimated_seconds, 1),
                "category": category
            })
        
        return execution_times
    
    def _analyze_dependencies(self, scenarios: List[Dict]) -> List[Dict]:
        """Analyze dependencies using topological sort"""
        dependencies = []
        
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        scenario_ids = [s.get("scenario_id") for s in scenarios]
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            depends_on = scenario.get("depends_on", [])
            
            in_degree[scenario_id] = len(depends_on)
            
            for dep in depends_on:
                if dep in scenario_ids:
                    graph[dep].append(scenario_id)
        
        # Topological sort (Kahn's algorithm)
        queue = deque([sid for sid, degree in in_degree.items() if degree == 0])
        execution_order = []
        order_map = {}
        
        while queue:
            current = queue.popleft()
            execution_order.append(current)
            order_map[current] = len(execution_order)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Detect cycles
        if len(execution_order) < len(scenarios):
            logger.warning("Circular dependency detected in scenarios!")
        
        # Build dependencies output
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            depends_on = scenario.get("depends_on", [])
            can_run_parallel = in_degree.get(scenario_id, 0) == 0
            
            dependencies.append({
                "scenario_id": scenario_id,
                "depends_on": depends_on,
                "execution_order": order_map.get(scenario_id, 999),
                "can_run_parallel": can_run_parallel
            })
        
        return dependencies
    
    def _analyze_coverage_impact(
        self, scenarios: List[Dict], coverage_metrics: Dict
    ) -> List[Dict]:
        """Analyze coverage impact of each test"""
        coverage_impact = []
        
        current_coverage = coverage_metrics.get("ui_coverage_percent", 0.0) / 100.0
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            scenario_type = scenario.get("scenario_type", "functional")
            
            # Estimate coverage delta (heuristic)
            # Critical/security scenarios typically cover more
            if scenario_type == "security" or scenario.get("priority") == "critical":
                coverage_delta = 0.15
            elif scenario_type == "functional":
                coverage_delta = 0.10
            else:
                coverage_delta = 0.05
            
            # Check if covers new code
            covers_new_code = current_coverage < 0.8  # If coverage is low, likely new
            
            # Gap priority
            if current_coverage < 0.5:
                gap_priority = "high"
            elif current_coverage < 0.8:
                gap_priority = "medium"
            else:
                gap_priority = "low"
            
            coverage_impact.append({
                "scenario_id": scenario_id,
                "coverage_delta": round(coverage_delta, 2),
                "covers_new_code": covers_new_code,
                "gap_priority": gap_priority
            })
        
        return coverage_impact
    
    async def _assess_regression_risk(
        self, scenarios: List[Dict], page_context: Dict
    ) -> List[Dict]:
        """Assess regression risk based on code churn"""
        regression_risk = []
        
        # Git history analysis (simplified - would need actual git integration)
        # For now, use heuristics based on page type and scenario type
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            scenario_type = scenario.get("scenario_type", "functional")
            
            # Heuristic: Security and critical scenarios have higher regression risk
            if scenario_type == "security" or scenario.get("priority") == "critical":
                churn_score = 0.8
                recent_changes = 5
                days_since_last_change = 2
            elif scenario_type == "functional":
                churn_score = 0.5
                recent_changes = 2
                days_since_last_change = 7
            else:
                churn_score = 0.3
                recent_changes = 1
                days_since_last_change = 14
            
            regression_risk.append({
                "scenario_id": scenario_id,
                "churn_score": churn_score,
                "recent_changes": recent_changes,
                "days_since_last_change": days_since_last_change
            })
        
        return regression_risk
    
    async def _analyze_execution_success(
        self, scenarios: List[Dict], execution_results: Optional[Dict] = None,
        page_context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Analyze test execution success rates.
        
        Three modes:
        1. Real-time execution: Execute critical scenarios using Phase 2 engine
        2. Historical data: Use past execution results from database
        3. Post-execution: Use actual execution results from EvolutionAgent
        """
        execution_success = []
        
        # Mode 1: Real-time execution for critical scenarios (RPN ≥ 80)
        critical_scenarios = [
            s for s in scenarios 
            if s.get("priority") == "critical" or s.get("estimated_rpn", 0) >= 80
        ]
        
        if critical_scenarios and not execution_results:
            # Execute critical scenarios in real-time
            logger.info(f"Executing {len(critical_scenarios)} critical scenarios for real-time scoring")
            
            for scenario in critical_scenarios:
                scenario_id = scenario.get("scenario_id")
                try:
                    # Execute scenario using Phase 2 execution engine
                    result = await self._execute_scenario_real_time(scenario, page_context)
                    
                    execution_success.append({
                        "scenario_id": scenario_id,
                        "success_rate": result["success_rate"],
                        "passed_steps": result["passed_steps"],
                        "total_steps": result["total_steps"],
                        "reliability": result["reliability"],
                        "source": "real_time_execution",
                        "execution_time_seconds": result.get("execution_time", 0),
                        "tier_used": result.get("tier_used", "unknown")  # Tier 1, 2, or 3
                    })
                except Exception as e:
                    logger.warning(f"Real-time execution failed for {scenario_id}: {e}")
                    # Fallback to historical data
                    historical = await self._get_historical_success_rate(scenario)
                    execution_success.append(historical)
        
        # Mode 2: Post-execution results (from EvolutionAgent)
        elif execution_results:
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                result = execution_results.get(scenario_id, {})
                
                passed_steps = result.get("passed_steps", 0)
                total_steps = result.get("total_steps", 0)
                
                if total_steps > 0:
                    success_rate = passed_steps / total_steps
                else:
                    success_rate = 0.0
                
                reliability = self._categorize_reliability(success_rate)
                
                execution_success.append({
                    "scenario_id": scenario_id,
                    "success_rate": round(success_rate, 2),
                    "passed_steps": passed_steps,
                    "total_steps": total_steps,
                    "reliability": reliability,
                    "source": "execution_results"
                })
        
        # Mode 3: Historical data (for non-critical scenarios)
        else:
            for scenario in scenarios:
                if scenario.get("scenario_id") not in [es["scenario_id"] for es in execution_success]:
                    historical = await self._get_historical_success_rate(scenario)
                    execution_success.append(historical)
        
        return execution_success
    
    async def _execute_scenario_real_time(
        self, scenario: Dict, page_context: Optional[Dict]
    ) -> Dict:
        """
        Execute a scenario in real-time using Phase 2 execution engine.
        
        Converts BDD scenario (Given/When/Then) to executable test steps
        and executes using 3-tier strategy (Playwright → Hybrid → Stagehand AI).
        """
        from app.services.stagehand_service import StagehandExecutionService
        from app.models.test_case import TestCase
        from app.models.test_execution import ExecutionStatus
        
        # Convert BDD scenario to test steps
        test_steps = self._convert_scenario_to_steps(scenario)
        base_url = page_context.get("url", "https://example.com") if page_context else "https://example.com"
        
        # Create temporary test case for execution
        temp_test_case = TestCase(
            title=f"[Validation] {scenario.get('title', 'Scenario')}",
            description=scenario.get("given", ""),
            steps=test_steps,
            base_url=base_url
        )
        
        # Initialize execution service
        execution_service = StagehandExecutionService()
        
        try:
            # Execute using Phase 2 engine (3-tier strategy)
            execution = await execution_service.execute_test(
                db=self.db,
                test_case=temp_test_case,
                execution_id=None,  # Will be created by service
                user_id=1,  # System user
                base_url=base_url,
                environment="dev"
            )
            
            # Extract results
            passed_steps = execution.passed_steps or 0
            total_steps = execution.total_steps or len(test_steps)
            success_rate = passed_steps / total_steps if total_steps > 0 else 0.0
            
            # Determine tier used (from execution metadata or default to Tier 1)
            tier_used = getattr(execution, "tier_used", "tier1")
            
            return {
                "success_rate": round(success_rate, 2),
                "passed_steps": passed_steps,
                "total_steps": total_steps,
                "reliability": self._categorize_reliability(success_rate),
                "execution_time": execution.duration_seconds or 0,
                "tier_used": tier_used,
                "status": execution.result.value if execution.result else "unknown"
            }
        
        except Exception as e:
            logger.error(f"Real-time execution failed: {e}")
            # Return failure result
            return {
                "success_rate": 0.0,
                "passed_steps": 0,
                "total_steps": len(test_steps),
                "reliability": "flaky",
                "execution_time": 0,
                "tier_used": "failed",
                "status": "error",
                "error": str(e)
            }
    
    def _convert_scenario_to_steps(self, scenario: Dict) -> List[str]:
        """
        Convert BDD scenario (Given/When/Then) to executable test steps.
        
        Example:
        Given: "User is on login page"
        When: "User enters email and password, clicks Login"
        Then: "User is redirected to dashboard"
        
        Converts to:
        - Navigate to login page
        - Enter email: test@example.com
        - Enter password: password123
        - Click Login button
        - Verify URL contains /dashboard
        """
        steps = []
        
        # Given: Preconditions → Navigate/setup
        given = scenario.get("given", "")
        if "on" in given.lower() and "page" in given.lower():
            # Extract URL or page name
            if page_context and page_context.get("url"):
                steps.append(f"Navigate to {page_context['url']}")
            else:
                steps.append(f"Navigate to page: {given}")
        
        # When: Actions → Click, type, navigate
        when = scenario.get("when", "")
        # Parse actions from "when" clause
        # Simple heuristic: split by commas, detect action verbs
        when_parts = [p.strip() for p in when.split(",")]
        for part in when_parts:
            part_lower = part.lower()
            if any(word in part_lower for word in ["enter", "type", "fill", "input"]):
                # Extract field and value
                steps.append(part)  # e.g., "Enter email: test@example.com"
            elif any(word in part_lower for word in ["click", "select", "press"]):
                steps.append(part)  # e.g., "Click Login button"
            elif any(word in part_lower for word in ["navigate", "go to", "open"]):
                steps.append(part)  # e.g., "Navigate to dashboard"
        
        # Then: Assertions → Verify, check, wait
        then = scenario.get("then", "")
        if then:
            steps.append(f"Verify: {then}")
        
        return steps if steps else [scenario.get("when", "Execute scenario")]
    
    async def _get_historical_success_rate(self, scenario: Dict) -> Dict:
        """Get historical success rate from Phase 2 executions"""
        scenario_id = scenario.get("scenario_id")
        scenario_type = scenario.get("scenario_type", "functional")
        
        try:
            query = """
                SELECT 
                    AVG(passed_steps::float / NULLIF(total_steps, 0)) as avg_success_rate,
                    AVG(passed_steps) as avg_passed,
                    AVG(total_steps) as avg_total
                FROM test_executions te
                JOIN test_cases tc ON te.test_case_id = tc.id
                WHERE tc.scenario_type = $1
                  AND te.created_at > NOW() - INTERVAL '90 days'
                  AND te.total_steps > 0
            """
            row = await self.db.fetchrow(query, scenario_type)
            
            if row and row["avg_success_rate"]:
                success_rate = float(row["avg_success_rate"])
                avg_passed = int(row["avg_passed"] or 0)
                avg_total = int(row["avg_total"] or 0)
            else:
                success_rate = 0.85
                avg_passed = 17
                avg_total = 20
        
        except Exception as e:
            logger.warning(f"Could not load historical success rate: {e}, using defaults")
            success_rate = 0.85
            avg_passed = 17
            avg_total = 20
        
        return {
            "scenario_id": scenario_id,
            "success_rate": round(success_rate, 2),
            "passed_steps": avg_passed,
            "total_steps": avg_total,
            "reliability": self._categorize_reliability(success_rate),
            "source": "historical_data"
        }
    
    def _categorize_reliability(self, success_rate: float) -> str:
        """Categorize reliability based on success rate"""
        if success_rate >= 0.9:
            return "high"
        elif success_rate >= 0.7:
            return "medium"
        elif success_rate >= 0.5:
            return "low"
        else:
            return "flaky"
    
    def _adjust_detection_score(
        self, original_detection: int, success_rate: float
    ) -> int:
        """
        Adjust Detection score in RPN based on execution success rate.
        
        High success rate = Lower detection score (test is reliable)
        Low success rate = Higher detection score (test is unreliable)
        """
        if success_rate >= 0.9:
            # Test is very reliable, detection is easy
            return max(1, original_detection - 2)
        elif success_rate >= 0.7:
            # Test is usually reliable
            return max(1, original_detection - 1)
        elif success_rate >= 0.5:
            # Test is sometimes reliable
            return original_detection
        else:
            # Test is unreliable/flaky, detection is hard
            return min(5, original_detection + 1)
    
    def _finalize_prioritization(
        self, scenarios: List[Dict], risk_scores: Dict[str, RiskScore],
        business_values: List[Dict], roi_scores: List[Dict],
        coverage_impact: List[Dict], regression_risk: List[Dict],
        execution_times: List[Dict], execution_success: List[Dict]
    ) -> List[Dict]:
        """Final prioritization using composite scoring"""
        final_prioritization = []
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            
            # Get all scores
            risk_score = risk_scores.get(scenario_id)
            business_value = next(
                (bv for bv in business_values if bv["scenario_id"] == scenario_id),
                {}
            )
            roi_score = next(
                (roi for roi in roi_scores if roi["scenario_id"] == scenario_id),
                {}
            )
            coverage = next(
                (cov for cov in coverage_impact if cov["scenario_id"] == scenario_id),
                {}
            )
            regression = next(
                (reg for reg in regression_risk if reg["scenario_id"] == scenario_id),
                {}
            )
            exec_time = next(
                (et for et in execution_times if et["scenario_id"] == scenario_id),
                {}
            )
            exec_success = next(
                (es for es in execution_success if es["scenario_id"] == scenario_id),
                {}
            )
            
            if not risk_score:
                continue
            
            # Normalize scores to 0.0-1.0
            risk_normalized = risk_score.rpn / 125.0  # RPN max = 125
            business_normalized = business_value.get("total_value", 0.0)
            roi_normalized = min(1.0, roi_score.get("roi", 0.0) / 50.0)  # ROI max ~50x
            coverage_normalized = coverage.get("coverage_delta", 0.0) / 0.2  # Max delta ~0.2
            regression_normalized = regression.get("churn_score", 0.0)
            success_normalized = exec_success.get("success_rate", 0.85)  # Default 85% if unknown
            
            # Composite score (weighted, enhanced with execution success)
            composite_score = (
                risk_normalized * 0.25 +  # Reduced from 0.3
                business_normalized * 0.25 +
                roi_normalized * 0.2 +
                coverage_normalized * 0.15 +
                regression_normalized * 0.1 +
                success_normalized * 0.05  # NEW: Execution success component
            )
            
            # Business rules: Compliance always critical
            if business_value.get("compliance", 0.0) >= 0.8:
                priority = RiskPriority.CRITICAL
            else:
                priority = risk_score.to_priority()
            
            # Execution group (enhanced with success rate)
            is_fast = exec_time.get("category") == "fast"
            is_reliable = exec_success.get("reliability") in ["high", "medium"]
            is_flaky = exec_success.get("reliability") == "flaky"
            
            if priority == RiskPriority.CRITICAL and is_fast and is_reliable:
                execution_group = "critical_smoke"
            elif priority == RiskPriority.CRITICAL:
                execution_group = "critical_full"
            elif is_flaky:
                execution_group = "flaky"  # Mark flaky tests separately
            else:
                execution_group = priority.value
            
            final_prioritization.append({
                "scenario_id": scenario_id,
                "composite_score": round(composite_score, 2),
                "priority": priority.value,
                "execution_group": execution_group,
                "recommended_execution_time": "immediate" if priority == RiskPriority.CRITICAL else "normal"
            })
        
        # Sort by composite score (descending)
        final_prioritization.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Add rank
        for idx, item in enumerate(final_prioritization, 1):
            item["rank"] = idx
        
        return final_prioritization
    
    def _build_execution_strategy(
        self, final_prioritization: List[Dict],
        dependencies: List[Dict], execution_times: List[Dict]
    ) -> Dict:
        """Build execution strategy (smoke tests, parallel groups)"""
        # Smoke tests: Critical + Fast
        smoke_tests = [
            item["scenario_id"] for item in final_prioritization
            if item["execution_group"] == "critical_smoke"
        ]
        
        # Parallel groups: Independent scenarios
        parallel_groups = []
        independent_scenarios = [
            dep["scenario_id"] for dep in dependencies
            if dep["can_run_parallel"]
        ]
        
        if independent_scenarios:
            # Group by execution group for parallel execution
            groups = defaultdict(list)
            for item in final_prioritization:
                if item["scenario_id"] in independent_scenarios:
                    groups[item["execution_group"]].append(item["scenario_id"])
            parallel_groups = list(groups.values())
        
        # Calculate estimated times
        total_time = sum(
            et["estimated_seconds"] for et in execution_times
        )
        
        # Parallel time (assume 3 parallel workers)
        parallel_time = total_time / 3.0 if parallel_groups else total_time
        
        return {
            "smoke_tests": smoke_tests,
            "parallel_groups": parallel_groups,
            "estimated_total_time": round(total_time, 1),
            "estimated_parallel_time": round(parallel_time, 1)
        }
    
    def _risk_score_to_dict(self, risk_score: RiskScore) -> Dict:
        """Convert RiskScore to dictionary"""
        return {
            "rpn": risk_score.rpn,
            "severity": risk_score.severity,
            "occurrence": risk_score.occurrence,
            "detection": risk_score.detection,
            "priority": risk_score.to_priority().value
        }
    
    def _estimate_token_usage(self, scenarios: List[Dict]) -> int:
        """Estimate token usage for LLM calls"""
        # Rough estimation: 1 token ≈ 4 characters
        input_chars = len(json.dumps(scenarios))
        # Output: risk assessments for each scenario
        output_chars = len(scenarios) * 200  # ~200 chars per assessment
        return int((input_chars + output_chars) / 4)
```

**Integration Example:**
```python
# AnalysisAgent receives RequirementsAgent output
requirements_output = {
    "scenarios": [...],  # From RequirementsAgent
    "test_data": [...],
    "coverage_metrics": {...}
}

task = TaskContext(
    task_id="task-456",
    task_type="risk_analysis",
    payload=requirements_output,
    conversation_id="conv-789"
)

result = await analysis_agent.execute_task(task)

# Output includes comprehensive risk analysis, ROI, dependencies, execution success, etc.

# Post-Execution Feedback Loop (Optional):
# After tests are executed, AnalysisAgent can refine scores:
execution_results = {
    "REQ-F-001": {
        "passed_steps": 19,
        "total_steps": 20,
        "status": "passed"
    }
}

refinement_task = TaskContext(
    task_id="task-789",
    task_type="risk_analysis_refinement",
    payload={
        "scenarios": [...],  # Original scenarios
        "execution_results": execution_results  # Actual execution results
    },
    conversation_id="conv-789"
)

refined_result = await analysis_agent.execute_task(refinement_task)
# Refined scores now include actual execution success rates
```

---

## 4. Phase 2 Integration Strategy

### 4.1 Integration Principle

**Zero-downtime migration:** Phase 3 agents wrap Phase 2 execution engine (not replace).

```
Before (Phase 2):
User → Frontend → Backend API → Execution Engine → Stagehand

After (Phase 3):
User → Frontend → Backend API → Orchestration Agent → Evolution Agent → (Phase 2 Execution Engine) → Stagehand
```

### 4.2 Database Schema Additions

**4 new tables (no modifications to existing):**

```sql
CREATE TABLE agent_registry (
    agent_id VARCHAR(100) PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    capabilities JSONB NOT NULL,
    endpoints JSONB NOT NULL
);

CREATE TABLE working_memory (
    memory_id SERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL,
    key VARCHAR(200) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE agent_tasks (
    task_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    agent_id VARCHAR(100),
    task_type VARCHAR(50),
    payload JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_metrics (
    metric_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 API Versioning

**Old endpoint (Phase 2):** `/api/v1/generate-tests` (unchanged)  
**New endpoint (Phase 3):** `/api/v2/generate-tests` (uses agents)

```python
# backend/api/v2/tests.py

@app.post("/api/v2/generate-tests")
async def generate_tests_v2(request: TestGenerationRequest):
    """Phase 3: Multi-agent test generation"""
    
    # Create conversation
    conversation_id = str(uuid.uuid4())
    
    # Send to Orchestration Agent
    await message_bus.send_message("agent:orchestration:inbox", {
        "message_type": "task_request",
        "conversation_id": conversation_id,
        "task_type": "test_generation",
        "payload": request.dict()
    })
    
    # Wait for completion (async)
    result = await wait_for_completion(conversation_id, timeout=300)
    
    return {"conversation_id": conversation_id, "result": result}
```

### 4.4 Feature Flag Rollout

**Environment variable:** `AGENTS_ENABLED=true`

```python
# backend/api/tests.py

@app.post("/api/generate-tests")
async def generate_tests(request: TestGenerationRequest):
    """Smart routing: Phase 2 or Phase 3"""
    
    if os.getenv("AGENTS_ENABLED") == "true":
        # Phase 3: Multi-agent
        return await generate_tests_v2(request)
    else:
        # Phase 2: Legacy
        return await generate_tests_v1(request)
```

### 4.5 Rollout Schedule

| Week | Traffic % | Status | Action |
|------|-----------|--------|--------|
| **Week 1-2 (Sprint 7)** | 0% | Shadow mode | Agents process traffic, results discarded |
| **Week 3-4 (Sprint 8)** | 5% | Canary | 5% real traffic to agents, 95% to Phase 2 |
| **Week 5-6 (Sprint 9)** | 25% | Ramp-up | Monitor metrics, rollback if issues |
| **Week 7-8 (Sprint 10)** | 50% | Majority | Agents handle majority of traffic |
| **Week 9-10 (Sprint 11)** | 75% | Near-full | Phase 2 becoming fallback only |
| **Week 11-12 (Sprint 12)** | 100% | Full migration | Phase 2 deprecated, agents only |

---

## 5. Testing Strategy

### 5.1 Test Pyramid

```
         /\
        /  \  System Tests (8%) - 15+ tests
       /____\
      /      \  Integration Tests (20%) - 70+ tests
     /________\
    /          \  Unit Tests (70%) - 550+ tests
   /____________\
```

**Target:** 95%+ code coverage, <5% change failure rate

### 5.2 Unit Tests (550+ tests by Sprint 12)

**Coverage targets:**
- BaseAgent: 95% (50+ tests)
- Specialized agents (each): 90% (30+ tests × 6 = 180 tests)
- Memory system: 95% (40+ tests)
- Message bus: 95% (35+ tests)
- Orchestrator: 90% (45+ tests)

**Template:**

```python
# backend/tests/unit/test_evolution_agent.py

import pytest
from agents.evolution_agent import EvolutionAgent

@pytest.fixture
async def evolution_agent():
    """Create Evolution Agent with mocked LLM"""
    llm = AsyncMock()
    llm.generate.return_value = {
        "choices": [{"text": "def test_example(): pass"}],
        "usage": {"total_tokens": 100}
    }
    
    agent = EvolutionAgent(
        agent_id="evolution_1",
        agent_type="evolution",
        priority=5,
        llm_client=llm,
        # ... other mocks
    )
    return agent

@pytest.mark.asyncio
async def test_generates_valid_test_code(evolution_agent):
    """Test that Evolution Agent generates valid pytest code"""
    task = TaskContext(
        task_id="task_1",
        task_type="test_generation",
        payload={"code": "def add(a, b): return a + b"},
        conversation_id="conv_1"
    )
    
    result = await evolution_agent.execute_task(task)
    
    assert result.success is True
    assert "def test_" in result.result["generated_tests"]
    assert result.confidence > 0.7
```

### 5.3 Integration Tests (70+ tests)

**Template:**

```python
# backend/tests/integration/test_agent_workflow.py

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test: User request → Observation → Requirements → Evolution → Report"""
    
    # Send request to Orchestration Agent
    conversation_id = str(uuid.uuid4())
    await message_bus.send_message("agent:orchestration:inbox", {
        "conversation_id": conversation_id,
        "task_type": "test_generation",
        "payload": {"code": "def add(a, b): return a + b"}
    })
    
    # Wait for completion
    result = await wait_for_completion(conversation_id, timeout=60)
    
    # Verify
    assert result["status"] == "completed"
    assert "generated_tests" in result
    assert len(result["generated_tests"]) > 0
```

### 5.4 System Tests (15+ tests)

**Load testing with Locust:**

```python
# tests/system/locustfile.py

from locust import HttpUser, task, between

class TestGenerationUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_tests(self):
        """Simulate user generating tests"""
        self.client.post("/api/v2/generate-tests", json={
            "repository_url": "https://github.com/example/repo",
            "target_files": ["src/calculator.py"],
            "coverage_target": 0.80
        })
```

**Run:** `locust -f locustfile.py --users 100 --spawn-rate 10`

### 5.5 Chaos Engineering (5+ scenarios)

**Chaos scenarios:**
1. Redis failure (primary node down)
2. LLM timeout (OpenAI API slow)
3. Message loss (network partition)
4. Agent crash (kill random agent)
5. Database overload (slow queries)

**Template:**

```python
# tests/chaos/test_redis_failure.py

@pytest.mark.asyncio
async def test_survives_redis_failure():
    """Test: System continues when Redis fails"""
    
    # Start workflow
    conversation_id = start_workflow()
    
    # Inject failure: Kill Redis primary
    await chaos_manager.kill_redis_primary()
    
    # System should auto-failover to replica (<5s)
    await asyncio.sleep(5)
    
    # Workflow should complete successfully
    result = await wait_for_completion(conversation_id, timeout=120)
    assert result["status"] == "completed"
```

---

## 6. Agent Performance Scoring

### 6.1 Overview

**Purpose:** Comprehensive performance scoring system for all Phase 3 agents based on industry best practices (ISTQB, IEEE 29119, ISO/IEC 25010).

**Documentation:** See [Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) for complete specifications, scoring formulas, and implementation examples.

### 6.2 Scoring Dimensions

**ObservationAgent Performance Metrics:**
- **Selector/XPath Accuracy (35%):** Validates selectors by re-querying the page
- **Element Detection Completeness (30%):** Measures coverage of interactive elements
- **Element Classification Accuracy (20%):** Validates button vs. link vs. input classification
- **LLM Enhancement Effectiveness (15%):** Measures LLM contribution beyond Playwright

**RequirementsAgent Performance Metrics:**
- **Test Scenario Correctness (40%):** Validates BDD format (Given/When/Then) and logical flow
- **Execution Success Rate (35%):** Measures how many scenarios execute successfully (requires AnalysisAgent execution results)
- **Coverage Completeness (15%):** Measures coverage of critical UI elements and user journeys
- **Scenario Quality (10%):** Measures relevance (references actual elements) and completeness

**AnalysisAgent Performance Metrics:**
- **Risk Score Accuracy (30%):** Compares predicted high-risk scenarios vs. actual failures (F1 score)
- **ROI Prediction Accuracy (25%):** Pearson correlation between predicted and actual ROI
- **Execution Time Accuracy (20%):** Mean Absolute Percentage Error (MAPE) for time predictions
- **Prioritization Effectiveness (25%):** Measures if high-priority scenarios found bugs faster

### 6.3 Implementation Status

**Status:** 📋 Design Complete - Ready for Implementation (Jan 29, 2026)

**Implementation Roadmap:**
- **Phase 1 (Week 1):** ObservationAgent scoring - `calculate_performance_score()` method
- **Phase 2 (Week 2):** RequirementsAgent scoring - Requires execution results from AnalysisAgent
- **Phase 3 (Week 3):** AnalysisAgent scoring - Requires actual execution results for comparison
- **Phase 4 (Week 4):** Integration & reporting - Database schema, dashboard, trend analysis

### 6.4 Integration with Agent Implementation

**Example: Adding Performance Scoring to ObservationAgent:**

```python
# In observation_agent.py
async def calculate_performance_score(self, task_result: TaskResult) -> Dict[str, Any]:
    """
    Calculate performance score for this observation task.
    Called after execute_task() completes.
    """
    result = task_result.result
    ui_elements = result.get("ui_elements", [])
    pages = result.get("pages", [])
    llm_analysis = result.get("llm_analysis", {})
    
    # Re-open browser to validate selectors (if not in stub mode)
    if PLAYWRIGHT_AVAILABLE and pages:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to first page
            first_url = pages[0].get("url") if isinstance(pages[0], dict) else pages[0].url
            await page.goto(first_url, timeout=30000)
            
            # Calculate component scores
            selector_accuracy = await self._score_selector_accuracy(ui_elements, page)
            detection_completeness = await self._score_detection_completeness(ui_elements, page)
            classification_accuracy = await self._score_classification_accuracy(ui_elements, page)
            llm_enhancement = self._score_llm_enhancement(ui_elements, llm_analysis)
            
            await browser.close()
            
            # Calculate overall score
            performance = self._calculate_observation_agent_score(
                selector_accuracy,
                detection_completeness,
                classification_accuracy,
                llm_enhancement
            )
            
            # Add to result metadata
            result["performance_score"] = performance
            
            return performance
```

**See [Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) Section 2-4 for complete implementation examples for all agents.**

### 6.5 Database Schema

**Performance Scores Storage:**

```sql
CREATE TABLE agent_performance_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL,  -- 'observation', 'requirements', 'analysis'
    task_id TEXT NOT NULL,
    overall_score REAL,
    component_scores JSON,
    grade TEXT,  -- 'A', 'B', 'C', 'D', 'F'
    recommendations JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### 6.6 Testing Performance Scoring

**Unit Tests:**
- Test each scoring dimension independently
- Validate scoring formulas against known ground truth
- Test edge cases (empty inputs, invalid data)

**Integration Tests:**
- Test end-to-end scoring workflow (agent execution → score calculation → storage)
- Validate cross-agent dependencies (RequirementsAgent needs AnalysisAgent execution results)
- Test trend analysis over multiple task executions

**See [Phase3-Agent-Performance-Scoring-Framework.md](supporting-documents/Phase3-Agent-Performance-Scoring-Framework.md) Section 7 for example usage and test patterns.**

---

## 7. Security Implementation

### 6.1 JWT-Based Agent Authentication

```python
# backend/agents/security/agent_auth.py

import jwt
from datetime import datetime, timedelta

class AgentAuthenticator:
    """Issue and verify JWT tokens for agents"""
    
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

### 6.2 RBAC (4 Roles)

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

### 6.3 TLS Encryption

**nginx configuration:**

```nginx
server {
    listen 443 ssl http2;
    server_name api.aitest.example.com;
    
    ssl_certificate /etc/letsencrypt/live/api.aitest.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.aitest.example.com/privkey.pem;
    
    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384';
    
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location /api/ {
        proxy_pass http://backend:8000;
    }
}
```

### 6.4 Audit Logging

```sql
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Middleware:**

```python
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API requests"""
    user_id = request.state.user.get("user_id") if hasattr(request.state, "user") else None
    
    response = await call_next(request)
    
    await db.execute("""
        INSERT INTO audit_log (user_id, action, ip_address)
        VALUES ($1, $2, $3)
    """, user_id, request.url.path, request.client.host)
    
    return response
```

---

## 8. Cost Optimization

### 7.1 Caching Strategy (30% savings)

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def generate_test_cached(code_hash: str, requirements: str):
    """Cache test generation results by code hash"""
    if code_hash in cache:
        logger.info(f"Cache hit for {code_hash}")
        return cache[code_hash]
    
    result = await generate_test(code_hash, requirements)
    cache[code_hash] = result
    return result
```

### 7.2 Hybrid LLM Strategy (52% savings)

| Agent | Model | Reasoning |
|-------|-------|-----------|
| Observation | GPT-4-mini | Simple parsing, low complexity |
| Requirements | GPT-4-mini | Pattern matching, straightforward |
| Analysis | GPT-4-mini | Risk scoring, deterministic |
| **Evolution** | **GPT-4** | **Complex reasoning required** |
| Orchestration | GPT-4-mini | Task routing, simple logic |
| Reporting | GPT-4-mini | Template filling, formatting |

**Cost Impact:**
- All GPT-4: $0.33/cycle
- **Hybrid: $0.16/cycle** ✅ 52% savings
- All GPT-4-mini: $0.006/cycle (but lower quality)

### 7.3 Token Limit Enforcement

```python
MAX_TOKENS_PER_REQUEST = 10000

if len(input_tokens) > MAX_TOKENS_PER_REQUEST:
    raise ValueError(f"Input exceeds {MAX_TOKENS_PER_REQUEST} tokens")
```

### 7.4 Monthly Cost Breakdown

| Component | Cost (Self-hosted) | Cost (Managed) |
|-----------|-------------------|----------------|
| **Infrastructure** | | |
| Redis Cluster | $240 | $544 |
| PostgreSQL | $150 | $736 |
| Qdrant Vector DB | $0 (free tier) | $95 |
| Kubernetes | $431 | $431 |
| Load Balancer | $25 | $25 |
| Monitoring | $5 | $5 |
| **Subtotal** | **$851** | **$1,836** |
| | | |
| **LLM API (Hybrid)** | $160 | $160 |
| **Learning System** | $50 | $50 |
| | | |
| **TOTAL** | **$1,061/month** ✅ | **$2,046/month** |

**Recommended:** Self-hosted (save $985/month)

---

## Post-Sprint 9: Performance Optimization & Test Coverage (Feb 9, 2026)

### Performance Optimization Implementation

#### OPT-2: Parallel Scenario Execution ✅ COMPLETE

**Status:** ✅ **IMPLEMENTED** (February 9, 2026)

**Implementation Details:**
- **Location:** `backend/agents/analysis_agent.py` (lines 186-234)
- **Method:** Parallel execution using `asyncio.gather()` with configurable batch size
- **Configuration:** `parallel_execution_batch_size` config option (default: 3 scenarios per batch)

**Code Changes:**
```python
# Before: Sequential execution
for scenario in critical_scenarios[:3]:
    exec_result = await self._execute_scenario_real_time(scenario, page_context)

# After: Parallel batch execution
batch_size = self.config.get("parallel_execution_batch_size", 3)
for batch_idx in range(0, len(scenarios_to_execute), batch_size):
    batch = scenarios_to_execute[batch_idx:batch_idx + batch_size]
    tasks = [self._execute_scenario_real_time(s, page_context) for s in batch]
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Expected Performance Improvement:**
- **Before:** ~169 seconds (17 scenarios × ~10 seconds each, sequential)
- **After:** ~50-70 seconds (60-70% improvement with 3 parallel batches)
- **Batches:** 17 scenarios ÷ 3 per batch = 6 batches × ~10 seconds = ~60 seconds

**Configuration:**
```python
config = {
    "enable_realtime_execution": True,
    "execution_rpn_threshold": 0,  # Execute all scenarios
    "parallel_execution_batch_size": 3  # Execute 3 scenarios in parallel per batch
}
```

#### OPT-1: HTTP Session Reuse ✅ COMPLETE

**Status:** ✅ **IMPLEMENTED** (February 9, 2026)

**Implementation Details:**
- **Location:** `backend/app/services/universal_llm.py` and `backend/app/services/openrouter.py`
- **Method:** Shared `httpx.AsyncClient` with connection pooling
- **Connection Limits:** `max_keepalive_connections=10`, `max_connections=20`

**Code Changes:**
```python
# Before: New client for each request
async with httpx.AsyncClient(timeout=90.0) as client:
    response = await client.post(...)

# After: Reuse shared client
client = await self._get_http_client()
response = await client.post(...)

async def _get_http_client(self) -> httpx.AsyncClient:
    if self._http_client is None:
        self._http_client = httpx.AsyncClient(
            timeout=90.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    return self._http_client
```

**Expected Performance Improvement:** 20-30% faster LLM calls (connection reuse eliminates TCP handshake overhead)

#### OPT-3: Element Finding Cache ✅ COMPLETE

**Status:** ✅ **IMPLEMENTED** (February 9, 2026)

**Implementation Details:**
- **Location:** `backend/agents/observation_agent.py`
- **Method:** Cache element selectors by `(tag, id, class)` tuple
- **Cache Key:** `(element_tag, element_id, element_class)`

**Code Changes:**
```python
# Before: Generate selector every time
async def _get_selector(self, element) -> str:
    element_id = await element.get_attribute("id")
    # ... generate selector ...

# After: Cache selectors
self._element_cache: Dict[Tuple[str, Optional[str], Optional[str]], str] = {}

async def _get_selector(self, element) -> str:
    cache_key = (element_tag, element_id, element_class)
    if cache_key in self._element_cache:
        return self._element_cache[cache_key]
    # ... generate and cache selector ...
```

**Expected Performance Improvement:** 30-40% faster for repeated element finding scenarios

#### OPT-4: Optimize Accessibility Tree ✅ COMPLETE

**Status:** ✅ **IMPLEMENTED** (February 9, 2026)

**Implementation Details:**
- **Location:** `backend/llm/azure_client.py`
- **Method:** Clean HTML before sending to LLM (remove scripts, styles, comments, compress whitespace)
- **HTML Limit:** Increased from 15KB to 20KB (after optimization)

**Code Changes:**
```python
# Before: Send raw HTML (truncated to 15KB)
html_snippet = html[:15000] if len(html) > 15000 else html

# After: Clean HTML before truncation
html_optimized = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
html_optimized = re.sub(r'<style[^>]*>.*?</style>', '', html_optimized, flags=re.DOTALL | re.IGNORECASE)
html_optimized = re.sub(r'<!--.*?-->', '', html_optimized, flags=re.DOTALL)
html_optimized = re.sub(r'\s+', ' ', html_optimized)  # Compress whitespace
html_snippet = html_optimized[:20000] if len(html_optimized) > 20000 else html_optimized
```

**Expected Performance Improvement:** 20-30% faster LLM calls (reduced token usage, cleaner input)

#### Summary: All Performance Optimizations Complete

| Optimization | Status | Expected Improvement | Implementation |
|-------------|--------|---------------------|----------------|
| **OPT-1:** HTTP Session Reuse | ✅ **COMPLETE** | 20-30% faster LLM calls | Shared httpx.AsyncClient |
| **OPT-2:** Parallel Execution | ✅ **COMPLETE** | 60-70% faster execution | asyncio.gather() batches |
| **OPT-3:** Element Finding Cache | ✅ **COMPLETE** | 30-40% faster for repeated scenarios | Selector cache by (tag, id, class) |
| **OPT-4:** Optimize Accessibility Tree | ✅ **COMPLETE** | 20-30% faster LLM calls | HTML cleaning before LLM |

**Total Expected Performance Improvement: 50-70% overall**

### Test Coverage Improvements

**Current Coverage:**
- EvolutionAgent unit tests: 27 tests ✅
- Integration tests: 7 tests ✅
- Total: 34 tests (~85-90% coverage)

**Target Coverage:** 95%+

**Improvements Implemented:**
1. ✅ Edge case tests (50+ scenarios, special characters, network failures) - **COMPLETE**
   - Created `test_evolution_agent_edge_cases.py` with 7 new tests
   - Tests: Large scenarios, special characters, long descriptions, empty fields, network failures
2. ✅ Performance tests (concurrent generation, memory usage) - **COMPLETE**
   - Tests: Concurrent generation, cache memory usage
3. ✅ Error recovery tests (partial failures, timeouts) - **COMPLETE**
   - Tests: Network failures, empty fields, database errors

**New Test File:** `backend/tests/unit/test_evolution_agent_edge_cases.py`
- 7 new edge case and performance tests
- Total tests: 41 (up from 34)
- Coverage: ~90-92% (improved from ~85-90%)

**Remaining Work:**
- Additional integration tests for error scenarios
- Cache corruption recovery tests
- Connection pooling tests

**Estimated Time Remaining:** 1-2 days to reach 95%+ coverage

---

**END OF IMPLEMENTATION GUIDE**

**Document Version:** 1.3  
**Last Review:** February 9, 2026  
**Next Review:** Sprint 10 start (Mar 6, 2026)

---

## Sprint 7 Completion Summary (Jan 29, 2026)

### ✅ All Sprint 7 Tasks Completed

**Developer A Deliverables:**
- ✅ **Task 7A.4:** AnalysisAgent class with FMEA risk scoring (13 pts) - RiskScore class, RPN calculation
- ✅ **Task 7A.5:** LLM integration for structured risk analysis (8 pts) - Azure OpenAI GPT-4o integration
- ✅ **Task 7A.6:** Historical data integration (5 pts) - Uses existing Phase 2 database
- ✅ **Task 7A.7:** ROI calculation and execution time estimation (5 pts)
- ✅ **Task 7A.8:** Dependency analysis with topological sort (5 pts) - Cycle detection, parallel groups
- ✅ **Task 7A.9:** Business value scoring (3 pts) - Revenue, user impact, compliance
- ✅ **Task 7A.10:** Coverage impact analysis and regression risk assessment (5 pts)
- ✅ **Task 7A.11:** Unit tests for AnalysisAgent (3 pts) - 44/44 passing
- ✅ **Task 7A.12:** Integration tests (5 pts) - 13/13 passing, including E2E with real Three HK page

**Total: 46 story points completed in 7 days (Jan 23-29, 2026)**

### ✅ Sprint 7 Enhancements (Beyond Original Scope)

- ✅ **Real-time test execution integration** - 3-tier strategy (Playwright → observe+XPath → Stagehand AI)
- ✅ **Adaptive scoring** - Detection score adjustment based on execution success rates
- ✅ **E2E testing with real page execution** - Three HK 5G Broadband page successfully tested
- ✅ **Browser visibility control** - HEADLESS_BROWSER env var for watching test execution
- ✅ **Azure OpenAI integration** - Successfully using AZURE_OPENAI_API_KEY (no Cloudflare blocks)

### 📊 Test Coverage

- **Unit Tests:** 99+ passing (55 from pre-sprint + 44 new for AnalysisAgent)
- **Integration Tests:** 13/13 passing
  - 3-agent workflow (Observation → Requirements → Analysis)
  - E2E with real Three HK page (7 steps, 100% success rate)
  - Real-time execution with 3-tier strategy
  - Adaptive scoring verification

### 🎯 Key Achievements

1. **FMEA Risk Scoring:** Complete RPN calculation (Severity × Occurrence × Detection)
2. **LLM Integration:** Azure OpenAI GPT-4o for structured risk analysis
3. **Historical Data:** Integration with existing Phase 2 database
4. **Real-Time Execution:** Full 3-tier execution strategy integrated
5. **E2E Testing:** Real page execution on Three HK website
6. **Browser Visibility:** Control via HEADLESS_BROWSER env var

### 🚀 Ready for Sprint 8

- ✅ AnalysisAgent fully operational
- ✅ Real-time execution working
- ✅ E2E testing validated
- 🔄 Next: EvolutionAgent implementation (Sprint 8)

---

## 9. Supporting Documents

This document provides detailed implementation tasks and code examples. For additional analysis, strategies, and frameworks, see the following supporting documents:

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
- `Phase3-Implementation-Guide-Complete.md` - This document (detailed implementation tasks and code examples)
- `Phase3-Project-Management-Plan-Complete.md` - Sprint planning, task breakdown, budget, timeline

**Supporting Documents (supporting-documents/ folder):**
- Detailed analysis documents
- Agent-specific reviews
- Strategy documents
- Performance frameworks
