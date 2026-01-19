# Phase 3: Phase 2 Integration Guide

**Purpose:** Migration strategy, API versioning, and database changes for Phase 2→Phase 3 integration  
**Status:** Ready for Sprint 7-8 implementation  
**Last Updated:** January 16, 2026

---

## 📋 Overview

This guide provides step-by-step integration between **Phase 2** (3-Tier Execution Engine) and **Phase 3** (Multi-Agent System). Integration occurs in **two stages**:

- **Stage 1 (Sprint 7-8):** Agent infrastructure alongside Phase 2 (parallel operation)
- **Stage 2 (Sprint 9-10):** Gradual agent integration (orchestration takes over)

**Key Principle:** **Zero downtime, backward compatible**

---

## 🎯 Integration Strategy

### Three-Phase Rollout

#### Phase A: Co-existence (Sprint 7-8)
- Phase 2 system continues normal operation
- Phase 3 agents deployed but **not in critical path**
- Agents observe and learn (shadow mode)
- No user-facing changes

#### Phase B: Partial Integration (Sprint 9-10)
- Agents handle **new test generation requests**
- Phase 2 handles **existing test execution**
- Feature flag controls agent usage (A/B testing)
- Rollback capability maintained

#### Phase C: Full Migration (Sprint 11-12)
- Agents handle 100% of workflows
- Phase 2 execution engine becomes **sub-component** (invoked by Evolution Agent)
- Legacy endpoints deprecated (6-month notice)

---

## 🗄️ Database Schema Changes

### New Tables (Add to existing PostgreSQL)

#### 1. `agent_registry`
```sql
CREATE TABLE agent_registry (
    agent_id VARCHAR(100) PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,  -- observation, requirements, analysis, evolution, orchestration, reporting
    status VARCHAR(20) NOT NULL,      -- healthy, unhealthy, shutting_down
    capabilities JSONB NOT NULL,      -- [{"name": "test_generation", "version": "1.0.0"}]
    priority INTEGER NOT NULL,
    endpoints JSONB NOT NULL,         -- {"inbox_stream": "agent:evolution_1:inbox"}
    health JSONB NOT NULL,            -- {"last_heartbeat": "2026-01-16T10:00:00Z", "active_tasks": 3}
    constraints JSONB,                -- {"max_concurrent_tasks": 5}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_type ON agent_registry(agent_type);
CREATE INDEX idx_agent_status ON agent_registry(status);
CREATE INDEX idx_agent_capabilities ON agent_registry USING GIN (capabilities);
```

#### 2. `working_memory`
```sql
CREATE TABLE working_memory (
    memory_id VARCHAR(100) PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL REFERENCES agent_registry(agent_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),           -- pgvector extension for semantic search
    timestamp TIMESTAMP NOT NULL,
    importance FLOAT NOT NULL CHECK (importance >= 0.0 AND importance <= 1.0),
    metadata JSONB,                   -- {"conversation_id": "abc-123", "task_id": "t-456"}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_working_memory_agent ON working_memory(agent_id);
CREATE INDEX idx_working_memory_timestamp ON working_memory(timestamp DESC);
CREATE INDEX idx_working_memory_conversation ON working_memory USING GIN (metadata);
CREATE INDEX idx_working_memory_embedding ON working_memory USING ivfflat (embedding vector_cosine_ops);
```

#### 3. `agent_tasks`
```sql
CREATE TABLE agent_tasks (
    task_id VARCHAR(100) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    assigned_agent_id VARCHAR(100) REFERENCES agent_registry(agent_id),
    status VARCHAR(20) NOT NULL,      -- pending, in_progress, completed, failed
    priority INTEGER NOT NULL DEFAULT 5,
    conversation_id VARCHAR(100),
    result JSONB,
    error TEXT,
    execution_time_seconds FLOAT,
    token_usage INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_agent_tasks_assigned ON agent_tasks(assigned_agent_id);
CREATE INDEX idx_agent_tasks_conversation ON agent_tasks(conversation_id);
CREATE INDEX idx_agent_tasks_type ON agent_tasks(task_type);
```

#### 4. `agent_metrics`
```sql
CREATE TABLE agent_metrics (
    metric_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL REFERENCES agent_registry(agent_id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,  -- tasks_completed, tasks_failed, token_usage, latency_ms
    metric_value FLOAT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_metrics_agent ON agent_metrics(agent_id, timestamp DESC);
CREATE INDEX idx_agent_metrics_type ON agent_metrics(metric_type);
```

### Migration Script

**File:** `backend/migrations/phase3_001_initial_schema.sql`

