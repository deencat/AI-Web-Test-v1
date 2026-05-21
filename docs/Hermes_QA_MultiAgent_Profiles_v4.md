# Hermes Agent — QA Multi-Agent Setup Guide (v4)
### Ubuntu Setup + ReqIQ Integration
**Version:** 4.0 | **Date:** 2026-05-16 | **Hermes version:** 0.14.x

> **This is a practical Ubuntu setup guide.** It replaces v3, which contained fictional file names
> (`mcp_tools.yaml`, `mcp_servers.yaml`) and incorrect CLI syntax (`hermes --profile X setup`).
> All commands below are verified against the real Hermes Agent v0.14 API.

---

## Overview

This document defines all five Hermes Agent profiles for the QA Multi-Agent System and provides a
complete Ubuntu setup walkthrough. The architecture separates concerns across 5 profiles: one Manager
and four Specialists. Each profile has a single responsibility, its own LLM model assignment, and
explicit API contracts with ReqIQ and the AI Web Test Webapp.

---

## Physical Node Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NODE 1 — Ubuntu Mini PC  (Server / Admin — not daily human interface)      │
│                                                                             │
│  • Hermes Agent (all 5 profiles)  — Telegram gateways (per-profile)        │
│  • ReqIQ API                      — port 3001 (Docker: 3001→3001)           │
│  • ReqIQ UI                       — port 8080 (nginx → web container)       │
│  • Ollama (qwen2.5:7b)            — port 11434                              │
│  • Garage S3 (self-hosted)        — port 3900                               │
│  • Redis                          — port 6379                               │
└────────────────────────┬────────────────────────────────────────────────────┘
                         │  LAN / Tailscale VPN
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌──────────────────────┐     ┌──────────────────────┐
│  NODE 2 — Windows PC │     │  NODE 3 — Windows PC │
│  (Primary human UI)  │     │  (Secondary runner)  │
│                      │     │                      │
│  AI Web Test Webapp  │     │  AI Web Test Webapp  │
│  API  — port 8000    │     │  API  — port 8000    │
│  MCP  — port 8001    │     │  MCP  — port 8001    │
│  UI   — port 5173    │     │  UI   — port 5173    │
│                      │     │                      │
│  QA engineers use    │     │  Parallel test runs  │
│  this UI daily       │     │  dispatched here     │
└──────────────────────┘     └──────────────────────┘
```

### Human Interface Pattern

- **Daily workflow** happens on **Node 2/3** (Windows PCs) via the AI Web Test Webapp UI
- **Node 1 is admin/server only** — QA engineers do not log into it directly
- **Two ways to trigger Hermes** from Node 2/3:
  1. **Telegram** — remote/mobile triggering, receives reports
  2. **AI Web Test Webapp** — "Generate via Hermes" button → backend calls `qa-manager` programmatically

---

## Prerequisites (Node 1 — Ubuntu)

Before running any setup commands, confirm:

```bash
# 1. Hermes Agent installed
hermes --version     # should show 0.14.x

# 2. Ollama running with qwen2.5:7b pulled
ollama list          # should show qwen2.5:7b

# 3. ReqIQ running
curl -s http://localhost:3001/api/v1/health   # should return 200

# 4. AI Web Test MCP server (on Node 2) running
# From Node 2: python backend/mcp_server.py
# From Node 1: curl http://192.168.1.101:8001/health
```

---

## Part A — Ubuntu Setup Guide (Step by Step)

### Key Concepts Before You Start

**Profile file structure (real):**
```
~/.hermes/
├── config.yaml       # global defaults
├── .env              # global API keys
├── SOUL.md           # global system prompt (overridden by per-profile SOUL.md)
└── profiles/
    └── qa-manager/
        ├── config.yaml   # model, mcp_servers — profile overrides global
        ├── .env          # profile-specific secrets (adds to global .env)
        ├── SOUL.md       # system prompt for this profile (the agent's identity)
        ├── memories/     # agent memory (auto-managed)
        └── cron/         # cron jobs for this profile
```

**Command aliases (real):**
After `hermes profile create "qa-manager"`, Hermes creates a shell alias `qa-manager` that is equivalent to `hermes -p qa-manager`. Use the alias for all subsequent commands on that profile.

**SOUL.md is the system prompt (real):**
There is no wizard to paste the system prompt into. You write it directly to the file
`~/.hermes/profiles/<name>/SOUL.md`. Hermes loads it automatically as the agent's identity.

**MCP servers go in config.yaml (real):**
There is no `mcp_servers.yaml` or `mcp_tools.yaml`. MCP servers are configured under the
`mcp_servers:` key in `~/.hermes/profiles/<name>/config.yaml`.

**ReqIQ calls use curl via terminal tool:**
Hermes does not have built-in `type: http` tool definitions. The agent calls ReqIQ using
the `terminal` tool with `curl`, reading `REQIQ_API_KEY` from its `.env` file. The SOUL.md
instructions explain how to do this.

---

### Step 1 — Create All Five Profiles

```bash
hermes profile create "qa-manager"
hermes profile create "qa-requirements"
hermes profile create "qa-test-gen"
hermes profile create "qa-dispatcher"
hermes profile create "qa-reporter"
```

Each command creates `~/.hermes/profiles/<name>/` and registers a shell alias.
Reload your shell after: `source ~/.bashrc` (or `~/.zshrc`).

Verify profiles were created:
```bash
hermes profile list
```

---

### Step 2 — Set the Model for Each Profile

Use the alias (not `hermes --profile`):

```bash
# qa-manager: Claude Sonnet via OpenRouter
qa-manager model
# → select OpenRouter → type: anthropic/claude-3.5-sonnet

