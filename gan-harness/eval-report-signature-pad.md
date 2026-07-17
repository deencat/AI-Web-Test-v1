# Evaluation Report: Signature Pad Ink Verification (Feature 5 / 5.1)

**Date:** 2026-07-17  
**Spec:** `gan-harness/spec.md` § Feature 5  
**Rubric:** `gan-harness/eval-rubric-signature-pad.md` (updated auto-fails for pixel-only / #1131)  
**Generator state:** `gan-harness/generator-state.md` (Sprint 14 / Feature 5.1 claimed done)  
**Evaluator:** gan-evaluator

---

## Verdict (Feature 5.1)

| Metric | Result |
|--------|--------|
| **Weighted score** | **1.00 / 1.00** |
| **Threshold** | ≥ 0.85 → **PASS** |
| **Automatic fails** | **None** |
| **`signature_pad.py` coverage** | **100%** (226 stmts / 0 miss) |
| **Unit tests** | **61/61 passed** |
| **#1131 class (cosmetic pixels + Required)** | **Gate verified (unit + code review)** — live CRM re-run **not** executed post-fix |

---

## Feature 5.1 — Cosmetic-Ink False PASS (#1131)

### What was evaluated

Close false-confidence ink gate where optional ctx paint left a straight cosmetic line (`source=pixels`) while SignaturePad / form state stayed empty (red **Required**), and the engine step still **PASS**ed.

### Pre-fix evidence (exec #1131 — bug class confirmed)

| Artifact | Observation |
|----------|-------------|
| `backend/logs/server_20260717.log` ~12:10 | `Ink verify source=pixels empty=False has_ink=True` → `Sign succeeded with ink verified` after stroke log `mouse + pointer/touch + optional ctx` |
| `exec_1131.jsonl` step 44 | Stagehand `act("sign it")` → `scrollIntoView` only on credit-card pad |
| `exec_1131_step_44_pass.png` | Credit Card Signature pad **empty**, Confirm **(0)** — step marked **PASS** |
| `exec_1131_step_51_pass.png` | Consent pad shows **cosmetic horizontal line** + toast **“Please complete the highlighted required fields”** — form still treats pad as unsigned |

### Code-review verify gate (post-fix — PASS)

| Gate | Implementation | Status |
|------|----------------|--------|
| Ctx paint off by default | `include_ctx_paint: bool = False` on `draw_signature_stroke` / `sign_canvas` | ✅ |
| Pixel-only after ctx rejected | `sign_canvas` → `reject_pixel_only=include_ctx_paint`; verify fails closed → `source=fail` | ✅ |
| SignaturePad empty blocks pixels | `library_present and empty` → `has_ink=False` (pixels never override) | ✅ |
| Required DOM fail | `requiredStillVisible` → `source=fail` / `reason=required_still_visible` | ✅ |
| Events preferred | Stroke order: mouse → Pointer/Mouse/Touch → optional touchscreen → optional ctx last | ✅ |
| Tier 3 always stroke+verify | Soft `act()` then always `_execute_draw_signature_fallback` → `sign_canvas`; raises if ink fail with `verify_source` | ✅ |
| Layering / lazy tiers | No tier imports under `app/api/`; no signature-specific early Stagehand | ✅ |

### Unit themes covering #1131

| Test | Asserts |
|------|---------|
| `test_pixel_only_after_ctx_paint_does_not_pass` | `reject_pixel_only=True` + pixels → `has_ink=False`, `source=fail` |
| `test_signaturepad_empty_pixels_do_not_override` | Library empty → fail |
| `test_signaturepad_empty_overrides_misleading_has_ink` | Misleading `has_ink=True` ignored when library empty |
| `test_required_still_visible_fails` | Required DOM → `source=fail` |
| `test_sign_canvas_rejects_pixel_only_when_ctx_enabled` | `include_ctx_paint=True` wires `reject_pixel_only=True` |
| `test_stroke_default_skips_ctx_paint` | Default path does not ctx-paint |
| Soft-act / empty ink / events | Prior Feature 5 suite retained (61 tests total) |

### Expected engine behavior after fix (#1131 class)

Cosmetic straight line + empty SignaturePad / visible **Required** must **FAIL** the engine step (raise / `success=false` with `verify_source=fail|signaturepad`), **not** PASS.

---

## Test Execution Summary

### Backend unit (evaluator re-run 2026-07-17)

```bash
cd backend && .\venv\Scripts\Activate.ps1
python -m pytest tests/unit/test_signature_pad.py -q --cov=app.services.signature_pad --cov-report=term-missing
```

**Result:** 61 passed · `app/services/signature_pad.py` **100%** (226/226 statements) · ~13.6s · exit 0

### Live / API smoke

| Step | Result | Evidence |
|------|--------|----------|
| Backend health | PASS | `GET /api/v1/health` → healthy |
| Auth login | PASS | Form `username=admin` / `admin123` → token; `admin@aiwebtest.com` as username form field **fails** (use `admin`) |
| Auth me | PASS | `email=admin@aiwebtest.com` |
| Executions API | PASS | `GET /api/v1/executions/stats` → 200 |
| Frontend | PASS | `http://localhost:5173` → HTTP 200 |
| Full CRM consent / credit-card pad live re-run **after** 5.1 deploy | **NOT RUN** | No post-fix `signature_pad` log lines with new format (`ctx=%s` / `reject_pixel` / `verify_source` in Tier 3). Last live sign logs are pre-fix #1131 (`source=pixels` PASS). |

**Live limit (honest):** Feature 5.1 merge gate is unit + code-review. Restart backend with new `signature_pad.py` before claiming live CRM proof. Optional follow-up: re-run equivalent of #1131; PASS screenshot must show real ink / Confirm count > 0; empty or Required-only pad must FAIL the step.

---

## Automatic Fail Checklist (rubric + #1131)

| Anti-pattern | Status |
|--------------|--------|
| Sign PASSes on `scrollIntoView` + empty canvas | **PASS** — Tier 3 always `sign_canvas` after optional `act()` |
| Fallback still exception-only | **PASS** |
| PASS without ink verification | **PASS** |
| Ctx-only / **pixel-only after ctx** leaves SignaturePad empty or Required shown while PASS | **PASS** — default no ctx; `reject_pixel_only`; library empty blocks pixels; Required → fail |
| Eager Stagehand for signatures | **PASS** |
| Tier executors from endpoints | **PASS** |

---

## Rubric Scoring (Feature 5 + 5.1)

### Tier 3 No False-PASS / Stroke Source of Truth (0.35)

| ID | Criterion | Wt | Pass | Evidence |
|----|-----------|-----|------|----------|
| S1 | Soft act does not PASS blank | 0.12 | ✅ | Soft `act()` + empty ink → fail |
| S2 | Stroke always attempted | 0.10 | ✅ | Always `_execute_draw_signature_fallback` |
| S3 | Fallback not exception-only | 0.08 | ✅ | Helper outside `except` |
| S4 | #1120/#1122 class fixed | 0.05 | ✅ | Same control flow; #1131 strengthens empty/Required |

**Subtotal: 0.35**

### Ink Verification Gate (0.25)

| ID | Criterion | Wt | Pass | Evidence |
|----|-----------|-----|------|----------|
| I1 | Empty → FAIL | 0.10 | ✅ | `ink_verified=False` + clear `source=` message |
| I2 | Ink → PASS | 0.08 | ✅ | SignaturePad not empty and/or allowed non-pixel-only paths |
| I3 | Events preferred / no cosmetic pixel PASS | 0.07 | ✅ | Events first; ctx off by default; pixel-only after ctx → fail; library empty → fail |

**Subtotal: 0.25**

### Shared Helper & Architecture (0.15)

| ID | Criterion | Wt | Pass | Evidence |
|----|-----------|-----|------|----------|
| H1 | Shared module | 0.06 | ✅ | `signature_pad.py` |
| H2 | Layering | 0.05 | ✅ | No endpoint→tier |
| H3 | Lazy tiers | 0.04 | ✅ | ADR-002-1 unchanged |

**Subtotal: 0.15**

### Tests (0.15)

| ID | Criterion | Wt | Pass | Evidence |
|----|-----------|-----|------|----------|
| T1 | Helper unit coverage | 0.08 | ✅ | **100%** on 226 stmts; 61 tests |
| T2 | Soft-act false-success test | 0.07 | ✅ | Soft scrollIntoView + empty → fail |

**Subtotal: 0.15**

### P1 Heuristics / P2 Detection (0.10)

| ID | Criterion | Wt | Pass | Evidence |
|----|-----------|-----|------|----------|
| P1 | Tier 2 empty observe | 0.06 | ✅ | Heuristics + unit |
| P2 | Click vs draw | 0.04 | ✅ | `infer_signature_step_action` matrix |

**Subtotal: 0.10**

---

## Final Score

```
S 0.35 + I 0.25 + H 0.15 + T 0.15 + P 0.10 = 1.00
```

**Status: PASS (ready to merge)** — Feature 5.1 P0 gate met; coverage 100%.

---

## Critical / Major / Minor Issues

### Critical Issues (must fix)
*None.*

### Major Issues (should fix)
*None for merge gate.* Restart backend and optionally re-run CRM sign path to prove live FAIL on empty/Required and PASS only with real ink.

### Minor Issues (nice to fix)
1. **Tier 1 draw without ink gate** — still a documented consistency gap.
2. **Iframe pads** — main-frame locate only.
3. **Login docs** — API OAuth form expects `username=admin`, not the email string.

---

## What Improved Since Feature 5 Eval

- Ctx paint default **off**; pixel-only after ctx **cannot** PASS
- SignaturePad empty **blocks** pixel override
- Near-pad **Required** → fail
- Stronger Pointer/touch multi-point stroke
- `verify_source` on results / Tier 3 FAIL messages
- Coverage held at **100%** while growing 186→226 stmts; tests 48→61

## What Regressed

- None observed in unit suite.
- Live CRM still unproven on **post-fix** binary (pre-fix #1131 remains the bug baseline).

---

## Artifacts

| Area | Files |
|------|--------|
| Shared helper | `backend/app/services/signature_pad.py` |
| Tier 3 | `backend/app/services/tier3_stagehand.py` |
| Unit tests | `backend/tests/unit/test_signature_pad.py` (61) |
| Rubric | `gan-harness/eval-rubric-signature-pad.md` |
| Docs | ADR-002-54 amend, `docs/CODEMAPS/execution-engine.md` |
