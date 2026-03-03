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
- `backend/tests/test_tier2_payment_helpers.py`

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

**Payment field wait after navigation button:**  
Single `page.wait_for_selector(combined_css, state="visible")` call (from ADR-002-4) with bounded timeout, replacing the sequential 10-probe loop.

**`wait_timeout` cap:** `min(self.timeout_ms, 10000)` — no wait can exceed 10s even if `timeout_ms` is set higher.

### Consequences

**Positive**
- Post-click time for navigation buttons reduced from 83s to ~1–3s typical.
- `networkidle` is not waited for navigation buttons — eliminates the longest waits (SPA route changes never reach `networkidle`).
- 0.4s sleep is bounded and explained; 3.0s was unconditional and unexplained.

**Negative**
- 0.4s may be insufficient for very slow backend pages that trigger a cascade of XHR requests. Monitoring required.
- `is_navigation_button` heuristic is keyword-based — custom button labels not in the list still get the full `networkidle` wait.

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

ADR-002-7 and ADR-002-8 carry medium risk because their heuristics (navigation-button keyword list, iframe frame enumeration) depend on real-world page structure diversity. Both should be monitored via tier-level execution metrics across test runs.
