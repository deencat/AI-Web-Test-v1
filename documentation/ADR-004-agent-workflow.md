# Architecture Decision Records — ObservationAgent HTTP Basic Auth for Preprod

**Document ID:** ADR-004  
**Component:** ObservationAgent / browser-use Integration  
**Status:** Accepted  
**Date:** March 13, 2026  
**Author:** Developer B  
**Related Files:**
- `backend/agents/observation_agent.py`
- `backend/app/schemas/workflow.py`
- `backend/app/api/v2/endpoints/observation.py`
- `backend/app/api/v2/endpoints/generate_tests.py`
- `backend/app/services/orchestration_service.py`
- `backend/tests/agents/test_observation_agent_http_credentials.py`
- `backend/tests/agents/test_observation_agent_browser_use.py`
- `frontend/src/features/agent-workflow/components/AgentWorkflowTrigger.tsx`

---

## Context

The ObservationAgent uses two execution paths:

1. **browser-use path** — activated when `user_instruction` is provided. An LLM-guided `BrowserSession` (from `browser_use` 0.12.x) navigates the target site and extracts UI elements.
2. **Traditional Playwright path** — activated when no `user_instruction` is provided. A raw Playwright browser context crawls pages up to `max_depth`.

Preprod and UAT environments (e.g. `https://wwwuat.three.com.hk/`) sit behind an HTTP Basic Auth gate. The server responds to every unauthenticated request with `401 WWW-Authenticate: Basic realm="..."`. Chromium handles this challenge at the browser context level; it must receive credentials **in response to the 401 challenge**, not as proactively injected headers.

Three prior approaches all failed:

| Approach | Why it failed |
|---|---|
| `BrowserProfile.headers = { Authorization: Basic ... }` | Headers are sent proactively on every request, but `BrowserProfile.http_credentials` is **commented out** in browser-use 0.12.x — headers alone do not respond to a `401` challenge |
| `browser.set_extra_headers({ Authorization: ... })` | Same issue: proactive headers, not a challenge response; also interfered with downstream SPA/API calls, causing pages to hang in skeleton state |
| Embedded `user:pass@host` URL | Chromium in headless CDP mode rejects this format for `https` targets, producing `ERR_INVALID_AUTH_CREDENTIALS` |

The core issue: **HTTP Basic Auth requires answering a `WWW-Authenticate` challenge**. Chrome DevTools Protocol (CDP) `Fetch.authRequired` is the correct interception point for this.

---

## Decision

### ADR-004-1: CDP `Fetch.authRequired` for HTTP Basic Auth in browser-use Path

Register a CDP-level `Fetch.authRequired` event handler on the `BrowserSession._cdp_client_root` that responds to every server auth challenge with `ProvideCredentials`.

**Implementation** — `ObservationAgent._setup_cdp_server_auth()`:

```python
await cdp_client.send.Fetch.enable(params={"handleAuthRequests": True})

def _on_auth_required(event, session_id=None):
    request_id = event.get("requestId") or event.get("request_id")
    async def _provide_creds():
        await cdp_client.send.Fetch.continueWithAuth(
            params={
                "requestId": request_id,
                "authChallengeResponse": {
                    "response": "ProvideCredentials",
                    "username": username,
                    "password": password,
                },
            },
            session_id=session_id,
        )
    asyncio.create_task(_provide_creds())

cdp_client.register.Fetch.authRequired(_on_auth_required)
cdp_client.register.Fetch.requestPaused(_on_request_paused)
```

This pattern mirrors `BrowserSession._setup_proxy_auth()` which browser-use already uses internally for proxy challenges, but only activates when `BrowserProfile.proxy` is set. `_setup_cdp_server_auth()` fills the same role for **server-level** `WWW-Authenticate: Basic` challenges.

**Lifecycle:**
1. `_prime_browser_session_http_auth()` calls `browser.start()` — CDP connection established, `_cdp_client_root` is available.
2. `_setup_cdp_server_auth()` is called — `Fetch.enable` and handler registration run.
3. `browser.navigate_to(url)` — initial page load triggers `401`; CDP handler responds with credentials; page loads.
4. Agent is constructed with the same already-started browser — `start()` is idempotent (guarded by `if self._cdp_client_root is None`), so the CDP state persists.
5. All subsequent navigation by the agent also benefits from the handler (e.g. if the agent re-navigates to the same URL).

### Consequences

**Positive**
- Correctly answers `401` challenges rather than injecting proactive headers that Chromium ignores for auth.
- CDP handler persists for the full agent session — no per-request setup needed.
- No SPA interference: `Fetch.enable` intercepts only auth challenges. Normal requests are continued immediately by `_on_request_paused`.
- Consistent with browser-use's own internal proxy auth pattern; low maintenance risk across version upgrades.
- Works in headless and non-headless modes.

**Negative**
- Requires `_cdp_client_root` to be set, which means `browser.start()` must be called first. If browser-use changes the internal attribute name, the fallback path logs a warning and skips auth (no crash, but auth fails silently).
- `asyncio.create_task()` means auth responses are fire-and-forget; if `continueWithAuth` fails, the request may stall. Error is logged at DEBUG level.

**Alternatives Considered**

