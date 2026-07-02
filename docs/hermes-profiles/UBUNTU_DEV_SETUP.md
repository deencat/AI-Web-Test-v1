# Hermes QA Factory — Ubuntu Mini PC Setup Guide

**Version:** 1.0 · **Date:** 2026-06-12  
**Branch:** `feat/hermes-qa-factory` · **Commit:** `58c9df3` or later  
**Audience:** First-time setup on Ubuntu mini PC (Hermes dev / Node 1)  
**Time:** ~2–4 hours (excluding full crawl smoke)

> **Export this file** to your mini PC (USB, email, or `git pull` after clone).  
> Work through sections **in order**. Tick each checkbox as you go.

---

## What you are building

```
┌─────────────────────────────┐         LAN          ┌──────────────────────────────┐
│  Ubuntu mini PC (YOU)       │ ◄──────────────────► │  Windows PC — AI Web Test    │
│  Hermes Agent profiles      │   ports 8000, 8001   │  API :8000 · MCP :8001       │
│  Hermes Factory Bridge :8790│                      │  Web UI :5173                │
└─────────────────────────────┘                      └──────────────────────────────┘
         │                                                      │
         │  optional ReqIQ :3001 (if not on Windows)            │
         └──────────────────────────────────────────────────────┘
```

**Hermes profiles (v5 factory):**

| Profile | Purpose |
|---------|---------|
| `qa-orchestrator` | Entry point — delegates work |
| `qa-journey-planner` | Coverage, backlog, ReqIQ readiness |
| `qa-test-gen` | Browser crawl → test case |
| Bridge (`hermes_bridge.py`) | AWT Agent Console → orchestrator |

---

## Before you start — fill in this worksheet

Write these down **before** editing any `.env` file.

| Item | Your value | Notes |
|------|------------|-------|
| Ubuntu mini PC IP | `192.168.___.___` | `hostname -I` on Ubuntu |
| Windows AWT PC IP | `192.168.___.___` | `ipconfig` on Windows |
| `AWT_MCP_SECRET` | `________________` | Must match `backend/.env` on Windows |
| `HERMES_BRIDGE_SECRET` | `________________` | Must match on **both** hosts |
| `REQIQ_PROJECT_ID` | `cl______________` | From ReqIQ project settings |
| `OPENROUTER_API_KEY` | `sk-or-__________` | Or use Ollama locally |
| `TEST_LOGIN_USERNAME` | `________________` | UAT login for crawl |
| `TEST_LOGIN_PASSWORD` | `________________` | |
| `HTTP_AUTH_USERNAME` | `________________` | UAT HTTP basic auth (if any) |
| `HTTP_AUTH_PASSWORD` | `________________` | |
| Git repo path on Ubuntu | `/home/___/AI-Web-Test-v1-2` | After clone |

### Worksheet field reference (lines 47–53)

#### `REQIQ_PROJECT_ID`

| | |
|--|--|
| **What it is** | ReqIQ project identifier (a CUID string like `cmp0zdx4g0004alp8z77ess7a`). |
| **Who uses it** | `qa-journey-planner` — passed to MCP tools `get_coverage_matrix`, `get_reqiq_readiness`, `suggest_scenarios_from_wiki`. |
| **Where to get it** | **Easiest:** open `backend/config/uat-journey-registry.yaml` on Windows — top line `reqiq_project_id:`. **Or:** ReqIQ UI → your project → Settings/URL (id in API paths). **Or:** `GET http://<reqiq-host>:3001/api/v1/projects` with Bearer token — copy the project `id`. |
| **Goes in** | Ubuntu `~/.hermes/.env` only (not Windows `backend/.env` unless you also use ReqIQ from AWT scripts). |

#### `OPENROUTER_API_KEY`