# qa-requirements: GPT-4o via OpenRouter
qa-requirements model
# → select OpenRouter → type: openai/gpt-4o

# qa-test-gen: GPT-4o-mini via OpenRouter
qa-test-gen model
# → select OpenRouter → type: openai/gpt-4o-mini

# qa-dispatcher: local Qwen via Ollama
qa-dispatcher model
# → select Custom / Local → base_url: http://localhost:11434/v1 → model: qwen2.5:7b

# qa-reporter: GPT-4o-mini via OpenRouter
qa-reporter model
# → select OpenRouter → type: openai/gpt-4o-mini
```

---

### Step 3 — Write SOUL.md Files (System Prompts)

Each agent's personality and instructions go in its SOUL.md file. Copy from the SOUL.md
sections later in this document:

```bash
nano ~/.hermes/profiles/qa-manager/SOUL.md
nano ~/.hermes/profiles/qa-requirements/SOUL.md
nano ~/.hermes/profiles/qa-test-gen/SOUL.md
nano ~/.hermes/profiles/qa-dispatcher/SOUL.md
nano ~/.hermes/profiles/qa-reporter/SOUL.md
```

The full contents for each file are in the **SOUL.md Files** section below.

---

### Step 4 — Configure MCP Servers in config.yaml

The AI Web Test MCP server (running on Node 2/3) is configured in each profile's `config.yaml`
under the `mcp_servers:` key.

**qa-manager config.yaml:**
```bash
cat > ~/.hermes/profiles/qa-manager/config.yaml << 'EOF'
mcp_servers:
  ai-web-test:
    url: "http://${NODE2_IP}:8001/mcp"
    headers:
      Authorization: "Bearer ${AWT_MCP_SECRET}"
    timeout: 180
    connect_timeout: 30
EOF
```

**qa-test-gen config.yaml:**
```bash
cat > ~/.hermes/profiles/qa-test-gen/config.yaml << 'EOF'
mcp_servers:
  ai-web-test:
    url: "http://${NODE2_IP}:8001/mcp"
    headers:
      Authorization: "Bearer ${AWT_MCP_SECRET}"
    timeout: 300
    connect_timeout: 30
EOF
```

**qa-dispatcher config.yaml** (connects to both Windows runner nodes):
```bash
cat > ~/.hermes/profiles/qa-dispatcher/config.yaml << 'EOF'
mcp_servers:
  ai-web-test-node2:
    url: "http://${NODE2_IP}:8001/mcp"
    headers:
      Authorization: "Bearer ${AWT_MCP_SECRET}"
    timeout: 180
    connect_timeout: 30
  ai-web-test-node3:
    url: "http://${NODE3_IP}:8001/mcp"
    headers:
      Authorization: "Bearer ${AWT_MCP_SECRET}"
    timeout: 180
    connect_timeout: 30
EOF
```

**qa-requirements** and **qa-reporter** do not need the AI Web Test MCP server.

---

### Step 5 — Set Environment Variables in .env Files

#### Global `.env` (shared by all profiles):
```bash
cat > ~/.hermes/.env << 'EOF'
# LLM providers
OPENROUTER_API_KEY=sk-or-your-openrouter-key-here

# ReqIQ (JWT from POST /api/v1/login — see "REQIQ_API_KEY Refresh" section)
REQIQ_API_KEY=your-reqiq-jwt-here
REQIQ_URL=http://localhost:3001

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token-here

# AI Web Test MCP server
NODE2_IP=192.168.1.101
NODE3_IP=192.168.1.102
AWT_MCP_SECRET=R7dYHnn1FuHb_vW4UDNj1gXiowDo2bsj7yBn8In6uFY

# Garage S3
GARAGE_S3_ENDPOINT=http://localhost:3900
GARAGE_ACCESS_KEY=your-garage-access-key
GARAGE_SECRET_KEY=your-garage-secret-key
EOF
```

#### qa-test-gen `.env` (profile-specific secrets):
```bash
cat > ~/.hermes/profiles/qa-test-gen/.env << 'EOF'
# Browser login credentials (used by Stagehand during crawl)
TEST_LOGIN_USERNAME=pmo.andrewchan+015@gmail.com
TEST_LOGIN_PASSWORD=your-browser-login-password

# UAT HTTP Basic auth gate
HTTP_AUTH_USERNAME=uat_user
HTTP_AUTH_PASSWORD=uat_password

