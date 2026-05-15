# Hermes Agent — QA Multi-Agent Profiles (v2)
### Redesigned for ReqIQ Integration
**Version:** 2.1 | **Date:** 2026-05-15

---

## Overview

This document defines all Hermes Agent profiles for the QA Multi-Agent System, redesigned to use ReqIQ as the centralised Requirements Intelligence Hub. The architecture separates concerns across 5 profiles: one Manager and four Specialists. Each profile has a single responsibility, its own LLM model assignment, and explicit API contracts with ReqIQ and the Test Automation Webapp.

---

## Physical Node Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NODE 1 — Ubuntu Mini PC  (Server / Admin only — not daily human interface) │
│                                                                             │
│  • Hermes Agent (all 5 profiles)  — port 8080 HTTP gateway                 │
│  • ReqIQ API                      — port 8090                               │
│  • ReqIQ UI                       — port 3000                               │
│  • Ollama (qwen2.5:7b)            — port 11434                              │
│  • Garage S3 (self-hosted)        — port 3900                               │
│  • Redis                          — port 6379                               │
└────────────────────────┬────────────────────────────────────────────────────┘
                         │  LAN / Tailscale VPN
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌──────────────────────┐     ┌──────────────────────┐
│  NODE 2 — Windows PC │     │  NODE 3 — Windows PC │
│  (Primary human UI)  │     │  (Secondary runner)  │
│                      │     │                      │
│  AI Web Test Webapp  │     │  AI Web Test Webapp  │
│  API  — port 8000    │     │  API  — port 8000    │
│  UI   — port 5173    │     │  UI   — port 5173    │
│                      │     │                      │
│  QA engineers use    │     │  Parallel test runs  │
│  this UI daily:      │     │  dispatched here by  │
│  • View test cases   │     │  qa-dispatcher       │
│  • Trigger Hermes    │     │                      │
│  • Review results    │     │                      │
└──────────────────────┘     └──────────────────────┘
```

### Human Interface Pattern

- **Daily workflow** happens on **Node 2/3** (Windows PCs) via the AI Web Test Webapp UI
- **Node 1 is admin/server only** — QA engineers do not log into it directly
- **Two ways to trigger Hermes** from Node 2/3:
  1. **Telegram** — remote/mobile triggering, receives reports
  2. **HTTP API call** — AI Web Test Webapp sends a POST to Hermes on Node 1 directly (fire-and-forget)
- **Option chosen: Fire-and-forget + Telegram notification**
  - Webapp POSTs task to Hermes HTTP gateway → receives `job_id` immediately
  - Pipeline runs on Node 1 (3–10 min browser crawl)
  - Telegram notification sent when complete with test_case_id and pass/fail summary
  - Webapp shows a "Recent Hermes Jobs" status panel (polls job status)

---

### How Profiles Work in Hermes

Each profile is an independent Hermes Agent instance with its own config, memory, skills, and gateway connection. Create them with:

```bash
hermes profile create "qa-manager"
hermes profile create "qa-requirements"
hermes profile create "qa-test-gen"
hermes profile create "qa-dispatcher"
hermes profile create "qa-reporter"
```

Switch to configure each:
```bash
hermes --profile qa-manager setup
hermes --profile qa-manager model   # set model
```

All profiles on the same machine share the same MCP tool registry but maintain independent memory and session history.

---

## Profile 1 — QA Manager Agent

**Profile name:** `qa-manager`
**Role:** Orchestrator. Receives requests from humans (via Telegram) and from the Test Automation Webapp (via REST API). Routes tasks to specialist profiles using `delegate_task`. Never executes tasks directly.

### Model Assignment
```yaml
model: anthropic/claude-3.5-sonnet   # via OpenRouter
# Rationale: Complex intent parsing, multi-step routing decisions,
# highest quality needed for orchestration judgements
```

### System Prompt

```
You are the QA Manager Agent for the company's AI-powered QA system.
You coordinate a team of specialist agents to automate and accelerate
software quality assurance across all projects.

YOUR TEAM:
- qa-requirements: Queries ReqIQ knowledge base and checks completeness
- qa-test-gen: Generates Test Instruction JSON by calling the test generation API
- qa-dispatcher: Distributes test execution across available Windows test runners
- qa-reporter: Compiles results, screenshots, and sends structured reports

YOUR TOOLS:
- delegate_task: Send a task to a specialist profile and wait for result
- http_request: Call external APIs directly if needed
- telegram_send: Send messages to human stakeholders

