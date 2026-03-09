# Architecture Decision Records — Test Case Generation Token Truncation Fix

**Document ID:** ADR-003  
**Component:** Test Case Generation Service  
**Status:** Accepted  
**Date:** March 9, 2026  
**Author:** Developer B  
**Related Files:**
- `backend/app/services/test_generation.py`
- `backend/tests/unit/test_test_generation_truncation.py`

---

## Table of Contents

1. [ADR-003-1: Minimum Token Floor for Generation Requests](#adr-003-1-minimum-token-floor-for-generation-requests)
2. [ADR-003-2: Truncated JSON Recovery via Brace-Counting Scan](#adr-003-2-truncated-json-recovery-via-brace-counting-scan)

---

## ADR-003-1: Minimum Token Floor for Generation Requests

### Context

`TestGenerationService.generate_tests()` uses `max_tokens` from the user's saved Settings row to cap the LLM response. The Settings page exposes this field alongside execution-oriented presets — users routinely save values like 1 200 or 2 000 that are sufficient for single-step execution answers but far too small for multi-test-case JSON payloads (5 complex e2e test cases with 15-20 steps each requires ≈ 3 000–6 000 tokens of output).

When a free OpenRouter model (`openai/gpt-oss-120b:free`) hit the 1 200-token ceiling mid-serialisation, the LLM emitted a structurally broken JSON string:

```
"steps": [
  "Open the My3 App login page",
  "Enter the registered email",
  "Click the 'Next' b          ← stream terminates here
```

`json.loads()` raised `JSONDecodeError: Unterminated string` and the endpoint returned `HTTP 500`.

### Decision

Introduce a **`MIN_GENERATION_TOKENS = 4096`** class constant on `TestGenerationService` and a `_effective_max_tokens(requested: int) -> int` helper that returns `max(requested, MIN_GENERATION_TOKENS)`.

All paths inside `generate_tests()` that compute `max_tokens_val` now call `_effective_max_tokens()`:

```python
# User config path
raw_max_tokens = user_config.get("max_tokens", 4096)
max_tokens_val = self._effective_max_tokens(raw_max_tokens)

# Defaults path
max_tokens_val = self._effective_max_tokens(4096)
```

The floor is **4 096** because:
- Empirically, 5 complete e2e test cases with detailed steps fit comfortably within 4 000 tokens.
- OpenRouter free models support at least 32 K output tokens; 4 096 is well below any practical limit.
- The value matches the existing default in the Settings UI, making the enforcement invisible to users who accept the default.

The user's saved `max_tokens` value is **not mutated** — the enforcement is applied only at call time inside `generate_tests()`, leaving execution requests unaffected.

### Consequences

**Positive**
- Eliminates token-truncation `HTTP 500` for all new generation calls regardless of stored settings.
- Zero impact on users who already have `max_tokens >= 4096`.
- Centralises the rule in one method — future changes to the floor require a single edit.
- Execution calls (`three_tier_execution_service.py`, stagehand) are unaffected; they want short answers and may legitimately use 1 200 tokens.

**Negative**
- Users who intentionally set a low token budget for cost control will find generation requests always spend at least 4 096 tokens.
- The discrepancy between stored and effective `max_tokens` is not surfaced in the UI (planned UX improvement: separate Generation and Execution token sliders).

**Alternatives Considered**
- **Raise the Settings UI minimum to 4 096**: Would prevent the problem at save time but requires a schema migration and is a breaking change for existing rows.
- **Increase the hardcoded default in `generate_tests()` without a floor**: The explicit `user_config.get("max_tokens", 4096)` would still be overridden by any stored value < 4 096.
- **Store separate `generation_max_tokens` / `execution_max_tokens` columns**: Correct long-term solution; deferred to Sprint 11 settings refactor (ADR pending).

---

## ADR-003-2: Truncated JSON Recovery via Brace-Counting Scan

### Context

Even with the token floor in place (ADR-003-1), truncation can still occur in edge cases:
- Users explicitly request a very large number of tests (e.g. `num_tests=20`) that exceeds even 4 096 tokens.
- A model-side rate-limit causes an early stream termination.
- The minimum floor is reduced in future configuration.

Prior to this fix the only behaviour on `JSONDecodeError` was a full `HTTP 500` with no partial result returned to the user, discarding any test cases that had been fully generated.

### Decision

Add `_try_recover_truncated_json(content: str) -> Optional[str]` to `TestGenerationService`.

**Algorithm:**
1. Attempt `json.loads(content)` — if it succeeds, return as-is (fast path, no overhead).
2. Locate the `"test_cases"` key and the opening `[` of the array.
3. Walk forward character-by-character, tracking:
   - Current brace depth (`{` increments, `}` decrements).
   - Whether the cursor is inside a JSON string (quoted run), respecting `\"` escapes.
4. When depth returns to zero, the object is complete — try `json.loads(obj_text)` and append to `complete_cases` on success.
5. If the end of the string is reached with `depth > 0`, the current object is truncated — stop immediately.
6. Reassemble: return `json.dumps({"test_cases": complete_cases})`.

**Integration into `generate_tests()`:**
```
try:
    result = json.loads(content)
except JSONDecodeError as e:
    recovered = _try_recover_truncated_json(content)
    if recovered and json.loads(recovered)["test_cases"]:
        result = json.loads(recovered)
        result["_truncation_recovered"] = True   # moved to metadata below
    else:
        raise Exception("Failed to parse LLM response …")
```

The recovery flag is surfaced in the response metadata as `truncation_recovered: true`, enabling the frontend and monitoring systems to alert on repeated occurrences without failing the request.

A `WARN` log is emitted on every recovery:
```
[WARN] LLM response was truncated; recovered 2 complete test case(s).
       Increase max_tokens to avoid this.
```

**What is NOT attempted:**
- Repairing the truncated object itself (too brittle; partial test cases are not useful).
- Retrying the LLM (doubles cost; callers may retry at a higher level).

### Consequences

**Positive**
- A truncated 5-test response that has 3 complete objects now returns those 3 instead of a `500`.
- User experience degrades gracefully: fewer tests than requested rather than an error.
- `truncation_recovered: true` in metadata enables future telemetry and proactive warnings.
- Recovery is a pure in-process operation — no extra LLM calls, no DB writes.

**Negative**
- Recovered count (`num_generated`) will be lower than `num_requested`; the UI should communicate this clearly (not yet implemented — tracked as a UX improvement).
- The brace-counting scanner is O(n) over the raw response string; negligible for typical token lengths (< 32 K characters) but worth noting.
- If a future model changes its output format (e.g. wraps the array differently), the scanner must be updated.

**Alternatives Considered**
- **`json.JSONDecoder().raw_decode()` loop**: Can extract one object at a time but does not handle the outer `{"test_cases": [...` wrapper cleanly with partial arrays.
- **Regex-based extraction**: Brittle against nested braces and escaped characters inside step strings.
- **LLM retry with `continue_from` prompt**: Would produce more test cases but doubles latency and cost; a higher-level retry is the appropriate place for that logic.
- **Return partial result without recovery attempt**: Simpler, but discards any complete objects already serialised before the cutoff.

---

## Test Coverage

All decisions above are covered by `backend/tests/unit/test_test_generation_truncation.py` (19 tests, all passing):

| Test Class | What is verified |
|------------|-----------------|
| `TestMinGenerationTokensConstant` | Constant exists and is ≥ 4 096 |
| `TestEffectiveMaxTokens` | `1200 → 4096`, `4096 → 4096`, `8192 → 8192` |
| `TestTryRecoverTruncatedJson` | Valid pass-through; 1, 2, 3 complete case recovery; no-case-found returns None/empty; output always parses |
| `TestGenerateTestsMinTokenEnforcement` | End-to-end: `max_tokens=1200` raises to floor; `max_tokens=8192` unchanged |
| `TestGenerateTestsTruncationRecovery` | Truncated response recovers complete cases + sets flag; garbage response still raises |
