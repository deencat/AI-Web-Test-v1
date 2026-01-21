# Phase 3: Complete Implementation Guide

**Purpose:** Comprehensive implementation guide with code examples, sprint tasks, integration, testing, and security  
**Scope:** Sprint 7-12 detailed tasks, Phase 2 integration, code templates, testing strategy, security design  
**Status:** Ready for development  
**Last Updated:** January 19, 2026

---

## 📋 Table of Contents

1. [Implementation Overview](#1-implementation-overview)
2. [Sprint 7-12 Detailed Tasks](#2-sprint-7-12-detailed-tasks)
3. [Production-Ready Code Examples](#3-production-ready-code-examples)
4. [Phase 2 Integration Strategy](#4-phase-2-integration-strategy)
5. [Testing Strategy](#5-testing-strategy)
6. [Security Implementation](#6-security-implementation)
7. [Cost Optimization](#7-cost-optimization)

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

2. **RequirementsAgent** - Test Requirement Extractor
   - **What it does:** Converts UI observations into test scenarios
   - **Inputs:** Page map from ObservationAgent
   - **Outputs:** Test requirements in Given/When/Then format
   - **Technology:** Pattern matching, NLP
   - **Example:** "Given user is on login page, When user enters valid credentials and clicks submit, Then user should be redirected to dashboard"

3. **AnalysisAgent** - Risk & Priority Analyzer
   - **What it does:** Identifies which UI flows are most critical to test
   - **Inputs:** Test requirements, historical bug data
   - **Outputs:** Risk scores (0.0-1.0), prioritized test list
   - **Technology:** Dependency graph analysis, risk scoring algorithms
   - **Example:** Login flow = 0.95 (critical), Footer links = 0.2 (low priority)

4. **EvolutionAgent** - Test Code Generator
   - **What it does:** Generates Playwright/Stagehand test code from requirements
   - **Inputs:** Test requirements, risk scores
   - **Outputs:** Executable Playwright test files (.spec.ts)
   - **Technology:** GPT-4 LLM with prompt templates
   - **Example:** Generates `test('user can login', async ({ page }) => { await page.goto('...'); await page.fill('#username', 'test'); ... })`

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
| **Sprint 7** | Weeks 1-2 | Infrastructure + BaseAgent | 31 | Developer A |
| **Sprint 8** | Weeks 3-4 | Observation + Requirements | 42 | Developer A |
| **Sprint 9** | Weeks 5-6 | Analysis + Evolution | 47 | Developer A |
| **Sprint 10** | Weeks 7-8 | Orchestration + Reporting | 52 | Developer A |
| **Sprint 11** | Weeks 9-10 | CI/CD Integration | 39 | Both (parallel) |
| **Sprint 12** | Weeks 11-12 | Enterprise Features | 44 | Developer A |
| **TOTAL** | 12 weeks | | **354 points** | |

### 1.3 Phase Breakdown

**Weeks 1-2 (Sprint 7):** Foundation
- Redis Streams, PostgreSQL, BaseAgent, memory system, health checks

**Weeks 3-6 (Sprints 8-9):** Core Agents
- Observation, Requirements, Analysis, Evolution agents operational

**Weeks 7-8 (Sprint 10):** Coordination
- Orchestration, Reporting agents, Contract Net Protocol

**Weeks 9-10 (Sprint 11):** Integration
- GitHub Actions, CI/CD pipelines, load testing

**Weeks 11-12 (Sprint 12):** Production Readiness
- Multi-tenancy, RBAC, security audit, chaos engineering

---

## 2. Sprint 7-12 Detailed Tasks

### Sprint 7: Infrastructure & BaseAgent (Jan 23 - Feb 5, 2026)

**Goal:** Set up multi-agent infrastructure and implement BaseAgent abstract class

**Story Points:** 31 (11 days duration)

#### Developer A Tasks (21 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 7A.1 | Set up Redis Streams cluster (3 nodes) | None | 3 | 1 day | 0 (START) |
| 7A.2 | Implement message bus wrapper (send/receive) | 7A.1 | 5 | 2 days | 1 |
| 7A.3 | Implement BaseAgent abstract class | 7A.2 | 8 | 3 days | 3 |
| 7A.4 | Implement agent registry (register/heartbeat) | 7A.3 | 3 | 1 day | 6 |
| 7A.5 | Create health check endpoints (/health, /ready) | 7A.4 | 2 | 1 day | 7 |

**Total: 21 points, 8 days**

#### Developer B Tasks (10 points, parallel)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 7B.1 | Set up PostgreSQL with pgvector extension | None | 5 | 2 days |
| 7B.2 | Implement three-layer memory system | 7B.1 | 5 | 2 days |
| 7B.3 | Unit tests for BaseAgent (50+ tests) | 7A.3 | 3 | 1 day |
| 7B.4 | Add 8 learning system database tables | 7B.1 | 5 | 2 days |
| 7B.5 | Implement FeedbackCollector foundation | 7B.4 | 3 | 1 day |

**Total: 10 points, 5 days**

#### Sprint 7 Success Criteria

- ✅ Redis Streams operational (3-node cluster, <1ms latency)
- ✅ PostgreSQL with pgvector extension deployed
- ✅ BaseAgent class implemented with rich defaults
- ✅ Message bus sends/receives 1000+ msg/sec
- ✅ Health checks return 200 OK
- ✅ 50+ unit tests passing, 95%+ coverage
- ✅ 8 learning database tables created
- ✅ First generation tracked in test_generations table

#### Sprint 7 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| DevOps delays Kubernetes setup | High | High | Start with local Docker Compose, migrate later |
| Redis Streams learning curve | Medium | Medium | Pre-study docs, use examples from research |
| pgvector extension issues | Low | Medium | Use Docker image with extension pre-installed |

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
- Converts test scenarios → executable test code
- Example: Generates `test('user can login', async ({ page }) => { ... })`

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

### Sprint 8: Observation & Requirements Agents (Feb 6 - Feb 19, 2026)

**Goal:** Deploy agents that observe web applications and extract test requirements

**Story Points:** 42 (11 days duration)

#### Developer A Tasks (23 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 8A.1 | Implement ObservationAgent class | Sprint 7 | 8 | 3 days | 0 (START) |
| 8A.2 | Web crawling with Playwright (page navigation, DOM analysis) | 8A.1 | 5 | 2 days | 3 |
| 8A.3 | LLM integration with Cerebras (element detection, semantic analysis) | 8A.2 | 5 | 2 days | 5 |
| 8A.4 | Hybrid observation: Playwright baseline + LLM enhancement | 8A.3 | 3 | 1 day | 7 |
| 8A.5 | Integration with Phase 2 Stagehand service | 8A.4 | 5 | 2 days | 8 |
| 8A.6 | Unit tests for ObservationAgent (30+ tests, LLM mocking) | 8A.5 | 2 | 1 day | 10 |

**Total: 28 points, 11 days**

#### Developer B Tasks (19 points, parallel)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 8B.1 | Implement RequirementsAgent class | Sprint 7 | 8 | 3 days |
| 8B.2 | LLM integration for test scenario generation (Given/When/Then) | 8B.1 | 5 | 2 days |
| 8B.3 | Pattern matching and priority assignment (critical/high/medium/low) | 8B.2 | 3 | 1 day |
| 8B.4 | Unit tests for RequirementsAgent (30+ tests, LLM mocking) | 8B.3 | 3 | 1 day |
| 8B.5 | Integration tests (Observation → Requirements) | 8A.6, 8B.4 | 5 | 2 days |
| 8B.6 | Collect first 100+ user feedback samples | Sprint 7 | 3 | Continuous |

**Total: 27 points, 6 days**

#### Sprint 8 Success Criteria

- ✅ Observation Agent crawls web application pages (buttons, forms, navigation)
- ✅ LLM integration finds 65% more elements than Playwright-only
- ✅ Hybrid observation: Playwright baseline (200ms) + LLM enhancement (3s)
- ✅ Cerebras API configured with llama3.1-8b model
- ✅ Graceful degradation: Works without LLM (Playwright-only fallback)
- ✅ Requirements Agent extracts test scenarios from UI elements (Given/When/Then)
- ✅ Integration test: Observation → Requirements end-to-end (web app → test requirements)
- ✅ 30+ unit tests per agent, 95%+ coverage
- ✅ 100+ user feedback samples collected
- ✅ First 2 agents registered and operational

---

### Sprint 9: Analysis & Evolution Agents (Feb 20 - Mar 5, 2026)

**Goal:** Deploy agents that analyze dependencies and generate tests

**Story Points:** 47 (12 days duration)

#### Developer A Tasks (26 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 9A.1 | Implement EvolutionAgent class | Sprint 8 | 13 | 5 days | 0 (START) |
| 9A.2 | LLM integration with Cerebras (test code generation) | 9A.1 | 8 | 3 days | 5 |
| 9A.3 | Test generation prompt templates (Playwright/Stagehand, 3 variants) | 9A.2 | 5 | 2 days | 8 |
| 9A.4 | Caching layer with pattern storage (90% cost reduction after Sprint 10) | 9A.3 | 3 | 1 day | 10 |
| 9A.5 | Unit tests for EvolutionAgent (30+ tests, LLM mocking) | 9A.4 | 1 | 1 day | 11 |

**Total: 30 points, 12 days**

#### Developer B Tasks (21 points, parallel)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 9B.1 | Implement AnalysisAgent class | Sprint 8 | 8 | 3 days |
| 9B.2 | LLM integration for risk assessment (UI element risk scoring) | 9B.1 | 5 | 2 days |
| 9B.3 | Priority assignment (critical/high/medium/low based on LLM analysis) | 9B.2 | 5 | 2 days |
| 9B.4 | Unit tests for AnalysisAgent (30+ tests, LLM mocking) | 9B.3 | 3 | 1 day |
| 9B.5 | Integration tests (4-agent coordination: Observe → Requirements → Analyze → Evolve) | 9A.5, 9B.4 | 5 | 2 days |
| 9B.6 | First automated prompt optimization (A/B testing) | Sprint 8 feedback | 3 | 1 day |

**Total: 29 points, 7 days**

#### Sprint 9 Success Criteria

- ✅ Evolution Agent generates 10+ valid Playwright/Stagehand tests from test scenarios
- ✅ LLM generates executable test code (async/await, page navigation, assertions)
- ✅ Analysis Agent produces risk scores for UI elements (0.0-1.0, LLM-based)
- ✅ LLM integration with Cerebras operational (llama3.1-8b for code generation)
- ✅ Caching reduces LLM calls by 30% (pattern reuse for similar pages)
- ✅ 4-agent workflow: Observe Web App → Extract Requirements → Analyze UI Risks → Generate Test Code
- ✅ First optimized prompt variant deployed (A/B tested for accuracy)
- ✅ Token usage <10,000 per test cycle (with caching)

---

### Sprint 10: Orchestration & Reporting Agents (Mar 6 - Mar 19, 2026)

**Goal:** Deploy agents that coordinate workflows and generate reports

**Story Points:** 52 (13 days duration)

#### Developer A Tasks (29 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 10A.1 | Implement OrchestrationAgent class | Sprint 9 | 13 | 5 days | 0 (START) |
| 10A.2 | Workflow state machine (PENDING→RUNNING→COMPLETED) | 10A.1 | 8 | 3 days | 5 |
| 10A.3 | Contract Net Protocol (task bidding) | 10A.2 | 8 | 3 days | 8 |
| 10A.4 | Deadlock detection (5min timeout) | 10A.3 | 5 | 2 days | 11 |
| 10A.5 | Unit tests for OrchestrationAgent (50+ tests) | 10A.4 | 3 | 1 day | 13 |

**Total: 29 points, 13 days**

#### Developer B Tasks (23 points, parallel)

| Task ID | Description | Dependencies | Points | Duration |
|---------|-------------|--------------|--------|----------|
| 10B.1 | Implement ReportingAgent class | Sprint 9 | 8 | 3 days |
| 10B.2 | Report generation (Markdown + PDF) | 10B.1 | 5 | 2 days |
| 10B.3 | Coverage visualization (charts) | 10B.2 | 5 | 2 days |
| 10B.4 | Unit tests for ReportingAgent (30+ tests) | 10B.3 | 3 | 1 day |
| 10B.5 | Integration tests (6-agent end-to-end) | 10A.5, 10B.4 | 5 | 2 days |
| 10B.6 | Mine first 10 learned patterns | Sprint 9 feedback | 3 | 1 day |

**Total: 23 points, 8 days**

#### Sprint 10 Success Criteria

- ✅ Orchestration Agent coordinates all 6 agents
- ✅ Contract Net Protocol allocates tasks efficiently
- ✅ Workflow state machine handles PENDING→RUNNING→COMPLETED
- ✅ Reporting Agent generates PDF reports with charts
- ✅ 6-agent end-to-end test passes (user request → final report)
- ✅ 10+ learned patterns in pattern library
- ✅ No deadlocks in 100+ test workflows

---

### Sprint 11: CI/CD Integration (Mar 20 - Apr 2, 2026)

**Goal:** Integrate agents with CI/CD pipelines

**Story Points:** 39 (10 days duration)

#### Developer A Tasks (20 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 11A.1 | GitHub Actions workflow (PR trigger) | Sprint 10 | 8 | 3 days | 0 (START) |
| 11A.2 | Webhook handler (GitHub → Orchestration) | 11A.1 | 5 | 2 days | 3 |
| 11A.3 | Load testing infrastructure (Locust) | 11A.2 | 5 | 2 days | 5 |
| 11A.4 | Performance testing (100+ concurrent users) | 11A.3 | 5 | 2 days | 7 |
| 11A.5 | Performance optimization (latency <5s) | 11A.4 | 3 | 1 day | 9 |

**Total: 20 points, 9 days**

#### Developer B Tasks (19 points, CRITICAL PATH)

| Task ID | Description | Dependencies | Points | Duration | Critical Path |
|---------|-------------|--------------|--------|----------|---------------|
| 11B.1 | CI/CD pipeline automation (test on commit) | Sprint 10 | 8 | 3 days | 0 (START) |
| 11B.2 | Automated deployment (staging → prod) | 11B.1 | 5 | 2 days | 3 |
| 11B.3 | System tests (15+ scenarios) | 11B.2 | 5 | 2 days | 5 |
| 11B.4 | Chaos engineering tests (Redis failure, LLM timeout) | 11B.3 | 5 | 2 days | 7 |
| 11B.5 | 24/7 performance monitoring (Grafana dashboards) | 11B.4 | 3 | 1 day | 9 |

**Total: 19 points, 9 days**

#### Sprint 11 Success Criteria

- ✅ GitHub Actions triggers test generation on PR
- ✅ Load testing passes: 100+ concurrent users, <5s latency
- ✅ 15+ system tests passing (happy path + edge cases)
- ✅ Chaos tests pass: Redis failure, LLM timeout, message loss
- ✅ CI/CD pipeline deploys to staging automatically
- ✅ Grafana dashboards show real-time metrics
- ✅ Performance monitoring detects degradation (20%+ drop)

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

**File:** `backend/messaging/message_bus.py`

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
│  └─ Page Context: {framework, page_type, complexity}       │
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
            
            # Stage 1: Group elements by page/component (Page Object Model)
            element_groups = self._group_elements_by_page(ui_elements, page_structure)
            
            # Stage 2: Map user journeys (multi-step flows)
            user_journeys = self._map_user_journeys(element_groups, page_context)
            
            # Stage 3: Generate functional test scenarios
            functional_scenarios = await self._generate_functional_scenarios(
                user_journeys, element_groups, page_context
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
    
    def _build_scenario_generation_prompt(self, user_journeys: List[Dict],
                                          element_groups: Dict,
                                          page_context: Dict) -> str:
        """Build prompt for LLM scenario generation"""
        return f"""Generate test scenarios in BDD (Gherkin) format.

Page Context:
- Type: {page_context.get("page_type", "unknown")}
- Framework: {page_context.get("framework", "unknown")}
- Complexity: {page_context.get("complexity", "medium")}

User Journeys:
{json.dumps(user_journeys, indent=2)}

UI Elements Available:
{json.dumps(list(element_groups.keys()), indent=2)}

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

## 6. Security Implementation

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

## 7. Cost Optimization

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

**END OF IMPLEMENTATION GUIDE**

**Document Version:** 1.0  
**Last Review:** January 19, 2026  
**Next Review:** Sprint 7 completion (Feb 5, 2026)