DECISION RULES:
1. If a human requests test generation for a feature:
   a. Delegate to qa-requirements first — check completeness score
   b. If completeness < 60: notify human of missing documents, STOP
   c. If completeness >= 60: delegate to qa-test-gen with the wiki content
   d. Once test cases are generated: delegate to qa-dispatcher
   e. Once execution completes: delegate to qa-reporter

2. If a scheduled regression run triggers:
   a. Delegate to qa-dispatcher directly (test cases already exist)
   b. Delegate to qa-reporter when complete

3. If a human asks about test results or status:
   a. Retrieve from Garage S3 results bucket or delegate to qa-reporter

4. If a human uploads requirements and requests knowledge base update:
   a. Confirm the upload was received by ReqIQ via its API
   b. Wait for compilation (poll /api/v1/documents/{id}/status)
   c. Notify human when wiki is updated with new completeness score

COMMUNICATION STYLE:
- Always respond in the same language the human used
- Keep Telegram messages concise — lead with the outcome, details on request
- For failures, always include: what failed, why (if known), and next action
```

### MCP Tools Configuration

```yaml
# ~/.hermes/profiles/qa-manager/mcp_tools.yaml
tools:
  reqiq_query:
    type: http
    method: POST
    url: "http://localhost:8090/api/v1/query"
    headers:
      Authorization: "Bearer ${REQIQ_API_KEY}"
    description: "Query ReqIQ for compiled requirements of a specific feature"

  reqiq_feature_list:
    type: http
    method: GET
    url: "http://localhost:8090/api/v1/projects/{project}/features"
    headers:
      Authorization: "Bearer ${REQIQ_API_KEY}"
    description: "List all features and completeness scores for a project"

  test_webapp_run:
    type: http
    method: POST
    url: "http://{WINDOWS_RUNNER_IP}:{PORT}/api/execute"
    headers:
      Authorization: "Bearer ${TEST_WEBAPP_API_KEY}"
    description: "Trigger test execution on a Windows test runner"
```

### Gateway Setup — Telegram + HTTP

qa-manager has **two gateways**: Telegram for human/mobile triggering, and HTTP REST for programmatic calls from AI Web Test Webapp and ReqIQ.

```bash
# Gateway 1 — Telegram (human interface, mobile, notifications)
hermes --profile qa-manager gateway setup
# Select: Telegram
# Bot name: QA Manager Bot
# Allowed users: [your Telegram user ID, team lead IDs]

# Gateway 2 — HTTP REST (called by AI Web Test Webapp and ReqIQ programmatically)
hermes --profile qa-manager gateway add
# Select: HTTP
# Port: 8080
# Set a strong API key — this is HERMES_HTTP_API_KEY in AI Web Test .env
```

This exposes:
```
POST http://node1-ip:8080/hermes/qa-manager/message
Authorization: Bearer ${HERMES_HTTP_API_KEY}
Content-Type: application/json

{ "message": "Generate and run tests for 5G Voucher Plan in Three-HK",
  "feature_url": "https://wwwuat.three.com.hk/...",
  "project": "Three-HK",
  "feature": "5G Voucher Plan Purchase" }
```

Hermes responds immediately with:
```json
{ "job_id": "hermes-job-abc123", "status": "accepted", "message": "Pipeline started" }
```
The pipeline then runs asynchronously on Node 1. Results arrive via Telegram.

### Cron Schedule

```yaml
# ~/.hermes/profiles/qa-manager/cron/nightly-regression.yaml
name: nightly-regression
schedule: "0 2 * * *"    # 2:00 AM daily
message: |
  Run nightly regression suite.
  Delegate to qa-dispatcher for all active projects.
  Do not ask for confirmation — auto-approve and run.
auto_approve: true
```

---

## Profile 2 — Requirements Agent

**Profile name:** `qa-requirements`
**Role:** Single-responsibility — query ReqIQ, assess completeness, format requirements into a Test Instruction JSON-ready context. Never calls the test execution API.

### Model Assignment

```yaml
model: openai/gpt-4o   # via OpenRouter
# Rationale: Needs strong reasoning for completeness assessment
# and multi-document synthesis. Also handles vision for any
# image-heavy documents if passed as base64.
# Cost-optimised: only called once per feature per new document upload.
```

### System Prompt

```
You are the Requirements Agent. Your sole job is to retrieve structured
requirements from the ReqIQ knowledge base and assess whether they are
sufficient for test case generation.

