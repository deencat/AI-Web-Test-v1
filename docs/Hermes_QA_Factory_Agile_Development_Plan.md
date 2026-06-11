# Hermes QA Factory — Agile Development Plan

**Version:** 1.0 · **Date:** 2026-06-11  
**Status:** Ready to execute  
**Parent design:** [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md)  
**Program code:** **HF** (Hermes Factory) — sprints **HF-1 … HF-6**

---

## 1. Executive summary

| Aspect | Details |
|--------|---------|
| **Goal** | Production QA Factory: KB + UAT URLs → tests → 24×7 regression → change detection → self-healing, controlled via AI Web Test webapp (not Telegram) |
| **Duration** | 12 weeks (6 × 2-week sprints) |
| **Effort estimate** | ~120 story points (avg 20 pts/sprint) |
| **Team model** | 1–2 developers; split **AWT** (this repo) vs **Hermes Node 1** (profiles + Bridge) |
| **Repos** | `deencat/AI-Web-Test-v1` (primary) · Hermes config on Node 1 (not in git) |
| **Launch criterion** | `full_cycle` job runnable from Agent Chat; Loops A–D on cron; Telegram disabled in prod |

### What already exists (do not rebuild)

| Asset | Location |
|-------|----------|
| MCP core tools | `backend/mcp_server.py` |
| Telegram trigger (dev) | `backend/app/api/v1/endpoints/hermes.py` |
| Schedules + APScheduler | `scheduler_service.py`, schedules API |
| Execution feedback + RCA | `execution_feedback` models/endpoints |
| XPath cache API | `settings.py` xpath-cache routes |
| ReqIQ proxy | `requirements.py` |
| `crawl_and_save` + `reference_test_id` | `api/v2/endpoints/crawl_and_save.py` |
| `improve-tests` | `api/v2/endpoints/improve_tests.py` |
| v4 Hermes profile templates | `docs/Hermes_QA_MultiAgent_Profiles_v4.md` |

---

## 2. Epics

| Epic | ID | Outcome | Sprints |
|------|-----|---------|---------|
| **Control plane** | EPIC-HF-01 | Jobs API, RBAC, scheduler, Agent Console shell | HF-1 |
| **MCP & registry** | EPIC-HF-02 | New MCP tools, journey registry, backlog | HF-2 |
| **Autonomous generation** | EPIC-HF-03 | Planner profiles, Loop A, batch test-gen | HF-3 |
| **Change detection** | EPIC-HF-04 | Snapshots, diff, Loop C | HF-4 |
| **Self-healing** | EPIC-HF-05 | Healer API, Loop D, Heal Review | HF-5 |
| **Observability & launch** | EPIC-HF-06 | Reporter, Observatory, hardening | HF-6 |

---

## 3. Sprint framework

### 3.1 Ceremonies (per 2-week sprint)

| Ceremony | When | Output |
|----------|------|--------|
| Sprint planning | Day 1 | Stories moved To Do → In Progress; owners assigned |
| Daily standup | Daily | Blockers; Node 1 vs AWT split |
| Mid-sprint demo | Day 5 | Working API or UI slice |
| Sprint review | Day 10 | Demo against acceptance criteria |
| Retrospective | Day 10 | Process tweaks |

### 3.2 Definition of Done (all stories)

- [ ] Code merged to `main` with PR review
- [ ] Unit or integration tests for new API routes (where applicable)
- [ ] `env.example` updated for new env vars
- [ ] RBAC enforced server-side (not UI-only)
- [ ] No secrets in logs or committed files
- [ ] Story acceptance criteria verified in demo

### 3.3 Story point scale

| Points | Meaning |
|--------|---------|
| 1 | < half day |
| 2 | ~1 day |
| 3 | 1–2 days |
| 5 | 2–3 days |
| 8 | Full sprint risk — split if possible |

### 3.4 Workstream tags

| Tag | Where |
|-----|--------|
| `[AWT-BE]` | `backend/` |
| `[AWT-FE]` | `frontend/` |
| `[MCP]` | `backend/mcp_server.py` |
| `[HERMES]` | Node 1 `~/.hermes/profiles/` |
| `[BRIDGE]` | Node 1 Hermes Bridge service/script |
| `[OPS]` | `.env`, systemd, runbooks |

---

## 4. Dependency graph

