# UF-6 — 5G Mobile Broadband pilot checklist

**Product workspace:** `/products/5g-mobile-broadband`  
**Admin sync:** Programs hub hidden from business users; use **Update summary** (auto-sync) or admin Sync after wiki compile.

**Quality follow-on:** [Quality-Test-Generation-Plan.md](../../Quality-Test-Generation-Plan.md)

## Scenarios

| # | Action | Pass |
|---|--------|------|
| 1 | Upload base offer batch (URS, T&C, MVP config, UX images) | Document count increases |
| 2 | Update summary / recompile wiki | Sections include Base offer, Active promotions, **Purchase journeys** |
| 3 | Confirm Purchase journeys survive after compile | Wiki still has `## Purchase journeys` step tables |
| 4 | Generate test scenarios (current UF-4.1) | ≥1 DRAFT requirement — treat as **review draft**, not automation-ready |
| 5 | Keep ~5–6 ideas; merge Steps 01–07 into **one E2E happy path** | One plain-language happy-path scenario |
| 6 | **Generate browser test** (suggest-tests → Crawl & Save) on that one scenario | Saved `TestCase` id; steps executable |
| 7 | Run overnight / factory regression (product-tagged) | Executions visible; no YAML edited by user |
| 8 | Add June promo PPT + recompile | June under Active promotions with dates |
| 9 | After 1 Jul (or sync with July wiki) | June promo not in active initiatives; tests retired |

## Known gaps (do not mark pilot “done” until fixed)

- [ ] Wiki recompile does not strip Purchase journeys
- [ ] Main product UX one-click **Generate browser test** (not only Advanced ReqIQ)
- [ ] Overnight scoped to product tags / registry (not global `regression` only)
- [ ] Optional: push **saved** high-quality tests back to ReqIQ for traceability

## Automated tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests/unit/test_product_workspace_uf.py tests/unit/test_ux_flow_extractor.py tests/unit/test_compile_progress.py tests/unit/test_offer_table_convert.py tests/unit/test_product_document_store.py -q
```

## Business user path (no YAML)

1. **Products** → 5G Mobile Broadband  
2. Upload documents  
3. Update summary → review wiki (check Purchase journeys)  
4. Create / keep scenarios → **Generate browser test** on happy path  
5. Run overnight  
