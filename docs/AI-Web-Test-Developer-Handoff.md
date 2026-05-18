# AI Web Test — ReqIQ integration handoff

**Audience:** AI Web Test backend/frontend developers  
**Version:** 1.3 · **Date:** 2026-05-18  
**ReqIQ contract:** [`openapi/reqiq-api-v1.yaml`](openapi/reqiq-api-v1.yaml) · [`openapi/README.md`](openapi/README.md)  
**AI Web Test API (crawl, execute, KB):** [`ReqIQ-API-Integration-Guide.md`](ReqIQ-API-Integration-Guide.md) · **§12** ReqIQ proxy (partial — extend per below)

---

## 0. What changed in ReqIQ (give this section to your team)

| Change | ReqIQ API | AI Web Test action |
| --- | --- | --- |
| **Delete uploaded document** | `DELETE /api/v1/projects/{projectId}/sources/{sourceId}` → **204** | Add proxy + UI “Remove document” (see §5.4) |
| **Collaboration (comments)** | `GET/POST …/requirements/{id}/comments` | Optional v1.1 — review threads, `@email` mentions |
| **Trace links** | `GET/POST/DELETE …/requirements/{id}/trace-links` | Optional — link requirement ↔ test case / Jira / defect |
| **Multi-pass LLM IQ** | `POST …/revisions/{index}/llm-iq-multipass` | Optional / power-user — needs admin flag (§5.5) |
| **Docker uploads** | Upload dir `/var/lib/reqiq/uploads` in Compose | No proxy change — ensure `REQIQ_URL` hits a **running** API (`GET /live`) |
| **Sprint 7 live harness** | `npm run test:sprint7:live` in ReqIQ repo | Use to validate ReqIQ before blaming the proxy |
| **Compiled wiki (Sprint 7.5)** | `GET …/wiki`, `POST …/wiki/compile`, readiness **`wikiSource`** | **Implement §5.6** — proxy wiki + surface **Test context** from readiness |

**Validated (2026-05-17):** AI Web Test → ReqIQ `POST …/rag/query` returns **200** when ReqIQ is up. **502** from your API usually means ReqIQ is down or wrong base URL (see §4, §9).

**Wiki strategy (PO locked):** [Wiki-Compile-Strategy.md](Wiki-Compile-Strategy.md). **ReqIQ Sprint 7.5 is shipped:** after upload + **reindex**, ReqIQ auto-compiles a **persisted wiki** per workspace. **`GET …/readiness`** returns stable **`wikiContent`** when `wikiSource: "compiled"`. AI Web Test **must** proxy readiness (already in §5.1) and **should** add **`GET …/wiki`** (and optionally compile) per §5.6.

---

## 1. Product split

| Tier | Primary UI | Who | Capabilities |
| --- | --- | --- | --- |
| **Standard users** | **AI Web Test** (`:5173` UI, `:8000` API) | QA, BAs, most testers | Workspaces, documents, **requirements**, **IQ**, **readiness + Test context (wiki)**, suggested tests, **test execution** |
| **Power users** | **ReqIQ** (`:8080/app`) | RAG engineers, index admins | **RAG** playground, **chunks**, reindex/snapshots/rollback, **Compiled wiki** recompile, admin scorecard, **Collab** |

**Rule:** Most users never open ReqIQ directly. AI Web Test **backend** proxies ReqIQ using a service account (or forwards the user JWT). **Do not** expose `REQIQ_SERVICE_TOKEN` to the browser.

**Canonical requirement documents** live in ReqIQ (`sources/upload`), not only AI Web Test’s native `/api/v1/kb/*` (see integration guide §2 vs §12).

---

## 2. Documents to read (order)

