# UF-6 — 5G Mobile Broadband pilot checklist

**Product workspace:** `/products/5g-mobile-broadband`  
**Admin sync:** Programs hub hidden from business users; use **Sync automation** (admin) after wiki compile.

## Scenarios

| # | Action | Pass |
|---|--------|------|
| 1 | Upload base offer batch (URS, T&C, MVP config) | Document count increases |
| 2 | Recompile wiki | Sections: Base offer, Active promotions, … |
| 3 | Generate test scenarios | ≥1 DRAFT requirement |
| 4 | Admin: Sync automation | Initiatives updated in manifest; journeys seeded |
| 5 | Run overnight | Factory job queued |
| 6 | Add June promo PPT + recompile | June under Active promotions with dates |
| 7 | After 1 Jul (or sync with July wiki) | June promo not in active initiatives; tests retired |

## Automated tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests/unit/test_product_workspace_uf.py -q
```

## Business user path (no YAML)

1. **Products** → 5G Mobile Broadband  
2. Upload documents  
3. Recompile wiki → review  
4. Generate test scenarios  
5. Run overnight  