```
HF-1 Control plane ─────────────────────────────────────────┐
       ↓                                                    │
HF-2 MCP + registry                                         │
       ↓                                                    │
HF-3 Planner + Loop A ←── [HERMES] profiles (orchestrator,  │
       │                    planner, test-gen)               │
       ├──────────────────→ HF-4 Change detection (Loop C)  │
       └──────────────────→ HF-5 Self-healing (Loop D)       │
                               ↓                            │
                         HF-6 Observatory + launch ←────────┘
```

**Parallelism:** After HF-2, HF-4 and HF-5 can overlap if two developers are available.

---

## 5. Sprint HF-1 — Control plane & access (2 weeks)

**Sprint goal:** Submit a factory job from webapp; see live status via SSE; cron can enqueue `run_regression`.

**Total:** 21 points

### Stories

#### HF-1.1 — Database models & migrations (5 pts) `[AWT-BE]`

**As** a platform developer, **I want** persistent factory job storage **so that** all factory activity is auditable.

**Tasks:**
- Add models: `FactoryJob`, `FactoryJobEvent` (summary columns only in HF-1; full payload in HF-6)
- Migration scripts in `backend/migrations/`
- CRUD service: `backend/app/services/factory_job_service.py`

**Acceptance criteria:**
- Tables created on `run_migrations.py`
- Can create job `{ job_type, project, params, status, created_by }`
- Can append events `{ job_id, event_type, profile, message, payload_summary }`

---

#### HF-1.2 — Agent jobs REST API (5 pts) `[AWT-BE]`

**As** an `agent_operator`, **I want** to submit and poll factory jobs **so that** I can trigger work without Telegram.

**Tasks:**
- `backend/app/api/v1/endpoints/agent/jobs.py`
- Register in `backend/app/api/v1/api.py`
- `POST /api/v1/agent/jobs` — create job, return `{ job_id, status: "queued" }`
- `GET /api/v1/agent/jobs/{id}` — status + event timeline
- `GET /api/v1/agent/jobs/{id}/stream` — SSE (heartbeat + new events)

**Acceptance criteria:**
- JWT required; `viewer` gets 403 on POST
- SSE client receives events within 2s of append
- OpenAPI docs show new routes

---

#### HF-1.3 — RBAC roles (3 pts) `[AWT-BE]`

**As** an admin, **I want** `agent_operator` and `superadmin` roles **so that** factory access is tiered.

**Tasks:**
- Extend `User.role` validation: `viewer`, `tester`, `agent_operator`, `admin`, `superadmin`
- Dependency: `require_roles(["agent_operator", "admin", "superadmin"])` for job POST
- Bootstrap script or migration: seed one `superadmin` user
- `superadmin` promotion endpoint (admin cannot promote to superadmin)

**Acceptance criteria:**
- Role hierarchy enforced on agent routes
- Non-superadmin cannot call superadmin-only routes (stub 403 for HF-6 routes)

---

#### HF-1.4 — Factory worker (5 pts) `[AWT-BE]`

**As** the system, **I want** a background worker **so that** queued jobs execute without blocking HTTP.

**Tasks:**
- `backend/app/services/factory_worker.py`
- On job create: enqueue async task (asyncio or background task pattern used elsewhere)
- **HF-1 scope:** implement `job_type: run_regression` only — `list_test_cases` + `execute_test` via internal service calls (same logic as MCP)
- Update job status: `queued` → `running` → `completed` | `failed`
- Append `factory_job_events` per step

**Acceptance criteria:**
- POST job → worker runs → executions start for tagged tests
- Failed worker run sets job `failed` with error event
- Integration test: `run_regression` with mock or smoke tag

---

#### HF-1.5 — Agent chat endpoint (3 pts) `[AWT-BE]`

**As** an `agent_operator`, **I want** a chat endpoint **so that** natural language maps to structured jobs.

**Tasks:**
- `POST /api/v1/agent/chat` in `agent/chat.py`
- HF-1: rule-based or LLM mapper → `job_type` + `params` (start with keyword rules: "regression" → `run_regression`)
- Returns `{ job_id, reply }`

**Acceptance criteria:**
- Message "run regression" creates `run_regression` job
- Invalid intent returns 400 with helpful reply

---

#### HF-1.6 — Agent Console shell (3 pts) `[AWT-FE]`