WORKFLOW:
1. Receive: project name + feature name (from qa-manager via delegate_task)
2. Call reqiq_query tool with the project and feature
3. Evaluate the response:
   - If completeness_score < 60:
     Return: { "status": "insufficient", "score": N, "missing": [...], "message": "..." }
   - If contradictions_count > 0:
     Return the wiki content AND flag contradictions for qa-manager to notify human
   - If completeness_score >= 60:
     Return: { "status": "ready", "score": N, "wiki_content": "...", "feature": "...", "project": "..." }

4. If ReqIQ returns no wiki page (feature has no documents at all):
   a. Use browser_navigate to visit the feature URL if provided
   b. Extract visible UI elements, form fields, and navigation flows
   c. Call reqiq_upload tool to create a minimal "UI Crawl" document in ReqIQ
   d. Wait 60 seconds for compilation
   e. Re-query and return result

IMPORTANT:
- Never generate test cases yourself — that is qa-test-gen's job
- Never trigger test execution — that is qa-dispatcher's job
- Your output is always a structured JSON object, never free-form prose
- If ReqIQ API is unreachable, return: { "status": "error", "message": "ReqIQ unavailable" }
```

### MCP Tools

```yaml
tools:
  reqiq_query:
    type: http
    method: POST
    url: "http://localhost:8090/api/v1/query"
    headers:
      Authorization: "Bearer ${REQIQ_API_KEY}"

  reqiq_upload:
    type: http
    method: POST
    url: "http://localhost:8090/api/v1/documents/upload"
    headers:
      Authorization: "Bearer ${REQIQ_API_KEY}"
    description: "Upload a crawled UI document to ReqIQ as fallback source"

  reqiq_status:
    type: http
    method: GET
    url: "http://localhost:8090/api/v1/documents/{document_id}/status"
    headers:
      Authorization: "Bearer ${REQIQ_API_KEY}"
```

---

## Profile 3 — Test Generation Agent

**Profile name:** `qa-test-gen`
**Role:** Receives compiled requirements context from qa-requirements (via qa-manager) **plus environment config**, constructs a `crawl-and-save-test` request body, calls the AI Web Test API, polls until the browser crawl completes, and returns the saved `test_case_id`.

> **API endpoint (corrected):** `POST ${TEST_WEBAPP_URL}/api/v2/crawl-and-save-test`  
> The old URL `/api/test-cases/generate` does **not** exist — it returns 404.

---

### Model Assignment

```yaml
model: openai/gpt-4o-mini   # via OpenRouter
# Rationale: The main LLM task is extracting a step-by-step user_instruction
# from the wiki_content. The heavy reasoning happened in ReqIQ's compile step.
# gpt-4o-mini is sufficient and keeps per-generation cost low.
```

---

### What qa-test-gen Receives vs What It Must Build

This is the critical question: the `crawl-and-save-test` API needs specific fields that come from **two different sources**:

| Field in API body | Source | Who provides it |
|---|---|---|
| `url` | Feature's target URL (UAT/preprod environment) | `qa-manager` passes it in delegate_task as `feature_url` |
| `user_instruction` | **Derived by LLM** from wiki_content — extract the step sequence described in acceptance criteria | `qa-test-gen` generates this |
| `stop_at_page_hint` | **Derived by LLM** from wiki — look for "stops at", "end state", "final page" language | `qa-test-gen` generates this |
| `test_title` | **Derived by LLM** from feature name + wiki summary | `qa-test-gen` generates this |
| `test_description` | **Derived by LLM** from wiki | `qa-test-gen` generates this |
| `login_module` | Infrastructure config — fixed per environment | `qa-manager` passes in `env_config` |
| `existing_subscriber_module` | Infrastructure config | `qa-manager` passes in `env_config` |
| `new_subscriber_module` | Infrastructure config | `qa-manager` passes in `env_config` |
| `subscriber_type_hint` | Infrastructure config | `qa-manager` passes in `env_config` |
| `login_credentials` | Secret — stored in environment variables | Read from `${TEST_LOGIN_USERNAME}` / `${TEST_LOGIN_PASSWORD}` |
| `http_credentials` | UAT gate credentials | Read from `${HTTP_AUTH_USERNAME}` / `${HTTP_AUTH_PASSWORD}` |
| `max_browser_steps` | Infrastructure config — default 50 for focused flows | `qa-manager` passes in `env_config`, or use default |
| `reference_test_id` | Optional gold-standard test case for LLM review pass | `qa-manager` passes in `env_config` if known |
| `tags` | Derived from project/feature names | `qa-test-gen` generates this |

---

### INPUT Format (from qa-manager via delegate_task)

```json
{
  "project": "Three-HK",
  "feature": "5G Voucher Plan Purchase",
  "wiki_content": "## 5G Voucher Plan Purchase\n\n### Acceptance Criteria\n1. User can navigate to 5G Monthly Plan section\n2. User can select the $288 voucher plan\n3. User can complete subscription by choosing new mobile number + Physical SIM\n4. Flow stops at SIM Setting page — no SIM details are submitted in this test\n\n### Flow Description\nUser logs in → clicks '5G Monthly Plan' in left menu → clicks 'Voucher monthly plan' tab → selects '$288 plan' → clicks 'Subscribe Now' → agrees to T&C → selects 'New mobile number' → selects 'Physical SIM' → arrives at SIM Card Setting page.\n\n### End State\nSIM Card Setting page is displayed. Test completes here.",
  "completeness_score": 87,
  "feature_url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
  "env_config": {
    "login_module": "login_my3_andrew",
    "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
    "new_subscriber_module": "plan_subscriber_flow_andrew",
    "subscriber_type_hint": "auto",
    "max_browser_steps": 50,
    "max_flow_timeout_seconds": 600,
    "reference_test_id": 1217,
    "available_file_paths": ["C:/Users/andrechw/Downloads/ekyctest/test06.jpg"]
  }
}
```

---

### System Prompt

```
You are the Test Generation Agent. You receive a compiled requirements wiki
and environment config from qa-manager, then generate ONE test case by calling
the AI Web Test crawl-and-save API.

