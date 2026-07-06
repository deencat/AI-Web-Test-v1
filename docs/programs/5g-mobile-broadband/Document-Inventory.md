# 5G 流動寬頻 — Document inventory

**Version:** 1.0 · **Date:** 2026-07-06  
**Source folder:** `docs/5G 流動寬頻/` (14 files at export time)

Maps each asset to **ReqIQ capability**, **DT components to test**, and **reference-only** flag.

---

## Summary

| Category | Count | Test? |
|----------|-------|-------|
| Reference only (MCS plan tables) | 2 JPG groups | No |
| Hub screenshots | 3 JPG | Structure seed for Reference Hub |
| DT procedure PDFs | 9 PDF | Yes (via DT components) |

---

## File mapping

| File | Type | capability_key | reference_only | DT components | Notes |
|------|------|----------------|----------------|---------------|-------|
| `01-Main.JPG` | Hub screenshot | — | — | — | TOC seed for Reference Hub sections |
| `02.JPG`, `03.JPG` | Hub screenshots | — | — | — | Sub-section layout reference |
| `5Z1-5Z2-5Z3 – 5G流動寬頻月費計劃.JPG` | Plan table | `REF_MCS_PLANS` | **true** | — | Plan codes for CRM offer assertions |
| `5Z4 – 5G流動寬頻月費計劃.JPG` | Plan table | `REF_MCS_PLANS` | **true** | — | 5Z4 / 5CU plans |
| `現有5G寬頻月費計劃Migration安排新舊系統至CRM User Guide.pdf` | User guide | `5GBB_MIGRATION`, `DT_MIGRATION` | false | CRM, WebApp, e-Coupon, Provisioning | Phase 1: 5Z1–5Z3; MMS rule from 2026-06-30 |
| `5G寬頻7日冷靜期內申請取消合約流程跟進(CRM).pdf` | Procedure | `5GBB_COOLING_OFF` | false | CRM, Billing | Post-migration CRM path |
| `更新後台支援3網站5G寬頻服務上台處理.pdf` | Procedure | `5GBB_PLANS` | false | WebApp, CRM, Provisioning | DT new sale / signup |
| `推出「5G寬頻任用數據包」服務(VAS Contract)(DT Version).pdf` | Contract | `5GBB_VAS` | false | CRM, Matrixx, Billing | Explicitly DT Version |
| `推出3香港5G寬頻Router租借優惠.pdf` | Circular | `5GBB_ROUTER` | false | CRM, Billing, e-Coupon | Rental / rebate rules |
| `5G 寬頻之自助服務密碼-SUPREME App and My3 App.pdf` | Procedure | `5GBB_SELF_SERVICE` | false | WebApp | Password / app login |
| `5G寬頻客戶於My3 App綁定 - 領取易賞錢帳戶.pdf` | Procedure | `5GBB_SELF_SERVICE` | false | WebApp | MoneyBack binding |
| `為大埔受影響居民提供3個月免費5G寬頻服務.pdf` | Campaign | `5GBB_PROMO` | false | WebApp, CRM | Tai Po promo |
| `3香港推出 - 家居寬頻服務計劃.pdf` | Circular | `5GBB_FMC` | false | WebApp, CRM | Adjacent FMC product |

---

## Hub sections (from `01-Main.JPG`)

| Section | Product features | Primary DT components |
|---------|------------------|----------------------|
| MCS / BAU 月費計劃 | `REF_MCS_PLANS` | *(reference)* |
| 支援大埔 | `5GBB_PROMO` | WebApp, CRM |
| DT 月費計劃 | `5GBB_PLANS`, `5GBB_MIGRATION` | CRM, WebApp |
| 5G 寬頻 Router | `5GBB_ROUTER` | CRM, e-Coupon, WebApp, Billing |
| 裝置規格 / 使用方法 | `5GBB_PLANS` | WebApp, CRM |
| 增值服務 | `5GBB_VAS` | CRM, Matrixx, Billing |
| 客戶自助服務 | `5GBB_SELF_SERVICE` | WebApp |
| 其他 | Various | TBD — mark **gap** until sourced |

---

## Known gaps (intranet links not in folder)

Track in program manifest `hub_gaps`:

- Device guides (CPE Pro 3, ZTE MC888, OPPO, TCL, Huawei Mesh, …)
- Sub-plan detail pages (「詳情按此」 per plan code)
- CRM deep-link-only procedures without PDF export
- Matrixx / Billing / Provisioning / MIS **operator** URLs (typically not in ops PDF pack)

---

## ReqIQ upload order (recommended)

1. Migration User Guide (highest cross-cutting value)
2. DT Version VAS + CRM cooling-off + signup backend
3. Router, self-service, promo PDFs
4. FMC (if in scope for sprint)
5. Reference JPGs + optional `.md` plan-code companion for RAG

After each batch: **reindex** → verify **readiness** → add DRAFT requirements from wiki suggest.
