# HF-3.1d — Orchestrator integration smoke

**Sprint:** HF-3 · **Story:** HF-3.1d  
**Acceptance:** `qa-orchestrator chat -q "drain backlog for Three-HK"` returns a **`test_case_id`** (real crawl, not demo).

**Chain:** `qa-orchestrator` → `qa-journey-planner` → `qa-test-gen` → structured JSON with `test_case_ids`.

---

## Prerequisites

| Layer | Requirement |
|-------|-------------|
| **AWT (Windows/dev server)** | `python start_server.py` running; MCP on `:8001`; `AWT_MCP_SECRET` + `AWT_SERVICE_USERNAME`/`PASSWORD` set |
| **Hermes (Ubuntu)** | Profiles deployed: `qa-orchestrator`, `qa-journey-planner`, `qa-test-gen` |
| **Network** | Ubuntu can reach AWT LAN IP on ports **8000** (API) and **8001** (MCP) |
| **ReqIQ** | `REQIQ_PROJECT_ID` in `~/.hermes/.env`; readiness ≥ 60 for target journey |
| **Backlog** | At least one **pending** backlog item for `Three-HK` (or planner enqueues one) |
| **Credentials** | `TEST_LOGIN_*`, `HTTP_AUTH_*` in `~/.hermes/.env` for crawl |
| **LLM** | `OPENROUTER_API_KEY` (or local model) configured per profile |

### AWT-side prereq check (Windows)

From repo root (PowerShell):

```powershell
.\scripts\hermes-migrate\smoke-awt-prereq-3.1d.ps1
```

### Hermes deploy (Ubuntu)

```bash
cd scripts/hermes-migrate
cp hermes.env.dev.example ~/.hermes/.env   # edit hosts + secrets
./deploy-profiles.sh --from-git /path/to/AI-Web-Test-v1-2

hermes profile create "qa-orchestrator"
hermes profile create "qa-journey-planner"
hermes profile create "qa-test-gen"

# Copy SOUL + config (deploy script rsyncs to ~/.hermes/profiles/)
qa-orchestrator model
qa-journey-planner model
qa-test-gen model
```

---

## Phase 1 — Connectivity (5 min)

```bash
source ~/.hermes/.env
./scripts/hermes-migrate/smoke-check.sh --env dev
```

Then MCP tool via orchestrator:

```bash
qa-orchestrator chat -q 'Call health_check on ai-web-test MCP. Reply with JSON only.'
```

Expected: `status` healthy / API reachable.

---

## Phase 2 — Planner-only dry run (5–10 min)

Validates delegate to **qa-journey-planner** without starting a crawl:

```bash
qa-orchestrator chat -q 'delegate to qa-journey-planner: task_type drain_backlog project Three-HK max_items 1. Return JSON only.'
```

**Pass:** JSON contains `items_for_test_gen` or `items_enqueued` with `status` success/partial.

**Fail:** `insufficient` readiness — fix ReqIQ or enqueue manually in Agent Console → Journey Backlog.

### Seed backlog (if empty)

Agent Console (superadmin) → Journey Registry → pick journey → **Enqueue**,  
or MCP `enqueue_journey` from orchestrator chat.

---

## Phase 3 — Full integration (15–45 min)

**This is the HF-3.1d acceptance run.**

```bash
source ~/.hermes/.env
export HERMES_BRIDGE_DEMO_MODE=0   # ensure real orchestrator, not bridge demo

qa-orchestrator chat -q 'drain backlog for Three-HK max_items 1'
```

Or structured job JSON (Bridge / automation path):

```bash
qa-orchestrator job run --json '{"job_type":"drain_backlog","project":"Three-HK","params":{"max_items":1}}'
```

**Pass criteria:**

1. Orchestrator delegates to **qa-journey-planner**, then **qa-test-gen**.
2. Final output JSON includes **`test_case_id`** (integer) or top-level **`test_case_ids`** array.
3. AWT Job Monitor / backlog shows item moved to **done** (factory worker path) or test visible in Tests UI.

Automated checker (Ubuntu):

```bash
./scripts/hermes-migrate/smoke-integration-3.1d.sh
# Planner only (no crawl):
./scripts/hermes-migrate/smoke-integration-3.1d.sh --planner-only
```

---

## Phase 4 — Bridge path (optional)

When Hermes profiles are stable, disable demo mode and wire real orchestrator:

**Ubuntu `~/.hermes/.env`:**

```env
HERMES_BRIDGE_DEMO_MODE=0
HERMES_ORCHESTRATOR_CMD=qa-orchestrator
```

**AWT `backend/.env`:**

```env
HERMES_BRIDGE_URL=http://<ubuntu-ip>:8790
HERMES_BRIDGE_SECRET=<shared>
```

```bash
python docs/hermes-profiles/bridge/hermes_bridge.py serve --port 8790
```

Agent Console (superadmin) → chat: **drain backlog for Three-HK**  
→ AWT forwards to Bridge → orchestrator CLI → same delegate chain.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| MCP 401 | Secret mismatch | Align `AWT_MCP_SECRET` on AWT + Ubuntu |
| Planner `insufficient` | Low ReqIQ readiness | Run readiness in ReqIQ UI; update wiki |
| No `test_case_id` | Crawl failed / timeout | Check workflow in Job Monitor; UAT creds |
| Orchestrator loops | Missing delegate profile | Deploy planner + test-gen SOUL/config |
| 15 min timeout | Slow UAT | Increase `tool_timeout_seconds` in test-gen `config.yaml` |
| Bridge shows demo only | `HERMES_BRIDGE_DEMO_MODE=1` | Set `0` + `HERMES_ORCHESTRATOR_CMD` |

---

## Demo mode (UI only — not HF-3.1d pass)

Bridge demo simulates delegate events **without** a real `test_case_id` from crawl.  
Useful for Agent Console timeline smoke before Ubuntu profiles are ready:

```bash
export HERMES_BRIDGE_DEMO_MODE=1
python docs/hermes-profiles/bridge/hermes_bridge.py serve
```

Demo `drain_backlog` events include a **placeholder** `test_case_id: 1291` in `payload_summary` —  
**does not** satisfy HF-3.1d acceptance (must be a real generated test).

---

## Related docs

- [qa-orchestrator/SOUL.md](qa-orchestrator/SOUL.md) — delegate tree
- [qa-journey-planner/SOUL.md](qa-journey-planner/SOUL.md) · [qa-test-gen/SOUL.md](qa-test-gen/SOUL.md)
- [MCP_CONNECTIVITY.md](_shared/MCP_CONNECTIVITY.md)
- [Hermes_Environment_Migration_Guide.md](Hermes_Environment_Migration_Guide.md)