```sql
-- Phase 3 Initial Schema Migration
-- Safe to run on existing Phase 2 database

BEGIN;

-- Enable pgvector extension (for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables (order matters for foreign keys)
-- (Insert CREATE TABLE statements from above)

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON agent_registry TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON working_memory TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON agent_tasks TO app_user;
GRANT SELECT, INSERT, UPDATE ON agent_metrics TO app_user;
GRANT USAGE, SELECT ON SEQUENCE agent_metrics_metric_id_seq TO app_user;

-- Verify migration
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'agent_registry') = 1,
           'agent_registry table not created';
    RAISE NOTICE 'Phase 3 schema migration completed successfully';
END $$;

COMMIT;
```

**Run Migration:**
```bash
psql -U postgres -d ai_web_test < backend/migrations/phase3_001_initial_schema.sql
```

---

## 🔌 API Changes

### Versioning Strategy

**URL Versioning:** `/api/v2/` for Phase 3 endpoints (Phase 2 uses `/api/v1/`)

**Rationale:**
- Clear separation (no breaking changes to v1)
- Both versions coexist during transition
- v1 deprecated after 6 months (announced in Sprint 11)

### New Endpoints (v2)

#### 1. Test Generation (Agent-Powered)

**POST `/api/v2/tests/generate`**

Request:
```json
{
  "repository_url": "https://github.com/user/repo",
  "target_files": ["src/services/user_service.py"],
  "coverage_target": 0.85,
  "requirements": "Focus on edge cases and error handling",
  "conversation_id": "uuid-abc-123"  // Optional: for follow-up requests
}
```

Response:
```json
{
  "task_id": "task-xyz-789",
  "status": "pending",
  "estimated_completion_seconds": 120,
  "conversation_id": "uuid-abc-123"
}
```

**GET `/api/v2/tests/generate/{task_id}`**

Response:
```json
{
  "task_id": "task-xyz-789",
  "status": "completed",
  "result": {
    "tests": "import pytest\n\ndef test_user_service():\n    ...",
    "coverage_estimate": 0.87,
    "test_count": 15
  },
  "execution_time_seconds": 98.5,
  "token_usage": 8500,
  "agent_id": "agent_evolution_1"
}
```

#### 2. Agent Status

**GET `/api/v2/agents`**

Response:
```json
{
  "agents": [
    {
      "agent_id": "agent_evolution_1",
      "agent_type": "evolution",
      "status": "healthy",
      "capabilities": ["test_generation", "mutation_testing"],
      "active_tasks": 3,
      "tasks_completed_today": 127
    }
  ]
}
```

#### 3. Metrics Dashboard

**GET `/api/v2/metrics/dashboard`**

Response:
```json
{
  "system_health": "healthy",
  "total_agents": 12,
  "active_agents": 11,
  "tasks_completed_24h": 1523,
  "avg_latency_seconds": 45.2,
  "token_usage_24h": 2500000,
  "cost_24h_usd": 37.50
}
```

### Backward Compatibility

**Phase 2 Endpoints (v1) - Keep Intact:**
- `POST /api/v1/execute` → Continues to work
- `GET /api/v1/execution/{id}/status` → Continues to work
- `GET /api/v1/settings` → Continues to work

**Migration Helper Endpoint:**

**POST `/api/v1/tests/generate`** (v1 endpoint, new feature)

```json
{
  "use_agents": true,  // Feature flag: true = use Phase 3, false = Phase 2
  "repository_url": "...",
  ...
}
```

Response redirects to v2 endpoint if `use_agents: true`.

---

## 🔀 Integration Points

### 1. Test Execution

**Current (Phase 2):**
```
User → Frontend → Backend API → 3-Tier Execution Engine → Stagehand
```

**Future (Phase 3):**
```
User → Frontend → Backend API → Orchestration Agent → Evolution Agent → (Phase 2 Execution Engine) → Stagehand
```

**Key Change:** Evolution Agent **wraps** Phase 2 execution engine (not replaces). Execution logic unchanged.

**Implementation:**

```python
# backend/agents/evolution_agent.py

async def execute_test(self, test_code: str):
    """Execute test using Phase 2 execution engine"""
    # Call Phase 2 API internally
    response = await self.http_client.post(
        "http://localhost:8000/api/v1/execute",
        json={
            "test_code": test_code,
            "execution_strategy": "tier1_to_tier2_to_tier3"  # From Sprint 5.5
        }
    )
    return response.json()
```

### 2. Settings Propagation

**Phase 2 Settings Table:**
```sql
SELECT fallback_strategy FROM execution_settings WHERE id = 1;
-- Result: 'tier1_to_tier2_to_tier3'
```

**Phase 3 Agent Configuration:**
Agents read same `execution_settings` table. No duplication.

