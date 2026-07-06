# Program manifest schema

**Version:** 1.2 · **Date:** 2026-07-06  
**Location:** `backend/config/programs/<program-slug>.yaml`  
**Discovery:** Loader reads all `*.yaml` except `_platform-profiles/` and files prefixed with `_`.

---

## Top-level keys

| Key | Required | Description |
|-----|----------|-------------|
| `program` | Yes | Identity and ReqIQ link |
| `platform_profile` | No | Shared platform library (e.g. `dt-telecom-default`) |
| `platform_components` | No | Inline platform bricks; merged over profile |
| `reference_layers` | No | Read-only context; `automate: false` default |
| `initiatives` | Yes | Time-bounded offers, promotions, projects |
| `feature_catalog` | No | Optional shared `capability_key` definitions |
| `hub_sections` | No | Reference Hub layout override |
| `hub_gaps` | No | Missing links/assets |
| `journey_templates` | No | Journey registry seeds |
| `factory` | No | Planner/worker rules |

**Removed from core schema:** top-level `product_features` as primary model (use `initiatives` + optional `feature_catalog`).  
**Migration waves** are **not** initiatives — use `reference_layers` only.

---

## `program`

```yaml
program:
  slug: my-product
  title: "Display name"
  locale: zh-HK
  kind: production | pilot | example
  test_scope: DT_ONLY                 # per-program; free text
  reqiq_project_id: "<cuid>"
  source_folder: "docs/..."
  notes: "..."
```

---

## `initiatives[]`

```yaml
initiatives:
  - id: abc-base-20260530
    kind: base_offer              # base_offer | promotion | project | bundle | ...
    title: "ABC plan"
    effective_from: "2026-05-30"
    effective_to: null            # null = no fixed end
    relationship: null            # null | replace | stack
    relates_to: []                # initiative ids when replace/stack
    audience: null                # optional: new_signups | all | existing_only
    capability_keys: [PLANS_ABC]
    platform_components: [DT_WEBAPP, DT_CRM, DT_MATRIXX, DT_BILLING]
    source_files: []
    regression_tags: [my-product, initiative:abc-base-20260530]
    amendments: []                # see below

  - id: june-marketing-20260605
    kind: promotion
    title: "June marketing"
    effective_from: "2026-06-05"
    effective_to: "2026-06-30"
    relationship: stack           # or replace
    relates_to: [abc-base-20260530]
    capability_keys: [PROMO_JUNE]
    platform_components: [DT_WEBAPP, DT_ECOUPON, DT_BILLING]
    amendments:
      - type: extend_end_date
        amended_at: "2026-06-28"
        previous_effective_to: "2026-06-30"
        new_effective_to: "2026-07-15"
        note: "Optional extension example"
```

### Initiative field reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique within program |
| `kind` | Yes | Display category (offer / promotion / project) |
| `title` | Yes | Human-readable name |
| `effective_from` | Yes | ISO date |
| `effective_to` | No | ISO date or `null` |
| `relationship` | No | `replace` \| `stack` |
| `relates_to` | No | List of initiative `id` |
| `capability_keys` | Yes | ReqIQ + journey tags |
| `platform_components` | Yes | Subset of program platform |
| `source_files` | No | Assets under `program.source_folder` |
| `regression_tags` | No | Factory / regression filters |
| `amendments` | No | End-date extensions and future amendment types |

---

## `reference_layers[]`

```yaml
reference_layers:
  - id: REF_MCS_PLANS
    title: "MCS / BAU plan tables"
    capability_key: REF_MCS_PLANS
    automate: false
    parity_note: "Optional DT vs BAU parity checks — no hard automation rules"
    assets:
      - file: "plan-table.jpg"
        type: image

  - id: REF_MCS_CRM_MIGRATION
    title: "MCS to CRM migration guide"
    capability_key: REF_MCS_CRM_MIGRATION
    automate: false
    parity_note: "Verify DT CRM reflects documented BAU behaviour where applicable"
    assets:
      - file: "migration-user-guide.pdf"
        type: pdf
```

---

## `feature_catalog` (optional)

```yaml
feature_catalog:
  - id: PLANS_ABC
    title: "ABC monthly plan"
    description: "Shared key used across initiatives"
```

---

## `platform_profile` / `platform_components`

Unchanged — see v1.1. Initiatives must only reference resolved platform component ids.

---

## `journey_templates[]`

```yaml
journey_templates:
  - slug: june-promo-wallet
    name: "June promo — My Wallet"
    capability_keys: [PROMO_JUNE]
    initiative_id: june-marketing-20260605
    extra_config:
      program_slug: my-product
      initiative_id: june-marketing-20260605
      platform_components: [DT_WEBAPP, DT_ECOUPON]
      test_kind: ui
    tags: [my-product, initiative:june-marketing-20260605]
```

`initiative_id` at template root mirrors `extra_config.initiative_id` for seed scripts.

---

## `factory`

```yaml
factory:
  program_tags: [my-product]
  exclude_capability_keys: [REF_MCS_PLANS, REF_MCS_CRM_MIGRATION]
  planner_rules:
    - "Initiatives drive test scope; reference_layers are not crawl targets"
    - "relationship stack → prefer delta coverage on relates_to base"
```

---

## Validation rules (loader)

1. `program.slug` matches filename stem.
2. Every `initiatives[].platform_components` id exists in resolved platform.
3. `relates_to` references valid initiative ids in the same manifest.
4. `relationship: replace | stack` should have non-empty `relates_to` (warn if missing).
5. `effective_from` ≤ resolved `effective_to` (after amendments).
6. Reference layer ids in `exclude_capability_keys` should have `automate: false`.

---

## Shared profiles

See [`backend/config/programs/README.md`](../../backend/config/programs/README.md).