**As** an `agent_operator`, **I want** Agent Console pages **so that** I can chat and monitor jobs.

**Tasks:**
- `frontend/src/pages/AgentConsole/AgentChatPage.tsx`
- `frontend/src/pages/AgentConsole/JobMonitorPage.tsx`
- API client: `frontend/src/services/agentService.ts`
- Nav entry (role-gated): "Agent Console"
- Chat → POST chat → show `job_id` link
- Job Monitor → SSE subscription → event list

**Acceptance criteria:**
- `agent_operator` sees nav; `viewer` does not
- Live events appear during `run_regression` job

---

#### HF-1.7 — Factory scheduler + Telegram flag (2 pts) `[AWT-BE]` `[OPS]`

**As** ops, **I want** cron and a Telegram kill switch **so that** 24×7 runs work and prod disables Telegram.

**Tasks:**
- `HERMES_TELEGRAM_ENABLED` in `config.py` + `env.example`
- Gate `hermes/trigger` when flag false (403 + message)
- `factory_scheduler` in `scheduler_service.py`: nightly `run_regression` via service account (internal job create)

**Acceptance criteria:**
- `HERMES_TELEGRAM_ENABLED=false` blocks Telegram trigger
- Cron creates job without human login (service account JWT or internal bypass)

---

### HF-1 demo script

1. Login as `agent_operator`
2. Agent Chat: "Run regression for tag regression"
3. Job Monitor shows steps → completed
4. Verify executions in Execution History

---

## 6. Sprint HF-2 — MCP expansion & journey registry (2 weeks)

**Sprint goal:** Hermes can call all backlog/schedule/feedback tools via MCP; journey registry seeded for Three HK UAT.

**Total:** 22 points

### Stories

#### HF-2.1 — MCP execution & schedule tools (5 pts) `[MCP]`

- `get_execution_feedback` → `GET /api/v1/executions/{id}/feedback`
- `list_failed_executions` → extend executions list with `result=fail&since=`
- `create_test_schedule`, `list_test_schedules`, `delete_test_schedule` → schedules API wrappers
- Tests in `backend/tests/unit/test_mcp_factory_tools.py`

**Acceptance criteria:** Hermes profile can call each tool via `mcp_server.py` stdio/HTTP and get valid JSON.

---

#### HF-2.2 — MCP ReqIQ proxy tools (3 pts) `[MCP]`

- `get_coverage_matrix`, `get_reqiq_readiness`, `suggest_scenarios_from_wiki`
- Thin wrappers around existing `requirements.py` proxy logic (shared internal function)

**Acceptance criteria:** Tools work with Three-HK `reqiq_project_id` from v5 registry example.

---

#### HF-2.3 — Journey registry API (5 pts) `[AWT-BE]`

- Model: `JourneyRegistryEntry` (id, name, feature_url, tags, capability_keys, reference_test_id, requires_login, project)
- `GET/POST/PATCH/DELETE /api/v1/agent/registry` — `admin`+ only
- Seed: `config/uat-journey-registry.yaml` (from v5 §4.3)

**Acceptance criteria:** Admin can CRUD journeys; seed loads on migration.

---

#### HF-2.4 — Journey backlog API (5 pts) `[AWT-BE]`

- Model: `JourneyBacklogItem` (status: pending | in_progress | done | failed)
- `GET /api/v1/agent/backlog`, `POST /api/v1/agent/backlog` (enqueue)
- MCP: `list_journey_backlog`, `enqueue_journey`

**Acceptance criteria:** Enqueued item appears in backlog; status transitions on worker update.

---

#### HF-2.5 — Registry & backlog UI (4 pts) `[AWT-FE]`

- `JourneyRegistryPage.tsx`, `BacklogQueuePage.tsx`
- Admin-only registry; backlog visible to `agent_operator`+

**Acceptance criteria:** UI CRUD matches API; backlog shows pending items.

---

## 7. Sprint HF-3 — Planner & batch generation (2 weeks)

**Sprint goal:** Loop A drains backlog — planner finds gaps, test-gen creates tests, schedules regression.

**Total:** 24 points

### Stories

#### HF-3.1 — Hermes profiles: orchestrator, planner, test-gen (8 pts) `[HERMES]`

