# Program framework — LEGO architecture

**Version:** 1.2 · **Date:** 2026-07-06  
**Audience:** QA, UAT, developers, factory operators

---

## 1. Principles

1. **Programs are data-driven** — one YAML manifest per product line; no hard-coded routes or product names in code.
2. **Initiatives are time-bounded** — offers, promotions, and delivery projects are **initiatives** under a program (same internal name; display label via `kind` + `title`).
3. **Platform components are stable per program** — WebApp, CRM, Billing, etc. Initiatives declare which components they touch.
4. **ReqIQ is a building block** — sources, requirements, readiness, wiki; structure and timeline live in AWT.
5. **Reference layers are not initiatives** — legacy docs (e.g. MCS migration guides) support **parity verification** only; no hard automation rules yet.

---

## 2. Four-layer model

```
┌─────────────────────────────────────────────────────────────┐
│  Program (long-lived: e.g. mobile broadband line)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ platform_      │ │ reference_   │ │ initiatives[]        │
│ components     │ │ layers       │ │ (timed commercial /  │
│ (what we test) │ │ (context)    │ │  delivery work)      │
└────────────────┘ └──────────────┘ └──────────────────────┘
```

| Layer | Lifetime | Example |
|-------|----------|---------|
| **Program** | Years | Product line umbrella |
| **Platform components** | Stable (per program) | DT WebApp, CRM, Billing, Matrixx |
| **Reference layers** | Stable context | MCS plan tables; migration user guide for **DT vs BAU parity checks** |
| **Initiatives** | Start/end (flexible) | ABC base offer 30-May; June marketing 5-Jun |

---

## 3. Initiatives (canonical term)

**Internal schema name:** `initiatives`  
**UI labels:** Offer, Promotion, Project — via `kind` + `title` (marketing language).

### 3.1 What an initiative is

One **launch or change** under a program: base plan go-live, rebate promo, IT project enabling a new CRM flow, etc.

### 3.2 Core fields

| Field | Meaning |
|-------|---------|
| `id` | Stable slug (e.g. `abc-base-20260530`) |
| `kind` | `base_offer` \| `promotion` \| `project` \| `bundle` \| … (display only) |
| `title` | Human name (e.g. "ABC plan", "June marketing") |
| `effective_from` | Launch / go-live date |
| `effective_to` | End date, or **`null`** = open-ended |
| `relationship` | `replace` \| `stack` — vs prior initiative(s) |
| `relates_to` | Initiative id(s) this replaces or stacks on (when applicable) |
| `capability_keys` | ReqIQ / journey / coverage tags |
| `platform_components` | Subset of program platform touched by **this** initiative |
| `source_files` | PDFs, circulars for this wave |
| `regression_tags` | Factory / Loop B filters |

### 3.3 Replace vs stack

| `relationship` | Meaning | Test focus |
|----------------|---------|------------|
| **`replace`** | Supersedes prior offer/terms for scope in `relates_to` | Full regression on new initiative; retire or narrow old journeys |
| **`stack`** | Adds on top; base offer still valid | **Delta** tests: promo, coupon, rebate, banner — plus smoke on base |

Audience (new customers only vs all) can be added per initiative when needed (`audience: new_signups | all | existing_only`) — optional field.

### 3.4 End dates and extensions

- **`effective_to: null`** — no fixed end.
- **Fixed end** — e.g. `2026-06-30`.
- **Extension before end** — `amendments[]` on the initiative (no new initiative required):

```yaml
amendments:
  - type: extend_end_date
    amended_at: "2026-06-28"
    previous_effective_to: "2026-06-30"
    new_effective_to: "2026-07-15"
    note: "Marketing extension approved"
```

Loader/UI uses **latest** `effective_to` after amendments for timeline display.

### 3.5 Worked example (generic)

```yaml
initiatives:
  - id: abc-base-20260530
    kind: base_offer
    title: "ABC plan"
    effective_from: "2026-05-30"
    effective_to: null
    relationship: null
    capability_keys: [PLANS_ABC]
    platform_components: [DT_WEBAPP, DT_CRM, DT_MATRIXX, DT_BILLING]

  - id: june-marketing-20260605
    kind: promotion
    title: "June marketing"
    effective_from: "2026-06-05"
    effective_to: "2026-06-30"
    relationship: stack          # or: replace
    relates_to: [abc-base-20260530]
    capability_keys: [PROMO_JUNE]
    platform_components: [DT_WEBAPP, DT_ECOUPON, DT_BILLING]
```

Multiple initiatives may be **active at once** (base + stacked promo).

---

## 4. Platform components

Defined per program via `platform_profile` and/or inline `platform_components` (see [Manifest-Schema.md](Manifest-Schema.md)).

Initiatives **reference** these ids; they do not redefine the platform stack unless a program adds inline components.

---

## 5. Reference layers (not initiatives)

For **read-only context** — especially legacy BAU/MCS material.

| Field | Meaning |
|-------|---------|
| `automate` | **`false`** by default — never crawl MCS/BAU |
| `capability_key` | ReqIQ tag for RAG / manual assertions |
| `parity_note` | Optional: "Use to verify DT CRM shows equivalent function to BAU MCS" |

**Migration guides** (e.g. MCS→CRM user guide) live here — **not** as initiatives or migration waves. QA may use them to compare DT behaviour to documented BAU behaviour; **no hard factory rules** until the team defines them.

---

## 6. Product features vs initiatives

- **`initiatives`** — primary unit for timeline, docs, tests, and factory backlog.
- **`feature_catalog`** (optional) — shared vocabulary of `capability_keys` across initiatives; omit if initiative keys are enough.

Do **not** create a separate program YAML per initiative.

---

## 7. Journey registry

```yaml
extra_config:
  program_slug: mobile-broadband
  initiative_id: june-marketing-20260605
  platform_components: [DT_ECOUPON, DT_WEBAPP]
  capability_keys: [PROMO_JUNE]
  test_kind: ui
```

Factory filters by `program_slug`, `initiative_id`, and `regression_tags`.

---

## 8. ReqIQ (unchanged schema)

| Artifact | Convention |
|----------|------------|
| Workspace | `program.reqiq_project_id` |
| Requirements | `capabilityKey` from initiative `capability_keys` |
| Readiness | `feature` scoped to initiative title or key |
| Sources | Upload per initiative `source_files` |
| Reference | `reference_layers` — parity context only |

---

## 9. AI Web Test UI (slug-agnostic)

| Route | Behaviour |
|-------|-----------|
| `/programs` | List programs |
| `/programs/:slug` | Hub: platform, reference, **initiative timeline** |
| `/programs/:slug/initiatives/:id` | Detail: docs, coverage, journeys (PG-1+) |

---

## 10. Factory integration

```yaml
factory:
  program_tags: [<program-slug>]
  exclude_capability_keys: [REF_MCS_PLANS]   # reference layers
  planner_rules:
    - "Scope test-gen to initiative platform_components"
    - "For relationship stack, prefer delta journeys over full base replay"
```

---

## 11. Adding a new program

1. Create `backend/config/programs/<slug>.yaml`.
2. Set `platform_profile` or `platform_components`.
3. Add `reference_layers` if legacy parity docs exist.
4. Add `initiatives[]` with dates, relationship, and capability keys.
5. Seed `journey_templates` per initiative when UAT URLs are known.

See [Manifest-Schema.md](Manifest-Schema.md) · [Implementation-Plan.md](Implementation-Plan.md).

---

## 12. Example manifest

[5G 流動寬頻](examples/5g-mobile-broadband/README.md) — DT telecom example with `reference_layers` (MCS + migration guide) and sample `initiatives`.
