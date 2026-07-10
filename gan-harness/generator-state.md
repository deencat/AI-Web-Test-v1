# Generator State — Iteration ASG Coverage Hardening

## What Was Built
- SQLAlchemy models: `asg_graphs`, `asg_nodes`, `asg_edges`, `asg_paths`, `asg_synthesized_tests`
- Migration: `backend/migrations/add_asg_tables.py`
- `ASGService`: fingerprinting, transition normalization, confidence scoring, policy engine, path planner, synthesizer, confidence gate
- CRUD: `backend/app/crud/asg.py`
- Schemas: `backend/app/schemas/asg.py`
- API: `/api/v2/asg/build`, `GET /{graph_id}`, `POST /{graph_id}/plan|synthesize|validate`
- Feature flags: `ASG_ENABLED`, `ASG_SHADOW_MODE`, `ASG_CONFIDENCE_MIN`, `ASG_PROJECT_ALLOWLIST`
- Integration: crawl-and-save shadow build; generate-tests ASG branch with legacy fallback
- Artifact storage under `artifacts/asg/{graph_id}/` including `replay/{execution_id}.json`
- `ASGService.write_replay_artifact()` helper linking graph/plan/synthesis/execution IDs
- `backend/pytest.ini` with `pythonpath = .`
- ADR-010 documentation

## What Changed This Iteration
- Added `backend/pytest.ini` (`pythonpath = .`) to fix import failures without `PYTHONPATH=.`
- Added `test_asg_coverage.py` for policy engine, planner modes, API error paths, CRUD gaps, feature flags
- Added `test_asg_execution_contract.py` — ASG synthesize → save TestCase → `ExecutionService.execute_test` consumes `string[]` steps
- Added `write_replay_artifact()` and replay bundle tests
- Removed redundant dead branch in `trigger_shadow_build()` (duplicate shadow-mode gate)
- **100% coverage** on all five ASG modules (`cov-fail-under=100` passes; 70 tests)

## Known Issues
- Requirement-coverage planner uses title/fingerprint heuristics until Requirements agent mapping is wired
- Risk-first mode produces single-edge probe paths (Phase 2 baseline)
- ASG primary mode skips Requirements/Analysis/Evolution when confidence passes (by design)

## Dev Server
- URL: http://localhost:8000
- Status: not started in this iteration
- Command: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`

## Coverage Verification
```bash
cd backend && source venv/bin/activate
pytest tests/unit/test_asg*.py -v \
  --cov=app.services.asg_service --cov=app.crud.asg --cov=app.api.v2.endpoints.asg \
  --cov=app.models.asg --cov=app.schemas.asg \
  --cov-report=term-missing --cov-fail-under=100
```
