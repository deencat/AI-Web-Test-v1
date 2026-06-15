# Hermes QA Factory — Agile Development Plan

**Version:** 1.5 · **Date:** 2026-06-08  
**Status:** **Phase A complete** · **Phase B in progress** (Bridge ✅ · Hermes profiles ⬜ · **HF-7 migration pack** ✅)  
**Parent design:** [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md)  
**Program code:** **HF** (Hermes Factory) — sprints **HF-1 … HF-6**

**Legend:** ✅ Done · ⚠️ Partial · 🔜 Next · ⬜ Not started · ⏸ Phase B (Hermes Node 1)

---

## 0. Progress tracker (live)

**Last updated:** 2026-06-08  
**Branch:** `feat/hermes-qa-factory`  
**Key commits:** HF-1 `e33a6b3` · HF-2+3 `503244e` · HF-4 `ff6af29` · HF-5 `e0e16cd` · HF-6 `07244fe` · superadmin RBAC `e77d1be` · Bridge ingest `173b4f7` · Bridge service `e45a2dc` · HF-7 migration docs/scripts *(pending commit)*

### Current focus

| Track | Status | Next |
|-------|--------|------|
| **Phase A (AWT)** | ✅ **Complete** | HF-1.6 SSE polish (optional) |
| **Phase B (Bridge)** | ✅ **HF-6.6 + HF-3.7** (`e45a2dc`) | Local demo: bridge `serve` + `HERMES_BRIDGE_URL` |
| **Phase B (Hermes)** | 🔜 **HF-2.6–2.7 done** | HF-3.1 deploy orchestrator on Ubuntu dev PC |
| **HF-7 Migration** | ✅ **Guide + script stubs** | Harden scripts after first dev smoke (HF-7.5 prod cutover) |

### Sprint rollup (AWT-first Phase A)

| Sprint | Phase A status | Hermes (Phase B) | Demo / validation |
|--------|----------------|------------------|-------------------|
| **HF-1** | ✅ Done | — | Agent Console + `run_regression` |
| **HF-2** | ✅ Done (2.1–2.5) | ✅ 2.6–2.7 | Registry, backlog, MCP tools |
| **HF-3** | ✅ Done (3.2–3.5) | ⬜ 3.1, 3.6, 3.7 | `drain_backlog`, Loops A & B cron |
| **HF-4** | ✅ Done (4.1–4.4, 4.6) | ⬜ 4.5 Hermes | `scan_changes`, registry badges |
| **HF-5** | ✅ Done (5.1–5.5 AWT) | ⬜ 5.3b | Heal API + Loop D |
| **HF-6** | ✅ AWT (6.1–6.5) · ✅ 6.2 ingest · ✅ 6.6 service · ✅ 3.7 chat→bridge | ⬜ 6.7 | Observatory + launch |

### Story checklist

| ID | Story | Status | Commit / note |
|----|-------|--------|---------------|
| **HF-1** | | | |
| HF-1.1 | Database models & migrations | ✅ | `e33a6b3` |
| HF-1.2 | Agent jobs REST API + SSE | ✅ | `e33a6b3` |
| HF-1.3 | RBAC roles | ⚠️ | Superadmin-only Agent Console (`e77d1be`); `bootstrap_factory_users.py`; promotion API **not** implemented |
| HF-1.4 | Factory worker (`run_regression`) | ✅ | `e33a6b3` |
| HF-1.5 | Agent chat endpoint | ✅ | `e33a6b3` |
| HF-1.6 | Agent Console shell | ⚠️ | Single page; job monitor uses **polling** (SSE auth deferred) |
| HF-1.7 | Factory scheduler + Telegram flag | ✅ | `e33a6b3` |
| **HF-2** | | | |
| HF-2.1 | MCP execution & schedule tools | ✅ | `503244e` |
| HF-2.2 | MCP ReqIQ proxy tools | ✅ | `503244e` |
| HF-2.3 | Journey registry API | ✅ | `503244e` |
| HF-2.4 | Journey backlog API | ✅ | `503244e` |
| HF-2.5 | Registry & backlog UI | ✅ | `503244e` |
| HF-2.6 | `qa-orchestrator` SOUL draft | ✅ | `docs/hermes-profiles/qa-orchestrator/` |
| HF-2.7 | Shared Hermes MCP config template | ✅ | `_shared/mcp_servers.yaml.example` |
| **HF-3** | | | |
| HF-3.1a–d | Hermes orchestrator / planner / test-gen | ⏸ | Phase B |
| HF-3.2 | Worker: `drain_backlog`, `generate_journey`, `full_cycle` | ✅ | `503244e` |
| HF-3.3 | Loop A scheduler | ✅ | `503244e` |
| HF-3.4 | Auto-schedule on generation | ✅ | `503244e` |
| HF-3.5 | Loop B regression scheduler | ✅ | `503244e` |
| HF-3.6a–c | Dispatcher / reporter / Hermes smoke | ⏸ | Phase B |
| HF-3.7 | Chat → Bridge stub | ✅ | `HERMES_BRIDGE_URL` → `factory_bridge_client` |
| **HF-4** | | | |
| HF-4.1 | Observe snapshot API | ✅ | `ff6af29` — httpx capture (lightweight; not full ObservationAgent) |
| HF-4.2 | Snapshot diff API | ✅ | `ff6af29` |
| HF-4.3 | MCP snapshot tools | ✅ | `ff6af29` |
| HF-4.4 | Loop C worker + cron (`scan_changes`) | ✅ | `ff6af29` |
| HF-4.5 | `qa-change-detector` Hermes deploy | ⏸ | Phase B |
| HF-4.6 | Change detection registry badge | ✅ | `ff6af29` |
| **HF-5** | | | |
| HF-5.1 | Heal from feedback API | ✅ | `POST /api/v2/heal-from-feedback` |
| HF-5.2 | MCP heal tools | ✅ | `heal_test_from_feedback`, `clear_xpath_cache` |
| HF-5.3a | Loop D worker + cron | ✅ | `heal_failures` + `FACTORY_LOOP_D_CRON` |
| HF-5.3b | `qa-healer` Hermes deploy | ⏸ | Phase B |
| HF-5.4 | Heal Review queue | ✅ | `/agent/heal-review` + UI |
| HF-5.5 | Heal integration tests | ✅ | `test_factory_heal_hf5.py` |
| **HF-6** | | | |
| HF-6.1 | In-app notifications | ✅ | Bell + worker hook |
| HF-6.2 | Hermes Bridge ingestion | ✅ | `POST /agent/hermes/events` |
| HF-6.3 | Observatory APIs | ✅ | hermes-trace + access log |
| HF-6.4 | Observatory UI | ✅ | Agent Console panel |
| HF-6.5 | Launch hardening + runbook | ✅ | `Hermes_QA_Factory_Ops_Runbook.md` |
| HF-6.6 | Bridge HTTP service + demo delegates | ✅ | `hermes_bridge.py serve` |
| HF-6.7 | Reporter → webapp notifications | ⬜ | Worker hook already notifies superadmin |
| **HF-7** | **Hermes dev → prod migration** | | |
| HF-7.1 | Migration guide + env templates | ✅ | `Hermes_Environment_Migration_Guide.md` |
| HF-7.2 | `pack-profiles.sh` | 🔜 | `scripts/hermes-migrate/` — harden after dev smoke |
| HF-7.3 | `deploy-profiles.sh` | 🔜 | `--from-tar` / `--from-git` |
| HF-7.4 | `smoke-check.sh` | 🔜 | MCP + Bridge health |
| HF-7.5 | Prod cutover + security sign-off | ⬜ | After mini PC dev checklist §4 |

