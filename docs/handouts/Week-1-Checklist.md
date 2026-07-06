# Week 1 Checklist — QA Factory Go-Live

**Goal:** Turn on background automation so Dev, UAT, and QA spend less time on repeat work.

**Branch:** `feat/hermes-qa-factory`  
**App URL (dev):** `http://localhost:5173` (frontend) · API `http://localhost:8000`

---

## Who does what

| Role | Week 1 responsibility |
|------|------------------------|
| **Ops / superadmin** | Enable scheduler, bridge, notifications |
| **QA + admin** | Journey registry, ReqIQ docs, review first auto-tests |
| **Developer** | Add registry row per new major URL; upload CR notes to ReqIQ |
| **UAT** | Learn `/executions` and `/heal-review`; stop manual repeat regression |

---

## Day 1–2 — Foundation (Ops + QA)

### ☐ 1. Pull latest code

```bash
git checkout feat/hermes-qa-factory
git pull origin feat/hermes-qa-factory
```

### ☐ 2. Run database migration (Windows backend)

```powershell
cd backend
python migrations/add_agent_conversations.py
```

Restart backend: `python start_server.py`

### ☐ 3. Enable factory scheduler

Edit `backend/.env`:

```env
FACTORY_SCHEDULER_ENABLED=true
FACTORY_SERVICE_USER_ID=1
FACTORY_AUTO_SCHEDULE_ENABLED=true
```

Use a valid user id for `FACTORY_SERVICE_USER_ID` (service account or superadmin).

Restart backend after saving.

### ☐ 4. Bootstrap factory users (if needed)

```powershell
cd backend
python scripts/bootstrap_factory_users.py
```

Roles: `agent_operator` (console), `admin` (registry edit), `superadmin` (settings, observatory).

### ☐ 5. Seed Journey Registry

**Screen:** Sidebar → **Journey Registry** → `/journey-registry`

For each core UAT flow, add:

| Field | Example |
|-------|---------|
| Slug | `diy-dashboard` |
| Project | `Three-HK` |
| Feature URL | UAT login URL |
| Tags | `regression`, `three-hk` |
| Login module | e.g. `login_my3_andrew` |

**Minimum:** 3–5 highest-traffic journeys before enabling loops.

### ☐ 6. Upload requirements to ReqIQ

**ReqIQ UI** (typically `:8080`) — upload BRD, wiki, acceptance criteria for those journeys.

Verify readiness (via API or planner later): score **≥ 60** = safe to auto-generate.

---

## Day 3–4 — First automation (QA)

### ☐ 7. Enqueue or wait for backlog

**Option A — Manual:** Sidebar → **Backlog** → `/backlog` → enqueue journey slug  

**Option B — Automatic:** Wait for Loop C (`scan_changes`) after registry baseline, or Agent Console:

**Screen:** **Agent Console** → `/agent-console`  
Message: `drain backlog` or `!drain backlog`

### ☐ 8. Watch factory build tests

**Screen:** **Backlog** → `/backlog` — status `pending` → `in_progress` → `done`

**Screen:** **Tests** → `/tests` — new cases appear (3–15 min per item)

### ☐ 9. Review and tag regression

Open each new test → confirm steps → add tag **`regression`**.

**Screen:** **Test Suites** → `/test-suites` — optional: group nightly suite

### ☐ 10. Confirm regression runs

**Screen:** **Executions** → `/executions` — runs every **2 hours** + **02:00 nightly**

Or trigger once: Agent Console → `run regression`

---

## Day 5 — Ubuntu bridge (optional but recommended)

### ☐ 11. Deploy Hermes bridge on factory node

Follow: [DEPLOY_CHECKLIST.md](../hermes-profiles/bridge/DEPLOY_CHECKLIST.md)

Or use migration bundle: `scripts/hermes-migrate/install-ubuntu-factory.sh`

### ☐ 12. Connect Windows app to bridge

**Screen:** **Settings** → `/settings` → section **QA Factory Connection** (superadmin)

Set orchestrator node URL, e.g. `http://192.168.x.x:8790`

Test health indicator → green.

### ☐ 13. Smoke test open chat

**Screen:** **Agent Console** → `/agent-console`  
Send: `Hi` — expect orchestrator summary reply (not “Job queued” only).

---

## Ongoing — Everyone

### Factory loops (once scheduler on)

| Loop | Schedule | What |
|------|----------|------|
| **C** | Every 4h | Scan URL changes → enqueue backlog |
| **A** | Every 6h | Build tests from backlog (max 3) |
| **B** | Every 2h + 02:00 | Run `regression` tag |
| **D** | Hourly | Heal recent failures |

### Screens by role

| Screen | Path | Primary user |
|--------|------|--------------|
| Agent Console | `/agent-console` | QA, UAT (operator+) |
| Journey Registry | `/journey-registry` | QA, admin |
| Backlog | `/backlog` | QA |
| Heal Review | `/heal-review` | UAT, QA, Dev |
| Executions | `/executions` | UAT, QA |
| Settings (QA Factory) | `/settings` | superadmin |
| Dashboard | `/dashboard` | Everyone — high-level stats |

### ☐ 14. Heal Review triage (weekly)

**Screen:** `/heal-review` — resolve or assign open items.

Only failures that **self-heal could not fix** (default: 2 attempts) appear here.

---

## Success criteria (end of Week 1)

- [ ] At least **3 journeys** in registry with `regression` tag  
- [ ] **Executions** show automated regression runs without manual trigger  
- [ ] **Backlog** has processed at least one item to `done`  
- [ ] Team handouts read: [Developer](Developer-Handout.md), [UAT](UAT-Handout.md), [QA](QA-Handout.md)  
- [ ] (Optional) Agent Console open chat works via bridge  

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No cron jobs | `FACTORY_SCHEDULER_ENABLED=true` + backend restarted |
| Open chat no reply | Bridge deployed? Settings → QA Factory URL? See DEPLOY_CHECKLIST |
| No tests generated | ReqIQ readiness &lt; 60? Backlog empty? Loop A enabled? |
| UAT still manual everything | Confirm `regression` tag on core tests; check `/executions` |

**Ops runbook:** [Hermes_QA_Factory_Ops_Runbook.md](../Hermes_QA_Factory_Ops_Runbook.md)