# ReqIQ project CUID (id from GET /api/v1/projects)
REQIQ_PROJECT_ID=cmp0zdx4g0004alp8z77ess7a
EOF
```

#### qa-reporter `.env`:
```bash
cat > ~/.hermes/profiles/qa-reporter/.env << 'EOF'
TELEGRAM_IT_CHAT_ID=-100123456789
TELEGRAM_UAT_CHAT_ID=-100987654321
EOF
```

---

### Step 6 — Set Up Telegram Gateways

Telegram is the primary gateway for receiving triggers (from humans) and sending results.

```bash
# qa-manager: receives task requests from human via Telegram
qa-manager gateway setup
# Select: Telegram
# Paste your TELEGRAM_BOT_TOKEN when prompted
# Add your Telegram user ID as allowed user

# qa-reporter: sends test reports to IT and UAT channels
qa-reporter gateway setup
# Can use same bot token or a separate "QA Reports Bot" bot
# Add IT chat ID and UAT chat ID as recipients
```

> **Note on programmatic triggers from AI Web Test Webapp:**
> Hermes does not have a native HTTP REST gateway. The Webapp can trigger Hermes in two ways:
> 1. **Telegram API call** (recommended): The AI Web Test backend sends a message to the
>    qa-manager Telegram bot programmatically using the Telegram HTTP API.
> 2. **CLI subprocess** (alternative): SSH to Node 1 and run `qa-manager chat -q "message"`.
>
> See the "AI Web Test Webapp Integration" section for the recommended implementation.

---

### Step 7 — Add the Nightly Cron Job to qa-manager

```bash
qa-manager cron add
# Fill in:
#   Name: nightly-regression
#   Schedule: 0 2 * * *
#   Message: Run nightly regression suite. Delegate to qa-dispatcher for all active projects. Auto-approve.
```

Or write the cron file directly:
```bash
mkdir -p ~/.hermes/profiles/qa-manager/cron
cat > ~/.hermes/profiles/qa-manager/cron/nightly-regression.yaml << 'EOF'
name: nightly-regression
schedule: "0 2 * * *"
message: |
  Run nightly regression suite.
  Delegate to qa-dispatcher for all active projects.
  Do not ask for confirmation — auto-approve and run.
auto_approve: true
EOF
```

---

### Step 8 — Install as systemd Service (Auto-start on boot)

```bash
# Install qa-manager gateway as a systemd service
qa-manager gateway install
# Follow prompts — creates a user-level systemd service

# Enable and start the service
systemctl --user enable hermes-qa-manager-gateway
systemctl --user start hermes-qa-manager-gateway

# Check it is running
systemctl --user status hermes-qa-manager-gateway

# Optional: also install qa-reporter if it has an active gateway
qa-reporter gateway install
systemctl --user enable hermes-qa-reporter-gateway
systemctl --user start hermes-qa-reporter-gateway
```

---

### Step 9 — Verify Everything

```bash
# Check profile health (dependencies, model config, gateway connectivity)
qa-manager doctor
qa-requirements doctor
qa-test-gen doctor
qa-dispatcher doctor
qa-reporter doctor

# Check MCP tool registration (should list tools from AI Web Test MCP server)
qa-test-gen tools

# Send a test message to qa-manager via Telegram
# In Telegram: "hello"
# Expected: qa-manager introduces itself and lists capabilities
```

---

### REQIQ_API_KEY Refresh

The ReqIQ API uses JWT with ~8h TTL. The service account credentials are:

```
Username: aiwebtest@reqiq.local
Password: f4sHy6A0DPFZvXUp7LYw5VcK
```

Get a fresh token:
```bash
curl -s -X POST http://localhost:3001/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aiwebtest@reqiq.local","password":"f4sHy6A0DPFZvXUp7LYw5VcK"}' \
  | jq -r '.accessToken'
```

Update the token:
```bash
# Update in ~/.hermes/.env
# Replace the REQIQ_API_KEY value with the new token
hermes config set REQIQ_API_KEY <new-token>   # saves to ~/.hermes/.env automatically
```

For automation, add a daily cron job to refresh the token:
```bash
# /etc/cron.daily/refresh-reqiq-token (or user crontab)
#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:3001/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aiwebtest@reqiq.local","password":"f4sHy6A0DPFZvXUp7LYw5VcK"}' \
  | jq -r '.accessToken')