### Loops (factory_worker — no Hermes required)

| Loop | Schedule env | Job type | Status |
|------|--------------|----------|--------|
| **A** — Backlog drain | `FACTORY_LOOP_A_CRON` | `drain_backlog` | ✅ |
| **B** — Regression | `FACTORY_REGRESSION_CRON` + nightly | `run_regression` | ✅ |
| **C** — Change scan | `FACTORY_LOOP_C_CRON` | `scan_changes` | ✅ |
| **D** — Self-heal | `FACTORY_LOOP_D_CRON` | `heal_failures` | ✅ |

### Phase B gate (required before launch)

| Item | Status |
|------|--------|
| HF-6.2 Bridge event ingest | ✅ `173b4f7` |
| HF-6.6 Bridge service on Node 1 | ✅ demo + orchestrator CLI mode |
| HF-3.7 Chat → Bridge | ✅ when `HERMES_BRIDGE_URL` set |
| HF-2.6–2.7 Hermes MCP template | ✅ |
| HF-3.1, 3.6, 4.5, 5.3b profile deploy | ⬜ |
| HF-6.7 Reporter Hermes wiring | ⬜ |
| HF-7.5 Prod migration cutover | ⬜ | After dev Ubuntu sign-off |

See §4.3 migration strategy and [Hermes_Environment_Migration_Guide.md](hermes-profiles/Hermes_Environment_Migration_Guide.md).

---

## 1. Executive summary

| Aspect | Details |
|--------|---------|
| **Goal** | Production QA Factory: KB + UAT URLs → tests → 24×7 regression → change detection → self-healing, controlled via AI Web Test webapp (not Telegram) |
| **Duration** | 12 weeks (6 × 2-week sprints) |
| **Effort estimate** | ~120 story points (avg 20 pts/sprint) |
| **Team model** | **AWT-first sequencing supported** (§4.2): finish all `[AWT-*]` / `[MCP]` stories, then Hermes + Bridge. Hermes still **required before launch**, not before AWT dev. |
| **Repos** | `deencat/AI-Web-Test-v1` (AWT + `docs/hermes-profiles/` SOUL templates) · Node 1 `~/.hermes/profiles/` (deployed copy) |
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

| Epic | ID | Outcome | Sprints | Status |
|------|-----|---------|---------|--------|
| **Control plane** | EPIC-HF-01 | Jobs API, RBAC, scheduler, Agent Console shell | HF-1 | ✅ AWT |
| **MCP & registry** | EPIC-HF-02 | New MCP tools, journey registry, backlog | HF-2 | ✅ AWT |
| **Autonomous generation** | EPIC-HF-03 | Planner profiles, Loop A, batch test-gen | HF-3 | ✅ AWT · ⬜ Hermes |
| **Change detection** | EPIC-HF-04 | Snapshots, diff, Loop C | HF-4 | ✅ AWT · ⬜ Hermes |
| **Self-healing** | EPIC-HF-05 | Healer API, Loop D, Heal Review | HF-5 | 🔜 |
| **Observability & launch** | EPIC-HF-06 | Reporter, Observatory, hardening | HF-6 | 🔜 Bridge ✅ · Hermes reporter ⬜ |
| **Hermes Node 1 profiles & Bridge** | EPIC-HF-07 | All 7 SOUL.md profiles, MCP config, deploy, Bridge | HF-2 … HF-6 | ⬜ Phase B |

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

