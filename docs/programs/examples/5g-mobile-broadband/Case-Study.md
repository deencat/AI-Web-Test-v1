# Example case study: 5G 流動寬頻

**Version:** 1.2 · **Date:** 2026-07-06  
**Type:** Example — see [Program Framework](../../Program-Framework.md).

---

## Program vs initiatives

| Level | This example |
|-------|----------------|
| **Program** | `5g-mobile-broadband` — long-lived 5G mobile broadband line |
| **Initiatives** | Plans base offer, VAS, router promo, Tai Po promo, signup project, … |
| **Reference** | MCS plan tables + migration guide (parity only, not initiatives) |

Migration **waves** are **not** modeled as initiatives. The migration PDF sits in `reference_layers` for optional BAU MCS vs DT CRM parity checks.

---

## Initiative patterns illustrated

| Initiative | `relationship` | Notes |
|------------|------------------|-------|
| `5gbb-plans-base` | — | Base offer; open-ended `effective_to` |
| `5gbb-vas-datapack` | `stack` | Adds VAS on top of base plans |
| `taipo-free-3m` | `stack` | Time-limited promo (`effective_to` + `amendments` when needed) |

Production manifests may use **`replace`** when a new plan supersedes an old one.

---

## ABC / June marketing (generic pattern)

Not specific to this YAML — shows how **any** program would model:

```yaml
initiatives:
  - id: abc-base-20260530
    kind: base_offer
    title: "ABC plan"
    effective_from: "2026-05-30"
    effective_to: null
    capability_keys: [PLANS_ABC]
    ...

  - id: june-marketing-20260605
    kind: promotion
    title: "June marketing"
    effective_from: "2026-06-05"
    effective_to: "2026-06-30"
    relationship: stack          # or replace
    relates_to: [abc-base-20260530]
    amendments:
      - type: extend_end_date
        new_effective_to: "2026-07-15"
```

---

## Related

- [Document-Inventory.md](Document-Inventory.md)
- [Manifest schema](../../Manifest-Schema.md)