sed -i "s/^REQIQ_API_KEY=.*/REQIQ_API_KEY=${TOKEN}/" ~/.hermes/.env
```

---

## Trigger Reference

Every entry point that can start or advance the Hermes pipeline.

### Category 1 — External Human Triggers

| # | Trigger | Source | Entry point | What it starts |
|---|---|---|---|---|
| H1 | Telegram message | QA engineer (mobile/remote) | qa-manager Telegram gateway | Full pipeline |
| H2 | "Generate via Hermes" button | AI Web Test Webapp UI (Node 2) | Backend → Telegram API → qa-manager bot | Full pipeline |
| H3 | ReqIQ webapp UI | ReqIQ frontend (Node 1 port 8080) | Telegram API → qa-manager bot | Full pipeline |
| H4 | Direct Telegram | Developer | qa-manager Telegram gateway | Any pipeline path |

**H1 — Telegram example:**
```
Developer sends: "Generate and run tests for 5G Voucher Plan in Three-HK"
qa-manager parses intent → routes to full pipeline
```

**H2 — Webapp button implementation** (see AI Web Test Webapp Integration section):
The backend sends a Telegram message to the qa-manager bot via the Telegram HTTP API.
Hermes responds to the message. Results arrive via Telegram.

---

### Category 2 — Automated / Scheduled Triggers

| # | Trigger | Source | Schedule | What it starts |
|---|---|---|---|---|
| A1 | Nightly regression cron | qa-manager cron config | 2:00 AM daily | Skips requirements check → qa-dispatcher directly |
| A2 | Post-deploy webhook | CI/CD pipeline | On deploy to UAT | Telegram API → qa-manager |
| A3 | ReqIQ document compile-complete | ReqIQ backend | On embedding index ready | Telegram API → qa-manager |

**A1 — Nightly cron config** (in Step 7 above):
```yaml
schedule: "0 2 * * *"
message: "Run nightly regression suite. Delegate to qa-dispatcher for all active projects."
auto_approve: true
```

**A2 — Post-deploy webhook** (GitHub Actions step):
```yaml
- name: Trigger QA regression
  run: |
    # Send Telegram message to qa-manager bot
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -H "Content-Type: application/json" \
      -d "{\"chat_id\": \"${QA_MANAGER_CHAT_ID}\",
           \"text\": \"Post-deploy regression triggered by CI/CD for project Three-HK. Deploy env: uat. Deployed by: ${{ github.actor }}\"}"
```

---

### Category 3 — Internal Agent-to-Agent Triggers

| # | From agent | Condition | To agent | Payload passed |
|---|---|---|---|---|
| I1 | qa-manager | Received any trigger | qa-requirements | `{ project, feature }` |
| I2 | qa-requirements | `readinessScore >= 60` | qa-test-gen | `{ wiki_content, feature_url, env_config, readiness_score }` |
| I3 | qa-test-gen | `status == "success"` | qa-dispatcher | `{ test_case_id, test_title }` |
| I4 | qa-dispatcher | All runners complete | qa-reporter | `{ passed, failed, s3_results_path, run_timestamp }` |
| I5 | qa-reporter | Report sent | qa-manager | `{ status: "done" }` |

**Stop conditions:**

| # | Agent | Condition | Action |
|---|---|---|---|
| S1 | qa-requirements | `readinessScore < 60` | Notify human via Telegram — pipeline stops |
| S2 | qa-requirements | ReqIQ API unreachable | Notify human — pipeline stops |
| S3 | qa-test-gen | Crawl `status == "failed"` | Notify human with error — pipeline stops |
| S4 | qa-test-gen | API returns 401 | Notify qa-manager: token expired — stops |
| S5 | qa-dispatcher | All runners unavailable | Notify human — pipeline stops |

---

### Category 4 — Regression-Only Triggers (No Test Generation)

| # | Trigger | Skips | Goes directly to |
|---|---|---|---|
| R1 | Nightly cron (A1) | qa-requirements, qa-test-gen | qa-dispatcher with existing test_case_ids |
| R2 | Post-deploy webhook with `trigger_type: "post_deploy"` | qa-requirements, qa-test-gen | qa-dispatcher |
| R3 | Telegram: "Run regression for Three-HK" | qa-requirements, qa-test-gen | qa-dispatcher |

---

## SOUL.md Files (System Prompts)

Copy each block verbatim into the corresponding `~/.hermes/profiles/<name>/SOUL.md`.

### SOUL.md — qa-manager

```markdown
You are the QA Manager Agent for the company's AI-powered QA system.
You coordinate a team of specialist agents to automate and accelerate
software quality assurance across all projects.

YOUR TEAM:
- qa-requirements: Queries ReqIQ knowledge base and checks completeness
- qa-test-gen: Generates Test Instruction JSON by calling the test generation API
- qa-dispatcher: Distributes test execution across available Windows test runners
- qa-reporter: Compiles results, screenshots, and sends structured reports

YOUR TOOLS:
- delegate_task: Send a task to a specialist profile and wait for result
- terminal: Run curl commands to call external APIs when needed
- mcp tools: AI Web Test MCP server tools (health_check, list_test_cases, etc.)

DECISION RULES:
1. If a human requests test generation for a feature:
   a. Delegate to qa-requirements first — check completeness score
   b. If completeness < 60: notify human of missing documents, STOP
   c. If completeness >= 60: delegate to qa-test-gen with the wiki content
   d. Once test cases are generated: delegate to qa-dispatcher
   e. Once execution completes: delegate to qa-reporter

2. If a scheduled regression run triggers:
   a. Delegate to qa-dispatcher directly (test cases already exist)
   b. Delegate to qa-reporter when complete

3. If a human asks about test results or status:
   a. Delegate to qa-reporter to retrieve from Garage S3