**AWT stories (`[AWT-BE]`, `[AWT-FE]`, `[MCP]`):**
- [ ] Code merged to `feat/hermes-qa-factory` (then `main`) with PR review
- [ ] Unit or integration tests for new API routes (where applicable)
- [ ] `env.example` updated for new env vars
- [ ] RBAC enforced server-side (not UI-only)
- [ ] No secrets in logs or committed files
- [ ] Story acceptance criteria verified in demo

**Hermes stories (`[HERMES]`, `[BRIDGE]`):**
- [ ] SOUL.md + `config.yaml` committed under `docs/hermes-profiles/<profile>/`
- [ ] Same files deployed to Node 1 `~/.hermes/profiles/<profile>/`
- [ ] `hermes doctor` / profile smoke test passes on Node 1
- [ ] MCP connectivity to AWT `:8001` verified (`health_check` tool)
- [ ] Delegate smoke test documented in sprint demo notes

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

## 4.1 Hermes Node 1 mandatory track (do not skip)

Hermes profiles are **required for production launch**, not a side quest. Version-control templates in this repo, then deploy to Node 1 each sprint.

### Profile delivery matrix

| Profile | Replaces | Sprint (draft in repo) | Sprint (deploy + smoke) | Loop / role |
|---------|----------|------------------------|-------------------------|-------------|
| **qa-orchestrator** | qa-manager | **HF-2** | HF-3 | Routes all jobs; single chat entry |
| **qa-journey-planner** | qa-requirements | HF-3 | HF-3 | Loop A — coverage + backlog |
| **qa-test-gen** | qa-test-gen (v4) | HF-3 | HF-3 | `crawl_and_save_test` batch |
| **qa-dispatcher** | qa-dispatcher (v4) | HF-3 | HF-3 | `execute_test` |
| **qa-reporter** | qa-reporter (v4) | HF-3 | HF-6 | Digests → webapp |
| **qa-change-detector** | new | HF-4 | HF-4 | Loop C — snapshots |
| **qa-healer** | new | HF-5 | HF-5 | Loop D — self-heal |

### Repo layout (version control)

```
docs/hermes-profiles/
  README.md
  qa-orchestrator/SOUL.md, config.yaml   # HF-2.6 ✅
  _shared/mcp_servers.yaml.example     # HF-2.7 ✅
  qa-journey-planner/SOUL.md, config.yaml
  qa-change-detector/SOUL.md, config.yaml
  qa-test-gen/SOUL.md, config.yaml
  qa-healer/SOUL.md, config.yaml
  qa-dispatcher/SOUL.md, config.yaml
  qa-reporter/SOUL.md, config.yaml
  bridge/README.md              # HF-6: Bridge install + event POST script
  Hermes_Environment_Migration_Guide.md   # HF-7: dev mini PC → prod PC
```

**Migration scripts (HF-7):** `scripts/hermes-migrate/` — `pack-profiles.sh`, `deploy-profiles.sh`, `smoke-check.sh`, env templates.

**Source templates:** [Hermes_QA_MultiAgent_Profiles_v4.md](Hermes_QA_MultiAgent_Profiles_v4.md) — adapt for v5 (no Telegram dependency in orchestrator).

### 4.3 Hermes environment migration (dev mini PC → prod PC)

**Approved approach:** Develop and smoke-test on a **small Ubuntu mini PC**. When sign-off checklist passes, **package profiles** (not the whole OS) and deploy to a **higher-spec production Ubuntu PC**, changing **environment variables only** (AWT URLs, rotated secrets, `HERMES_BRIDGE_URL` on AWT).

| Phase | Host | Work |
|-------|------|------|
| **Dev** | Ubuntu mini PC | Install Hermes, tune SOUL/config, smoke tests |
| **Package** | Dev or CI | `scripts/hermes-migrate/pack-profiles.sh` or git `docs/hermes-profiles/` |
| **Prod** | Ubuntu prod PC | `deploy-profiles.sh` + prod `~/.hermes/.env` + security sign-off |

**Does not migrate:** agent `memories/`, dev secrets, logs. **AWT** (API/MCP/DB) stays on its own host — update URLs only.

**Full guide:** [hermes-profiles/Hermes_Environment_Migration_Guide.md](hermes-profiles/Hermes_Environment_Migration_Guide.md)

### Master checklist (tick before HF-6 launch)

- [x] HF-2.6 — `qa-orchestrator` SOUL.md drafted in repo
- [ ] HF-3.1 — orchestrator, planner, test-gen deployed on Node 1
- [ ] HF-3.6 — dispatcher, reporter deployed on Node 1
- [ ] HF-4.5 — change-detector deployed on Node 1
- [ ] HF-5.3 — healer deployed on Node 1
- [x] HF-6.2 — AWT ingests `POST /api/v1/agent/hermes/events`
- [x] HF-6.6 — Hermes Bridge `serve` + posts events to AWT (demo or orchestrator CLI)
- [x] HF-3.7 — Chat path: AWT `agent/chat` → Bridge when `HERMES_BRIDGE_URL` set
- [ ] HF-6.7 — `qa-reporter` Hermes → webapp (worker hook covers AWT path today)
- [ ] HF-7.5 — Dev Ubuntu smoke sign-off → package → prod Ubuntu deploy (§4.3)
- [ ] All profiles: MCP `AWT_MCP_SECRET` + `AWT_BASE_URL` in `config.yaml`

---

## 4.2 AWT-first sequencing (recommended for solo / focused dev)

**Yes — you can finish the entire AWT track before touching Node 1.** The plan’s sprint numbers stay the same; only **execution order** changes.

### Why this works

