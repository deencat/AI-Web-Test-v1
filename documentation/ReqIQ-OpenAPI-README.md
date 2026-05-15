# ReqIQ API specification (for external integrations)

Hand this folder to **Agentic QA**, **test automation**, or any service that must drive ReqIQ over HTTP.

## Deliverables

| File | Purpose |
| --- | --- |
| **`reqiq-api-v1.yaml`** | **OpenAPI 3.0.3** machine-readable contract. Import into Postman, Insomnia, Bruno, ReadyAPI, Swagger UI, or codegen (`openapi-generator-cli`). |
| **This README** | Human integration notes that OpenAPI does not spell out (auth sequence, uploads, limits). |

## Quick integration sequence

1. **Resolve base URL** — e.g. `https://<your-reqiq-host>:3001` or the same host as your SPA with path `/api/v1` behind a reverse proxy.
2. **Authenticate** — `POST {base}/api/v1/login` with JSON `{"email":"...","password":"..."}`.
3. **Read `accessToken`** from the JSON body — use as **Bearer** JWT for all secured routes:  
   `Authorization: Bearer <accessToken>`
4. **Create or choose a project** — `GET /api/v1/projects` or `POST /api/v1/projects` with `{"name":"..."}` (mutating roles only).
5. **Upload documents** — `POST /api/v1/projects/{projectId}/sources/upload` as `multipart/form-data` with one or more **file** parts (see YAML + below).
6. **Index for RAG** — `POST /api/v1/projects/{projectId}/embedding/reindex` (mutating role; requires embeddings + Qdrant configured on the server).
7. **Query** — `POST /api/v1/projects/{projectId}/rag/query` with JSON body (`query`, optional `limit`, `threadId`, etc.) per **`reqiq-api-v1.yaml`**.

## Health checks (no JWT)

| Method | Path | Use |
| --- | --- | --- |
| GET | `/live` | Liveness |
| GET | `/ready` | Readiness (Postgres); **503** if DB unavailable |
| GET | `/version` | Build label |

These live at the **API root**, not under `/api/v1`.

## Multipart uploads

### Single or multiple files

- **Endpoint:** `POST /api/v1/projects/{projectId}/sources/upload`
- **Content-Type:** `multipart/form-data`
- **Body:** one or more **file** parts. **Field names are not prescribed** (e.g. `file`, `file1`, or browser defaults all work).
- **Response:** JSON with `uploadedCount`, `rejectedCount`, `uploaded[]`, `rejected[]` (see schema `SourceUploadBatchResponse` in the YAML).
- **Errors:** `400` + `{ "error": "no_files" }` if no file parts; `413` + `{ "error": "file_too_large" }` if over server limit.

### ZIP archive

- **Endpoint:** `POST /api/v1/projects/{projectId}/sources/upload-zip`
- **Body:** exactly one zip file part (`application/zip` or `.zip` filename).

## Rate limiting (RAG)

All paths under `/api/v1/projects/{projectId}/rag/*` share a **per-tenant, per-role** sliding window. On exceed:

- **HTTP 429**
- Header **`Retry-After`** (seconds)
- Body includes `"error": "rate_limited"` and tuning fields

Configure on the ReqIQ server with `REQIQ_RAG_RATE_*` (see `apps/api/.env.example`). Automation should **retry with backoff** when receiving **429**.

## OpenAPI import tips

- After import, **edit the Server URL** in your tool to match the customer deployment.
- Configure **collection-level** or **environment** variable for `accessToken`, set from login response.
- **Security scheme:** HTTP Bearer (JWT).

## Source of truth

If the spec and the server disagree, the implementation wins:

- `apps/api/src/routes/api.ts`
- `apps/api/src/routes/health.ts`

## Hermes / AI Web Test (agentic QA)

Profile reference: `docs/Hermes_QA_MultiAgent_Profiles_v3.md`. AI Web Test API: `docs/ReqIQ-API-Integration-Guide.md`.

### Service account (server-to-server)

1. Create a dedicated user (e.g. `aiwebtest@reqiq.local`) with role **ANALYST**, **LIBRARIAN**, or **ADMIN** (not **AUDITOR**).
2. `POST {base}/api/v1/login` with `{ "email", "password" }` → use **`accessToken`** as `Authorization: Bearer …` (default TTL **8h**; re-login when expired — **401**).
3. Resolve **`projectId`**: `GET {base}/api/v1/projects` → use the **`id`** field (cuid), not the display name.

### ReqIQ endpoints Hermes uses most

| Operation | Path | Notes |
| --- | --- | --- |
| Readiness gate | `GET …/projects/{projectId}/readiness?query=…` | Returns `readinessScore`, `wikiContent`, `status`, `missing[]` (threshold default **60**) |
| RAG Q&A | `POST …/rag/query` | Body `{ "query": "…" }`; wiki text in **`content`**, not `answer` |
| Requirements | `GET …/requirements` | Each row includes `latestCompositeScore`, `latestRevisionIndex` |
| Latest IQ only | `GET …/requirements/{id}/latest-iq` | IQ fields without full requirement body |
| Upload + index | `POST …/sources/upload` then `POST …/embedding/reindex` | Reindex may POST Hermes webhook when configured |
| Generate tests | `POST …/suggested-tests/generate` | LLM; **503** if chat not configured |
| Import tests | `POST …/suggested-tests/import` | No LLM; accepts `ragQuery` / JSON |

### Hermes webhook (optional)

After a successful **embedding reindex**, ReqIQ can notify the Hermes HTTP gateway:

- **Admin:** `PATCH /api/v1/admin/integration-config` with `hermesWebhookUrl` (full URL, e.g. `http://node1:8080/hermes/qa-manager/message`) and `hermesWebhookBearer`.
- **Env fallback:** `REQIQ_HERMES_WEBHOOK_URL`, `REQIQ_HERMES_WEBHOOK_BEARER` on the API host (`apps/api/.env`).

Payload: `{ "trigger_type": "reqiq_index_ready", "projectId", "embeddingIndexVersion", … }`.

### Docker / LAN ports (typical)

| Service | Port |
| --- | --- |
| ReqIQ API | **3001** |
| ReqIQ web (nginx) | **8080** |
| Hermes HTTP gateway | **8080** on Node 1 (separate process) |
| AI Web Test API | **8000** on Windows runners |

Use the host **LAN IP** in MCP tools when Hermes and ReqIQ run on different machines (`127.0.0.1` is always local to that host only).

## Related requirements

High-level product requirements: `docs/ReqIQ_Software_Requirements_Specification.md` (§6.2 is illustrative; this OpenAPI reflects the **implemented** API).
