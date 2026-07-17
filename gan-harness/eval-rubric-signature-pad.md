# Evaluation Rubric: Signature Pad Ink Verification

**Feature:** Fix Tier 3 false-PASS on empty signature canvas (programmatic stroke + ink verify)  
**Spec:** `gan-harness/spec.md` § Feature 5  
**Weight total:** 1.0  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Sign step PASSes when `act()` only `scrollIntoView`/locator and canvas stays empty; fallback still exception-only; PASS without ink verification; ctx-only / **pixel-only after ctx paint** leaves SignaturePad empty (or portal **Required** still shown) while PASS; eager Stagehand init for signatures; tier executors called from endpoints

---

## Implementation Checklist (Generator)

Sprint order — **do not skip P0**:

| Sprint | Priority | Deliverables | Key paths |
|--------|----------|--------------|-----------|
| 11 | P0 | Shared helper + Tier 3 always stroke + ink gate + unit tests | `signature_pad.py`, `tier3_stagehand.py`, `tests/unit/test_signature_pad.py` |
| 12 | P1 | Tier 2 empty-observe canvas heuristics + refactor to helper | `tier2_hybrid.py`, `signature_pad.py`, docs |
| 13 | P2 | Action detection: Click Signature → click | `execution_service.py` + unit matrix |

**Required behaviors:**

```text
# Must NOT pass
act() → method: scrollIntoView on "Please sign here:" + blank canvas → FAIL (or stroke then verify)

# Must pass only with ink
programmatic pointer/mouse/touch stroke + (SignaturePad.isEmpty === false | non-blank pixels) → PASS
```

```python
# Conceptual — Tier 3 sign path (NOT exception-only fallback)
result = await optional_act_as_locator_aid(...)
# Soft success (scrollIntoView / locator) must NOT return success here
await signature_pad.sign_canvas(page, instruction=...)  # source of truth
if not await signature_pad.verify_signature_ink(...):
    raise / return failure
return success
```

**Do NOT:**
- Trust `act()` success alone for `draw_signature` / `sign`
- Gate programmatic stroke only on `except` from `act()`
- Use `getContext` paint alone when SignaturePad stays `isEmpty`
- Init Stagehand early solely for signature steps (ADR-002-1)
- Call Tier1/Tier2/Tier3 from API endpoints
- Replace Features 1–4 or expand into unrelated Stagehand refactors

---

## Tier 3 No False-PASS / Stroke Source of Truth (0.35)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| S1 | Soft act does not PASS blank | Mock/real path where `act()` returns `scrollIntoView` (or locator-only) without throw → step does **not** PASS with empty canvas | 0.12 |
| S2 | Stroke always attempted | For `draw_signature`/`sign`, programmatic stroke/helper runs regardless of soft `act()` success | 0.10 |
| S3 | Fallback not exception-only | Code path no longer requires `act()` to throw before `_execute_draw_signature_fallback` / shared helper | 0.08 |
| S4 | #1120/#1122 class fixed | Consent "Please sign here" and credit-card "sign it" cannot false-PASS blank pads | 0.05 |

---

## Ink Verification Gate (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| I1 | Empty → FAIL | Blank pad after attempt → `success=false` (or raised error), clear message | 0.10 |
| I2 | Ink → PASS | After real stroke, `SignaturePad.isEmpty === false` and/or non-blank pixels → may PASS | 0.08 |
| I3 | Events preferred | Pointer/mouse/touch strategies used; ctx-only alone insufficient for PASS when library stays empty | 0.07 |

---

## Shared Helper & Architecture (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| H1 | Shared module | `backend/app/services/signature_pad.py` (or equivalent shared module) owns locate/stroke/verify | 0.06 |
| H2 | Layering | Dispatch remains ExecutionService → ThreeTier; no endpoint→tier calls | 0.05 |
| H3 | Lazy tiers | No new early Stagehand init for signatures (ADR-002-1) | 0.04 |

---

## Tests (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | Helper unit coverage | `test_signature_pad.py` covers locate, stroke strategies, verify true/false | 0.08 |
| T2 | Soft-act false-success test | Explicit test: `act()` soft success + empty ink → fail / helper invoked | 0.07 |

