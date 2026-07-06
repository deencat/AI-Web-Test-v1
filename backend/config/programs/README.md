# Program manifests

YAML files in this directory define **product programs** for AI Web Test. The application loads them dynamically — **do not hard-code product names or bricks in code**.

## Layout

```
programs/
  README.md                 # this file
  <program-slug>.yaml       # one program per file (slug = filename stem)
  _platform-profiles/       # optional shared platform component libraries
    dt-telecom-default.yaml
```

## Add a program

1. Create `<slug>.yaml` following [Manifest-Schema.md](../../docs/programs/Manifest-Schema.md).
2. Optionally set `platform_profile: dt-telecom-default` or define custom `platform_components`.
3. Add optional docs under `docs/programs/examples/<slug>/`.
4. Implement PG-1 loader (see [Implementation-Plan.md](../../docs/programs/Implementation-Plan.md)).

## Files

| File | Purpose |
|------|---------|
| `5g-mobile-broadband.yaml` | **Example** — 5G 流動寬頻 DT pilot |
| `_platform-profiles/dt-telecom-default.yaml` | Reusable DT telecom platform bricks |

## Excluded from discovery

- `_platform-profiles/` (included only via `platform_profile`)
- Files starting with `_` (except profiles folder)