| Path | Without Hermes | With Hermes (launch) |
|------|----------------|----------------------|
| **Cron / factory_worker** | ✅ Calls MCP tools directly (`drain_backlog`, `run_regression`, heal, snapshots) | Same — worker stays deterministic |
| **Agent Chat → job** | ✅ HF-1 keyword mapper → `factory_worker` (no LLM orchestration) | Bridge → `qa-orchestrator` delegates |
| **Job Monitor timeline** | ✅ Worker events only | + delegate / LLM events from Bridge |
| **Agent Observatory** | ✅ UI + APIs with stub/empty trace | Full Hermes session payloads |
| **Production launch** | ❌ Not complete | ✅ Required |

v5’s **hybrid execution** model means Loops A–D do **not** block on Hermes profiles during development — only **chat-driven multi-agent delegation** and **launch demo** do.

### Phase A — AWT only (do this first)

Complete every `[AWT-BE]`, `[AWT-FE]`, and `[MCP]` story in order:

| Order | Stories | Outcome |
|-------|---------|---------|
| 1 | HF-1 ✅ | Control plane + Agent Console |
| 2 | HF-2.1 – HF-2.5 ✅ | MCP tools, registry, backlog APIs + UI |
| 3 | HF-3.2 – HF-3.5 ✅ | `drain_backlog` / `generate_journey` / `full_cycle` worker + Loops A & B cron |
| 4 | HF-4.1 – HF-4.4, HF-4.6 ✅ | Snapshots, diff, Loop C |
| 5 | HF-5.1, HF-5.3a, HF-5.4, HF-5.5 ✅ | Heal API, Heal Review, Loop D |
| 6 | HF-6.1, HF-6.3, HF-6.4, HF-6.5 ✅ | Notifications, Observatory APIs + UI, ops runbook |

**Phase A:** ✅ **Complete** (2026-06-08).

**Defer until Phase B (remaining):** HF-2.6, HF-2.7, HF-3.1a–d, HF-3.6a–c, HF-4.5 (Hermes), HF-5.3b, HF-6.7.
**Phase B Bridge (done):** HF-6.2, HF-6.6, HF-3.7.

**Phase A demo:** Trigger jobs from Agent Chat (keyword rules) or cron; verify Job Monitor, registry, backlog, heal queue, Observatory (empty trace OK).

### Phase B — Hermes + Bridge (after Phase A)

| Order | Stories | Outcome |
|-------|---------|---------|
| 1 | HF-2.6, HF-2.7 | `qa-orchestrator` SOUL draft + MCP template in repo |
| 2 | HF-3.1a–d, HF-3.6a–c | Deploy all 5 core profiles; CLI `full_cycle` smoke |
| 3 | HF-3.7 | Chat → Bridge stub |
| 4 | HF-4.5 (Hermes) | `qa-change-detector` deploy |
| 5 | HF-5.3b | `qa-healer` deploy |
| 6 | HF-6.2, HF-6.6, HF-6.7 | Bridge production + reporter → webapp |

**Launch gate:** §4.1 master checklist — all boxes ticked.

### What you give up during Phase A

- No `delegate_task` / multi-agent reasoning from chat
- No real Hermes traces in Observatory (stub/empty is fine)
- HF-6.5 E2E “chat → orchestrator → delegate” waits until Phase B

---

## 5. Sprint HF-1 — Control plane & access (2 weeks)

**Sprint goal:** Submit a factory job from webapp; see live status via SSE; cron can enqueue `run_regression`.

**Status:** ✅ **Done** (commit `e33a6b3`). Gaps: HF-1.3 superadmin bootstrap, HF-1.6 SSE in UI — see §0.

**Total:** 21 points

### Stories

#### HF-1.1 — Database models & migrations (5 pts) `[AWT-BE]` ✅

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

#### HF-1.2 — Agent jobs REST API (5 pts) `[AWT-BE]` ✅

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

#### HF-1.3 — RBAC roles (3 pts) `[AWT-BE]` ⚠️

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

#### HF-1.4 — Factory worker (5 pts) `[AWT-BE]` ✅

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

#### HF-1.5 — Agent chat endpoint (3 pts) `[AWT-BE]` ✅

**As** an `agent_operator`, **I want** a chat endpoint **so that** natural language maps to structured jobs.

**Tasks:**
- `POST /api/v1/agent/chat` in `agent/chat.py`
- HF-1: rule-based or LLM mapper → `job_type` + `params` (start with keyword rules: "regression" → `run_regression`)
- Returns `{ job_id, reply }`

**Acceptance criteria:**
- Message "run regression" creates `run_regression` job
- Invalid intent returns 400 with helpful reply

---

#### HF-1.6 — Agent Console shell (3 pts) `[AWT-FE]` ⚠️

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

#### HF-1.7 — Factory scheduler + Telegram flag (2 pts) `[AWT-BE]` `[OPS]` ✅

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

**Status:** ✅ **Phase A done** (HF-2.1–2.5, commit `503244e`). ✅ HF-2.6–2.7 in repo. HF-3.1 deploy next.

**Total:** 22 points (AWT) + 5 (Hermes deferred)

### Stories

#### HF-2.1 — MCP execution & schedule tools (5 pts) `[MCP]` ✅

- `get_execution_feedback` → `GET /api/v1/executions/{id}/feedback`
- `list_failed_executions` → extend executions list with `result=fail&since=`
- `create_test_schedule`, `list_test_schedules`, `delete_test_schedule` → schedules API wrappers
- Tests in `backend/tests/unit/test_mcp_factory_tools.py`

**Acceptance criteria:** Hermes profile can call each tool via `mcp_server.py` stdio/HTTP and get valid JSON.

---

#### HF-2.2 — MCP ReqIQ proxy tools (3 pts) `[MCP]` ✅

