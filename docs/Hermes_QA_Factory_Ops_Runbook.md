# Hermes QA Factory — Operations Runbook

**Version:** 1.1 · **Date:** 2026-06-08  
**Branch:** `feat/hermes-qa-factory`  
**Related:** [Hermes_QA_Factory_Agile_Development_Plan.md](Hermes_QA_Factory_Agile_Development_Plan.md) · [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md)

---

## 1. Factory login accounts (separate users)

| Username | Role | Password (dev) | Use for |
|----------|------|----------------|---------|
| `admin` | `admin` | `admin123` | Journey registry, backlog, heal review (no Agent Console) |
| `superadmin` | `superadmin` | `superadmin123` or `FACTORY_SUPERADMIN_PASSWORD` | **Agent Console**, notifications bell, Observatory |

**Do not** promote `admin` to `superadmin` — use two accounts.

Bootstrap / fix local DB:

```powershell
cd backend
.\venv\Scripts\python.exe scripts\bootstrap_factory_users.py --fix-admin-role
```

---

## 2. Production checklist (before launch)

| Item | Setting | Verify |
|------|---------|--------|
| Telegram disabled | `HERMES_TELEGRAM_ENABLED=false` | `POST /api/v1/hermes/trigger` returns 403 |
| Factory cron | `FACTORY_SCHEDULER_ENABLED=true` | Logs show Loop A–D registration |
| MCP secret | `AWT_MCP_SECRET` rotated | Hermes MCP auth works |
| Bridge secret | `HERMES_BRIDGE_SECRET` set | Bridge events + `/run` auth |
| Bridge URL | `HERMES_BRIDGE_URL` (optional) | Chat routes to bridge instead of worker |
| Bridge service | `python hermes_bridge.py serve` on :8790 | Demo or orchestrator mode |
| Service user | `FACTORY_SERVICE_USER_ID` valid | Cron jobs enqueue |
| DB migrations | HF-1 … HF-6 tables exist | `user_notifications`, `observatory_access_log` |

---

## 3. Factory loops (AWT worker)

| Loop | Env cron | Job type | Purpose |
|------|----------|----------|---------|
| A | `FACTORY_LOOP_A_CRON` | `drain_backlog` | Process journey backlog |
| B | `FACTORY_REGRESSION_CRON` | `run_regression` | Tag-based regression |
| C | `FACTORY_LOOP_C_CRON` | `scan_changes` | URL snapshot diff |
| D | `FACTORY_LOOP_D_CRON` | `heal_failures` | Auto-heal failures |

**Manual trigger:** Agent Console chat — e.g. `Run regression`, `Drain backlog`, `Scan changes`, `Heal failures`, `Full cycle`.

---

## 4. Notifications (HF-6.1)

- On job **completed** or **failed**, all **superadmin** users receive in-app notifications (`user_notifications`). The bell is hidden for other roles.
- Bell icon in header; link opens Agent Console with job id.
- Stretch: wire email via existing email infra.

---

## 5. Agent Observatory (HF-6.3–6.4)

**Who:** `superadmin` only (`admin` gets 403).

| API | Purpose |
|-----|---------|
| `GET /api/v1/agent/jobs/{id}/hermes-trace` | Full event trace with `payload_full`, `llm_turns` |
| `GET /api/v1/agent/hermes/sessions/{sess_id}` | Session drill-down |

- Secrets redacted at read: API keys, passwords, tokens.
- Every trace view logged in `observatory_access_log`.

**Bridge path (HF-3.7 + HF-6.6):** Set `HERMES_BRIDGE_URL=http://localhost:8790` on AWT. Run bridge with `HERMES_BRIDGE_DEMO_MODE=1` for local delegate simulation without Node 1 Hermes.

**Event ingest (HF-6.2):** Bridge posts to `POST /api/v1/agent/hermes/events` with `HERMES_BRIDGE_SECRET`.

Smoke test (replace `JOB_ID`):

```bash
curl -X POST http://localhost:8000/api/v1/agent/hermes/events \
  -H "Authorization: Bearer $HERMES_BRIDGE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"JOB_ID","event_type":"delegate_complete","profile":"qa-test-gen","hermes_session_id":"sess_smoke","message":"ops smoke"}'
```

Or use `docs/hermes-profiles/bridge/hermes_bridge.py post-event`.

---

## 6. Node 1 Hermes (Phase B — EPIC-HF-07)

Before production launch:

1. Deploy all 7 SOUL.md profiles (`qa-orchestrator` **in repo** — copy to `~/.hermes/profiles/`, then planner, test-gen, dispatcher, healer, change-detector, reporter).
2. Configure shared MCP template (`_shared/mcp_servers.yaml.example`) — verify [MCP_CONNECTIVITY.md](hermes-profiles/_shared/MCP_CONNECTIVITY.md).
3. Run Hermes Bridge for chat → orchestrator path.
4. Smoke: `full_cycle` from webapp → delegate events in job timeline.

---

## 7. Hermes migration (dev mini PC → prod PC) — HF-7

**Strategy:** Prove on Ubuntu mini PC → package profiles → deploy to prod Ubuntu with **env-only** changes.

| Step | Command / doc |
|------|----------------|
| Guide | [hermes-profiles/Hermes_Environment_Migration_Guide.md](hermes-profiles/Hermes_Environment_Migration_Guide.md) |
| Pack (dev) | `scripts/hermes-migrate/pack-profiles.sh` |
| Deploy (prod) | `scripts/hermes-migrate/deploy-profiles.sh --from-git <repo>` |
| Smoke | `scripts/hermes-migrate/smoke-check.sh --env prod` |
| AWT side | Update `HERMES_BRIDGE_URL` + `HERMES_BRIDGE_SECRET` in `backend/.env` (see `awt-bridge.env.patch.example`) |

**Dev sign-off checklist:** migration guide §4 (MCP health, Bridge, Agent Console `full_cycle`, Observatory).

---

## 8. Troubleshooting

| Symptom | Check |
|---------|-------|
| Cron not running | `FACTORY_SCHEDULER_ENABLED`, APScheduler started in logs |
| No notifications | Log in as `superadmin`; check `user_notifications` for superadmin user id |
| Heal review growing | Inspect `heal_review_items`; fix UAT or raise `FACTORY_HEAL_MAX_ATTEMPTS` |
| Observatory 403 | User must be `superadmin` |
| Migration errors | Run `PYTHONPATH=. python -c "from migrations.add_observatory_hf6 import upgrade; upgrade()"` |

---

## 9. Restart procedure

```powershell
cd backend
.\venv\Scripts\python.exe start_server.py
# MCP (optional, for Hermes):
.\venv\Scripts\python.exe mcp_server.py
```

After env changes, restart backend so scheduler re-registers cron jobs.
