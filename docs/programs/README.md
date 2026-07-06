# Product programs (AWT)

A **program** is a configurable vertical initiative (product line, service, or release train) that spans one or more **platform components** under test. AI Web Test owns the program shell (structure, journeys, factory); **ReqIQ** is a composable knowledge brick (sources, requirements, readiness, wiki) — no ReqIQ schema changes required.

**5G 流動寬頻 is one example**, not the product model. Different products may use different platform stacks, reference layers, and feature taxonomies.

## Framework (read first)

| Document | Purpose |
|----------|---------|
| [Program-Framework.md](Program-Framework.md) | Generic LEGO model — platform × product × reference |
| [Manifest-Schema.md](Manifest-Schema.md) | YAML contract for `backend/config/programs/*.yaml` |
| [Implementation-Plan.md](Implementation-Plan.md) | Platform work **PG-1 … PG-5** (slug-agnostic) |

## Examples

| Example | Description | Manifest |
|---------|-------------|----------|
| [5g-mobile-broadband](examples/5g-mobile-broadband/README.md) | DT telecom pilot; MCS reference-only | [`5g-mobile-broadband.yaml`](../../backend/config/programs/5g-mobile-broadband.yaml) |

Add new programs by copying an example manifest, adjusting `platform_profile` or `platform_components`, and adding docs under `docs/programs/examples/<slug>/`.

## Config layout

```
backend/config/programs/
  README.md
  _platform-profiles/     # optional shared platform brick libraries
    dt-telecom-default.yaml
  <program-slug>.yaml       # one file per program — discovered by loader
```

## Related platform docs

- [Hermes QA Factory Agile Plan](../Hermes_QA_Factory_Agile_Development_Plan.md) — factory loops, registry, MCP (**HF**)
- [Journey registry seed](../../backend/config/uat-journey-registry.yaml) — UAT URLs and `capability_keys`
- [AI Web Test Developer Handoff](../AI-Web-Test-Developer-Handoff.md) — ReqIQ proxy
- [Team handouts](../handouts/README.md)

**Program track code:** **PG** (generic), implemented on top of **HF** factory infrastructure.
