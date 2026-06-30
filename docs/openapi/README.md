# OpenAPI folder

**Last Updated:** 2026-06-30

## Two OpenAPI contracts

This folder contains the **ReqIQ** API contract. AI Web Test has its **own** OpenAPI served by FastAPI:

| System | Spec location | Swagger UI |
| --- | --- | --- |
| **AI Web Test** (this repo) | `backend/openapi_spec.json` (static) or live `/api/v1/openapi.json` | `http://127.0.0.1:8000/api/v1/docs` |
| **ReqIQ** (companion system) | `docs/openapi/reqiq-api-v1.yaml` | ReqIQ server (separate repo) |

## For AI Web Test developers

**ReqIQ integration handoff:** [`docs/AI-Web-Test-Developer-Handoff.md`](../AI-Web-Test-Developer-Handoff.md) (v2.5+). **§5.1a** lists Sprint 8/8c proxy endpoints.

**AI Web Test API for Hermes/external callers:** [`docs/ReqIQ-API-Integration-Guide.md`](../ReqIQ-API-Integration-Guide.md) — crawl, execute, RCA endpoints.

**Architecture codemaps:** [`docs/CODEMAPS/INDEX.md`](../CODEMAPS/INDEX.md)

## Files here

| File | Purpose |
| --- | --- |
| **`reqiq-api-v1.yaml`** | OpenAPI 3.0.3 for **ReqIQ** `/api/v1` — Postman, Insomnia, Bruno, codegen |
| **This README** | Contract location guide |

## Hermes / other integrators

Service account and LAN port notes: handoff **§0** and **§4**, plus [`Hermes_QA_MultiAgent_Profiles_v3.md`](../Hermes_QA_MultiAgent_Profiles_v3.md).

If `reqiq-api-v1.yaml` and a running ReqIQ server disagree, the **running ReqIQ implementation** wins (ReqIQ ships in a separate repository).