1. **This file** — scope, proxy checklist, MVP flows, deliverables.
2. [`openapi/reqiq-api-v1.yaml`](openapi/reqiq-api-v1.yaml) — machine-readable ReqIQ contract. **Includes wiki (§5.6), readiness `wikiSource`/`wikiStale`, DELETE source, comments, trace-links.**
3. [`openapi/README.md`](openapi/README.md) — login, multipart upload, rate limits.
4. [`ReqIQ-API-Integration-Guide.md`](ReqIQ-API-Integration-Guide.md) — AI Web Test endpoints (§1–11) + existing §12 proxies.

Optional (agents only, not main UI): [`Hermes_QA_MultiAgent_Profiles_v3.md`](Hermes_QA_MultiAgent_Profiles_v3.md).

---

## 3. Architecture

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│  AI Web Test UI  :5173      │  HTTPS  │  AI Web Test API  :8000     │
│  (standard users)           │ ──────► │  • crawl / execute / tests  │
└─────────────────────────────┘         │  • ReqIQ proxy  /api/v1/    │
                                        │    requirements/...       │
                                        └──────────────┬────────────┘
                                                       │ server-side
                                                       ▼
                                        ┌─────────────────────────────┐
                                        │  ReqIQ API  :3001           │
                                        │  projects · sources · reqs  │
                                        │  IQ · wiki · readiness      │
                                        └─────────────────────────────┘

Power users ──► ReqIQ SPA  :8080/app  (RAG · chunks · embedding admin)
```

| System | Dev URL | Role |
| --- | --- | --- |
| ReqIQ API | `http://localhost:3001` | Requirements hub |
| ReqIQ web | `http://localhost:8080/app` | Power-user UI |
| AI Web Test API | `http://localhost:8000` | Primary API + proxy |
| AI Web Test UI | `http://localhost:5173` | Primary UI |

**Production:** use **LAN IP or DNS** per host (`127.0.0.1` is local to that machine only). Update AI Web Test `BACKEND_CORS_ORIGINS` for both UIs.

**If AI Web Test runs in Docker** while ReqIQ runs on the host: use `http://host.docker.internal:3001`, not `http://127.0.0.1:3001`.

---

## 4. Server configuration (AI Web Test `.env`)

```bash
# ReqIQ backend (server-side only)
REQIQ_URL=http://localhost:3001
REQIQ_SERVICE_EMAIL=aiwebtest@reqiq.local
REQIQ_SERVICE_PASSWORD=...
# Or cache JWT from POST /api/v1/login (refresh on 401, TTL ~8h):
# REQIQ_SERVICE_TOKEN=eyJhbGci...
# Optional link for "Advanced" button:
REQIQ_WEB_URL=http://localhost:8080
```

1. Create a ReqIQ user with role **LIBRARIAN**, **ANALYST**, or **ADMIN** (not **AUDITOR** for mutations).
2. `POST {REQIQ_URL}/api/v1/login` with `{ "email", "password" }` → use **`accessToken`** as `Authorization: Bearer …`.
3. Resolve **`projectId`** from `GET /api/v1/projects` → field **`id`** (cuid), not display name.

**Health check before proxying:** `GET {REQIQ_URL}/live` → `{"status":"ok"}`. If this fails, all proxied routes will **502**.

After document upload, call ReqIQ `POST …/embedding/reindex` **in the background** (server-side from your API is fine). ReqIQ then **auto-compiles the project wiki** when vectors are upserted. Standard users see document **`status`** and **Test context** via readiness (§5.6) — they do not need to know about “RAG” or “reindex”.

---

## 5. Standard-user API — proxy from AI Web Test

Implement **backend** routes (suggested prefix `/api/v1/requirements/…`, matching integration guide §12 style). Each proxies to ReqIQ with the service Bearer token. Forward status codes and JSON error bodies where practical.

### 5.1 Core proxy table (MVP + documents)