Mandatory themes (fail S/I/T if missing):

| Test theme | Must assert |
|------------|-------------|
| Soft scrollIntoView | Does not PASS blank pad |
| Ink empty | Verification fails |
| Ink present | Verification passes |
| Events | Pointer/mouse/touch path present |

---

## P1 Heuristics / P2 Detection (0.10)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| P1 | Tier 2 empty observe | On observe `[]` for sign, attempts canvas heuristics (near label / largest visible) before escalate — **partial credit OK if P0 solid and Sprint 12 pending** | 0.06 |
| P2 | Click vs draw | `"Click … Signature"` → `click`; `"Sign under…"` / `"Sign it"` → `draw_signature` — **partial credit OK if Sprint 13 pending** | 0.04 |

*Scoring note:* If only Sprint 11 (P0) is complete, award P1/P2 as 0 unless implemented; overall pass still possible if S+I+H+T ≥ 0.85 (0.35+0.25+0.15+0.15 = 0.90).

---

## Non-Regression

| Check | Pass condition |
|-------|----------------|
| Feature 1 Stop Execution | Unchanged |
| Feature 4 Timed Wait | Unchanged |
| Non-sign steps | Click/fill/navigate unaffected |
| Lazy Tier 2/3 | Normal escalation only; no signature-specific early Stagehand |
| Tier 2 existing draw | Still works when xpath available; prefer shared helper |

---

## Scoring

```
score = Σ (criterion_weight × pass?1:0)
```

| Band | Score | Meaning |
|------|-------|---------|
| Pass | ≥ 0.85 | Ready to merge |
| Revise | 0.70 – 0.84 | Fix failing criteria |
| Fail | < 0.70 or any automatic fail | Reject |

**Weight check:** S 0.35 + I 0.25 + H 0.15 + T 0.15 + P 0.10 = **1.00**

---

## Evaluator Test Script (manual / code-review + pytest)

1. **Backend unit:**  
   `cd backend && .\venv\Scripts\activate && python -m pytest tests/unit/test_signature_pad.py -q`  
   All must pass. Confirm a test covers soft `act()` / `scrollIntoView` → no blank PASS.
2. **Code review Tier 3:** Open `tier3_stagehand.py` `draw_signature`/`sign` branch.  
   Assert success is **not** returned solely from `act()` without stroke + ink verify.  
   Assert fallback/helper is **not** only inside `except`.
3. **Code review helper:** `signature_pad.py` includes pointer/mouse/touch stroke and `verify_signature_ink`.
4. **Optional live repro:** Re-run a test equivalent to exec #1120 consent sign / credit-card sign.  
   - PASS screenshot must show ink on canvas.  
   - If stroke cannot complete, step must **fail** (not green on blank pad).  
   - Downstream should not show "Please complete the highlighted required fields" solely due to blank pad after a "passed" sign step.
5. **Lazy tiers:** Confirm no new code path initializes Stagehand before normal Tier 1 failure escalation solely because action is sign.
6. **P1 (if claimed):** Empty observe + visible canvas near "Please sign here" succeeds at Tier 2 without requiring Tier 3.
7. **P2 (if claimed):** Instruction matrix — Click Signature → click; Sign under… → draw_signature.

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Trust `act()` success for sign without ink | Automatic fail (S1/S2) |
| Fallback only on `act()` exception | Automatic fail (S3) |
| PASS with blank canvas / empty SignaturePad | Automatic fail (I1) |
| Ctx paint alone; library still empty; step PASS | Automatic fail (I3) |
| Pixel-only after ctx paint (`source=pixels`) while Required/SignaturePad empty | Automatic fail (I3 / #1131) |
| Eager Stagehand for signatures | Automatic fail (H3) |
| Tier executors from endpoints | Automatic fail (H2 / hard constraint) |
| "Fix" only by longer Stagehand prompt | Automatic fail (S2) |
| Unrelated mega-refactor as the delivery | Automatic fail |
