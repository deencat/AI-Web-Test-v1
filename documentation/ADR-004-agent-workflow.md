# Architecture Decision Records — ObservationAgent HTTP Basic Auth for Preprod

**Document ID:** ADR-004  
**Component:** ObservationAgent / browser-use Integration  
**Status:** Accepted  
**Date:** March 13, 2026  
**Last Amended:** March 17, 2026 (Sprint 10.6 provider-aware LLM wiring)  
**Author:** Developer B  
**Related Files:**
- `backend/agents/observation_agent.py`
- `backend/llm/browser_use_adapter.py`
- `backend/llm/client_factory.py`
- `backend/app/schemas/workflow.py`
- `backend/app/api/v2/endpoints/observation.py`
- `backend/app/api/v2/endpoints/generate_tests.py`
- `backend/app/services/orchestration_service.py`
- `backend/tests/agents/test_observation_agent_http_credentials.py`
- `backend/tests/agents/test_observation_agent_browser_use.py`
- `backend/tests/unit/test_agent_runtime_model_wiring.py`
- `backend/tests/unit/test_orchestration_agent_config_wiring.py`
- `frontend/src/features/agent-workflow/components/AgentWorkflowTrigger.tsx`

---

## Context

The ObservationAgent uses two execution paths:

1. **browser-use path** — activated when `user_instruction` is provided. An LLM-guided `BrowserSession` (from `browser_use` 0.12.x) navigates the target site and extracts UI elements.
2. **Traditional Playwright path** — activated when no `user_instruction` is provided. A raw Playwright browser context crawls pages up to `max_depth`.

As of Sprint 10.6, the ObservationAgent also participates in the new **per-agent model selection** architecture. Its LLM provider/model are resolved from `user_settings` by `OrchestrationService`, passed into the agent as `config["llm_provider"]` / `config["llm_model"]`, and must remain effective even in the browser-use path.

### Problem: HTTP Basic Auth + Modal Loop-Back on Preprod

Preprod and UAT environments (e.g. `https://wwwuat.three.com.hk/`) presented two related issues:

1. **HTTP Basic Auth Gate** — The server responds to every unauthenticated request with `401 WWW-Authenticate: Basic realm="..."`. Chromium handles this challenge at the browser context level; it must receive credentials **in response to the 401 challenge**, not as proactively injected headers.

2. **Modal Loop-Back Without Saved Session** — On Three HK preprod, the purchase flow shows an initial plan-selection modal. When the user (or agent) clicks "I understand" to dismiss it, the page unexpectedly loops back to the same modal instead of advancing. This occurs when ObservationAgent runs **without a saved browser profile** (i.e. no cookies/localStorage to preserve prior selections). The agent lacks context about which plan was selected and re-presents the modal, creating a loop.

### Root Causes

**HTTP Auth:** Three prior approaches all failed:

| Approach | Why it failed |
|---|---|
| `BrowserProfile.headers = { Authorization: Basic ... }` | Headers are sent proactively on every request, but `BrowserProfile.http_credentials` is **commented out** in browser-use 0.12.x — headers alone do not respond to a `401` challenge |
| `browser.set_extra_headers({ Authorization: ... })` | Same issue: proactive headers, not a challenge response; also interfered with downstream SPA/API calls, causing pages to hang in skeleton state |
| Embedded `user:pass@host` URL | Chromium in headless CDP mode rejects this format for `https` targets, producing `ERR_INVALID_AUTH_CREDENTIALS` |

The core issue: **HTTP Basic Auth requires answering a `WWW-Authenticate` challenge**. Chrome DevTools Protocol (CDP) `Fetch.authRequired` is the correct interception point for this.

### Additional Runtime Gap Identified in Sprint 10.6

After ADR-004 shipped, Sprint 10.6 introduced independent provider/model selection for Observation, Requirements, Analysis, and Evolution. End-to-end testing exposed a runtime gap in the Observation browser-use path:

1. The agent itself was parameterized correctly through `llm/client_factory.py`.
2. But `_create_browser_use_llm_adapter()` still preferred Azure-specific browser-use wiring, even when ObservationAgent had been configured with `openrouter`, `google`, or `cerebras`.
3. Result: the authenticated browser session from ADR-004 worked, but the guiding LLM could still fall back to Azure-specific behavior or misleading logs.

This amendment records the decision that **HTTP-auth priming and provider/model selection are orthogonal concerns**: the same authenticated browser session must work regardless of which configured provider the ObservationAgent is using.

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