| AI Web Test (proposed) | ReqIQ | Purpose |
| --- | --- | --- |
| `GET /api/v1/requirements/projects` | `GET /api/v1/projects` | List workspaces |
| `POST /api/v1/requirements/projects` | `POST /api/v1/projects` | Create workspace `{ "name" }` |
| `PATCH /api/v1/requirements/projects/{id}` | `PATCH /api/v1/projects/{id}` | Rename workspace |
| `GET /api/v1/requirements/projects/{id}` | `GET /api/v1/projects/{id}` | Get one workspace |
| `GET …/requirements/{projectId}/requirements` | `GET …/requirements` | List requirements (`latestCompositeScore`) |
| `POST …/requirements` | `POST …/requirements` | Create `{ "title", "body" }` |
| `GET/PATCH …/requirements/{requirementId}` | `GET/PATCH …/requirements/{id}` | Get / update |
| `POST …/requirements/{id}/transition` | `POST …/transition` | Lifecycle (DRAFT → REVIEWED → BASELINE, etc.) |
| `GET …/requirements/{id}/audit` | `GET …/audit` | Audit trail |
| `GET …/requirements/{id}/revisions` | `GET …/revisions` | Revision list |
| `GET …/revisions/{revisionIndex}` | `GET …/revisions/{index}` | Revision detail |
| `POST …/revisions/{index}/stub-iq` | `POST …/stub-iq` | Stub IQ (no LLM) |
| `POST …/revisions/{index}/llm-iq` | `POST …/llm-iq` | LLM IQ (**503** `llm_not_configured` if chat off) |
| `GET …/requirements/{id}/latest-iq` | `GET …/latest-iq` | Latest IQ on requirement |
| `GET …/requirements/{projectId}/readiness?query=…` | `GET …/readiness` | **Required** — gate + **`wikiContent`** + `wikiSource`, `wikiStale` (§5.6) |
| **`GET …/requirements/{projectId}/wiki`** | **`GET …/wiki`** | **Recommended** — read compiled wiki without readiness query |
| **`POST …/requirements/{projectId}/wiki/compile?feature=…`** | **`POST …/wiki/compile`** | **Optional** — manual recompile (LIBRARIAN+); usually automatic after reindex |
| `POST …/requirements/{projectId}/sources/upload` | `POST …/sources/upload` | Multipart upload (DOCX, PDF, MD, TXT, PPTX, PNG) |
| `POST …/requirements/{projectId}/sources/upload-zip` | `POST …/sources/upload-zip` | Single ZIP batch (optional) |
| `GET …/requirements/{projectId}/sources` | `GET …/sources` | List documents (`status`, `_count.chunks`) |
| **`DELETE …/requirements/{projectId}/sources/{sourceId}`** | **`DELETE …/sources/{sourceId}`** | **Remove document (§5.4)** |
| `POST …/requirements/{projectId}/query` | `POST …/rag/query` | RAG Q&A *(optional — prefer readiness for gate)* |
| `POST …/…/suggest-tests` | `POST …/suggested-tests/generate` | LLM suggested tests |
| `GET/POST/PATCH/DELETE …/suggested-tests` | same under `…/suggested-tests` | Suggested test CRUD |
| `POST …/suggested-tests/import` | `POST …/import` | Import without LLM |

**Bodyless POSTs:** do not send `Content-Type: application/json` without a body (Fastify returns `FST_ERR_CTP_EMPTY_JSON_BODY`).

**Multipart upload:** forward `multipart/form-data` file part(s) to ReqIQ; do not JSON-wrap files.

### 5.2 Collaboration (optional v1.1 — review loops)

| AI Web Test (proposed) | ReqIQ | Purpose |
| --- | --- | --- |
| `GET …/requirements/{id}/comments` | `GET …/comments` | List comments |
| `POST …/requirements/{id}/comments` | `POST …/comments` | Body `{ "body": "… @user@example.com …" }` → **201**; `mentionEmails` parsed |
| `GET …/requirements/{id}/trace-links` | `GET …/trace-links` | List links to tests, defects, Jira, etc. |
| `POST …/requirements/{id}/trace-links` | `POST …/trace-links` | `{ "kind": "TEST"\|"DEFECT"\|"COMMIT"\|"JIRA"\|"OTHER", "externalId", "label?", "url?" }` → **201** |
| `DELETE …/trace-links/{linkId}` | `DELETE …/trace-links/{linkId}` | **204** |

