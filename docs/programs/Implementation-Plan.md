# Program framework — Implementation plan

**Version:** 1.1 · **Date:** 2026-07-06  
**Track code:** **PG** (generic; not tied to one product)  
**Depends on:** Hermes Factory **HF-2** (journey registry), **HF-3** (factory worker), ReqIQ proxy

**Legend:** ⬜ Not started · 🔜 Next · ⚠️ Partial · ✅ Done

---

## 0. Progress tracker

| Phase | Status | Notes |
|-------|--------|-------|
| **PG-0** Framework docs + schema | ✅ | Generic framework; 5G = example manifest only |
| **PG-1** Program loader + Reference Hub | ⬜ | Slug-agnostic `/programs/:slug` |
| **PG-2** ReqIQ onboarding pattern | ⬜ | Per-program checklist, not hard-coded uploads |
| **PG-3** Journey registry integration | ⬜ | `extra_config.program_slug`, `platform_components` |
| **PG-4** Factory planner scoping | ⬜ | Load manifest rules by `program_slug` |
| **PG-5** API / orchestration test profile | ⬜ | Optional per `test_surfaces` |

**Example pilot:** [5g-mobile-broadband](examples/5g-mobile-broadband/README.md) — first manifest to validate PG-1…PG-4.

---

## 1. Goals

1. **Data-driven programs** — any product via YAML; no 5G-specific code paths.
2. **Composable platform profiles** — reuse `dt-telecom-default` or define custom components.
3. **ReqIQ unchanged** — `capabilityKey`, readiness, wiki per program manifest.
4. **Journey registry** — extend `extra_config` only (no breaking DB change in Phase 1).
5. **Factory** — planner reads `factory` block from manifest for any `program_slug`.

---

## 2. Phase PG-0 — Framework documentation ✅

| ID | Story | Status |
|----|-------|--------|
| PG-0.1 | [Program-Framework.md](Program-Framework.md) | ✅ |
| PG-0.2 | [Manifest-Schema.md](Manifest-Schema.md) | ✅ |
| PG-0.3 | Example manifest + platform profile | ✅ |
| PG-0.4 | Example case study (5G) | ✅ |

---

## 3. Phase PG-1 — Program loader + Reference Hub

**Estimate:** 3–5 days

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-1.1 | Loader service | `program_registry_service.py` | Discovers all `config/programs/*.yaml`; merges `platform_profile` |
| PG-1.2 | REST API | `GET /api/v1/programs`, `GET /api/v1/programs/{slug}` | List + detail from YAML |
| PG-1.3 | Hub page | `ProgramHubPage.tsx` at `/programs/:slug` | Renders manifest sections dynamically |
| PG-1.4 | Programs index | `/programs` | Lists all loaded programs |
| PG-1.5 | Sidebar | **Programs** menu | No single-product label |
| PG-1.6 | Reference / gap UI | Hub items | `automate: false` badge; `hub_gaps` status |

**Out of scope:** Visual manifest editor (YAML + redeploy for v1).

---

## 4. Phase PG-2 — ReqIQ onboarding pattern

**Estimate:** 2–3 days (per program, repeatable)

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-2.1 | Onboarding doc template | `docs/programs/examples/_template/ReqIQ-Onboarding.md` | Steps: upload → reindex → requirements |
| PG-2.2 | Script optional | `scripts/seed-program-reqiq.py --manifest <slug>` | Reads `source_files` from manifest |
| PG-2.3 | KB filter | Filter requirements by `program_slug` / capability | Uses existing coverage matrix |

Validate with **5G example** first; same process for next product.

---

## 5. Phase PG-3 — Journey registry integration

**Estimate:** 3–4 days

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-3.1 | Template seed | Merge `journey_templates` from any manifest | Idempotent upsert |
| PG-3.2 | `extra_config` schema | Document + validate | `program_slug`, `platform_components`, `test_kind` |
| PG-3.3 | Registry UI | Columns: program, platform components | Journey Registry page |
| PG-3.4 | Multi-program | Several manifests coexist | No slug collision |

---

## 6. Phase PG-4 — Factory planner scoping

**Estimate:** 2–3 days

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-4.1 | Pass `program_slug` | Worker / bridge / planner | From backlog item or journey |
| PG-4.2 | Load manifest rules | `factory.exclude_capability_keys`, `planner_rules` | No product-specific `if` in code |
| PG-4.3 | Readiness gate | `feature` from `product_features` | Before test-gen |
| PG-4.4 | Regression tags | `factory.program_tags` | Loop B filter |

---

## 7. Phase PG-5 — API / orchestration profile

**Estimate:** 5–8 days (when a program needs non-UI surfaces)

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-5.1 | `test_kind: api` | Registry validation | Journeys with `test_surfaces: api` |
| PG-5.2 | Orchestration suites | Tagged test groups | Multi-`platform_components` golden paths |
| PG-5.3 | Linked runbooks | Hub links to Postman/collections | Per manifest |

---

## 8. Suggested order

| Week | Focus |
|------|--------|
| 1 | PG-1 loader + `/programs` + `/programs/:slug` |
| 2 | PG-3 journey seed + PG-2 for one example manifest |
| 3 | PG-4 factory scoping |
| 4+ | PG-5; second program manifest to prove generality |

---

## 9. Verification (framework launch)

- [ ] Two different slugs load without code change (e.g. 5G example + minimal stub manifest)
- [ ] Hub UI renders from YAML only
- [ ] `reference_layers` with `automate: false` show **Reference — not tested**
- [ ] Journey `extra_config.program_slug` round-trips
- [ ] Factory respects per-manifest `exclude_capability_keys`

---

## 10. Related documents

- [Program-Framework.md](Program-Framework.md)
- [Manifest-Schema.md](Manifest-Schema.md)
- [examples/5g-mobile-broadband/](examples/5g-mobile-broadband/README.md)
- [Hermes QA Factory Agile Plan](../Hermes_QA_Factory_Agile_Development_Plan.md)
