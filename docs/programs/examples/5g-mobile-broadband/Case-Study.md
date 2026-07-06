# Example case study: 5G 流動寬頻

**Version:** 1.1 · **Date:** 2026-07-06  
**Type:** Example only — see [Program Framework](../../Program-Framework.md) for the generic model.

---

## Program summary

| Field | Value |
|-------|-------|
| Slug | `5g-mobile-broadband` |
| `test_scope` | `DT_ONLY` (MCS is reference, not automated) |
| Platform profile | `dt-telecom-default` |
| ReqIQ workspace | `cmp0zdx4g0004alp8z77ess7a` (Three-HK) |

---

## Layer mapping (this product)

### Platform (from profile)

WebApp, CRM, Billing, Matrixx, Provisioning, e-Coupon, MIS — see `_platform-profiles/dt-telecom-default.yaml`.

A **different product** might use only `{WEBAPP, API_GATEWAY}` or add custom components inline.

### Product features (this program)

| Feature ID | Platform components |
|------------|---------------------|
| `5GBB_PLANS` | WebApp, CRM, Matrixx, Billing |
| `5GBB_MIGRATION` | CRM, WebApp, e-Coupon, Provisioning |
| `5GBB_VAS` | CRM, Matrixx, Billing |
| `5GBB_ROUTER` | CRM, Billing, e-Coupon, WebApp, Provisioning |
| … | See manifest |

### Reference layer (not tested)

| Layer | Purpose |
|-------|---------|
| `REF_MCS_PLANS` | Plan codes 5Z1–5Z4 for CRM offer assertions |

### Extension (this program only)

`extensions.migration` — MCS→CRM user guide, phase-1 cohort, MMS rules. Other programs omit this block.

---

## Golden paths (illustrative)

1. WebApp new sale → CRM → Provisioning → Matrixx  
2. CRM renewal → e-Coupon → WebApp My Wallet → Provisioning MMS  
3. VAS subscribe → Matrixx rating → Billing invoice  

Orchestration suites are defined per program in manifest `journey_templates` — not global constants.

---

## Related

- [Document-Inventory.md](Document-Inventory.md)
- [Manifest schema](../../Manifest-Schema.md)
