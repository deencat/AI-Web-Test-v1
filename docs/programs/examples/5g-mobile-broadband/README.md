# Example: 5G 流動寬頻

**Manifest:** [`backend/config/programs/5g-mobile-broadband.yaml`](../../../backend/config/programs/5g-mobile-broadband.yaml)  
**Kind:** `example` — illustrates the [Program Framework](../../Program-Framework.md) for a DT telecom product.  
**Not** the only supported program shape.

## Documents

| Document | Purpose |
|----------|---------|
| [Case-Study.md](Case-Study.md) | How this product maps to platform × features × reference |
| [Document-Inventory.md](Document-Inventory.md) | Local PDF/JPG assets → capabilities |
| [Pilot-Checklist.md](Pilot-Checklist.md) | UF-6 pilot checks + quality path |
| [Quality-Test-Generation-Plan.md](../../Quality-Test-Generation-Plan.md) | Why ReqIQ drafts ≠ E2E browser tests; AWT factory plan |

## Why this example

- Uses **`platform_profile: dt-telecom-default`**.
- **`initiatives[]`** for plans, VAS, promos, projects (timed commercial work).
- **`reference_layers`** for MCS plans + migration guide (parity only — not initiatives).
- Another product would use different initiatives, or fewer platform components.

## Validate framework

When PG-1 ships: `/programs/5g-mobile-broadband` shows initiative timeline; no product-specific code paths.