**AUDITOR** role: read-only on ReqIQ — no POST/PATCH/DELETE.

### 5.3 Power-user only — do **not** expose in standard UI

| ReqIQ path | Notes |
| --- | --- |
| `POST …/rag/query`, `…/rag/retrieve`, `…/rag/threads` | RAG playground |
| `GET/PATCH …/chunks`, `…/chunks/{chunkId}` | Chunk metadata |
| `POST …/embedding/reindex`, `snapshot`, `rollback-hard` | Index ops (server may call reindex silently after upload) |
| `POST …/revisions/{index}/llm-iq-multipass` | Multi-sample IQ consensus (§5.5) |
| `/api/v1/admin/*` | Tenant admin, IQ weights, integration toggles |

Link: **“Open ReqIQ advanced”** → `{REQIQ_WEB_URL}/app` (e.g. `http://localhost:8080/app`).

### 5.4 Document delete — behavior (important for UX)

When the user removes a document, proxy:

```http
DELETE /api/v1/projects/{projectId}/sources/{sourceId}
Authorization: Bearer <token>
```

| ReqIQ response | Meaning |
| --- | --- |
| **204** | Deleted: file on disk, all DB chunks, Qdrant vectors for that `sourceId` |
| **404** `not_found` | Unknown `sourceId` or wrong project |
| **403** `forbidden` | AUDITOR or no mutate role |
| **500** `delete_source_failed` | Often Qdrant unreachable — show retry |

**Does not happen automatically:**

- No full-project **reindex**
- No re-chunking of other files

**Other documents stay indexed.** RAG/readiness should stop citing the deleted file immediately. Optional: call `POST …/embedding/reindex` only after bulk deletes or if your team wants a full refresh.

**UI copy suggestion:** “Remove document” with confirm: *This deletes the file and its search index entries. Other documents are not affected.*

### 5.5 Multi-pass LLM IQ (optional / advanced)

```http
POST /api/v1/projects/{projectId}/requirements/{requirementId}/revisions/{revisionIndex}/llm-iq-multipass
```

| Response | Meaning |
| --- | --- |
| **200** | `iqSnapshot.multiPass`, `consensusCompositeScore`, `sampleCount` |
| **403** `multipass_disabled` | Tenant admin must set `iqMultiPassCritiqueEnabled: true` via `PATCH /api/v1/admin/integration-config` |
| **503** `llm_not_configured` | Chat LLM not configured on ReqIQ |

Not required for standard AI Web Test MVP unless product asks for “consensus IQ” on revisions.

### 5.6 Compiled wiki — Test context (Sprint 7.5) **← implement for AI Web Test**

ReqIQ now stores a **compile-once Markdown wiki** per project (workspace). This is the artifact test generation should use — not ad hoc `POST …/rag/query` answers.

**Product rules**

| Rule | Detail |
| --- | --- |
| **Primary path for standard UI** | `GET …/readiness?query=…` — use returned **`wikiContent`** as **Test context** for crawl / suggest-tests |
| **Stable wiki** | When `wikiSource === "compiled"`, repeated readiness calls return the **same** `wikiContent` (until reindex recompiles) |
| **Provisional fallback** | When `wikiSource === "rag"`, show a non-blocking banner: *Test context is provisional — upload documents and wait for indexing* |
| **Stale wiki** | When `wikiStale === true`, show warning: *Documents or index changed — refresh Test context* (do **not** block `ready` unless product asks) |
| **Do not expose** | `POST …/rag/query` in standard UI (power users use ReqIQ `/app`) |
| **Recompile** | Optional in AI Web Test; default is ReqIQ auto-compile after reindex. Power users can use ReqIQ **Compiled wiki** panel |

