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
- `backend/app/services/step_progress_guard.py`
- `backend/app/api/v1/endpoints/executions.py`
- `backend/app/utils/http_auth_credentials.py`
- `frontend/src/components/RunTestButton.tsx`
- `frontend/src/utils/urlUtils.ts`
- `backend/tests/test_execution_service_uat_auto_creds.py`
- `frontend/src/components/__tests__/RunTestButton.test.tsx`
- `backend/tests/test_tier2_payment_helpers.py`
- `backend/tests/test_post_click_readiness.py`
- `backend/tests/test_three_tier_execution_service.py`
- `backend/tests/test_step_progress_guard.py`
- `backend/tests/test_stagehand_service_azure_cdp.py`
- `backend/tests/unit/test_universal_llm_azure.py`
- `backend/tests/test_post_click_readiness.py` (extended)
- `backend/tests/test_execution_service_three_tier_logging.py`
- `backend/tests/test_xpath_cache_service.py`
- `backend/tests/test_file_upload.py`

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
24. [ADR-002-24: Modal Backdrop Exclusion from Boundary Loading Detection](#adr-002-24-modal-backdrop-exclusion-from-boundary-loading-detection)
25. [ADR-002-25: Auth-Modal Interactable Fast-Path in Post-Click Readiness](#adr-002-25-auth-modal-interactable-fast-path-in-post-click-readiness)
26. [ADR-002-26: Forward Real Execution ID into ThreeTierExecutionService for Tier Logging](#adr-002-26-forward-real-execution-id-into-threetierexecutionservice-for-tier-logging)
27. [ADR-002-27: Cache-First Payment Field Handling and Session-Normalized Gateway Cache Keys](#adr-002-27-cache-first-payment-field-handling-and-session-normalized-gateway-cache-keys)
28. [ADR-002-28: Scope Business-Action Modal Auto-Dismiss to Nuisance Dialogs](#adr-002-28-scope-business-action-modal-auto-dismiss-to-nuisance-dialogs)
29. [ADR-002-29: Visible Progress Guard for Repeated Confirm Steps](#adr-002-29-visible-progress-guard-for-repeated-confirm-steps)
30. [ADR-002-30: Cross-Platform Upload File Path Extraction from Free-Text Step Descriptions](#adr-002-30-cross-platform-upload-file-path-extraction-from-free-text-step-descriptions)
31. [ADR-002-31: Three HK Plan-Tab SPA Spinner-Settle Before Tab-State Verification](#adr-002-31-three-hk-plan-tab-spa-spinner-settle-before-tab-state-verification)
32. [ADR-002-32: Post-Settle Tab State Re-Verification and Recovery Re-Click](#adr-002-32-post-settle-tab-state-re-verification-and-recovery-re-click)
33. [ADR-002-33: T&C Checkbox Post-Check Verification and Subscribe Now Fast-Fail Guard](#adr-002-33-tc-checkbox-post-check-verification-and-subscribe-now-fast-fail-guard)
34. [ADR-002-34: Bounded Navigate and Loading-Indicator Timeouts to Eliminate SPA Stalls](#adr-002-34-bounded-navigate-and-loading-indicator-timeouts-to-eliminate-spa-stalls)
35. [ADR-002-35: Further Narrow Modal Auto-Dismiss — Move 'I understand' and 'Close' to Conditional, Purge Button-Label Tokens from Nuisance Detector](#adr-002-35-further-narrow-modal-auto-dismiss--move-i-understand-and-close-to-conditional-purge-button-label-tokens-from-nuisance-detector)
36. [ADR-002-36: Expand THREE_HK_PLAN_TAB_LABELS to Cover 4.5G Monthly Plans and 5G Broadband Categories](#adr-002-36-expand-three_hk_plan_tab_labels-to-cover-45g-monthly-plans-and-5g-broadband-categories)

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

**`_try_click_inside_iframe(page, instruction, iframe_xpath) -> bool`**  
First resolves the specific iframe returned by `observe()` via `page.locator(f"xpath={iframe_xpath}").first.element_handle().content_frame()`. If the target frame cannot be resolved, Tier 2 only falls back to generic frame enumeration when there is exactly one non-main frame; it refuses to guess across multiple frames.

Inside the resolved frame, Tier 2 derives button keywords from the instruction (`submit`, `pay`, `continue`, `confirm`, `login`) and tries role-based button lookup before CSS selectors. A plain `submit` instruction stays `submit`; it no longer expands to `pay` unless the instruction explicitly mentions payment/checkout semantics.

```python
selector_candidates = [
    "button[type='submit']", "input[type='submit']", "input[type='image']",
    "button[name*='submit' i]", "button[id*='submit' i]",
    "input[value*='submit' i]", "input[type='button'][value*='submit' i]",
    "[aria-label*='submit' i]", "[title*='submit' i]",
    # plus the same pattern for pay / continue / confirm / login keywords
]
```

For each candidate: `wait_for(state="visible", timeout=1200)`, verify that the control's readable label (`textContent`, `value`, `aria-label`, `title`, `name`, `id`) matches the step keywords, wait briefly for the control to become enabled, click it, then run the shared `wait_for_post_click_readiness()` flow. Mismatched visible controls are skipped and search continues. If the click looks like a navigation/submit action but the URL does not change and the clicked control remains visible, the attempt is treated as unverified and returns `False` instead of reporting success.

**Intercept in `execute_step()`:** When action is `"click"` and `_xpath_targets_iframe()` is True, route to `_try_click_inside_iframe()` before calling `_execute_action_with_xpath()`. On success, return immediately without caching the iframe XPath. On failure, raise a `ValueError` and stop the Tier 2 path instead of clicking the iframe container element itself.

### Consequences

**Positive**
- Handles the most common embedded payment gateway pattern without requiring explicit selectors in test definitions.
- Uses the exact iframe identified by `observe()` when available, which avoids cross-frame false positives.
- Reuses the shared post-click readiness logic so iframe clicks are validated the same way as normal Tier 2 clicks.
- Prevents a generic `submit` step from drifting onto a `pay` control or another visible button whose label does not match the instruction.

**Negative**
- Selector list is heuristic — unusual payment button markup (e.g., `<div onclick>`) is not covered.
- If `observe()` returns an iframe XPath that cannot be resolved and multiple frames exist, Tier 2 now fails instead of guessing.
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
| 002-24 | Exclude modal backdrops from loading detection; `_overlay_has_loading_signal` guard | Accepted | Low |
| 002-25 | Auth-modal interactable fast-path; skip `hidden`/`networkidle` waits when modal stays open | Accepted | Low |
| 002-26 | Forward real `execution_id` into `ThreeTierExecutionService` so `tier_execution_logs` is populated | Accepted | Low |
| 002-27 | Validate cached XPath before payment probes; try page labels before iframe fan-out; normalize sessionized gateway cache keys | Accepted | Low |
| 002-28 | Scope `Confirm` / `Continue` / `Done` auto-dismiss to nuisance/info dialogs only | Accepted | Medium |
| 002-29 | Downgrade repeated confirm clicks to `no_progress` when URL/modal/body state does not advance | Accepted | Medium |
| 002-30 | Extract explicit Windows and POSIX upload paths from free-text step descriptions before falling back to built-in sample files | Accepted | Low |
| 002-31 | Wait for Three HK SPA spinner-border lifecycle to complete before verifying plan-tab state; fixes RC1 (verify-before-settle) and RC2 (non-navigation short-circuit) | Accepted | Low |
| 002-32 | Step-boundary pending-tab-key re-verification after ADR-002-23 spinner clears; recovery re-click when tab has reverted | Accepted | Low |
| 002-33 | Post-check `is_checked()` verification for `check` actions; immediate `ValueError` when Subscribe Now button stays permanently disabled | Accepted | Low |
| 002-34 | Change navigate Tier 2 `wait_until` from `networkidle` to `domcontentloaded`; raise nav-click loading timeout to 20 s; cap non-nav networkidle wait at 3 s | Accepted | Low |
| 002-35 | Move `'I understand'`, `'I Understand'`, and `'Close'` from `SAFE` to `CONDITIONAL` dismiss list; remove button-label tokens (`'i understand'`, `'got it'`, `'information'`) from `NUISANCE_MODAL_TEXT_TOKENS` | Accepted | Low |

ADR-002-24 and ADR-002-25 are low risk: ADR-002-24's overlay guard only fires for the two generic overlay selectors, leaving all other loading indicators unchanged; ADR-002-25's fast-path requires both conditions — URL unchanged and interactive modal visible — to be true simultaneously, which is conservative. ADR-002-26 is a one-line wiring fix with no behavioural change to step execution. All three were applied together to fix the repeated 10–20 s per-step stalls in Execution #637 and to restore tier-level diagnostics.

ADR-002-27 is also low risk: it reorders existing Tier 2 fallbacks rather than introducing new ones, only skips iframe fan-out when no matching payment iframe exists in the DOM, and normalizes only the sessionized gateway path segment for XPath cache keys. Non-payment steps and non-sessionized URLs are unchanged.

ADR-002-28 narrows ADR-002-20's original modal helper by splitting dismiss buttons into a safe list and a business-action list. `Confirm`, `Continue`, and `Done` are now auto-clicked only when the dialog text matches nuisance/info tokens such as reminder, notice, session-timeout, or maintenance messaging. This preserves the Three HK reminder-modal fix while avoiding silent consumption of business confirmation chains.

ADR-002-29 adds a shared confirm-step progress guard in `ThreeTierExecutionService`. For `click` steps whose instruction contains `confirm`, a small pre/post snapshot of URL, visible modal text, and page-body text is compared after any apparent tier success. If the UI did not visibly advance, the result is downgraded to `error_type=no_progress` and normal fallback continues.

ADR-002-30 is low risk: the two new helpers only replace a narrower regex that missed Windows paths; POSIX paths and structured `file_path` fields in `detailed_steps` are unaffected. The keyword-based sample-file fallback is preserved as the last resort when no explicit path is present in the step text.

ADR-002-32 is low risk: the pending-key mechanism only activates when a Three HK UAT tab-click step has previously been recorded, and the recovery re-click is bounded to one attempt with `_wait_for_spa_spinner_settle` afterwards. Non-Three-HK steps are entirely unaffected. ADR-002-33 is also low risk: the `is_checked()` post-verification adds one Playwright API call after every `check` action (fast path skips if already checked); the Subscribe Now guard replaces a silent disabled-button wait loop with an immediate failure, which surfaces bugs earlier without affecting any other button type. ADR-002-34 is low risk: `domcontentloaded` resolves correctly on all sites tested; the higher nav-click loading timeout gives slow post-click spinners (like Three HK document-upload) more room without affecting fast pages (they complete well under 20 s); the shorter non-nav networkidle cap does not affect pages that reach networkidle quickly (they resolve before 3 s in practice).

ADR-002-35 is low risk: the change only tightens when dismissal fires — it never removes the ability to dismiss nuisance modals. The Three HK preprod reminder ("Reminder" or "Notice" in body text) still passes `_modal_allows_business_autodismiss` and is dismissed as before. The risk of a nuisance modal that truly requires an unconditional `Close` or `I understand` click being missed is accepted; such modals should instead have their text adjusted or an explicit test step added.

ADR-002-7, ADR-002-8, ADR-002-19, ADR-002-20, ADR-002-21, ADR-002-28, and ADR-002-29 carry medium risk because their heuristics depend on real-world page structure diversity and environment-specific flow behavior. ADR-002-11 carries medium risk due to process-global `os.environ` mutation — safe for single-worker deployments but must be revisited when parallel test execution is introduced. ADR-002-22, ADR-002-23, and ADR-002-27 are low risk because they reuse existing URL extraction, loading-indicator, and Tier 2 fallback mechanisms rather than introducing new execution tiers or unbounded waits. These decisions should be monitored via tier-level execution metrics and environment-specific failure rates across test runs.

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

> Note: ADR-002-20 records the baseline modal auto-dismiss mechanism introduced for Three HK preprod gating dialogs. The original broad `Confirm` / `Continue` / `Done` allowlist later proved too permissive for repeated business confirmation chains and was narrowed by ADR-002-28.

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
- The original broad dismiss-button list can consume later business-flow confirmation buttons that happen to be labeled `Confirm`, `Continue`, or `Done`. This exact failure mode was observed in Execution #637 and is narrowed by ADR-002-28.

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

---

## ADR-002-24: Modal Backdrop Exclusion from Boundary Loading Detection

**Date:** April 2, 2026

### Context

Root-cause analysis of Execution #637 (Three HK login flow) identified that the `wait_for_step_boundary_readiness()` gate introduced in ADR-002-23 caused 15-second stalls before every non-navigate step in the login sequence.

The login modal in Three HK's preprod site keeps a semi-transparent backdrop element in the DOM while the modal is open. That backdrop matches the generic overlay selector `[class*='overlay']` and `.overlay` from `LOADING_SELECTORS`. Because the backdrop is a permanent modal decoration, not a transient loading overlay, it never disappears — so every fill or click step inside the modal blocked for the full `STEP_BOUNDARY_LOADING_TIMEOUT_MS = 15000 ms` before timing out and continuing.

Steps 3, 5 in Execution #637 each showed exactly 15.6 seconds, matching the hard cap. The page was fully interactable throughout; there was no actual loading in progress.

### Decision

Generic overlay selectors (`[class*='overlay']` and `.overlay`) are treated as loading blockers **only** when the element also exhibits at least one real loading signal:

- `aria-busy="true"` attribute on the element, **or**
- A class or id hint containing one of `loading`, `spinner`, `skeleton`, `shimmer`, **or**
- A descendant matching `[role='status']`, `[aria-busy='true']`, `[class*='spinner']`, `[class*='loading']`, `.spinner`, or `.loading`.

**Implementation in `post_click_readiness.py`:**

Two module-level constants are added:

```python
GENERIC_OVERLAY_SELECTORS = {"[class*='overlay']", ".overlay"}
LOADING_SIGNAL_TOKENS = ("loading", "spinner", "skeleton", "shimmer")
```

A new async helper `_overlay_has_loading_signal(locator) -> bool` checks the three signal categories above.

Inside `wait_for_loading_indicators_to_clear()`, a guard is inserted before any wait is issued for generic overlays:

```python
if selector in GENERIC_OVERLAY_SELECTORS and not await _overlay_has_loading_signal(loading_element):
    logger.debug("Ignoring non-loading overlay while checking readiness: %s", selector)
    continue
```

All other selectors in `LOADING_SELECTORS` (spinners, skeletons, specific loading classes, `aria-busy`) are unaffected.

### Consequences

**Positive**
- Steps 3 and 5 of the Three HK login flow no longer stall for 15 seconds; the modal backdrop is correctly skipped.
- The fix is minimal and contained inside one helper — all other loading-indicator detection is unchanged.
- `aria-busy`, spinner, and skeleton selectors continue to block correctly.

**Negative**
- An overlay element that genuinely blocks UI but uses none of the standard loading signal attributes or classes will no longer be waited on. This scenario is atypical (non-standard loader), and Tier 2/observe retry logic already handles transient page availability issues.
- `_overlay_has_loading_signal` performs up to nine additional locator queries per visible overlay hit. In practice, the boundary wait is fast when no overlay is present (count check exits immediately).

**Alternatives Considered**
- **Remove overlay selectors from `LOADING_SELECTORS` entirely**: Would miss real loading overlays on other sites that rely on `[class*='overlay']` without a spinner child.
- **Use stricter overlay selectors (e.g. `[class*='loading-overlay']`)**: Reduces false positives but misses sites with custom class naming.
- **Rename selectors with a combined rule**: Combining `[class*='overlay'][aria-busy='true']` into `LOADING_SELECTORS` is cleaner but doesn't handle the descendant spinner signal case.

**Tests added (TDD):**
- `backend/tests/test_post_click_readiness.py::test_wait_for_step_boundary_readiness_ignores_modal_backdrop_overlays` — overlay present, no loading signals → `wait_for` NOT called.
- `backend/tests/test_post_click_readiness.py::test_wait_for_loading_indicators_waits_for_busy_overlay` — overlay present with `aria-busy=true` → `wait_for` IS called.

---

## ADR-002-25: Auth-Modal Interactable Fast-Path in Post-Click Readiness

**Date:** April 2, 2026

### Context

The same Execution #637 analysis showed that click steps inside the Three HK login modal (Steps 4 and 6 — the "Login" button submissions) each consumed 24–30 seconds.

The login flow uses a **same-URL popup modal**: clicking the Login button inside the modal does not navigate away; instead the modal's content changes (e.g., from email entry to password entry). The URL remains unchanged.

Because the button instruction and element text both matched `AUTH_KEYWORDS` (`login`), `wait_for_post_click_readiness()` entered the auth-click path in `post_click_readiness.py`:

1. `clicked_element.wait_for(state="hidden", timeout=5000)` — waited 5 s because the Login button is replaced by the password form but the locator remains "visible" from Playwright's perspective until garbage-collected.
2. `page.wait_for_load_state("networkidle", timeout=5000)` — waited up to 5 s; a modal content swap does not trigger a full network idle.
3. `wait_for_loading_indicators_to_clear(page, timeout=8000)` — ran the full selector scan before the 0.4 s settle.

The modal remained open and its fields were immediately interactable after the click; there was no actual page transition or network activity requiring these waits.

### Decision

Add a fast-path check **before** the auth-click hidden/networkidle waits: if the URL has not changed and a modal/dialog with interactive child elements is still visible and interactable, skip directly to the caller without issuing any hidden or networkidle wait.

**New async helper `_visible_interactable_modal_present(page) -> bool`:**

Iterates `MODAL_CONTAINER_SELECTORS` (`.modal.show`, `[role='dialog']`, `[aria-modal='true']`). For each visible container, checks whether it has at least one descendant matching:

```python
INTERACTABLE_MODAL_CHILD_SELECTOR = (
    "input, button, textarea, select, "
    "[contenteditable='true'], [role='button']"
)
```

Returns `True` if any visible container has interactive children, `False` otherwise.

**Fast-path guard inserted in `wait_for_post_click_readiness()`** immediately before the auth wait block:

```python
if classification["is_auth_click"] and not url_changed:
    if await _visible_interactable_modal_present(page):
        logger.info(
            "Auth modal remained interactable after click; "
            "skipping hidden/networkidle waits"
        )
        return classification
```

When this condition fires: no `wait_for(state="hidden")`, no `wait_for_load_state("networkidle")`, no loading-indicator scan. The step completes as soon as the fast-path returns.

### Consequences

**Positive**
- Steps 4 and 6 in the Three HK login modal flow no longer incur 10–15 seconds of redundant waits; the fast path returns within milliseconds of the modal content update.
- The logic is conservative: it only short-circuits when both conditions hold simultaneously — URL unchanged AND interactable modal still visible. A real page transition (URL changes) or a dismissing modal (becomes invisible) will still run the full auth-click readiness path.
- No change to non-auth clicks or to auth clicks that do trigger a page navigation.

**Negative**
- If a site's login button both closes the modal AND then immediately shows a new modal in the same pass, the fast-path may return too early. This is an edge case; the call to `wait_for_loading_indicators_to_clear` that follows would normally catch any subsequent spinner.
- The selector `INTERACTABLE_MODAL_CHILD_SELECTOR` is broad. An informational modal with a button counts as "interactable". The guard is further protected by the `not url_changed` condition, which ensures no navigation occurred.

**Alternatives Considered**
- **Detect modal content change via MutationObserver JS**: Accurate but requires JS injection into every page, crosses Playwright API boundaries, and is harder to unit-test.
- **Lower `auth_timeout` from 5000ms to 500ms**: Reduces the wait but still adds 500 ms per auth step unnecessarily; does not fix the root cause.
- **Remove `wait_for(state="hidden")` for auth clicks entirely**: Regresses other flows where the modal does close after login (e.g. correct full-page login flows that navigate away). The fast-path condition is safer.

**Tests added (TDD):**
- `backend/tests/test_post_click_readiness.py::test_wait_for_post_click_readiness_skips_auth_wait_for_interactable_modal_transition` — auth click, URL unchanged, visible modal with interactive child → `clicked_element.wait_for` NOT awaited, `page.wait_for_load_state` NOT awaited.

---

## ADR-002-26: Forward Real Execution ID into ThreeTierExecutionService for Tier Logging

**Date:** April 2, 2026

### Context

Post-execution diagnosis of Execution #637 revealed that the `tier_execution_logs` table was empty for that run. The schema and `_log_tier_execution()` implementation in `ThreeTierExecutionService` were both correct; the problem was the call site in `execution_service.py`:

```python
# execution_service.py line 1171 (before fix)
result = await self.three_tier_service.execute_step(
    step=step_data,
    execution_id=None,  # Will add execution_id later if needed
    step_index=step_number - 1
)
```

`ThreeTierExecutionService.execute_step()` only calls `_log_tier_execution()` when **both** `execution_id is not None` and `step_index is not None`. Because `execution_id=None` was always passed, no log rows were ever written — regardless of how many tiers were attempted. This made post-run tier analysis and performance diagnosis impossible from the database.

The comment `# Will add execution_id later if needed` indicates the wiring was intentionally deferred and never followed up.

### Decision

Pass the real `execution_id` parameter received by `_execute_step()` directly to `three_tier_service.execute_step()`. No new infrastructure is required; the plumbing was already correct end-to-end.

**Change in `execution_service.py`:**

```python
# Before
result = await self.three_tier_service.execute_step(
    step=step_data,
    execution_id=None,  # Will add execution_id later if needed
    step_index=step_number - 1
)

# After
result = await self.three_tier_service.execute_step(
    step=step_data,
    execution_id=execution_id,
    step_index=step_number - 1
)
```

`_execute_step()` already receives `execution_id` as a parameter (set correctly by both the main step loop and the loop-step path in `execute_test()`), so no signature changes are needed elsewhere.

### Consequences

**Positive**
- `tier_execution_logs` is now populated for every step of every execution, enabling:
  - Per-step tier breakdown (`tier1_time_ms`, `tier2_time_ms`, `tier3_time_ms`).
  - Tier fallback reason analysis (`tier1_error`, `tier2_error`).
  - Strategy effectiveness tracking over time.
- Supports the `track_strategy_effectiveness` and `track_fallback_reasons` flags already present in `ExecutionSettings`.
- Zero behavioural change to step execution — the log write is async fire-and-forget inside `_log_tier_execution()`.

**Negative**
- Adds one database INSERT per step per execution. For a 47-step test like Execution #637, this is 47 extra rows per run — negligible overhead.
- Historical executions (before this fix) have no tier log rows and cannot be retroactively populated.

**Alternatives Considered**
- **Add a post-execution batch log-write**: Would reconstruct tier data from in-memory history at execution end rather than per step. More fragile (requires keeping history in memory for the full run) and loses timing precision.
- **Log tiers in `execution_service` rather than `three_tier_service`**: Duplicates logging logic; the 3-tier service already owns `_log_tier_execution()` and the per-tier timing data.
- **Keep `execution_id=None` and use a separate logging decorator**: Over-engineering a one-line fix.

**Tests added (TDD):**
- `backend/tests/test_execution_service_three_tier_logging.py::test_execute_step_passes_execution_id_to_three_tier_service` — verifies `three_tier_service.execute_step` is awaited with `execution_id=637` (not `None`) when `_execute_step(execution_id=637)` is called.

---

## ADR-002-27: Cache-First Payment Field Handling and Session-Normalized Gateway Cache Keys

**Date:** April 2, 2026

### Context

Follow-up analysis of Execution #637 showed that the worst remaining payment/autopay stalls were no longer caused by page rendering delays. The target fields were already visible and interactable, but Tier 2 still spent 36–78 seconds inside its own payment helper before reporting success.

Four gaps were identified in the Tier 2 flow:

1. **Validated cache hits still paid the payment-probe cost** — `Tier2HybridExecutor.execute_step()` ran payment readiness and `_try_payment_field_action()` before checking the XPath cache. For known instructions on stable pages, this meant the executor spent time probing CSS selectors and labels even though a valid cached XPath already existed.

2. **Page labels were tried after iframe fan-out** — `_try_payment_field_action()` tried page CSS selectors, then iframe CSS selectors, and only then attempted page labels. On the Mastercard gateway page, the correct field was often found by a simple page label such as `Cardholder name` or `Security code`, but only after multiple failed 3-second iframe probes.

3. **Single-field expiry inputs had no label fallback** — combined expiry fill steps such as `Input exp. Date. 01/39` had CSS selector support, but no label candidates. When the selectors missed, the helper fell through to cached XPath or `observe()` only after the full probe loop.

4. **Sessionized gateway URLs fragmented the XPath cache** — `XPathCacheService.generate_cache_key()` used the full payment gateway URL. Mastercard gateway paths include a unique session token (`/checkout/pay/SESSION...`), so each run created a new cache key and historical gateway XPath entries accumulated with `hit_count=0`.

### Decision

#### ADR-002-27-A: Check validated cache entries before payment direct handling

In `Tier2HybridExecutor.execute_step()`, the XPath cache lookup and validation now run before payment readiness and `_try_payment_field_action()`. Payment direct handling only runs when there is no validated cache hit.

This preserves the existing self-healing path: stale cache entries are still invalidated and re-extracted, but stable payment/autopay instructions no longer pay the direct-probe cost on every run.

#### ADR-002-27-B: Prefer page labels before iframe fan-out

Within `_try_payment_field_action()`, page-local labels are now attempted before any iframe probing. The helper still tries page CSS selectors first, but if those miss it moves directly to `page.get_by_label(...)` instead of enumerating iframe selectors first.

This reorders existing fallback logic rather than adding a new tier. The goal is to take the cheapest high-signal match first and only inspect iframe contents when page-local strategies have failed.

#### ADR-002-27-C: Add label fallback for single Exp. Date inputs

For combined expiry fill instructions (`fill` / `type` / `input` with `exp. date`, `exp date`, `expiry`, or `expiration`), page-label candidates are added:

```python
[
    "Exp. Date (MM/YY)",
    "Exp. Date (MM/YYYY)",
    "Exp. Date",
    "Expiry date",
    "Expiration date",
    "Exp date",
]
```

This lets the helper resolve standard labeled expiry inputs without falling back to iframe probing or `observe()`.

#### ADR-002-27-D: Only inspect iframe candidates that actually exist

Before building frame-locator probes, Tier 2 now checks whether each payment iframe selector exists in the DOM. If no matching iframe is present, iframe fan-out is skipped entirely.

This avoids paying iframe probe time on same-document payment forms and on gateway pages where the target fields are not actually inside one of the known iframe patterns.

#### ADR-002-27-E: Normalize sessionized gateway URLs before hashing XPath cache keys

`XPathCacheService` now normalizes cacheable URLs before computing the SHA256 cache key. For payment gateway paths matching:

```text
/checkout/pay/SESSION<token>
```

the session token is collapsed to a stable placeholder:

```text
/checkout/pay/SESSION
```

The normalized URL is then combined with the instruction:

```python
normalized_page_url = XPathCacheService.normalize_cacheable_url(page_url)
key_string = f"{normalized_page_url}::{instruction}"
```

This preserves instruction-level specificity while allowing successive Mastercard sessions to reuse the same XPath cache entry.

### Consequences

**Positive**
- Stable cached payment/autopay steps now bypass the slow direct payment probe loop entirely.
- Cardholder, CVV, and combined expiry fields resolve faster on pages where labels are more reliable than attribute-based selectors.
- Same-page payment forms no longer pay iframe fan-out costs when no matching iframe exists.
- Gateway XPath cache entries can now accumulate real reuse (`hit_count`) across different sessionized Mastercard URLs instead of staying fragmented at zero hits.

**Negative**
- Reordering the helper means a stale but still semantically valid cached XPath will be preferred over a potentially simpler direct selector until that cache entry fails and is invalidated.
- The new expiry label list is heuristic; uncommon localized labels still require selector or `observe()` fallback.
- URL normalization is intentionally narrow. It covers the known `/checkout/pay/SESSION...` pattern only; other providers with different sessionized path shapes still need explicit normalization rules if reuse becomes important.

**Alternatives Considered**
- **Keep payment probes ahead of cache lookup**: Rejected because validated cache hits would continue to pay unnecessary 36–78 second probe costs.
- **Skip iframe probing entirely for payment helpers**: Rejected because real cross-origin iframe-hosted payment widgets still need this fallback.
- **Normalize the entire payment gateway URL to hostname-only**: Rejected because it risks merging unrelated gateway flows that share a host but not a page shape.
- **Add Three-HK-specific hardcoded selectors only**: Rejected because the observed issue was about fallback ordering and cache fragmentation, not the absence of site-specific selectors.

**Tests added (TDD):**
- `backend/tests/test_tier2_payment_helpers.py::TestTier2PaymentHelpers::test_execute_step_prefers_cached_xpath_before_payment_probes`
- `backend/tests/test_tier2_payment_helpers.py::TestCombinedExpiryFill::test_combined_expiry_fill_uses_page_label_fallback_before_iframe_probes`
- `backend/tests/test_tier2_payment_helpers.py::TestPaymentFieldProbeOrdering::test_page_labels_are_tried_before_iframe_probes`
- `backend/tests/test_tier2_payment_helpers.py::TestPaymentFieldProbeOrdering::test_iframe_probes_are_skipped_when_no_payment_iframe_exists`
- `backend/tests/test_xpath_cache_service.py::test_generate_cache_key_normalizes_mastercard_session_urls`
- `backend/tests/test_xpath_cache_service.py::test_generate_cache_key_keeps_instruction_specificity_after_gateway_normalization`
- `backend/tests/test_xpath_cache_service.py::test_generate_cache_key_does_not_merge_gateway_and_autopay_pages`

---

## ADR-002-28: Scope Business-Action Modal Auto-Dismiss to Nuisance Dialogs

**Date:** April 2, 2026

> Note: ADR-002-28 records the first round of narrowing applied to ADR-002-20's original broad dismiss-button list. Two further narrowings — moving `'I understand'`/`'Close'` to CONDITIONAL and purging button-label tokens from `NUISANCE_MODAL_TEXT_TOKENS` — were made in response to Executions #689 and #692 and are recorded in ADR-002-35.

### Context

Execution #637 on the Three HK flow exposed a second-order effect of ADR-002-20's broad modal helper. The system did not have an outer "retry the same step three times" loop. Instead, repeated plain-text confirm steps were vulnerable to being collapsed because one logical step could both:

1. Click a business `Confirm` button as intended, then
2. Enter post-click readiness where `confirm` still classified the action as navigation-like, and
3. Opportunistically auto-dismiss the next visible modal because `auto_dismiss_blocking_modals()` treated `Confirm`, `Continue`, and `Done` as universal dismiss labels.

That behavior was correct for nuisance gates such as the Three HK reminder dialog introduced by ADR-002-20, but too permissive for business dialogs where the product flow genuinely requires multiple sequential confirmations. In those cases, the readiness helper could silently consume the next required confirmation before the next test step started.

### Decision

Keep the existing modal auto-dismiss call sites from ADR-002-20, but narrow what counts as safe to auto-click.

#### ADR-002-28-A: Split dismiss buttons into always-safe and conditional groups

`post_click_readiness.py` defines (as of this ADR; see ADR-002-35 for subsequent narrowing):

```python
SAFE_MODAL_DISMISS_BUTTON_TEXTS = [
    "I understand",
    "I Understand",
    "OK",
    "Ok",
    "Close",
    "Dismiss",
    "Got it",
    "Accept",
    "Agree",
]

CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS = [
    "Confirm",
    "Continue",
    "Done",
]
```

`auto_dismiss_blocking_modals()` always tries the safe list. It only considers the conditional list when the modal itself looks like a nuisance/info blocker rather than business flow UI.

#### ADR-002-28-B: Gate business-action auto-dismiss behind nuisance-modal text detection

The helper now inspects normalized modal text through `_modal_allows_business_autodismiss(modal)` and only unlocks the conditional button list when the dialog text contains one of:

```python
NUISANCE_MODAL_TEXT_TOKENS = (
    "reminder",
    "notice",
    "informational",
    "information",
    "session expired",
    "session timeout",
    "timed out",
    "maintenance",
    "security reminder",
    "i understand",
    "got it",
)
```

This preserves the original Three HK reminder-modal behavior while preventing generic business `Confirm` / `Continue` / `Done` buttons from being auto-clicked by default.

> Note: `NUISANCE_MODAL_TEXT_TOKENS` as defined in this ADR included `"i understand"` and `"got it"` as tokens. Those were later removed by ADR-002-35 because they are button labels, not modal-purpose indicators.

#### ADR-002-28-C: Do not remove `confirm` from navigation readiness classification

`confirm` remains part of `NAVIGATION_KEYWORDS`. The goal of this change is not to skip readiness logic for confirm-like actions, because some confirm buttons genuinely trigger page transitions or server round-trips. The change is intentionally scoped to the auto-dismiss side effect only.

### Consequences

**Positive**
- Preserves the original nuisance-modal recovery from ADR-002-20 for reminder/info dialogs that gate entry into a flow.
- Prevents post-click readiness from silently consuming business confirmation chains by default.
- Keeps the same call sites and readiness sequencing, so the behavior change is isolated to one helper.

**Negative**
- Nuisance detection is text-heuristic based. A real reminder/info modal with unusual wording may no longer auto-dismiss if its text does not match `NUISANCE_MODAL_TEXT_TOKENS`.
- Localized or redesigned dialogs may require token-list maintenance over time.
- Because `confirm` remains a navigation keyword, confirm steps still go through post-click readiness; they are simply no longer allowed to auto-click the next business dialog unless the modal looks informational.

**Alternatives Considered**
- **Remove `confirm` / `continue` from `NAVIGATION_KEYWORDS` entirely**: Rejected. This would suppress legitimate readiness waits for real confirmation submits and navigation steps.
- **Disable modal auto-dismiss globally**: Rejected. That would regress the original Three HK reminder-modal fix from ADR-002-20.
- **Encode every nuisance modal as an explicit generated test step**: Rejected. These dialogs are environment-specific and would make tests less portable between production and preprod.

**Tests added (TDD):**
- `backend/tests/test_post_click_modal_dismiss.py::test_business_confirm_modal_is_not_auto_dismissed`
- `backend/tests/test_post_click_modal_dismiss.py::test_reminder_confirm_modal_can_still_be_auto_dismissed`

---

## ADR-002-29: Visible Progress Guard for Repeated Confirm Steps

**Date:** April 2, 2026

### Context

Narrowing modal auto-dismiss fixed the most aggressive collapse path, but it did not solve the more general ambiguity of repeated selectorless confirm steps.

In Execution #637, the test case contained multiple business steps that were effectively variations of `Click Confirm`. For those steps, Tier 1 / Tier 2 / Tier 3 success criteria were action-level rather than business-level:

- Tier 1 considered the step successful if it could click the selector supplied by the test data.
- Tier 2 and Tier 3 considered the step successful if the inferred click completed without throwing and the usual readiness waits settled.

That was insufficient for repeated confirm chains because the engine had no shared post-condition proving that confirm #1, confirm #2, and confirm #3 each advanced the UI. A click could technically succeed while leaving the browser on the same modal or same page state, causing the step to be recorded as `PASS` and letting later business confirmations drift out of sync.

### Decision

Add a small, tier-agnostic visible-progress check for repeated confirm clicks and enforce it in the shared 3-tier orchestrator.

#### ADR-002-29-A: Add `step_progress_guard.py` with compact UI snapshots

New helper module: `backend/app/services/step_progress_guard.py`

```python
@dataclass(frozen=True)
class StepProgressSnapshot:
    url: str
    modal_signature: str
    body_signature: str
```

`capture_step_progress_snapshot(page)` records:
- Current `page.url`
- Normalized text from the first visible modal/dialog, if one exists
- Otherwise, a trimmed normalized body-text signature

The snapshot is intentionally small and text-based so it can be captured cheaply and compared across tiers.

#### ADR-002-29-B: Only enforce the guard for repeated confirm clicks

`should_enforce_confirm_progress(step)` is intentionally narrow:

```python
action == "click" and "confirm" in instruction.lower()
```

This avoids changing the success contract for unrelated clicks. The guard targets the specific failure mode observed in Three HK: multiple business confirmations with near-identical natural-language instructions and no selector-level disambiguation.

#### ADR-002-29-C: Apply the guard once in `ThreeTierExecutionService`, not separately in each tier

`ThreeTierExecutionService.execute_step()` now captures one pre-step snapshot after the shared step-boundary readiness wait. Whenever Tier 1, Tier 2, or Tier 3 reports success, `_step_made_expected_progress()` captures a second snapshot and calls `has_confirm_step_progress(...)`.

Progress is accepted when any of the following is true:
- URL changed
- Visible modal signature changed
- No modal was present and the body signature changed

When none of those conditions is true, `_mark_no_progress_failure()` converts the apparent success into:

```python
{
    "success": False,
    "error_type": "no_progress",
    ...
}
```

Fallback then continues normally according to Option A / B / C, and if no tier produces visible progress the final step result is a real failure instead of a false-positive pass.

### Consequences

**Positive**
- Prevents repeated confirm steps from being marked successful when the UI did not visibly advance.
- Covers Tier 1, Tier 2, and Tier 3 uniformly because the check lives in the shared orchestrator.
- Preserves the existing fallback strategy semantics: a no-progress result is treated like any other tier failure and can escalate to the next tier.

**Negative**
- The guard is heuristic. Purely visual changes with identical text and unchanged URL may still look like "no progress" to the snapshot comparison.
- A legitimate confirm step that intentionally keeps the same visible text may escalate unnecessarily.
- The scope is currently limited to instructions containing `confirm`. Similar repeated chains based on `continue` or `next` are not covered until there is evidence that they need the same protection.

**Alternatives Considered**
- **Add a generic three-times retry loop around every step**: Rejected. That would mask root causes and make it easier for one logical step to consume multiple downstream actions.
- **Implement site-specific confirm counters for Three HK only**: Rejected. The failure mode is structural and should be handled at the shared orchestration layer.
- **Require every generated confirm step to include selectors or explicit post-conditions**: Long-term desirable, but not sufficient for existing tests and not something the runtime executor can assume today.

**Tests added (TDD):**
- `backend/tests/test_step_progress_guard.py::test_has_confirm_step_progress_returns_false_when_modal_state_is_unchanged`
- `backend/tests/test_step_progress_guard.py::test_has_confirm_step_progress_returns_true_when_modal_changes`
- `backend/tests/test_three_tier_execution_service.py::test_execute_step_escalates_when_confirm_click_makes_no_progress`

**Targeted validation:** 18 impacted tests passed across `test_post_click_modal_dismiss.py`, `test_step_progress_guard.py`, `test_three_tier_execution_service.py`, and adjacent readiness/orchestration suites.

---

## ADR-002-30: Cross-Platform Upload File Path Extraction from Free-Text Step Descriptions

**Date:** April 9, 2026

### Context

When a test step description contains a natural-language instruction such as:

```
Upload the HKID document from the local file system C:\test_RNR\HKID-Sample.jpeg
```

`ExecutionService._execute_step()` must resolve a `file_path` value before the step is forwarded to the 3-tier engine. The original logic attempted extraction with a single regex before falling back to built-in keyword-based sample files:

```python
file_path_pattern = r'(/[\w\-/.]+\.(pdf|jpg|jpeg|png|gif|doc|docx|xls|xlsx|txt|csv))\b'
file_path_match = re.search(file_path_pattern, step_description, re.IGNORECASE)
```

This pattern only matched POSIX-style absolute paths starting with `/`, using word characters, hyphens, forward slashes, and periods. A Windows absolute path fails to match because it uses:

- A drive letter and colon prefix (`C:`)
- Backslash directory separators (`\`)
- Spaces in directory or file names (e.g. `My Documents\HKID Sample.jpg`)
- Filenames with hyphens not immediately preceded by a `/` (e.g. `HKID-Sample-Blank.jpeg`)

When the match failed, the fallback keyword scan saw `"hkid"` in the description and silently substituted the built-in sample file:

```
file_path: '/home/dt-qa/.../backend/test_files/hkid_sample.pdf'
```

The debug log revealed the mismatch:

```
[DEBUG] Calling 3-Tier with {
  'action': 'upload_file',
  'selector': "input[type='file']",
  'value': None,
  'file_path': 'C:\\AI-Web-Test-v1\\backend\\test_files/hkid_sample.pdf'
}
```

The step's explicitly stated path was discarded. The test was uploading a backend sample file instead of the user's test file.

**Scope:** this only affects natural-language upload steps where `file_path` is absent from the structured `detailed_steps` payload. Structured steps with an explicit `file_path` field bypass extraction entirely and are unaffected.

### Decision

Replace the single inline regex with two focused private helpers and move the upload resolution block outside the action-detection `elif` chain so it applies unconditionally whenever `step_data["action"] == "upload_file"`.

#### `_extract_upload_file_path_from_description(step_description) -> Optional[str]`

Extracts an explicit file path from natural-language step text. Priority order:

1. **Quoted candidates first** — extract all text inside `"..."` or `'...'` and accept the first one that matches the absolute-path pattern. Handles paths with spaces or special characters:
   ```
   "C:\Test User\My Documents\passport sample.jpg"
   ```

2. **Unquoted Windows absolute path** — matches `[A-Za-z]:\...` followed by a supported extension, terminated by whitespace, punctuation, or end of string:
   ```
   C:\old_Drive\RNR\test_RNR\HKID-Sample-Blank-66.jpeg
   ```

3. **Unquoted POSIX absolute path** — matches `/...` followed by a supported extension. Preserves the original regex intent for Linux/Docker paths:
   ```
   /app/test_files/hkid_sample.pdf
   ```

Returns `None` when no explicit path is found, triggering the keyword fallback.

#### `_get_default_upload_file_path(step_description) -> str`

Isolates the keyword-based sample-file fallback that previously lived inline. Unchanged behavior:

| Keyword in description | Default file |
|---|---|
| `passport` | `{base_path}/passport_sample.jpg` |
| `hkid` | `{base_path}/hkid_sample.pdf` |
| `address` or `proof` | `{base_path}/address_proof.pdf` |
| _(any other)_ | `{base_path}/passport_sample.jpg` |

`base_path` is `/app/test_files` when running inside Docker, otherwise the absolute path of `backend/test_files/` on the host.

#### Dispatch in `_execute_step()`

```python
if step_data["action"] == "upload_file":
    if not step_data.get("file_path"):
        extracted = self._extract_upload_file_path_from_description(step_description)
        if extracted:
            step_data["file_path"] = extracted
            logger.info(f"[Extracted from description] File path: {step_data['file_path']}")
        else:
            step_data["file_path"] = self._get_default_upload_file_path(step_description)
            logger.info(f"[Auto-detected from keywords] File upload with file_path: ...")
    else:
        logger.info(f"[User-specified in detailed_step] File upload with file_path: ...")

    if not step_data["selector"]:
        step_data["selector"] = "input[type='file']"
```

The block is placed after the `elif "upload" in desc_lower:` action-detection branch and guards on `action == "upload_file"`, so existing detection for both free-text upload descriptions and pre-classified structured steps uses the same path.

### Consequences

**Positive**
- Windows absolute paths in free-text step descriptions are now preserved and forwarded to the 3-tier engine unchanged.
- Quoted paths with spaces (e.g. `"C:\Test User\My Docs\file.jpg"`) are handled correctly.
- Existing POSIX absolute paths (e.g. `/app/test_files/hkid_sample.pdf`) continue to work exactly as before.
- Structured `detailed_steps` entries with an explicit `file_path` are not affected — the upload block only runs when `file_path` is absent or empty.
- The keyword-based sample-file fallback is preserved as a last resort when no explicit path appears anywhere in the step text.
- Both helpers are small, independently testable, and have no side effects.

**Negative**
- Tier executors (`Tier1PlaywrightExecutor`, `Tier2HybridExecutor`, `Tier3StagehandExecutor`) validate the resolved path with `os.path.exists()` at execution time. A Windows path forwarded to a Linux backend runtime will still fail at that point because the path does not exist on the server. This is a deployment concern, not a parsing concern, and cannot be fixed in the parser.
- Unquoted Windows paths containing characters outside `[^\r\n]` stop matching at the first line break — acceptable because step descriptions are never multi-line.
- A step description that contains two valid-looking absolute paths (e.g. `"Move file from /source/file.pdf to /dest/file.pdf"`) returns the first match. This is unlikely in practice because upload steps are single-purpose.

**Alternatives Considered**
- **Extend the original inline regex to also handle Windows paths**: A single regex covering both POSIX and Windows paths with optional quoting becomes long and hard to reason about. Splitting into two helpers keeps each case readable.
- **Require users to always put the path in `detailed_steps.file_path`**: Correct long-term contract; the extraction is a convenience layer for test steps generated without a structured `file_path`. Removing it would break all existing upload steps written as plain natural language.
- **Normalise Windows paths to POSIX before storing**: Path normalisation on the backend cannot work because cross-OS path semantics differ — a Windows drive letter has no POSIX equivalent on the server filesystem.

**Tests added (TDD):**  
3 new tests in `backend/tests/test_execution_service_three_tier_logging.py`:
- `test_execute_step_extracts_windows_upload_path_from_step_description` — unquoted Windows path in description is forwarded unchanged to `three_tier_service.execute_step`.
- `test_execute_step_extracts_quoted_windows_upload_path_with_spaces` — quoted Windows path with spaces in directory name is extracted without the surrounding quotes.
- `test_execute_step_preserves_posix_upload_path_from_step_description` — existing POSIX absolute path continues to be extracted correctly (regression guard).

**Total tests impacted:** 4 passed in `test_execution_service_three_tier_logging.py`, 11 passed in `test_file_upload.py` (no regressions).

---

## ADR-002-31: Three HK Plan-Tab SPA Spinner-Settle Before Tab-State Verification

**Date:** April 14, 2026

### Context

Execution #669 (test case 149, "Successful Navigation to Preprod Voucher Plan") showed the same PASS-on-wrong-branch symptom as #668. The previous fix (ADR introduced with the tab-click guard system) verified tab state within ~416 ms of the click — during the immediate DOM-event window — but the Three HK SPA mounts a Bootstrap spinner (`div[role='status'].spinner-border`) ~200 ms after the click and takes ~3 seconds to clear while fetching plan data. When the fetch completes, React reconciles the plan section and overwrites the active-tab class, reverting to the default tab (World Plan). The tab-state check had already passed before this reversion.

Two compounding root causes were identified from execution #669 logs:

**RC1 — Tab-state verified before the SPA data-fetch cycle completes (ADR-002-23 gap):**  
`_ensure_three_hk_plan_tab_click_progressed` confirmed `aria-selected=true` on the voucher tab within the immediate DOM-event window. The SPA then triggered a fetch, the spinner mounted at `10:06:22,939` and cleared at `10:06:25,745` (~3 s later). React reconciliation after the fetch reverted the active tab to World Plan. The verification had run against the pre-settle DOM.

**RC2 — `wait_for_post_click_readiness` exits early for non-navigation tab clicks (ADR-002-7 + ADR-002-19 gap):**  
Because the tab click does not change the URL, `wait_for_post_click_readiness` classifies it as a non-navigation click and returns early without the spinner-lifecycle wait that is applied to URL-changing navigation clicks. The SPA spinner cycle therefore happened entirely outside any wait boundary owned by the tab-click step.

### Decision

Add `_wait_for_spa_spinner_settle(page)` to `tier2_hybrid.py` and call it at two points in the tab-click flow:

**`_wait_for_spa_spinner_settle()` logic:**
1. Probe for `div[role='status'].spinner-border, [role='status'].spinner-border` with a 600 ms appearance window.
2. If the spinner never mounts, return immediately (zero overhead for tab clicks on non-SPA pages).
3. If the spinner mounts, call `wait_for(state="hidden", timeout=min(timeout_ms, 8000))` to block until the data-fetch cycle completes.

**Call site 1 — `_try_three_hk_plan_tab_click()` after `wait_for_post_click_readiness`:**  
Inserted between the `wait_for_post_click_readiness` call and `_ensure_three_hk_plan_tab_click_progressed`. This ensures the progress check always sees the settled DOM state (RC1 + RC2).

**Call site 2 — `_ensure_three_hk_plan_tab_click_progressed()` retry path:**  
Called after `auto_dismiss_blocking_modals` (in case modal dismissal itself triggers a data-fetch) and after `_retry_three_hk_plan_tab_click` (in case the retry click triggers a fresh data-fetch cycle).

### Consequences

**Positive**
- Tab-state verification now always occurs after the SPA data-fetch cycle, not before it.
- The fix adds at most 600 ms overhead when no spinner mounts (appearance-window timeout), and no overhead at all when the page has no Bootstrap spinner.
- Reuses the already-present spinner CSS shared with ADR-002-23 (`div[role='status'].spinner-border`) — consistent with step-boundary loading detection elsewhere.
- Covers the retry path too: each re-click also settles before re-checking.

**Negative**
- The 600 ms appearance window is a heuristic. If the Three HK SPA delays spinner mount beyond 600 ms (e.g. under heavy load), the settle is skipped and the old symptom may recur. This is narrowly unlikely given observed ~200 ms mount time.
- `_wait_for_spa_spinner_settle` is Three HK-specific only in its call sites; the implementation is general enough to reuse anywhere the Bootstrap spinner pattern is present.

**Alternatives Considered**
- **Add `"tab"` to `NAVIGATION_KEYWORDS`**: Would force `wait_for_post_click_readiness` to enter the navigation path for all tab clicks everywhere, including cases where no URL change ever occurs. Risk of false `wait_for_load_state("load")` calls on other sites. Rejected.
- **Increase `_wait_for_three_hk_plan_tab_transition` deadline from 5 s to 8 s**: The transition deadline polls for tab attributes, not spinner state. Even with a longer deadline, if the spinner clears and React reconciliation reverts the tab, the check still sees the wrong state. This does not fix RC1.
- **Re-read snapshot inside `_wait_for_three_hk_plan_tab_transition` after detecting a spinner**: More complex; requires detecting the spinner inside the transition poller. An explicit separate settle call before the check is simpler and easier to test.

**Tests added (TDD):**  
4 new tests in `backend/tests/test_tier2_plan_selection.py` — `TestThreeHkPlanTabSpinnerSettle` class:
- `test_try_tab_click_waits_for_spinner_before_progress_check` — call order: `spinner` then `ensure` (RC1 + RC2)
- `test_spinner_settle_waits_for_spinner_appear_then_hide` — spinner mounts → `wait_for(state="hidden")` is called
- `test_spinner_settle_is_noop_when_no_spinner_present` — spinner never mounts → `wait_for` never called
- `test_spinner_settle_in_retry_path` — spinner settle invoked in the `_ensure_three_hk_plan_tab_click_progressed` retry branch

- `test_spinner_settle_waits_for_spinner_appear_then_hide` — spinner mounts → `wait_for(state="hidden")` is called
- `test_spinner_settle_is_noop_when_no_spinner_present` — spinner never mounts → `wait_for` never called
- `test_spinner_settle_in_retry_path` — spinner settle invoked in the `_ensure_three_hk_plan_tab_click_progressed` retry branch

**Total tests:** 14 passed in `test_tier2_plan_selection.py`; 22 passed across `test_tier2_plan_selection.py`, `test_three_tier_execution_service.py`, `test_post_click_readiness.py` (no regressions).

---

## ADR-002-32: Post-Settle Tab State Re-Verification and Recovery Re-Click

**Date:** April 14, 2026

### Context

ADR-002-31 extended the tab-click path so that `_wait_for_spa_spinner_settle` blocks until the Three HK SPA Bootstrap spinner clears before `_ensure_three_hk_plan_tab_click_progressed` reads the tab's `aria-selected` attribute. This eliminated the verify-before-settle race (RC1).

However, Executions #675 and #676 exposed a second independent race: the ADR-002-23 **step-boundary loading wait** in `ThreeTierExecutionService` runs before every non-navigate tier call, and it also waits for `div[role='status'].spinner-border` to become hidden. If the SPA spinner mounts in the gap between the tab-click step returning and the *next* step starting, ADR-002-23 clears it at the step boundary — but by then the tab had already been reset to World Plan without any guard seeing it.

Execution #675 shows the happy path: the pending tab key was set and re-verified successfully before step 3 ran. Execution #676 shows the failure path: the revert was detected but the step still failed because the guard raised immediately without attempting recovery.

Two root causes:

**RC-PSR-1 — No post-settle tab re-verification at the step boundary:**  
The `execute_step` entry point for the *next* step had no mechanism to re-check whether the previously confirmed tab was still selected after ADR-002-23's spinner-boundary wait. Once any spinner had cleared, the step executed against whatever DOM state existed — which could be the wrong tab.

**RC-PSR-2 — Revert detection raised immediately without attempting recovery:**  
Once the pending tab re-check detected a revert it raised `ValueError`, failing the current step. A single recovery re-click was already known to succeed (the tab click itself had worked once) but was never attempted before the raise.

### Decision

#### ADR-002-32-A: `_pending_three_hk_tab_key` instance variable

Add `_pending_three_hk_tab_key: Optional[str] = None` to `Tier2HybridExecutor.__init__`. After a successful Three HK plan-tab click, `_try_three_hk_plan_tab_click` sets this to the confirmed `tab_key` string (e.g. `"handsetVoucher"`). The variable acts as a deferred intent: *"the previous step confirmed this tab; re-verify it before the next step touches the plan section."*

#### ADR-002-32-B: `_verify_and_clear_pending_tab_check(page)` called at `execute_step` entry

At the start of every `execute_step` call, before any other action, `_verify_and_clear_pending_tab_check` is called:

```python
await self._verify_and_clear_pending_tab_check(page)
```

**Logic:**
1. If `_pending_three_hk_tab_key is None`, return immediately (zero overhead for all non-tab-click executions).
2. Attempt to locate the pending tab by `role=tab` / `aria-label` / text.
3. If the locator resolves and `aria-selected == "true"`: log, clear `_pending_three_hk_tab_key`, return (happy path, #675 scenario).
4. If the tab is no longer selected (has reverted): call `_recovery_click_three_hk_tab` (see ADR-002-32-C) before raising.

Clearing the key on success ensures no double-check on subsequent steps.

#### ADR-002-32-C: `_recovery_click_three_hk_tab(page, tab_key)` — one recovery re-click

When the pending-tab recheck detects a revert:
1. Locate the tab element and click it.
2. Call `_wait_for_spa_spinner_settle(page)` after the recovery click.
3. Re-read `aria-selected`.
4. If the tab is now selected: log recovery success, clear the pending key, return (step proceeds normally).
5. If still not selected: raise `ValueError f"Three HK plan tab '{tab_key}' reverted to default after SPA spinner-settle and recovery re-click also failed."`

The recovery is bounded to **one attempt** — it does not loop.

### Consequences

**Positive**
- Execution #676 scenario (bounce detected, step 3 fails 4/5) now recovers silently: the recovery re-click succeeds, step 3 clicks the correct plan card, and the test passes.
- ADR-002-23's step-boundary wait is no longer a gap — the pending-key mechanism fills the window between the tab-click step completing and the next `execute_step` call.
- Zero overhead for non-Three-HK steps: `_pending_three_hk_tab_key` remains `None` throughout.

**Negative**
- Recovery re-click adds up to ~2 s latency on the rare execution where a revert is detected (spinner settle after re-click). This is acceptable: it avoids a full test failure.
- If the tab reverts twice (initial click + recovery click both clear), the step raises `ValueError`. This is the correct outcome — it surfaces a persistent SPA state management issue rather than silently looping.

**Alternatives Considered**
- **Retry the full tab-click step from `ThreeTierExecutionService`**: Would cause duplicated step logging and step-counter issues. Recovery at the Tier 2 boundary is cleaner.
- **Increase ADR-002-23 spinner-settle timeout to catch slower mounts**: Does not help because the core issue is the inter-step gap, not the spinner duration.
- **Store the pending key in the step result dict**: Would require `ThreeTierExecutionService` to forward per-step state between iterations; violates the executor's stateless design.

**Tests added (TDD):**  
New classes `TestPostSettleTabRecheck` (6 tests) and `TestPostSettleTabRecheckRecovery` (7 tests) in `backend/tests/test_tier2_plan_selection.py`:
- `test_executor_initialises_with_no_pending_tab_key`
- `test_try_tab_click_sets_pending_key_on_success`
- `test_verify_and_clear_pending_tab_check_is_noop_when_no_pending_key`
- `test_verify_and_clear_passes_and_clears_when_tab_still_selected`
- `test_verify_and_clear_raises_when_tab_has_reverted`
- `test_execute_step_calls_pending_tab_check_before_processing_step`
- `test_recovery_returns_true_when_tab_selected_after_reclick`
- `test_recovery_returns_false_when_tab_still_not_selected_after_reclick`
- `test_recovery_returns_false_when_locator_not_found`
- `test_recovery_returns_false_when_click_raises`
- `test_verify_calls_recovery_reclick_when_tab_reverted_and_succeeds`
- `test_verify_raises_when_recovery_reclick_also_fails`
- `test_verify_does_not_call_recovery_when_tab_still_selected`

**Total tests:** 37 passed across `test_tier2_plan_selection.py` (no regressions).

---

## ADR-002-33: T&C Checkbox Post-Check Verification and Subscribe Now Fast-Fail Guard

**Date:** April 14, 2026

### Context

Execution #683 (Test Case 1075) showed two independent failures in a longer subscription flow:

**RC-CHK-1 — `check` action appears to succeed but element remains visually unchecked:**  
The XPath cache key for the T&C checkbox was shared with a previously cached element on the same URL (earlier-loaded DOM). The cached XPath resolved and `element.check()` was called, but `is_checked()` returned `False` immediately after — the click had landed on a different element whose DOM index had shifted. The step returned `success: True` because no Playwright exception was raised; the actual checkbox state was never verified post-action.

**RC-CHK-2 — Subscribe Now button stays permanently disabled, but the step polls for 8 s before failing:**  
ADR-002-10's `_wait_for_element_enabled_before_click` polls `is_enabled()` in a loop capped at `min(timeout_ms, 8000)`. For a Subscribe Now button that is disabled because a required field upstream is unfilled (e.g. T&C checkbox from RC-CHK-1 was never checked), the button will *never* become enabled in the current step context. Waiting 8 s before logging a warning and proceeding wastes time and produces a misleading click on a disabled control.

### Decision

#### ADR-002-33-A: Post-check `is_checked()` verification for `check` actions

After `element.check()` completes, read back the checkbox state:

**Fast path:** If `is_checked()` returns `True` before `check()` is called (element already checked), skip the `check()` call entirely and return success immediately. This preserves idempotency for re-runs.

**Post-check verification:** If `is_checked()` returns `False` after `check()`, `execute_step` raises `ValueError("Checkbox element is still unchecked after check() — possible XPath index shift")`. The existing cache-invalidation path on step failure (ADR-002-3) then marks the entry `is_valid=False`, so the next run extracts a fresh XPath via `observe()`. No separate retry loop is added — the same single-retry pattern used elsewhere in Tier 2 ensures overhead is bounded.

#### ADR-002-33-B: Subscribe Now permanent-disable fast-fail in `_wait_for_element_enabled_before_click()`

Keep the general 8-second polling loop for ordinary buttons (preserving ADR-002-10 behavior). Add an early-exit for Subscribe Now before the polling loop:

```python
if "subscribe now" in instruction.lower():
    if not await element.is_enabled():
        raise ValueError(
            "Subscribe Now button is disabled — likely a required field (e.g. T&C checkbox) "
            "was not completed in a previous step."
        )
```

If the button is already enabled (normal path), the guard is a no-op. If it is disabled, the step fails immediately with a specific diagnostic message instead of polling for 8 s and then silently clicking a disabled control.

The guard is intentionally scoped to `"subscribe now"` substring only. Other disabled buttons continue to use the 8-second polling loop (backward-compatible with ADR-002-10).

### Consequences

**Positive**
- `check` actions now have a DOM-state proof: a mismatch between the cached XPath and the actual element is surfaced instead of silently passing.
- Cache self-healing (ADR-002-3) is triggered by the `ValueError` on subsequent runs, so the stale XPath is automatically replaced.
- Subscribe Now fast-fail converts an 8-second silent-wrong-click into an immediate, informative error that points to the upstream missed step.

**Negative**
- `is_checked()` post-verification adds one Playwright API call per `check` action. Small overhead (< 10 ms per call).
- The Subscribe Now guard is instruction-text-based. Different labels (locale-specific text, or "Click Subscribe") do not trigger the fast-fail and continue using the 8-second poll.
- On first `check` failure the cached XPath is bypassed and `observe()` is called. If the page has rendered correctly but the XPath is simply stale, Tier 3 may be reached. This is the intended self-healing path.

**Alternatives Considered**
- **Add `is_checked()` to cache-key validation (`_validate_cached_xpath_for_step`)**: Mixes cache validation with action verification; the post-check approach is simpler and consistent with how fill validation works.
- **Use `force=True` in `element.check()`**: Bypasses Playwright's `is_checked` semantics and forces a click regardless. Masks the DOM index problem rather than surfacing it.
- **Apply permanent-disable fast-fail to all buttons**: Would change the semantics of ADR-002-10 for every click, potentially breaking flows where a button is briefly disabled while JavaScript processes a prior input.

**Tests added (TDD):**  
New class `TestCheckboxStateVerification` (10 tests) in `backend/tests/test_tier2_plan_selection.py`:
- `test_should_retry_observe_for_check_action_with_no_results`
- `test_should_not_retry_observe_for_check_action_when_success`
- `test_should_not_retry_observe_for_check_action_with_selector`
- `test_should_not_retry_observe_for_uncheck_action_with_no_results`
- `test_check_action_raises_when_still_unchecked_after_element_check`
- `test_check_action_passes_when_is_checked_after_element_check`
- `test_check_action_skips_element_check_when_already_checked`
- `test_subscribe_now_button_disabled_raises_value_error`
- `test_subscribe_now_button_enabled_no_raise`
- `test_other_button_disabled_only_logs_warning_not_raises`

**Total tests:** 45 passed across `test_tier2_plan_selection.py` and `test_post_click_readiness.py` (no regressions).

---

## ADR-002-34: Bounded Navigate and Loading-Indicator Timeouts to Eliminate SPA Stalls

**Date:** April 14, 2026

### Context

Execution #688 (Test Case 1075) completed in ~8 minutes against an expected 2–3 minutes. Log analysis identified three hardcoded-timeout anti-patterns that compounded into multi-minute stalls on a Three HK SPA that never reaches `networkidle`:

**RC-PERF-1 — `wait_until="networkidle"` in Tier 2 navigate action (`tier2_hybrid.py`):**  
The Three HK UAT SPA (`wwwuat.three.com.hk`) continuously fires background XHR requests after page load and never reaches Playwright's `networkidle` state (≥ 500 ms with no pending network requests). With a 30 s `timeout_ms`, each navigate tier call stalled for 30 s before timing out. The 3-tier fallback retried all three tiers, producing `total_time_ms: 90373ms` for Step 1 in the #688 log (3 × 30 s = 90 s).

**RC-PERF-2 — Navigation click loading indicator per-selector timeout too small (`post_click_readiness.py`):**  
```python
loading_timeout = min(timeout_ms, 8000)  # 8 s per selector
```
The Three HK document-upload landing page (`?step=documentUpload`) mounts a `div[role='status'].spinner-border` for ~18 s after "Next" is clicked. With an 8 s per-selector timeout, `wait_for_loading_indicators_to_clear` timed out and retried for each of the three overlapping spinner selectors in `LOADING_SELECTORS`. Execution #688 log shows three sequential "Waiting for loading indicator" entries exactly 8 s apart (14:24:50, 14:24:58, 14:25:06), producing a 24 s stall for Step 17 instead of one 18 s wait.

**RC-PERF-3 — Non-navigation click networkidle timeout set at 10 s (`post_click_readiness.py`):**  
Every non-navigation click (`check`, `fill`, `select`, etc.) waited up to 10 s for `networkidle`. On the Three HK SPA this always times out and falls back to `domcontentloaded`, adding 10 s to every non-nav click step. Steps 5, 6, 9, 10, 11 (T&C checkbox, field fills, selects) each incurred this 10 s penalty.

### Decision

#### ADR-002-34-A: Navigate action uses `wait_until="domcontentloaded"` (`tier2_hybrid.py`)

```python
# Before
await page.goto(value or instruction, timeout=self.timeout_ms, wait_until="networkidle")
# After
await page.goto(value or instruction, timeout=self.timeout_ms, wait_until="domcontentloaded")
```

`domcontentloaded` fires as soon as the initial HTML document is parsed, without waiting for subresources or background XHR. Subsequent step-boundary waits (ADR-002-23) and tab-click spinner settle (ADR-002-31) handle SPA readiness at the point each step executes. This aligns the Tier 2 in-step navigate action with the bootstrap navigation in `ExecutionService` (ADR-002-22).

#### ADR-002-34-B: Navigation click loading indicator timeout raised to 20 s (`post_click_readiness.py`)

```python
# Before
loading_timeout = 15000 if classification["is_payment_click"] else min(timeout_ms, 8000)
# After
loading_timeout = 15000 if classification["is_payment_click"] else min(timeout_ms, 20000)
```

A 20 s timeout means an ~18 s spinner on a navigation-click landing page resolves on the **first** selector match rather than timing out and cycling through three overlapping CSS selectors. The net wall-clock wait is unchanged (~18 s), but only one `wait_for` call is made instead of three. Payment clicks retain their own `loading_timeout = 15000` cap.

#### ADR-002-34-C: Non-navigation networkidle timeout capped at 3 s (`post_click_readiness.py`)

```python
# Before
await page.wait_for_load_state("networkidle", timeout=wait_timeout)  # min(timeout_ms, 10000)
# After
non_nav_idle_timeout = min(timeout_ms, 3000)
await page.wait_for_load_state("networkidle", timeout=non_nav_idle_timeout)
```

3 s is sufficient for pages that genuinely reach `networkidle`. For SPA pages that never reach it, the fallback to `domcontentloaded` is reached 7 s sooner than before, saving time on every non-navigation click on SPA-heavy sites.

### Consequences

**Positive**
- RC-PERF-1: Step 1 (Navigate) drops from ~90 s (3 × 30 s networkidle timeout) to ~2–5 s (domcontentloaded resolve). Regression-tested via `test_navigate_uses_domcontentloaded_not_networkidle`.
- RC-PERF-2: Step 17 (Next → document upload) stall drops from ~24 s (3 × 8 s per selector) to ~18 s (1 × up-to-20 s on the first matching selector). Regression-tested via `test_navigation_click_loading_timeout_allows_slow_spinners`.
- RC-PERF-3: Each non-navigation click on the Three HK SPA saves ~7 s. For a 12-step form with non-nav clicks this is ~84 s of savings. Regression-tested via `test_non_nav_click_networkidle_timeout_is_short`.
- Overall execution time for #688-equivalent flows estimated to drop from ~8 min to ~3–4 min.

**Negative**
- `domcontentloaded` for navigate resolves before all SPA components mount. Flows that immediately follow a navigate step and interact with a slow-mounting SPA component rely entirely on ADR-002-23 step-boundary waits and per-action waits for readiness.
- 20 s navigation-click timeout means a stuck spinner (e.g. server error) stalls for 20 s before the step fails. Previously it stalled for 8 s (too short, causing false multi-selector retries); 20 s is the correct budget aligned with the actual observed duration.
- 3 s non-nav networkidle cap may miss pages that fire a small number of background requests after load and do reach `networkidle` in 4–8 s. Those pages fall back to `domcontentloaded` (already resolves) rather than the cleaner `networkidle` signal. Functionally equivalent; diagnostically less precise.

**Alternatives Considered**
- **Remove `networkidle` wait for non-nav clicks entirely**: Would miss the brief settle period that prevents race conditions on reactive form frameworks. The 3 s cap is a safe middle ground.
- **Use Playwright `network_idle_timeout` context option**: Per-context, not per-call. Changing it globally would affect all waits including navigation and payment readiness.
- **Increase `_APPEAR_TIMEOUT_MS` in `_wait_for_spa_spinner_settle` to cover RC-PERF-2**: The document-upload spinner (RC-PERF-2) is in the generic `LOADING_SELECTORS` loop inside `wait_for_loading_indicators_to_clear`, not in `_wait_for_spa_spinner_settle`. They are separate mechanisms serving different call sites.

**Tests added (TDD):**  
New class `TestTier2NavigatePerformance` (1 test) in `backend/tests/test_tier2_plan_selection.py` and 2 new standalone tests in `backend/tests/test_post_click_readiness.py`:
- `test_navigate_uses_domcontentloaded_not_networkidle` — `page.goto` called with `wait_until='domcontentloaded'`
- `test_navigation_click_loading_timeout_allows_slow_spinners` — navigation-click spinner wait timeout ≥ 20 000 ms
- `test_non_nav_click_networkidle_timeout_is_short` — non-nav networkidle timeout ≤ 3 000 ms

**Total tests:** 45 passed across `test_tier2_plan_selection.py` and `test_post_click_readiness.py` (no regressions).

---

## ADR-002-35: Further Narrow Modal Auto-Dismiss — Move 'I understand' and 'Close' to Conditional, Purge Button-Label Tokens from Nuisance Detector

**Date:** April 14, 2026

### Context

Two consecutive production executions of Test Case 101 on the Three HK flow revealed that ADR-002-28's SAFE list was still too broad:

**Execution #689 — 'I understand' pre-empted by post-click readiness after Step 8 'Click Next'**

Step 8 (*"Click the 'Next' button to proceed to the terms and conditions page"*) matched `"next"` in `NAVIGATION_KEYWORDS`, so `wait_for_post_click_readiness()` classified it as a navigation click and called `auto_dismiss_blocking_modals()` after loading indicators cleared. The T&C purchase modal appeared on the landing page. `"I understand"` was in `SAFE_MODAL_DISMISS_BUTTON_TEXTS` and was clicked unconditionally — consuming the modal before Step 9 (*"Click the 'I understand' button"*) could execute.

Secondary root cause: `_modal_allows_business_autodismiss()` returned `True` even for the T&C modal because `"i understand"` was in `NUISANCE_MODAL_TEXT_TOKENS`, meaning the modal's own button label was used as evidence that it was a nuisance dialog. Any modal containing an "I understand" button therefore passed the nuisance check, defeating the business-flow guard.

**Execution #692 — 'Close' pre-empted the same modal after 'I understand' was moved to CONDITIONAL**

After ADR-002-35-A was applied (moving `"I understand"` to CONDITIONAL), the same Three HK account/purchase page T&C modal continued to be auto-dismissed via its Bootstrap close (×) button (`"Close"`), which remained in `SAFE_MODAL_DISMISS_BUTTON_TEXTS`. Log evidence: `[Modal] Auto-dismissed with button 'Close'` at 15:54:00 during Step 8's post-click readiness, immediately before Step 9 started.

The URL at the time of dismissal was `https://www.three.com.hk/postpaid/en/account/purchase`, confirming the modal was on the purchase checkout page — a business-flow screen, not a preprod gate.

### Decision

#### ADR-002-35-A: Move 'I understand' / 'I Understand' from SAFE to CONDITIONAL

`"I understand"` and `"I Understand"` are moved from `SAFE_MODAL_DISMISS_BUTTON_TEXTS` to `CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS`. They now fire only when `_modal_allows_business_autodismiss()` confirms the modal is a nuisance/informational blocker.

**Rationale:** "I understand" is a common acknowledgment button on both preprod environment reminder dialogs *and* production T&C/terms modals. Treating it as safe-to-click on any visible modal is incorrect. The Three HK UAT preprod reminder modal (which contains `"reminder"` in its text) still passes the nuisance check and is dismissed. The T&C purchase modal does not contain any nuisance token and is correctly left alone.

#### ADR-002-35-B: Move 'Close' from SAFE to CONDITIONAL

`"Close"` is moved from `SAFE_MODAL_DISMISS_BUTTON_TEXTS` to `CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS` for the same reason.

**Rationale:** Bootstrap modals universally include a dismiss button labeled "Close" (the × icon). On nuisance/reminder overlays this is appropriate to auto-click. On business-flow dialogs (payment confirmations, T&C modals, subscription overlays) clicking `"Close"` dismisses the dialog without completing the required business action, silently breaking the flow.

#### ADR-002-35-C: Remove button-label tokens from NUISANCE_MODAL_TEXT_TOKENS

`"i understand"`, `"got it"`, and `"information"` are removed from `NUISANCE_MODAL_TEXT_TOKENS`.

**Rationale:**
- `"i understand"` and `"got it"` are button labels. A modal containing a button labeled "I understand" is not inherently informational — it could be a T&C agreement, a warning, or any required action step. Including them caused `_modal_allows_business_autodismiss()` to return `True` for any modal with either button, making the guard circular: a button previously in the SAFE list was also used to classify modals as safe to auto-dismiss regardless of content.
- `"information"` is too generic. Production pages routinely render informational UI sections (e.g. plan details, help text) inside modal containers. Matching this token would incorrectly classify business-flow dialogs as nuisance blockers.

**Final state of the lists after ADR-002-35:**

```python
SAFE_MODAL_DISMISS_BUTTON_TEXTS = [
    "OK",
    "Ok",
    "Dismiss",
    "Got it",
    "Accept",
    "Agree",
]

CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS = [
    "I understand",
    "I Understand",
    "Close",
    "Confirm",
    "Continue",
    "Done",
]

NUISANCE_MODAL_TEXT_TOKENS = (
    "reminder",
    "notice",
    "informational",
    "session expired",
    "session timeout",
    "timed out",
    "maintenance",
    "security reminder",
)
```

### Consequences

**Positive**
- The Three HK T&C purchase modal (`account/purchase`, `step=offer`) is no longer consumed by `auto_dismiss_blocking_modals()` during Step 8's post-click readiness. Step 9's explicit interaction with the "I understand" button proceeds as designed.
- The preprod UAT reminder modal (`"reminder"` in body text with "I understand" button) still passes the nuisance guard and is auto-dismissed as before.
- Session-expired dialogs (`"session expired"` token) with a "Close" button are still auto-dismissed.
- `_modal_allows_business_autodismiss()` is now based purely on modal purpose tokens, not button labels — making the guard logically coherent.

**Negative**
- A nuisance modal that only has a "Close" or "I understand" dismiss option and whose body text does not contain any `NUISANCE_MODAL_TEXT_TOKENS` will no longer be auto-dismissed. If such a modal is encountered, either its token should be added to `NUISANCE_MODAL_TEXT_TOKENS` or an explicit test step should dismiss it.
- `"Got it"` remains in `SAFE` because it is used exclusively as a nuisance/onboarding acknowledgment in practice. If a business-flow modal is ever observed using "Got it", it should be moved to CONDITIONAL.

**Alternatives Considered**
- **Keep "I understand" in SAFE, add URL exclusion for purchase pages**: Too brittle — would require maintaining a URL-pattern list alongside the button list and would break for other sites.
- **Add lookahead into upcoming steps before auto-dismissing**: If the next step's instruction contains a button label that auto-dismiss would click, skip. Viable but adds coupling between `auto_dismiss_blocking_modals()` and the step-execution context it has no access to.
- **Remove `auto_dismiss_blocking_modals()` from `wait_for_post_click_readiness()`**: Would regress the original ADR-002-20 fix for Three HK preprod gating; the preprod reminder must be dismissed automatically after plan selection or the flow cannot advance.

**Tests added (TDD, `backend/tests/test_post_click_modal_dismiss.py`):**
- `test_modal_show_i_understand_clicked_for_nuisance_reminder` — nuisance reminder modal with "I understand" button → dismissed (replaces original `test_modal_show_i_understand_clicked`)
- `test_tnc_business_modal_i_understand_not_auto_dismissed` — T&C modal without nuisance tokens → NOT dismissed
- `test_nuisance_modal_text_tokens_does_not_contain_i_understand` — regression guard: `"i understand"` must not be in `NUISANCE_MODAL_TEXT_TOKENS`
- `test_nuisance_modal_text_tokens_does_not_contain_got_it` — regression guard: `"got it"` must not be in `NUISANCE_MODAL_TEXT_TOKENS`
- `test_i_understand_is_in_conditional_not_safe_list` — regression guard: `"I understand"` must be in CONDITIONAL, not SAFE
- `test_close_is_in_conditional_not_safe_list` — regression guard: `"Close"` must be in CONDITIONAL, not SAFE
- `test_tnc_modal_close_button_not_auto_dismissed` — purchase-page T&C modal with Close button → NOT dismissed
- `test_session_expired_modal_close_button_is_auto_dismissed` — session-expired modal with Close button → dismissed

**Total tests after ADR-002-35: 22 passed** in `test_post_click_modal_dismiss.py` + 7 in `test_post_click_readiness.py` (no regressions).

---

## ADR-002-36: Expand THREE_HK_PLAN_TAB_LABELS to Cover 4.5G Monthly Plans and 5G Broadband Categories

### Context

`THREE_HK_PLAN_TAB_LABELS` in `Tier2HybridExecutor` gates the specialist tab-click path (`_try_three_hk_plan_tab_click`), which applies SPA spinner-settle and tab-state verification (ADR-002-31/32). At the time of those ADRs only the 5G Monthly SIM Plans category was tested, so the registry only contained its six tab labels.

Executions #705 (Test Case 1078, 5G Broadband) and #707 (Test Case 1078, 4.5G Monthly Plans) both PASS all steps yet show the wrong tab active in screenshots:

- Exec #705 Step 3: "Click 'Wi-Fi 6 Monthly Plan' tab" → screenshot shows default "HSBC credit card offer" tab still active with content in skeleton state.
- Exec #707 Step 3: "Click 'HK-UK Pro Sharing Monthly Plan' tab" → screenshot shows default "4.5G SIM Monthly Plan" tab still active.

Root cause chain:
1. `_extract_three_hk_plan_tab_key()` returns `None` for all 4.5G Monthly Plans and 5G Broadband tab labels → `_is_three_hk_plan_tab_click()` returns `False`.
2. The step falls into the generic Tier 2 `observe()`/XPath path which calls `.click()` then returns in < 100 ms with no spinner-settle and no tab-state check.
3. The SPA data-fetch spinner mounts ~1170 ms after the click and resets the active-tab class to the page default when it resolves (~3–5 s total). The step has already been marked PASS.
4. `_pending_three_hk_tab_key` is never set, so the RC2 inter-step re-verification (ADR-002-32) also fires no check at the next step.

### Decision

Add all tabs from the two affected categories to `THREE_HK_PLAN_TAB_LABELS` and their corresponding content tokens to `THREE_HK_PLAN_TAB_CONTENT_TOKENS`:

**4.5G Monthly Plans:**
| Key | Display label |
|---|---|
| `4.5g sim monthly plan` | `4.5G SIM Monthly Plan` |
| `hk-uk pro sharing monthly plan` | `HK-UK Pro Sharing Monthly Plan` |
| `greater china pro monthly plan` | `Greater China Pro Monthly Plan` |

**5G Broadband:**
| Key | Display label |
|---|---|
| `hsbc credit card offer` | `HSBC credit card offer` |
| `tertiary students and staff offer` | `Tertiary students and staff offer` |
| `wi-fi 6 monthly plan` | `Wi-Fi 6 Monthly Plan` |
| `wi-fi 7 monthly plan` | `Wi-Fi 7 Monthly Plan` |

No changes to the specialist click path — adding entries to the registry is sufficient to route these tab instructions through the existing spinner-settle + tab-state verification that 5G Monthly SIM Plans already uses.

### Consequences

**Positive**
- All Three HK plan-tab categories now go through spinner-settle + `_is_three_hk_plan_tab_selected` verification and the RC2 pending-key re-check.
- No code path changes — risk is confined to a data-only addition to two class-level dictionaries.
- `THREE_HK_PLAN_TAB_CONTENT_TOKENS` fallback (`(tab_key,)`) would also work for these tabs; explicit tokens are added for clarity and earlier body-text matching.

**Negative**
- Registry requires manual maintenance as Three HK adds or renames plan categories. No automatic discovery.
- `_is_three_hk_plan_tab_selected` uses ARIA attributes and CSS class heuristics. If a new category renders active-tab state differently (e.g., only via inline style), `target_selected` may remain `False` and the verification step relies on body-text token matching alone.

**Alternatives Considered**
- **Generic tab-click detection** (any `"tab"` in instruction on Three HK UAT): Would bypass the registry entirely but risks routes non-tab instructions through the specialist path if instructions incidentally contain the word "tab".
- **Content-only progress verification without tab-label registry**: Would require body-text tokens for every possible tab, and `_has_three_hk_plan_tab_progress` already falls back to body-text tokens if ARIA selection check fails.

**Related files changed:**
- `backend/app/services/tier2_hybrid.py` — `THREE_HK_PLAN_TAB_LABELS` and `THREE_HK_PLAN_TAB_CONTENT_TOKENS` class constants

**Tests added (TDD, `backend/tests/test_tier2_plan_tab_registry.py`):**
- `TestTabLabelRegistry` — 9 tests verifying `_extract_three_hk_plan_tab_key` matches all new and existing labels.
- `TestIsThreeHkPlanTabClickRouting` — 8 parametrized tests verifying `_is_three_hk_plan_tab_click` returns `True` for all new tab instructions.
- `TestExecuteStepRoutesNewTabsToSpecialistPath` — 2 integration-level tests verifying `execute_step` calls `_try_three_hk_plan_tab_click` (not the XPath/cache path) for the two categories broken in Executions #705 and #707.

**Total: 57 passed** across `test_tier2_plan_tab_registry.py` (19) + `test_tier2_plan_selection.py` (38), no regressions.
