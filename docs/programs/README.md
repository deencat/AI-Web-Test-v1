# Product programs (AWT)

## User-facing UI (one place)

**Sidebar → Products & offers** (`/products`) is the **only** section users need.

Each **product** maps 1:1 to a ReqIQ workspace (see `backend/config/product-workspaces.yaml`), including the 5G Mobile Broadband pilot and related voucher / monthly-plan workspaces.

Per product: **Documents → Summary → Tests**, plus collapsible **Advanced (ReqIQ)** for readiness, RAG Q&A, coverage, full scenario editor, and IQ scoring.

**UX/UI flow images (PNG/JPG):** On **Update summary**, vision extracts **Purchase journeys** (numbered steps, branches, UI labels) into the wiki. **Create tests from summary** currently creates ReqIQ DRAFT UAT scenarios (hints from journeys when present).

**Quality path (planned):** Executable 3-tier tests must come from **AI Web Test** (journey planner → Crawl & Save → saved tests), not from ReqIQ `suggest-from-wiki` alone. ReqIQ remains the knowledge/requirements hub; IQ scoring is for human review only. See **[Quality-Test-Generation-Plan.md](Quality-Test-Generation-Plan.md)**.

`/knowledge-base` and `/programs` redirect to `/products`.

Config: `backend/config/product-workspaces.yaml`

---

## Internal docs (engineers / agent)

| Document | Purpose |
|----------|---------|
| **[User-Friendly-Implementation-Plan.md](User-Friendly-Implementation-Plan.md)** | UX flows and scenarios (UF-0…UF-6) |
| **[Quality-Test-Generation-Plan.md](Quality-Test-Generation-Plan.md)** | E2E quality follow-on — AWT factory vs ReqIQ drafts |
| [Program-Framework.md](Program-Framework.md) | Agent/YAML contract |
| [Manifest-Schema.md](Manifest-Schema.md) | YAML schema |

Agent manifests: `backend/config/programs/*.yaml`