- Create on Node 1:
  - `qa-orchestrator/SOUL.md` (from v4 qa-manager, remove Telegram dependency)
  - `qa-journey-planner/SOUL.md` (coverage + wiki + enqueue)
  - `qa-test-gen/SOUL.md` (batch `crawl_and_save_test`)
- MCP config in each `config.yaml`
- Document in `docs/hermes-profiles/` (optional export folder for version control)

**Acceptance criteria:** Manual CLI: `qa-orchestrator chat -q "drain backlog for Three-HK"` delegates to planner → test-gen → returns test_case_id.

---

#### HF-3.2 — Factory worker: `drain_backlog` + `generate_journey` (5 pts) `[AWT-BE]`

- Worker job types: `drain_backlog`, `generate_journey`, `full_cycle` (orchestrates sub-steps)
- HF-3: cron path uses **factory_worker + MCP** (deterministic); chat path can invoke Hermes Bridge (stub OK if worker-only for demo)

**Acceptance criteria:** `drain_backlog` processes up to N pending backlog items; events logged per item.

---

#### HF-3.3 — Loop A scheduler (3 pts) `[AWT-BE]`

- Cron every 6h: `{ type: drain_backlog, max_items: 3 }`
- Configurable via env: `FACTORY_LOOP_A_CRON`

**Acceptance criteria:** Backlog item auto-processed without human trigger.

---

#### HF-3.4 — Auto-schedule on successful generation (3 pts) `[AWT-BE]`

- After successful `crawl_and_save_test`: `create_test_schedule` cron `0 2 * * *` with regression tag

**Acceptance criteria:** New test appears in Schedules UI with nightly cron.

---

#### HF-3.5 — Loop B regression scheduler (2 pts) `[AWT-BE]`

- Cron every 2h: `run_regression` with `tags: [regression]`
- Nightly full run: `0 2 * * *`

**Acceptance criteria:** Regression runs without human; Job Monitor shows recurring jobs.

---

#### HF-3.6 — Hermes dispatcher & reporter profiles (3 pts) `[HERMES]`

- `qa-dispatcher/SOUL.md`, `qa-reporter/SOUL.md` (webapp notification stub in HF-3; full reporter in HF-6)

**Acceptance criteria:** `full_cycle` manual run: plan → gen → execute → summary event in job log.

---

### HF-3 demo script

1. Enqueue DIY dashboard journey in backlog
2. Trigger `drain_backlog` (chat or wait for cron)
3. New test case + schedule created; smoke execution logged

---

## 8. Sprint HF-4 — Change detection (2 weeks)

**Sprint goal:** Loop C detects UAT URL changes and enqueues regeneration.

**Total:** 20 points

### Stories

#### HF-4.1 — Observe snapshot API (5 pts) `[AWT-BE]`

- `POST /api/v2/observe-snapshot` — wraps `ObservationAgent` for URL-only capture
- Store: `url_snapshots` table (url_hash, html_summary, element_fingerprint, captured_at)

**Acceptance criteria:** Snapshot stored; retrievable by url_hash.

---

#### HF-4.2 — Snapshot diff API (5 pts) `[AWT-BE]`

- `GET /api/v2/snapshots/{url_hash}`
- `POST /api/v2/snapshots/diff` — returns `material_change: bool` + summary text

**Acceptance criteria:** Diff detects meaningful DOM change between two captures; ignores timestamp noise.

---

#### HF-4.3 — MCP snapshot tools (3 pts) `[MCP]`

- `observe_url_snapshot`, `get_url_snapshot`, `diff_url_snapshots`

---

#### HF-4.4 — qa-change-detector profile + Loop C (5 pts) `[HERMES]` `[AWT-BE]`

- Profile SOUL.md: iterate registry URLs, snapshot, diff, enqueue regenerate
- Cron every 4h: `{ type: scan_changes }`
- On material change: enqueue backlog with `reference_test_id` + diff summary as instruction hint

**Acceptance criteria:** Simulated DOM change enqueues regeneration job.

---

#### HF-4.5 — Change detection UI badge (2 pts) `[AWT-FE]`

- Journey Registry shows last snapshot time + change flag

---

## 9. Sprint HF-5 — Self-healing (2 weeks)

**Sprint goal:** Loop D heals failures; double-fail escalates to Heal Review.

**Total:** 22 points

### Stories

