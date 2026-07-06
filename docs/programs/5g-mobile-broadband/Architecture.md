# 5G 流動寬頻 — DT platform architecture

**Version:** 1.0 · **Date:** 2026-07-06  
**Audience:** QA, UAT, developers, factory operators  
**Parent:** [Program README](README.md)

---

## 1. Scope

| In scope (test) | Out of scope (reference only) |
|-----------------|--------------------------------|
| DT **WebApp** (web + API) | MCS / BAU operational systems |
| DT **CRM** (product catalog, customer portal) | MCS plan-table **execution** |
| DT **Billing** | |
| DT **Matrixx / MTX** (rating, charging, RAN policy) | |
| DT **Provisioning** (core network, notification gateway) | |
| DT **e-Coupon** (coupons, vouchers) | |
| DT **MIS** (reporting) | |

**MCS / BAU plan tables** (JPG screenshots in `docs/5G 流動寬頻/`) remain in ReqIQ as **reference** so testers can assert DT behaviour (e.g. CRM subscription offer shows BAU plan code **5Z1**). They are **not** journey or factory targets.

---

## 2. Layered LEGO model

```
┌─────────────────────────────────────────────────────────────┐
│  Product program: 5G 流動寬頻                                │
│  Features: plans, VAS, router, migration, promos, self-svc  │
└──────────────────────────┬──────────────────────────────────┘
                           │ spans multiple DT components
┌──────────────────────────▼──────────────────────────────────┐
│  DT platform (TEST TARGETS)                                  │
│  WebApp │ CRM │ Billing │ Matrixx │ Prov │ e-Coupon │ MIS   │
└──────────────────────────┬──────────────────────────────────┘
                           │ reference only
┌──────────────────────────▼──────────────────────────────────┐
│  REF_MCS_PLANS — legacy plan codes & charge-code context       │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Platform bricks (`dt_component`)

| Brick ID | Subsystem | Modules / notes |
|----------|-----------|-----------------|
| `DT_WEBAPP` | WebApp | Public DTPPD pages, My3 / 3.com, REST APIs |
| `DT_CRM` | CRM | Product catalog, customer management portal |
| `DT_BILLING` | Billing | GL, reporting, invoice, autopay, offline billing, **3SUPREME class movement** (upgrade/downgrade) |
| `DT_MATRIXX` | Matrixx / MTX | Online real-time rating & charging; RAN policy & usage configuration |
| `DT_PROVISIONING` | Provisioning | Core mobile network configuration; notification gateway (SMS/MMS) |
| `DT_ECOUPON` | e-Coupon | Coupon & voucher lifecycle (e.g. My Wallet router redemption) |
| `DT_MIS` | MIS | Management / operational reporting |
| `DT_MIGRATION` | Cross-cutting | MCS→CRM migration **rules as DT expectations** (not MCS testing) |

### 2.2 Product feature bricks (`capability_key`)

| Feature ID | Description | Typical DT components |
|------------|-------------|------------------------|
| `5GBB_PLANS` | 5G broadband monthly plans (5Z1–5Z4, etc.) | WebApp, CRM, Matrixx, Billing |
| `5GBB_VAS` | VAS data packs (DT Version contracts) | CRM, Matrixx, Billing |
| `5GBB_ROUTER` | Router rental, renewal, shop collection | CRM, e-Coupon, WebApp, Provisioning, Billing |
| `5GBB_MIGRATION` | Migrated customer shape on DT | CRM, WebApp, e-Coupon, Provisioning |
| `5GBB_COOLING_OFF` | 7-day cooling-off (CRM procedure) | CRM, Billing |
| `5GBB_SELF_SERVICE` | My3 / 3SUPREME password, 易賞錢 binding | WebApp |
| `5GBB_PROMO` | Campaigns (e.g. Tai Po) | WebApp, CRM |
| `5GBB_FMC` | Home broadband FMC (adjacent) | WebApp, CRM |
| `REF_MCS_PLANS` | **Reference only** — MCS plan tables | *(none — ReqIQ context)* |

### 2.3 Two tagging dimensions

Every test journey or requirement should specify:

1. **`dt_components`** — *where* on DT (platform brick)
2. **`capability_keys`** — *what* product feature

Example — **Router renewal + My Wallet coupon**:

| Step | Component |
|------|-----------|
| CRM renewal order | `DT_CRM` |
| Coupon issued | `DT_ECOUPON` |
| My3 wallet display | `DT_WEBAPP` |
| MMS 14 days before effective date | `DT_PROVISIONING` |

---

## 3. Migration context (DT testing, not MCS)

Anchor document: `現有5G寬頻月費計劃Migration安排新舊系統至CRM User Guide.pdf`

**Purpose on DT:** define expected CRM/WebApp behaviour for **migrated** 5GBB customers (Phase 1: plans **5Z1 / 5Z2 / 5Z3**, no secondary MSISDN or Add-On SIM).

| Topic | DT assertion (examples) |
|-------|-------------------------|
| Subscription offer | BAU plan code (e.g. **5Z1**) visible in CRM offer details |
| Billing account | CRM billing acct = **`0000` + MCS account** |
| Rebates / rental | Remaining rebate periods carried to CRM |
| Cooling-off | Follow **CRM** procedure PDF (not MCS) |
| My3 first login | OTP → optional password update after BAU→DT |
| Router collection | Coupon in My Wallet; MMS before effective date (from **2026-06-30**) |

**ReqIQ:** ingest migration guide under `5GBB_MIGRATION` + `DT_MIGRATION`; link `REF_MCS_PLANS` for plan-code lookup.

---

## 4. ReqIQ as a LEGO brick (no schema changes)

| Artifact | Usage |
|----------|--------|
| **One workspace** | e.g. Three-HK / 5G program (`reqiq_project_id` in manifest) |
| **Sources** | Upload DT PDFs + reference JPGs; reindex for RAG |
| **Requirements** | `capabilityKey` = product feature or `DT_*` platform key |
| **Readiness / RAG** | `feature` query string scopes test-gen (e.g. `5G BB VAS on DT`) |
| **Wiki** | DT-focused compiled context for Hermes; MCS tables as appendix |
| **Coverage matrix** | Gaps per `capabilityKey` × DT component (AWT manifest + matrix UI) |

Flag reference-only sources in the **AWT program manifest** (`reference_only: true`) so factory excludes them from crawl targets.

---

## 5. AI Web Test responsibilities

| Layer | Owner | Deliverable |
|-------|-------|-------------|
| **Program manifest** | AWT | `backend/config/programs/5g-mobile-broadband.yaml` |
| **Reference Hub UI** | AWT | Portal-style nav: DT Platform → Product features → Reference |
| **Journey Registry** | AWT | UAT URLs + `extra_config.dt_components` |
| **Tests & execution** | AWT | Playwright (WebApp, CRM), API tests (Matrixx, Billing, …) |
| **Factory / Hermes** | AWT + Bridge | `plan_coverage`, `drain_backlog` scoped to DT + capability keys |
| **Knowledge** | ReqIQ via proxy | Sources, requirements, readiness |

### Journey registry `extra_config` (recommended shape)

```yaml
extra_config:
  dt_components: [DT_CRM, DT_WEBAPP]
  test_kind: ui          # ui | api | orchestration
  customer_state: migrated   # new_sale | migrated | renewal
  requires_runtime_credentials: true   # CRM — Sprint 10.14
