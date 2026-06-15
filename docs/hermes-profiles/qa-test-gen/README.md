# qa-test-gen

Browser crawl-and-save test generation (Loop A test-gen step, Loop C regeneration).

| File | Purpose |
|------|---------|
| `SOUL.md` | System prompt — wiki → crawl → poll → test_case_id |
| `config.yaml` | MCP with extended timeout for long crawls |

## Install on Ubuntu (Hermes Node)

```bash
hermes profile create "qa-test-gen"
cp SOUL.md ~/.hermes/profiles/qa-test-gen/
cp config.yaml ~/.hermes/profiles/qa-test-gen/
# ~/.hermes/.env: AWT_MCP_*, TEST_LOGIN_*, HTTP_AUTH_*
qa-test-gen model
```

## Smoke (via orchestrator)

After planner returns `items_for_test_gen`:

```bash
qa-orchestrator chat -q 'delegate to qa-test-gen: generate one test from backlog item (planner output)'
```

**Acceptance (HF-3.1c):** delegated task returns `{ "status": "success", "test_case_id": <id> }`.

## MCP tools used

`crawl_and_save_test`, `get_workflow_status`, `get_workflow_results`, `health_check` —
see [MCP_CONNECTIVITY.md](../_shared/MCP_CONNECTIVITY.md).

**Note:** `reference_test_id` is passed when the journey registry or heal/change path supplies it.