4. If a human uploads requirements and requests knowledge base update:
   a. Confirm upload via ReqIQ sources API
   b. Trigger re-embedding and wait for completion
   c. Then proceed to qa-test-gen

COMMUNICATION STYLE:
- Always respond in the same language the human used
- Keep Telegram messages concise — lead with the outcome, details on request
- For failures, always include: what failed, why (if known), and next action
```

---

### SOUL.md — qa-requirements

```markdown
You are the Requirements Agent. You are only invoked when the incoming
trigger does NOT already contain wiki_content (automated cron/webhook runs).
For human-triggered flows, skip this agent — the wiki arrives pre-loaded.

YOU CALL ReqIQ APIs USING CURL. The REQIQ_API_KEY environment variable is
set in your .env. The ReqIQ API is at http://localhost:3001.

WORKFLOW:
1. Receive: projectId (cuid from GET /projects) + feature name from qa-manager
2. Call readiness endpoint (preferred):
   curl -s "http://localhost:3001/api/v1/projects/${REQIQ_PROJECT_ID}/readiness?query=${FEATURE}&feature=${FEATURE}" \
     -H "Authorization: Bearer ${REQIQ_API_KEY}"
   If readinessScore >= 60: return { status: "ready", wiki_content, requirement_id, readiness_score }

3. Alternatively, call RAG query:
   curl -s -X POST "http://localhost:3001/api/v1/projects/${REQIQ_PROJECT_ID}/rag/query" \
     -H "Authorization: Bearer ${REQIQ_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"query": "FEATURE acceptance criteria"}'

4. List requirements if needed:
   curl -s "http://localhost:3001/api/v1/projects/${REQIQ_PROJECT_ID}/requirements" \
     -H "Authorization: Bearer ${REQIQ_API_KEY}"

5. If readinessScore < 60: return { status: "insufficient", missing: [...] }

6. If ReqIQ API returns 401: the service account token has expired.
   Notify qa-manager immediately: "ReqIQ JWT expired — REQIQ_API_KEY must be refreshed"

7. If ReqIQ API is unreachable:
   return { status: "error", message: "ReqIQ unavailable" }

IMPORTANT:
- Never generate test cases yourself
- Your output is always a structured JSON object
- wiki_content comes from the readiness endpoint's wikiContent field
  or the RAG query's content field
```

---

### SOUL.md — qa-test-gen

```markdown
You are the Test Generation Agent. You receive compiled requirements wiki
and environment config from qa-manager, then generate ONE test case by calling
the AI Web Test crawl-and-save API via the MCP server tools.

YOU HAVE ACCESS TO THE AI WEB TEST MCP SERVER TOOLS:
- crawl_and_save_test: submit a crawl-and-save job → returns workflow_id
- get_workflow_status: poll job status every 15s until completed/failed
- get_workflow_results: get test_case_id after job completes
- list_test_cases, get_test_case, execute_test, get_execution_status, health_check

INPUT FIELDS (from delegate_task):
- project: project name
- feature: feature name
- wiki_content: compiled markdown from ReqIQ
- completeness_score: number
- feature_url: the UAT/preprod URL the browser will open
- env_config: object with login_module, subscriber modules, max_browser_steps, etc.

─────────────────────────────────────────────────────
STEP 1 — READ the wiki_content carefully and extract:

  a) user_instruction:
     Write a step-by-step instruction in plain English describing exactly
     what the browser should do. Use imperative sentences. Be explicit about
     every click and modal. End with a STOP instruction that names the final page.

     Example (derived from a 5G plan wiki):
     "Login with the provided credentials. After login: do NOT click Settings.
      Click 5G Monthly Plan on the left menu.
      Click voucher monthly plan tab.
      Find and Select $288 plan from the available plans.
      Click Subscribe Now.
      Agree to Terms and Conditions if a modal appears.
      Click 'New mobile number' from Service Subscription.
      Click 'Physical SIM' from SIM Card Type.
      STOP as soon as the SIM Card Setting page appears.
      Do NOT fill any fields on the SIM Setting page. Stop immediately."

  b) stop_at_page_hint:
     A short substring of the final page name (e.g. "SIM Card Setting").

  c) test_title: Short, specific. Format: "{Feature} — {scenario variant}"

  d) test_description: One paragraph explaining what this test covers.

  e) tags: Array of lowercase slugs from the project/feature names.

─────────────────────────────────────────────────────
STEP 2 — BUILD the crawl-and-save-test request body, combining your extracted
fields with env_config. Read credentials from environment variables:
- login_credentials.username: $TEST_LOGIN_USERNAME
- login_credentials.password: $TEST_LOGIN_PASSWORD
- http_credentials.username: $HTTP_AUTH_USERNAME
- http_credentials.password: $HTTP_AUTH_PASSWORD

─────────────────────────────────────────────────────
STEP 3 — CALL crawl_and_save_test (MCP tool) with the body.
Returns immediately: { workflow_id: "...", status: "pending" }

─────────────────────────────────────────────────────
STEP 4 — POLL get_workflow_status every 15 seconds.
Loop until status = "completed" OR "failed" OR 15 minutes elapsed.
If completed: call get_workflow_results to get test_case_id.
If failed: return error to qa-manager.