- `get_coverage_matrix`, `get_reqiq_readiness`, `suggest_scenarios_from_wiki`
- Thin wrappers around existing `requirements.py` proxy logic (shared internal function)

**Acceptance criteria:** Tools work with Three-HK `reqiq_project_id` from v5 registry example.

---

#### HF-2.3 — Journey registry API (5 pts) `[AWT-BE]` ✅

- Model: `JourneyRegistryEntry` (id, name, feature_url, tags, capability_keys, reference_test_id, requires_login, project)
- `GET/POST/PATCH/DELETE /api/v1/agent/registry` — `admin`+ only
- Seed: `config/uat-journey-registry.yaml` (from v5 §4.3)

**Acceptance criteria:** Admin can CRUD journeys; seed loads on migration.

---

#### HF-2.4 — Journey backlog API (5 pts) `[AWT-BE]` ✅

- Model: `JourneyBacklogItem` (status: pending | in_progress | done | failed)
- `GET /api/v1/agent/backlog`, `POST /api/v1/agent/backlog` (enqueue)
- MCP: `list_journey_backlog`, `enqueue_journey`

**Acceptance criteria:** Enqueued item appears in backlog; status transitions on worker update.

---

#### HF-2.5 — Registry & backlog UI (4 pts) `[AWT-FE]` ✅

- `JourneyRegistryPage.tsx`, `BacklogQueuePage.tsx`
- Admin-only registry; backlog visible to `agent_operator`+

**Acceptance criteria:** UI CRUD matches API; backlog shows pending items.

---

#### HF-2.6 — Draft `qa-orchestrator` in repo (3 pts) `[HERMES]` **mandatory** ✅

**As** a platform owner, **I want** `qa-orchestrator` SOUL.md version-controlled **so that** Node 1 work is not lost and HF-3 deploy is ready.

**Tasks:**
- Create `docs/hermes-profiles/README.md` (profile index + deploy instructions)
- Create `docs/hermes-profiles/qa-orchestrator/SOUL.md` from v4 `qa-manager` SOUL.md:
  - Remove Telegram-only assumptions; route via `delegate_task`
  - Document job types: `drain_backlog`, `run_regression`, `full_cycle`, `heal_failures`, `scan_changes`
  - Reference AWT Agent Console as production human entry (not Telegram)
- Create `docs/hermes-profiles/qa-orchestrator/config.yaml` stub (model, MCP server URL, `AWT_MCP_SECRET` via env)

**Acceptance criteria:**
- SOUL.md committed in repo; peer-reviewed against v5 §4 and v4 profile doc
- `config.yaml` documents required env vars (no secrets in git)

---

#### HF-2.7 — Shared Hermes MCP config template (2 pts) `[HERMES]` `[OPS]` ✅

**Tasks:**
- Add `docs/hermes-profiles/_shared/mcp_servers.yaml.example` (MCP :8001, Bearer auth)
- Document Node 1 deploy: `rsync` or manual copy `docs/hermes-profiles/*` → `~/.hermes/profiles/`
- Verify `health_check` MCP tool from Node 1 against AWT

**Acceptance criteria:** README steps reproduce MCP connectivity on Node 1.

**HF-2 revised total:** 27 points (AWT 22 + Hermes 5)

---

## 7. Sprint HF-3 — Planner & batch generation (2 weeks)

**Sprint goal:** Loop A drains backlog — planner finds gaps, test-gen creates tests, schedules regression.

**Status:** ✅ **Phase A done** (HF-3.2–3.5, commit `503244e`). ⏸ HF-3.1, 3.6, 3.7 deferred to Phase B.

**Total:** 32 points (AWT 19 + Hermes 13)

### Stories

#### HF-3.1a — `qa-orchestrator` finalize + deploy (3 pts) `[HERMES]` ⏸

- Finalize SOUL.md from HF-2.6; add `delegate_task` decision tree (v5 §7, v4 trigger tree)
- Deploy to Node 1; `qa-orchestrator doctor` passes
- **Acceptance:** `qa-orchestrator chat -q "run regression"` returns structured plan or delegates

#### HF-3.1b — `qa-journey-planner` SOUL + deploy (3 pts) `[HERMES]` ⏸

- SOUL.md: `get_coverage_matrix`, `get_reqiq_readiness`, `suggest_scenarios_from_wiki`, `enqueue_journey`
- Repo + Node 1 deploy
- **Acceptance:** Delegated task returns backlog item for a coverage gap

#### HF-3.1c — `qa-test-gen` SOUL + deploy (3 pts) `[HERMES]` ⏸

- SOUL.md: batch `crawl_and_save_test`, `reference_test_id`, poll workflow
- Repo + Node 1 deploy
- **Acceptance:** Delegated task returns `{ test_case_id, status: success }`

#### HF-3.1d — Orchestrator integration smoke (4 pts) `[HERMES]` ⏸

- Manual CLI end-to-end: orchestrator → planner → test-gen
- **Acceptance:** `qa-orchestrator chat -q "drain backlog for Three-HK"` returns `test_case_id`

---

#### HF-3.2 — Factory worker: `drain_backlog` + `generate_journey` (5 pts) `[AWT-BE]` ✅

- Worker job types: `drain_backlog`, `generate_journey`, `full_cycle` (orchestrates sub-steps)
- HF-3: cron path uses **factory_worker + MCP** (deterministic); chat path can invoke Hermes Bridge (stub OK if worker-only for demo)

**Acceptance criteria:** `drain_backlog` processes up to N pending backlog items; events logged per item.

---

#### HF-3.3 — Loop A scheduler (3 pts) `[AWT-BE]` ✅

