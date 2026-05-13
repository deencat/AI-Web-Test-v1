# Architecture Decision Records — Knowledge Base Upload Size Limit

**Document ID:** ADR-005  
**Component:** Knowledge Base — File Upload Service  
**Status:** Accepted  
**Date:** May 11, 2026  
**Author:** Developer B  
**Related Files:**
- `backend/app/services/file_upload.py`
- `backend/app/api/v1/endpoints/kb.py`
- `backend/app/main.py`
- `frontend/src/pages/KnowledgeBasePage.tsx`
- `backend/tests/unit/test_kb_file_upload_size_limit.py`

---

## Context

The Knowledge Base file upload limit was set to **10 MB** at initial implementation. In practice, real telecom product catalogs, process guides, and system documentation frequently exceed 10 MB — particularly PDFs that embed diagrams or screenshots.

At the same time, the workflow file upload endpoint (`POST /api/v1/uploads/workflow-files`) already accepts **50 MB**, meaning the backend infrastructure (Uvicorn, Docker networking, no nginx `client_max_body_size` constraint) can handle files well above 10 MB without configuration changes.

The request was to evaluate increasing the limit to 50 MB.

---

## Decision

Increase the maximum upload size for Knowledge Base documents from **10 MB to 25 MB**.

50 MB was not chosen because the current `FileUploadService._validate_file()` reads the entire file into memory before writing it to disk, then `save_file()` reads it again — meaning a 50 MB upload consumes ~100 MB of RAM per concurrent request. Additionally, extracted text content is written directly to a single `content` DB column with no chunking, making very large PDFs a row-size risk.

25 MB:
- Covers the practical upper bound of known telecom documentation (catalog PDFs, CRM guides).
- Keeps peak memory per upload at ~50 MB — acceptable for the current single-process deployment.
- Leaves a clear upgrade path to 50 MB once the double-read and DB chunking issues are addressed.

---

## Changes Made

| Layer | File | Change |
|---|---|---|
| Backend service | `backend/app/services/file_upload.py` | `max_size = 25 * 1024 * 1024` |
| Backend endpoint docstring | `backend/app/api/v1/endpoints/kb.py` | Updated "up to 25MB" |
| API version metadata | `backend/app/main.py` | `"max_file_size": "25MB"` |
| Frontend client validation | `frontend/src/pages/KnowledgeBasePage.tsx` | Size check and UI label updated to 25 MB |

---

## Consequences

**Positive**
- Documents up to 25 MB (e.g. rich product catalog PDFs) can now be uploaded without rejection.
- Consistent with real telecom QA use-cases where large reference documents are common.
- No infrastructure changes required — Uvicorn and the Docker networking layer already support this.

**Negative**
- Peak RAM per concurrent KB upload is ~50 MB (file read into memory twice: once for validation, once for `aiofiles` write). Tracked for future optimisation.
- Extracted text from a 25 MB PDF can be 15–20 MB; stored without chunking in the `content` column. Acceptable for current scale; tracked for Sprint 12 chunking work.
- Users who relied on a 10 MB policy for storage budget control will need to enforce limits via other means.

**Alternatives Considered**
- **50 MB**: Infrastructure supports it, but double-read memory risk (~100 MB/request) and unbounded DB content column make it premature without streaming + chunking refactors.
- **Direct 10 MB → 50 MB**: Rejected for the same reasons above.
- **Keep 10 MB**: Rejected — confirmed user-facing blocker with real project documents.

---

## Known Technical Debt (Not Fixed Here)

| Issue | Description | Target |
|---|---|---|
| Double-read memory usage | `_validate_file` reads entire file then `save_file` reads again | Sprint 12 |
| Unbounded DB `content` column | No truncation or chunking of extracted text | Sprint 12 |
| No async text extraction | PyPDF2 extraction runs synchronously (may block event loop on large PDFs) | Sprint 12 |

---

## Test Coverage

Covered by `backend/tests/unit/test_kb_file_upload_size_limit.py` (7 tests, all passing):

| Test | What is verified |
|------|-----------------|
| `test_max_size_is_25mb` | `FileUploadService.max_size == 25 * 1024 * 1024` |
| `test_max_size_greater_than_10mb` | Regression: strictly above old 10 MB ceiling |
| `test_file_at_exact_limit_passes` | Exactly 25 MB file is accepted |
| `test_file_one_byte_over_limit_raises` | 25 MB + 1 byte raises `HTTPException 400` |
| `test_file_just_under_limit_passes` | 25 MB − 1 byte is accepted |
| `test_old_11mb_file_now_passes` | 11 MB file (previously rejected) now accepted |
| `test_error_message_states_correct_limit` | Error detail references "25.0MB", not "10.0MB" |
