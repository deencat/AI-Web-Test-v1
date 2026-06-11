# Hermes QA Factory — Autonomous Workflow Design (v5)

**Version:** 5.0 · **Date:** 2026-06-08  
**Status:** Phase 2 implementation target  
**Supersedes:** Telegram-first patterns in v4 for production; v4 remains valid for dev bootstrap.

---

## 1. Design principles

| Principle | Decision |
|-----------|----------|
| **Production control plane** | AI Web Test webapp + authenticated REST API — not social/messaging channels |
| **Hermes role** | Agent orchestration brain on Node 1 (Ubuntu); specialists call MCP tools |
| **Access control** | JWT + RBAC in AI Web Test; MCP uses service account + `AWT_MCP_SECRET` |
| **Telegram** | Dev-only (`HERMES_TELEGRAM_ENABLED=true`); disabled at launch |
| **“Not ready yet”** | Means **not implemented** — all Phase 2 capabilities are **technically possible** with existing platform building blocks |
| **Extensibility** | Add MCP tools + thin API wrappers in AI Web Test; Hermes SOUL.md updated to use them |

---

## 2. Clarified bottom line (Phase 2 targets)

| Capability | Today (v4) | Phase 2 (implementable) |
|------------|------------|-------------------------|
| Build tests from KB + UAT URLs | ✅ One journey per trigger via `crawl_and_save_test` | ✅ Batch planner processes journey backlog |
| Run many journeys without human | ❌ Not wired | ✅ `qa-journey-planner` cron + backlog queue |
| 24×7 regression unasked | ⚠️ Partial (`test_schedules` + Hermes cron, not unified) | ✅ Unified scheduler via MCP + factory jobs |
| Detect site changes → new tests | ❌ Not wired | ✅ `observe_url_snapshot` + diff + auto-enqueue |
| Self-improving loop | ⚠️ Code exists (`execution_feedback`, `EvolutionAgent`) | ✅ `qa-healer` + `heal_test_from_feedback` MCP |
| Controlled access | ⚠️ Telegram / open trigger | ✅ Webapp Agent Console + RBAC API gateway |
| Hermes agent introspection | ❌ Hermes logs on Node 1 only | ✅ Agent Observatory (`superadmin` only) |

---

## 3. Architecture — QA Factory (production)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI Web Test Webapp (:5173) — ONLY human interface at launch                │
│  • Agent Console (chat)                                                       │
│  • Journey registry editor                                                    │
│  • Factory job monitor (SSE)                                                  │
│  • Schedule & regression dashboard                                            │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ HTTPS + JWT (user/admin roles)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI Web Test API (:8000) — Hermes Control Plane (NEW Phase 2)               │
│  POST /api/v1/agent/jobs          — submit factory job (authenticated)      │
│  GET  /api/v1/agent/jobs/{id}     — job status + logs                       │
│  POST /api/v1/agent/chat          — conversational trigger (same pipeline)  │
│  GET  /api/v1/agent/jobs/{id}/stream — SSE progress                         │
│  Internal: factory_scheduler (APScheduler) — 24×7 cron, no human            │
│  Service account → forwards to Hermes Bridge OR direct MCP orchestration    │
└───────────────┬───────────────────────────────┬─────────────────────────────┘
                │ MCP :8001 (Bearer secret)      │ ReqIQ proxy :3001
                ▼                                ▼
┌───────────────────────────┐      ┌──────────────────────────────────────────┐
│  Hermes Agent (Node 1)    │      │  ReqIQ — KB, wiki, coverage matrix       │
│  Profiles (Phase 2):      │      │  readiness, suggest-from-wiki, feedback  │
│  • qa-orchestrator        │      └──────────────────────────────────────────┘
│  • qa-journey-planner     │
│  • qa-change-detector     │
│  • qa-test-gen            │
│  • qa-healer              │
│  • qa-dispatcher          │
│  • qa-reporter            │
│  Cron: internal only      │
│  Telegram: DEV ONLY         │
└───────────────┬───────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Test runners (Node 2/3 Windows) — Playwright / Stagehand execution         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Access control model