```

Existing model: `JourneyRegistryEntry.extra_config` (JSON) — **no DB migration required** for Phase 1.

---

## 6. Test strategy by component

| Component | Primary automation | Notes |
|-----------|-------------------|--------|
| **DT_WEBAPP** | Playwright + API | Existing UAT URLs, OTP, preprod modules |
| **DT_CRM** | Playwright | Ephemeral CRM credentials (Sprint 10.14) |
| **DT_BILLING** | API / batch / MIS export | Invoice, autopay, SUPREME class movement |
| **DT_MATRIXX** | API integration | Usage, rating, policy after subscribe |
| **DT_PROVISIONING** | Integration | Order → prov → MMS/SMS |
| **DT_ECOUPON** | UI + API | CRM → My Wallet coupon path |
| **DT_MIS** | Report validation | Post-order snapshots |
| **REF_MCS_PLANS** | None | ReqIQ reference only |

**Golden paths** (multi-component suites):

1. WebApp new sale → CRM order → Provisioning → Matrixx policy  
2. CRM renewal → e-Coupon → WebApp My Wallet → Provisioning MMS  
3. VAS subscribe → Matrixx rating → Billing invoice line  

---

## 7. UI information architecture (target)

```
Programs → 5G 流動寬頻
├── Overview (coverage by DT component, migration banner)
├── DT Platform
│   ├── WebApp · CRM · Billing · Matrixx · Provisioning · e-Coupon · MIS
├── Product features (plans, VAS, router, …)
└── Reference (MCS plan tables — read-only, no Run test)
```

Knowledge Base page retains **ReqIQ workspace** tab; program hub adds **structure** ReqIQ does not provide.

---

## 8. Related documents

- [Implementation-Plan.md](Implementation-Plan.md)
- [Document-Inventory.md](Document-Inventory.md)
- [Hermes QA Factory Agile Plan](../../Hermes_QA_Factory_Agile_Development_Plan.md)
- [Team handouts](../../handouts/README.md)