#### Proxy: `GET …/wiki`

```http
GET /api/v1/projects/{projectId}/wiki
Authorization: Bearer <token>
```

**AI Web Test (proposed):** `GET /api/v1/requirements/projects/{projectId}/wiki`

| Status | Body |
| --- | --- |
| **200** | See JSON below |
| **404** `wiki_not_compiled` | No compile yet — prompt user to upload + index, or call compile |
| **404** `not_found` | Bad `projectId` |

**Response 200 (example):**

```json
{
  "projectId": "cmp0zdx4g0004alp8z77ess7a",
  "embeddingIndexVersion": 3,
  "featureHint": null,
  "markdown": "# My Project — Compiled wiki\n\n## Overview\n…",
  "citationCount": 8,
  "compileStatus": "ok",
  "compiledAt": "2026-05-18T10:00:00.000Z",
  "wikiStale": false
}
```

| Field | Use in AI Web Test |
| --- | --- |
| `markdown` | Display as **Test context**; pass to test-gen / crawl `user_instruction` |
| `compileStatus` | `ok` \| `no_sources` \| `failed` — show status chip |
| `wikiStale` | Show refresh banner when true |
| `embeddingIndexVersion` | Debug only / optional “Index vN” label |
| `citationCount` | Optional “Based on N source excerpts” |

#### Proxy: `POST …/wiki/compile` (optional)

```http
POST /api/v1/projects/{projectId}/wiki/compile?feature=5G%20Voucher%20Plan
Authorization: Bearer <token>
```

**No request body.** Bodyless POST — do not send `Content-Type: application/json` with an empty body.

**AI Web Test (proposed):** `POST /api/v1/requirements/projects/{projectId}/wiki/compile?feature=…`

| Status | Meaning |
| --- | --- |
| **200** | Same shape as `GET …/wiki` |
| **400** `no_sources` | No embedded chunks — `{ "error": "no_sources", "message": "…" }` |
| **403** `forbidden` | AUDITOR or read-only role |
| **502** `wiki_compile_failed` | LLM/retrieval error — show retry |

**When to call:** “Refresh Test context” button after bulk upload/delete, or when `wikiStale` is true. Otherwise rely on ReqIQ auto-compile after your backend triggers `POST …/embedding/reindex`.

#### Readiness — updated fields (required proxy passthrough)

```http
GET /api/v1/projects/{projectId}/readiness?query={naturalLanguage}&feature={optional}
Authorization: Bearer <token>
```

**Response 200 (excerpt — new fields in bold):**

```json
{
  "projectId": "cmp0zdx4g0004alp8z77ess7a",
  "query": "5G voucher purchase flow",
  "readinessScore": 87,
  "status": "ready",
  "threshold": 60,
  "missing": [],
  "wikiContent": "# My Project — Compiled wiki\n\n…",
  "wikiSource": "compiled",
  "wikiCompiledAt": "2026-05-18T10:00:00.000Z",
  "wikiEmbeddingIndexVersion": 3,
  "wikiStale": false,
  "matchedRequirement": { "id": "…", "title": "…", "state": "BASELINE", "latestCompositeScore": 87 },
  "rag": { "content": "…", "citationCount": 8, "skippedLlm": false, "abstained": false }
}
```

| Field | AI Web Test behavior |
| --- | --- |
| `wikiContent` | **Test context** — primary payload for downstream test generation |
| `wikiSource` | `compiled` = stable; `rag` = provisional banner; `none` = empty |
| `wikiStale` | Warning banner; suggest “Refresh Test context” |
| `wikiCompiledAt` | “Last compiled” timestamp in UI |
| `status` | `ready` \| `insufficient` \| `no_sources` \| `error` — map to **Ready for testing?** |
| `readinessScore` | Show 0–100; default gate **≥ 60** (unchanged) |
| `missing[]` | Bullet list under readiness (may include stale/provisional hints) |

**Implementation checklist (copy to your sprint)**

