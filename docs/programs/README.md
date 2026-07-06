# Product programs (AWT)

A **program** is a long-lived product line. Under it, **initiatives** (offers, promotions, projects — same schema, different `kind` labels) capture timed launches and changes. AI Web Test owns structure, journeys, and factory; **ReqIQ** is a composable knowledge brick.

**5G 流動寬頻** is one **example** manifest, not the only shape.

## Framework (read first)

| Document | Purpose |
|----------|---------|
| [Program-Framework.md](Program-Framework.md) | Program → platform + reference + **initiatives** |
| [Manifest-Schema.md](Manifest-Schema.md) | YAML contract (`initiatives[]`, amendments, parity reference) |
| [Implementation-Plan.md](Implementation-Plan.md) | **PG-1 … PG-5** (slug-agnostic) |

## Key terms

| Term | Meaning |
|------|---------|
| **Program** | Product line umbrella (years) |
| **Initiative** | Timed offer, promotion, or project under a program |
| **Platform component** | System under test (WebApp, CRM, …) — stable per program |
| **Reference layer** | Read-only context (e.g. MCS docs for DT parity checks) — **not** an initiative |

## Examples

| Example | Manifest |
|---------|----------|
| [5g-mobile-broadband](examples/5g-mobile-broadband/README.md) | [`5g-mobile-broadband.yaml`](../../backend/config/programs/5g-mobile-broadband.yaml) |

## Config layout

```
backend/config/programs/
  <program-slug>.yaml
  _platform-profiles/
```

**Program track:** **PG** on top of **HF** factory infrastructure.
