# Hermes QA Factory — Operations Runbook

**Version:** 1.0 · **Date:** 2026-06-08  
**Branch:** `feat/hermes-qa-factory`  
**Related:** [Hermes_QA_Factory_Agile_Development_Plan.md](Hermes_QA_Factory_Agile_Development_Plan.md) · [Hermes_QA_Autonomous_Workflow_v5.md](Hermes_QA_Autonomous_Workflow_v5.md)

---

## 1. Production checklist (before launch)

| Item | Setting | Verify |
|------|---------|--------|
| Telegram disabled | `HERMES_TELEGRAM_ENABLED=false` | `POST /api/v1/hermes/trigger` returns 403 |
| Factory cron | `FACTORY_SCHEDULER_ENABLED=true` | Logs show Loop A–D registration |
| MCP secret | `AWT_MCP_SECRET` rotated | Hermes MCP auth works |
| Bridge secret | `HERMES_BRIDGE_SECRET` set (Phase B) | Bridge events accepted |
| Service user | `FACTORY_SERVICE_USER_ID` valid | Cron jobs enqueue |
| DB migrations | HF-1 … HF-6 tables exist | `user_notifications`, `observatory_access_log` |

---

## 2. Factory loops (AWT worker)

| Loop | Env cron | Job type | Purpose |
|------|----------|----------|---------|
| A | `FACTORY_LOOP_A_CRON` | `drain_backlog` | Process journey backlog |
| B | `FACTORY_REGRESSION_CRON` | `run_regression` | Tag-based regression |
| C | `FACTORY_LOOP_C_CRON` | `scan_changes` | URL snapshot diff |
| D | `FACTORY_LOOP_D_CRON` | `heal_failures` | Auto-heal failures |

**Manual trigger:** Agent Console chat — e.g. `Run regression`, `Drain backlog`, `Scan changes`, `Heal failures`, `Full cycle`.

---

## 3. Notifications (HF-6.1)

- On job **completed** or **failed**, creator receives in-app notification (`user_notifications`).
- Bell icon in header; link opens Agent Console with job id.
- Stretch: wire email via existing email infra.

---

## 4. Agent Observatory (HF-6.3–6.4)

**Who:** `superadmin` only (`admin` gets 403).

| API | Purpose |
|-----|---------|
| `GET /api/v1/agent/jobs/{id}/hermes-trace` | Full event trace with `payload_full`, `llm_turns` |
| `GET /api/v1/agent/hermes/sessions/{sess_id}` | Session drill-down |

- Secrets redacted at read: API keys, passwords, tokens.
- Every trace view logged in `observatory_access_log`.

**Phase B:** Hermes Bridge posts events to `POST /api/v1/agent/hermes/events` with `HERMES_BRIDGE_SECRET`.

---

## 5. Node 1 Hermes (Phase B — EPIC-HF-07)

Before production launch:

1. Deploy all 7 SOUL.md profiles (`qa-orchestrator`, planner, test-gen, dispatcher, healer, change-detector, reporter).
2. Configure shared MCP template pointing at AWT MCP port.
3. Run Hermes Bridge for chat → orchestrator path.
4. Smoke: `full_cycle` from webapp → delegate events in job timeline.

---

## 6. Troubleshooting

| Symptom | Check |
|---------|-------|
| Cron not running | `FACTORY_SCHEDULER_ENABLED`, APScheduler started in logs |
| No notifications | `created_by_user_id` on job; `user_notifications` table |
| Heal review growing | Inspect `heal_review_items`; fix UAT or raise `FACTORY_HEAL_MAX_ATTEMPTS` |
| Observatory 403 | User must be `superadmin` |
| Migration errors | Run `PYTHONPATH=. python -c "from migrations.add_observatory_hf6 import upgrade; upgrade()"` |

---

## 7. Restart procedure

```powershell
cd backend
.\venv\Scripts\python.exe start_server.py
# MCP (optional, for Hermes):
.\venv\Scripts\python.exe mcp_server.py
```

After env changes, restart backend so scheduler re-registers cron jobs.