**Role hierarchy** (lowest → highest): `viewer` → `tester` → `agent_operator` → `admin` → **`superadmin`**

| Layer | Mechanism |
|-------|-----------|
| **Webapp users** | JWT login; roles: `viewer`, `tester`, `agent_operator`, `admin`, `superadmin` |
| **Who can start factory jobs** | `agent_operator`, `admin`, `superadmin` |
| **Who can edit journey registry** | `admin`, `superadmin` |
| **Who can view Hermes agent introspection** | **`superadmin` only** (see §8.3 Agent Observatory) |
| **Hermes MCP** | `Authorization: Bearer ${AWT_MCP_SECRET}` — never exposed to browser |
| **Hermes ↔ Control Plane** | Shared `HERMES_BRIDGE_SECRET` on internal network only |
| **Telegram (dev)** | `HERMES_TELEGRAM_ENABLED=false` in production `.env` |

`superadmin` is **not** assignable via normal user self-registration. Only an existing `superadmin` (or bootstrap seed) may promote users. All Observatory access is audit-logged.

### 3.2 Trigger sources (production)

| Source | Auth | Use |
|--------|------|-----|
| **Agent Console chat** | User JWT | Ad-hoc: “Build dashboard journey for DIY UAT” |
| **Factory job API** | User JWT or service account | Structured jobs from UI buttons |
| **Internal cron** | Service account | 24×7 planner, regression, change scan, healer |
| **ReqIQ webhook** | HMAC signature | Wiki compile complete → enqueue planner |
| **CI/CD webhook** | Shared secret | Post-deploy regression |
| ~~Telegram~~ | Dev only | Disabled at launch |

---

## 4. Agent profiles (Phase 2)

### 4.1 Profile map

| Profile | Replaces / extends | Responsibility |
|---------|-------------------|----------------|
| **qa-orchestrator** | qa-manager | Job routing, backlog drain, cron handler, no social dependency |
| **qa-journey-planner** | qa-requirements + new | Coverage gaps, ReqIQ wiki, journey registry → backlog items |
| **qa-change-detector** | new | Snapshot UAT URLs, diff, enqueue regeneration |
| **qa-test-gen** | same | `crawl_and_save_test` per backlog item; batch mode |
| **qa-healer** | new | Failure → feedback → heal / recrawl / xpath cache |
| **qa-dispatcher** | same | Execute tests across runners |
| **qa-reporter** | same | Webapp notifications + optional email; not Telegram in prod |

### 4.2 Factory job types

```yaml
job_types:
  generate_journey:     # KB + UAT URL → new test case
  run_regression:       # Execute tagged test suite
  scan_changes:         # UAT snapshot diff
  heal_failures:        # Process failed executions since last run
  drain_backlog:        # Process N items from journey backlog
  full_cycle:           # planner → generate → execute → heal → report
```

### 4.3 Journey registry (config)

Stored in AI Web Test DB or `config/uat-journey-registry.yaml` (admin-editable via UI).

```yaml
project: Three-HK
reqiq_project_id: cmp0zdx4g0004alp8z77ess7a
default_env_config:
  login_module: login_my3_andrew
  existing_subscriber_module: plan_subscribe_flow_existing_preprod_andrew
  new_subscriber_module: plan_subscriber_flow_andrew
  max_browser_steps: 50
  max_flow_timeout_seconds: 600

journeys:
  - id: postpaid-preprod4-entry
    name: Postpaid Preprod4 Browse
    feature_url: https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/
    tags: [postpaid, preprod4, regression]
    capability_keys: [POSTPAID_BROWSE]
    reference_test_id: null
    stop_at_page_hint: null

  - id: diy-dashboard
    name: DIY Account Dashboard
    feature_url: https://wwwuat.three.com.hk/DTPPD/preprod3/DIY/en/account/dashboard/
    tags: [diy, dashboard, regression, logged-in]
    capability_keys: [DIY_DASHBOARD]
    reference_test_id: null   # set after first login test exists
    requires_login: true
```

---

## 5. Autonomous loops (24×7)

### Loop A — Journey backlog drain (every 6h)

