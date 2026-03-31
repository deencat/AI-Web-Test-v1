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
- `backend/app/api/v1/endpoints/executions.py`
- `backend/app/utils/http_auth_credentials.py`
- `frontend/src/components/RunTestButton.tsx`
- `frontend/src/utils/urlUtils.ts`
- `backend/tests/test_execution_service_uat_auto_creds.py`
- `frontend/src/components/__tests__/RunTestButton.test.tsx`
- `backend/tests/test_tier2_payment_helpers.py`
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

ADR-002-7 and ADR-002-8 carry medium risk because their heuristics (navigation-button keyword list, iframe frame enumeration) depend on real-world page structure diversity. ADR-002-11 carries medium risk due to process-global `os.environ` mutation — safe for single-worker deployments but must be revisited when parallel test execution is introduced. All three should be monitored via tier-level execution metrics and LLM provider error rates across test runs.

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
