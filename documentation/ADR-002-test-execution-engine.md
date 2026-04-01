# Architecture Decision Records — Test Execution Engine

**Document ID:** ADR-002  
**Component:** Test Execution Engine  
**Status:** Accepted  
**Date:** March 3, 2026  
**Author:** Engineering Team  
**Related Files:**
- `backend/app/services/three_tier_execution_service.py`
- `backend/app/services/tier1_playwright.py`
- `backend/app/services/tier2_hybrid.py`
- `backend/app/services/tier3_stagehand.py`
- `backend/app/services/xpath_extractor.py`
- `backend/app/services/xpath_cache_service.py`
- `backend/app/services/stagehand_service.py`
- `backend/app/services/execution_service.py`
- `backend/app/services/post_click_readiness.py`
- `backend/app/api/v1/endpoints/executions.py`
- `backend/app/utils/http_auth_credentials.py`
- `frontend/src/components/RunTestButton.tsx`
- `frontend/src/utils/urlUtils.ts`
- `backend/tests/test_execution_service_uat_auto_creds.py`
- `frontend/src/components/__tests__/RunTestButton.test.tsx`
- `backend/tests/test_tier2_payment_helpers.py`
- `backend/tests/test_post_click_readiness.py`
- `backend/tests/test_three_tier_execution_service.py`
- `backend/tests/test_stagehand_service_azure_cdp.py`
- `backend/tests/unit/test_universal_llm_azure.py`

---

## Table of Contents