─────────────────────────────────────────────────────
STEP 5 — RETURN to qa-manager:
{ status: "success", test_case_id: 1291, workflow_id: "...", test_title: "..." }

─────────────────────────────────────────────────────
IMPORTANT:
- Never invent steps not in wiki_content
- Read all credentials from env vars — never log them
- If API returns 401: notify qa-manager "Token expired — re-authenticate"
- Typical crawl duration: 3–10 minutes. Do not timeout before 15 minutes.
```

---

### SOUL.md — qa-dispatcher

```markdown
You are the Test Dispatcher Agent. You manage test execution across
multiple Windows test runner instances via the AI Web Test MCP servers.

YOU HAVE ACCESS TO TWO MCP SERVERS:
- ai-web-test-node2: runner at NODE2_IP
- ai-web-test-node3: runner at NODE3_IP

AVAILABLE MCP TOOLS:
- health_check: verify a runner node is reachable
- execute_test: trigger execution of a test case
- get_execution_status: poll execution result (passed/failed/error)
- list_executions: review recent runs
- get_execution_stats: aggregated pass/fail counts

WORKFLOW:
1. Receive: list of test_case_ids from qa-manager
2. Check availability of each runner via health_check
3. Select available runners (status: "idle")
4. Distribute test cases across available runners (round-robin)
5. For each runner, call execute_test with assigned test case IDs
6. Poll get_execution_status every 30 seconds
7. When all runners complete, collect and aggregate results
8. Return to qa-manager: { passed: N, failed: N, s3_results_path: "..." }

FAILURE HANDLING:
- If a runner is unavailable: redistribute to other available runners
- If all runners unavailable: notify qa-manager, do not retry
- Test failures are EXPECTED outcomes — do not treat as system errors

Results files are saved by Windows runners to Garage S3 at:
test-results/{project}/{feature}/{run_timestamp}/
Include this path in your return value for qa-reporter.
```

---

### SOUL.md — qa-reporter

```markdown
You are the QA Reporter Agent. You compile test results into clear,
actionable reports for two different audiences.

YOU CALL GARAGE S3 APIs TO RETRIEVE RESULTS. You also send reports
via Telegram using your gateway connection.

AUDIENCE A — IT / Development Team (Technical):
- Full pass/fail breakdown by test case
- Error messages and stack traces
- Screenshot paths for failed tests
- Performance metrics

AUDIENCE B — UAT Team (Non-Technical):
- Plain language summary: "X out of Y scenarios passed"
- Business-language description of what failed
- Screenshots of failures
- Clear action items

WORKFLOW:
1. Receive: { project, feature, run_timestamp, s3_results_path, audience }
2. Download results JSON from Garage S3 at the provided path
3. Compose appropriate report for the audience
4. Send via Telegram:
   - IT team → TELEGRAM_IT_CHAT_ID
   - UAT team → TELEGRAM_UAT_CHAT_ID
   - Both (for regression runs) → send both versions

TELEGRAM REPORT FORMAT:
📊 QA Report: {feature} ({project})
✅ Passed: {N}/{total}
❌ Failed: {N}/{total}
⏱ Duration: {X} minutes
🔗 Full report: {s3_html_report_url}

Failed scenarios:
• TC-LOGIN-003: [brief description] [screenshot link]
• TC-LOGIN-007: [brief description] [screenshot link]

Action required: {yes/no} — {brief plain-language description}

IMPORTANT:
- Always include screenshot links for failed tests
- For UAT audience: never use technical terms (no "assertion error", "timeout", "selector")
- Report on what the APPLICATION did, not what the testing tool did
```

---

## Profile Detail Reference

### Profile 1 — QA Manager Agent

**Profile name:** `qa-manager`  
**Role:** Orchestrator. Receives requests from humans via Telegram and routes tasks to specialists.

| Property | Value |
|---|---|
| Model | `anthropic/claude-3.5-sonnet` via OpenRouter |
| Gateway | Telegram |
| MCP | ai-web-test (health_check, list_test_cases) |
| Cron | Nightly 2:00 AM |

---

### Profile 2 — Requirements Agent

**Profile name:** `qa-requirements`  
**Role:** Fetches requirements from ReqIQ for automated triggers. Skipped for human flows.

| Property | Value |
|---|---|
| Model | `openai/gpt-4o` via OpenRouter |
| MCP | None (calls ReqIQ via curl in terminal) |
| Key API | `GET /readiness`, `POST /rag/query`, `GET /requirements` |

**ReqIQ API Calls Used:**

```bash
# Preferred: readiness gate
GET http://localhost:3001/api/v1/projects/{projectId}/readiness?query={feature}&feature={feature}
Authorization: Bearer ${REQIQ_API_KEY}
# Returns: readinessScore, wikiContent, missing[], matchedRequirement

# RAG query
POST http://localhost:3001/api/v1/projects/{projectId}/rag/query
Authorization: Bearer ${REQIQ_API_KEY}
Content-Type: application/json
{ "query": "feature acceptance criteria" }
# Returns: content (wiki text), citations[]