```
factory_scheduler → POST /api/v1/agent/jobs { type: drain_backlog, max_items: 3 }
  → qa-orchestrator
  → qa-journey-planner
       GET coverage_matrix (ReqIQ via MCP proxy)
       list_test_cases (tags) — skip if test exists
       for each gap: enqueue journey item
  → qa-test-gen (batch)
       crawl_and_save_test per item (reference_test_id when set)
  → create_schedule (regression cron per new test)
  → qa-reporter → webapp notification
```

### Loop B — Regression (every 2h + nightly full)

```
factory_scheduler → { type: run_regression, tags: [regression] }
  → qa-dispatcher: list_test_cases + execute_test each (or list_schedules + trigger)
  → qa-reporter: digest to Agent Console
```

### Loop C — Change detection (every 4h)

```
factory_scheduler → { type: scan_changes }
  → qa-change-detector
       for each journey in registry:
         observe_url_snapshot(url)
         diff_url_snapshot(url)
       if material_change:
         enqueue heal or regenerate job
  → qa-test-gen with reference_test_id + updated instruction from diff summary
```

### Loop D — Self-improvement (every 1h)

```
factory_scheduler → { type: heal_failures, since: last_run }
  → qa-healer
       list_executions (failed, recent)
       get_execution_feedback(execution_id)
       if xpath issue: clear_xpath_cache(step)
       if flow issue: heal_test_from_feedback → crawl_and_save with reference_test_id
       re-execute_test
       if pass: mark_healed; else escalate to Agent Console review queue
```

---

## 6. MCP server — current vs Phase 2 tools

### 6.1 Already implemented (`backend/mcp_server.py`)

| Tool | Purpose |
|------|---------|
| `crawl_and_save_test` | Generate executable test from UAT URL + instruction |
| `get_workflow_status` / `get_workflow_results` | Poll crawl job |
| `list_test_cases` / `get_test_case` | Test inventory |
| `execute_test` / `get_execution_status` / `list_executions` | Run & poll |
| `get_execution_stats` | Health summary |
| `list_step_library_modules` | Reusable login/subscriber modules |
| `health_check` | Connectivity |

### 6.2 Phase 2 — MCP tools to implement

| Tool | Backend endpoint (to add or proxy) | Used by |
|------|-----------------------------------|---------|
| `get_execution_feedback` | `GET /executions/{id}/feedback` | qa-healer |
| `list_failed_executions` | `GET /executions?result=fail&since=` | qa-healer |
| `create_test_schedule` | `POST /schedules/` | qa-orchestrator |
| `list_test_schedules` | `GET /schedules/` | qa-orchestrator |
| `delete_test_schedule` | `DELETE /schedules/{id}` | qa-orchestrator |
| `observe_url_snapshot` | `POST /api/v2/observe-snapshot` (new) | qa-change-detector |
| `get_url_snapshot` | `GET /api/v2/snapshots/{url_hash}` (new) | qa-change-detector |
| `diff_url_snapshots` | `POST /api/v2/snapshots/diff` (new) | qa-change-detector |
| `get_coverage_matrix` | ReqIQ proxy `GET …/coverage-matrix` | qa-journey-planner |
| `get_reqiq_readiness` | ReqIQ proxy `GET …/readiness` | qa-journey-planner |
| `suggest_scenarios_from_wiki` | ReqIQ proxy `POST …/suggest-from-wiki` | qa-journey-planner |
| `heal_test_from_feedback` | `POST /api/v2/heal-from-feedback` (new) | qa-healer |
| `clear_xpath_cache` | `DELETE /api/v1/xpath-cache/...` | qa-healer |
| `list_journey_backlog` | `GET /api/v1/agent/backlog` (new) | qa-orchestrator |
| `enqueue_journey` | `POST /api/v1/agent/backlog` (new) | qa-journey-planner |
| `submit_factory_job` | `POST /api/v1/agent/jobs` (new) | webapp, cron |
| `get_factory_job_status` | `GET /api/v1/agent/jobs/{id}` (new) | webapp SSE |

Implementation note: MCP server already authenticates as AWT service account — new tools are thin wrappers like existing ones.

---

