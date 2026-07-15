# Evaluation Rubric: CRM Login Toggle Persist

**Feature:** Fix `requires_runtime_credentials` omitted by API sanitizer  
**Spec:** `gan-harness/spec.md` § Feature 3  
**Weight total:** 1.0  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Sanitizer still omits `requires_runtime_credentials`; GET after update `true` returns `false`; passwords/credentials persisted to DB or `localStorage`; CRM auth redesign scope creep

---

## Implementation Checklist (Generator)

Sprint order — **do not skip**:

| Sprint | Deliverables | Key paths |
|--------|--------------|-----------|
| 7 | Sanitizer + round-trip tests | `tests.py` `sanitize_test_case_for_response`, unit/API tests |
| 7 (same PR if cheap) | SavedTestsPage local map + optional E2E | `SavedTestsPage.tsx` post-save `setTests`; Playwright optional |

**Required change:**

```python
# backend/app/api/v1/endpoints/tests.py — inside sanitize_test_case_for_response dict
'requires_runtime_credentials': getattr(test_case, 'requires_runtime_credentials', False),
```

**Optional frontend:**

```typescript
// SavedTestsPage post-save setTests map — include:
requires_runtime_credentials: editForm.requires_runtime_credentials,
```

**Do NOT:**
- Persist passwords, usernames, or credential objects
- Add migrations or rename the column
- Redesign CredentialPromptModal / Run injection

---

## Backend Sanitizer & API Round-Trip (0.40)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| B1 | Sanitizer key present | `sanitize_test_case_for_response` dict includes `requires_runtime_credentials` | 0.12 |
| B2 | True round-trip | Update/set ORM `true` → GET `/tests/{id}` JSON `requires_runtime_credentials === true` | 0.12 |
| B3 | False round-trip | Update `false` → GET returns `false` | 0.06 |
| B4 | List includes field | GET list item for that test includes correct boolean (not missing → default false) | 0.05 |
| B5 | Clone response honest | Clone of `true` source returns sanitized `true` | 0.05 |

---

## Security — Credentials Remain Ephemeral (0.20)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| S1 | No credential in DB | After toggle save / Run prompt, `test_cases` row has no password/username columns or credential blobs in JSON fields from this feature | 0.08 |
| S2 | No credential in API test-case body | GET/PUT `TestCaseResponse` has boolean only — no `login_credentials` / password fields | 0.06 |
| S3 | No localStorage secrets | Frontend does not write passwords to `localStorage` / `sessionStorage` on toggle save | 0.06 |

---

## Frontend Persistence UX (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| F1 | Toggle survives navigate | Enable → save → leave page → return → Edit → toggle ON | 0.08 |
| F2 | Toggle survives hard reload | Enable → save → full browser reload → Edit → toggle ON | 0.08 |
| F3 | OFF still works | Disable → save → reload → toggle OFF | 0.04 |
| F4 | SavedTests local map (Should-Have) | Post-save `setTests` includes `requires_runtime_credentials` | 0.03 |
| F5 | Run consumes flag | With flag ON, Run shows credential prompt (existing behavior preserved) | 0.02 |

---

## Tests & E2E Expectations (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | Unit/API covers sanitize path | New or extended test fails if sanitizer omits field; update true → GET true | 0.07 |
| T2 | Existing CRM ephemeral tests pass | `test_crm_ephemeral_credentials.py` (or successor) still green | 0.03 |
| T3 | E2E or documented manual script | Playwright spec **or** evaluator script below executed with evidence | 0.05 |

**E2E expectation:** Prefer a focused Playwright journey (toggle → save → reload → assert checked). If timeboxed, document manual run of the script below with screenshots/network proof. Missing both T1 and T3 → fail T1 (sanitize unit test is mandatory).

---

## Non-Regression (included in automatic fail / craft)

| Check | Pass condition |
|-------|----------------|
| Feature 1 Stop Execution | Unchanged |
| Feature 2 Clone | Still clones; clone of `true` still true after sanitizer fix |
| Empty description sanitization | Still rewrites empty `description` / `expected_result` |

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

---

## Evaluator Test Script (Playwright / manual)

1. Log in as a normal user; open **Saved Tests** (`/tests/saved`).
2. Edit an existing test (or create one, save, then edit).
3. Enable **Requires CRM Login** → **Save**.
4. In Network tab, confirm PUT response includes `"requires_runtime_credentials": true`.
5. Close drawer; navigate to Dashboard (or any other route); return to Saved Tests; Edit same test → assert toggle **ON**.
6. Hard-reload the browser; Edit same test → assert toggle **ON**.
7. GET `/api/v1/tests/{id}` (or via DevTools) → field is `true`.
8. Click **Run** → credential prompt appears (do not need successful login).
9. Confirm no password appears in Application → Local Storage for this app origin from the toggle/save flow.
10. Disable toggle → Save → reload → assert **OFF**; GET returns `false`.
11. Optional: Clone a `true` test → open clone → toggle ON.
12. Run backend tests covering sanitize round-trip:
    `cd backend && .\venv\Scripts\activate && python -m pytest tests/unit/ -q -k "requires_runtime or crm_ephemeral or sanitize"`  
    (adjust `-k` to match the files the Generator adds).

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Sanitizer still omits the key | Automatic fail |
| Frontend caches flag only in memory/localStorage without API fix | Fail B2 / F2 |
| Persisting password to fix "login forgotten" | Automatic fail (S1) |
| Large CRM auth refactor in same PR | Automatic fail (scope) |
| Removing Pydantic default without fixing sanitizer | Fail B2 |
| Claiming fix via TestDetail only while SavedTests still broken | Fail F1 |
