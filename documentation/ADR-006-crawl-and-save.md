# Architecture Decision Records — Crawl & Save CDP Proxy Bypass for Corporate HTTP_PROXY Environments

**Document ID:** ADR-006  
**Component:** Crawl & Save / ObservationAgent / browser-use CDP Integration  
**Status:** Accepted  
**Date:** June 16, 2026  
**Author:** Developer B  
**Related Files:**
- `backend/app/utils/proxy_bypass.py`
- `backend/agents/observation_agent.py`
- `backend/app/services/stagehand_service.py`
- `backend/app/api/v2/endpoints/crawl_and_save.py`
- `backend/app/services/orchestration_service.py`
- `backend/app/utils/http_auth_credentials.py`
- `backend/mcp_server.py`
- `documentation/ADR-004-agent-workflow.md` (cross-reference — HTTP Basic Auth)
- `backend/tests/test_proxy_bypass.py`
- `backend/tests/test_stagehand_service_proxy_bypass.py`
- `backend/tests/agents/test_observation_agent_http_credentials.py`

---

## Context

### Incident: Test ID #1390 — Crawl & Save Failure on Three HK UAT

A user ran **crawl and save** via `POST /api/v2/crawl-and-save-test` with:

| Field | Value |
|---|---|
| URL | `https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en` |
| Instruction | "Subscribe a $458 world plan" |

The workflow failed before any page navigation or HTTP Basic Auth setup:

```
Failed to setup CDP connection: proxy rejected connection: HTTP 403
websockets.exceptions.InvalidProxyStatus: proxy rejected connection: HTTP 403
```

**Stack trace path:** `ObservationAgent._prime_browser_session_http_auth()` → `browser.start()` → browser-use `BrowserSession.connect()` attempts a CDP WebSocket connection to local Chromium at `127.0.0.1`, which is routed through the system `HTTP_PROXY`.

### Root Cause

On Windows corporate machines, `HTTP_PROXY` / `HTTPS_PROXY` environment variables are injected into the backend process. browser-use connects to local Chromium's CDP endpoint (`127.0.0.1:<port>`) via the `websockets` library, which honours those proxy settings. The corporate HTTP proxy rejects loopback destinations with **HTTP 403** before any browser session is established.

This is **not** an HTTP Basic Auth issue (see [ADR-004](ADR-004-agent-workflow.md)). CDP connection fails **before** `_setup_cdp_server_auth()` can register `Fetch.authRequired` handlers.

### Prior Art in Codebase

`stagehand_service.py` already contained an inline `_ensure_loopback_no_proxy()` helper for Stagehand CDP connections. **ObservationAgent** — used by crawl-and-save — did not call an equivalent bypass, so the same corporate-proxy failure affected browser-use paths only.

### Crawl & Save Flow (Affected Path)

```
POST /api/v2/crawl-and-save-test
  └─ crawl_and_save_test()          [crawl_and_save.py]
       └─ _run_crawl_and_save()     [background worker]
            ├─ http_credentials_for_url(url)  → auto-inject Three HK UAT creds
            ├─ OrchestrationService._create_agents() → ObservationAgent
            └─ ObservationAgent.execute_task()
                 └─ _execute_multi_page_flow_crawling()   [browser-use path — user_instruction present]
                      └─ _prime_browser_session_http_auth()
                           └─ browser.start()  ← CDP WebSocket via HTTP_PROXY → 403
```

**MCP entry point:** `crawl_and_save_test` tool in `backend/mcp_server.py` calls the same crawl-and-save workflow.

Three HK UAT URLs receive HTTP credentials automatically via `http_credentials_for_url()` (documented in ADR-004). Proxy bypass and HTTP Basic Auth are **orthogonal** — both are required for successful crawl-and-save on corporate Windows machines targeting Three HK UAT.

---

## Decision

### ADR-006-1: Shared `ensure_loopback_no_proxy()` Utility for All Local CDP Traffic

**Decision:** Extract loopback proxy bypass into a single shared utility at `backend/app/utils/proxy_bypass.py` and use it from every code path that opens a local CDP WebSocket connection.

**Implementation** — `ensure_loopback_no_proxy()`:

```python
def ensure_loopback_no_proxy() -> None:
    required_hosts = ("127.0.0.1", "localhost", "::1")
    # Merge required_hosts into both NO_PROXY and no_proxy, preserving existing entries
    ...
    os.environ["NO_PROXY"] = merged_value
    os.environ["no_proxy"] = merged_value
    logger.info("Added loopback hosts to NO_PROXY for local CDP traffic")
```