## 7. Hermes Control Plane API (AI Web Test — new)

Replace `POST /api/v1/hermes/trigger` (Telegram) with:

### 7.1 Submit job

```http
POST /api/v1/agent/jobs
Authorization: Bearer <user_jwt>
Content-Type: application/json

{
  "job_type": "full_cycle",
  "project": "Three-HK",
  "params": {
    "max_backlog_items": 3,
    "tags": ["regression"],
    "auto_approve": true
  }
}
```

Response: `{ "job_id": "uuid", "status": "queued" }`

### 7.2 Chat interface (webapp)

```http
POST /api/v1/agent/chat
Authorization: Bearer <user_jwt>

{
  "message": "Build and schedule regression for DIY dashboard UAT",
  "context": { "project": "Three-HK" }
}
```

Response: `{ "job_id": "uuid", "reply": "Queued full_cycle job…" }`

Backend translates natural language → structured `job_type` + params → forwards to Hermes Bridge.

### 7.3 Hermes Bridge (Node 1)

Thin service or SSH-invoked CLI:

```bash
# Internal only — called by AWT API with HERMES_BRIDGE_SECRET
qa-orchestrator job run --json '{"job_type":"drain_backlog",...}'
```

Alternative: AWT `factory_worker` calls MCP tools directly without Hermes for deterministic cron paths; Hermes handles chat/ad-hoc reasoning.

**Recommended hybrid:**
- **Cron / deterministic loops** → AWT `factory_worker` + MCP (reliable, testable)
- **Chat / complex planning** → Hermes `qa-orchestrator` (LLM reasoning)

### 7.4 Hermes Bridge — event ingestion (for monitoring)

Hermes Bridge on Node 1 **POSTs structured events** to AWT as each `delegate_task` and MCP call progresses. This powers Job Monitor (all operators) and Agent Observatory (superadmin only).

```http
POST /api/v1/agent/hermes/events
Authorization: Bearer <HERMES_BRIDGE_SECRET>
Content-Type: application/json

{
  "job_id": "uuid",
  "hermes_session_id": "sess_abc123",
  "profile": "qa-test-gen",
  "event_type": "delegate_complete",
  "parent_profile": "qa-orchestrator",
  "payload_summary": { "test_case_id": 1302, "status": "success" },
  "payload_full": { "...": "..." },
  "llm_turns": [
    { "role": "assistant", "content": "Calling crawl_and_save_test...", "tokens": 412 }
  ],
  "timestamp": "2026-06-08T14:02:45Z"
}
```

**Event types:** `job_started` · `delegate_start` · `delegate_complete` · `mcp_tool_call` · `mcp_tool_result` · `llm_turn` · `error` · `job_complete`

Stored in `factory_job_events` (summary for all roles; `payload_full` + `llm_turns` retained for superadmin retrieval with secret redaction at ingest).

**Superadmin read APIs:**

```http
GET /api/v1/agent/jobs/{id}/events          # step timeline (agent_operator+)
GET /api/v1/agent/jobs/{id}/hermes-trace    # full delegate + LLM trace (superadmin only)
GET /api/v1/agent/hermes/sessions/{sess_id} # session drill-down + Node 1 log link (superadmin only)
```

---

## 8. Webapp UI — Agent Console (Phase 2)

| Screen | Purpose | Roles |
|--------|---------|-------|
| **Agent Chat** | Natural language → factory jobs; shows `job_id` | `agent_operator`+ |
| **Job Monitor** | Live SSE: planner → gen → run → heal → done | `agent_operator`+ |
| **Journey Registry** | CRUD for UAT URLs, tags, `reference_test_id` | `admin`+ |
| **Backlog Queue** | Pending / in-progress / done journeys | `agent_operator`+ |
| **Heal Review** | Escalations qa-healer could not auto-fix | `agent_operator`+ |
| **Schedules** | Visual cron for regression | `agent_operator`+ |
| **Agent Observatory** | Hermes delegate traces, LLM reasoning, session drill-down | **`superadmin` only** |

### 8.1 Chat model — one window, not one per agent