- Cron every 6h: `{ type: drain_backlog, max_items: 3 }`
- Configurable via env: `FACTORY_LOOP_A_CRON`

**Acceptance criteria:** Backlog item auto-processed without human trigger.

---

#### HF-3.4 — Auto-schedule on successful generation (3 pts) `[AWT-BE]` ✅

- After successful `crawl_and_save_test`: `create_test_schedule` cron `0 2 * * *` with regression tag

**Acceptance criteria:** New test appears in Schedules UI with nightly cron.

---

#### HF-3.5 — Loop B regression scheduler (2 pts) `[AWT-BE]` ✅

- Cron every 2h: `run_regression` with `tags: [regression]`
- Nightly full run: `0 2 * * *`

**Acceptance criteria:** Regression runs without human; Job Monitor shows recurring jobs.

---

#### HF-3.6a — `qa-dispatcher` SOUL + deploy (2 pts) `[HERMES]` ⏸

- SOUL.md: `list_test_cases`, `execute_test`, `get_execution_status`, aggregate results
- Repo + Node 1 deploy

#### HF-3.6b — `qa-reporter` SOUL draft + deploy (2 pts) `[HERMES]` ⏸

- SOUL.md: plain-language summary (HF-3: log/CLI output; HF-6: webapp notifications)
- Repo + Node 1 deploy

#### HF-3.6c — `full_cycle` Hermes smoke (2 pts) `[HERMES]` ⏸

- **Acceptance:** Manual `full_cycle`: plan → gen → execute → reporter summary (Telegram disabled)

#### HF-3.7 — Wire chat → Hermes Bridge stub (3 pts) `[BRIDGE]` `[AWT-BE]` ✅

- AWT `POST /api/v1/agent/chat` forwards to Bridge when `HERMES_BRIDGE_URL` set (`factory_bridge_client`)
- Otherwise falls back to `factory_worker`
- Bridge invokes `qa-orchestrator job run --json` or demo delegate simulation

---

### HF-3 demo script

1. Enqueue DIY dashboard journey in backlog
2. Trigger `drain_backlog` (chat or wait for cron)
3. New test case + schedule created; smoke execution logged

---

## 8. Sprint HF-4 — Change detection (2 weeks)

**Sprint goal:** Loop C detects UAT URL changes and enqueues regeneration.

**Status:** ✅ **Phase A done** (HF-4.1–4.4 + registry UI, commit `ff6af29`). ⏸ HF-4.5 Hermes deferred.

**Total:** 20 points

### Stories

#### HF-4.1 — Observe snapshot API (5 pts) `[AWT-BE]` ✅

- `POST /api/v2/observe-snapshot` — wraps `ObservationAgent` for URL-only capture
- Store: `url_snapshots` table (url_hash, html_summary, element_fingerprint, captured_at)

**Acceptance criteria:** Snapshot stored; retrievable by url_hash.

---

#### HF-4.2 — Snapshot diff API (5 pts) `[AWT-BE]` ✅

- `GET /api/v2/snapshots/{url_hash}`
- `POST /api/v2/snapshots/diff` — returns `material_change: bool` + summary text

**Acceptance criteria:** Diff detects meaningful DOM change between two captures; ignores timestamp noise.

---

#### HF-4.3 — MCP snapshot tools (3 pts) `[MCP]` ✅

- `observe_url_snapshot`, `get_url_snapshot`, `diff_url_snapshots`

---

#### HF-4.4 — Loop C worker + cron (3 pts) `[AWT-BE]` ✅

- Cron every 4h: `{ type: scan_changes }`
- On material change: enqueue backlog with `reference_test_id` + diff summary

**Acceptance criteria:** Simulated DOM change enqueues regeneration job.

---

#### HF-4.5 — `qa-change-detector` SOUL + deploy (4 pts) `[HERMES]` **mandatory** ⏸

- `docs/hermes-profiles/qa-change-detector/SOUL.md`: `observe_url_snapshot`, `diff_url_snapshots`, `enqueue_journey`
- Deploy Node 1; orchestrator delegates for `scan_changes` jobs
- **Acceptance:** Manual delegate returns `material_change: true` on known diff fixture

---

#### HF-4.6 — Change detection UI badge (2 pts) `[AWT-FE]` ✅

- Journey Registry shows last snapshot time + change flag *(was HF-4.5 UI in early drafts)*

---

## 9. Sprint HF-5 — Self-healing (2 weeks)

**Sprint goal:** Loop D heals failures; double-fail escalates to Heal Review.

**Status:** ✅ **Phase A done** — HF-5.1–5.5 implemented. ⏸ HF-5.3b Hermes deferred.

**Total:** 22 points

### Stories

#### HF-5.1 — Heal from feedback API (5 pts) `[AWT-BE]` ✅

- `POST /api/v2/heal-from-feedback` — input: `execution_id`
- Logic: load feedback → if flow break, `crawl_and_save` with `reference_test_id`; if xpath, clear cache first
- Reuse `improve_tests` / `evolution_agent` where appropriate

**Acceptance criteria:** Failed execution → heal → new or updated test case ID returned.

---

#### HF-5.2 — MCP heal tools (3 pts) `[MCP]` ✅

- `heal_test_from_feedback`, `clear_xpath_cache` (wrap settings DELETE routes)

---

#### HF-5.3a — Loop D worker + cron (3 pts) `[AWT-BE]` ✅

- Cron every 1h: `{ type: heal_failures, since: last_run }`
- Wire `learn_from_feedback` after successful heal

#### HF-5.3b — `qa-healer` SOUL + deploy (4 pts) `[HERMES]` **mandatory** ⏸

