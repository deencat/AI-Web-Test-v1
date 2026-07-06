# Example: 5G 流動寬頻

**Manifest:** [`backend/config/programs/5g-mobile-broadband.yaml`](../../../backend/config/programs/5g-mobile-broadband.yaml)  
**Kind:** `example` — illustrates the [Program Framework](../../Program-Framework.md) for a DT telecom product.  
**Not** the only supported program shape.

## Documents

| Document | Purpose |
|----------|---------|
| [Case-Study.md](Case-Study.md) | How this product maps to platform × features × reference |
| [Document-Inventory.md](Document-Inventory.md) | Local PDF/JPG assets → capabilities |

## Why this example

- Uses shared profile **`dt-telecom-default`** (WebApp, CRM, Billing, Matrixx, …).
- **`reference_layers`** for MCS plan tables (`automate: false`).
- **`extensions.migration`** for MCS→CRM transition context (DT testing only).
- Another product (e.g. postpaid-only, FMC-only, B2B API) would use different `product_features` and may omit `extensions` or use a different `platform_profile`.

## Source materials

`docs/5G 流動寬頻/` — partial ops portal export (not in git by default).

## Validate framework

When PG-1 is implemented, this slug should load at `/programs/5g-mobile-broadband` with no 5G-specific UI code.
