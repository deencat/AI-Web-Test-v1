# Generator State — Iteration ASG Phase 4

## What Was Built
- **Confidence scoring v2** in `score_selector_stability()`: `playwright_suggestions` role+name (0.85) and css_id (0.75) now win over bare `xpath` (0.55)
- **`_score_selector_stability_v1()`** helper for uplift comparison in confidence reports
- **`extract_readiness_snapshots_from_flow_steps()`** extracts `readiness` / `post_click_readiness` from flow steps
- **`normalize_transition()`** copies `playwright_suggestions` from locator bundle into transition payload
- **`trigger_shadow_build()`** forwards extracted `readiness_snapshots` into `ASGBuildRequest`
- **Observation agent** attaches per-step `readiness` on navigate/click/input flow_steps
- **confidence-report.json** now includes `scoring_version: "v2"` and `uplift: {v1_mean, v2_mean}`
- Pilot fixtures: `backend/tests/fixtures/asg/pilot_graph5_flow_steps.json`, `pilot_graph6_flow_steps.json`
- Phase 4 tests in `TestPhase4ConfidenceV2` (unit + integration)

## What Changed This Iteration
- Fixed xpath-first regression: xpath + role suggestion → **0.85** (was 0.55)
- Wired readiness snapshots through shadow build path (settled → 0.90, loading_cleared → 0.80)
- Pilot rebuild from fixtures passes `ASG_CONFIDENCE_MIN=0.75` gate without lowering threshold
- **100% coverage** maintained on all six ASG modules (94 tests pass)

## Pilot Confidence Scores (v2 rebuild from fixtures)
| Fixture | Mean Confidence | v1 Mean | v2 Mean | fallback_recommended |
|---------|----------------|---------|---------|---------------------|
| pilot_graph5 (18 steps) | 0.7703 | 0.7204 | 0.7703 | false |
| pilot_graph6 (17 steps) | 0.7700 | 0.7206 | 0.7700 | false |

## Known Issues
- Requirement-coverage planner still uses title/fingerprint heuristics
- Crawl quality tuning (terminal nodes, self-loops) deferred to post-scoring-fix guidelines

## Dev Server
- URL: http://localhost:8000
- Status: running (per parent session `python start_server.py`)
- Command: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`

## Coverage Verification
```bash
cd backend && source venv/bin/activate
pytest tests/unit/test_asg*.py tests/e2e/test_asg_pipeline_e2e.py -v \
  --cov=app.services.asg_service --cov=app.crud.asg --cov=app.api.v2.endpoints.asg \
  --cov=app.models.asg --cov=app.schemas.asg --cov=app.services.asg_metrics \
  --cov-report=term-missing --cov-fail-under=100
```