- `docs/hermes-profiles/qa-healer/SOUL.md` per v5 §12.6
- MCP: `get_execution_feedback`, `heal_test_from_feedback`, `clear_xpath_cache`
- Deploy Node 1; orchestrator delegates for `heal_failures` jobs
- **Acceptance:** Recent failure auto-healed or escalated after 2 attempts (manual + cron)

---

#### HF-5.4 — Heal Review queue (5 pts) `[AWT-BE]` `[AWT-FE]` ✅

- Model: `HealReviewItem` (execution_id, test_case_id, reason, status: open | resolved)
- API: `GET/PATCH /api/v1/agent/heal-review`
- UI: `HealReviewPage.tsx` for `agent_operator`+

**Acceptance criteria:** Double-fail appears in queue; operator can mark resolved.

---

#### HF-5.5 — Heal integration tests (4 pts) `[AWT-BE]` ✅

- Test: feedback → heal API → execute passes (mock browser tier acceptable)

---

## 10. Sprint HF-6 — Reporting, Observatory & launch (2 weeks)

**Sprint goal:** Production-ready: in-app reports, superadmin Observatory, Telegram off, ops runbook.

**Status:** ✅ Phase A done · ✅ 6.2 ingest · ✅ 6.6 bridge service · ✅ 3.7 chat→bridge · ⬜ 6.7 reporter Hermes.

**Total:** 23 points

### Stories

#### HF-6.1 — In-app notifications (5 pts) `[AWT-BE]` `[AWT-FE]` ✅

- `notifications` table + bell icon in header
- `qa-reporter` posts digest on job complete (worker hook)
- Optional email via existing email infra (stretch)

**Acceptance criteria:** User sees notification when `full_cycle` completes.

---

#### HF-6.2 — Hermes Bridge event ingestion (5 pts) `[BRIDGE]` `[AWT-BE]` ✅

- Node 1: Bridge posts to `POST /api/v1/agent/hermes/events` (`HERMES_BRIDGE_SECRET`)
- AWT: ingest service with secret redaction
- Extend `FactoryJobEvent` with `payload_full`, `llm_turns`, `hermes_session_id`

**Acceptance criteria:** Delegate events from Hermes appear in job timeline within 5s.

---

#### HF-6.3 — Superadmin Observatory APIs (5 pts) `[AWT-BE]` ✅

- `GET /api/v1/agent/jobs/{id}/hermes-trace` — superadmin only
- `GET /api/v1/agent/hermes/sessions/{sess_id}`
- `observatory_access_log` table

**Acceptance criteria:** `admin` gets 403; `superadmin` sees full payloads; access logged.

---

#### HF-6.4 — Agent Observatory UI (5 pts) `[AWT-FE]` ✅

- Job detail: Observatory tab (superadmin only; tab hidden for others)
- Expandable delegate payloads, LLM turns, session link

**Acceptance criteria:** Matches v5 §8.3 layout; 403 if role tampered client-side.

---

#### HF-6.5 — Launch hardening (3 pts) `[AWT-BE]` `[OPS]` ✅

- Integration test: end-to-end `full_cycle` from chat API
- Integration test: Observatory 403 for non-superadmin
- `docs/Hermes_QA_Factory_Ops_Runbook.md` (new)
- Prod checklist: `HERMES_TELEGRAM_ENABLED=false`, secrets rotated

---

#### HF-6.6 — Hermes Bridge service on Node 1 (5 pts) `[BRIDGE]` **mandatory** ✅

- `docs/hermes-profiles/bridge/hermes_bridge.py serve`: `POST /run`, demo delegates or orchestrator CLI
- Env: `HERMES_BRIDGE_SECRET`, `AWT_AGENT_EVENTS_URL`, `HERMES_BRIDGE_DEMO_MODE`
- systemd unit `hermes-factory-bridge.service`
- **Acceptance:** `full_cycle` from Agent Chat (with `HERMES_BRIDGE_URL`) shows delegate events in timeline

---

#### HF-6.7 — `qa-reporter` production wiring (2 pts) `[HERMES]` `[AWT-BE]`

- Reporter SOUL updated to call AWT notification API (or worker hook) instead of Telegram
- **Acceptance:** Job complete → in-app notification bell

**HF-6 revised total:** 30 points

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

### HF-7 — Hermes environment migration (dev → prod)

| ID | Story | Points | Status |
|----|-------|--------|--------|
| HF-7.1 | Migration guide + `hermes.env.*.example` templates | 2 | ✅ |
| HF-7.2 | `pack-profiles.sh` — tarball from `~/.hermes/profiles` | 2 | 🔜 stub |
| HF-7.3 | `deploy-profiles.sh` — `--from-tar` / `--from-git` | 2 | 🔜 stub |
| HF-7.4 | `smoke-check.sh` — MCP + Bridge health | 1 | 🔜 stub |
| HF-7.5 | Prod cutover checklist + security sign-off | 2 | ⬜ |

**Guide:** [hermes-profiles/Hermes_Environment_Migration_Guide.md](hermes-profiles/Hermes_Environment_Migration_Guide.md) · **Scripts:** `scripts/hermes-migrate/`

---

## 12. Environment variables checklist