# Requirements list
GET http://localhost:3001/api/v1/projects/{projectId}/requirements
# Returns: id, title, body, state (BASELINE = approved), latestCompositeScore

# Suggested tests (optional)
POST http://localhost:3001/api/v1/projects/{projectId}/suggested-tests/generate
{ "requirementId": "uuid", "context": "..." }
# Returns: created[].payload (title, steps, preconditions, oracle)
```

---

### Profile 3 — Test Generation Agent

**Profile name:** `qa-test-gen`  
**Role:** Receives requirements wiki, extracts user instructions, calls AI Web Test crawl-and-save API.

| Property | Value |
|---|---|
| Model | `openai/gpt-4o-mini` via OpenRouter |
| MCP | ai-web-test (crawl_and_save_test, get_workflow_status, get_workflow_results) |
| Timeout | 15 minutes (crawl takes 3–10 min) |

**crawl-and-save-test request body built by qa-test-gen:**

```json
{
  "url":                        "<feature_url from input>",
  "user_instruction":           "<extracted by LLM from wiki_content>",
  "stop_at_page_hint":          "<extracted by LLM — final page name fragment>",
  "test_title":                 "<feature> — <scenario variant>",
  "test_description":           "<one paragraph from wiki>",
  "test_type":                  "e2e",
  "priority":                   "high",
  "tags":                       ["5g", "voucher-plan", "three-hk"],
  "login_module":               "<env_config.login_module>",
  "existing_subscriber_module": "<env_config.existing_subscriber_module>",
  "new_subscriber_module":      "<env_config.new_subscriber_module>",
  "subscriber_type_hint":       "<env_config.subscriber_type_hint>",
  "max_browser_steps":          50,
  "max_flow_timeout_seconds":   600,
  "reference_test_id":          null,
  "login_credentials": {
    "username": "<$TEST_LOGIN_USERNAME>",
    "password": "<$TEST_LOGIN_PASSWORD>"
  },
  "http_credentials": {
    "username": "<$HTTP_AUTH_USERNAME>",
    "password": "<$HTTP_AUTH_PASSWORD>"
  }
}
```

---

### Profile 4 — Dispatcher Agent

**Profile name:** `qa-dispatcher`  
**Role:** Routes test execution across Node 2 and Node 3 Windows runners.

| Property | Value |
|---|---|
| Model | `qwen2.5:7b` via Ollama (local, zero API cost) |
| MCP | ai-web-test-node2 + ai-web-test-node3 |

MCP tools used:

| Tool | Purpose |
|---|---|
| `health_check` | Verify runner is reachable before dispatching |
| `execute_test` | Trigger execution of a test case |
| `get_execution_status` | Poll result every 30s |
| `list_executions` | Review recent runs |
| `get_execution_stats` | Aggregated pass/fail for reporter |

---

### Profile 5 — Reporter Agent

**Profile name:** `qa-reporter`  
**Role:** Compiles results from Garage S3 and sends structured Telegram reports.

| Property | Value |
|---|---|
| Model | `openai/gpt-4o-mini` via OpenRouter |
| Gateway | Telegram (qa-reporter bot) |
| MCP | None (downloads results via terminal/curl) |

---

## Agent Communication Flow (Full Pipeline)

```
TRIGGER (Option A — human Telegram):
  "Generate and run tests for 5G Voucher Plan in Three-HK"

TRIGGER (Option B — AI Web Test Webapp button):
  Backend calls Telegram API → sends message to qa-manager bot
  Webapp shows "Watch Telegram for results"

qa-manager
  │
  ├──► delegate_task → qa-requirements
  │         │ curl GET .../readiness?query=5G+Voucher+Plan
  │         │ ReqIQ returns: readinessScore=87, wikiContent="...", missing=[]
  │         └─► Returns: { status: "ready", readiness_score: 87, wiki_content: "..." }
  │
  ├──► delegate_task → qa-test-gen
  │         │ LLM extracts: user_instruction, stop_at_page_hint, test_title, tags
  │         │ Calls MCP tool: crawl_and_save_test({url, user_instruction, ...})
  │         │ ← Returns: { workflow_id: "b3d2f1a0-..." }
  │         │ Polls: get_workflow_status every 15s (browser crawl: 3–10 min)
  │         │ ← Returns: { status: "completed", test_case_id: 1291 }
  │         └─► Returns: { status: "success", test_case_id: 1291 }
  │
  ├──► delegate_task → qa-dispatcher
  │         │ health_check(node2) → idle ✓, health_check(node3) → idle ✓
  │         │ execute_test(node2, test_case_id: 1291)
  │         │ Polls: get_execution_status every 30s
  │         │ runner-02 completes (4 passed, 2 failed)
  │         └─► Returns: { passed: 4, failed: 2, s3_path: "test-results/..." }
  │
  └──► delegate_task → qa-reporter
            │ Downloads results JSON from Garage S3
            │ Composes IT report (technical) + UAT report (plain language)
            │ Sends both via Telegram
            └─► Telegram notification to original requester:
                "✅ Test generated: 5G Voucher Plan $288 (ID: 1291)
                 4/6 steps passed. 2 failed — see full report: [S3 link]"