| | |
|--|--|
| **What it is** | API key so Hermes profiles can call cloud LLMs (Claude, GPT-4o, etc.) during `qa-orchestrator chat` and delegate tasks. |
| **Who uses it** | All three Hermes profiles when you pick **OpenRouter** in `qa-orchestrator model` (and planner/test-gen). |
| **Where to get it** | [https://openrouter.ai](https://openrouter.ai) → sign in → **Keys** → Create key (`sk-or-v1-...`). |
| **Alternative** | Skip OpenRouter — install **Ollama** on Ubuntu (`ollama pull qwen2.5:7b`) and choose Ollama in each `* model` wizard instead. |
| **Goes in** | Ubuntu `~/.hermes/.env`. Never commit this key to git. |

#### `TEST_LOGIN_USERNAME` / `TEST_LOGIN_PASSWORD`

| | |
|--|--|
| **What they are** | Credentials for logging into the **Three HK UAT web app** (My3 / shop) while the browser agent crawls a journey. |
| **Who uses them** | `qa-test-gen` — reads from `~/.hermes/.env` and passes them to MCP `crawl_and_save_test` as `login_email` / `login_password` (unless the journey uses a Step Library `login_module` only). |
| **Where to get them** | Your team's **UAT test subscriber account** (same as you use manually on `wwwuat.three.com.hk`). Example in repo script `crawl_and_save_5g_voucher_plan_v2.ps1` uses a `pmo.andrewchan+...@gmail.com` style account — use **your** approved UAT user, not a random value. |
| **Goes in** | Ubuntu `~/.hermes/.env`. These are secrets — do not commit. |

#### `HTTP_AUTH_USERNAME` / `HTTP_AUTH_PASSWORD`

| | |
|--|--|
| **What they are** | **HTTP Basic Auth** for the UAT site **gate** in front of the browser (browser popup before the page loads). Not the same as My3 login. |
| **Who uses them** | `qa-test-gen` → MCP `crawl_and_save_test` → `http_auth_username` / `http_auth_password`. |
| **Where to get them** | For **Three HK UAT** (`wwwuat.three.com.hk`), AWT already knows defaults in code: username `user`, password `3.comUXuat` (`backend/app/utils/http_auth_credentials.py`). Set these same values in Hermes `.env` so the agent passes them explicitly. For other hosts, ask your UAT/DevOps team. |
| **If empty** | Crawl to `wwwuat.three.com.hk` may still work when AWT injects UAT gate creds server-side, but HF-3.1d Hermes path expects them in `~/.hermes/.env` per `qa-test-gen/SOUL.md`. |
| **Goes in** | Ubuntu `~/.hermes/.env`. |

#### Git repo path on Ubuntu

| | |
|--|--|
| **What it is** | Absolute path where you cloned AI Web Test on the mini PC. |
| **Who uses it** | You — for `deploy-profiles.sh --from-git <path>`, smoke scripts, and Bridge (`docs/hermes-profiles/bridge/`). |
| **Where to get it** | After `git clone ... ~/AI-Web-Test-v1-2`, run `pwd` inside that folder. Typical: `/home/<your-linux-username>/AI-Web-Test-v1-2`. |
| **Not a secret** | Just a folder path on the mini PC. |

---

## Part 0 — Prepare Windows (AWT host) first

Do this **on your Windows PC** before touching Ubuntu.

### 0.1 Start AI Web Test

```powershell
cd backend
# activate venv if you use one
python ..\start_server.py
```

Confirm in browser: `http://localhost:5173` loads. Log in as **superadmin**.

### 0.2 Verify `backend/.env` (Windows)

Open `backend/.env` and confirm these exist (values must be real, not placeholders):

```env
AWT_MCP_SECRET=<your-secret>
AWT_MCP_PORT=8001
AWT_SERVICE_USERNAME=<service-account-user>
AWT_SERVICE_PASSWORD=<service-account-password>
HERMES_BRIDGE_SECRET=<same-as-ubuntu-will-use>
```

**Later** (after Ubuntu Bridge is running), add:

```env
HERMES_BRIDGE_URL=http://<UBUNTU-IP>:8790
```

Do **not** use `localhost` for `HERMES_BRIDGE_URL` — AWT on Windows must reach Ubuntu by LAN IP.

### 0.3 Run AWT prerequisite smoke (Windows)

From repo root in PowerShell:

```powershell
.\scripts\hermes-migrate\smoke-awt-prereq-3.1d.ps1
```

**Expected:** MCP health OK, API health OK.  
**Warn OK:** `0 pending` backlog — fix in step 0.4.

### 0.4 Seed journey backlog (if empty)

1. Open Agent Console (superadmin).
2. Go to **Journey Registry**.
3. Pick a journey (e.g. 5G voucher plan).
4. Click **Enqueue** → status **pending**.

### 0.5 Note Windows firewall

Ubuntu must reach Windows on **TCP 8000** and **8001**. If smoke fails with *connection refused*, allow inbound on Windows Firewall for those ports (private network).

### 0.6 Test from Ubuntu later

On Ubuntu you will run:

```bash
curl -H "Authorization: Bearer <AWT_MCP_SECRET>" http://<WINDOWS-IP>:8001/health
```

---

## Part 1 — Ubuntu base system

### 1.1 Update packages

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install common tools

```bash
sudo apt install -y git curl jq rsync python3 python3-venv build-essential
```

### 1.3 Note your IP

```bash
hostname -I
```

Write it in the worksheet above.

### 1.4 Optional — allow SSH from Windows

If you develop from Windows over SSH:

```bash
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
```

---

## Part 2 — Install Hermes Agent

Hermes Agent is the CLI/runtime for profiles (`qa-orchestrator`, etc.).

### 2.1 Install per official Hermes Agent docs

Install Hermes Agent on Ubuntu using the method from your team's Hermes documentation  
(see also legacy reference: `docs/Hermes_QA_MultiAgent_Profiles_v4.md` § Prerequisites).

### 2.2 Verify installation

```bash
hermes --version
# Expected: 0.14.x or compatible with your team standard

hermes profile list
# May be empty on first run — that is OK
```

### 2.3 Reload shell after install

```bash
source ~/.bashrc
# or: source ~/.zshrc
```

---

## Part 3 — Get the AI Web Test repo on Ubuntu

### Option A — Git clone (recommended)

```bash
cd ~
git clone https://github.com/deencat/AI-Web-Test-v1.git AI-Web-Test-v1-2
cd AI-Web-Test-v1-2
git checkout feat/hermes-qa-factory
git pull
```

> Adjust remote URL if your fork differs.

### Option B — Copy from USB

Copy the whole `AI-Web-Test-v1-2` folder to e.g. `~/AI-Web-Test-v1-2`.

### 3.1 Verify profile templates exist

```bash
ls ~/AI-Web-Test-v1-2/docs/hermes-profiles/
```

You should see: `qa-orchestrator/`, `qa-journey-planner/`, `qa-test-gen/`, `bridge/`, `_shared/`.

---

## Part 4 — Configure `~/.hermes/.env`

### 4.1 Create Hermes home

```bash
mkdir -p ~/.hermes
```

### 4.2 Copy template and edit

```bash
cp ~/AI-Web-Test-v1-2/scripts/hermes-migrate/hermes.env.dev.example ~/.hermes/.env
nano ~/.hermes/.env
```

### 4.3 Set these values (use your worksheet)

```env
# --- AI Web Test (Windows PC LAN IP — NOT localhost) ---
AWT_MCP_URL=http://<WINDOWS-IP>:8001
AWT_AGENT_EVENTS_URL=http://<WINDOWS-IP>:8000/api/v1/agent/hermes/events

# Must match backend/.env on Windows exactly
AWT_MCP_SECRET=<your-awt-mcp-secret>
HERMES_BRIDGE_SECRET=<your-bridge-secret>

# Bridge on this Ubuntu machine
HERMES_BRIDGE_PORT=8790
HERMES_BRIDGE_DEMO_MODE=1

# ReqIQ (planner uses MCP proxy; project id required)
REQIQ_API_URL=http://<REQIQ-HOST>:3001
REQIQ_API_KEY=<reqiq-jwt-if-needed>
REQIQ_PROJECT_ID=<your-reqiq-project-cuid>

# UAT credentials for qa-test-gen crawl
TEST_LOGIN_USERNAME=<uat-login>
TEST_LOGIN_PASSWORD=<uat-password>
HTTP_AUTH_USERNAME=<http-basic-user>
HTTP_AUTH_PASSWORD=<http-basic-password>

# LLM
OPENROUTER_API_KEY=<your-openrouter-key>
```

**Save and exit** (`Ctrl+O`, `Enter`, `Ctrl+X` in nano).

### 4.4 Load env in every new terminal

```bash
source ~/.hermes/.env
```

Optional — add to `~/.bashrc`:

```bash
echo 'set -a && [ -f ~/.hermes/.env ] && source ~/.hermes/.env && set +a' >> ~/.bashrc
source ~/.bashrc
```

---

## Part 5 — Deploy factory profiles

### 5.1 Run deploy script

```bash
cd ~/AI-Web-Test-v1-2/scripts/hermes-migrate
chmod +x *.sh
./deploy-profiles.sh --from-git ~/AI-Web-Test-v1-2
```

This copies `docs/hermes-profiles/*` → `~/.hermes/profiles/`.

### 5.2 Create Hermes profile shells

Hermes needs a profile registered before aliases work:

```bash
hermes profile create "qa-orchestrator"
hermes profile create "qa-journey-planner"
hermes profile create "qa-test-gen"
```

Reload shell:

```bash
source ~/.bashrc
```

### 5.3 Verify files landed

```bash
ls -la ~/.hermes/profiles/qa-orchestrator/
ls -la ~/.hermes/profiles/qa-journey-planner/
ls -la ~/.hermes/profiles/qa-test-gen/
```

Each folder must contain **`SOUL.md`** and **`config.yaml`**.

If missing, copy manually:

```bash
cp ~/AI-Web-Test-v1-2/docs/hermes-profiles/qa-orchestrator/* ~/.hermes/profiles/qa-orchestrator/
cp ~/AI-Web-Test-v1-2/docs/hermes-profiles/qa-journey-planner/* ~/.hermes/profiles/qa-journey-planner/
cp ~/AI-Web-Test-v1-2/docs/hermes-profiles/qa-test-gen/* ~/.hermes/profiles/qa-test-gen/
```

### 5.4 List profiles

```bash
hermes profile list
```

Expected: `qa-orchestrator`, `qa-journey-planner`, `qa-test-gen`.

---

## Part 6 — Assign LLM models per profile

Run once per profile. Pick models your team approves.

```bash
qa-orchestrator model
# Suggested: OpenRouter → anthropic/claude-3.5-sonnet (or claude-sonnet)

qa-journey-planner model
# Suggested: OpenRouter → openai/gpt-4o or claude-3.5-sonnet

qa-test-gen model
# Suggested: OpenRouter → anthropic/claude-3.5-sonnet (long crawl instructions)
```

**Alternative — Ollama (local, no API cost):**

```bash
# If Ollama installed:
ollama pull qwen2.5:7b
# Then select Ollama provider in each `* model` wizard
```

---

## Part 7 — Connectivity smoke (required)

### 7.1 HTTP — MCP health from Ubuntu

```bash
source ~/.hermes/.env
curl -v -H "Authorization: Bearer ${AWT_MCP_SECRET}" "${AWT_MCP_URL}/health"
```

**Pass:** HTTP 200, JSON health body.  
**Fail:** connection refused → Windows firewall / wrong IP / AWT not running.

### 7.2 MCP endpoint auth

```bash
curl -sf -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer ${AWT_MCP_SECRET}" \
  -H "Content-Type: application/json" \
  "${AWT_MCP_URL}/mcp"
```

**Pass:** not `401`.  
**Fail 401:** `AWT_MCP_SECRET` mismatch between Ubuntu and Windows.

### 7.3 Automated smoke script

```bash
cd ~/AI-Web-Test-v1-2/scripts/hermes-migrate
./smoke-check.sh --env dev
```

**Pass:** MCP health OK. Bridge health may fail until Part 8 — that is OK for now.

### 7.4 Hermes MCP tool via orchestrator

```bash
qa-orchestrator chat -q 'Call health_check on ai-web-test MCP. Reply with JSON only.'
```

**Pass:** JSON shows API healthy.

---

## Part 8 — Start Hermes Factory Bridge

The Bridge lets the **Agent Console** on Windows trigger Hermes jobs.

### 8.1 Start Bridge (demo mode first)

Open a **dedicated terminal** on Ubuntu and leave it running:

```bash
source ~/.hermes/.env
cd ~/AI-Web-Test-v1-2/docs/hermes-profiles/bridge
python3 hermes_bridge.py serve --port 8790
```

**Expected log:** `Listening on 0.0.0.0:8790`

### 8.2 Test Bridge health (second terminal)

```bash
curl http://127.0.0.1:8790/health
```

**Pass:** `{"status":"ok","service":"hermes-factory-bridge"}`

### 8.3 Wire Windows AWT to Bridge

On **Windows** `backend/.env`:

```env
HERMES_BRIDGE_URL=http://<UBUNTU-IP>:8790
HERMES_BRIDGE_SECRET=<same-as-ubuntu>
```

Restart AWT (`python start_server.py`).

### 8.4 Agent Console demo (Windows browser)

1. Log in as **superadmin**.
2. Open **Agent Console**.
3. Chat: `full cycle` or `drain backlog`.
4. Open **Job Monitor** — you should see delegate events (demo mode simulates planner → test-gen).

> Demo mode uses **fake** `test_case_id` — good for UI smoke only.

---

## Part 9 — HF-3.1d integration smoke (real Hermes)

Full guide: `docs/hermes-profiles/HF-3.1d_Integration_Smoke.md`

### 9.1 Planner-only dry run (~5–10 min)

```bash
source ~/.hermes/.env
qa-orchestrator chat -q 'delegate to qa-journey-planner: task_type drain_backlog project Three-HK max_items 1. Return JSON only.'
```

**Pass:** JSON with `items_for_test_gen` or `items_enqueued`.  
**Fail `insufficient`:** ReqIQ readiness low — update wiki or enqueue journey manually.

Automated:

```bash
cd ~/AI-Web-Test-v1-2/scripts/hermes-migrate
chmod +x smoke-integration-3.1d.sh
./smoke-integration-3.1d.sh --planner-only
```

### 9.2 Full acceptance (~15–45 min)

**Pre-check:** at least one **pending** backlog item on Windows Agent Console.

```bash
source ~/.hermes/.env
export HERMES_BRIDGE_DEMO_MODE=0

qa-orchestrator chat -q 'drain backlog for Three-HK max_items 1'
```

**Pass (HF-3.1d):** output contains **`test_case_id`** (real integer from crawl).

Automated:

```bash
./smoke-integration-3.1d.sh
```

### 9.3 Verify on Windows

- Agent Console → Job Monitor: delegate events from real profiles.
- Tests UI: new test case appears.
- Journey Backlog: item status **done**.

---

## Part 10 — Production Bridge mode (after smoke passes)

When HF-3.1d passes, switch Bridge from demo to real orchestrator.

### 10.1 Ubuntu `~/.hermes/.env`

```env
HERMES_BRIDGE_DEMO_MODE=0
HERMES_ORCHESTRATOR_CMD=qa-orchestrator
```

### 10.2 Restart Bridge

Stop the old `serve` process (`Ctrl+C`), then:

```bash
source ~/.hermes/.env
cd ~/AI-Web-Test-v1-2/docs/hermes-profiles/bridge
python3 hermes_bridge.py serve --port 8790
```

### 10.3 Optional — systemd service (runs on boot)

```bash
sudo cp ~/AI-Web-Test-v1-2/docs/hermes-profiles/bridge/hermes-factory-bridge.service /etc/systemd/system/
# Edit the service file if paths differ for your user
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-factory-bridge
sudo systemctl status hermes-factory-bridge
```

---

## Part 11 — Dev sign-off checklist

Tick when complete on mini PC:

- [ ] `hermes --version` works
- [ ] `~/.hermes/.env` filled with correct Windows LAN IP
- [ ] `curl $AWT_MCP_URL/health` returns 200 from Ubuntu
- [ ] Three profiles: orchestrator, planner, test-gen — SOUL + config deployed
- [ ] Models assigned for all three profiles
- [ ] `qa-orchestrator chat` → `health_check` succeeds
- [ ] Bridge `serve` running; Windows `HERMES_BRIDGE_URL` set
- [ ] Agent Console demo shows delegate timeline
- [ ] HF-3.1d planner-only smoke passes
- [ ] HF-3.1d full run returns real `test_case_id`

After sign-off → package for prod: `scripts/hermes-migrate/pack-profiles.sh`  
See: `docs/hermes-profiles/Hermes_Environment_Migration_Guide.md`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` to :8001 | Windows firewall / AWT down | Start AWT; open ports 8000, 8001 |
| MCP `401 Unauthorized` | Secret mismatch | Sync `AWT_MCP_SECRET` both sides |
| `localhost` fails on Ubuntu | Wrong host | Use **Windows LAN IP** in `AWT_MCP_URL` |
| `qa-orchestrator: command not found` | Profile not created | `hermes profile create "qa-orchestrator"` + `source ~/.bashrc` |
| Planner `insufficient` | ReqIQ readiness &lt; 60 | Improve wiki; check `REQIQ_PROJECT_ID` |
| No `test_case_id` | Crawl failed | Check `TEST_LOGIN_*`, UAT URL, Job Monitor on Windows |
| Bridge 401 from AWT | Bridge secret mismatch | Sync `HERMES_BRIDGE_SECRET` |
| Agent Console no events | `HERMES_BRIDGE_URL` wrong | Use Ubuntu IP; restart AWT |
| Tool timeout | Slow UAT / long crawl | Raise `tool_timeout_seconds` in test-gen `config.yaml` |
| `command not found: qa-journey-planner` | Shell not reloaded | `source ~/.bashrc` after `profile create` |

---

## Quick reference — commands you will use often

```bash
# Load secrets
source ~/.hermes/.env

# Redeploy profiles after git pull
cd ~/AI-Web-Test-v1-2 && git pull
./scripts/hermes-migrate/deploy-profiles.sh --from-git ~/AI-Web-Test-v1-2

# Smoke
./scripts/hermes-migrate/smoke-check.sh --env dev
./scripts/hermes-migrate/smoke-integration-3.1d.sh --planner-only

# Bridge
cd ~/AI-Web-Test-v1-2/docs/hermes-profiles/bridge
python3 hermes_bridge.py serve --port 8790

# Orchestrator chat
qa-orchestrator chat -q 'drain backlog for Three-HK max_items 1'
```

---

## Related documents (in repo)

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Profile index |
| [HF-3.1d_Integration_Smoke.md](HF-3.1d_Integration_Smoke.md) | Integration acceptance |
| [_shared/MCP_CONNECTIVITY.md](_shared/MCP_CONNECTIVITY.md) | MCP debug detail |
| [Hermes_Environment_Migration_Guide.md](Hermes_Environment_Migration_Guide.md) | Dev → prod packaging |
| [bridge/README.md](bridge/README.md) | Bridge API |
| [../Hermes_QA_Factory_Agile_Development_Plan.md](../Hermes_QA_Factory_Agile_Development_Plan.md) | Sprint tracker |
| [../Hermes_QA_Factory_Ops_Runbook.md](../Hermes_QA_Factory_Ops_Runbook.md) | Operations |

---

## Export tips

**Easiest:** clone repo on mini PC (`git pull` on `feat/hermes-qa-factory`) — this file is at:

```
docs/hermes-profiles/UBUNTU_DEV_SETUP.md
```

**USB only:** copy these paths to the mini PC:

```
docs/hermes-profiles/          (entire folder)
scripts/hermes-migrate/        (entire folder)
```

You do **not** need the full backend on Ubuntu for Hermes-only setup (Bridge uses `python3` only).
