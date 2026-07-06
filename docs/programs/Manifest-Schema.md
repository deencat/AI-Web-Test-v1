# Program manifest schema

**Version:** 1.1 · **Date:** 2026-07-06  
**Location:** `backend/config/programs/<program-slug>.yaml`  
**Discovery:** Loader reads all `*.yaml` except `_platform-profiles/` and files prefixed with `_`.

---

## Top-level keys

| Key | Required | Description |
|-----|----------|-------------|
| `program` | Yes | Identity and ReqIQ link |
| `platform_profile` | No | Include shared profile by name (e.g. `dt-telecom-default`) |
| `platform_components` | No | Inline platform bricks; merged over profile if both set |
| `reference_layers` | No | Read-only context; default `automate: false` |
| `product_features` | Yes | Business capabilities + platform mapping |
| `extensions` | No | Program-specific optional blocks |
| `hub_sections` | No | Reference Hub layout (if omitted, UI derives from features) |
| `hub_gaps` | No | Missing links/assets |
| `journey_templates` | No | Seeds for journey registry |
| `factory` | No | Planner/worker rules |

---

## `program`

```yaml
program:
  slug: my-product                    # URL-safe, unique
  title: "Display name"
  locale: zh-HK                       # optional
  kind: production | pilot | example  # optional metadata
  test_scope: DT_ONLY                 # free-text or enum — per program
  reqiq_project_id: "<cuid>"
  source_folder: "docs/..."           # optional local asset path
  notes: "..."                        # optional
```

---

## `platform_profile`

```yaml
platform_profile: dt-telecom-default
```

Resolves to `backend/config/programs/_platform-profiles/dt-telecom-default.yaml` → `platform_components` array.

---

## `platform_components[]`

```yaml
platform_components:
  - id: DT_CRM
    title: CRM
    modules: [product_catalog, customer_portal]
    test_surfaces: [ui]
    notes: "optional"
```

---

## `reference_layers[]`

```yaml
reference_layers:
  - id: REF_LEGACY_PLANS
    title: "Legacy plan tables"
    capability_key: REF_LEGACY_PLANS
    automate: false
    note: "Assertions only — not crawled"
    assets:
      - file: "plan-table.jpg"
        type: image
```

---

## `product_features[]`

```yaml
product_features:
  - id: FEATURE_SIGNUP
    title: "Online signup"
    platform_components: [DT_WEBAPP, DT_CRM]
    reference_layers: [REF_LEGACY_PLANS]
    source_files:
      - "signup-guide.pdf"
```

---

## `extensions` (optional)

Arbitrary YAML per program. Example (5G pilot only):

```yaml
extensions:
  migration:
    capability_key: 5GBB_MIGRATION
    anchor_file: "migration-user-guide.pdf"
```

---

## `journey_templates[]`

```yaml
journey_templates:
  - slug: my-journey-slug
    name: "Human-readable name"
    capability_keys: [FEATURE_A]
    feature_url: "https://..."       # or feature_url_tbd: true
    tags: [regression]
    extra_config:
      program_slug: my-product
      platform_components: [DT_WEBAPP]
      test_kind: ui
```

Merged into `journey_registry_entries` with `project` from journey registry project meta (may equal program slug or a parent project name — configure per deployment).

---

## `factory`

```yaml
factory:
  program_tags: [my-product]
  exclude_capability_keys: [REF_LEGACY_PLANS]
  planner_rules:
    - "Respect test_scope in manifest"
    - "Exclude reference_layers with automate: false"
```

---

## Validation rules (loader)

1. `program.slug` must match filename stem (`<slug>.yaml`).
2. Every `product_features[].platform_components` id must exist in resolved `platform_components`.
3. Every `reference_layers[].id` referenced by features must exist.
4. `journey_templates[].extra_config.program_slug` defaults to `program.slug` if omitted.

---

## Shared profiles

See [`backend/config/programs/README.md`](../../backend/config/programs/README.md) and `_platform-profiles/`.