Production uses **one Agent Chat** routed to `qa-orchestrator` only (replaces the single Telegram `qa-manager` bot). Users do not open separate chats per specialist profile. Multi-agent activity appears in **Job Monitor**, not as peer-to-peer agent conversations.

### 8.2 Agent communication — hub-and-spoke (not group chat)

Hermes specialists **do not message each other directly**. Communication patterns:

```
Human → qa-orchestrator (single chat entry)
           ├─ delegate_task → qa-journey-planner → JSON result back
           ├─ delegate_task → qa-test-gen        → JSON result back (+ MCP calls to AWT)
           ├─ delegate_task → qa-dispatcher      → JSON result back (+ MCP calls to AWT)
           ├─ delegate_task → qa-healer          → JSON result back
           └─ delegate_task → qa-reporter        → JSON result back

Cron path (no Hermes LLM): factory_worker → MCP tools directly
```

**What `agent_operator` / `admin` see in Job Monitor** — structured pipeline events only:

```
14:02:01  qa-orchestrator      job queued (full_cycle)
14:02:03  qa-journey-planner  coverage gap → enqueue DIY dashboard
14:02:45  qa-test-gen         crawl_and_save_test → test_case_id 1302
14:03:12  qa-dispatcher       execute_test → 4/5 passed
14:03:22  qa-reporter         digest posted
```

This is a **CI-style build log**, not raw LLM transcripts between agents.

**AWT backend agents** (`ObservationAgent`, `RequirementsAgent`, etc.) are a separate layer inside `crawl_and_save` — synchronous in-process handoffs, not Hermes profiles. Redis message-bus remains a future AWT-internal concern; Hermes factory monitoring uses `factory_job_events` instead.

### 8.3 Agent Observatory — Hermes introspection (`superadmin` only)

Platform operators and QA leads use Job Monitor. **`superadmin`** users get an additional **Agent Observatory** panel (hidden from `admin` and below) to inspect internal Hermes behaviour for debugging, compliance, and prompt tuning.

| Capability | Visible to | Source |
|------------|------------|--------|
| Step timeline (profile, status, duration) | `agent_operator`+ | `factory_job_events` summary |
| `delegate_task` request/response payloads | **`superadmin`** | `payload_full` on `delegate_*` events |
| LLM reasoning turns per profile | **`superadmin`** | `llm_turns` on events |
| MCP tool args/results linked to job | **`superadmin`** | `mcp_tool_*` events |
| Hermes `session_id` + Node 1 log path | **`superadmin`** | Bridge metadata |
| Who viewed a trace | **`superadmin`** | `observatory_access_log` |

**UI layout (job detail page):**

```
┌─────────────────────────────────────────────────────────────┐
│ Job #a1b2 — full_cycle — completed                          │
├──────────────────────────────┬──────────────────────────────┤
│ Job Monitor (all operators)  │ Agent Observatory            │
│ • planner ✓                  │ 🔒 superadmin only           │
│ • test-gen ✓                 │                              │
│ • dispatcher ✓               │ delegate: orch → test-gen    │
│ • reporter ✓                 │   [expand payload JSON]      │
│                              │   [expand LLM turns]         │
│                              │ session: sess_abc123         │
│                              │ [Open Node 1 Hermes log]     │
└──────────────────────────────┴──────────────────────────────┘
```

**Security rules:**

- Observatory routes return **403** for non-`superadmin` JWT (server-enforced; UI tab not rendered).
- Secrets redacted at ingest: `AWT_MCP_SECRET`, `HERMES_BRIDGE_SECRET`, passwords, API keys, `REQIQ_API_KEY`.
- `observatory_access_log` records `{ user_id, job_id, session_id, viewed_at }` for every trace open.
- Optional retention policy: raw `llm_turns` purged after N days; summary events kept.

**Not in Observatory (by design):**

- Peer-to-peer chat between specialists (does not exist — orchestrator mediates).
- Redis message-bus events (AWT stub; not wired to Hermes — use `factory_job_events` instead).

---

## 9. Phase 2 implementation plan

### Sprint A — Control plane & access (2 weeks)