| Variable | Sprint | Purpose |
|----------|--------|---------|
| `HERMES_TELEGRAM_ENABLED` | HF-1 | `false` in prod |
| `HERMES_BRIDGE_SECRET` | HF-6 | Bridge ↔ AWT auth (rotate on prod) |
| `HERMES_BRIDGE_URL` | HF-3.7 / HF-6 | AWT → Bridge `POST /run` (change when moving Hermes host) |
| `AWT_MCP_URL` | HF-7 | Hermes `~/.hermes/.env` — MCP host (dev vs prod) |
| `AWT_AGENT_EVENTS_URL` | HF-7 | Bridge → AWT events endpoint |
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
| Hermes Node 1 not ready for HF-3 | **Not a blocker** if using AWT-first (§4.2): worker + MCP runs Loops A–D. Hermes required only for Phase B / launch. |
| OneDrive file locks on docs | Close files before agent edits |
| ReqIQ downtime blocks planner | Worker marks job `failed` with clear event; retry cron |
| LLM cost on chat mapper | HF-1 keyword rules; optional LLM in HF-3 |
| Secret leakage in Observatory | Redact at ingest; never stream raw env to browser |

---

## 15. Sprint calendar (suggested)

| Sprint | Weeks | Dates (example) | Goal | Status |
|--------|-------|-----------------|------|--------|
| HF-1 | 1–2 | Jun 16 – Jun 27, 2026 | Control plane + Agent Console shell | ✅ |
| HF-2 | 3–4 | Jun 30 – Jul 11, 2026 | MCP + registry (+ orchestrator draft Phase B) | ✅ AWT |
| HF-3 | 5–6 | Jul 14 – Jul 25, 2026 | Loop A/B (+ Hermes profiles Phase B) | ✅ AWT |
| HF-4 | 7–8 | Jul 28 – Aug 8, 2026 | Loop C change detection | ✅ AWT |
| HF-5 | 9–10 | Aug 11 – Aug 22, 2026 | Loop D self-healing | 🔜 |
| HF-6 | 11–12 | Aug 25 – Sep 5, 2026 | Observatory + production launch | ⬜ |

Adjust dates to your team start; maintain 2-week cadence.

---

## 16. How to use this plan day-to-day

1. **Progress:** Update **§0 Progress tracker** when a story lands on `feat/hermes-qa-factory` (commit hash + status emoji).
2. **Sprint planning:** Copy HF-* stories into your board (Jira/GitHub Projects/Tasks.json) as To Do.
3. **Each story:** Create branch `feat/HF-1.2-agent-jobs-api`; link PR to story ID.
4. **Status tags:** `Done` | `In Progress` | `To Do` | `Backlog` (per team convention).
5. **Design reference:** When acceptance criteria are unclear, read [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md) section cited in story.
6. **Demo:** Use sprint demo script at end of each sprint section.
7. **After HF-6:** Move §11 backlog items into HF-7+ planning.

---

## 17. Related documents

| Document | Use |
|----------|-----|
| [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md) | Architecture, APIs, loops, Observatory |
| [Hermes_QA_Factory_Ops_Runbook.md](Hermes_QA_Factory_Ops_Runbook.md) | Production checklist, loops, troubleshooting (HF-6) |
| [Hermes_QA_MultiAgent_Profiles_v4.md](Hermes_QA_MultiAgent_Profiles_v4.md) | SOUL.md source templates for Hermes profiles |
| [hermes-profiles/README.md](hermes-profiles/README.md) | Version-controlled profile folder + deploy steps |
| [hermes-profiles/Hermes_Environment_Migration_Guide.md](hermes-profiles/Hermes_Environment_Migration_Guide.md) | Dev mini PC → prod PC migration (HF-7) |
| [scripts/hermes-migrate/README.md](../scripts/hermes-migrate/README.md) | Pack / deploy / smoke scripts |
| [ReqIQ-API-Integration-Guide.md](ReqIQ-API-Integration-Guide.md) | MCP / proxy behaviour |
| [AI-Web-Test-Developer-Handoff.md](AI-Web-Test-Developer-Handoff.md) | ReqIQ proxy, platform context |
| `Phase3-project-documents/Phase3-Project-Management-Plan-Complete.md` | Platform sprints (Sprint 10.x) — separate from HF program |

---

## 18. Sprint-by-sprint: what not to miss

### Default (parallel tracks)

| Sprint | AWT (this repo) | Hermes Node 1 (mandatory at launch) |
|--------|-----------------|-------------------------------------|
| **HF-1** ✅ | Jobs API, worker, Agent Console | — |
| **HF-2** ✅ | MCP tools, registry, backlog UI | ✅ **HF-2.6–2.7** orchestrator SOUL + MCP template · HF-3.1 deploy |
| **HF-3** ✅ | Loop A/B, `drain_backlog` worker | ⬜ Deploy orchestrator, planner, test-gen, dispatcher, reporter · Bridge stub |
| **HF-4** ✅ | Snapshot/diff APIs, Loop C, registry badges | ⬜ Deploy **qa-change-detector** |
| **HF-5** ✅ | Heal API, Heal Review UI, Loop D | ⬜ Deploy **qa-healer** |
| **HF-6** 🔜 | Observatory, notifications, Bridge ingest+service | ⬜ **qa-reporter** Hermes · profile deploy |

### AWT-first (§4.2) — your preferred order

| Phase | Do now | Defer to Phase B |
|-------|--------|------------------|
| **A** | HF-1 ✅ → HF-6 AWT ✅ **(complete)** | — |
| **B** | HF-6.2, 6.6, 3.7 ✅ | HF-2.6–2.7 → HF-3.1a–d, 3.6a–c → HF-4.5 → HF-5.3b → HF-6.7 |

---

*This plan implements v5 §9 sprints A–F as executable agile stories. Hermes Node 1 work is **EPIC-HF-07** and is required for **launch** — see §4.1. Use **§4.2 AWT-first** to finish this-repo development before Node 1. **Keep §0 Progress tracker current** after each merge to `feat/hermes-qa-factory`.*