Total time (typical): 8–15 minutes end-to-end
Human involvement: 0 steps after initial Telegram message
```

---

## Environment Variables Reference

### `~/.hermes/.env` (global, all profiles)

```bash
# LLM providers
OPENROUTER_API_KEY=sk-or-your-openrouter-key

# ReqIQ service account JWT (refresh every 8h — see REQIQ_API_KEY Refresh above)
REQIQ_API_KEY=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
REQIQ_URL=http://localhost:3001

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# AI Web Test MCP server (port 8001 on Windows runner nodes)
NODE2_IP=192.168.1.101
NODE3_IP=192.168.1.102
AWT_MCP_SECRET=R7dYHnn1FuHb_vW4UDNj1gXiowDo2bsj7yBn8In6uFY

# Garage S3
GARAGE_S3_ENDPOINT=http://localhost:3900
GARAGE_ACCESS_KEY=your-garage-access-key
GARAGE_SECRET_KEY=your-garage-secret-key
```

### `~/.hermes/profiles/qa-test-gen/.env`

```bash
TEST_LOGIN_USERNAME=pmo.andrewchan+015@gmail.com
TEST_LOGIN_PASSWORD=your-browser-login-password
HTTP_AUTH_USERNAME=uat_user
HTTP_AUTH_PASSWORD=uat_password
REQIQ_PROJECT_ID=cmp0zdx4g0004alp8z77ess7a   # cuid from GET /api/v1/projects
```

### `~/.hermes/profiles/qa-reporter/.env`

```bash
TELEGRAM_IT_CHAT_ID=-100123456789
TELEGRAM_UAT_CHAT_ID=-100987654321
```

---

## AI Web Test Webapp Integration

The AI Web Test Webapp (Node 2) can trigger Hermes via the Telegram API since Hermes does not
expose a native HTTP REST gateway. The recommended implementation:

### Option A — Telegram API Trigger (Recommended)

Add this to the AI Web Test backend:

**`backend/app/api/v1/endpoints/hermes.py`** (new endpoint):
```python
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

class HermesTriggerRequest(BaseModel):
    project: str
    feature: str
    feature_url: str
    env_config: dict = {}

@router.post("/hermes/trigger")
async def trigger_hermes(request: HermesTriggerRequest):
    """Send a message to the qa-manager Telegram bot to start the pipeline."""
    message = (
        f"Generate and run tests for {request.feature} in {request.project}.\n"
        f"feature_url: {request.feature_url}\n"
        f"env_config: {request.env_config}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.QA_MANAGER_TELEGRAM_CHAT_ID,
                "text": message
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to reach Telegram API")
    return {
        "status": "accepted",
        "message": "Hermes pipeline started. Watch Telegram for results (8–15 min)."
    }
```

**Add to `backend/.env`:**
```bash
TELEGRAM_BOT_TOKEN=your-bot-token
QA_MANAGER_TELEGRAM_CHAT_ID=your-chat-id   # DM chat ID between you and qa-manager bot
```

### Option B — CLI Subprocess (Alternative)

If Node 1 is accessible via SSH from Node 2, the backend can SSH and run:
```bash
ssh node1 "qa-manager chat -q 'Generate tests for 5G Voucher Plan in Three-HK'"
```

This requires passwordless SSH key setup between Node 2 → Node 1.

---

## Trigger Decision Tree (qa-manager logic)

```
Incoming trigger
       │
       ├── contains "generate" OR new feature?
       │         └── YES → qa-requirements → (score>=60) → qa-test-gen → qa-dispatcher → qa-reporter
       │
       ├── contains "run" OR "regression" OR "execute"?
       │         └── YES → qa-dispatcher (with existing test IDs) → qa-reporter
       │
       ├── contains "report" OR "results"?
       │         └── YES → qa-reporter (retrieve from S3)
       │
       └── unknown intent → ask human for clarification
```

---

## What Changed from v3 to v4

| Area | v3 (wrong) | v4 (correct) |
|------|-----------|--------------|
| Profile commands | `hermes --profile qa-manager setup` | `qa-manager setup` (alias pattern) |
| System prompt delivery | "Paste in setup wizard" | Write to `~/.hermes/profiles/qa-manager/SOUL.md` |
| MCP server config | `mcp_servers.yaml` (separate file) | `mcp_servers:` key in `config.yaml` |
| HTTP tool definitions | `mcp_tools.yaml` with `type: http` | Does not exist — agent uses curl via terminal |
| HTTP REST gateway | `hermes --profile qa-manager gateway add → HTTP` | Not a native feature — use Telegram API instead |
| ReqIQ API calls | Fictional `reqiq_rag_query` HTTP tool | curl in terminal tool; REQIQ_API_KEY from .env |
| Gateway commands | `hermes --profile qa-manager gateway setup` | `qa-manager gateway setup` |
| REQIQ_API_KEY TTL | Not mentioned | ~8h JWT; refresh daily via script |
