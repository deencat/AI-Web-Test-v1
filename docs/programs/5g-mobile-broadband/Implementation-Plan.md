# 5G 流動寬頻 — Implementation plan

**Version:** 1.0 · **Date:** 2026-07-06  
**Program code:** **PG-5G**  
**Depends on:** Hermes Factory **HF-2** (journey registry), **HF-3** (factory worker), ReqIQ proxy (handoff §5)  
**Branch target:** `feat/hermes-qa-factory` (or feature branch `feat/pg-5g-program`)

**Legend:** ⬜ Not started · 🔜 Next · ⚠️ Partial · ✅ Done

---

## 0. Progress tracker

| Phase | Status | Notes |
|-------|--------|-------|
| **PG-5G-0** Documentation & manifest | ✅ | This plan + `5g-mobile-broadband.yaml` |
| **PG-5G-1** Program loader + Reference Hub (read-only) | ⬜ | |
| **PG-5G-2** ReqIQ seed + coverage tags | ⬜ | |
| **PG-5G-3** Journey registry 5G DT entries | ⬜ | |
| **PG-5G-4** Factory planner DT scoping | ⬜ | |
| **PG-5G-5** API / orchestration test profile | ⬜ | Matrixx, Billing, Provisioning |

---

## 1. Goals

1. Model **5G 流動寬頻** as an AWT **program** with DT platform LEGO bricks.
2. Keep **MCS/BAU reference-only**; all automation targets **DT**.
3. Use **ReqIQ unchanged** — workspace, sources, `capabilityKey`, readiness, wiki.
4. Extend **Journey Registry** via `extra_config` (no breaking schema changes in Phase 1).
5. Enable **Hermes factory** to plan/generate tests per `dt_component` + `capability_key`.

---

## 2. Phase PG-5G-0 — Documentation & manifest ✅

| ID | Story | Owner | Status |
|----|-------|-------|--------|
| PG-5G-0.1 | Architecture doc | AWT | ✅ |
| PG-5G-0.2 | Implementation plan (this file) | AWT | ✅ |
| PG-5G-0.3 | Document inventory | AWT | ✅ |
| PG-5G-0.4 | Program manifest YAML | AWT | ✅ |

**Acceptance:** Docs under `docs/programs/5g-mobile-broadband/`; manifest at `backend/config/programs/5g-mobile-broadband.yaml`.

---

## 3. Phase PG-5G-1 — Program loader + Reference Hub (read-only)

**Estimate:** 3–5 days · **Priority:** High

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-5G-1.1 | YAML loader service | `program_registry_service.py` | Load manifest; validate brick IDs |
| PG-5G-1.2 | `GET /api/v1/programs` | REST list + detail | Returns program slug, bricks, features |
| PG-5G-1.3 | Reference Hub page | `ProgramHubPage.tsx` route `/programs/5g-mobile-broadband` | Sections: Overview, DT Platform, Product features, Reference |
| PG-5G-1.4 | Sidebar nav | `Layout` / routes | **Programs** menu entry |
| PG-5G-1.5 | Migration banner | Hub overview | Shows Phase 1 criteria + link to migration PDF |
| PG-5G-1.6 | Gap markers | Hub items | `ingested` / `external_url` / `gap` from manifest |

**Out of scope:** Admin UI to edit hub (YAML edit + redeploy is OK for pilot).

**Dependencies:** None beyond existing FastAPI + React stack.

---

## 4. Phase PG-5G-2 — ReqIQ seed + coverage

**Estimate:** 2–3 days · **Priority:** High

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-5G-2.1 | Upload script or checklist | `scripts/seed-5g-reqiq-sources.md` or Python script | All DT PDFs uploaded to workspace |
| PG-5G-2.2 | Reference JPGs | Upload + TXT companion | Plan tables searchable (or note OCR gap per handoff) |
| PG-5G-2.3 | Starter requirements | 15–25 DRAFT requirements | Tagged `capabilityKey` per inventory |
| PG-5G-2.4 | Wiki compile | DT-focused wiki patch | Migration + DT procedures; MCS appendix |
| PG-5G-2.5 | Coverage matrix review | KB UI filter by program | Gaps visible per feature |

**ReqIQ workspace:** use `reqiq_project_id` from manifest (default Three-HK project until dedicated workspace created).

---

## 5. Phase PG-5G-3 — Journey registry (DT only)

