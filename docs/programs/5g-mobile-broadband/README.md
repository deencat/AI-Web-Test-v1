# 5G 流動寬頻 — Program hub

**Program slug:** `5g-mobile-broadband`  
**Test scope:** **DT platform only** (MCS/BAU is reference-only)  
**Status:** Planning documented · Implementation **not started** (see [Implementation-Plan.md](Implementation-Plan.md))

## Documents

| Document | Purpose |
|----------|---------|
| [Architecture.md](Architecture.md) | DT platform LEGO model, ReqIQ role, migration context |
| [Implementation-Plan.md](Implementation-Plan.md) | Phased stories (**PG-5G-1 … PG-5G-5**), acceptance criteria |
| [Document-Inventory.md](Document-Inventory.md) | Maps `docs/5G 流動寬頻/` assets → DT components & ReqIQ keys |

## Config

- Program manifest: [`backend/config/programs/5g-mobile-broadband.yaml`](../../../backend/config/programs/5g-mobile-broadband.yaml)
- Journey registry (shared): [`backend/config/uat-journey-registry.yaml`](../../../backend/config/uat-journey-registry.yaml)

## Source materials

Operational PDFs and plan-table screenshots live in:

`docs/5G 流動寬頻/`

That folder is a **partial export** of the internal ops portal. The Reference Hub (when built) will mark **gaps** for links visible on the intranet but not yet in the repo.

## Quick rules

1. **Do not** automate or regression-test MCS/BAU systems.
2. **Do** test WebApp, CRM, Billing, Matrixx, Provisioning, e-Coupon, and MIS on DT.
3. **Do** ingest MCS plan tables into ReqIQ as **reference** (`REF_MCS_PLANS`) for CRM offer validation (e.g. plan code 5Z1).
4. Tag every journey with `dt_components[]` and `capability_keys[]` in registry `extra_config`.
