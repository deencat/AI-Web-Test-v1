# 4-Agent E2E Real Test – Run Guide

This guide explains how to run the **real** 4-agent E2E test (`test_four_agent_e2e_real.py`), which uses live web crawling, LLM calls, and test execution.

---

## Quick start

1. **Activate venv** (from repo root or `backend/`):
   ```powershell
   cd backend
   .\venv\Scripts\activate
   ```
2. **Set required env vars** (see below). At minimum you need Azure OpenAI for the agents.
3. **Run the test** (use `-s` for real-time logs):
   ```powershell
   python -u -m pytest tests/integration/test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
   ```

Or use the helper script (checks env and runs the test):

```powershell
cd backend
.\scripts\run_e2e_real.ps1
```

---

## Environment variables

### Required for 4-agent E2E

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | (from Azure portal) |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://your-resource.openai.azure.com` |
| `AZURE_OPENAI_MODEL` | Deployment name | `ChatGPT-UAT` |

These are used by ObservationAgent (browser-use LLM), RequirementsAgent, AnalysisAgent, and EvolutionAgent.

### Optional – test behaviour

| Variable | Description | Example |
|----------|-------------|---------|
| `USER_INSTRUCTION` | Goal for the flow (enables multi-page flow crawling) | `Complete purchase flow for '5G寬頻數據無限任用' plan` |
| `LOGIN_EMAIL` | Login email **on the test website** | `user@example.com` or `user+010@gmail.com` |
| `LOGIN_PASSWORD` | Login password **on the test website** | (your password) |

### Optional – OTP via Gmail

If the flow requires OTP and the agent should open Gmail to get the code:

| Variable | Description | Example |
|----------|-------------|---------|
| `GMAIL_EMAIL` | Gmail account used **only for Gmail** (inbox access) | `user@gmail.com` |
| `GMAIL_PASSWORD` | Gmail password or app password | (your Gmail password) |

- If you **omit** `GMAIL_EMAIL` / `GMAIL_PASSWORD`, the agent will still use `LOGIN_EMAIL` / `LOGIN_PASSWORD` for Gmail by **stripping the `+...` part** from the email (see below).
- For flows that send OTP to email, you typically want to set `GMAIL_EMAIL` / `GMAIL_PASSWORD` explicitly so the agent can log into Gmail and read the code.

---

## Gmail “+” alias behaviour

Many setups use one Gmail with **aliases** for different test users, e.g.:

- **On the test website:** `pmo.andrewchan+010@gmail.com` (full address).
- **In Gmail:** you still log in as `pmo.andrewchan@gmail.com` (same inbox).

The code does the following:

- **Test website login:** always uses the **full** address (e.g. `pmo.andrewchan+010@gmail.com`) from `LOGIN_EMAIL`.
- **Gmail login (for OTP):**
  - If `GMAIL_EMAIL` and `GMAIL_PASSWORD` are set → use those.
  - If only `LOGIN_EMAIL` / `LOGIN_PASSWORD` are set → the **base** email is derived by **removing everything from `+` to `@`** and that base email + `LOGIN_PASSWORD` are used for Gmail.

So for `pmo.andrewchan+010@gmail.com`:

- Test site: `pmo.andrewchan+010@gmail.com`
- Gmail: `pmo.andrewchan@gmail.com` (and same password or the one in `GMAIL_PASSWORD` if set).

---

## Security

- **Do not commit `.env` or real credentials.** The repo’s `backend/.gitignore` includes `.env`.
- Prefer setting env vars in the shell or in a local script that is not committed, rather than hardcoding.

---

## Example: PowerShell with all variables

```powershell
# Required (Azure OpenAI)
$env:AZURE_OPENAI_API_KEY = "your-azure-api-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com"
$env:AZURE_OPENAI_MODEL = "ChatGPT-UAT"

# Optional: user instruction (enables multi-page flow)
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"

# Optional: test website login
$env:LOGIN_EMAIL = "pmo.andrewchan+010@gmail.com"
$env:LOGIN_PASSWORD = "your-test-site-password"

# Optional: Gmail (for OTP) – use base address or same as LOGIN_EMAIL if no +
$env:GMAIL_EMAIL = "pmo.andrewchan@gmail.com"
$env:GMAIL_PASSWORD = "your-gmail-password"

# Run from backend with venv active
python -u -m pytest tests/integration/test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

---

## Logs and duration

- **Log file:** each run writes to `backend/logs/test_four_agent_e2e_YYYYMMDD_HHMMSS.log`.
- **Duration:** typically in the 45s–10 min range depending on flow (e.g. OTP and multi-page flows take longer).
- Use **`-s`** so pytest does not capture stdout and you see logs in real time.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Azure/LLM errors | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_MODEL` set and valid. |
| OTP step never completes | Set `GMAIL_EMAIL` and `GMAIL_PASSWORD` (or ensure `LOGIN_EMAIL` uses a form that strips `+...` for Gmail). |
| Encoding errors on Windows | The test forces UTF-8 for stdout/stderr; if you still see errors, run in a terminal that supports UTF-8. |
| No real-time logs | Run with `-s`: `pytest ... -v -s`. |

For more on user instructions and login credentials, see:

- [USER_INSTRUCTION_USAGE.md](./USER_INSTRUCTION_USAGE.md)
- [LOGIN_CREDENTIALS_USAGE.md](./LOGIN_CREDENTIALS_USAGE.md)

---

## CI (optional)

A GitHub Actions workflow runs this E2E test on demand or on a schedule: `.github/workflows/e2e-real.yml`. It does **not** run on every push or PR. To enable it, add these repository secrets:

- **Required:** `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`
- **Optional:** `AZURE_OPENAI_MODEL` (default `ChatGPT-UAT`), `E2E_USER_INSTRUCTION`, `E2E_LOGIN_EMAIL`, `E2E_LOGIN_PASSWORD`, `E2E_GMAIL_EMAIL`, `E2E_GMAIL_PASSWORD`

Logs are uploaded as artifacts when the job runs.