**Estimate:** 3–4 days · **Priority:** High

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-5G-3.1 | Extend seed YAML | `backend/config/programs/5g-journey-registry.yaml` or extend uat registry | Journeys include `extra_config` |
| PG-5G-3.2 | WebApp journeys | Plan browse, signup path | `dt_components: [DT_WEBAPP]`, UAT URLs |
| PG-5G-3.3 | CRM journeys | Subscription maintenance, cooling-off | `DT_CRM`, `requires_runtime_credentials` |
| PG-5G-3.4 | e-Coupon + WebApp | My Wallet router coupon | Multi-component tags |
| PG-5G-3.5 | Registry UI | Show `dt_components` column | Journey Registry page |
| PG-5G-3.6 | Seed on startup | Optional env `PROGRAM_REGISTRY_SEED=true` | Idempotent upsert |

**Placeholder URLs:** CRM / Matrixx UAT endpoints to be filled by ops (document in manifest `url_tbd: true`).

---

## 6. Phase PG-5G-4 — Factory planner DT scoping

**Estimate:** 2–3 days · **Priority:** Medium

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-5G-4.1 | Planner context | Bridge / worker passes `program_slug` | Hermes prompt includes DT-only rule |
| PG-5G-4.2 | `plan_coverage` filter | MCP or worker | Excludes `REF_MCS_PLANS` from crawl |
| PG-5G-4.3 | Readiness gate | Before test-gen | `feature` from manifest per capability |
| PG-5G-4.4 | Regression tags | `5g-broadband`, `dt-crm`, etc. | Loop B can filter program |

**Dependencies:** HF-3 worker, ReqIQ readiness proxy.

---

## 7. Phase PG-5G-5 — API & orchestration (Matrixx, Billing, Provisioning)

**Estimate:** 5–8 days · **Priority:** Medium (after UI paths stable)

| ID | Story | Deliverable | Acceptance |
|----|-------|-------------|------------|
| PG-5G-5.1 | `test_kind: api` in registry | Schema docs + validation | Journeys without `feature_url` browser crawl |
| PG-5G-5.2 | API test runner stub | Or Postman collection linked from Hub | Matrixx usage check documented |
| PG-5G-5.3 | Orchestration suites | Test suite entity or tagged group | Golden path 1–3 from Architecture |
| PG-5G-5.4 | MIS report snapshot | Manual or scripted compare | Document procedure in QA handout |

**Note:** Full API automation may require new execution engine profile beyond Playwright — track as platform spike if needed.

---

## 8. Suggested sprint order

| Week | Focus |
|------|--------|
| **1** | PG-5G-1 (Hub UI + API loader) |
| **2** | PG-5G-2 (ReqIQ upload + requirements) + PG-5G-3.1–3.3 (WebApp + CRM journeys) |
| **3** | PG-5G-3.4–3.6 + PG-5G-4 (factory scoping) |
| **4+** | PG-5G-5 API/orchestration; expand hub gaps from intranet |

---

## 9. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| CRM UAT URL / credentials not available | Document placeholders; use Sprint 10.14 ephemeral login when ready |
| Plan table JPGs weak in ReqIQ RAG | TXT/MD companions per Developer Handoff; OCR spike later |
| Matrixx/Billing not browser-testable | Phase 5 API profile; manual checklist in QA handout until automated |
| Intranet links missing from repo | Hub `gap` markers; assign owners in manifest |
| DHCP / UAT URL churn | Journey registry as single source; env-specific overlay YAML optional |

---

## 10. Verification checklist (program launch)

- [ ] Program Hub loads from YAML without server error
- [ ] MCS section shows **Reference only — not tested**
- [ ] ≥2 WebApp journeys in registry with `DT_WEBAPP`
- [ ] ≥1 CRM journey with ephemeral credential flag
- [ ] ReqIQ coverage matrix shows all `5GBB_*` keys with ≥1 requirement each
- [ ] Factory `drain_backlog` respects `test_scope: DT_ONLY`
- [ ] Team handouts link to program docs

---

## 11. Related documents

- [Architecture.md](Architecture.md)
- [Document-Inventory.md](Document-Inventory.md)
- [Hermes QA Factory Agile Plan](../../Hermes_QA_Factory_Agile_Development_Plan.md) §17 (add PG-5G cross-link)
- [Week-1 Checklist](../../handouts/Week-1-Checklist.md)
