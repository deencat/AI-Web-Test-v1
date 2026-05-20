# ReqIQ OpenAPI folder

## For AI Web Test developers

**Use one document:** [`docs/AI-Web-Test-Developer-Handoff.md`](../AI-Web-Test-Developer-Handoff.md) (v2.1+). **§5.1a** lists every Sprint 8/8c endpoint for AI Web Test proxies.

That handoff includes auth, uploads, rate limits, proxy tables, shipped ReqIQ APIs, and verification. You do **not** need this README to integrate.

## Files here

| File | Purpose |
| --- | --- |
| **`reqiq-api-v1.yaml`** | OpenAPI 3.0.3 — import into Postman, Insomnia, Bruno, or codegen |
| **This README** | Pointer for Hermes/automation; human notes moved into the handoff |

## Hermes / other integrators

Service account, webhook, and LAN port notes for Hermes are in the handoff **§0** and **§4**, and in [`Hermes_QA_MultiAgent_Profiles_v3.md`](../Hermes_QA_MultiAgent_Profiles_v3.md).

High-level SRS: [`ReqIQ_Software_Requirements_Specification.md`](../ReqIQ_Software_Requirements_Specification.md).

**Delivery status:** [`ReqIQ_Project_Management_and_Sprint_Plan.md`](../ReqIQ_Project_Management_and_Sprint_Plan.md) v2.32 — **Sprint 8 complete** (`dd2e90e`); next Sprint 9 hardening.

If the YAML and a running server disagree, implementation wins: `apps/api/src/routes/api.ts`.
