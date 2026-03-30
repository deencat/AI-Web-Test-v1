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

There is **one** full-pipeline entry point: **POST /generate-tests**. It runs all four agents in sequence (Observation → Requirements → Analysis → Evolution). Test execution is **part of** this pipeline: AnalysisAgent may run real-time execution of critical scenarios for scoring. There is no separate API for “pipeline with execution”—this is it.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/generate-tests` | **Full 4-agent pipeline** from URL (Obs → Req → Analysis* → Evo). *Analysis may run real-time test execution for scoring. |
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
| `scenarios_executed` | number \| null | Scenarios executed in real-time (Analysis, when enabled). |
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
| `analysis_result` | object \| null | AnalysisAgent output. See [Analysis result shape](#analysis-result-shape) below. |
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

#### Analysis result shape

When AnalysisAgent ran in the pipeline or via POST /analysis, `analysis_result` has the following shape:

| Field | Type | Description |
|-------|------|-------------|
| `risk_scores` | object[] | Per-scenario RPN (Severity × Occurrence × Detection), priority. |
| `business_values` | object[] | Per-scenario revenue/user/compliance impact. |
| `roi_scores` | object[] | Per-scenario ROI, bug_detection_value, test_cost. |
| `execution_times` | object[] | Per-scenario estimated_seconds, category (fast/medium/slow). |
| `dependencies` | object[] | Scenario dependencies, execution_order, can_run_parallel. |
| `final_prioritization` | object[] | Per-scenario composite_score, rank, priority, execution_group. |
| `execution_strategy` | object | `smoke_tests` (scenario IDs), `parallel_groups`, `estimated_total_time`, `estimated_parallel_time`. |
| `execution_success` | object[] | **When real-time execution is enabled:** per-scenario execution results. Each entry: `scenario_id`, `success_rate` (0–1), `passed_steps`, `total_steps`, `tier_used` (e.g. "tier1", "tier2"), `reliability` (e.g. "high"), `source` (`"real_time_execution"` \| `"execution_results"` \| `"historical"`). Empty or omitted when real-time execution is disabled. |

Reference: `test_four_agent_e2e_real.py` (AnalysisAgent with `enable_realtime_execution: True`).

---

## 3. Entry Points (Workflow Triggers)

All POST endpoints below return **202 Accepted** with a **WorkflowStatusResponse** body. The workflow runs in the background; use `workflow_id` to poll status or fetch results.

---

### 3.1 POST /generate-tests (full 4-agent pipeline)

Runs all four agents in sequence: Observation → Requirements → Analysis → Evolution. Single-call “generate from URL” flow. If **`flow_recording_path`** is set, Observation is skipped and the same pipeline continues from a saved folder under `artifacts/flow_recordings/` (Requirements → Analysis → Evolution), using the same request fields as a full run (`url` still used for HTTP Basic auth and URL fallbacks).

**Observation goal gate:** If `user_instruction` is non-empty, **Requirements (and the rest of the pipeline) run only when** Observation reports `observation_result.page_context.goal_reached === true`. Observation derives this from visited URLs/titles, browser-use history text, and LLM step fields (eval/memory/next goal). If the guided flow **times out** or ends without a detected goal, the workflow **fails** before Requirements (partial `observation_result` and flow recordings may still be saved). For long UAT flows, increase **`max_browser_steps`** and optional **`max_flow_timeout_seconds`** (wall-clock wait for browser-use per run; default **1200** when omitted; on timeout the server cancels browser-use before returning so later agents do not overlap). To run the pipeline without this gate, omit `user_instruction` (URL-only crawl).

**Scope:** This is the **only** full 4-agent pipeline API; there is **no separate API** for “pipeline with execution.” Test execution is **part of** this pipeline: AnalysisAgent may run real-time execution of critical scenarios (RPN ≥ 80) via the Phase 2 execution engine (3-tier: Playwright → Hybrid → Stagehand AI) to measure success rates and refine risk scores. This execution is for **scoring and prioritization**; results appear in `analysis_result.execution_success`. The final API output is `test_case_ids` and agent artifacts from Evolution. Running the full generated test suite after the workflow (e.g. from the UI) is a separate flow. See Phase3-Architecture-Design-Complete.md §6.4 (AnalysisAgent).

**Real-time execution:** Enabled by default via server config `ENABLE_ANALYSIS_REALTIME_EXECUTION` (default: true). Set to `false` in `.env` to disable. When enabled, `GET /workflows/{id}/results` → `analysis_result.execution_success` contains per-scenario results (`scenario_id`, `success_rate`, `passed_steps`, `total_steps`, `tier_used`, `reliability`, `source`). Verified by `test_four_agent_e2e_real.py`.

**Request body:** `GenerateTestsRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string (URL) | Yes | Target URL to analyze and generate tests for. |
| `user_instruction` | string | No | Optional instruction (e.g. “Test purchase flow for 5G plan”). Drives goal-focused generation when enabled. |
| `depth` | integer | No | Crawl depth: 1 = current page, 2 = include links, 3 = deep crawl. Default: 1. Range: 1–3. |
| `login_credentials` | object | No | Website login: `{ "username": "...", "password": "..." }` or `{ "email": "...", "password": "..." }`. |
| `gmail_credentials` | object | No | Gmail login for OTP: `{ "email": "...", "password": "..." }` (e.g. Gmail app password). |
| `available_file_paths` | string[] | No | Local file paths for uploads during the flow (e.g. HKID image). When the flow requires identity document upload, the agent uses the first path. Example: `["C:\\Users\\...\\test01.jpg"]`. |
| `scenario_types` | string[] | No | Optional filter for scenario categories generated by RequirementsAgent. Allowed values: `\"functional\"`, `\"accessibility\"`, `\"security\"`, `\"edge_case\"`, `\"usability\"`, `\"performance\"`. When omitted, all applicable categories may be generated. |
| `max_scenarios` | integer | No | Optional hard cap on total scenarios produced by RequirementsAgent (after filtering and goal ranking). Range: 1–100. |
| `focus_goal_only` | boolean | No | When `true`, RequirementsAgent runs in **goal-focused mode**: it prioritizes scenarios that are highly aligned with `user_instruction` and trims low-alignment ones before applying `max_scenarios`. Default: `false`. |
| `save_flow_recording` | boolean | No | When `true` (default), after observation the server writes `playwright_flow_recording.json`, `flow_steps.json`, and `playwright_step_ir.json` (deterministic locator IR for tooling) under `backend/artifacts/flow_recordings/{YYYYMMDDTHHMMSSZ}_{short_workflow}/` (UTC time + first UUID segment or slug; sorts by time when listed A→Z). **Full** `POST /generate-tests` also writes `by_test_case/test_case_{id}.json` manifests linking each stored test case to those files. Paths appear in `observation_result.flow_recording_artifacts` (`directory`, `directory_name`, `workflow_id`). Set `false` to skip disk writes. Server-wide disable: `FLOW_RECORDINGS_ENABLED=false` in `.env`. Optional directory override: `FLOW_RECORDINGS_DIR`. **Ignored for observation** when `flow_recording_path` is set (no new crawl). |
| `flow_recording_path` | string | No | Directory name or relative path under `backend/artifacts/flow_recordings` (same validation as `RequirementsRequest`). When set, **skips ObservationAgent** and loads `playwright_flow_recording.json` / `flow_steps.json` from disk; then runs Requirements → Analysis → Evolution in one background job. Use with the same optional fields as a normal generate-tests call (`user_instruction`, `login_credentials`, `scenario_types`, `max_scenarios`, `focus_goal_only`, etc.). **`user_instruction` goal gate** still applies: the saved recording must indicate goal reached (`goal_reached` / `page_context.goal_reached`) if you pass a non-empty instruction. New `requirements/` and `by_test_case/` artifacts are written **next to the existing recording** when enabled. |
| `max_browser_steps` | integer | No | Optional browser-use step cap (1–500); server default 120 if omitted. **Unused** when `flow_recording_path` is set. |
| `max_flow_timeout_seconds` | integer | No | Wall-clock seconds Observation waits for browser-use before snapshotting partial history and cancelling the run (allowed **60–7200**). Default **1200** (20m) if omitted. Ensures Requirements starts only after observation fully finishes (including cancel cleanup on timeout). |
| `http_credentials` | object | No | HTTP Basic auth `{ "username", "password" }` for UAT/preprod. |
| `enable_signature_pad_tool` | boolean | No | Register `draw_signature_pad` for canvas signatures during observation (default: true). |

