# Agent / developer notes

## Product context

ReqIQ is a self-hosted web app for QA requirements, **local RAG** (no cloud LLM by default), **RQ‑IQ** outputs, and **Markdown/PDF** export. Canonical requirements: `docs/ReqIQ_Software_Requirements_Specification.md`.

## Hermes / agentic QA (integration narrative)

External **Hermes** multi-agent setups treat ReqIQ as the **requirements and retrieval hub** (ingest, lifecycle, RAG, suggested tests), while specialist profiles call this repo’s **HTTP API** and humans may use Telegram and separate test runners. See:

- `docs/architecture.html` — system layers, flows, and roles (reference UI; some labels describe an earlier stack sketch).
- `docs/Hermes_QA_MultiAgent_Profiles_v3.md` — profile names, prompts, and MCP HTTP tool URLs (aligned with OpenAPI).

**Ground truth for shipped contracts** is **`docs/openapi/reqiq-api-v1.yaml`** plus the SRS. Hermes tools should use: `rag/query` (response field **`content`**), **`GET …/readiness`** (compiled wiki when available per **`docs/Wiki-Compile-Strategy.md`**), requirements (with **`latestCompositeScore`**, **`isWikiSuggest`**), `sources/upload`, `embedding/reindex` (optional Hermes webhook), **`POST …/suggested-tests/generate`**, **`POST …/suggested-tests/import`**, **`POST …/requirements/suggest-from-wiki`** (wiki → DRAFT scenarios; **`feedbackApplied`** when profile exists). Wiki review learning (ReqIQ `/app` only): **`POST …/wiki-feedback`**, **`GET/PATCH/DELETE …/wiki-suggest-feedback`**, **`GET …/wiki-suggest-profile`**. Service accounts: `POST /api/v1/login` → Bearer JWT (no API keys). See **`docs/AI-Web-Test-Developer-Handoff.md`** v1.8.

**Sprint tracking:** **`docs/ReqIQ_Project_Management_and_Sprint_Plan.md`** v2.32 — **Sprint 8 complete** (`dd2e90e`); handoff **v2.1** (§5.1a full API proxy table for AI Web Test); next: **Sprint 9** hardening.

**Wiki / readiness (PO locked):** hybrid **Phase 1** (integrate now with readiness) + **Phase 2** (compile-once per project, Sprint 7.5). See **`docs/Wiki-Compile-Strategy.md`**. Early **`POST /compile`** sketch in **`docs/architecture.html`** is non-normative until OpenAPI adds it.

### AI Web Test (companion webapp)

Integration reference: **`docs/ReqIQ-API-Integration-Guide.md`** (AI Web Test’s FastAPI-style API: crawl-and-save, workflows, execution, feedback). **AI Web Test developer handoff:** **`docs/AI-Web-Test-Developer-Handoff.md`** (standard vs power-user API, proxy checklist).

**Current dev (same laptop as ReqIQ):** backend **`http://127.0.0.1:8000`**, frontend **`http://localhost:5173/`**. For **LAN / Hermes**, run Uvicorn with **`--host 0.0.0.0`** (not `127.0.0.1` only) and allow **TCP 8000** in Windows Firewall.

**Hermes on another PC (same Wi‑Fi):** reach this laptop by **LAN IP**, not loopback — e.g. AI Web Test API **`http://192.168.68.52:8000`** (confirm Windows firewall allows inbound **8000** from the LAN). ReqIQ from **Docker Compose** on this machine is typically **`http://192.168.68.52:3001`** (API) and **`http://192.168.68.52:8080`** (static web via nginx); if you run `npm run dev` instead, use whatever host/port Vite/Fastify print. **DHCP can change `.52`** — use a router reservation or DNS when you hard-code Hermes env.

**Production plan:** run **ReqIQ on a separate PC** from AI Web Test. When you split hosts:

- Use **hostnames or LAN IPs** in Hermes MCP tools and server-to-server calls — **`127.0.0.1` / `localhost` always means that machine only**, so ReqIQ on PC B cannot reach AI Web Test on PC A if URLs still say `127.0.0.1:8000`.
- Update **CORS** on AI Web Test (`BACKEND_CORS_ORIGINS` per the integration guide) to allow the **ReqIQ API and SPA origins** (and any Telegram webhook origins if applicable), not only local Vite.
- Any future **ReqIQ → AI Web Test** outbound integration should read the webapp base URL from **configuration** (env / tenant integration), not hard-coded localhost.

## Traceability

When implementing features, **tag PRs and commits** with `SRS:FR-…` or `SRS:NFR-…` per `CONTRIBUTING.md`. Sprint scaffolding may use `SRS:S0` or “infrastructure only”.

## Repo layout

| Path | Role |
| --- | --- |
| `apps/api` | Fastify HTTP API, `/live` `/ready`, structured logs |
| `apps/web` | React + Vite SPA |
| `docker-compose.yml` | Postgres, Qdrant, API, web |
| `docs/` | SRS, **`ReqIQ_Project_Management_and_Sprint_Plan.md`** (sprint status), **`AI-Web-Test-Developer-Handoff.md`**, **`Wiki-Compile-Strategy.md`**, Hermes profiles, **`ReqIQ-API-Integration-Guide.md`** |
| `docs/openapi/reqiq-api-v1.yaml` | **OpenAPI 3** contract for `/api/v1` + root health (import into Postman, codegen, agentic QA tools) |
| `docs/openapi/README.md` | **Integration guide** for external developers (auth, multipart, RAG, rate limits) |

## Commands

See root **README.md** for `npm install`, per-app `dev`, and `docker compose up`.