**Behaviour:**
- **Idempotent** — safe to call multiple times; skips work when all three hosts are already present.
- **Preserves existing entries** — corporate `NO_PROXY` allowlists (e.g. `example.com`) are not overwritten.
- **Sets both casings** — `NO_PROXY` and `no_proxy` — because different libraries read different env var names on Windows.
- **Logs on change** — INFO log when hosts are added, silent when already configured.

**Consequences**

**Positive**
- Single source of truth for loopback bypass; eliminates duplicated inline logic.
- Stagehand and ObservationAgent share identical behaviour.
- No runtime dependency on proxy library internals — pure `os.environ` mutation before CDP connect.

**Negative**
- Mutates process-global environment; concurrent requests in the same worker share the updated `NO_PROXY`. This is acceptable because loopback bypass is universally correct for local CDP and idempotent.
- Does not unset `HTTP_PROXY` / `HTTPS_PROXY` themselves — relies on `NO_PROXY` precedence, which is the standard convention.

**Alternatives Considered**

| Alternative | Verdict |
|---|---|
| Inline duplicate in ObservationAgent (copy from Stagehand) | Rejected — violates DRY; divergent copies risk drift |
| Unset `HTTP_PROXY` globally at process start | Rejected — breaks legitimate outbound proxy use for LLM/API calls |
| Per-connection `proxies=None` in websockets | Rejected — browser-use does not expose WebSocket proxy config; env-level bypass is the only reliable hook |
| Corporate proxy PAC file exemption | Rejected — not controllable from application code; env bypass is portable |

---

### ADR-006-2: Call Bypass at browser-use Flow Entry AND Before `browser.start()` in Auth Priming

**Decision:** Call `ensure_loopback_no_proxy()` at two points in ObservationAgent:

1. **Flow entry** — start of `_execute_multi_page_flow_crawling()`, before `Browser()` construction. Covers crawl-and-save, generate-tests, and any other `user_instruction`-driven observation.
2. **Auth priming** — immediately before `browser.start()` in `_prime_browser_session_http_auth()`. Defence-in-depth for the CDP connection that ADR-004 requires before `Fetch.authRequired` registration.

**Why two call sites:**
- The flow-entry call protects all browser-use paths, including those without HTTP credentials (no auth priming).
- The pre-`start()` call guarantees bypass is applied at the exact moment CDP connects, even if a future caller invokes `_prime_browser_session_http_auth()` without going through `_execute_multi_page_flow_crawling()`.

**Consequences**

**Positive**
- Eliminates `proxy rejected connection: HTTP 403` on corporate Windows for crawl-and-save and all browser-use observation flows.
- Ordering is testable: `NO_PROXY` must contain loopback hosts **before** `browser.start()` is invoked.

**Negative**
- Redundant call when both paths execute (flow entry + auth priming). Cost is negligible — idempotent env check only.

---

### ADR-006-3: Traditional Playwright Path Does NOT Need Bypass

**Decision:** `_execute_traditional_crawling()` (activated when `user_instruction` is absent) does **not** call `ensure_loopback_no_proxy()`.

**Why:** The traditional path uses Playwright's `async_playwright()` launcher, which communicates with Chromium via subprocess stdio/pipes — not an HTTP CDP WebSocket routed through `HTTP_PROXY`. Corporate proxy injection does not affect this connection model.

**Consequences**
- **Positive:** No unnecessary env mutation for the simpler crawling path.
- **Negative:** If Playwright's connection model changes to HTTP CDP in a future version, this assumption must be revisited.

---

### ADR-006-4: Relationship to ADR-004 — Proxy Bypass Is Orthogonal to HTTP Basic Auth

**Decision:** Corporate proxy bypass (ADR-006) and HTTP Basic Auth via CDP `Fetch.authRequired` (ADR-004) are independent concerns that must both succeed for Three HK UAT crawl-and-save:

| Layer | ADR | When it runs | Failure symptom |
|---|---|---|---|
| CDP WebSocket connect | ADR-006 | `browser.start()` | `proxy rejected connection: HTTP 403` |
| HTTP Basic Auth challenge | ADR-004 | After CDP connect, on first navigation | `401` / page load failure |

**Three HK UAT crawl-and-save requires both:**
1. `ensure_loopback_no_proxy()` — CDP connects to local Chromium.
2. `http_credentials_for_url()` + `_setup_cdp_server_auth()` — preprod gate is cleared.

Neither subsumes the other. Fixing ADR-004 auth without ADR-006 bypass (or vice versa) leaves crawl-and-save broken on proxied corporate machines.

---

## Implementation Summary