### ADR-004-5: No-Profile Session Hardening to Prevent Modal Loop-Back

**Decision:** When ObservationAgent runs **without a saved browser profile** (no cookies/localStorage to carry state), the browser session and LLM instructions are hardened to prevent modal/wizard loop-back:

1. **Browser defaults** — Chrome-like user agent, anti-automation flags (`--disable-blink-features=AutomationControlled`), viewport, and minimum wait times (`wait_for_network_idle_page_load_time=1.0s`).
2. **Task instruction enhancement** — Agent is instructed:
   - If a reminder/confirmation modal appears, dismiss it and continue from the current step (not restart).
   - If the site shows both selections and a modal, preserve the selections and continue forward.
   - If redirected backward to a plan-selection step, **reselect the same choices made previously** and resume progressing instead of starting over.

**Why:** The Three HK preprod purchase flow shows a plan-selection modal on page load. After dismissal and navigation, if the backend returns the plan-selection modal again (e.g., due to a form validation error or temporary 503), the agent without prior session context would click "I understand" again, creating an infinite loop. The hardened instructions tell the agent to "remember" the first selection it made and reuse it if the page re-presents the step.

**Consequences**
- **Positive:** No-profile observation runs complete the preprod purchase flow even without saved session state.
- **Negative:** Instructions are site-specific guidance; highly complex multi-step wizards may still confuse the agent if the flow diverges unpredictably.

**Related Changes:**
- `DEFAULT_OBSERVATION_USER_AGENT`: Chrome-like UA string
- `DEFAULT_OBSERVATION_BROWSER_ARGS`: Anti-automation flags
- `DEFAULT_OBSERVATION_VIEWPORT`: Standard viewport for consistency
- Task description string in `_execute_multi_page_flow_crawling()`: Enhanced flow-continuity and modal-recovery guidance

---

### ADR-004-6: Provider-Aware LLM Selection for browser-use Path

**Decision:** ObservationAgent's browser-use path must use the same configured provider/model that the orchestration layer resolved for the Observation agent, rather than implicitly preferring Azure.

**Implementation:**

1. `OrchestrationService._resolve_per_agent_llm_config()` reads per-agent overrides from `user_settings` and injects `llm_provider` / `llm_model` into ObservationAgent config.
2. `ObservationAgent.__init__()` initializes `self.llm_client = get_llm_client(llm_provider, llm_model)`.
3. `ObservationAgent._create_browser_use_llm_adapter()` branches by provider:
    - **Azure** → prefer browser-use's built-in `ChatAzureOpenAI` when available.
    - **Non-Azure** (`openrouter`, `google`, `cerebras`) → skip `ChatAzureOpenAI` entirely and wrap the already-configured client in the custom provider-aware adapter.
4. `backend/llm/browser_use_adapter.py` derives adapter metadata from the supplied client (`deployment` or `model`) so browser-use logs and downstream calls reflect the configured provider/model.

**Why:** The auth mechanism added by ADR-004 is independent from LLM selection. A user may need both at once: for example, authenticate into a preprod site via CDP `Fetch.authRequired`, then guide the crawl with a non-Azure model. Treating the browser-use path as Azure-only would violate Sprint 10.6's per-agent settings contract.

**Consequences**
- **Positive:** ObservationAgent now honors per-agent provider/model overrides in the same browser-use flow that already supports HTTP Basic Auth.
- **Positive:** Authenticated preprod crawling works with Azure and non-Azure providers.
- **Positive:** Runtime logs are clearer because adapter creation now reports the configured provider/model.
- **Negative:** The custom adapter retains the legacy class name `AzureOpenAIAdapter` for backward compatibility even though it now supports multiple providers; this is a naming mismatch but not a runtime problem.

**Alternatives Considered**

| Alternative | Verdict |
|---|---|
| Keep browser-use path Azure-only and document it as a limitation | Rejected — conflicts with Sprint 10.6 architecture and user-facing settings |
| Force all non-Azure providers through env-level Azure fallback | Rejected — hides misconfiguration and makes settings ineffective |
| Create a separate adapter class per provider immediately | Deferred — current generic adapter is sufficient; provider-specific adapters can be introduced later if browser-use interfaces diverge |

---

## Implementation Summary

