# Product programs (AWT)

## User-facing UI (one place)

**Sidebar → Products & offers** (`/products`) is the **only** section users need.

Each **product** maps 1:1 to a ReqIQ workspace:

| Product (UI) | ReqIQ workspace |
|--------------|-----------------|
| Voucher Plan (DNS / 5GBB bundle) | `Voucher Plan` |
| 5G Voucher Monthly Plan | `5G Voucher Monthly Plan` |

Per product: **Documents → Summary → Tests**, plus collapsible **Advanced (ReqIQ)** for readiness, RAG Q&A, coverage, full scenario editor, and IQ scoring.

**UX/UI flow images (PNG/JPG):** On **Update summary**, vision extracts **Purchase journeys** (numbered steps, branches, UI labels) into the wiki. **Create tests from summary** uses those steps to guide scenario generation.

`/knowledge-base` and `/programs` redirect to `/products`.

Config: `backend/config/product-workspaces.yaml`

---

## Internal docs (engineers / agent)

| Document | Purpose |
|----------|---------|
| **[User-Friendly-Implementation-Plan.md](User-Friendly-Implementation-Plan.md)** | UX flows and scenarios |
| [Program-Framework.md](Program-Framework.md) | Agent/YAML contract |
| [Manifest-Schema.md](Manifest-Schema.md) | YAML schema |

Agent manifests: `backend/config/programs/*.yaml`