| Alternative | Verdict |
|---|---|
| `BrowserProfile.http_credentials` | Field commented out in browser-use 0.12.x; not available without patching the library |
| `set_extra_headers({ Authorization: ... })` | No 401 challenge response; caused SPA loading hang by leaking auth header to JSON API calls |
| `user:pass@host` URL | `ERR_INVALID_AUTH_CREDENTIALS` in headless Chromium for HTTPS targets |
| Upgrade browser-use to 0.12.2 | Changelog does not add `http_credentials` support; same root cause |
| Patch `BrowserSession._setup_proxy_auth` to handle server challenges | Would require monkey-patching a private method — higher maintenance risk |

---

### ADR-004-2: Credential Normalisation Before Auth Injection

**Decision:** `_normalize_http_credentials()` strips whitespace and returns `None` when either `username` or `password` is blank. All auth paths (CDP handler, Playwright context, URL builder) consume the normalised value.

```python
def _normalize_http_credentials(self, creds):
    if not creds:
        return None
    username = str(creds.get("username", "")).strip()
    password = str(creds.get("password", "")).strip()
    if not username or not password:
        return None
    return {"username": username, "password": password}
```

**Why:** Prevents sending `Authorization: Basic <base64(:)>` or `Authorization: Basic <base64(user:)>` which Chromium rejects with a malformed-credentials error even before a challenge is issued.

**Consequences:** Blank credentials are silently dropped (no auth setup). The page either loads without auth (public page) or returns 401 (preprod page, surfaced as a navigation error in logs).

---

### ADR-004-3: Traditional Playwright Path Uses `browser.new_context(http_credentials=...)`

**Decision:** When `user_instruction` is absent, ObservationAgent falls back to traditional Playwright crawling. In this path, normalised `http_credentials` are passed directly to `browser.new_context(http_credentials=...)` which is Playwright's native HTTP Basic Auth support.

**Why:** This path does not use browser-use at all; Playwright natively supports `http_credentials` in `new_context()`. No CDP manipulation is needed.

**Consequences:** The two auth paths are deliberately different (`new_context` for Playwright, CDP for browser-use) because each library has its own auth mechanism. This is correct and intentional — using the same mechanism for both would require either reimplementing CDP auth in plain Playwright (unnecessary) or forcing browser-use to use Playwright contexts (not supported).

---

### ADR-004-4: Auth Priming Before Agent Handoff

**Decision:** After the CDP handler is registered, `_prime_browser_session_http_auth()` performs an explicit `navigate_to(url)` before constructing the `browser-use Agent`. The `start_instruction` passed to the agent then says `"You are already on {url}. Continue from the current page..."` rather than asking the agent to navigate itself.

**Why:** If the agent performs the initial navigation itself (without prior priming), the `401` challenge fires during that navigate — which is handled by CDP — but browser-use 0.12.x may interpret the intermediate `401` response as a navigation failure before the handler responds. Pre-priming eliminates this race condition by ensuring the page is fully loaded before the agent starts.

**Consequences**
- **Positive:** Agent sees the authenticated page from step 1, reducing the chance of a navigation error on the first action.
- **Negative:** Adds one additional page load before the agent runs. Negligible latency compared to LLM round-trips.

---

## Implementation Summary

| Method | File | Role |
|---|---|---|
| `_normalize_http_credentials()` | `observation_agent.py` | Strip/validate credentials before use |
| `_build_http_auth_headers()` | `observation_agent.py` | Build `Authorization: Basic` headers (used in `_build_browser_profile`) |
| `_setup_cdp_server_auth()` | `observation_agent.py` | Register CDP `Fetch.authRequired` handler on `BrowserSession` |
| `_prime_browser_session_http_auth()` | `observation_agent.py` | Start session, register CDP handler, perform initial navigation |
| `_build_browser_profile()` | `observation_agent.py` | Create `BrowserProfile` with hardened defaults + optional `storage_state` |
| `_execute_multi_page_flow_crawling()` | `observation_agent.py` | browser-use path, calls priming then constructs agent |
| `_execute_traditional_crawling()` | `observation_agent.py` | Playwright path, uses `new_context(http_credentials=...)` |
| `execute_task()` | `observation_agent.py` | Extracts and forwards `http_credentials` to both paths |

## Test Coverage

| Test class | File | Tests |
|---|---|---|
| `TestWorkflowSchemas` | `test_observation_agent_http_credentials.py` | Schema acceptance |
| `TestObservationAgentHelpers` | `test_observation_agent_http_credentials.py` | `_build_browser_profile`, `_build_authenticated_url`, traditional crawling Playwright context |
| `TestCdpServerAuth` | `test_observation_agent_http_credentials.py` | `_setup_cdp_server_auth` unit, `authRequired` handler callback, `_prime_browser_session_http_auth` |
| `TestExecuteTaskPassThrough` | `test_observation_agent_http_credentials.py` | `execute_task()` forwarding for both paths; CDP used, not `set_extra_headers` |
| `TestOrchestrationPassThrough` | `test_observation_agent_http_credentials.py` | Endpoint and orchestration passthrough |
| Browser-use regression | `test_observation_agent_browser_use.py` | No regressions after CDP changes |

**Total: 39 tests passing.**

## Status

**Accepted** — implemented and tested March 13, 2026. All 39 backend regression tests pass.