#### HF-5.1 — Heal from feedback API (5 pts) `[AWT-BE]`

- `POST /api/v2/heal-from-feedback` — input: `execution_id`
- Logic: load feedback → if flow break, `crawl_and_save` with `reference_test_id`; if xpath, clear cache first
- Reuse `improve_tests` / `evolution_agent` where appropriate

**Acceptance criteria:** Failed execution → heal → new or updated test case ID returned.

---

#### HF-5.2 — MCP heal tools (3 pts) `[MCP]`

- `heal_test_from_feedback`, `clear_xpath_cache` (wrap settings DELETE routes)

---

#### HF-5.3 — qa-healer profile + Loop D (5 pts) `[HERMES]` `[AWT-BE]`

- `qa-healer/SOUL.md` per v5 §12.6
- Cron every 1h: `{ type: heal_failures, since: last_run }`
- Wire `learn_from_feedback` after successful heal (call `EvolutionAgent`)

**Acceptance criteria:** Recent failure auto-healed or escalated after 2 attempts.

---

#### HF-5.4 — Heal Review queue (5 pts) `[AWT-BE]` `[AWT-FE]`

- Model: `HealReviewItem` (execution_id, test_case_id, reason, status: open | resolved)
- API: `GET/PATCH /api/v1/agent/heal-review`
- UI: `HealReviewPage.tsx` for `agent_operator`+

**Acceptance criteria:** Double-fail appears in queue; operator can mark resolved.

---

#### HF-5.5 — Heal integration tests (4 pts) `[AWT-BE]`

- Test: feedback → heal API → execute passes (mock browser tier acceptable)

---

## 10. Sprint HF-6 — Reporting, Observatory & launch (2 weeks)

**Sprint goal:** Production-ready: in-app reports, superadmin Observatory, Telegram off, ops runbook.

**Total:** 23 points

### Stories

#### HF-6.1 — In-app notifications (5 pts) `[AWT-BE]` `[AWT-FE]`

- `notifications` table + bell icon in header
- `qa-reporter` posts digest on job complete (worker hook)
- Optional email via existing email infra (stretch)

**Acceptance criteria:** User sees notification when `full_cycle` completes.

---

#### HF-6.2 — Hermes Bridge event ingestion (5 pts) `[BRIDGE]` `[AWT-BE]`

- Node 1: Bridge posts to `POST /api/v1/agent/hermes/events` (`HERMES_BRIDGE_SECRET`)
- AWT: ingest service with secret redaction
- Extend `FactoryJobEvent` with `payload_full`, `llm_turns`, `hermes_session_id`

**Acceptance criteria:** Delegate events from Hermes appear in job timeline within 5s.

---

#### HF-6.3 — Superadmin Observatory APIs (5 pts) `[AWT-BE]`

- `GET /api/v1/agent/jobs/{id}/hermes-trace` — superadmin only
- `GET /api/v1/agent/hermes/sessions/{sess_id}`
- `observatory_access_log` table

**Acceptance criteria:** `admin` gets 403; `superadmin` sees full payloads; access logged.

---

#### HF-6.4 — Agent Observatory UI (5 pts) `[AWT-FE]`

- Job detail: Observatory tab (superadmin only; tab hidden for others)
- Expandable delegate payloads, LLM turns, session link

**Acceptance criteria:** Matches v5 §8.3 layout; 403 if role tampered client-side.

---

#### HF-6.5 — Launch hardening (3 pts) `[AWT-BE]` `[OPS]`

- Integration test: end-to-end `full_cycle` from chat API
- Integration test: Observatory 403 for non-superadmin
- `docs/Hermes_QA_Factory_Ops_Runbook.md` (new)
- Prod checklist: `HERMES_TELEGRAM_ENABLED=false`, secrets rotated

---

## 11. Product backlog (post-launch)

| ID | Story | Priority |
|----|-------|----------|
| HF-BL-01 | ReqIQ webhook → auto-enqueue planner on wiki compile | High |
| HF-BL-02 | CI/CD post-deploy webhook → `run_regression` | High |
| HF-BL-03 | `factory_worker` vs Hermes Bridge routing per job_type config | Medium |
| HF-BL-04 | LLM turn retention purge job (N days) | Medium |
| HF-BL-05 | Customer export whitelist for Agent Console docs | Low |
| HF-BL-06 | `@healer` hints in single chat (orchestrator forwards) | Low |