| Method / Component | File | Role |
|---|---|---|
| `ensure_loopback_no_proxy()` | `proxy_bypass.py` | Shared util — merge loopback hosts into `NO_PROXY` / `no_proxy` |
| `_execute_multi_page_flow_crawling()` | `observation_agent.py` | Calls bypass at browser-use flow entry |
| `_prime_browser_session_http_auth()` | `observation_agent.py` | Calls bypass immediately before `browser.start()` |
| `_ensure_loopback_no_proxy` (re-export) | `stagehand_service.py` | Imports shared util; backward-compatible alias |
| `connect_to_existing_browser()` | `stagehand_service.py` | Calls bypass before Stagehand CDP connect |
| `crawl_and_save_test()` | `crawl_and_save.py` | API entry — dispatches background `_run_crawl_and_save()` |
| `_run_crawl_and_save()` | `crawl_and_save.py` | Builds ObservationAgent payload; auto-injects UAT creds |
| `http_credentials_for_url()` | `http_auth_credentials.py` | Resolves Three HK UAT credentials from URL |
| `crawl_and_save_test` | `mcp_server.py` | MCP tool wrapper for crawl-and-save workflow |

## Test Coverage

| Test | File | What is verified |
|---|---|---|
| `test_ensure_loopback_no_proxy_sets_required_hosts` | `test_proxy_bypass.py` | `127.0.0.1`, `localhost`, `::1` added to both env vars when absent |
| `test_ensure_loopback_no_proxy_preserves_existing_entries` | `test_proxy_bypass.py` | Pre-existing `NO_PROXY` entries (e.g. `example.com`) preserved |
| `test_stagehand_reexports_ensure_loopback_no_proxy` | `test_stagehand_service_proxy_bypass.py` | Stagehand `_ensure_loopback_no_proxy` is the shared util (re-export compat) |
| `TestCdpServerAuth::test_prime_browser_session_bypasses_proxy_before_browser_start` | `test_observation_agent_http_credentials.py` | Loopback hosts present in `NO_PROXY` **before** `browser.start()` is called |

**9 proxy-related tests passing** across the above files and related CDP/auth integration tests.

## Known Gaps / Technical Debt

| Gap | Description | Notes |
|---|---|---|
| `execution_service` CDP paths | Test execution uses `connect_over_cdp()` to `127.0.0.1:<port>` but does not yet call `ensure_loopback_no_proxy()` | Affects test **execution**, not crawl-and-save |
| `stagehand_service.initialize()` | Non-CDP-init path (launches its own browser) not yet covered | CDP connect path (`connect_to_existing_browser`) is covered |

## Consequences (Overall)

**Positive**
- Crawl-and-save works on corporate Windows machines with `HTTP_PROXY` injected.
- Shared utility reduces duplication and aligns Stagehand + ObservationAgent behaviour.
- Idempotent, low-overhead env mutation with no new dependencies.

**Negative**
- Process-global `NO_PROXY` mutation affects all concurrent requests in the worker (acceptable — loopback bypass is universally correct).
- Not all CDP code paths in the codebase are covered yet (see Known Gaps).

## Alternatives Considered (Overall)

| Alternative | Verdict |
|---|---|
| Document as operator workaround ("unset HTTP_PROXY before starting backend") | Rejected — poor UX; fails silently for non-technical users |
| Run backend in a subprocess with clean env per request | Rejected — high overhead; breaks shared browser/session pooling |
| Patch browser-use to pass `proxies=None` to websockets | Rejected — forks third-party library; env bypass is simpler and upgrade-safe |

## Status

**Accepted** — implemented and tested. Last updated June 16, 2026.

### What Was Fixed

1. **CDP proxy 403 on corporate Windows (ADR-006-1, ADR-006-2)** — `ensure_loopback_no_proxy()` shared utility ensures local CDP WebSocket traffic bypasses corporate HTTP proxies. ObservationAgent calls it at browser-use flow entry and before `browser.start()` in auth priming.

2. **Stagehand deduplication (ADR-006-1)** — Inline `_ensure_loopback_no_proxy()` in `stagehand_service.py` refactored to import the shared util (re-exported for backward compatibility).

3. **ADR-004 complement (ADR-006-4)** — Proxy bypass and HTTP Basic Auth are documented as orthogonal layers; both required for Three HK UAT crawl-and-save on proxied machines.

### Test Results

**9 proxy-related tests passing:**
- `test_proxy_bypass.py` — 2 tests (host injection, entry preservation)
- `test_stagehand_service_proxy_bypass.py` — 1 test (re-export compatibility)
- `test_observation_agent_http_credentials.py` — ordering test confirms bypass before `browser.start()`

**All tests green; ready for production.**