1. [ADR-002-1: 3-Tier Execution Architecture with Configurable Fallback](#adr-002-1-3-tier-execution-architecture-with-configurable-fallback)
2. [ADR-002-2: XPath Extraction via Stagehand observe() in Tier 2](#adr-002-2-xpath-extraction-via-stagehand-observe-in-tier-2)
3. [ADR-002-3: PostgreSQL-Backed XPath Cache with Self-Healing](#adr-002-3-postgresql-backed-xpath-cache-with-self-healing)
4. [ADR-002-4: Context-Aware Payment Gateway Readiness Waits](#adr-002-4-context-aware-payment-gateway-readiness-waits)
5. [ADR-002-5: observe() Retry on Loading Page and Navigation Race](#adr-002-5-observe-retry-on-loading-page-and-navigation-race)
6. [ADR-002-6: option XPath Normalization for select Actions](#adr-002-6-option-xpath-normalization-for-select-actions)
7. [ADR-002-7: Bounded Post-Click Wait — Remove Unconditional sleep and networkidle](#adr-002-7-bounded-post-click-wait--remove-unconditional-sleep-and-networkidle)
8. [ADR-002-8: Iframe Container Click Fallback](#adr-002-8-iframe-container-click-fallback)
9. [ADR-002-9: Semantic Field-Type XPath Cache Validation](#adr-002-9-semantic-field-type-xpath-cache-validation)
10. [ADR-002-10: Pre-Click Enabled State Polling](#adr-002-10-pre-click-enabled-state-polling)
11. [ADR-002-11: Azure LiteLLM Native Provider Routing for Stagehand Initialization](#adr-002-11-azure-litellm-native-provider-routing-for-stagehand-initialization)
12. [ADR-002-12: Auto-Inject UAT HTTP Credentials in ExecutionService](#adr-002-12-auto-inject-uat-http-credentials-in-executionservice)
13. [ADR-002-13: Step-URL Fallback Scan for UAT Credential Detection](#adr-002-13-step-url-fallback-scan-for-uat-credential-detection)
14. [ADR-002-14: Remove Browser Profile Picker from Saved-Test Run Flow](#adr-002-14-remove-browser-profile-picker-from-saved-test-run-flow)
15. [ADR-002-15: Payment Direct Handler — Enable by Default + exp. date Keyword + Combined Expiry Fill](#adr-002-15-payment-direct-handler--enable-by-default--exp-date-keyword--combined-expiry-fill)
16. [ADR-002-16: Autopay Page URL Path Detection for Extended Readiness Wait](#adr-002-16-autopay-page-url-path-detection-for-extended-readiness-wait)
17. [ADR-002-17: Split Payment Host Detection — Separate Readiness Wait from Probe Timeout](#adr-002-17-split-payment-host-detection--separate-readiness-wait-from-probe-timeout)
18. [ADR-002-18: Quote-Aware Expiry Month/Year Value Extraction + `select` Guard for `value=None`](#adr-002-18-quote-aware-expiry-monthyear-value-extraction--select-guard-for-valuenone)
19. [ADR-002-19: URL-Change-Triggered Navigation Upgrade in Post-Click Readiness](#adr-002-19-url-change-triggered-navigation-upgrade-in-post-click-readiness)
20. [ADR-002-20: Auto-Dismiss Blocking Modals After Navigation](#adr-002-20-auto-dismiss-blocking-modals-after-navigation)
21. [ADR-002-21: Three HK Plan-Selection Progress Validation and Single Retry](#adr-002-21-three-hk-plan-selection-progress-validation-and-single-retry)
22. [ADR-002-22: Initial Bootstrap Navigation Uses First Step URL, Not Placeholder `base_url`](#adr-002-22-initial-bootstrap-navigation-uses-first-step-url-not-placeholder-base_url)
23. [ADR-002-23: Shared Step-Boundary Loading Wait Before Tier Execution](#adr-002-23-shared-step-boundary-loading-wait-before-tier-execution)

---

## ADR-002-1: 3-Tier Execution Architecture with Configurable Fallback

### Context

Automating real-world web applications requires handling a wide variety of page structures: some pages have stable, known CSS selectors; others require AI reasoning to identify elements; payment gateways introduce additional complexity with iframes and dynamic loading. A single execution strategy cannot handle all cases reliably and cost-effectively.

### Decision

Implement a **3-tier execution architecture** with three configurable fallback strategies:

| Tier | Method | Cost | Expected Success Rate |
|------|--------|------|----------------------|
| Tier 1 | Playwright direct (pre-defined CSS selector) | Zero LLM | 85–90% |
| Tier 2 | Stagehand `observe()` + Playwright execution | Low–Medium LLM | 90–95% (when T1 fails) |
| Tier 3 | Stagehand `act()` full AI reasoning | High LLM | 60–70% (when T1+T2 fail) |

**Fallback Strategies (user-configurable via `ExecutionSettings`):**
- **Option A** — Tier 1 → Tier 2 (cost-conscious, 90–95% overall success)
- **Option B** — Tier 1 → Tier 3 (AI-first, 92–94% overall success)
- **Option C** — Tier 1 → Tier 2 → Tier 3 (maximum reliability, 97–99% overall success)

Tier 2 and Tier 3 are **lazily initialized** — Stagehand/CDP connections are only established when a Tier 1 failure requires them.

**Orchestration:** `ThreeTierExecutionService` owns the strategy dispatch. Per-tier executors (`Tier1PlaywrightExecutor`, `Tier2HybridExecutor`, `Tier3StagehandExecutor`) are independently instantiated and share a single `Page` object and optionally a single Stagehand instance via CDP.

### Consequences

**Positive**
- 85–90% of steps execute at zero LLM cost (Tier 1).
- Cost scales with step complexity, not test volume.
- Strategy is user-configurable without code changes.
- Execution history per step enables auditability and tier-level analytics.

**Negative**
- Three layers of initialization logic increase service complexity.
- Lazy init means Tier 2/3 first-call latency is higher (Stagehand CDP connect).
- Debugging failures requires inspecting per-tier execution history entries.

**Alternatives Considered**
- **Single Playwright executor**: Simple, but brittle. No recovery path when selectors drift.
- **Stagehand-only**: Reliable but high per-step LLM cost and slow.
- **Random retry**: No cost control, unpredictable.

---

## ADR-002-2: XPath Extraction via Stagehand observe() in Tier 2

### Context

Tier 2 needs to locate page elements without pre-defined selectors. The core problem is mapping a natural-language instruction (e.g., *"click the Subscribe button"*) to a stable DOM locator at runtime without full AI act() cost.

### Decision

Use Stagehand `observe()` to extract XPath selectors at the point of execution. `observe()` returns a list of `ObserveResult` objects each with a `selector` field. Tier 2 takes the first result.

**Process in `XPathExtractor.extract_xpath_with_page()`:**
1. Call `page.observe(instruction)` on the current Playwright `Page`.
2. Take `result[0].selector`, strip the `xpath=` prefix if present.
3. Return the raw XPath string for Playwright to use as `page.locator(f"xpath={xpath}")`.

**Key implementation detail:** `observe()` shares the same browser context as the running test via CDP endpoint. This avoids opening a second browser — both Playwright and Stagehand operate on the same live page.

### Consequences

**Positive**
- Single `observe()` call per cache-miss vs. a full `act()` with multiple round-trips.
- XPath is then executed by Playwright directly — no further LLM calls for that step.
- Shareable Stagehand instance across Tier 2 and Tier 3 reduces browser resource use.

**Negative**
- `observe()` can return no results if the page is mid-navigation or in a skeleton/loading state (addressed in ADR-002-5).
- `observe()` can return an `<option>` XPath for `<select>` elements (addressed in ADR-002-6).
- `observe()` can return an `<iframe>` XPath for embedded payment widgets (addressed in ADR-002-8).

**Alternatives Considered**
- **CSS selector heuristic generation**: Not reliable for dynamic pages.
- **Full Stagehand act()**: Higher cost, no caching benefit.
- **Computer vision (screenshot + bounding box)**: Not yet supported in Stagehand SDK version in use.

---

## ADR-002-3: PostgreSQL-Backed XPath Cache with Self-Healing

### Context

For repeated test runs against the same URLs, re-running `observe()` every time wastes LLM tokens. However, XPaths can become stale when page structure changes (deployments, A/B tests, DOM refactors).

### Decision

Cache extracted XPaths in the PostgreSQL `xpath_cache` table (`XPathCacheService`), keyed by `SHA256(page_url + "::" + instruction)`.

**Cache lifecycle:**
1. **On cache hit**: validate element exists with `wait_for(state="attached", timeout=2000)` before using.
2. **On validation failure**: invalidate entry (`is_valid=False`), fall through to `observe()`.
3. **On `observe()` success**: write new entry with `hit_count=0`, `is_valid=True`, TTL 7 days.
4. **On step failure with a cache hit**: invalidate entry to force re-extraction next run.

**Cache key** is instruction-level, not selector-level: same instruction on same URL always maps to the same key, regardless of which XPath is returned.

### Consequences

**Positive**
- Repeated test runs against stable pages are zero LLM cost after the first run.
- `hit_count` metric enables identification of high-value cached selectors.
- Self-healing: stale entries are automatically replaced on the next run.

**Negative**
- Requires a database write per new extraction (small overhead).
- 7-day TTL may be too long for frequently-changing UIs — configurable but not yet per-domain.
- Cache is not invalidated on application deployment events.

**Alternatives Considered**
- **In-memory cache**: Fast, but lost on server restart and not shared across workers.
- **Redis cache**: Faster reads, but adds infrastructure dependency.
- **No cache**: Every step calls `observe()` — acceptable for small test suites, expensive at scale.

---

## ADR-002-4: Context-Aware Payment Gateway Readiness Waits

### Context

Payment form fields (card number, expiry, CVV) appear on two categories of pages:
1. **Embedded forms** on the merchant's own origin (e.g., checkout page at `shop.example.com`) — fields load quickly.
2. **External payment gateways** hosted on a separate domain (e.g., `paygwuat.hthk.com`, `gphk.gateway.mastercard.com`) — fields load inside iframes and may take 5–8 seconds after navigation.

The original implementation used an unconditional 8-second `wait_for_selector()` loop with 10 sequential CSS selectors regardless of context, causing 8-second unnecessary delays on embedded forms.

### Decision

**`_is_external_payment_gateway_url(url: str) -> bool`**  
Classifies the current page URL by hostname against a list of known gateway domains:
`gateway`, `mastercard`, `stripe`, `adyen`, `paypal`, `checkout`, `payment`, `paygw`, `pay.`

**`_payment_input_css_selector() -> str`**  
Returns a single combined comma-separated CSS selector covering all payment input types:
```
input[name*='card' i], input[id*='card' i], input[placeholder*='card number' i],
input[data-encrypted-name*='card' i], input[name*='cvv' i], input[id*='cvv' i],
input[name*='cvc' i], input[id*='cvc' i], input[name*='expiry' i], input[name*='expire' i]
```

**`_maybe_wait_for_payment_gateway(page)`**  
Single `page.wait_for_selector(combined_css, state="visible")` call with:
- **Gateway URL**: 8000ms timeout (external iframe loads slowly)
- **Non-gateway URL**: 1500ms timeout (embedded form, fail fast and continue)

**Fast-path for steps with explicit `selector`:**  
If the test step already has a `selector` field, attempt `wait_for(state="visible", timeout=1500)` directly before falling back to gateway detection. This avoids gateway detection overhead entirely when the selector is known.

### Consequences

**Positive**
- Embedded payment forms no longer incur 8-second waits.
- Single `wait_for_selector()` replaces 10 sequential probing iterations.
- URL-based classification is stateless and zero-cost.

**Negative**
- Gateway domain list requires manual maintenance as new providers are added.
- False-negative classification (unknown gateway domain) results in a 1500ms timeout instead of 8000ms — may fail on slow new gateways.

**Alternatives Considered**
- **Always use 8s timeout**: Simple but slow for embedded forms.
- **Remove wait entirely**: Faster but causes fill failures when gateway iframe hasn't loaded.
- **DOM-presence check before gateway wait**: Added as the fast-path for explicit selectors.

---

## ADR-002-5: observe() Retry on Loading Page and Navigation Race

### Context

Two distinct runtime conditions cause `observe()` to fail with no results even though the target element exists:

1. **Loading page** (e.g., plan-selection step): The page is in a skeleton/shimmer loading state when `observe()` runs. The target element exists in the DOM but is hidden behind a loading overlay.

2. **Navigation race** (e.g., card number fill after gateway redirect): A navigation event is in-flight when `observe()` — or a preceding `page.title()` call — executes, causing "Execution context was destroyed, most likely because of a navigation".

### Decision

**`_should_retry_observe_extraction(extraction_result, action, selector, instruction)`**  
Returns `True` (trigger one retry) when:
- `selector` is absent (Tier 1 would have handled it otherwise), **AND** one of:
  - error contains `"execution context was destroyed"` or `"because of a navigation"` (any action)
  - error contains `"observe() returned no results"` AND action is `"click"`
  - error contains `"observe() returned no results"` AND action is a payment fill/select (via `_is_payment_instruction()`)

**`_wait_for_page_interactable_for_observe(page)`**  
Sequentially waits:
1. `wait_for_load_state("domcontentloaded", timeout=5000)`
2. `wait_for_load_state("load", timeout=5000)`
3. For each of 14 loading/skeleton/spinner CSS selector patterns: `wait_for(state="hidden", timeout=5000)`
4. 0.4s fixed settle

**Retry policy:** Maximum **one** retry. The second `observe()` result is used regardless.

### Consequences

**Positive**
- Eliminates spurious failures on pages with loading states.
- Handles gateway navigation race within the existing Tier 2 flow without escalating to Tier 3.
- Loading wait is reused for any action type that triggers it.

**Negative**
- One retry per cache-miss adds up to ~10s latency on the affected step in the worst case.
- Loading-selector list is heuristic — custom loading patterns (e.g., branded overlays) may not be covered.
- Maximum-one-retry is conservative; persistent failures still escalate to the next tier.

**Alternatives Considered**
- **Increase base observe() timeout**: Raises cost for all steps, not just loading pages.
- **Polling loop with N retries**: Harder to bound; adds complexity without proportional benefit.
- **Pre-step page readiness check**: Would add latency to every step, not just affected ones.

---

## ADR-002-6: `option` XPath Normalization for `select` Actions

### Context

When a test step instructs selection of a specific dropdown value (e.g., *"select expiry year 2027"*), Stagehand `observe()` returns an XPath pointing to the `<option>` element rather than the parent `<select>`:

```
/html/body[1]/div[1]/select[1]/option[16]
```

`page.locator("xpath=...option[16]").wait_for(state="visible")` times out permanently because `<option>` elements are not independently visible in the DOM — they are only visible when their parent `<select>` is open.

### Decision

**`_looks_like_option_xpath(xpath) -> bool`**  
Returns `True` if `"/option["` or `"/option"` (case-insensitive) appears in the XPath.

**`_select_xpath_from_option_xpath(xpath) -> str`**  
Strips the `/option[N]` suffix to return the parent `<select>` XPath:
```
/html/body[1]/div[1]/select[1]/option[16]  →  /html/body[1]/div[1]/select[1]
```

**Execution change in `_execute_action_with_xpath()` for `select` actions:**
1. Normalize XPath via the two helpers above if applicable.
2. Use `wait_for(state="attached")` instead of `wait_for(state="visible")` — `<select>` is attached but may not be "visible" in Playwright's strict definition.
3. Primary: `select_option(value=value)`.
4. Fallback: `select_option(label=value)` on exception.

### Consequences

**Positive**
- Eliminates permanent timeout on all `<select>` dropdown steps where LLM returns `<option>` XPath.
- Transparent to the test step definition — no change needed to generated test data.

**Negative**
- XPath normalization is heuristic — pathological XPaths (e.g., `optiongroup`) might be incorrectly matched. Pattern is intentionally conservative: only matches `/option[` or trailing `/option`.
- `state="attached"` is weaker than `state="visible"` — may proceed on a select that is in a collapsed accordion. Acceptable trade-off given the `<option>` visibility limitation.

**Alternatives Considered**
- **Prompt Stagehand to return `<select>` XPath**: Requires prompt engineering; non-deterministic.
- **Post-process all XPaths for select steps**: Would need action-type awareness at extraction time.
- **Try `<option>` XPath first, fallback to parent**: More complex; no benefit over direct normalization.

---

## ADR-002-7: Bounded Post-Click Wait — Remove Unconditional sleep and networkidle

### Context

After clicking a navigation button (e.g., Checkout, Continue, Pay), the original implementation applied:
1. An unconditional `asyncio.sleep(3.0)`.
2. `wait_for_load_state("networkidle")` with the full `timeout_ms` (up to 30s).
3. 10 sequential `wait_for_selector()` loops for payment input selectors.

On the `three.com.hk` checkout flow this caused **83 seconds** of post-click stall on Step 17 (Checkout button).

### Decision

**Post-click wait restructure in `_execute_action_with_xpath()` after click:**

```
asyncio.sleep(0.2)                              # minimal settle
if url_changed:
    wait_for_load_state("load", min(timeout_ms, 10000))   # bounded
if not is_navigation_button:
    wait_for_load_state("networkidle", min(timeout_ms, 10000))  # skip for nav buttons
asyncio.sleep(0.4)                              # replaced: was 3.0s unconditional
```

**`is_navigation_button`** classification: instruction contains any of: `next`, `continue`, `submit`, `proceed`, `confirm`, `checkout`, `payment`, `pay`.

**Auth popup/page-transition extension:**
- Click classification also inspects the step instruction and clicked element text for `login`, `log in`, `sign in`, `sign-in`, `signin`, `authenticate`.
- For auth submission clicks, the executor performs a bounded popup/page readiness wait before advancing:
    1. wait briefly for the clicked control to become hidden when the login modal is expected to close,
    2. wait for a short `networkidle` window,
    3. wait for common loading/spinner/overlay selectors to disappear,
    4. apply a final 0.4s bounded settle.

This covers same-URL popup login flows where the DOM updates asynchronously after authentication but the browser does not perform a full navigation.

**Application loading-indicator extension:**
- The readiness wait now treats disappearance of known application loaders as the primary UI-ready signal when present, instead of relying only on action classification.
- The shared loading-indicator set includes generic loading/spinner/skeleton selectors and the app-specific Bootstrap spinner markup:

```html
<div role="status" class="spinner-border text-primary"><span class="visually-hidden">Loading...</span></div>
```

- Practically, this means the executor waits for `div[role='status'].spinner-border` / `[role='status'].spinner-border` to become hidden before advancing to the next step, with a bounded timeout.

This reduces the need to special-case individual actions because readiness is tied to the webapp's actual loading state, while still preserving bounded fallback waits for pages that do not render the spinner.

**Payment field wait after navigation button:**  
Single `page.wait_for_selector(combined_css, state="visible")` call (from ADR-002-4) with bounded timeout, replacing the sequential 10-probe loop.

**`wait_timeout` cap:** `min(self.timeout_ms, 10000)` — no wait can exceed 10s even if `timeout_ms` is set higher.

### Consequences

**Positive**
- Post-click time for navigation buttons reduced from 83s to ~1–3s typical.
- `networkidle` is not waited for navigation buttons — eliminates the longest waits (SPA route changes never reach `networkidle`).
- 0.4s sleep is bounded and explained; 3.0s was unconditional and unexplained.
- Popup login/auth transitions no longer race the next step when the URL stays unchanged.
- Shared loader disappearance now works as a reusable readiness signal across popup, SPA, and same-URL transitions.

**Negative**
- 0.4s may be insufficient for very slow backend pages that trigger a cascade of XHR requests. Monitoring required.
- `is_navigation_button` heuristic is keyword-based — custom button labels not in the list still get the full `networkidle` wait.
- Loader-based readiness depends on the spinner being mounted and hidden consistently; flows that never render the loader still rely on the bounded fallback waits.

**Alternatives Considered**
- **Remove all fixed sleeps**: Risky — some pages require a brief settle after click before DOM is queryable.
- **Use `wait_for_load_state("commit")` only**: Too early; DOM not ready.
- **Adaptive timeout based on page timing API**: Over-engineering for current scale.

---

## ADR-002-8: Iframe Container Click Fallback

### Context

On payment gateway pages, the submit/pay button is often rendered inside an `<iframe>` (e.g., Mastercard Simplify hosted payment page). Stagehand `observe()` correctly identifies the iframe container element but returns its XPath:

```
/html/body[1]/div[1]/iframe[1]
```

Clicking the `<iframe>` element itself does nothing — the click must be dispatched inside the frame's content context.

### Decision

**`_xpath_targets_iframe(xpath) -> bool`**  
Returns `True` if `"/iframe["` or `"/iframe"` (case-insensitive) appears in the XPath.

**`_try_click_inside_iframe(page, instruction) -> bool`**  
Iterates `page.frames` (excluding `page.main_frame`). For each frame, tries a prioritized list of CSS selectors for submit/pay controls:

```python
selector_candidates = [
    "button[type='submit']", "input[type='submit']",
    "button[name*='submit' i]", "button[id*='submit' i]",
    "[role='button'][name*='submit' i]",
]
# If instruction contains "pay" / "payment":
selector_candidates += [
    "button[id*='pay' i]", "button[name*='pay' i]",
    "[role='button'][id*='pay' i]", "[role='button'][name*='pay' i]",
    "input[value*='pay' i]",
]
```

For each candidate: `wait_for(state="visible", timeout=1200)` then `click()`. Returns `True` on first success.

**Intercept in `execute_step()`:** When action is `"click"` and `_xpath_targets_iframe()` is True, route to `_try_click_inside_iframe()` before calling `_execute_action_with_xpath()`. On success, return immediately without caching the iframe XPath.

### Consequences

**Positive**
- Handles the most common embedded payment gateway pattern without requiring explicit selectors in test definitions.
- Works for any frame on the page, not just the first one.
- 1200ms per-selector timeout keeps total fallback time bounded (~12s worst case for 10 selectors × 2 frames).

**Negative**
- Frame enumeration order is non-deterministic — if multiple frames exist, the wrong frame may be tried first.
- Selector list is heuristic — unusual payment button markup (e.g., `<div onclick>`) is not covered.
- Iframe XPath is not cached (correct: next run should also use the in-frame fallback).

**Alternatives Considered**
- **Inject JS to click inside iframe**: Requires `allow_eval` browser context option; security implications.
- **Prompt Stagehand to return in-frame selector**: Non-deterministic; would require Tier 3 escalation.
- **Explicit selector in test step**: Requires test author to know gateway iframe structure in advance; defeats AI-based test generation.

---

## ADR-002-9: Semantic Field-Type XPath Cache Validation

### Context

The XPath cache key is `SHA256(page_url + "::" + instruction)`. On login flows that use a modal or popup, the URL does not change between the email-entry step and the password-entry step. This means the password fill step can hit the cached XPath from the email fill step, typing the password into the email field. The form validation engine keeps the Login button `disabled` because email and password fields now contain mismatched values.

### Decision

Before accepting a cache hit for `fill`/`type`/`input` actions, call `_validate_cached_xpath_for_step()` to semantically verify that the cached element's DOM attributes match the step's intent.

**Implementation in `execute_step()` — replaces bare `wait_for(state="attached")`:**
```python
is_valid_cache = await self._validate_cached_xpath_for_step(
    page=page, xpath=xpath, action=action,
    instruction=instruction, value=value,
)
if not is_valid_cache:
    raise ValueError("Cached XPath does not match current step intent")
```

**`_validate_cached_xpath_for_step()` logic:**
1. Early-exit `True` for non-fill actions (click, select, etc.).
2. Classify step intent: `expected_password` if `"password"` in instruction; `expected_email` if `"email"` in instruction or `"@"` in value.
3. If neither email nor password intent, return `True` (no semantic check needed).
4. Read element attributes via Playwright: `type`, `name`, `id`, `placeholder`, `aria-label`, `autocomplete`.
5. If expected_password: reject if any attribute contains `email`; require at least one attribute to signal a password field (`password` in type/name/id/placeholder/autocomplete).
6. If expected_email: reject if any attribute signals a password field without email signals.
7. On mismatch: return `False` → cache entry is bypassed, Tier 2 falls through to `observe()` re-extraction.

**Cache invalidation:** The existing self-healing path (ADR-002-3) handles invalidation when the step ultimately fails with a cache hit. Semantic rejection does not immediately invalidate; it only bypasses for this execution.

### Consequences

**Positive**
- Eliminates false cache hits on same-URL multi-field login flows.
- No change to cache key required — validation is a read-time check, not a write-time change.
- Transparent to test step definitions.

**Negative**
- Adds one Playwright attribute-read round-trip per cache hit on fill steps.
- Heuristic: only covers email/password field disambiguation. Other field-type conflicts (e.g., first-name vs. last-name) are not detected.
- Non-standard field markup (no `type`/`name`/`id`/`placeholder`/`aria-label`/`autocomplete`) may defeat the check.

**Alternatives Considered**
- **Include field-type context in cache key**: Would require test-step schema changes and break existing cached entries.
- **Always invalidate on same-URL sequential fill steps**: Eliminates all caching benefit for multi-field forms.
- **LLM-based semantic comparison**: Accurate but adds latency and LLM cost to every cache hit check.

---

## ADR-002-10: Pre-Click Enabled State Polling

### Context

After filling form fields, submit/login buttons often remain `disabled` for a brief period while client-side form validation runs (React controlled components, Angular validators, custom JS). If Tier 2 clicks the button before it transitions to `enabled`, the click has no effect but returns no error — the test step appears to succeed while the form was never submitted.

This was observed when a password was typed into the email field (ADR-002-9 root cause): re-typing the password into the email field left the Login button permanently disabled, and the Tier 2 click retry loop exhausted without ever triggering navigation.

### Decision

Before dispatching a click action, poll `is_enabled()` in `_wait_for_element_enabled_before_click()` for up to `min(timeout_ms, 8000)` ms.

**Implementation in `_execute_action_with_xpath()` for click actions:**
```python
await element.wait_for(state="visible", timeout=self.timeout_ms)
await self._wait_for_element_enabled_before_click(element, instruction)  # NEW
await element.click(timeout=self.timeout_ms)
```

**`_wait_for_element_enabled_before_click()` logic:**
```python
if await element.is_enabled(): return          # fast path
wait_deadline = time.time() + (min(self.timeout_ms, 8000) / 1000.0)
while time.time() < wait_deadline:
    await asyncio.sleep(0.2)
    if await element.is_enabled(): return
logger.warning("[Tier 2] ⚠️ Click target still disabled after wait")
# Proceed anyway — let click() surface the real error
```

The 8-second cap prevents runaway waits on permanently disabled controls. Logging at WARNING level keeps the disabled-button condition visible in execution logs.

### Consequences

**Positive**
- Prevents clicking disabled buttons after fill steps on reactive form frameworks.
- 200ms polling interval is low-overhead and does not block the event loop.
- Fast path returns immediately if button is already enabled (zero overhead for most clicks).

**Negative**
- 8s upper bound adds latency if a button is permanently disabled (test step should fail, not wait).
- Does not distinguish between "disabled while validating" (transient) and "disabled by design" (permanent). Both poll to timeout.
- Only applies to Tier 2 click execution; Tier 1 (Playwright direct) and Tier 3 (Stagehand act) are unaffected.

**Alternatives Considered**
- **`wait_for(state="enabled")`**: Not a valid Playwright wait state — only `attached`, `detached`, `visible`, `hidden` are supported.
- **Fixed sleep before click**: Unpredictable; too short misses slow validators, too long wastes time on fast validators.
- **Check form validity via JS**: Fragile across frameworks; requires eval access.

---

## ADR-002-11: Azure LiteLLM Native Provider Routing for Stagehand Initialization

### Context

All cached-miss steps in Tier 2 call Stagehand `observe()`, which routes through LiteLLM. When the configured LLM provider is Azure OpenAI, the model string and environment variables must match LiteLLM's native Azure provider path exactly. Two incorrect configurations were observed:

1. **Missing Azure branch in `initialize_with_cdp()`**: Only Cerebras/Google/OpenRouter branches existed, so Azure fell through to the OpenRouter path, producing model string `openrouter/ChatGPT-UAT` — an invalid model ID. Error: `OpenrouterException: ChatGPT-UAT is not a valid model ID`.

2. **`openai/` prefix with `OPENAI_API_BASE`**: Switching to `openai/ChatGPT-UAT` + `OPENAI_API_BASE=https://chatgpt-uat.openai.azure.com` is routed through the OpenAI (non-Azure) LiteLLM path, which sends requests to `https://api.openai.com`. Error: `NotFoundError: OpenAIException - Resource not found`.

### Decision

All three Stagehand initialization paths (`initialize()`, `initialize_with_cdp()`, `initialize_persistent()`) use LiteLLM's native Azure provider for `model_provider == "azure"`:

```python
elif model_provider == "azure":
    azure_api_key   = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint  = os.getenv("AZURE_OPENAI_ENDPOINT",
                         "https://chatgpt-uat.openai.azure.com/openai/v1")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    azure_model     = user_config.get("model") or os.getenv("AZURE_OPENAI_MODEL", "ChatGPT-UAT")
    if azure_model.lower().startswith("azure/"):
        azure_model = azure_model.split("/", 1)[1]    # strip prefix if already qualified
    clean_endpoint  = azure_endpoint.replace("/openai/v1", "").replace("/openai", "").rstrip("/")
    os.environ["AZURE_API_BASE"]    = clean_endpoint  # e.g. https://chatgpt-uat.openai.azure.com
    os.environ["AZURE_API_KEY"]     = azure_api_key
    os.environ["AZURE_API_VERSION"] = azure_api_version
    os.environ.pop("OPENAI_API_BASE", None)           # clear stale OpenAI base URL
    config = StagehandConfig(
        env="LOCAL", ...,
        model_name=f"azure/{azure_model}",            # e.g. "azure/ChatGPT-UAT"
        model_api_key=azure_api_key,
    )
```

**Key rules:**
- Model string: `azure/<deployment>` (not `openai/<deployment>`, not `openrouter/<deployment>`).
- Base URL env var: `AZURE_API_BASE` (clean hostname, no `/openai/v1` suffix) — used by LiteLLM Azure path.
- `OPENAI_API_BASE` explicitly cleared to prevent LiteLLM from routing Azure calls through the OpenAI path.
- `AZURE_API_VERSION` set to the deployment's API version (default `2024-02-01`).

### Consequences

**Positive**
- All three init modes (headless, CDP, persistent/debug) now produce valid Azure `observe()` calls.
- No `/openai/v1` suffix confusion — LiteLLM appends the correct path internally.
- Explicit `OPENAI_API_BASE` clearing prevents cross-contamination when switching providers across runs.

**Negative**
- `os.environ` mutation is process-global — if multiple concurrent test executions with different providers run in the same process, they can overwrite each other's env vars. Acceptable for current single-worker architecture; must be revisited if parallelism is added.
- Clean-endpoint stripping is string-based heuristic (strips `/openai/v1`, `/openai`). An unusual endpoint format could be stripped incorrectly.

**Alternatives Considered**
- **Pass Azure config as LiteLLM kwargs directly**: LiteLLM does not expose per-call `api_base` override through the Stagehand `StagehandConfig` interface.
- **Keep `openai/` prefix with `OPENAI_API_BASE`**: Routes through non-Azure LiteLLM path; ignores deployment-level auth and API version. Fails for Azure-only deployments.
- **Separate Stagehand instance per provider**: Would require major refactor of `ThreeTierExecutionService` initialization.

---

## ADR-002-12: Auto-Inject UAT HTTP Credentials in ExecutionService

**Date:** March 30, 2026 (Sprint 10.7)

### Context

The agent workflow path (`OrchestrationService` → `ObservationAgent`) already calls `http_credentials_for_url(url)` from `app.utils.http_auth_credentials` before opening a Playwright context. This returns the default http credential for any `wwwuat.three.com.hk` hostname and `None` otherwise.

The 3-tier saved-test execution path (`POST /tests/{id}/run` → queue manager → `ExecutionService.execute_test()`) did not call this function. Playwright's `new_context()` was created with no `http_credentials`, so every navigation to `wwwuat.three.com.hk` returned `ERR_INVALID_AUTH_CREDENTIALS`. Users had to work around this by manually selecting a browser profile with stored credentials before every run.

### Decision

In `ExecutionService.execute_test()`, immediately before `create_context()`, resolve credentials with a two-stage lookup:

**Stage 1** — call `http_credentials_for_url(base_url)`. Returns UAT creds when `base_url` is the UAT hostname; `None` otherwise.

**Stage 2** — if stage 1 returns `None` and `test_case.steps` is non-empty, scan each step string for embedded `https?://` URLs using `re.findall`, strip trailing punctuation, and call `http_credentials_for_url` on each. Stop at the first match. (Covered by ADR-002-13.)

The resolved value (UAT creds dict or `None`) is passed directly to `create_context(http_credentials=...)`. Explicit credentials supplied by callers are never overwritten (guarded by `if not http_credentials`).

### Consequences

**Positive**
- UAT saved tests run without any user action on credentials — mirrors the agent workflow policy.
- Non-UAT tests are entirely unaffected (both stages return `None`).
- Explicit `http_credentials` passed by the queue manager (e.g. from a browser profile) are preserved.

**Negative**
- Stage 2 `re.findall` is a heuristic — won't match URLs stored only in variable tokens (e.g. `{{base_url}}`).
- `import re` added to `execution_service.py`.

**Alternatives Considered**
- **Resolve credentials in queue manager**: Splits responsibility; queue manager already passes credentials through unchanged.
- **Keep browser profile picker**: Removed by design (see ADR-002-14).
- **Front-end sends correct `base_url`**: Correct long-term fix (requires `url` field in `GeneratedTestCase` type); deferred.

---

## ADR-002-13: Step-URL Fallback Scan for UAT Credential Detection

**Date:** March 30, 2026 (Sprint 10.7)

### Context

`RunTestButton` sends `base_url: 'https://web.three.com.hk'` as a hardcoded fallback because `GeneratedTestCase` (the TypeScript type returned by the tests API) carries no `url` field. `http_credentials_for_url('https://web.three.com.hk')` returns `None` — the hostname is `web.three.com.hk`, not `wwwuat.three.com.hk`. The Playwright context was therefore created without credentials and step 1 (`Navigate to https://wwwuat.three.com.hk/...`) failed with `ERR_INVALID_AUTH_CREDENTIALS` in production.

### Decision

Add a **stage 2 step-text scan** in `execute_test()`: iterate `test_case.steps`, extract all `https?://...` substrings with `re.findall`, strip trailing punctuation (`rstrip('.,;)"\'`)`), call `http_credentials_for_url` on each, and use the first non-`None` result.

Key properties:
- Runs only when stage 1 yields `None` — zero overhead when `base_url` already resolves credentials.
- Stops at the first credentialled URL found — consistent with navigate-first step ordering.
- Coerces each step to `str()` before scanning — handles both plain-string and JSON-object step formats.

### Consequences

**Positive**
- Fixes the `ERR_INVALID_AUTH_CREDENTIALS` production failure transparently, without frontend or API schema changes.
- Works for both plain-string steps and JSON step objects.
- Covered by a dedicated regression test: `test_execute_test_uat_url_in_step_injects_creds_when_base_url_is_non_uat`.

**Negative**
- Heuristic: steps storing the UAT URL only in a variable substitution token (e.g. `{{uat_url}}`) won't be matched.
- Ordering assumption: a non-credentialled URL appearing before a credentialled one in steps is correctly skipped, but this relies on `http_credentials_for_url` returning `None` for non-UAT URLs.

**Alternatives Considered**
- **Add `url` field to `GeneratedTestCase` TypeScript type**: Correct long-term fix; when the frontend passes the real test URL as `base_url`, stage 2 is never reached. Deferred to a future sprint.
- **Parse only `navigate` action steps**: More precise but requires all steps to carry an `action` field; plain-string steps don't.

---

## ADR-002-14: Remove Browser Profile Picker from Saved-Test Run Flow

**Date:** March 30, 2026 (Sprint 10.7)

### Context

`RunTestButton` rendered a modal dialog with a `<select>` dropdown for choosing a browser profile before every test run, unconditionally for all URLs. This blocked execution until the user made a selection and caused two problems:

1. **UAT tests**: users had to maintain a browser profile with http credential and select it manually — even though those credentials are hardcoded in `http_auth_credentials.py` and already auto-applied by the agent workflow.
2. **Non-UAT tests**: most tests require no HTTP credentials. The picker still appeared and blocked the run, adding mandatory friction with no functional benefit.

### Decision

**Remove the browser profile picker entirely from `RunTestButton`.**

- Drop all profile-related state: `selectedProfileId`, `profiles`, `profilesLoading`, `showProfileDialog`.
- Drop `enableProfileUpload` prop; add `testUrl?: string` prop.
- Send `POST /tests/{id}/run` immediately on click — no `browser_profile_id` in the payload.
- Render a read-only `🔐 UAT credentials auto-applied` badge below the Run button **only** when `isUatUrl(testUrl)` is `true`.

**`isUatUrl(url: string): boolean`** — new pure utility in `frontend/src/utils/urlUtils.ts`, hostname check against `wwwuat.three.com.hk` via `new URL()`.

**Browser Profiles sidebar nav item and `/browser-profiles` route** removed from `App.tsx` and `Sidebar.tsx`. The underlying API, service, and TypeScript types are retained — available via direct URL or future UI entry points.

**`has_session_data` guard removed** from `POST /tests/{id}/run` (`executions.py`): the guard blocked runs when a profile had no synced session data. Since `browser_profile_id` is no longer sent, the guard is dead code and is removed.

### Consequences

**Positive**
- Zero-click execution from Saved Tests for all URL types.
- UAT credential injection is guaranteed and transparent.
- `RunTestButton` reduced from ~170 lines to ~70 lines.
- Consistent UX with the agent workflow (no credential prompt there either).

**Negative**
- Users who used the picker for session-cookie injection (logged-in test replay) lose the UI entry point. The browser profile sync API remains accessible at `/browser-profiles` directly and via API.
- `testUrl` falls back to `''` when omitted by callers — UAT badge not shown, but execution still works (credentials injected via ADR-002-12/13 regardless of badge state).

**Alternatives Considered**
- **Keep picker, make it optional with a bypass**: One extra click still adds friction; picker implies user responsibility for credentials.
- **Auto-populate picker with UAT profile**: Brittle, requires a matching profile to exist, duplicates credential logic in `http_auth_credentials.py`.
- **Remove picker only for UAT URLs**: Conditional picker adds UI complexity. Current test suite has no known non-UAT tests requiring HTTP Basic Auth.

---

## Summary Table

| ADR | Decision | Status | Risk |
|-----|----------|--------|------|
| 002-1 | 3-Tier architecture with configurable fallback | Accepted | Low |
| 002-2 | Stagehand observe() for XPath extraction in Tier 2 | Accepted | Low |
| 002-3 | PostgreSQL XPath cache with self-healing | Accepted | Low |
| 002-4 | Context-aware payment gateway readiness waits | Accepted | Low |
| 002-5 | observe() retry on loading page / navigation race | Accepted | Low |
| 002-6 | `<option>` XPath normalization for select actions | Accepted | Low |
| 002-7 | Bounded post-click wait, remove unconditional 3s sleep | Accepted | Medium |
| 002-8 | Iframe container click fallback | Accepted | Medium |
| 002-9 | Semantic field-type XPath cache validation | Accepted | Low |
| 002-10 | Pre-click enabled state polling | Accepted | Low |
| 002-11 | Azure LiteLLM native provider routing for Stagehand init | Accepted | Medium |
| 002-12 | Auto-inject UAT HTTP credentials in `ExecutionService` before `new_context()` | Accepted | Low |
| 002-13 | Step-URL fallback scan for UAT credential detection when `base_url` is generic | Accepted | Low |
| 002-14 | Remove browser profile picker from saved-test run flow; UAT badge only | Accepted | Low |
| 002-15 | Payment direct handler: enable by default, add `exp. date` keyword, add combined expiry fill selectors | Accepted | Low |
| 002-16 | Autopay URL path/query detection: extend 8000ms readiness wait to `?step=autopay` pages | Accepted | Low |
| 002-17 | Split host detection: `_is_cross_origin_payment_host()` for per-selector probe timeout; add `"Credit Card No."` label | Accepted | Low |
| 002-18 | Quote-aware expiry month/year value extraction; `select` guard for `value=None` in payment direct handler | Accepted | Low |
| 002-19 | URL-change-triggered navigation upgrade; Chrome UA injection for execution context | Accepted | Medium |
| 002-20 | Auto-dismiss blocking modals after navigation; override `navigator.webdriver` | Accepted | Medium |
| 002-21 | Validate Three HK plan click progression; retry once with price-aware `Select` locator | Accepted | Medium |
| 002-22 | Resolve initial navigation URL from test steps; bootstrap with `domcontentloaded` | Accepted | Low |
| 002-23 | Wait for shared loading indicators before each non-navigate step begins | Accepted | Low |

ADR-002-7, ADR-002-8, ADR-002-19, ADR-002-20, and ADR-002-21 carry medium risk because their heuristics depend on real-world page structure diversity and environment-specific flow behavior. ADR-002-11 carries medium risk due to process-global `os.environ` mutation — safe for single-worker deployments but must be revisited when parallel test execution is introduced. ADR-002-22 and ADR-002-23 are low risk because they reuse existing URL extraction and loading-indicator mechanisms rather than introducing new tier logic. These decisions should be monitored via tier-level execution metrics and environment-specific failure rates across test runs.

---

## ADR-002-15: Payment Direct Handler — Enable by Default + exp. date Keyword + Combined Expiry Fill

**Date:** Mar 31, 2026 · **Author:** Developer B

### Context

Field testing against a Three HK autopay/payment gateway page revealed three independent bugs that caused steps 31–33 (credit card number, card holder name, expiry date) to fail with `[3-Tier] ❌ All tiers exhausted`:

1. **`ENABLE_PAYMENT_DIRECT_HANDLING` defaulted to `false`** — The iframe-aware CSS-selector fill path (`_try_payment_field_action`) was built in a prior sprint but left opt-in via an env var. In practice this setting was never set, so the direct handler was never called. After the payment-readiness wait failed (`⚠️ Payment gateway readiness not confirmed`), execution fell through to `observe()`, which cannot penetrate cross-origin payment iframes.

2. **`"exp. date"` / `"exp date"` not in `_is_payment_instruction` keywords** — The keyword list contained `"expiry"` and `"expiration"` but not the abbreviated form used by LLM-generated test steps. Step 33 (`Input exp. date '01/39'`) was therefore never identified as a payment step, bypassing both the readiness wait and the direct handler entirely.

3. **No `fill` selector for combined MM/YY expiry inputs** — `_try_payment_field_action` handled expiry only as a `select` action (separate month/year dropdowns). A single combined text input (`01/39`) had no matching selector branch.

### Decision

**Bug 1 — Default to `true`:**  
Change `ENABLE_PAYMENT_DIRECT_HANDLING` default from `"false"` to `"true"`. The direct handler is safe: it attempts multiple CSS selectors and returns `None` on failure, letting execution continue normally. Operators who need to disable it can still set `ENABLE_PAYMENT_DIRECT_HANDLING=false` in `.env`.

**Bug 2 — Add `"exp. date"` and `"exp date"` to `_is_payment_instruction` keywords:**  
Both abbreviated forms are added to the keyword list alongside `"expiry"` and `"expiration"`.

**Bug 3 — Add combined expiry fill selectors to `_try_payment_field_action`:**  
When `action` is `fill`/`type`/`input` and the instruction contains `exp. date`, `exp date`, `expiry`, or `expiration`, try these selectors (main page then iframes):
```
input[name*='expiry'], input[id*='expiry'], input[name*='expiration'],
input[id*='expiration'], input[name*='exp'], input[id*='exp'],
input[autocomplete='cc-exp'], input[placeholder*='MM'], input[placeholder*='mm']
```

### Consequences

**Positive**
- Steps 31–33 (card number, cardholder name, combined expiry) now succeed via direct CSS fill without requiring `observe()` to penetrate cross-origin iframes.
- No change for non-payment steps — detection is keyword-gated.
- Operators retain opt-out capability via `ENABLE_PAYMENT_DIRECT_HANDLING=false`.

**Negative**
- Direct handler now runs on all deployments by default; if a site uses non-standard card field names not in the selector list, it falls through silently (existing behavior preserved).
- `"exp"` substring in selectors may occasionally match unrelated inputs named `expand` or similar — mitigated by also requiring the instruction to contain the keyword.

**Tests added (TDD):** 13 new tests in `tests/test_tier2_payment_helpers.py` — `TestPaymentInstructionKeywords` (5), `TestPaymentDirectDefault` (3), `TestCombinedExpiryFill` (2), plus existing 18 passing.

---

## ADR-002-16: Autopay Page URL Path Detection for Extended Readiness Wait

**Date:** Mar 31, 2026 · **Author:** Developer B

### Context

The Three HK autopay setup page URL is:
```
https://wwwuat.three.com.hk/...?step=autopay
```

Credit card fields on this page (Credit Card No., Card Holder Name, Exp. Date MM/YY) are standard HTML inputs rendered by a SPA — they are **not** inside cross-origin iframes. However, the SPA component takes longer than 1500ms to mount after navigation.

`_is_external_payment_gateway_url()` only checked the **hostname** against a keyword list. `wwwuat.three.com.hk` matches none of `gateway`, `pay`, `mastercard`, etc., so `_maybe_wait_for_payment_gateway()` used the 1500ms fast-path timeout. The SPA form was not yet rendered when the CSS selector probe ran, so the warning `⚠️ Payment gateway readiness not confirmed` was logged and `observe()` ran immediately — before the fields existed in the DOM. This is exactly the scenario ADR-002-4 documented as a known false-negative: *"Unknown gateway domain results in a 1500ms timeout instead of 8000ms"*.

**Why 60 seconds is wrong:** The waits are already bounded. Adding a 60s timeout would stall every payment step on genuinely missing elements for a full minute. The correct fix is to **classify autopay pages correctly** so they get the existing 8000ms wait, not to increase the global cap.

### Decision

Extend `_is_external_payment_gateway_url()` to also check the **URL path and query string** for autopay-specific keywords in addition to the hostname check:

```python
path_and_query = (parsed.path + "?" + (parsed.query or "")).lower()
autopay_keywords = ["autopay", "auto-pay", "step=autopay", "step=auto-pay"]
return any(keyword in path_and_query for keyword in autopay_keywords)
```

This makes the Three HK autopay page use the 8000ms readiness wait, giving the SPA component time to render before the CSS selector probe and `observe()` run.

### Consequences

**Positive**
- `wwwuat.three.com.hk/...?step=autopay` now correctly gets 8000ms wait.
- Zero impact on non-autopay pages — the path/query check only activates on the new keywords.
- Hostname checks are unchanged; existing external gateways (Mastercard, Stripe, etc.) are unaffected.
- Directly addresses the documented ADR-002-4 known limitation about manual gateway list maintenance.

**Negative**
- Sites that use `step=autopay` in their URL for non-payment purposes (unlikely) would get the extended wait unnecessarily — acceptable trade-off.
- Path-based matching is still a heuristic; sites with unconventional autopay URL patterns require further additions.

**Tests added (TDD):** 8 new tests in `tests/test_tier2_payment_helpers.py` — `TestAutopayUrlDetection` class (5 parametrized URL checks + 3 boundary tests).

---

## ADR-002-17: Split Payment Host Detection — Separate Readiness Wait from Probe Timeout

**Date:** Mar 31, 2026

### Context

ADR-002-16 extended `_is_external_payment_gateway_url()` to return `True` for same-origin autopay pages (`?step=autopay`) so they get the 8000ms readiness wait. This was correct for `_maybe_wait_for_payment_gateway()`.

However, `_try_payment_field_action()` used the same function to choose its **per-selector probe timeout**:

```python
wait_timeout = 3000 if payment_gateway_ready else 10000
```

When `payment_gateway_ready=False` (the readiness CSS selector probe failed to match the page's actual field attributes), the fallback became `wait_timeout=10000`. For a card-number step with 5 CSS selectors this meant up to **50 seconds** of stall before `observe()` was called — even on a same-origin SPA form where fields are always instantly accessible once rendered.

Root cause: `_is_external_payment_gateway_url()` conflates two distinct concepts:
1. **Extended readiness wait** — Does this page need 8000ms for the CSS probe? (includes same-origin autopay)
2. **Generous per-selector probe** — Is the field likely inside a slow cross-origin iframe? (external hostnames only)

### Decision

Introduce **`_is_cross_origin_payment_host(url)`** — a hostname-only check that returns `True` only for known external payment gateway domains (not same-origin autopay pages). Factor out `_GATEWAY_HOST_KEYWORDS` as a class-level constant shared by both methods to avoid duplication.

**`_try_payment_field_action()` timeout logic:**
```python
if payment_gateway_ready and payment_gateway_url == page.url:
    wait_timeout = 3000       # confirmed ready, fast probe
elif _is_cross_origin_payment_host(page.url):
    wait_timeout = 5000       # cross-origin iframe may still be loading
else:
    wait_timeout = 1500       # same-origin form: probe quickly
```

**`_maybe_wait_for_payment_gateway()`** continues to use `_is_external_payment_gateway_url()` (unchanged) so same-origin autopay pages still get the 8000ms mount wait.

Also add `"Credit Card No."` and `"Credit Card Number"` to `label_candidates` for card-number steps — these are the exact visible labels used by the Three HK autopay form when none of the CSS attribute selectors match.

### Consequences

**Positive**
- Same-origin autopay page: per-selector probe drops from 10000ms to 1500ms → worst-case stall drops from ~50s to ~7.5s (5 selectors × 1.5s) before `observe()` is called.
- `get_by_label("Credit Card No.")` now resolves the Three HK card number field without needing `observe()`.
- Cross-origin gateways (Mastercard, etc.) are unaffected — they keep the 5000ms generous probe.
- `_GATEWAY_HOST_KEYWORDS` is defined once; both methods stay in sync automatically.

**Negative**
- Same-origin forms not yet handled by CSS or label fallbacks still escalate to `observe()`, but much faster (seconds, not minutes).
- If a same-origin form takes genuinely long to mount (>1500ms per field), this probe timeout is too short. In practice, same-origin SPA forms render all fields together so a single 8000ms readiness wait is sufficient before probing begins.

**Tests added (TDD):** `TestAutopayDirectHandlerTimeout` (2 async tests) and `TestCreditCardLabelCandidates` (1 async test) in `tests/test_tier2_payment_helpers.py`.

---

## ADR-002-18: Quote-Aware Expiry Month/Year Value Extraction + `select` Guard for `value=None`

**Date:** Mar 31, 2026

### Context

On the Mastercard payment gateway (`gphk.gateway.mastercard.com`), AI-generated test steps for expiry dropdowns took the form:

```
Step 43: Select expiry month '01' from the dropdown
Step 44: Select expiry year '39' from the dropdown
```

The value (`'01'`, `'39'`) appears **after the field label** and is **single-quoted**. The existing `_extract_value_from_description()` patterns for month:

```python
r'(?:select|choose|pick|set)\s+(?:expiry\s+)?month\s+(\d{1,2})'
```

require the digit to follow `month ` with only whitespace — they don't allow a quote character before the digit. The quoted pattern in the list:

```python
rf'(?:select|choose|pick|set)\s+[{quote_chars}]?(\d{{1,2}})[{quote_chars}]?\s+as\s+(?:the\s+)?(?:expiry\s+)?month'
```

handles `"Select '01' as the expiry month"` (value-first ordering) but not `"Select expiry month '01' from the dropdown"` (field-first ordering).

Result: `value=None` was passed to the 3-tier engine. `_try_payment_field_action()` had no early-exit guard for `select` with `value=None`, so it exhausted all CSS selector candidates (each timing out at the `wait_timeout`), then fell through to Stagehand `observe()`. Both tiers consumed the full 36-second budget finding the `<select>` element — but `select_option(None)` silently completed without selecting any option. The form validation engine displayed `"This field is required"` and blocked the next step.

### Decision

**Fix 1 — Quote-aware month/year patterns in `_extract_value_from_description()`:**

Convert the plain `r'...'` month and year patterns to f-strings that include the `quote_chars` character class:

```python
rf'(?:select|choose|pick|set)\s+(?:expiry\s+)?month\s+[{quote_chars}]?(\d{{1,2}})[{quote_chars}]?',
rf'(?:select|choose|pick|set)\s+(?:expiry\s+)?year\s+[{quote_chars}]?(\d{{2,4}})[{quote_chars}]?',
```

The `[{quote_chars}]?` is optional on both sides — so `Select expiry month 01` (unquoted) and `Select expiry month '01'` (quoted) both match.

**Fix 2 — Early-exit guard in `_try_payment_field_action()` for `select` with `value=None`:**

```python
if action == "select" and not value:
    return None
```

This mirrors the existing fill guard (`if action in ["fill", "type", "input"] and not value: return None`) and prevents the function from spending time probing CSS selectors that cannot succeed without a value to select.

### Consequences

**Positive**
- Expiry month/year values are correctly extracted from both field-first (`"Select expiry month '01' from the dropdown"`) and value-first (`"Select '01' as the expiry month"`) orderings.
- The 36-second stall on these steps is eliminated — the payment direct handler selects the correct `<select>` element and sets the value with CSS selectors typically within 200ms.
- `select` with `value=None` exits immediately instead of exhausting the probe loop — reduces diagnostic noise and wasted time if extraction fails for any other reason.

**Negative**
- If `value=None` for a `select` step (e.g. due to a future extraction gap), the direct handler returns early and the step escalates to Stagehand `observe()` faster. The underlying extraction failure must be fixed rather than relying on `observe()` to somehow pick a value from the instruction.

**Tests added (TDD):** 8 new parametrized cases in `TestExecutionServiceValueExtraction.test_dropdown_value_extraction` in `tests/test_execution_service_value_extraction.py` covering both quoted/unquoted variants and the `Step N:` prefix format.

---

## ADR-002-19: URL-Change-Triggered Navigation Upgrade in Post-Click Readiness

**Date:** March 31, 2026

### Context

On the Three HK preprod site (`wwwuat.three.com.hk`), Step 7 — *"Select a $338 plan from the available plans"* — clicked a plan card "Select" button via Tier 2 (cache hit, XPath ending in `button[1]`). The 3-tier engine reported `success: True`, but the browser immediately returned to the original plan-selection page instead of advancing.

Two root causes were identified:

1. **`NAVIGATION_KEYWORDS` gap** — `post_click_readiness.py → classify_click_transition()` tests instruction + element text against a keyword list (`next`, `continue`, `submit`, `proceed`, `checkout`, etc.). Neither the instruction (`"Select a $338 plan..."`) nor the button text (`"Select"`) matched any keyword → `is_navigation_click = False`. The code then entered the non-navigation branch: tried `wait_for_load_state("networkidle")` (which never resolves on SPA route changes), fell back to `domcontentloaded`, and returned **without waiting for loading indicators to clear**. The next test step executed before the SPA had rendered the new page.

2. **Preprod session state gap (mirror of ADR-004-5)** — On Three HK preprod, the plan-selection flow requires session cookies/localStorage to be present. When the execution service runs in a fresh browser context (no saved browser profile), the preprod server detects the missing state after the plan click and redirects back to the plan-selection page. This is the same loop-back behavior documented in ADR-004-5 for the ObservationAgent; it also affects the 3-tier execution engine.

### Decisions

#### ADR-002-19-A: Upgrade Classification to Navigation When URL Already Changed

**File:** `backend/app/services/post_click_readiness.py`

When the browser URL has already changed within 0.2 s of the click, this is definitive evidence of a page navigation — regardless of whether any keyword in the instruction or button text matches `NAVIGATION_KEYWORDS`. The classification is upgraded:

```python
url_changed = page.url != current_url
if url_changed:
    logger.info("URL changed from %s to %s after click", current_url, page.url)
    # URL already changed → treat as navigation regardless of keyword classification.
    # Covers "Select plan" buttons on SPAs (e.g. Three HK preprod) where the button
    # text never matches NAVIGATION_KEYWORDS but a full page transition occurs.
    classification["is_navigation_click"] = True
    try:
        await page.wait_for_load_state("load", timeout=wait_timeout)
    except PlaywrightTimeout:
        logger.warning("Timed out waiting for page load after click")
```

As a result, once a URL change is observed, the full readiness path runs: loading indicators are waited on and a 0.4 s bounded settle is applied — the same treatment already used by keyword-matched navigation clicks.

#### ADR-002-19-B: Inject Chrome-Like User Agent into Every Browser Context

**File:** `backend/app/services/execution_service.py`

The `ExecutionService` was creating Playwright browser contexts without a `user_agent` option. Playwright's headless Chromium sends `HeadlessChrome/...` in the UA string by default, which many preprod/UAT servers (including Three HK) detect as automation and respond to with a session redirect/loop-back instead of the expected page transition.

The same pattern is used in `ObservationAgent` (`DEFAULT_OBSERVATION_USER_AGENT`, `DEFAULT_OBSERVATION_BROWSER_ARGS`) and was already confirmed to eliminate the loop-back on `wwwuat.three.com.hk` (ADR-004-5). Since browser profiles are no longer used (removed by ADR-002-14) and HTTP credentials are injected automatically (ADR-002-12/13), identical browser context hardening is the only remaining delta.

**Implementation:**

```python
# New module-level constant in execution_service.py
STEALTH_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)
```

`create_context()` — unconditionally includes `user_agent` in `context_options`:

```python
context_options = {
    "viewport": self.config.viewport,
    "user_agent": STEALTH_USER_AGENT,  # prevent HeadlessChrome UA detection
}
```

Chromium `launch()` args extended to match `DEFAULT_OBSERVATION_BROWSER_ARGS`:

```python
args=[
    '--remote-debugging-port=9222',
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',    # new: prevents /dev/shm OOM in containers
    '--no-first-run',             # new: suppress first-run setup UI
    '--no-default-browser-check', # new: suppress browser check UI
]
```

**Why not browser profile:** Browser profiles were removed from the saved-test run flow (ADR-002-14) in Sprint 10.7 for user-friendliness. HTTP Basic Auth was already auto-injected (ADR-002-12/13). The user agent was the remaining fingerprint difference between the ObservationAgent (which works on preprod) and the execution engine (which looped back).

**Tests added (TDD):**
- `test_execute_test_injects_chrome_user_agent` — verifies `new_context()` called with `user_agent=STEALTH_USER_AGENT` containing `"Chrome"` but not `"HeadlessChrome"`.
- `test_execute_test_chromium_launch_has_anti_automation_args` — verifies `chromium.launch()` called with `--disable-blink-features=AutomationControlled` and `--disable-dev-shm-usage` in `args`.

### Consequences

**Positive (ADR-002-19-A)**
- "Select plan" clicks on SPAs now correctly receive the full navigation readiness treatment.
- No keyword list maintenance required for future plan/option/select-style navigation buttons.
- Existing behaviour for non-navigating clicks (where URL stays the same) is unchanged.

**Positive (ADR-002-19-B)**
- Eliminates the `HeadlessChrome` UA fingerprint that preprod servers use to detect automation and issue session redirects.
- Matches the ObservationAgent's existing hardened browser defaults (confirmed to work on the same site via ADR-004-5).
- No browser profile required — consistent with the direction set in ADR-002-14 (profile picker removed) and ADR-002-12/13 (credentials auto-injected).
- `--disable-dev-shm-usage` prevents container OOM crashes on Linux under memory pressure (separate but related hardening benefit).

**Negative**
- `STEALTH_USER_AGENT` is pinned to Chrome 133. Must be updated periodically to stay current with real browser UA strings, or server UA checks will eventually re-detect it as stale.
- The UA string alone is not sufficient when the server enforces a **business-logic gate** (e.g. a mandatory modal click) independently of browser identity. See ADR-002-20 for the modal auto-dismissal fix that addresses this remaining gap.

**Alternatives Considered**
- **Add `"select"` to `NAVIGATION_KEYWORDS`**: Would create false positives on every `<select>` dropdown step that is genuinely not a navigation. Rejected.
- **Post-click URL polling loop (N × 200 ms)**: More latency per step; the 0.2 s window has proven sufficient in practice because SPA route changes are near-instantaneous.
- **Detect redirect loop and re-inject session**: Out of scope for the execution engine; the UA fix addresses the root cause instead.
- **Require a saved browser profile for preprod**: This was the original ADR-002-19-B conclusion, but browser profiles were removed by ADR-002-14 and are no longer used. UA injection is the correct no-profile equivalent.
- **Use Playwright's `stealth` plugin**: Not available in the Playwright Python package without external patching; `user_agent` + `--disable-blink-features` covers the same detection vectors for this site.

---

## ADR-002-20: Auto-Dismiss Blocking Modals After Navigation

**Date:** April 1, 2026

### Context

After applying the Chrome UA and anti-automation flag hardening from ADR-002-19-B, the preprod loop-back on Three HK (`wwwuat.three.com.hk`) persisted. The UA fix alone was insufficient because the root cause was not UA-based detection — it was a **mandatory modal gate**.

**What happens on preprod:**
The plan-selection page shows a "Reminder" modal with an "I understand" button before the user can select a plan. This modal is not present on the production site. Clicking "I understand" sets a server-side session marker (cookie/storage) that permits the "Select plan" click to advance to the next page. Without it, the server's plan-selection handler finds no gate marker and returns a redirect back to the plan-selection page.

**Why the existing test doesn't include a modal step:**
Test cases are generated by the ObservationAgent or from the production site where the modal does not exist. The generated steps go directly from "Navigate to URL" to "Select a $338 plan" with no intermediate "click I understand" step.

**How the ObservationAgent handles this (ADR-004-5):**
The ObservationAgent's LLM task instruction includes:
> *"If a reminder, confirmation, or informational modal appears, click the close, confirm, or I understand button and continue from the current step"*

The LLM sees the modal and clicks it autonomously. The execution engine has no such intelligence.

**Why ADR-002-19-B (`navigator.webdriver` override + Chrome UA) are insufficient alone:**
Both reduce automation fingerprinting. The modal itself is a *business-logic gate*, not a bot-detection mechanism. Even a real human browser with no automation flags would be redirected if they somehow bypassed the modal click. The session marker set by the modal dismissal is required regardless of browser identity.

### Decision

#### ADR-002-20-A: `auto_dismiss_blocking_modals()` in `post_click_readiness.py`

Add a deterministic modal detection and dismissal function as the execution-engine equivalent of the ObservationAgent LLM instruction.

**Implementation in `backend/app/services/post_click_readiness.py`:**

```python
MODAL_CONTAINER_SELECTORS = [
    ".modal.show",
    "[role='dialog']",
    "[aria-modal='true']",
]

MODAL_DISMISS_BUTTON_TEXTS = [
    "I understand", "I Understand", "OK", "Ok",
    "Close", "Dismiss", "Got it",
    "Accept", "Agree", "Confirm", "Continue", "Done",
]

async def auto_dismiss_blocking_modals(page, logger) -> bool:
    for container_sel in MODAL_CONTAINER_SELECTORS:
        modal = page.locator(container_sel).first
        if await modal.count() == 0 or not await modal.is_visible():
            continue
        for btn_text in MODAL_DISMISS_BUTTON_TEXTS:
            btn = modal.get_by_role("button", name=btn_text, exact=False)
            if await btn.count() > 0:
                await btn.first.click(timeout=3000)
                await asyncio.sleep(0.5)
                return True
    return False
```

**Called in three places:**

| Call site | When | Why |
|---|---|---|
| `execution_service.py` after `page.goto(base_url)` | Initial navigation | The preprod modal appears on first page load |
| `execution_service.py` after navigate-action `page.goto()` | In-test navigate steps | Any navigation step may land on a modal-gated page |
| `wait_for_post_click_readiness()` after loading-indicators clear, for `is_navigation_click=True` | After navigation clicks (plan select, continue, etc.) | If server redirects back to modal page, modal is auto-dismissed before next step runs |

#### ADR-002-20-B: `navigator.webdriver` Override via `addInitScript`

The `--disable-blink-features=AutomationControlled` Chromium flag suppresses the Chrome-level webdriver flag, but Playwright re-enables `navigator.webdriver = true` via CDP's `Runtime.enable` after context creation. Pages that check `window.navigator.webdriver` via JavaScript will still detect automation.

**Fix in `execution_service.py → create_page()`:**

```python
await self.page.add_init_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
)
```

`add_init_script` registers a script that runs in the page before any web content, so `navigator.webdriver` is already `false` when the page's own JavaScript executes. This is the correct Playwright mechanism for this override (equivalent to Puppeteer's `page.evaluateOnNewDocument`).

### Consequences

**Positive**
- Modal auto-dismissal is deterministic and general — works for any Bootstrap `.modal.show` or ARIA `[role="dialog"]` pattern, not just Three HK.
- The three call sites ensure modals are cleared at initial load, navigate-step loads, and post-click navigation landings — covering the full execution flow.
- `navigator.webdriver=false` eliminates a secondary fingerprint vector independent of UA strings.
- Zero cost for sites without modals — `count() == 0` exits immediately.

**Negative**
- `auto_dismiss_blocking_modals` is opportunistic: it tries a fixed list of button texts. An unusual dismiss label (e.g. a locale-specific text not in `MODAL_DISMISS_BUTTON_TEXTS`) will not be recognised and the modal will block the next step.
- Called after every navigation click — adds one full `MODAL_CONTAINER_SELECTORS` iteration (~3 locator queries) to every navigation step. Latency impact is negligible (< 50ms for empty modals) but measurable at scale.
- `navigator.webdriver` override via `addInitScript` does not survive cross-origin navigations in Playwright — each new page requires the script to be added again. The current approach adds it once in `create_page()`, which covers the single `Page` object used throughout a test execution.

**Alternatives Considered**
- **Add `navigator.webdriver` to all future test-generated steps**: Requires every test generation to output a JS-evaluate step; impractical.
- **Inject the modal-dismissal step into test generation**: Would require the AI to know about preprod-specific steps at generation time; breaks test portability.
- **Detect loop-back by comparing landing URL to expected URL**: More complex; requires knowing the expected URL for each step. The modal dismissal approach fixes the root cause directly.
- **Use a `playwright-stealth` library**: Not available for Playwright's Python API; workaround via `addInitScript` achieves the same effect.

**Tests added (TDD):** 6 new tests in `backend/tests/test_post_click_modal_dismiss.py`:
- `test_no_modal_returns_false` — no visible modal → returns False, no click
- `test_modal_show_i_understand_clicked` — `.modal.show` + "I understand" button → clicked, returns True
- `test_aria_dialog_no_button_returns_false` — `[role="dialog"]` but no matching button → returns False
- `test_modal_ok_button_clicked` — modal with "OK" → clicked, returns True
- `test_hidden_modal_not_dismissed` — modal in DOM but `is_visible=False` → skipped, returns False
- `test_auto_dismiss_is_exported` — import smoke test

**Total tests impacted: 11 passing** (6 new modal tests + 5 existing ADR-002-19 tests).

---

## ADR-002-21: Three HK Plan-Selection Progress Validation and Single Retry

**Date:** April 1, 2026

### Context

After ADR-002-19 and ADR-002-20, Step 7 on Three HK preprod still showed a specific failure mode:

```text
Step 7: Select a $338 plan from the available plans
cache_hit: True
xpath: .../button[1]
success: True
```

The Tier 2 click technically succeeded — Playwright clicked a visible `Select` button and no timeout occurred — but the browser remained on, or quickly returned to, the same plan-selection page. The next step then executed against the wrong page.

The key gap was that Tier 2 treated this as a **generic cached click**:

1. `XPathCacheService` keys entries by `page_url + instruction` only.
2. `_validate_cached_xpath_for_step()` in `tier2_hybrid.py` performs semantic validation only for `fill` / `type` / `input` actions.
3. For `click` actions it returns `True` as soon as the element is attached, so a cached `button[1]` remains valid even if the business outcome is wrong.
4. `_execute_action_with_xpath()` considered the step successful once the click and bounded readiness waits completed; it did not verify that the flow had actually left the plan-selection screen.

This is different from the ObservationAgent path in ADR-004-5. The agent has flow-level reasoning instructions: if the site returns to an earlier plan-selection step, it reselects the same plan and continues. Tier 2 had no equivalent recovery logic.

### Decision

#### ADR-002-21-A: Detect Three HK plan-selection clicks explicitly

Add `_is_three_hk_plan_selection_click(page_url, instruction, action)` in `tier2_hybrid.py`.

The guard is intentionally narrow:
- `action == "click"`
- `is_three_hk_uat_url(page_url) == True`
- instruction contains both `"plan"` and `"select"`

This limits the recovery path to the known preprod plan-selection screen and avoids affecting unrelated clicks.

#### ADR-002-21-B: Validate that the plan click actually progressed

Add `_wait_for_three_hk_plan_transition(page, current_url)`.

The helper does **not** rely only on URL change. It repeatedly checks for up to 5 seconds whether the page still "looks like" the plan-selection screen by counting visible `Select` buttons:

```python
select_buttons = page.locator("button:has-text('Select')")
return await select_buttons.count() >= 2
```

If the page no longer looks like the plan-selection grid, the transition is treated as successful even if the URL is unchanged (SPA case). If it still looks like the plan-selection grid after the bounded wait, the step is considered not progressed.

#### ADR-002-21-C: Retry once with a price-aware locator instead of the cached generic XPath

When progress validation fails:

1. Call `auto_dismiss_blocking_modals(page, logger)` again.
2. Retry the click **once** using a price-aware locator derived from the step instruction.

`_extract_plan_price()` parses the price from instructions like:

```text
Step 7: Select a $338 plan from the available plans
```

Then `_retry_three_hk_plan_click()` tries price-aware XPaths before falling back to the first `Select` button:

```python
(//*[contains(., '$338') or contains(., '338')]//button[normalize-space()='Select'])[1]
(//*[contains(., '$338') or contains(., '338')]/following::button[normalize-space()='Select'][1])[1]
(//button[normalize-space()='Select'])[1]
```

If the retry also fails to move the flow off the plan-selection screen, Tier 2 raises:

```python
ValueError("Three HK plan selection did not advance from the plan selection page")
```

That causes the cached XPath to be invalidated through the existing failure path and prevents the step from being falsely reported as success.

#### ADR-002-21-D: Wire the validation into `_execute_action_with_xpath()` after click readiness

The new call is placed after `wait_for_post_click_readiness(...)` and after payment-click waits, so the normal readiness path still runs first. Only then does Tier 2 verify business progress for this specific class of click:

```python
await self._ensure_three_hk_plan_click_progressed(page, instruction, current_url)
```

### Consequences

**Positive**
- Prevents false-positive success on Three HK preprod plan-selection clicks.
- Converts a silent bounce-back into deterministic recovery or an explicit failure.
- Invalidates stale/generic click cache entries through the existing failure path when the business outcome is wrong.
- The retry is bounded to one attempt and only runs for the narrow Three HK UAT plan-selection case.

**Negative**
- The recovery logic uses page-shape heuristics (`button:has-text('Select')`, price text extraction from instruction). If the site changes its labeling significantly, the helper may need updating.
- The bounded plan-transition check adds up to 5 seconds only for matching Three HK preprod plan-selection clicks.
- Price-aware XPath retry depends on the instruction containing the plan price. If the instruction becomes generic (`Select the first plan`), the fallback is less precise.

**Alternatives Considered**
- **Disable XPath cache for all click steps**: Too expensive; would remove one of Tier 2's main benefits for every site and flow.
- **Add full semantic validation for every click action**: Too broad and difficult to generalize; most clicks have no reliable business-success oracle.
- **Escalate immediately to Tier 3 when the page still shows plan cards**: Higher LLM cost and slower than a single deterministic retry.
- **Encode Three HK-specific modal and reselect steps into all generated tests**: Breaks portability between production and preprod and couples generation to one environment.

**Tests added (TDD):** 6 new tests in `backend/tests/test_tier2_plan_selection.py`:
- `test_is_three_hk_plan_selection_click_true_for_uat_plan_step`
- `test_is_three_hk_plan_selection_click_false_for_non_plan_click`
- `test_ensure_plan_click_progressed_returns_when_transition_confirms`
- `test_ensure_plan_click_progressed_retries_once_after_bounce`
- `test_ensure_plan_click_progressed_raises_when_still_on_plan_page`
- `test_execute_action_with_xpath_calls_plan_progress_guard`

**Total tests impacted:** 18 targeted tests passing for the affected area:
- 6 new Three HK plan-selection tests
- 1 existing post-click readiness test
- 6 modal auto-dismiss tests
- 5 execution-service UAT credential/browser hardening tests

---

## ADR-002-22: Initial Bootstrap Navigation Uses First Step URL, Not Placeholder `base_url`

**Date:** April 1, 2026

### Context

Saved test execution still performed one unconditional bootstrap navigation before step execution:

```python
await page.goto(base_url)
```

This conflicted with the Saved Tests frontend contract in `frontend/src/pages/SavedTestsPage.tsx`, which intentionally sends:

```typescript
base_url: 'https://web.three.com.hk' // Base domain (actual URL comes from test steps)
```

The placeholder `base_url` is not the real target page for the generated test. The actual URL lives in the first navigate step, for example:

```text
Navigate to https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/
```

This created a separate failure mode from the Three HK plan-selection issue:

1. `execute_test()` created the browser context correctly.
2. It immediately navigated to `https://web.three.com.hk/` instead of the first real step URL.
3. Playwright waited for the default `load` event.
4. The marketing homepage did not reach `load` within 30000 ms, producing:

```text
Page.goto: Timeout 30000ms exceeded.
Call log:
    - navigating to "https://web.three.com.hk/", waiting until "load"
```

The test then failed **before** it ever reached Step 1, even though the real URL was already present in the generated steps. This is the same placeholder-vs-real-URL gap already identified in ADR-002-13 for HTTP credential injection, but it also affected the initial navigation path.

### Decision

#### ADR-002-22-A: Normalize steps once and reuse them for both credential lookup and initial navigation

Add helper methods in `execution_service.py`:

```python
_normalize_test_steps(raw_steps)
_extract_urls_from_step(step)
_extract_urls_from_steps(steps)
_resolve_http_credentials_from_steps(base_url, steps, explicit_credentials)
_resolve_initial_navigation_url(base_url, steps, detailed_steps)
```

This removes duplicated URL-scanning logic and ensures the same ordered step list is used consistently for:
- UAT credential detection
- initial bootstrap navigation URL resolution

#### ADR-002-22-B: Bootstrap navigation uses the first real URL from `detailed_steps` or `steps`

`_resolve_initial_navigation_url(...)` selects the first real URL in this order:

1. First `detailed_step` where `action == "navigate"` and `value` is a literal HTTP(S) URL
2. First literal HTTP(S) URL embedded anywhere in `detailed_steps`
3. First literal HTTP(S) URL found in ordered `steps`
4. Fallback to `base_url`

This preserves existing behavior for tests that genuinely rely on `base_url`, while fixing Saved Tests runs where `base_url` is intentionally a placeholder.

#### ADR-002-22-C: Initial bootstrap navigation waits for `domcontentloaded`, not full `load`

The initial navigation now uses:

```python
await page.goto(initial_navigation_url, timeout=30000, wait_until="domcontentloaded")
```

Reasoning:
- The bootstrap navigation exists only to land the browser on the correct starting page.
- Later readiness logic already handles loading indicators, modal dismissal, and step-level waits.
- Marketing pages and SPA shells often delay or never complete the full `load` event due to long-tail analytics, ads, or third-party tags.
- `domcontentloaded` is sufficient for the execution engine to start its own readiness logic without the 30 s stall.

### Consequences

**Positive**
- Fixes the `Page.goto("https://web.three.com.hk/") timeout waiting until load` failure.
- Aligns backend behavior with the Saved Tests frontend contract.
- Reuses one consistent URL extraction path for both credentials and navigation.
- Reduces startup latency on heavy landing pages by using `domcontentloaded` for bootstrap navigation.

**Negative**
- URL extraction still relies on literal URLs in generated steps. Variable-only placeholders such as `{{base_url}}` are not resolved here.
- If the first literal URL in the steps is not actually the intended starting page, bootstrap navigation may choose the wrong target. This is acceptable because generated tests are expected to start with a navigate step.

**Alternatives Considered**
- **Keep using `base_url` and rely on Step 1 to navigate later**: Rejected — the execution can fail before Step 1, which is exactly what happened.
- **Require frontend to send the exact URL in `base_url`**: Correct long-term shape, but the existing Saved Tests contract intentionally sends a placeholder and already depends on backend URL extraction.
- **Use `wait_until="load"` on the real step URL**: Still vulnerable to slow marketing/analytics assets and unnecessary for bootstrap.

**Tests added (TDD):** 1 new regression test in `backend/tests/test_execution_service_uat_auto_creds.py`:
- `test_execute_test_initial_navigation_uses_step_url_when_base_url_is_placeholder`

**Total tests impacted:** 19 targeted tests passing for the affected area:
- 7 execution-service UAT credential/bootstrap/browser hardening tests
- 6 new Three HK plan-selection tests
- 1 existing post-click readiness test
- 6 modal auto-dismiss tests

---

## ADR-002-23: Shared Step-Boundary Loading Wait Before Tier Execution

**Date:** April 1, 2026

### Context

The execution engine already waited for loading indicators in post-click readiness flows, but that protection only ran when a tier-specific action path explicitly called the helper.

This left a gap at the boundary between steps:

1. A prior step could trigger a same-page async refresh or a long-running SPA render.
2. The application displayed the Bootstrap loading indicator:

```html
<div role="status" class="spinner-border text-primary"><span class="visually-hidden">Loading...</span></div>
```

3. The next step started immediately because `ThreeTierExecutionService.execute_step()` had no shared readiness gate before dispatching Tier 1.
4. Tier 1, Tier 2, and Tier 3 could all begin against a page that was still visibly loading, leading to false selector misses and avoidable fallbacks.

### Decision

Add `wait_for_step_boundary_readiness(page, logger, timeout_ms)` in `post_click_readiness.py` and call it once at the start of `ThreeTierExecutionService.execute_step()` for every non-`navigate` step.

Implementation details:

- The helper reuses the shared loading-indicator selector set, including `div[role='status'].spinner-border` and `[role='status'].spinner-border`.
- The wait is bounded to 15000 ms per step boundary, followed by a 0.2 s settle.
- The wait runs **once per step**, before Tier 1, not once per tier. This prevents duplicate readiness waits when Tier 1 falls back to Tier 2 or Tier 3.
- `navigate` steps are excluded because the current page does not need to stabilize before a fresh navigation replaces it.

### Consequences

**Positive**
- The Bootstrap spinner now blocks the next non-navigate step until it disappears or the bounded wait is exhausted.
- All fallback strategies benefit because the wait is in the shared orchestrator, not duplicated in per-tier executors.
- Selector misses caused by stepping into a still-loading SPA transition are reduced before any tier is attempted.

**Negative**
- Every non-navigate step now performs a quick loading-indicator probe, adding a small amount of locator overhead even when the page is already idle.
- If an application leaves a matched loading indicator visible for an extended period, step start can now be delayed by up to 15000 ms.
- The mechanism is still selector-based; applications with non-standard loaders require additional selectors.

**Alternatives Considered**
- **Keep the wait only in post-click helpers**: Rejected — not all step-to-step transitions pass through those helpers.
- **Add the wait separately in Tier 1, Tier 2, and Tier 3**: Rejected — duplicates logic and can triple the delay during fallbacks.
- **Run the wait before `navigate` steps as well**: Rejected — the current page's loader does not matter when the next action is a fresh navigation.

**Tests added (TDD):** 3 new targeted tests:
- `backend/tests/test_post_click_readiness.py::test_wait_for_step_boundary_readiness_waits_for_bootstrap_spinner_before_next_step`
- `backend/tests/test_three_tier_execution_service.py::test_execute_step_waits_for_step_boundary_readiness_before_tier1`
- `backend/tests/test_three_tier_execution_service.py::test_execute_step_waits_once_before_fallbacks`

**Total tests impacted:** 4 targeted tests passing for the affected area:
- 2 post-click readiness tests
- 2 three-tier orchestration tests