1. [ ] Proxy **`GET …/readiness`** — forward all fields above (do not strip `wikiSource` / `wikiStale`).
2. [ ] **Readiness UI** — feature/scenario query, score, status, expandable **Test context** (`wikiContent` markdown render).
3. [ ] Proxy **`GET …/wiki`** — load Test context on workspace open without a readiness query.
4. [ ] After upload (and optional background reindex), poll **`GET …/wiki`** or re-call readiness until `wikiSource === "compiled"` or timeout.
5. [ ] Map `wikiStale` / `wikiSource === "rag"` to user-visible banners (§6).
6. [ ] *(Optional)* Proxy **`POST …/wiki/compile`** + “Refresh Test context” for LIBRARIAN+ roles.
7. [ ] Pass **`wikiContent`** (not raw RAG `content`) into **suggest-tests** / **crawl-and-save** `user_instruction` per [ReqIQ-API-Integration-Guide.md](ReqIQ-API-Integration-Guide.md) §12.8.
8. [ ] Validate with ReqIQ `npm run test:sprint7_5:live` against your `REQIQ_URL` before shipping proxy.

**ReqIQ verification (direct, no proxy):**

```powershell
$env:REQIQ_API_BASE = "http://localhost:3001"
$env:REQIQ_ACCESS_TOKEN = "<from login>"
$env:REQIQ_PROJECT_ID = "<cuid>"
npm run test:sprint7_5:live
```

---

## 6. User-facing labels (standard UI)

| ReqIQ concept | Show as |
| --- | --- |
| Project | **Workspace** |
| Source | **Document** |
| Requirement | **Requirement** |
| `latestCompositeScore` | **Quality score** |
| `readinessScore` / `status` | **Ready for testing?** |
| `wikiContent` | **Test context** — Markdown wiki for test generation |
| `wikiSource` | *(internal)* `compiled` = stable; `rag` = show “provisional” banner |
| `wikiStale` | **Test context may be outdated** — offer refresh |
| `compileStatus` | **Wiki status** — Ready / No sources / Failed (if you proxy `GET …/wiki`) |
| `Source.status` | **Processing** / **Ready** / **Failed** (map `PARSED` → Ready, `FAILED` → Failed) |
| Comment / trace link | **Review note** / **Linked item** (if you ship §5.2) |
| RAG / chunk / reindex | *(hidden — advanced link only)* |

---

## 7. MVP build order

1. **Login** — AI Web Test auth; proxy ReqIQ when needed; handle **401** (re-login ReqIQ token).
2. **Workspaces** — list, create, rename; persist selected `projectId`.
3. **Documents** — multipart upload, list with status; **delete** with confirm (§5.4).
4. **Requirements** — list (with score), create, edit, optional transition.
5. **IQ** — run stub/LLM IQ on revisions; show `latest-iq` on list.
6. **Readiness + Test context** — proxy `GET …/readiness`; show score, status, **`wikiContent`**; handle `wikiSource` / `wikiStale` (§5.6).
7. **Compiled wiki (recommended)** — proxy `GET …/wiki`; load Test context on workspace detail; optional `POST …/compile` for refresh.
8. **Suggested tests** — generate using **`wikiContent`** from readiness/wiki as context → **crawl-and-save-test** (integration guide §3).
9. **Execute** — existing AI Web Test flows (§3–8); label `triggered_by: "AI Web Test"`.
10. **Advanced link** — ReqIQ `/app` for power users (RAG, manual recompile).
11. *(Optional)* **Comments / trace links** (§5.2).

---

## 8. End-to-end flow (reference)