**Example request:**

```json
{
  "url": "https://example.com/login",
  "user_instruction": "Test login flow with invalid and locked-out credentials",
  "depth": 1,
  "login_credentials": {
    "username": "test@example.com",
    "password": "password123"
  },
  "gmail_credentials": {
    "email": "myaccount@gmail.com",
    "password": "gmail-app-password"
  },
  "scenario_types": ["functional", "accessibility"],
  "max_scenarios": 12,
  "focus_goal_only": true
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse** (e.g. `workflow_id`, `status: "pending"`, `started_at`).

**Next steps:** Poll `GET /workflows/{workflow_id}` for status; `GET /workflows/{workflow_id}/results` for `test_case_ids` and agent outputs when completed.

**Observation artifacts on disk:** When `save_flow_recording` is true (default), `observation_result.flow_recording_artifacts` includes `directory`, `playwright_flow_recording_file`, `flow_steps_file`, `playwright_step_ir_file` (absolute paths). After a full generate-tests run, `test_case_manifest_files` and `test_case_manifest_count` may list per–test-case JSON under `by_test_case/`. The same metadata is mirrored under `observation_result.page_context.flow_recording_artifacts`.

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
| `available_file_paths` | string[] | No | Local file paths for uploads (e.g. HKID image). Same as generate-tests. |
| `save_flow_recording` | boolean | No | Same as `GenerateTestsRequest.save_flow_recording` (default: true). |
| `max_browser_steps` | integer | No | Same as generate-tests (1–500, default 120 on server). |
| `max_flow_timeout_seconds` | integer | No | Same as generate-tests (60–7200; default 1200s wall-clock). |
| `http_credentials` | object | No | HTTP Basic auth for UAT/preprod. |
| `enable_signature_pad_tool` | boolean | No | Same as generate-tests. |

**Example request:**

```json
{
  "url": "https://example.com/login",
  "depth": 1
}
```

**Response:** 202 Accepted, body = **WorkflowStatusResponse**.

**Output (in results):** `observation_result` with `ui_elements`, `flow_steps`, `playwright_flow_recording`, `page_structure`, `page_context`, and (when enabled) `flow_recording_artifacts` with on-disk JSON paths. Use this `workflow_id` in POST `/requirements` to run the next stage.

---

### 3.3 POST /requirements (RequirementsAgent only)

Generates BDD scenarios from observation data. Input is a prior workflow ID (from observation), an inline observation payload, or a saved **`flow_recordings`** folder path (reloads `playwright_flow_recording.json` / `flow_steps.json` — **no ObservationAgent**).

**Request body:** `RequirementsRequest`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | No* | ID of a completed observation workflow (to load observation_result from store). |
| `observation_result` | object | No* | Inline observation result: `ui_elements`, `page_structure`, `page_context`. If set, overrides `flow_recording_path`. |
| `flow_recording_path` | string | No* | Directory name or relative path under `backend/artifacts/flow_recordings` (e.g. `613bbc29-4bde-493d-bbcc-fa874fcaf69c`). Must stay under the recordings root. Rebuilds an observation snapshot from disk. |
| `user_instruction` | string | No | Optional instruction for scenarios. When combined with `focus_goal_only`, drives goal-focused scenario selection. |
| `scenario_types` | string[] | No | Optional filter for scenario categories (same semantics as in `GenerateTestsRequest`). |
| `max_scenarios` | integer | No | Optional hard cap on total scenarios produced (same semantics as in `GenerateTestsRequest`). |
| `focus_goal_only` | boolean | No | When `true`, RequirementsAgent prioritizes scenarios aligned with `user_instruction` and trims low-alignment ones. |

*Provide one of: `workflow_id`, `observation_result`, or `flow_recording_path`.

**Example (chaining from observation endpoint):**

```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_instruction": "Focus on 5G Wi-Fi 7 purchase flow with 48-month contract term",
  "scenario_types": ["functional", "security"],
  "max_scenarios": 10,
  "focus_goal_only": true
}
```

**Example (replay from saved flow recording — skip observation):**

```json
{
  "flow_recording_path": "613bbc29-4bde-493d-bbcc-fa874fcaf69c",
  "user_instruction": "Subscribe to $368/month plan - World Plan.",
  "scenario_types": ["functional", "accessibility"],
  "max_scenarios": 12,
  "focus_goal_only": true
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

**Output (in results):** `analysis_result` with full shape (see [Analysis result shape](#analysis-result-shape)): `risk_scores`, `business_values`, `roi_scores`, `final_prioritization`, `execution_strategy`, and when real-time execution is enabled: `execution_success` (per-scenario `scenario_id`, `success_rate`, `passed_steps`, `total_steps`, `tier_used`, `reliability`, `source`). Use this workflow_id in POST `/evolution` to generate tests.

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
- When the pipeline ran with AnalysisAgent real-time execution enabled: `analysis_result.execution_success` is an array of per-scenario execution results; `analysis_result.execution_strategy` includes `smoke_tests`, `parallel_groups`, and time estimates.

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
| `agent_completed` | An agent finishes (e.g. `elements_found`, `scenarios_generated`, `scenarios_executed` for analysis when real-time execution ran, `duration_seconds`). |
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