- [ ] `HERMES_TELEGRAM_ENABLED` flag; deprecate Telegram trigger in prod
- [ ] `POST/GET /api/v1/agent/jobs` + job store (SQLite table `factory_jobs`)
- [ ] `factory_job_events` table (summary + full payload columns)
- [ ] RBAC: `agent_operator` + `superadmin` roles; hierarchy enforcement middleware
- [ ] Agent Console shell page + job monitor SSE
- [ ] `factory_scheduler` APScheduler jobs (service account)

### Sprint B — MCP expansion (2 weeks)

- [ ] MCP: `get_execution_feedback`, `list_failed_executions`
- [ ] MCP: `create_test_schedule`, `list_test_schedules`, `delete_test_schedule`
- [ ] MCP: `get_coverage_matrix`, `get_reqiq_readiness` (ReqIQ proxy)
- [ ] MCP: `list_journey_backlog`, `enqueue_journey`
- [ ] Journey registry API + YAML seed for Three HK UAT URLs

### Sprint C — Planner + batch generation (2 weeks)

- [ ] `qa-journey-planner` SOUL.md + Hermes profile
- [ ] Backlog drain loop (Loop A)
- [ ] Batch `qa-test-gen` (process up to N per cycle)
- [ ] Auto `create_test_schedule` on successful generation

### Sprint D — Change detection (2 weeks)

- [ ] `POST /api/v2/observe-snapshot` (ObservationAgent wrapper)
- [ ] Snapshot store + diff API
- [ ] MCP: `observe_url_snapshot`, `diff_url_snapshots`
- [ ] `qa-change-detector` profile + Loop C

### Sprint E — Self-healing (2 weeks)

- [ ] `POST /api/v2/heal-from-feedback` (reference_test_id recrawl)
- [ ] MCP: `heal_test_from_feedback`, `clear_xpath_cache`
- [ ] `qa-healer` profile + Loop D
- [ ] Heal review queue in webapp

### Sprint F — Reporting, Observatory & hardening (2 weeks)

- [ ] `qa-reporter` → webapp notifications (in-app + optional email)
- [ ] Daily digest cron
- [ ] Hermes Bridge → `POST /api/v1/agent/hermes/events` (delegate + MCP + LLM events)
- [ ] Superadmin APIs: `GET …/hermes-trace`, `GET …/hermes/sessions/{id}`
- [ ] Agent Observatory UI panel (superadmin-only tab on job detail)
- [ ] `observatory_access_log` + secret redaction at event ingest
- [ ] Integration tests for full_cycle job + Observatory 403 for non-superadmin
- [ ] Disable Telegram; document ops runbook

---

## 10. Example: UAT journey via webapp (production flow)

**User (Agent Console):**

> Build a regression test for Postpaid Preprod4 starting at  
> https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/  
> using the KB wiki for Three-HK. Schedule nightly regression.

**System:**

1. `POST /api/v1/agent/chat` → job `full_cycle`
2. qa-journey-planner: `get_reqiq_readiness` → wiki OK
3. qa-test-gen: `crawl_and_save_test` with extracted `user_instruction`
4. qa-dispatcher: `execute_test` (smoke validation)
5. qa-orchestrator: `create_test_schedule` cron `0 2 * * *`
6. Webapp: “Test #1302 created. Scheduled nightly. First run: 4/5 steps passed.”

No Telegram. Full audit trail in `factory_jobs` table.

---

## 11. Migration from v4

| v4 pattern | v5 replacement |
|------------|----------------|
| Telegram → qa-manager | `POST /api/v1/agent/chat` or jobs API |
| `hermes/trigger` (Telegram) | `agent/jobs` with JWT |
| qa-manager | qa-orchestrator |
| Nightly cron message to Telegram bot | `factory_scheduler` → jobs API |
| qa-reporter → Telegram | qa-reporter → webapp + email |
| Manual one journey | Journey registry + backlog drain |

Keep v4 Telegram setup in dev: `HERMES_TELEGRAM_ENABLED=true` for mobile testing only.

---

## 12. Self-improvement architecture

Self-improvement is **technically possible** and partially built today. Phase 2 closes the loop so the QA factory improves **without being asked**. This section documents what exists now, what Phase 2 adds, and how the layers fit together.