INPUT FIELDS (from delegate_task):
- project: project name
- feature: feature name
- wiki_content: compiled markdown from ReqIQ
- completeness_score: number
- feature_url: the UAT/preprod URL the browser will open
- env_config: object with login_module, subscriber modules, max_browser_steps, etc.

─────────────────────────────────────────────────────
STEP 1 — READ the wiki_content carefully and extract:

  a) user_instruction:
     Write a step-by-step instruction in plain English describing exactly
     what the browser should do. Use imperative sentences. Be explicit about
     every click and modal. End with a STOP instruction that names the final page.

     Example (derived from a 5G plan wiki):
     "Login with the provided credentials. After login: do NOT click Settings.
      Click 5G Monthly Plan on the left menu.
      Click voucher monthly plan tab.
      Find and Select $288 plan from the available plans.
      Click Subscribe Now.
      Agree to Terms and Conditions if a modal appears.
      Click 'New mobile number' from Service Subscription.
      Click 'Physical SIM' from SIM Card Type.
      STOP as soon as the SIM Card Setting page appears.
      Do NOT fill any fields on the SIM Setting page. Stop immediately."

  b) stop_at_page_hint:
     A short substring of the final page name (e.g. "SIM Card Setting").
     The browser will stop as soon as this appears in the page title or URL.
     Extract this from the wiki's "End State" or "stops at" description.

  c) test_title:
     Short, specific. Format: "{Feature} — {scenario variant}"
     Example: "5G Voucher Plan $288/month — new subscriber purchase flow"

  d) test_description:
     One paragraph explaining what this test covers and what modules handle.
     Mention the step library modules by name.

  e) tags:
     Array of lowercase slugs from the project/feature names.
     Example: ["5g", "voucher-plan", "purchase-flow", "three-hk"]

─────────────────────────────────────────────────────
STEP 2 — BUILD the crawl-and-save-test request body:

Combine your extracted fields (step 1) with the provided env_config and
credentials from environment variables:

{
  "url":                        <feature_url from input>,
  "user_instruction":           <extracted in step 1a>,
  "stop_at_page_hint":          <extracted in step 1b>,
  "test_title":                 <extracted in step 1c>,
  "test_description":           <extracted in step 1d>,
  "test_type":                  "e2e",
  "priority":                   "high",
  "tags":                       <extracted in step 1e>,
  "login_module":               <env_config.login_module>,
  "existing_subscriber_module": <env_config.existing_subscriber_module>,
  "new_subscriber_module":      <env_config.new_subscriber_module>,
  "subscriber_type_hint":       <env_config.subscriber_type_hint>,
  "max_browser_steps":          <env_config.max_browser_steps or 50>,
  "max_flow_timeout_seconds":   <env_config.max_flow_timeout_seconds or 600>,
  "reference_test_id":          <env_config.reference_test_id or null>,
  "available_file_paths":       <env_config.available_file_paths or null>,
  "login_credentials": {
    "username": "<TEST_LOGIN_USERNAME env var>",
    "password": "<TEST_LOGIN_PASSWORD env var>"
  },
  "http_credentials": {
    "username": "<HTTP_AUTH_USERNAME env var>",
    "password": "<HTTP_AUTH_PASSWORD env var>"
  }
}

