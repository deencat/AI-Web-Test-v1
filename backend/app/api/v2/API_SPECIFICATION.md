# API v2 Specification

**Purpose:** Authoritative reference for API v2 with request/response details, parameters, and examples.  
**Audience:** Frontend developers, integration partners, QA.  
**Base path:** `/api/v2`  
**OpenAPI:** Available at `/api/v2/docs` when the backend is running.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Common Types](#2-common-types)
3. [Entry Points (Workflow Triggers)](#3-entry-points-workflow-triggers)
4. [Workflow Resource](#4-workflow-resource)
5. [Errors](#5-errors)
6. [SSE Stream](#6-sse-stream)
7. [Chaining Flows](#7-chaining-flows)

---

## 1. Overview

### 1.1 Design

- **Multiple entry points:** Full pipeline, per-agent (observation, requirements, analysis, evolution), and improve-tests.
- **Resource-oriented:** Every run returns a `workflow_id`; status and results are at `GET /workflows/{id}` and `GET /workflows/{id}/results`.
- **Async:** All POST triggers return **202 Accepted** and a `WorkflowStatusResponse`; the job runs in the background.
- **Consistent responses:** Same status/results shape for all workflow types (including partial results for single-stage runs).

### 1.2 Base URL and Versioning

| Item | Value |
|------|--------|
| Base path | `/api/v2` |
| Content-Type | `application/json` (request and response) |
| Versioning | Path-based; future versions would use `/api/v3`, etc. |

### 1.3 Entry Points Summary

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/generate-tests` | Full 4-agent pipeline from URL |
| POST | `/observation` | ObservationAgent only |
| POST | `/requirements` | RequirementsAgent only |
| POST | `/analysis` | AnalysisAgent only |
| POST | `/evolution` | EvolutionAgent only (test generation) |
| POST | `/improve-tests` | Iterative improvement by test case IDs |
| GET | `/workflows/{workflow_id}` | Workflow status |
| GET | `/workflows/{workflow_id}/results` | Workflow results (partial or full) |
| GET | `/workflows/{workflow_id}/stream` | SSE progress stream |
| DELETE | `/workflows/{workflow_id}` | Cancel workflow (stub) |

---

## 2. Common Types

### 2.1 WorkflowStatusResponse (used by all POST entry points and GET status)

Returned on **202 Accepted** (POST) or **200 OK** (GET status). Used as the single “workflow handle” for polling.

| Field | Type | Description |
|-------|------|-------------|
| `workflow_id` | string | Unique workflow identifier (UUID). |
| `status` | string | One of: `pending`, `running`, `completed`, `failed`, `cancelled`. |
| `current_agent` | string \| null | Currently executing agent: `observation`, `requirements`, `analysis`, `evolution`, or null. |
| `progress` | object | Map of agent name → progress object (see AgentProgress). |
| `total_progress` | number | Overall progress 0.0–1.0. |
| `started_at` | string (ISO 8601) | When the workflow started. |
| `estimated_completion` | string \| null | Estimated completion time (ISO 8601), if available. |
| `error` | string \| null | Error message if status is `failed`. |

**AgentProgress** (each entry in `progress`):

| Field | Type | Description |
|-------|------|-------------|
| `agent` | string | Agent name. |
| `status` | string | `pending`, `running`, `completed`, `failed`. |
| `progress` | number | 0.0–1.0. |
| `message` | string \| null | Current status message. |
| `started_at`, `completed_at` | string \| null | ISO 8601. |
| `duration_seconds` | number \| null | Duration for that agent. |
| `confidence` | number \| null | 0.0–1.0 (e.g. ObservationAgent). |
| `elements_found` | number \| null | UI elements found (Observation). |
| `scenarios_generated` | number \| null | Scenarios (Requirements). |
| `tests_generated` | number \| null | Tests (Evolution). |

### 2.2 WorkflowResultsResponse (GET /workflows/{id}/results)

Returned when the workflow has finished and results are available (full or partial).

| Field | Type | Description |
|-------|------|-------------|
| `workflow_id` | string | Workflow identifier. |
| `status` | string | `completed` or `failed`. |
| `test_case_ids` | integer[] | Generated test case IDs (empty for observation/requirements/analysis-only runs). |
| `test_count` | integer | Number of tests (0 for partial runs). |
| `observation_result` | object \| null | ObservationAgent output (ui_elements, page_structure, page_context). |
| `requirements_result` | object \| null | RequirementsAgent output (scenarios, test_data, coverage_metrics). |
| `analysis_result` | object \| null | AnalysisAgent output (risk_scores, final_prioritization). |
| `evolution_result` | object \| null | EvolutionAgent output. |
| `completed_at` | string (ISO 8601) | When the workflow completed. |
| `total_duration_seconds` | number | Total duration in seconds. |

### 2.3 WorkflowErrorResponse (4xx / 5xx)

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Human-readable error message. |
| `code` | string | Machine-readable code (e.g. `INVALID_URL`, `NOT_FOUND`, `MISSING_INPUT`). |
| `workflow_id` | string \| null | Workflow ID if applicable. |
| `timestamp` | string (ISO 8601) | When the error occurred. |

---

## 3. Entry Points (Workflow Triggers)

All POST endpoints below return **202 Accepted** with a **WorkflowStatusResponse** body. The workflow runs in the background; use `workflow_id` to poll status or fetch results.

---

### 3.1 POST /generate-tests (full pipeline)

Runs all four agents in sequence: Observation → Requirements → Analysis → Evolution. Single-call “generate from URL” flow.

**Request body:** `GenerateTestsRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string (URL) | Yes | Target URL to analyze and generate tests for. |
| `user_instruction` | string | No | Optional instruction (e.g. “Test purchase flow for 5G plan”). |
| `depth` | integer | No | Crawl depth: 1 = current page, 2 = include links, 3 = deep crawl. Default: 1. Range: 1–3. |
| `login_credentials` | object | No | Website login: `{ "username": "...", "password": "..." }` or `{ "email": "...", "password": "..." }`. |
| `gmail_credentials` | object | No | Gmail login for OTP: `{ "email": "...", "password": "..." }` (e.g. Gmail app password). |

**Example request:**

```json
{
  "url": "https://example.com/login",
  "user_instruction": "Test login flow with invalid credentials",
  "depth": 1,
  "login_credentials": {
    "username": "test@example.com",
    "password": "password123"
  },
  "gmail_credentials": {
    "email": "myaccount@gmail.com",
    "password": "gmail-app-password"
  }
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse** (e.g. `workflow_id`, `status: "pending"`, `started_at`).

**Next steps:** Poll `GET /workflows/{workflow_id}` for status; `GET /workflows/{workflow_id}/results` for `test_case_ids` and agent outputs when completed.

---

### 3.2 POST /observation (ObservationAgent only)

Crawls the URL and extracts UI elements. Use the returned `workflow_id` to chain into `/requirements` or to fetch observation result only.

**Request body:** `ObservationRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string (URL) | Yes | Target URL to observe. |
| `user_instruction` | string | No | Optional instruction for observation. |
| `depth` | integer | No | Crawl depth 1–3. Default: 1. |
| `login_credentials` | object | No | Optional login credentials. |

**Example request:**

```json
{
  "url": "https://example.com/login",
  "depth": 1
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse**.

**Output (in results):** `observation_result` with `ui_elements`, `page_structure`, `page_context`. Use this `workflow_id` in POST `/requirements` to run the next stage.

---

### 3.3 POST /requirements (RequirementsAgent only)

Generates BDD scenarios from observation data. Input is either a prior workflow ID (from observation) or an inline observation payload.

**Request body:** `RequirementsRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | No* | ID of a completed observation workflow (to load observation_result from store). |
| `observation_result` | object | No* | Inline observation result: `ui_elements`, `page_structure`, `page_context`. |
| `user_instruction` | string | No | Optional instruction for scenarios. |

*Exactly one of `workflow_id` or `observation_result` must be provided.

**Example (chaining from observation):**

```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_instruction": "Focus on login and checkout"
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse**.

**Output (in results):** `requirements_result` (scenarios, test_data, coverage_metrics). Use this workflow_id in POST `/analysis` next.

---

### 3.4 POST /analysis (AnalysisAgent only)

Runs risk analysis and prioritization. Input is a workflow that has requirements (and observation) results, or inline payloads.

**Request body:** `AnalysisRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | No* | Workflow that already has requirements_result (and observation). |
| `requirements_result` | object | No* | Inline requirements result. |
| `observation_result` | object | No* | Inline observation (at least page_context). Required if using inline requirements. |
| `user_instruction` | string | No | Optional instruction. |

*Either `workflow_id` (with prior results in store) or both `requirements_result` and `observation_result` must be provided.

**Example:**

```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse**.

**Output (in results):** `analysis_result` (risk_scores, final_prioritization). Use this workflow_id in POST `/evolution` to generate tests.

---

### 3.5 POST /evolution (EvolutionAgent only – test generation)

Generates executable test cases. Input is a workflow that has analysis (and prior stages) results, or inline payloads.

**Request body:** `EvolutionRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | No* | Workflow that has analysis_result (and requirements, observation). |
| `analysis_result` | object | No* | Inline analysis result. |
| `requirements_result` | object | No* | Inline requirements result. |
| `observation_result` | object | No* | Inline observation (e.g. page_context). |
| `user_instruction` | string | No | Optional instruction for test generation. |
| `login_credentials` | object | No | Optional login credentials for evolution. |

*Either `workflow_id` or all three of `analysis_result`, `requirements_result`, and `observation_result` must be provided.

**Example:**

```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440002",
  "user_instruction": "Add assertions for error messages"
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse**.

**Output (in results):** `test_case_ids`, `test_count`, `evolution_result`.

---

### 3.6 POST /improve-tests (iterative improvement)

Runs the iterative improvement workflow on existing test cases (evolution + analysis loop). Implementation may be stub until fully built.

**Request body:** `ImproveTestsRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_case_ids` | integer[] | Yes | IDs of test cases to improve. |
| `user_instruction` | string | No | Optional (e.g. “Focus on edge cases”, “Add assertions”). |
| `max_iterations` | integer | No | Max improvement iterations. Default: 5. Range: 1–20. |

**Example request:**

```json
{
  "test_case_ids": [101, 102, 103],
  "user_instruction": "Add more assertions",
  "max_iterations": 3
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse**.

---

## 4. Workflow Resource

### 4.1 GET /workflows/{workflow_id}

Returns current workflow status.

**Path parameters:**

| Name | Type | Description |
|------|------|-------------|
| `workflow_id` | string | UUID returned from any POST entry point. |

**Response:** 200 OK → **WorkflowStatusResponse**.  
**Errors:** 404 if workflow not found (body includes `error`, `code`, `workflow_id`, `timestamp`).

---

### 4.2 GET /workflows/{workflow_id}/results

Returns workflow results (partial or full). Available once the workflow has completed and results are stored.

**Path parameters:** `workflow_id` (same as above).

**Response:** 200 OK → **WorkflowResultsResponse**.  
- For observation-only: `observation_result` set, `test_case_ids`/`test_count` empty.  
- For full pipeline or evolution: `test_case_ids`, `test_count`, and agent results as available.

**Errors:** 404 if workflow not found or results not ready (e.g. still running). Body includes `code: "NOT_READY"` when not ready.

---

### 4.3 GET /workflows/{workflow_id}/stream

SSE stream for real-time progress. See [Section 6](#6-sse-stream).

---

### 4.4 DELETE /workflows/{workflow_id}

Cancel a running workflow. **Status:** Stub (returns 501 Not Implemented).

---

## 5. Errors

| HTTP | When | Response body |
|------|------|----------------|
| 400 | Invalid request (e.g. missing required input, invalid URL) | **WorkflowErrorResponse** (or validation detail). |
| 404 | Workflow not found or results not ready | **WorkflowErrorResponse** with `code: "NOT_FOUND"` or `"NOT_READY"`. |
| 501 | Cancel not implemented | **WorkflowErrorResponse** with `code: "NOT_IMPLEMENTED"`. |

---

## 6. SSE Stream

**Endpoint:** `GET /api/v2/workflows/{workflow_id}/stream`

**Purpose:** Real-time progress events for a workflow.

**Event types:**

| Event | When |
|-------|------|
| `agent_started` | An agent begins (data includes `agent`, `timestamp`). |
| `agent_progress` | Progress update (e.g. `progress`, `message`). |
| `agent_completed` | An agent finishes (e.g. `elements_found`, `scenarios_generated`, `duration_seconds`). |
| `workflow_completed` | Workflow finished successfully. |
| `workflow_failed` | Workflow failed (data includes `error`). |

**Example SSE payload (conceptual):**

```
event: agent_started
data: {"agent": "observation", "timestamp": "2026-02-23T10:00:00Z"}

event: agent_completed
data: {"agent": "observation", "elements_found": 38, "duration_seconds": 12.5}
```

---

## 7. Chaining Flows

### 7.1 Full pipeline (one call)

1. `POST /generate-tests` with `url` (and optional `user_instruction`, `depth`, `login_credentials`).
2. Poll `GET /workflows/{id}` or listen to `GET /workflows/{id}/stream`.
3. When `status === "completed"`, call `GET /workflows/{id}/results` for `test_case_ids` and agent outputs.

### 7.2 Per-stage chaining

1. **Observation:** `POST /observation` with `url` → get `workflow_id` (e.g. `wf-obs`).
2. **Requirements:** `POST /requirements` with `workflow_id: "wf-obs"` → get `workflow_id` (e.g. `wf-req`).
3. **Analysis:** `POST /analysis` with `workflow_id: "wf-req"` → get `workflow_id` (e.g. `wf-ana`).
4. **Evolution:** `POST /evolution` with `workflow_id: "wf-ana"` → get `workflow_id` (e.g. `wf-evo`).
5. Poll and fetch **results** for `wf-evo` to get `test_case_ids` and full outputs.

Each POST returns a **new** `workflow_id` for that stage; the `workflow_id` in the request body refers to the **previous** stage’s workflow (to load prior results from the store).

### 7.3 Improve existing tests

1. `POST /improve-tests` with `test_case_ids` (and optional `user_instruction`, `max_iterations`).
2. Poll `GET /workflows/{id}` and `GET /workflows/{id}/results` when implementation is complete.

---

**Reference implementation:** `backend/app/schemas/workflow.py` (Pydantic models), `backend/app/api/v2/endpoints/` (FastAPI routers).  
**OpenAPI (Swagger):** `GET /api/v2/docs` when the backend is running.