### 12.1 Five layers of self-improvement

```
Layer 1 (runtime)      Test run → 3-tier engine + XPath cache → adapt in same execution
Layer 2 (capture)      Failure → execution_feedback + RCA + screenshots → stored in DB
Layer 3 (regenerate)   Feedback → recrawl / improve-tests / learn_from_feedback → update test assets
Layer 4 (requirements) ReqIQ wiki-feedback + wiki-suggest-profile → better scenarios from KB
Layer 5 (Phase 2)      qa-healer cron → wires Layers 2–4 automatically (closed loop)
```

| Layer | Mechanism | Status today | Phase 2 |
|-------|-----------|--------------|---------|
| **1 — Runtime** | 3-tier execution (Playwright → hybrid/observe → Stagehand); XPath cache promote/clear | ✅ Works on every run | ✅ Same |
| **2 — Capture** | `execution_feedback` table; RCA on `all_tiers_exhausted`; screenshots, DOM snapshot | ✅ Stored after failures | ✅ Same |
| **3 — Regenerate** | `EvolutionAgent.learn_from_feedback()`; `POST /api/v2/improve-tests`; `crawl_and_save_test` + `reference_test_id` | ⚠️ Code exists, **not wired** to Hermes or cron | ✅ qa-healer invokes automatically |
| **4 — Requirements** | ReqIQ `wiki-feedback`, `wiki-suggest-profile`, `suggest-from-wiki` | ⚠️ Human review in ReqIQ UI | ✅ Planner uses profile; optional auto-policy |
| **5 — Closed loop** | `qa-healer` + Loop D + MCP heal tools | ❌ Not implemented | ✅ Sprint E |

### 12.2 Layer 1 — Runtime self-heal (during execution)

No Hermes involvement. When a test runs:

1. **Tier 1** — Cached XPath / Playwright selectors (fast path)
2. **Tier 2** — `observe()` + hybrid re-find if DOM changed
3. **Tier 3** — Stagehand AI fallback

**XPath cache** (Sprint 10.16): successful selectors promoted; stale entries cleared per step via Settings / XPath Cache UI.

This adapts **within the same execution**. It does not rewrite the saved test case unless regeneration is triggered (Layer 3 or 5).

**Code:** `backend/app/services/three_tier_execution_service.py`, `tier2_hybrid.py`, `xpath_cache_service.py`

### 12.3 Layer 2 — Failure capture (after execution)

On failure, the execution service writes to `execution_feedback`:

- Error type, failed selector, page URL
- Screenshot + HTML snapshot
- Root cause analysis (plain-English LLM summary when all tiers fail)
- Optional human correction (`corrected_step`)

**API:** `GET /api/v1/executions/{id}/feedback`

**Gap today:** Data is stored but nothing **automatically** reads it to update tests or trigger the factory.

**Code:** `backend/app/models/execution_feedback.py`, `backend/app/services/execution_service.py`

### 12.4 Layer 3 — Test asset regeneration (code exists, not closed)

#### A. `EvolutionAgent.learn_from_feedback()`

Analyzes pass/fail patterns, queries execution history, emits **recommendations** for `RequirementsAgent` on the next generation cycle.

`RequirementsAgent` already accepts `execution_feedback` in its LLM prompt.

**Gap:** Not called from Hermes, crawl-and-save, factory cron, or production E2E path.

**Code:** `backend/agents/evolution_agent.py`, `backend/agents/requirements_agent.py`

#### B. `POST /api/v2/improve-tests`

Iterative evolution + analysis loop on existing `test_case_ids` (`max_iterations`).

**Gap:** Not wired to factory scheduler or qa-healer.

**Code:** `backend/app/api/v2/endpoints/improve_tests.py`

#### C. `crawl_and_save_test` + `reference_test_id`

Recrawl with prior test as quality anchor when UI/flow changes.

**Gap:** Nothing **automatically** triggers recrawl after failure today.

**Code:** `backend/app/api/v2/endpoints/crawl_and_save.py`, MCP `crawl_and_save_test`

### 12.5 Layer 4 — ReqIQ requirements learning

