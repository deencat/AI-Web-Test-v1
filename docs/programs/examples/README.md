# Program examples

Illustrations of the [Program Framework](../Program-Framework.md). **Copy and adapt** — do not treat as exhaustive product list.

| Example | Slug | Notes |
|---------|------|-------|
| [5g-mobile-broadband](5g-mobile-broadband/README.md) | `5g-mobile-broadband` | DT telecom; profile `dt-telecom-default`; MCS reference layer |

## Adding an example

1. Add `backend/config/programs/<slug>.yaml`.
2. Add `docs/programs/examples/<slug>/README.md` (+ optional case study).
3. No application code changes required after PG-1 loader ships.

Future examples might include: postpaid browse-only (WebApp), B2B API-only (no CRM UI), or FMC with a reduced platform set.