```mermaid
sequenceDiagram
  participant U as User
  participant UI as AI Web Test UI
  participant A as AI Web Test API
  participant R as ReqIQ API

  U->>UI: Login
  UI->>A: auth
  U->>UI: Create workspace
  A->>R: POST /api/v1/projects
  U->>UI: Upload documents
  A->>R: POST …/sources/upload
  Note over A,R: Background …/embedding/reindex → auto wiki/compile
  U->>UI: Remove wrong document
  A->>R: DELETE …/sources/{sourceId}
  U->>UI: Create requirement + Run IQ
  A->>R: POST/PATCH requirements, POST …/llm-iq
  U->>UI: Check readiness / Test context
  A->>R: GET …/readiness
  Note over A,R: wikiContent stable when wikiSource=compiled
  opt View wiki without query
    A->>R: GET …/wiki
  end
  U->>UI: Generate & run test
  A->>A: crawl-and-save-test, execute
```

---

## 9. Verification

### ReqIQ is up (do this first)

```powershell
curl.exe http://localhost:3001/live
# Expect: {"status":"ok"}
```

If **502** from AI Web Test: check `REQIQ_URL`, Docker (`docker compose ps`), and that the API container is not exited.

### ReqIQ repo smoke tests

```powershell
$env:REQIQ_API_BASE = "http://localhost:3001"
$env:REQIQ_ACCESS_TOKEN = "<from POST /api/v1/login>"
$env:REQIQ_PROJECT_ID = "<cuid from GET /api/v1/projects>"
npm run test:sprint6:live
npm run test:sprint7:live   # comments, trace-links, optional multipass (ADMIN token)
npm run test:sprint7_5:live # compiled wiki + readiness artifact (Sprint 7.5)
```

Your proxy should support the same **standard** operations your UI uses. Import [`reqiq-api-v1.yaml`](openapi/reqiq-api-v1.yaml) into Postman; set server URL and Bearer token from login.

**Key response fields:**

- RAG answer text (power-user only): **`content`** (not `answer`)
- Readiness / Test context: **`readinessScore`**, **`status`**, **`wikiContent`**, **`wikiSource`**, **`wikiStale`**
- Compiled wiki: **`markdown`**, **`compileStatus`**, **`wikiStale`** on `GET …/wiki`
- Login: **`accessToken`** (JWT, three dot-separated segments)
- Source list: **`id`**, **`originalFilename`**, **`status`**, **`_count.chunks`**
- Delete source: **204** empty body

**Manual delete test (Postman / curl):**

```http
DELETE http://localhost:3001/api/v1/projects/{projectId}/sources/{sourceId}
Authorization: Bearer <accessToken>
```

---

## 10. Deliverables back to ReqIQ team

1. **OpenAPI or markdown** listing all **new/updated** proxy routes (extends integration guide §12) — include **`GET/POST …/wiki`**, readiness fields, **DELETE source**.
2. **Demo or screenshots:** workspace → upload → (index) → **Test context / readiness** → requirement → IQ → test run.
3. **`.env.example`** entries for `REQIQ_URL`, `REQIQ_SERVICE_*`, optional `REQIQ_WEB_URL`.
4. **Short note:** what is proxied vs what still requires ReqIQ `/app`.
5. **Troubleshooting note:** how you detect ReqIQ down vs ReqIQ 4xx (avoid masking as generic 502).

---

## 11. Out of scope for v1

- Hermes / Telegram / MCP tool wiring (separate track; see Hermes profiles doc).
- Chunk editor, RAG thread UI, embedding rollback UI in AI Web Test (reindex may run server-side; wiki refresh via readiness/`GET …/wiki`).
- ReqIQ admin scorecard UI (stay in ReqIQ admin).
- Multi-pass IQ unless explicitly requested (§5.5).

---

## 12. One-line summary

> Build AI Web Test as the primary QA app: **proxy ReqIQ** (projects, documents, requirements, IQ, **readiness + compiled wiki / Test context** per §5.6) from your **backend**; pass **`wikiContent`** into test generation; hide RAG/chunks/reindex from normal users; link **ReqIQ advanced** at `:8080/app`; use **`reqiq-api-v1.yaml`** and extend **integration guide §12** until §5.1 + §5.6 are implemented.
