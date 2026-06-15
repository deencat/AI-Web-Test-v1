# Hermes Environment Migration — Dev Ubuntu → Production Ubuntu

**Version:** 1.0 · **Date:** 2026-06-08  
**Program:** Hermes QA Factory (HF) · **Phase:** B / launch hardening  
**Related:** [Hermes_QA_Factory_Agile_Development_Plan.md](../Hermes_QA_Factory_Agile_Development_Plan.md) §4.3 · [Hermes_QA_Factory_Ops_Runbook.md](../Hermes_QA_Factory_Ops_Runbook.md) §9 · [scripts/hermes-migrate/README.md](../../scripts/hermes-migrate/README.md)

---

## 1. Strategy (approved approach)

Use a **small Ubuntu mini PC** for Hermes development and smoke testing. After sign-off, **package profiles + bridge** and deploy to a **higher-spec production Ubuntu PC** by changing **environment-specific settings only** — not rebuilding SOUL.md or re-running full Hermes setup from scratch.

| Principle | Detail |
|-----------|--------|
| **Source of truth** | Git: `docs/hermes-profiles/` in AI Web Test repo |
| **Runtime copy** | `~/.hermes/profiles/` on each Ubuntu host |
| **What moves** | `SOUL.md`, `config.yaml`, bridge scripts, systemd unit |
| **What does not move** | Agent `memories/` (optional fresh prod), logs, dev secrets |
| **AWT stays separate** | Hermes only needs network access to AWT API `:8000` and MCP `:8001` |

---

## 2. Environment roles

| Host | Role | Typical name |
|------|------|--------------|
| **AWT dev** | AI Web Test API + MCP + webapp (Windows or server) | `awt-dev` |
| **Hermes dev** | Mini Ubuntu — install, profile tuning, smoke | `hermes-dev` |
| **AWT prod** | Production AI Web Test | `awt-prod` |
| **Hermes prod** | Production Ubuntu — packaged deploy from dev | `hermes-prod` |

Hermes dev and Hermes prod run the **same profile files**; only `.env` URLs and rotated secrets differ.

---

## 3. What changes between dev and prod

| Variable / setting | Dev (mini PC) | Prod (bigger PC) |
|--------------------|---------------|------------------|
| `AWT_MCP_URL` / MCP in `config.yaml` | `http://awt-dev:8001` | `https://awt-prod:8001` or internal IP |
| `AWT_AGENT_EVENTS_URL` | `http://awt-dev:8000/api/v1/agent/hermes/events` | prod URL |
| `HERMES_BRIDGE_SECRET` | dev secret | **rotated** — must match AWT `backend/.env` |
| `AWT_MCP_SECRET` | dev | prod (match AWT) |
| `HERMES_BRIDGE_URL` (on **AWT**) | `http://hermes-dev:8790` | `http://hermes-prod:8790` |
| `HERMES_BRIDGE_DEMO_MODE` | `1` OK for fake delegates | `0` — real orchestrator |
| LLM API keys | dev OpenRouter / etc. | prod keys per security policy |

**Do not** hardcode hostnames inside `SOUL.md`. Use `config.yaml` + `~/.hermes/.env` only.

---

## 4. Dev sign-off checklist (before packaging)

Complete on **Hermes dev** mini PC:

- [ ] Hermes CLI installed; `hermes profile list` shows all required profiles
- [ ] MCP health: `curl -H "Authorization: Bearer $AWT_MCP_SECRET" $AWT_MCP_URL/health`
- [ ] Bridge `serve` running; `GET /health` returns OK
- [ ] AWT `HERMES_BRIDGE_URL` points at dev Ubuntu
- [ ] Agent Console (`superadmin`): `full_cycle` → delegate events in job timeline
- [ ] Observatory shows `hermes_session_id` and delegate payloads
- [ ] At least one real MCP tool invoked from a specialist profile (smoke)
- [ ] Profile files committed or synced to `docs/hermes-profiles/` in git

---

## 5. Packaging (dev → artifact)

Use repo scripts (HF-7.2):

```bash
# On Hermes dev — from AI Web Test repo clone
cd scripts/hermes-migrate
cp hermes.env.dev.example ~/.hermes/.env   # first-time only
./pack-profiles.sh
# Output: dist/hermes-factory-profiles-YYYYMMDD.tar.gz
```

**Includes:** `profiles/*` (SOUL, config), `bridge/`, systemd unit  
**Excludes:** `*/memories/`, `*.log`, `.env` (secrets)

**Preferred path:** commit tested profiles to git, then on prod run `deploy-profiles.sh --from-git` instead of tarball.

---

## 6. Production deploy (artifact → prod PC)

```bash
# On Hermes prod — fresh Ubuntu with Hermes CLI installed
cd scripts/hermes-migrate
cp hermes.env.prod.example ~/.hermes/.env
nano ~/.hermes/.env                    # prod hosts + rotated secrets

./deploy-profiles.sh --from-tar ../dist/hermes-factory-profiles-YYYYMMDD.tar.gz
# OR
./deploy-profiles.sh --from-git /path/to/AI-Web-Test-v1-2

sudo cp ../../docs/hermes-profiles/bridge/hermes-factory-bridge.service /etc/systemd/system/
sudo systemctl enable --now hermes-factory-bridge

./smoke-check.sh --env prod
```

**On AWT prod** `backend/.env`:

```env
HERMES_BRIDGE_URL=http://hermes-prod:8790
HERMES_BRIDGE_SECRET=<prod-secret>
```

Restart AWT backend after env change.

---

## 7. Rollback

| Scenario | Action |
|----------|--------|
| Bad prod deploy | Restore previous tarball from `dist/` backup; restart bridge |
| Wrong secrets | Fix `~/.hermes/.env` + AWT `.env`; restart bridge + AWT |
| Profile bug | Fix in git → redeploy `--from-git`; no Hermes reinstall |

---

## 8. Sprint mapping (HF program)

| ID | Story | Status |
|----|-------|--------|
| **HF-7.1** | This guide + env templates | ✅ |
| **HF-7.2** | `pack-profiles.sh` | 🔜 stub → harden after dev smoke |
| **HF-7.3** | `deploy-profiles.sh` | 🔜 stub → harden after dev smoke |
| **HF-7.4** | `smoke-check.sh` | 🔜 stub → harden after dev smoke |
| **HF-7.5** | Prod cutover runbook sign-off with security | ⬜ |

---

## 9. References

- Profile templates: [README.md](README.md)
- Bridge service: [bridge/README.md](bridge/README.md)
- v5 architecture: [Hermes_QA_Autonomous_Workflow_v5.md](../Hermes_QA_Autonomous_Workflow_v5.md) §3, §7