```python
# backend/agents/evolution_agent.py

async def load_execution_settings(self):
    """Load Phase 2 execution settings"""
    async with self.pg_pool.acquire() as conn:
        settings = await conn.fetchrow(
            "SELECT * FROM execution_settings WHERE id = 1"
        )
    self.fallback_strategy = settings["fallback_strategy"]
```

### 3. Frontend Changes

**Minimal Changes Required:**

**Before (Phase 2 UI):**
```typescript
// frontend/src/services/testService.ts

export async function generateTests(params) {
  const response = await fetch('/api/v1/execute', {
    method: 'POST',
    body: JSON.stringify(params)
  });
  return response.json();
}
```

**After (Phase 3 UI with Feature Flag):**
```typescript
// frontend/src/services/testService.ts

export async function generateTests(params, useAgents = false) {
  const endpoint = useAgents ? '/api/v2/tests/generate' : '/api/v1/execute';
  const response = await fetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(params)
  });
  return response.json();
}

// Usage:
const useAgents = localStorage.getItem('feature_agents_enabled') === 'true';
await generateTests(params, useAgents);
```

**Feature Flag UI:**

Add toggle in settings page:

```tsx
// frontend/src/pages/Settings.tsx

<Switch
  label="Use AI Agents for Test Generation (Beta)"
  checked={featureFlags.agentsEnabled}
  onChange={(enabled) => {
    localStorage.setItem('feature_agents_enabled', String(enabled));
    setFeatureFlags({ ...featureFlags, agentsEnabled: enabled });
  }}
/>
```

---

## 📊 Data Migration

### No Data Migration Required ✅

**Reason:** Phase 3 introduces **new tables** but doesn't modify existing Phase 2 tables.

**Existing Data:**
- `tests` table: Unchanged
- `executions` table: Unchanged
- `execution_settings` table: Unchanged (agents read from it)

**New Data:**
- `agent_registry`: Populated on agent startup (auto-registration)
- `working_memory`: Empty initially, fills during operation
- `agent_tasks`: Empty initially, fills when agents used

---

## 🧪 Testing Strategy

### Integration Test Suite

**File:** `backend/tests/integration/test_phase2_phase3_integration.py`

```python
import pytest
from tests.fixtures import db_session, test_client

@pytest.mark.integration
async def test_phase2_execution_still_works(test_client):
    """Verify Phase 2 API unchanged"""
    response = await test_client.post('/api/v1/execute', json={
        "test_code": "def test_example(): assert True",
        "execution_strategy": "tier1_to_tier2"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.integration
async def test_phase3_agents_coexist(test_client, db_session):
    """Verify agents can operate alongside Phase 2"""
    # Start agent
    agent = EvolutionAgent(...)
    await agent.start()
    
    # Phase 2 API still works
    response = await test_client.post('/api/v1/execute', json={...})
    assert response.status_code == 200
    
    # Phase 3 API also works
    response = await test_client.post('/api/v2/tests/generate', json={...})
    assert response.status_code == 200
    
    await agent.stop()

@pytest.mark.integration
async def test_agent_uses_phase2_execution(test_client):
    """Verify Evolution Agent calls Phase 2 execution engine"""
    response = await test_client.post('/api/v2/tests/generate', json={
        "repository_url": "https://github.com/test/repo",
        "target_files": ["test.py"]
    })
    task_id = response.json()["task_id"]
    
    # Poll for result
    for _ in range(30):  # 30 seconds max
        result = await test_client.get(f'/api/v2/tests/generate/{task_id}')
        if result.json()["status"] == "completed":
            break
        await asyncio.sleep(1)
    
    # Verify Phase 2 execution engine was called
    assert result.json()["status"] == "completed"
    assert "tests" in result.json()["result"]
```

### Rollback Plan

**If Phase 3 causes issues:**

1. **Immediate:** Disable feature flag
   ```sql
   UPDATE system_config SET value = 'false' WHERE key = 'agents_enabled';
   ```

2. **Database:** No rollback needed (new tables unused)

3. **Code:** Revert deployment to previous version

4. **Time to rollback:** <5 minutes

---

## 🔧 Configuration Changes

### Environment Variables

**Add to `.env`:**

```bash
# Phase 3 Configuration
AGENTS_ENABLED=false                 # Feature flag (false in Sprint 7-8, true in Sprint 9+)
REDIS_STREAMS_URL=redis://localhost:6379
VECTOR_DB_URL=http://localhost:6333  # Qdrant
AGENT_MAX_CONCURRENT_TASKS=5
AGENT_TOKEN_BUDGET_DAILY=1000000     # 1M tokens/day
LLM_MODEL=gpt-4o-mini                # Default model for agents
LLM_API_KEY=sk-...                   # OpenAI API key

# Keep existing Phase 2 config
POSTGRES_URL=postgresql://...
STAGEHAND_API_KEY=...
```

