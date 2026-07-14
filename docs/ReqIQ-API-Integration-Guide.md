# AI Web Test — API Integration Guide for ReqIQ

**Version** 1.2 · **Date** 2026-07-03  
**Base URL** `http://<host>:8000`  
**OpenAPI spec** → `backend/openapi_spec.json` (import into Postman / Insomnia)  
**Interactive docs** → `http://localhost:8000/api/v1/docs` (Swagger UI, live server only)  
**Live OpenAPI JSON** → `http://localhost:8000/api/v1/openapi.json`  
**Execution architecture** → [`documentation/ADR-002-test-execution-engine.md`](../documentation/ADR-002-test-execution-engine.md) (three-tier engine, Accepted March 2026)

---

## Table of Contents

0. [Architecture & Hermes Agent Flow](#0-architecture--hermes-agent-flow)
1. [Authentication](#1-authentication)
2. [Knowledge Base — Upload Requirement Documents](#2-knowledge-base--upload-requirement-documents)
3. [Crawl-and-Save Test (PRIMARY endpoint)](#3-generate-a-test-case-from-a-url-crawl-and-save)
4. [Track Workflow Progress (SSE or Polling)](#4-track-workflow-progress-sse-or-polling)
5. [Test Case CRUD — Create, Read, Update, Delete](#5-test-case-crud--create-read-update-delete)
6. [Test Steps & Version Control](#6-test-steps--version-control)
7. [Execute a Test Case](#7-execute-a-test-case)
8. [Get Execution Results & AI Root-Cause Analysis](#8-get-execution-results--ai-root-cause-analysis)
9. [Convenience: Quick Test Generation (LLM-only, no browser crawl)](#9-convenience-quick-test-generation-llm-only-no-browser-crawl)
10. [Error Codes](#10-error-codes)
11. [Common Flows for ReqIQ](#11-common-flows-for-reqiq)
12. [ReqIQ Proxy Endpoints](#12-reqiq-proxy-endpoints)
    - [12.7 Get Latest IQ Score](#127-get-latest-iq-score-for-a-requirement)
    - [12.8 Project Readiness Check](#128-project-readiness-check)

---

## 0. Architecture & Hermes Agent Flow

### 0.1 Three-System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  HERMES  (multi-agent orchestration — triggered by Telegram)    │
│                                                                 │
│  qa-manager     → Claude 3.5 Sonnet  (orchestrator)            │
│  qa-requirements→ GPT-4o             (analyses requirement docs)│
│  qa-test-gen    → GPT-4o-mini        (generates test cases)     │
│  qa-dispatcher  → Qwen 2.5:7b local  (dispatches executions)   │
│  qa-reporter    → GPT-4o-mini        (sends Telegram reports)   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                                         ▼
┌─────────────────────┐               ┌────────────────────────────┐
│  REQIQ WEBAPP        │               │  AI WEB TEST WEBAPP         │
│  Port 3001 (API)    │◄──────────────►│  Port 8000 (API)           │
│  Port 8080 (UI)     │               │  Port 5173 (UI / dev)      │
│                     │               │                            │
│  • Ingests PPTX,    │               │  • Crawls URLs with        │
│    Figma, Word,     │               │    browser-use             │
│    Email, JIRA      │               │  • Generates & stores      │
│  • Compiles reqs    │               │    test cases (SQLite)     │
│    via Ollama       │               │  • Executes tests with     │
│  • Outputs wiki +   │               │    Stagehand/Playwright    │
│    completeness     │               │  • AI root-cause analysis  │
│    score            │               │    on failures             │
└─────────────────────┘               └────────────────────────────┘
```

- **ReqIQ** is the requirements intelligence hub. It receives raw requirement documents and produces structured, scored test instructions. It calls **AI Web Test** as its execution backend.
- **AI Web Test** owns the test case database, browser automation, and execution engine. ReqIQ never stores test cases directly — it delegates to this webapp.
- **Hermes** orchestrates both. It wires the two systems together via MCP tool calls and reports results back to the QA team via Telegram.

---

### 0.2 Hermes Agent → API Endpoint Mapping

This is the exact sequence Hermes runs for each QA cycle. Each agent calls a specific endpoint in a specific system:

| # | Hermes Agent | Calls | Endpoint | Purpose |
|---|---|---|---|---|
| 1 | `qa-requirements` | **ReqIQ** `POST /api/v1/projects/{id}/rag/query` | ReqIQ internal | RAG Q&A over uploaded source docs — returns answer + citations |
| 2 | `qa-test-gen` | **AI Web Test** `POST /api/v2/crawl-and-save-test` | Section 3 below | Crawls the target URL, saves test case → returns `test_case_id` |
| 3 | `qa-dispatcher` | **AI Web Test** `POST /api/v1/executions/tests/{id}/execute` | Section 7 below | Executes the saved test case → returns `execution_id` |
| 4 | `qa-reporter` | **AI Web Test** `GET /api/v1/executions/{id}/step-results` | Section 8 below | Downloads results + AI RCA, sends Telegram summary |

> **⚠️ Known issue in Hermes profile v2:** The `qa-test-gen` profile contains `url: "${TEST_WEBAPP_URL}/api/test-cases/generate"` — **this endpoint does not exist** and will return 404. The correct URL is `${TEST_WEBAPP_URL}/api/v2/crawl-and-save-test`. Update the Hermes profile before running the pipeline.

---

### 0.3 Base URLs per Environment

| System | Role | Local Dev URL | LAN / Production URL |
|---|---|---|---|
| AI Web Test API | Test case DB + executor | `http://localhost:8000` | `http://192.168.1.101:8000` |
| AI Web Test UI | Dashboard | `http://localhost:5173` | `http://192.168.1.101:5173` |
| ReqIQ API | Requirements hub | `http://localhost:3001` | `http://192.168.1.100:3001` |
| ReqIQ UI | Requirements dashboard | `http://localhost:8080` | `http://192.168.1.100:8080` |

> **Port note:** ReqIQ UI port is set in `docker-compose.yml` under the `web` service (`ports: - '8080:80'`). To change it, update the host-side port in that file (e.g. `9090:80`) and restart Docker. No `.env` variable controls it — it is a Compose mapping only.

All API calls in Sections 1–11 target the **AI Web Test** base URL (`port 8000`). **Section 12** below documents the ReqIQ proxy endpoints — AI Web Test backend calls ReqIQ on behalf of users so they never need to access ReqIQ directly.

---

---

## 1. Authentication

All endpoints (except `GET /api/v1/kb/categories` and health checks) require a **Bearer JWT** token.

### 1.1 Login

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Request body** (form-encoded, OAuth2 password flow):

| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Username or email |
| `password` | string | Password |

**Response 200:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Rate limit:** 10 requests per minute per IP.

**Use the token** by adding to every subsequent request:

```
Authorization: Bearer <access_token>
```

**Token lifetime:** 1440 minutes (24 hours). Refresh with `POST /api/v1/auth/refresh` using the same token before expiry.

### 1.2 Refresh Token

```
POST /api/v1/auth/refresh
Authorization: Bearer <current_token>
```

Returns a new `access_token` (same shape as login response).

---

## 2. Knowledge Base — Upload Requirement Documents

ReqIQ can push SRS documents, feature specs, or acceptance criteria into the AI Web Test knowledge base. These are used by agents as context when generating tests.

### 2.1 List Categories

```
GET /api/v1/kb/categories
```

No authentication required. Returns the list of available categories.

**Response 200 (array):**

```json
[
  { "id": 1, "name": "System Guide",       "description": "..." },
  { "id": 2, "name": "Product Info",       "description": "..." },
  { "id": 3, "name": "Process",            "description": "..." },
  { "id": 4, "name": "Login Flows",        "description": "..." },
  { "id": 5, "name": "API Documentation",  "description": "..." },
  { "id": 6, "name": "User Guides",        "description": "..." },
  { "id": 7, "name": "Test Cases",         "description": "..." },
  { "id": 8, "name": "Bug Reports",        "description": "..." }
]
```

### 2.2 Upload a Document

```
POST /api/v1/kb/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | Yes | Document file. Accepted formats: PDF, DOCX, MD, TXT. Max size: **25 MB**. |
| `title` | string | Yes | Display title for the document |
| `category_id` | integer | No | Category ID (from step 2.1). Defaults to uncategorised. |
| `description` | string | No | Short description of the document |
| `tags` | string | No | Comma-separated tags |

**Response 201:**

```json
{
  "id": 42,
  "title": "ReqIQ SRS v1.0",
  "filename": "ReqIQ_SRS_v1.0.pdf",
  "file_type": "pdf",
  "file_size": 154320,
  "category_id": 5,
  "description": "Software Requirements Specification",
  "tags": ["requirements", "srs"],
  "created_at": "2026-05-14T09:00:00Z"
}
```

**cURL example:**

```bash
curl -X POST http://localhost:8000/api/v1/kb/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@ReqIQ_SRS_v1.0.pdf" \
  -F "title=ReqIQ SRS v1.0" \
  -F "category_id=5" \
  -F "tags=requirements,srs"
```

### 2.3 List Documents

```
GET /api/v1/kb
Authorization: Bearer <token>
```

Optional query params: `?category_id=5&search=login&page=1&page_size=20`

---

## 3. Generate a Test Case from a URL (Crawl-and-Save)

> **Note:** `POST /api/v2/generate-tests` (4-agent workflow) is not currently recommended — it has reliability issues. Use `POST /api/v2/crawl-and-save-test` instead. This is the active, production-tested endpoint.

This is the primary integration point. ReqIQ sends a target URL with a natural-language instruction. The server launches a browser (via browser-use), crawls the exact flow described, stops at a configurable page, and saves **one precise test case** directly to the database. Step Library modules handle reusable parts (login, checkout) so they are not hard-coded into every test.

```
POST /api/v2/crawl-and-save-test
Authorization: Bearer <token>
Content-Type: application/json
```

**Request body:**

```json
{
  "url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
  "user_instruction": "Login with the provided credentials. Click 5G Monthly Plan. Click voucher monthly plan tab. Select $288 plan. Click Subscribe Now. Agree to Terms and Conditions. Click 'New mobile number'. Click 'Physical SIM'. STOP as soon as the SIM Setting page appears.",
  "stop_at_page_hint": "SIM Card Setting",
  "login_module": "login_my3_andrew",
  "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
  "new_subscriber_module": "plan_subscriber_flow_andrew",
  "subscriber_type_hint": "auto",
  "test_title": "5G Monthly Voucher Plan $288/month - purchase flow",
  "test_description": "E2E subscription flow for 5G Voucher Plan $288/month. Navigation crawled by browser-use; login and checkout handled by Step Library modules.",
  "test_type": "e2e",
  "priority": "high",
  "login_credentials": {
    "username": "test_user@example.com",
    "password": "TestPassword123"
  },
  "available_file_paths": ["C:/path/to/ekyctest/test06.jpg"],
  "max_browser_steps": 50,
  "max_flow_timeout_seconds": 600,
  "tags": ["5g", "voucher-plan", "purchase-flow"],
  "reference_test_id": 1217
}
```

**Field reference:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string (URL) | **required** | Start URL — the page the browser opens first |
| `user_instruction` | string | **required** | Step-by-step natural language instruction for the browser agent. Be specific about what to click and where to stop. |
| `stop_at_page_hint` | string | null | Substring matched against page title/URL. Crawl stops immediately when matched (e.g. `"SIM Card Setting"`). Prevents the browser from attempting fragile payment/form pages. |
| `login_credentials` | object | null | `{"username": "...", "password": "..."}` or `{"email": "...", "password": "..."}` |
| `http_credentials` | object | null | HTTP Basic auth for UAT/preprod gates `{"username": "...", "password": "..."}` |
| `available_file_paths` | string[] | null | Local file paths for upload steps (e.g. HKID image) |
| `max_browser_steps` | int 1–500 | 120 | Cap on browser-use steps. Keep low (50) for focused flows to avoid loops. |
| `max_flow_timeout_seconds` | int 60–7200 | 1200 | Wall-clock timeout for the crawl phase |
| `test_title` | string | **required** | Title for the saved test case |
| `test_description` | string | **required** | Description for the saved test case |
| `test_type` | string | `"e2e"` | `e2e`, `integration`, `unit` |
| `priority` | string | `"high"` | `high`, `medium`, `low` |
| `tags` | string[] | null | Tags for filtering in the test library |
| `reference_test_id` | int | null | ID of an existing "gold standard" test case. The LLM review pass compares generated steps against it and strips noise. |

**Step Library fields** (replace crawled sections with reusable modules):

| Field | Type | Description |
|-------|------|-------------|
| `login_module` | string | Step Library module name to substitute for captured login steps. Inserted as `@module:<name>()` at the start. E.g. `"login_my3_andrew"` |
| `existing_subscriber_module` | string | Module appended when an existing-subscriber popup is detected after login. E.g. `"plan_subscribe_flow_existing_preprod_andrew"` |
| `new_subscriber_module` | string | Module appended when no existing-subscriber popup is detected. E.g. `"plan_subscriber_flow_andrew"` |
| `subscriber_type_hint` | string | `"auto"` (detect from browser history), `"existing"`, or `"new"` |

**Response 202** (background job started):

```json
{
  "workflow_id": "b3d2f1a0-9c8e-4b7d-a6e5-1234567890ab",
  "status": "pending",
  "message": "Crawl-and-save job started",
  "started_at": "2026-05-14T09:00:00Z"
}
```

Poll status and retrieve results the same way as any other workflow (Section 4).

**Results response** (when `status == "completed"`):

```json
{
  "result": {
    "test_case_id": 1291,
    "total_steps": 18,
    "crawled_steps_count": 12,
    "login_module": "login_my3_andrew",
    "subscriber_type": "existing",
    "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
    "new_subscriber_module": "plan_subscriber_flow_andrew"
  }
}
```

### How it works internally

```
Browser opens URL → follows user_instruction step by step
        ↓  (stops when stop_at_page_hint is matched)
Crawled navigation steps extracted from browser history
        ↓
Login steps stripped → replaced with @module:<login_module>()
        ↓
Subscriber type auto-detected → correct checkout module appended
        ↓
LLM review pass (if reference_test_id set) cleans noise
        ↓
One test case saved to DB → returns test_case_id
```

Total typical duration: **3–10 minutes** depending on flow complexity and `max_browser_steps`.

---

## 4. Track Workflow Progress (SSE or Polling)

### Option A — Server-Sent Events (recommended)

```
GET /api/v2/workflows/{workflow_id}/stream
Authorization: Bearer <token>
Accept: text/event-stream
```

The server pushes events as agents run. Each event:

```
event: agent_progress
data: {"agent": "observation", "status": "running", "progress": 0.6, "message": "Found 24 UI elements"}

event: agent_completed
data: {"agent": "observation", "status": "completed", "elements_found": 38, "confidence": 0.9}

event: workflow_completed
data: {"workflow_id": "b3d2f1a0-...", "status": "completed", "test_count": 12}
```

Event types: `agent_started` · `agent_progress` · `agent_completed` · `workflow_completed` · `workflow_failed`

### Option B — Polling

```
GET /api/v2/workflows/{workflow_id}
Authorization: Bearer <token>
```

Poll every 5–10 seconds. **Response 200:**

```json
{
  "workflow_id": "b3d2f1a0-...",
  "status": "running",
  "current_agent": "requirements",
  "progress": {
    "observation": {
      "agent": "observation",
      "status": "completed",
      "progress": 1.0,
      "message": "38 UI elements found",
      "elements_found": 38,
      "confidence": 0.90
    },
    "requirements": {
      "agent": "requirements",
      "status": "running",
      "progress": 0.65,
      "message": "Generating scenarios...",
      "scenarios_generated": 8
    }
  },
  "total_progress": 0.41,
  "started_at": "2026-05-14T09:00:00Z",
  "error": null
}
```

`status` values: `pending` · `running` · `completed` · `failed` · `cancelled`

### Cancel a Workflow

```
DELETE /api/v2/workflows/{workflow_id}
Authorization: Bearer <token>
```

---

## 5. Test Case CRUD — Create, Read, Update, Delete

### 5.1 Create a Test Case

```
POST /api/v1/tests
Authorization: Bearer <token>
Content-Type: application/json
```

**Request body:**

```json
{
  "title": "Verify login with invalid credentials",
  "description": "Ensure the system rejects login with a wrong password and shows an error message",
  "test_type": "e2e",
  "priority": "high",
  "status": "pending",
  "steps": [
    "Navigate to https://example.com/login",
    "Enter username: test@example.com",
    "Enter password: wrongpassword",
    "Click the Login button",
    "Verify error message is displayed"
  ],
  "expected_result": "Error message 'Invalid username or password' is shown. User remains on login page.",
  "preconditions": "User account test@example.com exists in the system",
  "tags": ["login", "negative", "functional"],
  "category_id": 4
}
```

**Field reference:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string (1–255) | Yes | Test case title |
| `description` | string | Yes | What the test verifies |
| `test_type` | enum | Yes | `e2e`, `unit`, `integration`, `api` |
| `priority` | enum | No | `high`, `medium` (default), `low` |
| `status` | enum | No | `pending` (default), `active`, `passed`, `failed`, `skipped` |
| `steps` | array | Yes | Minimum 1 step. Each item is a string or step object (see below). |
| `expected_result` | string | Yes | Overall pass criteria |
| `preconditions` | string | No | Setup state required before running |
| `test_data` | object | No | Extra data (max 10 KB). Can include `detailed_steps`, `loop_blocks`. |
| `category_id` | int | No | KB category ID for context linkage |
| `tags` | string[] | No | Labels for filtering |

**Step object format** (alternative to plain strings):

```json
{
  "action": "fill",
  "selector": "#email-input",
  "value": "test@example.com",
  "instruction": "Type the test email address",
  "expected": "Field shows test@example.com"
}
```

Actions: `click`, `fill`, `navigate`, `verify`, `upload_file`, `select`

**Response 201:** Full test case object (same shape as GET below).

---

### 5.2 Get a Single Test Case

```
GET /api/v1/tests/{test_case_id}
Authorization: Bearer <token>
```

**Response 200:**

```json
{
  "id": 123,
  "title": "Verify 5G plan purchase with new SIM",
  "description": "Test that a user can complete the 5G plan purchase selecting a new SIM card",
  "test_type": "e2e",
  "priority": "high",
  "status": "pending",
  "steps": [
    "Navigate to plan selection page",
    "Select '5G Unlimited 100GB' plan",
    "Choose 'New SIM' option",
    "Proceed to checkout"
  ],
  "expected_result": "Order confirmation page displayed with correct plan details",
  "preconditions": "User is logged in and on the plans page",
  "tags": ["5G", "purchase", "functional"],
  "category_id": 2,
  "user_id": 1,
  "created_at": "2026-05-14T09:06:10Z",
  "updated_at": "2026-05-14T09:06:10Z"
}
```

---

### 5.3 Update a Test Case

```
PUT /api/v1/tests/{test_case_id}
Authorization: Bearer <token>
Content-Type: application/json
```

All fields are **optional** — only the fields you provide will be updated (partial update).

```json
{
  "title": "Verify 5G plan purchase with new SIM — updated",
  "priority": "high",
  "status": "active",
  "tags": ["5G", "purchase", "functional", "regression"]
}
```

**Response 200:** Full updated test case object.

**Notes:**
- Only the test case owner or an admin can update.
- Updating `steps` via this endpoint does **not** create a version snapshot. Use [Section 6.1](#61-update-steps-with-version-snapshot) if you need version history.

---

### 5.4 Delete a Test Case

```
DELETE /api/v1/tests/{test_case_id}
Authorization: Bearer <token>
```

**Response 204 No Content** on success.

---

### 5.5 Batch Delete Test Cases

```
DELETE /api/v1/tests/batch
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "ids": [123, 124, 125]
}
```

Max 100 IDs per request.

**Response 200:**

```json
{
  "deleted": 3,
  "failed": []
}
```

`failed` lists any IDs that could not be deleted (not found, not owned, or DB error).

---

### 5.6 List All Test Cases

```
GET /api/v1/tests
Authorization: Bearer <token>
```

Query params: `?page=1&page_size=20&status=active&priority=high&search=login`

---

### 5.7 Workflow Results (from AI generation)

After a `POST /api/v2/generate-tests` workflow completes, retrieve the IDs of the generated test cases:

```
GET /api/v2/workflows/{workflow_id}/results
Authorization: Bearer <token>
```

**Response 200:**

```json
{
  "workflow_id": "b3d2f1a0-...",
  "status": "completed",
  "test_case_ids": [123, 124, 125, 126],
  "test_count": 4,
  "completed_at": "2026-05-14T09:06:42Z",
  "total_duration_seconds": 402.1
}
```

Then use [Section 5.2](#52-get-a-single-test-case) to fetch each test case.

---

## 6. Test Steps & Version Control

### 6.1 Update Steps with Version Snapshot

Use this endpoint (instead of the general PUT) when you want each edit to be tracked as a named version with a rollback trail.

```
PUT /api/v1/tests/{test_case_id}/steps
Content-Type: application/json
```

> Note: This endpoint does **not** require a Bearer token in the current implementation.

**Request body:**

```json
{
  "steps": [
    "Navigate to https://example.com/login",
    "Enter email: test@example.com",
    "Enter password: correct_password",
    "Click Login",
    "Assert dashboard is visible"
  ],
  "expected_result": "Dashboard page loads successfully",
  "test_data": null,
  "created_by": "ReqIQ",
  "change_reason": "Added assertion step from RQ-IQ review"
}
```

**Response 200** — the new version snapshot:

```json
{
  "id": 55,
  "test_case_id": 123,
  "version_number": 3,
  "steps": ["..."],
  "expected_result": "Dashboard page loads successfully",
  "created_at": "2026-05-14T10:00:00",
  "created_by": "ReqIQ",
  "change_reason": "Added assertion step from RQ-IQ review",
  "parent_version_id": 54
}
```

---

### 6.2 Get Version History

```
GET /api/v1/tests/{test_case_id}/versions?limit=50
```

Returns an array of version snapshots (newest first).

---

### 6.3 Get a Specific Version

```
GET /api/v1/tests/{test_case_id}/versions/{version_id}
```

---

### 6.4 Rollback to a Previous Version

```
POST /api/v1/tests/{test_case_id}/versions/rollback
Content-Type: application/json
```

```json
{
  "version_id": 52,
  "created_by": "ReqIQ"
}
```

Creates a new version whose content is copied from version 52. The live test case is updated to match.

---

### 6.5 Compare Two Versions

```
GET /api/v1/tests/{test_case_id}/versions/compare/{version_id_1}/{version_id_2}
```

Returns a diff of steps and expected_result between the two versions.

---

## 7. Execute a Test Case

```
POST /api/v1/executions/tests/{test_case_id}/execute
Authorization: Bearer <token>
Content-Type: application/json
```

**Request body:**

```json
{
  "browser": "chromium",
  "environment": "staging",
  "base_url": "https://uat.example.com",
  "triggered_by": "ReqIQ"
}
```

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `browser` | string | `"chromium"` | `chromium`, `firefox`, `webkit` |
| `environment` | string | `"staging"` | `dev`, `staging`, `production` |
| `base_url` | string | null | Override base URL for this run |
| `triggered_by` | string | null | Label for audit trail (e.g. `"ReqIQ"`) |

**Response 201:**

```json
{
  "execution_id": 77,
  "test_case_id": 123,
  "status": "pending",
  "browser": "chromium",
  "environment": "staging",
  "triggered_by": "ReqIQ",
  "created_at": "2026-05-14T09:10:00Z"
}
```

### Poll Execution Status

```
GET /api/v1/executions/{execution_id}
Authorization: Bearer <token>
```

`status` values: `pending` · `running` · `passed` · `failed` · `error` · `cancelled`

### Cancel Execution (cooperative stop)

```
DELETE /api/v1/executions/{execution_id}/cancel
Authorization: Bearer <token>
```

**Response 204** — no body. Idempotent when execution is already terminal.

Cancels `pending` (dequeued before browser starts) or `running` (cooperative poll between steps/tiers). Partial step history is preserved. Use `DELETE /executions/{id}` only to **delete** the record, not to stop a run. See `documentation/ADR-009-execution-cancel.md`.

---

## 8. Get Execution Results & AI Root-Cause Analysis

```
GET /api/v1/executions/{execution_id}/feedback
Authorization: Bearer <token>
```

Returns per-step feedback including the AI-generated root cause analysis when a test fails.

**Response 200 (array of feedback items):**

```json
[
  {
    "id": 201,
    "execution_id": 77,
    "step_index": 3,
    "step_description": "Click 'Buy Now' button",
    "outcome": "failed",
    "failure_type": "element_not_found",
    "error_message": "Element '#buy-now-btn' not found after 5s",
    "root_cause_analysis": "The 'Buy Now' button is conditionally rendered and only appears after plan selection. The test step did not first select a plan, so the button was never rendered in the DOM.",
    "suggested_fix": "Add a preceding step to select a plan before attempting to click 'Buy Now'.",
    "screenshot_path": "/artifacts/screenshots/exec_77_step_3.png",
    "created_at": "2026-05-14T09:11:30Z"
  }
]
```

The `root_cause_analysis` and `suggested_fix` fields are populated by the AI after a failed three-tier execution attempt — ready to feed back into ReqIQ's requirement refinement workflow.

---

## 9. Convenience: Quick Test Generation (LLM-only, no browser crawl)

> **Note:** This is a lightweight LLM-only endpoint — no browser is launched. It is suitable for generating draft test cases from requirement text alone, but produces lower-fidelity steps than `crawl-and-save-test` because it cannot observe the real UI. Use `crawl-and-save-test` (Section 3) for production test cases.

```
POST /api/v1/tests/generate
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "requirements": "User must be able to log in with valid credentials and see the dashboard. Login must fail with an appropriate error for invalid credentials.",
  "test_type": "functional",
  "count": 5
}
```

Returns an array of generated test case objects saved to the database.

---

## 10. Error Codes

| HTTP Status | Meaning |
|-------------|---------|
| `400 Bad Request` | Invalid request body or missing required fields |
| `401 Unauthorized` | Missing or expired Bearer token |
| `403 Forbidden` | Authenticated but insufficient role (e.g. admin-only endpoint) |
| `404 Not Found` | Resource (test case, workflow, execution) does not exist |
| `422 Unprocessable Entity` | Request body fails schema validation — check `detail` field for field-level errors |
| `429 Too Many Requests` | Rate limit exceeded (login: 10/min; other endpoints: varies) |
| `500 Internal Server Error` | Server-side error — check server logs |

**Error response shape:**

```json
{
  "detail": "Incorrect username or password"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 11. Common Flows for ReqIQ

### Flow A — Push a Requirement Doc and Crawl-Save a Test Case

```
1. POST /api/v1/auth/login                        → get token
2. POST /api/v1/kb/upload  (attach SRS PDF)       → document stored as KB context
3. POST /api/v2/crawl-and-save-test               → workflow_id returned
     (url, user_instruction from compiled wiki,
      stop_at_page_hint, login_module,
      existing/new subscriber modules)
4. GET  /api/v2/workflows/{id}  (poll ~15s)       → status: pending → completed
5. GET  /api/v2/workflows/{id}/results            → result.test_case_id
6. GET  /api/v1/tests/{id}                        → fetch full test case details
```

### Flow B — Run a Test and Get Root-Cause Feedback

```
1. POST /api/v1/auth/login                                      → token
2. POST /api/v1/executions/tests/{test_case_id}/execute         → execution_id
3. GET  /api/v1/executions/{execution_id}  (poll until done)    → status: passed/failed
4. GET  /api/v1/executions/{execution_id}/feedback              → step results + RCA
```

### Flow C — ReqIQ Sends User Instruction from RQ-IQ Analysis

When ReqIQ produces a RQ-IQ analysis for a requirement, convert the acceptance criteria into
a step-by-step `user_instruction` for the crawl agent. Be specific about what to click and
where to stop — the browser follows it literally.

```json
{
  "url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
  "user_instruction": "Login. Click 5G Monthly Plan. Select the $288 voucher plan. Click Subscribe Now. Choose New mobile number. Choose Physical SIM. STOP when the SIM Card Setting page appears.",
  "stop_at_page_hint": "SIM Card Setting",
  "login_module": "login_my3_andrew",
  "new_subscriber_module": "plan_subscriber_flow_andrew",
  "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
  "subscriber_type_hint": "auto",
  "test_title": "5G $288 Voucher Plan — new subscriber",
  "test_description": "Generated from RQ-IQ analysis of 5G plan purchase requirement",
  "max_browser_steps": 50
}
```

### Flow D — Crawl a Specific Flow, Then Refine It

```
1. POST /api/v1/auth/login                            → token
2. POST /api/v2/crawl-and-save-test                   → crawl + save test case
3. GET  /api/v2/workflows/{id}/results                → result.test_case_id
4. PUT  /api/v1/tests/{id}                            → update metadata (title, tags, priority)
5. PUT  /api/v1/tests/{id}/steps                      → refine steps with version snapshot
6. GET  /api/v1/tests/{id}/versions                   → verify version history
```

### Flow E — Review, Edit, Then Rollback

```
1. POST /api/v1/auth/login                                          → token
2. GET  /api/v1/tests/{id}/versions                                 → list versions
3. PUT  /api/v1/tests/{id}/steps  (change_reason: "RQ-IQ review")  → creates version N+1
4. GET  /api/v1/tests/{id}/versions/compare/{v_N}/{v_N+1}          → inspect diff
5. POST /api/v1/tests/{id}/versions/rollback  {"version_id": v_N}   → revert if needed
```

### Flow F — Delete Stale Tests in Bulk

```
1. POST /api/v1/auth/login             → token
2. GET  /api/v1/tests?status=skipped   → find tests to remove
3. DELETE /api/v1/tests/batch          → {"ids": [101, 102, 103]}
```

---

## Notes

- **Server port:** `8000` (configurable via `uvicorn` startup)
- **CORS origins allowed:** `http://localhost:5173` and `http://localhost:8080` by default — update `BACKEND_CORS_ORIGINS` in the server `.env` if ReqIQ UI is on a different port (set in ReqIQ `docker-compose.yml` `web.ports`)
- **Full machine-readable spec:** `backend/openapi_spec.json` — import into Postman, Insomnia, or any OpenAPI-compatible tool
- **All timestamps** are ISO 8601 UTC (`2026-05-14T09:00:00Z`)

---

## 12. ReqIQ Proxy Endpoints

> **Full handoff (standard vs power-user, proxy gaps, MVP order):** [`AI-Web-Test-Developer-Handoff.md`](AI-Web-Test-Developer-Handoff.md).  
> §12 below is **partial** — implement the **§5.2 extensions** in that doc (create/rename project, requirements CRUD, revisions/IQ, full suggested-tests).

AI Web Test acts as a transparent proxy to ReqIQ. Users and agents call these endpoints on AI Web Test (port 8000) — the server forwards the request to ReqIQ (`localhost:3001`) using a service account, and returns the result. **Users never need to know ReqIQ exists or what port it runs on.**

> All endpoints below require `Authorization: Bearer <AI_Web_Test_token>`.  
> The server-side `.env` must have `REQIQ_URL=http://localhost:3001` and `REQIQ_SERVICE_TOKEN=<jwt from POST /api/v1/login>`.

---

### 12.1 List Projects

```
GET /api/v1/requirements/projects
Authorization: Bearer <token>
```

Proxies to ReqIQ `GET /api/v1/projects`.

**Response 200:**
```json
[
  { "id": "clx1234abcd", "name": "Three-HK", "createdAt": "2026-01-10T08:00:00Z" },
  { "id": "clx5678efgh", "name": "Internal Tools", "createdAt": "2026-02-01T08:00:00Z" }
]
```

Note: `id` is a CUID string (not an integer). Use this `id` as `projectId` in all subsequent calls.

---

### 12.2 List Requirements for a Project

```
GET /api/v1/requirements/{projectId}/requirements
Authorization: Bearer <token>
```

Proxies to ReqIQ `GET /api/v1/projects/{projectId}/requirements`.

**Response 200 (array):**
```json
[
  {
    "id": "req_abc123",
    "title": "5G Voucher Plan Purchase",
    "body": "## Acceptance Criteria\n1. User can navigate to 5G Monthly Plan...",
    "state": "BASELINE",
    "createdAt": "2026-03-15T09:00:00Z",
    "updatedAt": "2026-05-01T14:00:00Z"
  }
]
```

`state` values: `DRAFT` → `REVIEWED` → `BASELINE` (approved, use for test gen) → `SUPERSEDED`

---

### 12.3 RAG Query (Ask a Question About Requirements)

This is the main way to retrieve requirement context for test generation. Ask a question in plain language; ReqIQ searches all uploaded source documents and returns an LLM-composed answer with citations.

```
POST /api/v1/requirements/{projectId}/query
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "query": "What is the acceptance criteria for the 5G Voucher Plan purchase flow?",
  "limit": 8
}
```

Proxies to ReqIQ `POST /api/v1/projects/{projectId}/rag/query`.

**Response 200:**
```json
{
  "content": "The 5G Voucher Plan purchase flow requires: 1. User must be able to navigate to 5G Monthly Plan section. 2. User can select the $288 voucher plan. 3. User completes subscription by choosing new or existing mobile number...",
  "citations": [
    { "sourceFilename": "5G_Plan_SRS_v2.docx", "chunkIndex": 3, "score": 0.91 },
    { "sourceFilename": "UAT_Acceptance_Criteria.pdf", "chunkIndex": 7, "score": 0.87 }
  ],
  "suggestedTests": [
    {
      "title": "5G $288 Voucher Plan — new subscriber",
      "steps": ["Navigate to 5G Monthly Plan", "Select $288 plan", "Click Subscribe Now", "Choose New mobile number", "Choose Physical SIM"],
      "oracle": "SIM Card Setting page displayed",
      "automation": { "viable": true }
    }
  ]
}
```

> **Key field:** `suggestedTests[]` — if ReqIQ's IQ pipeline is active, this array contains LLM-generated test step suggestions ready to pass directly to `qa-test-gen` as `test_instructions`. No LLM extraction needed.

---

### 12.4 Upload a Source Document

Allows QA engineers to upload requirement documents directly from the AI Web Test UI — proxied to ReqIQ's document store.

```
POST /api/v1/requirements/{projectId}/sources/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form fields:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | binary | One or more files. Accepted: DOCX, PDF, MD, TXT, PPTX, PNG. Max size: `REQIQ_MAX_UPLOAD_BYTES` (default 25MB). |

Multiple files in one request are supported (repeat the `file` field).

Proxies to ReqIQ `POST /api/v1/projects/{projectId}/sources/upload`.

**Response 201:**
```json
{
  "projectId": "clx1234abcd",
  "uploadedCount": 2,
  "rejectedCount": 0,
  "uploaded": [
    { "id": "src_001", "originalFilename": "5G_Plan_SRS_v2.docx", "status": "processing" },
    { "id": "src_002", "originalFilename": "UAT_Acceptance_Criteria.pdf", "status": "processing" }
  ],
  "rejected": []
}
```

> After upload, ReqIQ processes and embeds the file automatically. The RAG query endpoint (`12.3`) will include the new document once `status` transitions from `processing` to `ready` (typically < 60 seconds).

---

### 12.5 List Source Documents

```
GET /api/v1/requirements/{projectId}/sources
Authorization: Bearer <token>
```

Proxies to ReqIQ `GET /api/v1/projects/{projectId}/sources`.

Returns the list of uploaded documents with their processing status.

---

### 12.6 Generate Suggested Tests from a Requirement (LLM)

Triggers ReqIQ's LLM pipeline to generate 1–5 candidate test cases from a specific requirement. Returns structured test steps ready to pass to `crawl-and-save-test`.

```
POST /api/v1/requirements/{projectId}/requirements/{requirementId}/suggest-tests
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "maxTests": 3,
  "hints": "Focus on the happy path and the SIM selection step"
}
```

Proxies to ReqIQ `POST /api/v1/projects/{projectId}/suggested-tests/generate` with `{ requirementId, maxTests, hints }`.

**Response 200:**
```json
{
  "created": [
    {
      "id": "st_001",
      "title": "5G $288 Voucher — new subscriber happy path",
      "payload": {
        "preconditions": ["User has a valid My3 account"],
        "steps": [
          { "action": "Navigate to 5G Monthly Plan", "expected": "Plan list page visible" },
          { "action": "Select $288 Voucher plan", "expected": "Plan highlighted" },
          { "action": "Click Subscribe Now", "expected": "T&C modal appears" },
          { "action": "Agree to T&C", "expected": "Service Subscription options shown" },
          { "action": "Choose New mobile number + Physical SIM", "expected": "SIM Card Setting page displayed" }
        ],
        "oracle": "SIM Card Setting page is displayed. No SIM fields are submitted.",
        "automation": { "viable": true, "markers": ["e2e", "happy-path"] }
      }
    }
  ],
  "errors": [],
  "model": "gpt-4o-mini"
}
```

The `steps[]` array maps directly to `user_instruction` in `crawl-and-save-test` — join them with `\n` and append `STOP when {oracle}` as the final instruction.

---

### 12.7 Get Latest IQ Score for a Requirement

Lightweight endpoint — returns only the IQ fields without the full requirement body. Useful when Hermes only needs to check the score before deciding to proceed.

```
GET /api/v1/requirements/{projectId}/requirements/{requirementId}/latest-iq
Authorization: Bearer <token>
```

Proxies to ReqIQ `GET /api/v1/projects/{projectId}/requirements/{requirementId}/latest-iq`.

**Response 200:**
```json
{
  "requirementId": "req_abc123",
  "latestCompositeScore": 87,
  "latestRevisionIndex": 3,
  "updatedAt": "2026-05-14T10:00:00Z"
}
```

Use this instead of `12.8` when `wikiContent` is already available and you only need to re-check the score.

---

### 12.8 Project Readiness Check

Single-call gate that replaces the three-step pattern (RAG query + requirements list + IQ score). Returns everything needed to decide whether to proceed with test generation.

> **Wiki phases (ReqIQ):** Until ReqIQ **Sprint 7.5**, `wikiContent` is a **provisional** RAG-backed answer (may differ across calls). After 7.5, ReqIQ returns a **persisted compiled wiki** per project when available. See [`Wiki-Compile-Strategy.md`](Wiki-Compile-Strategy.md). AI Web Test should label this **Test context**, not “RAG query”.

```
GET /api/v1/requirements/{projectId}/readiness?query={query}&feature={feature}
Authorization: Bearer <token>
```

Proxies to ReqIQ `GET /api/v1/projects/{projectId}/readiness?query={query}&feature={feature}`.

**Query parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `query` | Yes | Natural-language description of the feature/scenario you want to test |
| `feature` | No | Feature name for more targeted matching (e.g. `5G Voucher Plan Purchase`) |

**Response 200:**
```json
{
  "projectId": "cmp0zdx4g0004alp8z77ess7a",
  "readinessScore": 87,
  "status": "ready",
  "wikiContent": "## 5G Voucher Plan\n\n### Acceptance Criteria\n1. User can navigate to 5G Monthly Plan...",
  "matchedRequirement": {
    "id": "req_abc123",
    "title": "5G Voucher Plan Purchase",
    "state": "BASELINE",
    "latestCompositeScore": 87
  },
  "missing": []
}
```

`status` values:
- `ready` — `readinessScore >= 60`, `wikiContent` populated, safe to proceed with test generation
- `insufficient` — score below threshold; `missing[]` lists what documents/sections are absent
- `no_sources` — no documents uploaded for this project yet

> **This is the preferred entry point for Hermes `qa-requirements` agent** — one call replaces RAG query + requirements list + IQ score lookup.

---

### 12.9 Environment Variables (AI Web Test `.env`)

```bash
# ReqIQ service account (server-side only — never exposed to browser)
REQIQ_URL=http://localhost:3001
REQIQ_SERVICE_EMAIL=service@reqiq.internal
REQIQ_SERVICE_PASSWORD=your-service-account-password
# Or store the pre-issued JWT directly:
# REQIQ_SERVICE_TOKEN=eyJhbGci...
```
