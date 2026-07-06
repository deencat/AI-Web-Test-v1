# Example: 5G 流動寬頻 — Document inventory

**Version:** 1.1 · **Date:** 2026-07-06  
**Program slug:** `5g-mobile-broadband`  
**Source folder:** `docs/5G 流動寬頻/` (14 files at export time)

Maps each asset to **ReqIQ capability**, **platform components**, and **reference** flag for **this example program only**.

---

## Summary

| Category | Count | Automate? |
|----------|-------|-----------|
| Reference layer (MCS plan tables) | 2 JPG groups | No (`automate: false`) |
| Hub screenshots | 3 JPG | Hub layout seed only |
| DT procedure PDFs | 9 PDF | Yes (via platform components) |

---

## File mapping

| File | Type | capability_key | automate | platform_components | Notes |
|------|------|----------------|----------|---------------------|-------|
| `01-Main.JPG` | Hub screenshot | — | — | — | TOC seed for Reference Hub |
| `02.JPG`, `03.JPG` | Hub screenshots | — | — | — | Sub-section layout |
| `5Z1-5Z2-5Z3 – 5G流動寬頻月費計劃.JPG` | Plan table | `REF_MCS_PLANS` | **false** | — | Plan codes for CRM assertions |
| `5Z4 – 5G流動寬頻月費計劃.JPG` | Plan table | `REF_MCS_PLANS` | **false** | — | 5Z4 / 5CU |
| `現有5G寬頻月費計劃Migration…User Guide.pdf` | User guide | `5GBB_MIGRATION` | true | CRM, WebApp, e-Coupon, Provisioning | See `extensions.migration` |
| `5G寬頻7日冷靜期…(CRM).pdf` | Procedure | `5GBB_COOLING_OFF` | true | CRM, Billing | |
| `更新後台…5G寬頻上台處理.pdf` | Procedure | `5GBB_SIGNUP` | true | WebApp, CRM, Provisioning | |
| `推出「5G寬頻任用數據包」…(DT Version).pdf` | Contract | `5GBB_VAS` | true | CRM, Matrixx, Billing | |
| `推出3香港5G寬頻Router租借優惠.pdf` | Circular | `5GBB_ROUTER` | true | CRM, Billing, e-Coupon | |
| `5G 寬頻之自助服務密碼…pdf` | Procedure | `5GBB_SELF_SERVICE` | true | WebApp | |
| `5G寬頻客戶於My3 App綁定…pdf` | Procedure | `5GBB_SELF_SERVICE` | true | WebApp | |
| `為大埔…免費5G寬頻服務.pdf` | Campaign | `5GBB_PROMO` | true | WebApp, CRM | |
| `3香港推出 - 家居寬頻服務計劃.pdf` | Circular | `5GBB_FMC` | true | WebApp, CRM | |

---

## ReqIQ upload order (this example)

1. Migration User Guide  
2. DT VAS + CRM cooling-off + signup  
3. Router, self-service, promo  
4. FMC (if in scope)  
5. Reference JPGs + optional `.md` companions  

After each batch: reindex → readiness → DRAFT requirements.