─────────────────────────────────────────────────────
STEP 3 — CALL test_webapp_crawl_and_save with the body above.

The API returns immediately with:
  { "workflow_id": "...", "status": "pending" }

─────────────────────────────────────────────────────
STEP 4 — POLL test_webapp_workflow_status every 15 seconds.

  Call GET /api/v2/workflows/{workflow_id}
  Loop until status = "completed" OR "failed" OR timeout (15 minutes).

  If status = "completed":
    Extract result.test_case_id from the results endpoint.
    Call test_webapp_workflow_results to get the full result object.

  If status = "failed":
    Return the error to qa-manager immediately — do not retry.

─────────────────────────────────────────────────────
STEP 5 — RETURN to qa-manager:

{
  "status": "success",
  "test_case_id": 1291,
  "workflow_id": "b3d2f1a0-...",
  "test_title": "...",
  "subscriber_type_detected": "existing",
  "total_steps": 18,
  "crawled_steps_count": 12
}

─────────────────────────────────────────────────────
IMPORTANT:
- Never invent steps not described in the wiki_content
- The user_instruction must read like a human QA tester's instruction, not a JSON schema
- If wiki_content has no clear "end state" or stop page, ask qa-manager for clarification before calling the API
- If the API returns 401, the token has expired — notify qa-manager to re-authenticate
- If the API returns 422, log the full detail field — it means the body is malformed
- Typical crawl duration: 3–10 minutes. Do not timeout before 15 minutes.
```

---

### MCP Tools

```yaml
tools:
  test_webapp_crawl_and_save:
    type: http
    method: POST
    url: "${TEST_WEBAPP_URL}/api/v2/crawl-and-save-test"
    headers:
      Authorization: "Bearer ${TEST_WEBAPP_API_KEY}"
      Content-Type: "application/json"
    description: "Submit a crawl-and-save job. Browser crawls the feature URL following user_instruction. Returns workflow_id immediately — job runs in background."

  test_webapp_workflow_status:
    type: http
    method: GET
    url: "${TEST_WEBAPP_URL}/api/v2/workflows/{workflow_id}"
    headers:
      Authorization: "Bearer ${TEST_WEBAPP_API_KEY}"
    description: "Poll workflow status. Returns status (pending/running/completed/failed) and progress. Poll every 15 seconds."

  test_webapp_workflow_results:
    type: http
    method: GET
    url: "${TEST_WEBAPP_URL}/api/v2/workflows/{workflow_id}/results"
    headers:
      Authorization: "Bearer ${TEST_WEBAPP_API_KEY}"
    description: "Get final results once workflow is completed. Returns test_case_id, total_steps, subscriber_type_detected, and module names used."
```

---

### Environment Variables (Profile-specific)

```bash
# ~/.hermes/profiles/qa-test-gen/.env
TEST_WEBAPP_URL=http://192.168.1.101:8000
TEST_WEBAPP_API_KEY=your-test-webapp-api-key

# Login credentials used by the browser during crawl
TEST_LOGIN_USERNAME=pmo.andrewchan+015@gmail.com
TEST_LOGIN_PASSWORD=your-password-here

# HTTP Basic auth for UAT/preprod gate
HTTP_AUTH_USERNAME=uat_user
HTTP_AUTH_PASSWORD=uat_password
```

> **Security note:** Never put credentials in the delegate_task payload or wiki_content. Always read from environment variables so they are not logged in Hermes session memory.

---

## Profile 4 — Dispatcher Agent

**Profile name:** `qa-dispatcher`
**Role:** Manages test execution scheduling across multiple Windows RDP instances. Selects available runners, dispatches test cases, and monitors execution status.

### Model Assignment

```yaml
model: ollama/qwen2.5:7b   # LOCAL — runs on mini PC via Ollama
# Rationale: Pure routing logic — check runner availability, assign test IDs,
# monitor status. No complex reasoning needed. Zero API cost.
# This agent runs frequently (nightly + on-demand), so local model saves money.
```

### System Prompt

```
You are the Test Dispatcher Agent. You manage test execution across
multiple Windows test runner instances.

RUNNER REGISTRY:
# Update this list as Windows runners are added/removed
- runner-01: http://192.168.1.101:3001
- runner-02: http://192.168.1.102:3001
- runner-03: http://192.168.1.103:3001

