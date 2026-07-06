# Program framework — LEGO architecture

**Version:** 1.1 · **Date:** 2026-07-06  
**Audience:** QA, UAT, developers, factory operators

---

## 1. Principles

1. **Programs are data-driven** — one YAML manifest per product; no hard-coded routes, menus, or bricks in application code.
2. **Platform components vary by product** — telecom DT may use WebApp + CRM + Billing + Matrixx; another product might use only WebApp + API + a single admin portal.
3. **ReqIQ is a building block** — workspace, sources, `capabilityKey`, readiness, wiki; structure and navigation live in AWT.
4. **Reference layers are optional** — legacy systems or read-only context (e.g. MCS plan tables) are **not** test targets unless explicitly marked `automate: true`.

---

## 2. Three LEGO layers

```
┌─────────────────────────────────────────────────────────────┐
│  Program (e.g. 5G 流動寬頻, Postpaid, FMC, …)                │
│  product_features[] — business capabilities                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ each feature maps to ≥1 platform component
┌──────────────────────────▼──────────────────────────────────┐
│  platform_components[] — systems under test for THIS program   │
│  (from platform_profile and/or inline manifest)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ optional
┌──────────────────────────▼──────────────────────────────────┐
│  reference_layers[] — context only (automate: false)           │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Platform components (`platform_components`)

Defined per program via:

- **`platform_profile`** — include a shared library from `backend/config/programs/_platform-profiles/<name>.yaml`, or
- **`platform_components`** — inline list in the program manifest, or
- **Both** — profile as base, manifest entries merge/override.

Each component has:

| Field | Meaning |
|-------|---------|
| `id` | Stable key (e.g. `DT_CRM`, `WEB_PORTAL`, `PAYMENT_API`) |
| `title` | Display name |
| `modules` | Optional sub-areas |
| `test_surfaces` | e.g. `ui`, `api`, `batch`, `integration` |

**Do not assume** every program uses the DT telecom seven-tuple. The **dt-telecom-default** profile is one reusable library.

### 2.2 Product features (`product_features`)

Business-facing capabilities for **this** program:

| Field | Meaning |
|-------|---------|
| `id` | `capability_key` for ReqIQ and journey registry |
| `title` | Display name |
| `platform_components` | Which systems are involved |
| `reference_layers` | Optional links to read-only context |
| `source_files` | Docs/assets for ReqIQ ingest |

### 2.3 Reference layers (`reference_layers`)

| Field | Meaning |
|-------|---------|
| `id` | Layer key |
| `automate` | **`false`** = never crawl/automate (default for legacy) |
| `capability_key` | ReqIQ tag for RAG/assertions only |
| `assets` | Files or URLs |

### 2.4 Extensions (`extensions`)

**Optional, program-specific** blocks — not required in the schema. Examples:

- `extensions.migration` — dual-system transition rules (5G example)
- `extensions.compliance` — regulatory checklist
- `extensions.promo_calendar` — campaign dates

AWT loader passes extensions through to Hub UI as opaque structured data; no code change per extension type in Phase 1.

---

## 3. Journey registry tagging (generic)

Use `JourneyRegistryEntry.extra_config` (existing JSON column):

```yaml
extra_config:
  program_slug: <manifest program.slug>
  platform_components: [DT_CRM, DT_WEBAPP]
  capability_keys: [FEATURE_A, FEATURE_B]
  test_kind: ui          # ui | api | orchestration
  test_scope_note: "DT only; REF_MCS for assertions"
```

Factory and planner read **`program_slug`** and manifest `factory` rules — not product-specific constants in code.

---

## 4. ReqIQ (unchanged)

| Artifact | Convention |
|----------|------------|
| Workspace | `program.reqiq_project_id` per manifest (programs may share or split workspaces) |
| Requirements | `capabilityKey` = `product_features[].id` or platform `id` |
| Readiness | `feature` string from manifest or requirement |
| Wiki | Compiled per workspace; AWT may stitch per-program snippets |
| Exclusions | `factory.exclude_capability_keys` in manifest |

---

## 5. AI Web Test UI (slug-agnostic)

| Route | Behaviour |
|-------|-----------|
| `/programs` | List manifests from `backend/config/programs/*.yaml` |
| `/programs/:slug` | Reference Hub driven entirely by that manifest |
| Knowledge Base | ReqIQ workspace (unchanged); filter by `program_slug` / capability |

Hub sections come from manifest (`hub_sections`, `product_features`, `reference_layers`, `hub_gaps`) — not from hard-coded 5G section names.

---

## 6. Factory integration

Manifest `factory` block:

```yaml
factory:
  program_tags: [<slug>, ...]
  exclude_capability_keys: [...]
  planner_rules: [...]
```

Worker/planner receives `program_slug`, loads manifest, applies rules. **No** `if slug == '5g-mobile-broadband'` in application code.

---

## 7. Adding a new program (checklist)

1. Copy `backend/config/programs/5g-mobile-broadband.yaml` → `<new-slug>.yaml`.
2. Set `program.slug`, `title`, `reqiq_project_id`, `test_scope`.
3. Choose `platform_profile` or define `platform_components`.
4. Define `product_features` and optional `reference_layers`.
5. Add `docs/programs/examples/<slug>/` case study (optional).
6. Seed `journey_templates` with real UAT URLs when known.
7. Register journeys with `extra_config.program_slug`.

See [Manifest-Schema.md](Manifest-Schema.md) and [Implementation-Plan.md](Implementation-Plan.md).

---

## 8. Example

[5G 流動寬頻](examples/5g-mobile-broadband/README.md) — DT telecom pilot using profile `dt-telecom-default`, MCS reference layer, and `extensions.migration`.