---

## 12. Environment variables checklist

| Variable | Sprint | Purpose |
|----------|--------|---------|
| `HERMES_TELEGRAM_ENABLED` | HF-1 | `false` in prod |
| `HERMES_BRIDGE_SECRET` | HF-6 | Bridge → AWT auth |
| `AWT_MCP_SECRET` | existing | Hermes → MCP |
| `FACTORY_LOOP_A_CRON` | HF-3 | Backlog drain schedule |
| `FACTORY_LOOP_B_CRON` | HF-3 | Regression schedule |
| `FACTORY_LOOP_C_CRON` | HF-4 | Change scan schedule |
| `FACTORY_LOOP_D_CRON` | HF-5 | Healer schedule |
| `FACTORY_SERVICE_ACCOUNT_TOKEN` | HF-1 | Cron job auth (or internal bypass) |

Add all to `backend/env.example` as each sprint lands.

---

## 13. Testing strategy

| Layer | HF-1 | HF-2+ |
|-------|------|-------|
| Unit | factory_job_service, RBAC deps | MCP tool wrappers, diff logic |
| Integration | `run_regression` job API | `drain_backlog`, heal flow |
| E2E (manual) | Agent Console chat + SSE | Full cycle Three HK UAT journey |
| Security | JWT on all agent routes | Observatory 403, secret redaction |

Test folder: `backend/tests/integration/test_factory_*.py` (create in HF-1).

---

## 14. Risk register

| Risk | Mitigation |
|------|------------|
| Hermes Node 1 not ready for HF-3 | HF-1–2 use worker+MCP only; Hermes profiles parallel track |
| OneDrive file locks on docs | Close files before agent edits |
| ReqIQ downtime blocks planner | Worker marks job `failed` with clear event; retry cron |
| LLM cost on chat mapper | HF-1 keyword rules; optional LLM in HF-3 |
| Secret leakage in Observatory | Redact at ingest; never stream raw env to browser |

---

## 15. Sprint calendar (suggested)

| Sprint | Weeks | Dates (example) | Goal |
|--------|-------|-----------------|------|
| HF-1 | 1–2 | Jun 16 – Jun 27, 2026 | Control plane + Agent Console shell |
| HF-2 | 3–4 | Jun 30 – Jul 11, 2026 | MCP + registry/backlog |
| HF-3 | 5–6 | Jul 14 – Jul 25, 2026 | Loop A/B + Hermes profiles |
| HF-4 | 7–8 | Jul 28 – Aug 8, 2026 | Loop C change detection |
| HF-5 | 9–10 | Aug 11 – Aug 22, 2026 | Loop D self-healing |
| HF-6 | 11–12 | Aug 25 – Sep 5, 2026 | Observatory + production launch |

Adjust dates to your team start; maintain 2-week cadence.

---

## 16. How to use this plan day-to-day

1. **Sprint planning:** Copy HF-* stories into your board (Jira/GitHub Projects/Tasks.json) as To Do.
2. **Each story:** Create branch `feat/HF-1.2-agent-jobs-api`; link PR to story ID.
3. **Status tags:** `Done` | `In Progress` | `To Do` | `Backlog` (per team convention).
4. **Design reference:** When acceptance criteria are unclear, read [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md) section cited in story.
5. **Demo:** Use sprint demo script at end of each sprint section.
6. **After HF-6:** Move §11 backlog items into HF-7+ planning.

---

## 17. Related documents

| Document | Use |
|----------|-----|
| [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md) | Architecture, APIs, loops, Observatory |
| [Hermes_QA_MultiAgent_Profiles_v4.md](Hermes_QA_MultiAgent_Profiles_v4.md) | SOUL.md templates for Hermes profiles |
| [ReqIQ-API-Integration-Guide.md](ReqIQ-API-Integration-Guide.md) | MCP / proxy behaviour |
| [AI-Web-Test-Developer-Handoff.md](AI-Web-Test-Developer-Handoff.md) | ReqIQ proxy, platform context |
| `Phase3-project-documents/Phase3-Project-Management-Plan-Complete.md` | Platform sprints (Sprint 10.x) — separate from HF program |

---

*This plan implements v5 §9 sprints A–F as executable agile stories. Update story status in your task board; update this doc only when scope changes.*