WORKFLOW:
1. Receive: list of test_case_ids from qa-manager
2. Check availability of each runner via GET /api/status
3. Select available runners (status: "idle")
4. Distribute test cases across available runners (round-robin)
5. For each runner, call POST /api/execute with assigned test case IDs
6. Poll GET /api/execution/{execution_id}/status every 30 seconds
7. When all runners complete, collect results:
   { runner: "runner-01", execution_id: "...", passed: N, failed: N, results_path: "..." }
8. Return aggregated results to qa-manager

FAILURE HANDLING:
- If a runner is unavailable: redistribute its cases to other available runners
- If all runners are unavailable: notify qa-manager, do not retry automatically
- If a runner reports execution error (not test failure): retry that runner's cases once on a different runner
- Test failures are EXPECTED outcomes — do not treat as system errors

IMPORTANT:
- Never modify test cases — execute exactly what was provided
- Results files (screenshots, HTML reports) are saved by the Windows runner
  to Garage S3 at: test-results/{project}/{feature}/{run_timestamp}/
- Return the S3 path in your result so qa-reporter can find them
```

### MCP Tools

```yaml
tools:
  runner_status:
    type: http
    method: GET
    url: "{runner_url}/api/status"
    description: "Check if a Windows test runner is idle and available"

  runner_execute:
    type: http
    method: POST
    url: "{runner_url}/api/execute"
    description: "Start test execution on a Windows runner with test case IDs"

  runner_execution_status:
    type: http
    method: GET
    url: "{runner_url}/api/execution/{execution_id}/status"
    description: "Poll execution status from a Windows runner"
```

---

## Profile 5 — Reporter Agent

**Profile name:** `qa-reporter`
**Role:** Retrieves execution results from Garage S3, compiles a structured report, and sends it to the appropriate stakeholders via Telegram with different detail levels for the IT team vs UAT team.

### Model Assignment

```yaml
model: openai/gpt-4o-mini   # via OpenRouter
# Rationale: Template-based report generation.
# Cheap model appropriate — formatting task, not reasoning task.
```

### System Prompt

```
You are the QA Reporter Agent. You compile test results into clear,
actionable reports for two different audiences:

AUDIENCE A — IT / Development Team (Technical)
- Full pass/fail breakdown by test case
- Error messages and stack traces
- Screenshot paths for failed tests
- Performance metrics (execution time per scenario)

AUDIENCE B — UAT Team (Non-Technical, different department)
- Plain language summary: "X out of Y scenarios passed"
- Business-language description of what failed (not technical errors)
- Screenshots of failures embedded in report
- Clear action items: "Please review the Checkout page button colour"

WORKFLOW:
1. Receive: { project, feature, run_timestamp, s3_results_path, audience }
2. Download results JSON from Garage S3 at the provided path
3. If screenshots are available, include the S3 download URLs in the report
4. Compose report appropriate for the audience
5. Send via Telegram to the appropriate channel:
   - IT team: use TELEGRAM_IT_CHAT_ID
   - UAT team: use TELEGRAM_UAT_CHAT_ID
   - Both (for regression runs): send both versions

REPORT FORMAT — Telegram (concise):
📊 QA Report: {feature} ({project})
✅ Passed: {N}/{total}
❌ Failed: {N}/{total} — [see details below]
⏱ Duration: {X} minutes
🔗 Full report: {s3_html_report_url}

Failed scenarios:
• TC-LOGIN-003: Password field accepts < 8 characters [screenshot]
• TC-LOGIN-007: Error message not displayed on invalid email [screenshot]

Action required: {yes/no} — {brief plain-language description}

IMPORTANT:
- Always include screenshot links for failed tests — never omit them
- Never blame the testing tool in the report — describe what the application did
- For UAT audience: never use technical terms (no "assertion error", "timeout", "selector")
- Save the full HTML report to Garage S3 at: test-results/{project}/{feature}/{run}/report.html
```

### Telegram Gateway Setup

```bash
hermes --profile qa-reporter gateway setup
# Can share same bot as qa-manager OR use a separate dedicated bot
# Recommended: separate bot named "QA Reports Bot" for cleaner separation
# Add both IT chat ID and UAT chat ID as allowed recipients
```

### Environment Variables

```bash
# ~/.hermes/profiles/qa-reporter/.env
TELEGRAM_IT_CHAT_ID=-100123456789       # IT team group chat
TELEGRAM_UAT_CHAT_ID=-100987654321      # UAT team group chat
GARAGE_S3_ENDPOINT=http://localhost:3900
GARAGE_S3_BUCKET=test-results
GARAGE_ACCESS_KEY=your-garage-key
GARAGE_SECRET_KEY=your-garage-secret
```

---

## Agent Communication Flow (Full Pipeline)

```
TRIGGER (Option A — from AI Web Test Webapp UI, fire-and-forget):
  POST http://node1:8080/hermes/qa-manager/message
  Body: { project, feature, feature_url, env_config }
  ← Immediate response: { job_id: "hermes-job-abc123", status: "accepted" }
  User continues working. Telegram notification arrives when done (8–15 min later).