| Mechanism | What improves |
|-----------|----------------|
| `POST …/wiki-feedback` (accept / reject) | Which wiki-suggested scenarios are valid |
| `GET …/wiki-suggest-profile` | Ranking for future `suggest-from-wiki` |
| `PATCH …/requirements` on edited DRAFT | Records `accept_edited` feedback |

Improves **what journeys get generated from KB**, not Playwright steps directly. Used by `qa-journey-planner`.

**Code:** `backend/app/api/v1/endpoints/requirements.py` (ReqIQ proxy)

### 12.6 Layer 5 — qa-healer closed loop (Phase 2 — Sprint E)

See also **§5 Loop D**.

```
Every 1h (factory_scheduler, job_type: heal_failures):
  list_failed_executions(since: last_run)
    for each failure:
      feedback = get_execution_feedback(execution_id)

      if xpath/selector stale:
        clear_xpath_cache(step) → retry execute_test once

      elif flow/navigation broke (RCA):
        heal_test_from_feedback → crawl_and_save with reference_test_id
        execute_test(updated id)

      if pass: mark_healed; optional learn_from_feedback → planner
      elif fail twice: Heal Review queue (human escalation)
```

**MCP tools:** `get_execution_feedback`, `list_failed_executions`, `heal_test_from_feedback`, `clear_xpath_cache`

**New API:** `POST /api/v2/heal-from-feedback`

### 12.7 Three improvement speeds

| Speed | Mechanism | Typical latency | Updates test file? |
|-------|-----------|-----------------|-------------------|
| **Fast** | 3-tier + XPath cache | Seconds (same run) | No |
| **Medium** | qa-healer + `reference_test_id` | Minutes–hours | Yes |
| **Slow** | ReqIQ profile + journey planner | Days | New journeys |

### 12.8 Honest summary — what “self-improving” means

| Question | Today | After Phase 2 (Sprint E) |
|----------|-------|---------------------------|
| Test adapts **mid-run** if selector breaks? | ✅ | ✅ |
| Failed run **stored** with RCA? | ✅ | ✅ |
| Test case **updated automatically** after failure? | ❌ | ✅ qa-healer |
| Next **generation** avoids past mistakes? | ⚠️ Unused code | ✅ |
| KB scenarios **improve** over time? | ⚠️ Human wiki-feedback | ✅ + profile |
| Factory does this **without being asked**? | ❌ | ✅ Loop D |
| Human only when auto-heal stuck? | ❌ | ✅ Heal Review |

### 12.9 Phase 2 priority for self-improvement (Sprint E)

1. MCP: `get_execution_feedback`, `list_failed_executions`
2. API: `POST /api/v2/heal-from-feedback`
3. MCP: `heal_test_from_feedback`, `clear_xpath_cache`
4. Profile: `qa-healer` SOUL.md + Loop D cron
5. Wire `learn_from_feedback` after successful heal → journey planner
6. Webapp: **Heal Review** queue for double-fail escalations

---

## 13. References

- [Hermes_QA_Factory_Agile_Development_Plan.md](Hermes_QA_Factory_Agile_Development_Plan.md) — executable sprint plan (HF-1 … HF-6) with user stories and acceptance criteria
- [Hermes_QA_MultiAgent_Profiles_v4.md](Hermes_QA_MultiAgent_Profiles_v4.md) — SOUL.md templates; `delegate_task` communication flow
- [ReqIQ-API-Integration-Guide.md](ReqIQ-API-Integration-Guide.md) — crawl-and-save, execution, feedback
- [AI-Web-Test-Developer-Handoff.md](AI-Web-Test-Developer-Handoff.md) — ReqIQ proxy, wiki, coverage
- `backend/mcp_server.py` — MCP tool implementations
- `backend/app/services/scheduler_service.py` — APScheduler foundation
- `backend/agents/evolution_agent.py` — `learn_from_feedback()` for healer logic
- `backend/tests/integration/CONTINUOUS_IMPROVEMENT_AND_AGENT_COMMUNICATION.md` — continuous improvement status
- `backend/app/api/v2/endpoints/improve_tests.py` — iterative test improvement API
