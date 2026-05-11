# API Reference: Agentic Workflow on AI-Web-Test

> **Purpose**: Quick reference for building automated/agentic workflows on top of the platform.
> All endpoints require a Bearer token (except `/auth/login`).
> Base URL: `http://localhost:8000`

---

## 1. Authentication

### Login
```
POST /api/v1/auth/login
Content-Type: application/json

{ "username": "admin", "password": "admin123" }
```
**Response**: `{ "access_token": "...", "token_type": "bearer" }`

Use in all subsequent requests:
```
Authorization: Bearer <access_token>
```

---

## 2. Test Case Management

### List tests
```
GET /api/v1/tests?skip=0&limit=100
```

### Get single test
```
GET /api/v1/tests/{test_case_id}
```
Returns full test case including `steps` (JSON array of step strings).

### Create test manually
```
POST /api/v1/tests
Content-Type: application/json

{
  "title": "My test",
  "description": "...",
  "test_type": "e2e",
  "priority": "high",
  "steps": ["Step 1: Navigate to ...", "Step 2: Click ..."]
}
```

### Update steps only
```
PUT /api/v1/tests/{test_case_id}/steps
Content-Type: application/json

{ "steps": ["Step 1: ...", "Step 2: ..."] }
```

### Delete test
```
DELETE /api/v1/tests/{test_case_id}
```

### Version history & rollback
```
GET  /api/v1/tests/{test_case_id}/versions
POST /api/v1/tests/{test_case_id}/versions/rollback
     Body: { "version_id": 3 }
```

---

## 3. 3-Tier Test Execution

The execution engine tries three strategies in order:
- **Tier 1**: Playwright (fast, CSS/XPath selectors)
- **Tier 2**: Hybrid/XPath fallback
- **Tier 3**: Stagehand (AI-powered, slowest but most robust)

### Start execution (queued, async)
```
POST /api/v1/executions/tests/{test_case_id}/run
Content-Type: application/json

{
  "browser": "chromium",
  "base_url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
  "environment": "dev",
  "triggered_by": "agentic-workflow",
  "http_credentials": {
    "username": "preprod_user",
    "password": "preprod_pass"
  }
}
```
**Response**: `{ "id": 807, "test_case_id": 1224, "status": "PENDING", "message": "..." }`

### Poll execution status
```
GET /api/v1/executions/{execution_id}
```
**Status values**: `PENDING` → `RUNNING` → `PASSED` / `FAILED` / `SKIPPED`

Key response fields:
```json
{
  "id": 807,
  "status": "PASSED",
  "started_at": "...",
  "completed_at": "...",
  "steps_passed": 9,
  "steps_failed": 0,
  "error_message": null,
  "tier_used": "playwright"
}
```

### List all executions for a test
```
GET /api/v1/executions/tests/{test_case_id}/executions
```

### Queue management
```
GET /api/v1/executions/queue/status
GET /api/v1/executions/queue/statistics
GET /api/v1/executions/queue/active
```

---

## 4. AI-Powered Test Generation

### Generate from crawl-and-save (browser-use)
Crawls the actual UI flow, records steps, assembles with Step Library modules.

```
POST /api/v2/crawl-and-save-test
Content-Type: application/json

{
  "url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
  "user_instruction": "Login. Click 5G Monthly Plan. Select $288 Voucher plan. Click Subscribe Now. ...",
  "stop_at_page_hint": "SIM Card Setting",

  "login_module": "login_my3_andrew",
  "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
  "new_subscriber_module": "plan_subscriber_flow_andrew",
  "subscriber_type_hint": "auto",

  "reference_test_id": 1217,

  "test_title": "5G Voucher Plan $288 - auto-crawled",
  "test_description": "...",
  "test_type": "e2e",
  "priority": "high",

  "login_credentials": {
    "username": "pmo.andrewchan+015@gmail.com",
    "password": "cA8mn49&"
  },
  "max_browser_steps": 50,
  "max_flow_timeout_seconds": 600,
  "tags": ["5g", "voucher-plan"]
}
```
**Response**: `{ "workflow_id": "abc-123" }`

### Poll crawl workflow
```
GET /api/v2/workflows/{workflow_id}
```
**Status values**: `running` → `completed` / `failed`

```json
{
  "status": "completed",
  "current_agent": null
}
```

### Get crawl results (after completed)
```
GET /api/v2/workflows/{workflow_id}/results
```
```json
{
  "result": {
    "test_case_id": 1231,
    "total_steps": 11,
    "crawled_steps_count": 9,
    "login_module": "login_my3_andrew",
    "subscriber_type": "new",
    "new_subscriber_module": "plan_subscriber_flow_andrew"
  }
}
```

### Stream workflow progress (SSE)
```
GET /api/v2/workflows/{workflow_id}/stream
Accept: text/event-stream
```

---

## 5. Step Library

### List all modules
```
GET /api/v1/step-library
```

### Create module
```
POST /api/v1/step-library
Content-Type: application/json

{
  "name": "login_my3_andrew",
  "description": "Login to My3 portal with Andrew's credentials",
  "steps": ["Step 1: ...", "Step 2: ..."],
  "tags": ["login", "my3"]
}
```

### Update module
```
PUT /api/v1/step-library/{module_id}
```

### Preview rename impact
```
GET /api/v1/step-library/{module_id}/rename-preview
```

---

## 6. Execution Feedback & False Positive Reporting

### Submit feedback on an execution
```
POST /api/v1/feedback
Content-Type: application/json

{
  "execution_id": 807,
  "test_case_id": 1224,
  "feedback_type": "false_positive",
  "comment": "Step 5 fails because the button is rendered differently in this environment",
  "correction": "Use data-testid selector instead of text match"
}
```

### Get feedback for an execution
```
GET /api/v1/executions/{execution_id}/feedback
```

---

## 7. Full Agentic Workflow Loop

```
┌─────────────────────────────────────────────────────────┐
│                  Agentic Workflow Loop                    │
└─────────────────────────────────────────────────────────┘

1. GENERATE
   POST /api/v2/crawl-and-save-test  →  { workflow_id }
   GET  /api/v2/workflows/{id}        →  poll until "completed"
   GET  /api/v2/workflows/{id}/results →  { test_case_id }

2. EXECUTE
   POST /api/v1/executions/tests/{test_case_id}/run  →  { execution_id }
   GET  /api/v1/executions/{execution_id}             →  poll until PASSED/FAILED

3. EVALUATE
   if FAILED:
     POST /api/v1/feedback  →  log failure + correction hint
     POST /api/v2/improve-tests  →  evolve test
     goto EXECUTE
   if PASSED:
     done ✓

4. OPTIONAL: EVOLVE
   POST /api/v2/evolution   →  generate test variants
   POST /api/v2/analysis    →  analyse execution patterns
```

---

## 8. Swagger / Interactive Docs

The full interactive API explorer is available while the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

---

## 9. Key Field Notes

| Field | Values | Notes |
|---|---|---|
| `browser` | `chromium`, `firefox`, `webkit` | Default: `chromium` |
| `environment` | `dev`, `staging`, `production` | Default: `dev` |
| `subscriber_type_hint` | `auto`, `existing`, `new` | `auto` = detect from crawl |
| `reference_test_id` | integer | Optional model answer for LLM review pass |
| `stop_at_page_hint` | string | Substring matched against page title/URL/agent memory |
| `triggered_by` | any string | Label for audit trail (e.g. `"agentic-workflow"`) |

---

*Last updated: 2026-05-11*