TRIGGER (Option B — Telegram, for remote/mobile use):
  Developer sends Telegram message to qa-manager:
  "Generate and run tests for Login feature in Project-X"

qa-manager
  │
  ├──► delegate_task → qa-requirements
  │         │ Queries ReqIQ: POST /api/v1/query {project: "Project-X", feature: "Login"}
  │         │ ReqIQ returns: completeness_score: 87, wiki_content: "..."
  │         └─► Returns to qa-manager: { status: "ready", score: 87, wiki_content: "..." }
  │
  ├──► delegate_task → qa-test-gen
  │         │ Receives: wiki_content + feature_url + env_config
  │         │
  │         │ LLM extracts from wiki_content:
  │         │   → user_instruction (step-by-step, imperative)
  │         │   → stop_at_page_hint ("SIM Card Setting")
  │         │   → test_title, test_description, tags
  │         │
  │         │ Combines with env_config + credentials from env vars:
  │         │   → url, login_module, subscriber modules, max_browser_steps
  │         │   → login_credentials (from TEST_LOGIN_USERNAME/PASSWORD)
  │         │
  │         │ Calls Test Webapp: POST /api/v2/crawl-and-save-test
  │         │   ← Returns: { workflow_id: "b3d2f1a0-..." }
  │         │
  │         │ Polls: GET /api/v2/workflows/{workflow_id} every 15s
  │         │   (browser crawl takes 3–10 minutes)
  │         │   ← Returns: { status: "completed", result: { test_case_id: 1291 } }
  │         │
  │         └─► Returns to qa-manager: { status: "success", test_case_id: 1291 }
  │
  ├──► delegate_task → qa-dispatcher
  │         │ Checks runner-01: idle ✓, runner-02: idle ✓, runner-03: busy ✗
  │         │ Distributes: runner-01 gets TC-001–TC-006, runner-02 gets TC-007–TC-012
  │         │ Polls status every 30s...
  │         │ runner-01 completes (4 passed, 2 failed)
  │         │ runner-02 completes (5 passed, 1 failed)
  │         └─► Returns: { passed: 9, failed: 3, s3_path: "test-results/Project-X/Login/20260510-1430/" }
  │
  └──► delegate_task → qa-reporter
            │ Downloads results from Garage S3
            │ Composes IT report (technical detail)
            │ Composes UAT report (plain language)
            │ Sends both via Telegram
            └─► Done. qa-manager sends Telegram to original requester:
                  "✅ Test generated: 5G Voucher Plan $288 (test_case_id: 1291)
                   9/12 steps passed. 3 failed — see full report: [S3 link]"

Total time (typical): 8–15 minutes end-to-end
Human involvement: 0 steps after initial trigger
Human notification: Telegram when complete (fire-and-forget pattern)
```

---

## Environment Variables Reference

All profiles share access to these via `~/.hermes/.env`:

```bash
# ReqIQ
REQIQ_API_KEY=your-reqiq-api-key
REQIQ_URL=http://localhost:8090

# Test Automation Webapp (AI Web Test — port 8000, NOT 3001)
TEST_WEBAPP_URL=http://192.168.1.101:8000   # Node 2 primary runner
TEST_WEBAPP_URL_NODE3=http://192.168.1.102:8000  # Node 3 secondary runner
TEST_WEBAPP_API_KEY=your-test-webapp-key

# Hermes HTTP Gateway (used by AI Web Test Webapp to trigger Hermes)
HERMES_HTTP_API_KEY=your-hermes-http-gateway-key
HERMES_HTTP_URL=http://node1-ip:8080

# Garage S3
GARAGE_S3_ENDPOINT=http://localhost:3900
GARAGE_ACCESS_KEY=your-garage-access-key
GARAGE_SECRET_KEY=your-garage-secret-key

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_IT_CHAT_ID=-100123456789
TELEGRAM_UAT_CHAT_ID=-100987654321

# LLM
OPENROUTER_API_KEY=your-openrouter-key
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Profile Setup Commands (In Order)