### Settings UI Update

**Add to Settings Page (Sprint 8):**

```tsx
// frontend/src/pages/Settings.tsx

<Section title="AI Agents (Phase 3 Beta)">
  <Switch
    label="Enable AI Agents"
    checked={settings.agentsEnabled}
    description="Use multi-agent system for intelligent test generation"
  />
  
  <Select
    label="Primary LLM Model"
    value={settings.llmModel}
    options={[
      { value: 'gpt-4o-mini', label: 'GPT-4 Mini (Fast, $0.15/1M tokens)' },
      { value: 'gpt-4o', label: 'GPT-4 (Best quality, $5/1M tokens)' }
    ]}
  />
  
  <NumberInput
    label="Daily Token Budget"
    value={settings.dailyTokenBudget}
    min={10000}
    max={10000000}
    description="Maximum tokens per day across all agents"
  />
</Section>
```

---

## 📅 Rollout Schedule

### Week 1-2 (Sprint 7): Infrastructure
- ✅ Database schema deployed
- ✅ Agents deployed (shadow mode, not handling requests)
- ✅ Feature flag OFF
- ✅ Phase 2 unchanged, fully operational

### Week 3-4 (Sprint 8): Alpha Testing
- ✅ 2 agents operational (Observation, Requirements)
- ✅ Feature flag available to internal users
- ✅ 5% traffic to agents (A/B test)
- ✅ Monitor metrics: latency, error rate, cost

### Week 5-6 (Sprint 9): Beta Testing
- ✅ 4 agents operational (add Analysis, Evolution)
- ✅ 25% traffic to agents
- ✅ Beta opt-in for external users
- ✅ Collect user feedback

### Week 7-8 (Sprint 10): Expanded Rollout
- ✅ All 6 agents operational
- ✅ 50% traffic to agents
- ✅ Monitor system health closely

### Week 9-10 (Sprint 11): Majority Migration
- ✅ 90% traffic to agents
- ✅ Phase 2 as fallback only

### Week 11-12 (Sprint 12): Full Migration
- ✅ 100% traffic to agents
- ✅ Announce Phase 2 API deprecation (6-month timeline)
- ✅ Documentation updated

---

## 🚨 Monitoring \& Alerts

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Agent availability | >99% | <95% |
| Request latency (P95) | <30s | >60s |
| Error rate | <1% | >5% |
| Token usage per request | <10,000 | >20,000 |
| Daily cost | <$100 | >$200 |
| Phase 2 fallback rate | <5% | >20% |

### Grafana Dashboard

**Panels:**
1. **Traffic Split:** Percentage of requests handled by agents vs Phase 2
2. **Agent Health:** Status of all 6 agent types
3. **Latency Comparison:** Phase 2 vs Phase 3 response times
4. **Cost Tracking:** Token usage and estimated daily cost
5. **Error Rates:** By agent type and endpoint

**Alerts:**
```yaml
# grafana/alerts/phase3_integration.yaml

- alert: AgentAvailabilityLow
  expr: sum(agent_registry_healthy) / sum(agent_registry_total) < 0.95
  for: 5m
  annotations:
    summary: "Less than 95% of agents are healthy"
    
- alert: Phase3LatencyHigh
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{path="/api/v2/*"}[5m])) > 60
  for: 10m
  annotations:
    summary: "Phase 3 API P95 latency exceeds 60 seconds"
    
- alert: TokenBudgetExceeded
  expr: sum(rate(agent_token_usage_total[24h])) > 1000000
  annotations:
    summary: "Daily token budget exceeded"
```

---

## ✅ Pre-Launch Checklist

**Before enabling agents in production:**

- [ ] All database migrations applied successfully
- [ ] pgvector extension installed and tested
- [ ] Redis Streams operational (test message throughput)
- [ ] Vector DB (Qdrant) running and accepting embeddings
- [ ] All 6 agents registered and healthy
- [ ] Phase 2 APIs tested and confirmed working
- [ ] Feature flag tested (toggle on/off works)
- [ ] Integration tests pass (95%+ coverage)
- [ ] Load testing completed (100+ concurrent requests)
- [ ] Rollback procedure tested
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] On-call rotation scheduled
- [ ] Documentation updated
- [ ] Stakeholders notified

---

## 📞 Support \& Escalation

**If issues arise during integration:**

1. **Check dashboards:** Grafana Phase 3 Integration dashboard
2. **Review logs:** `kubectl logs -l app=agents -n production --tail=100`
3. **Disable agents:** Set `AGENTS_ENABLED=false` environment variable
4. **Escalate:** Contact Phase 3 team lead (Developer A)

**Rollback SLA:** <5 minutes from decision to rollback complete

---

**END OF PHASE 2 INTEGRATION GUIDE**