| Method | File | Role |
|---|---|---|
| `_normalize_http_credentials()` | `observation_agent.py` | Strip/validate credentials before use |
| `_build_http_auth_headers()` | `observation_agent.py` | Build `Authorization: Basic` headers (used in `_build_browser_profile`) |
| `_setup_cdp_server_auth()` | `observation_agent.py` | Register CDP `Fetch.authRequired` handler on `BrowserSession` |
| `_prime_browser_session_http_auth()` | `observation_agent.py` | Start session, register CDP handler, perform initial navigation |
| `_build_browser_profile()` | `observation_agent.py` | Create `BrowserProfile` with hardened defaults (Chrome-like UA, anti-automation args, viewport) + optional `storage_state` |
| `__init__()` | `observation_agent.py` | Initialize provider/model-specific LLM client via `get_llm_client(...)` |
| `_create_browser_use_llm_adapter()` | `observation_agent.py` | Select Azure built-in adapter only for Azure; use provider-aware custom adapter otherwise |
| `_execute_multi_page_flow_crawling()` | `observation_agent.py` | browser-use path, calls priming then constructs agent with enhanced modal-recovery and flow-continuity instructions |
| `_execute_traditional_crawling()` | `observation_agent.py` | Playwright path, uses `new_context(http_credentials=...)` |
| `execute_task()` | `observation_agent.py` | Extracts and forwards `http_credentials` to both paths |
| `_resolve_per_agent_llm_config()` | `orchestration_service.py` | Resolve ObservationAgent provider/model override from `user_settings` before workflow start |
| `AzureOpenAIAdapter.__init__()` | `browser_use_adapter.py` | Wrap provider-specific clients for browser-use and expose provider/model metadata |

## Test Coverage

| Test class | File | Tests |
|---|---|---|
| `TestWorkflowSchemas` | `test_observation_agent_http_credentials.py` | Schema acceptance |
| `TestObservationAgentHelpers` | `test_observation_agent_http_credentials.py` | `_build_browser_profile`, `_build_authenticated_url`, traditional crawling Playwright context |
| `TestCdpServerAuth` | `test_observation_agent_http_credentials.py` | `_setup_cdp_server_auth` unit, `authRequired` handler callback, `_prime_browser_session_http_auth` |
| `TestExecuteTaskPassThrough` | `test_observation_agent_http_credentials.py` | `execute_task()` forwarding for both paths; CDP used, not `set_extra_headers` |
| `TestOrchestrationPassThrough` | `test_observation_agent_http_credentials.py` | Endpoint and orchestration passthrough |
| Browser-use regression | `test_observation_agent_browser_use.py` | No regressions after CDP changes |
| Observation runtime wiring | `test_agent_runtime_model_wiring.py` | Non-Azure browser-use adapter path honors configured provider/model |
| Orchestration config wiring | `test_orchestration_agent_config_wiring.py` | ObservationAgent receives provider/model override from `user_settings` |

**Total: 41 directly relevant tests passing** (39 ADR-004 auth/browser-use tests + 2 Sprint 10.6 Observation runtime/config wiring tests).

## Status

**Accepted** — implemented and tested March 13, 2026.

### What Was Fixed

This ADR resolves two preprod environment issues discovered during ObservationAgent testing:

1. **HTTP Basic Auth Gate (ADR-004-1 to ADR-004-4)** — ObservationAgent can now access preprod pages protected by HTTP Basic Auth. The CDP-level `Fetch.authRequired` handler (mirroring browser-use's own `_setup_proxy_auth` pattern) responds to `401 WWW-Authenticate: Basic` challenges, eliminating `ERR_INVALID_AUTH_CREDENTIALS` errors.

2. **Modal Loop-Back Without Saved Session (ADR-004-5)** — ObservationAgent can now complete multi-step preprod flows (like Three HK purchase) even without a saved browser profile. Hardened browser defaults and enhanced LLM instructions guide the agent to dismiss modals, preserve selections, and re-select previous choices if the page loops backward.

3. **Provider-Aware browser-use Runtime (ADR-004-6)** — ObservationAgent now preserves the configured per-agent provider/model in the browser-use execution path instead of implicitly favoring Azure-only adapter logic. This keeps Sprint 10.6 settings behavior consistent with ADR-004's authenticated crawling flow.

### Test Results

**41 directly relevant backend tests passing:**
- `test_observation_agent_http_credentials.py` — HTTP auth schema, CDP handler unit, browser-use flow integration, traditional Playwright path
- `test_observation_agent_browser_use.py` — No regressions after hardened browser session and enhanced instructions
- `test_agent_runtime_model_wiring.py` — Observation runtime uses provider-aware adapter path for non-Azure models
- `test_orchestration_agent_config_wiring.py` — Orchestration resolves and injects Observation provider/model overrides

**All tests green; ready for production.**