```bash
# 1. Create all profiles
hermes profile create "qa-manager"
hermes profile create "qa-requirements"
hermes profile create "qa-test-gen"
hermes profile create "qa-dispatcher"
hermes profile create "qa-reporter"

# 2. Set models for each profile
hermes --profile qa-manager model       # → select claude-3.5-sonnet via OpenRouter
hermes --profile qa-requirements model  # → select gpt-4o via OpenRouter
hermes --profile qa-test-gen model      # → select gpt-4o-mini via OpenRouter
hermes --profile qa-dispatcher model    # → select qwen2.5:7b via Ollama
hermes --profile qa-reporter model      # → select gpt-4o-mini via OpenRouter

# 3. Copy system prompts from this document into each profile via:
hermes --profile qa-manager setup       # paste system prompt when prompted

# 4. Add MCP tools for each profile
hermes --profile qa-manager tools       # add HTTP tools from this document

# 5. Set up gateways
hermes --profile qa-manager gateway setup   # Telegram
hermes --profile qa-manager gateway add     # HTTP REST (port 8080) — for webapp/ReqIQ calls
hermes --profile qa-reporter gateway setup  # Telegram (for sending reports)

# 6. Add nightly cron to qa-manager
hermes --profile qa-manager cron add    # paste cron config from Profile 1 section

# 7. Verify
hermes doctor --profile qa-manager
hermes doctor --profile qa-requirements
```

---

---

## AI Web Test Webapp — Hermes Trigger Endpoint

This is the small addition needed on **Node 2/3** (AI Web Test backend) to enable the "Generate via Hermes" button in the webapp UI. It proxies the request to Hermes on Node 1 and returns the job ID immediately (fire-and-forget).

### New endpoint: `POST /api/v1/hermes/trigger`

**Request body:**
```json
{
  "project": "Three-HK",
  "feature": "5G Voucher Plan Purchase",
  "feature_url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
  "env_config": {
    "login_module": "login_my3_andrew",
    "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
    "new_subscriber_module": "plan_subscriber_flow_andrew",
    "subscriber_type_hint": "auto",
    "max_browser_steps": 50,
    "reference_test_id": 1217
  }
}
```

**Response 202** (accepted, pipeline running on Node 1):
```json
{
  "job_id": "hermes-job-abc123",
  "status": "accepted",
  "message": "Hermes pipeline started. You will receive a Telegram notification when complete.",
  "estimated_duration_minutes": "8–15"
}
```

**How the endpoint works internally:**
```
User clicks "Generate via Hermes" in AI Web Test UI (Node 2)
  → POST /api/v1/hermes/trigger
  → Backend validates request
  → Backend POSTs to Hermes HTTP gateway on Node 1:
       POST http://node1:8080/hermes/qa-manager/message
       { message: "Generate and run tests for 5G Voucher Plan in Three-HK",
         project, feature, feature_url, env_config }
  → Hermes returns { job_id } immediately
  → Backend returns 202 with job_id to frontend
  → Frontend shows "Job started — watch Telegram for results"

Meanwhile on Node 1 (8–15 minutes later):
  → qa-requirements → qa-test-gen → qa-dispatcher → qa-reporter
  → Telegram sent: "✅ Test generated: test_case_id 1291. 9/12 passed."
```

**Optional: Job status polling**

The frontend can show a status panel by polling:
```
GET http://node1:8080/hermes/jobs/{job_id}
Authorization: Bearer ${HERMES_HTTP_API_KEY}
```
Returns: `{ status: "running" | "completed" | "failed", current_agent: "qa-test-gen", ... }`

### Environment variables to add to AI Web Test `.env`

```bash
# Node 1 Hermes HTTP gateway
HERMES_HTTP_URL=http://192.168.1.100:8080
HERMES_HTTP_API_KEY=your-hermes-http-gateway-key
```

---

## What Changed from v1 to v2

| Area | v1 | v2 |
|------|----|----|
| Requirements source | Hermes reads files directly | Hermes queries ReqIQ API |
| Document storage | Samba share / local filesystem | Garage S3 via ReqIQ |
| Completeness scoring | Done inside Requirements Agent | Done by ReqIQ on ingest |
| Knowledge accumulation | RAG-style re-parsing | LLM-Wiki compile-once pattern |
| Contradiction detection | None | ReqIQ flags on wiki page |
| UAT team access | None | ReqIQ web UI + Telegram reports |
| Dispatcher model cost | Cloud LLM | Local Qwen — zero API cost |
| Report audiences | Single IT report | Separate IT + UAT reports |
