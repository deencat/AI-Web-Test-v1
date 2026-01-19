# Phase 3: Testing Strategy - Detailed

**Purpose:** Comprehensive testing approach for multi-agent system  
**Status:** Ready for Sprint 7+ implementation  
**Last Updated:** January 16, 2026

---

## 📋 Overview

Multi-agent systems require **specialized testing** beyond traditional unit/integration tests. This strategy covers:

1. **Unit Tests** (70% of test suite)
2. **Integration Tests** (20%)
3. **System Tests** (8%)
4. **Chaos Engineering** (2%)

**Goal:** 95%+ code coverage, <5% change failure rate, 99.5%+ uptime

---

## 🧪 Testing Pyramid

```
         /\
        /  \  System Tests (8%)
       /____\
      /      \  Integration Tests (20%)
     /________\
    /          \  Unit Tests (70%)
   /____________\
   
  Chaos Tests (2%, continuous)
```

---

## 1. Unit Tests (70%)

### Coverage Targets

| Component | Coverage Target | Test Count |
|-----------|----------------|------------|
| BaseAgent | 95% | 50+ |
| Specialized Agents (each) | 90% | 30+ per agent |
| Memory System | 95% | 40+ |
| Message Bus | 95% | 35+ |
| Orchestrator | 90% | 45+ |

### Test Templates

#### BaseAgent Unit Tests

**File:** `backend/tests/unit/test_base_agent.py`

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from backend.agents.base_agent import BaseAgent, TaskContext, TaskResult, AgentCapability


class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent functionality"""
    
    @property
    def capabilities(self):
        return [AgentCapability("test_capability", "1.0.0")]
    
    async def can_handle(self, task):
        return task.task_type == "test_task", 0.85
    
    async def execute_task(self, task):
        await asyncio.sleep(0.1)  # Simulate work
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={"output": "test_result"},
            confidence=0.85
        )


@pytest.fixture
async def mock_agent():
    """Create mock agent with mocked dependencies"""
    redis = AsyncMock()
    mq = AsyncMock()
    llm = AsyncMock()
    vector_db = AsyncMock()
    registry = AsyncMock()
    
    agent = MockAgent(
        agent_id="test_agent_1",
        agent_type="test",
        priority=5,
        redis_client=redis,
        message_queue=mq,
        llm_client=llm,
        vector_db=vector_db,
        registry=registry,
        config={"max_concurrent_tasks": 5}
    )
    
    yield agent
    
    # Cleanup
    if agent.accepting_requests:
        await agent.stop()


@pytest.mark.asyncio
class TestBaseAgentLifecycle:
    """Test agent startup, operation, and shutdown"""
    
    async def test_start_registers_agent(self, mock_agent):
        """Agent registers with registry on startup"""
        await mock_agent.start()
        
        mock_agent.registry.register.assert_called_once()
        call_args = mock_agent.registry.register.call_args[0][0]
        assert call_args["agent_id"] == "test_agent_1"
        assert call_args["agent_type"] == "test"
    
    async def test_start_begins_accepting_requests(self, mock_agent):
        """Agent accepts requests after startup"""
        await mock_agent.start()
        assert mock_agent.accepting_requests is True
    
    async def test_stop_completes_active_tasks(self, mock_agent):
        """Agent waits for active tasks before shutdown"""
        await mock_agent.start()
        
        # Start a task
        task = TaskContext(
            task_id="t1",
            task_type="test_task",
            payload={},
            conversation_id="c1"
        )
        
        # Execute in background
        task_future = asyncio.create_task(mock_agent.execute_task(task))
        await asyncio.sleep(0.05)  # Let it start
        
        # Initiate shutdown
        stop_future = asyncio.create_task(mock_agent.stop())
        
        # Task should complete before shutdown
        await task_future
        await stop_future
        
        assert mock_agent.tasks_completed == 1
    
    async def test_stop_deregisters_agent(self, mock_agent):
        """Agent de-registers from registry on shutdown"""
        await mock_agent.start()
        await mock_agent.stop()
        
        mock_agent.registry.deregister.assert_called_once_with("test_agent_1")
    
    async def test_heartbeat_sent_periodically(self, mock_agent):
        """Heartbeat sent every 30 seconds"""
        await mock_agent.start()
        
        # Wait for first heartbeat
        await asyncio.sleep(0.1)
        
        # Should have called heartbeat at least once
        assert mock_agent.registry.heartbeat.call_count >= 1
        
        await mock_agent.stop()


@pytest.mark.asyncio
class TestBaseAgentTaskHandling:
    """Test task acceptance and execution"""
    
    async def test_can_handle_returns_confidence(self, mock_agent):
        """can_handle returns boolean and confidence score"""
        task = TaskContext(
            task_id="t1",
            task_type="test_task",
            payload={},
            conversation_id="c1"
        )
        
        can_handle, confidence = await mock_agent.can_handle(task)
        assert can_handle is True
        assert 0.0 <= confidence <= 1.0
    
    async def test_execute_task_returns_result(self, mock_agent):
        """execute_task returns TaskResult"""
        task = TaskContext(
            task_id="t1",
            task_type="test_task",
            payload={},
            conversation_id="c1"
        )
        
        result = await mock_agent.execute_task(task)
        assert isinstance(result, TaskResult)
        assert result.success is True
        assert result.task_id == "t1"
    
    async def test_process_message_rejects_unsupported_tasks(self, mock_agent):
        """process_message rejects tasks agent can't handle"""
        await mock_agent.start()
        
        message = {
            "message_id": "m1",
            "conversation_id": "c1",
            "content": {
                "type": "unsupported_task",
                "payload": {}
            },
            "priority": 5
        }
        
        result = await mock_agent.process_message(message)
        assert result is None  # Rejected
    
    async def test_metrics_updated_on_success(self, mock_agent):
        """Metrics incremented on successful task completion"""
        await mock_agent.start()
        
        task = TaskContext(
            task_id="t1",
            task_type="test_task",
            payload={},
            conversation_id="c1"
        )
        
        await mock_agent.execute_task(task)
        assert mock_agent.tasks_completed == 1
        assert mock_agent.tasks_failed == 0
    
    async def test_metrics_updated_on_failure(self, mock_agent):
        """Metrics incremented on task failure"""
        # Make execute_task fail
        with patch.object(mock_agent, 'execute_task', side_effect=Exception("Test error")):
            await mock_agent.start()
            
            message = {
                "message_id": "m1",
                "conversation_id": "c1",
                "content": {
                    "type": "test_task",
                    "payload": {}
                },
                "priority": 5
            }
            
            result = await mock_agent.process_message(message)
            assert result.success is False
            assert mock_agent.tasks_failed == 1


@pytest.mark.asyncio
class TestBaseAgentBidding:
    """Test Contract Net Protocol bidding"""
    
    async def test_bid_on_task_returns_confidence(self, mock_agent):
        """bid_on_task returns bid with confidence"""
        cfp = {
            "task_id": "t1",
            "task_type": "test_task",
            "requirements": {},
            "conversation_id": "c1"
        }
        
        bid = await mock_agent.bid_on_task(cfp)
        assert bid is not None
        assert "confidence" in bid
        assert "agent_id" in bid
    
    async def test_bid_adjusted_by_load(self, mock_agent):
        """Confidence adjusted by current load"""
        cfp = {
            "task_id": "t1",
            "task_type": "test_task",
            "requirements": {}
        }
        
        # No load
        bid1 = await mock_agent.bid_on_task(cfp)
        confidence1 = bid1["confidence"]
        
        # Simulate high load
        mock_agent.active_tasks = {f"t{i}": None for i in range(4)}
        bid2 = await mock_agent.bid_on_task(cfp)
        confidence2 = bid2["confidence"]
        
        # Confidence should be lower with high load
        assert confidence2 < confidence1
    
    async def test_no_bid_if_cannot_handle(self, mock_agent):
        """No bid submitted if can't handle task"""
        cfp = {
            "task_id": "t1",
            "task_type": "unsupported_task",
            "requirements": {}
        }
        
        bid = await mock_agent.bid_on_task(cfp)
        assert bid is None


# Run tests
# pytest backend/tests/unit/test_base_agent.py -v --cov=backend/agents/base_agent
```

#### Evolution Agent Unit Tests

**File:** `backend/tests/unit/test_evolution_agent.py`

```python
import pytest
from backend.agents.evolution_agent import EvolutionAgent


@pytest.fixture
async def evolution_agent():
    """Create Evolution Agent with mocked LLM"""
    # Mock LLM to return test code
    llm = AsyncMock()
    llm.generate.return_value = {
        "text": "import pytest\n\ndef test_example():\n    assert True",
        "token_usage": 1500
    }
    
    agent = EvolutionAgent(
        agent_id="evolution_1",
        agent_type="evolution",
        priority=9,
        redis_client=AsyncMock(),
        message_queue=AsyncMock(),
        llm_client=llm,
        vector_db=AsyncMock(),
        registry=AsyncMock(),
        config={"max_concurrent_tasks": 5}
    )
    
    yield agent


@pytest.mark.asyncio
class TestEvolutionAgentCapabilities:
    """Test Evolution Agent capabilities"""
    
    async def test_declares_test_generation_capability(self, evolution_agent):
        """Agent declares test_generation capability"""
        caps = evolution_agent.capabilities
        cap_names = [c.name for c in caps]
        assert "test_generation" in cap_names
    
    async def test_declares_mutation_testing_capability(self, evolution_agent):
        """Agent declares mutation_testing capability"""
        caps = evolution_agent.capabilities
        cap_names = [c.name for c in caps]
        assert "mutation_testing" in cap_names


@pytest.mark.asyncio
class TestEvolutionAgentTestGeneration:
    """Test test generation functionality"""
    
    async def test_generates_valid_test_code(self, evolution_agent):
        """Generates syntactically valid pytest code"""
        task = TaskContext(
            task_id="t1",
            task_type="test_generation",
            payload={
                "class_name": "UserService",
                "coverage_target": 0.85
            },
            conversation_id="c1"
        )
        
        result = await evolution_agent.execute_task(task)
        
        assert result.success is True
        assert "tests" in result.result
        assert "import pytest" in result.result["tests"]
    
    async def test_uses_memory_for_context(self, evolution_agent):
        """Uses memory system to retrieve context"""
        # Mock memory system
        evolution_agent.memory = AsyncMock()
        evolution_agent.memory.get_context.return_value = "Previous patterns: Factory method"
        
        task = TaskContext(
            task_id="t1",
            task_type="test_generation",
            payload={"class_name": "UserService"},
            conversation_id="c1"
        )
        
        await evolution_agent.execute_task(task)
        
        # Should have queried memory
        evolution_agent.memory.get_context.assert_called_once()
    
    async def test_stores_success_in_memory(self, evolution_agent):
        """Stores successful generation in long-term memory"""
        evolution_agent.memory = AsyncMock()
        
        task = TaskContext(
            task_id="t1",
            task_type="test_generation",
            payload={"class_name": "UserService"},
            conversation_id="c1"
        )
        
        await evolution_agent.execute_task(task)
        
        # Should have stored in memory
        evolution_agent.memory.store.assert_called_once()
        call_args = evolution_agent.memory.store.call_args
        assert "UserService" in call_args[1]["content"]
```

---

## 2. Integration Tests (20%)

### Agent-to-Agent Communication

**File:** `backend/tests/integration/test_agent_communication.py`

```python
import pytest
import asyncio
from backend.agents.observation_agent import ObservationAgent
from backend.agents.requirements_agent import RequirementsAgent
from backend.infrastructure.message_bus import MessageBus


@pytest.mark.integration
@pytest.mark.asyncio
async def test_observation_to_requirements_workflow():
    """Test message passing from Observation → Requirements Agent"""
    # Setup real Redis (or Redis mock)
    bus = MessageBus("redis://localhost:6379")
    
    # Create agents
    obs_agent = ObservationAgent(...)
    req_agent = RequirementsAgent(...)
    
    await obs_agent.start()
    await req_agent.start()
    
    # Observation Agent detects pattern
    pattern = {
        "type": "factory_method",
        "location": "src/services/user_service.py",
        "confidence": 0.87
    }
    
    # Publish event
    await obs_agent.publish_event("pattern_detected", pattern)
    
    # Requirements Agent should receive and process
    await asyncio.sleep(0.5)  # Allow propagation
    
    # Verify Requirements Agent received pattern
    # (Check logs or internal state)
    
    await obs_agent.stop()
    await req_agent.stop()
```

### End-to-End Test Generation

**File:** `backend/tests/integration/test_e2e_test_generation.py`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_test_generation_pipeline():
    """Full pipeline: Observe → Requirements → Analysis → Evolution → Report"""
    
    # Start all agents
    agents = await start_all_agents()
    
    # Trigger test generation
    response = await http_client.post('/api/v2/tests/generate', json={
        "repository_url": "https://github.com/test/repo",
        "target_files": ["src/user_service.py"],
        "coverage_target": 0.85
    })
    
    task_id = response.json()["task_id"]
    
    # Poll for completion (max 60 seconds)
    for _ in range(60):
        result = await http_client.get(f'/api/v2/tests/generate/{task_id}')
        if result.json()["status"] == "completed":
            break
        await asyncio.sleep(1)
    
    # Verify result
    assert result.json()["status"] == "completed"
    assert "tests" in result.json()["result"]
    assert result.json()["result"]["coverage_estimate"] >= 0.80
    
    # Cleanup
    await stop_all_agents(agents)
```

---

## 3. System Tests (8%)

### Load Testing

**File:** `backend/tests/system/test_load.py`

```python
import pytest
import asyncio
from locust import HttpUser, task, between


class TestGenerationUser(HttpUser):
    """Simulated user for load testing"""
    wait_time = between(1, 5)
    
    @task
    def generate_tests(self):
        self.client.post('/api/v2/tests/generate', json={
            "repository_url": "https://github.com/test/repo",
            "target_files": ["src/test.py"],
            "coverage_target": 0.80
        })


# Run: locust -f backend/tests/system/test_load.py --users 100 --spawn-rate 10 --run-time 10m
```

**Target Metrics:**
- **100 concurrent users:** P95 latency <30s
- **500 requests/minute sustained:** No errors
- **1000+ requests total:** <1% failure rate

### Resilience Testing

**File:** `backend/tests/system/test_resilience.py`

```python
@pytest.mark.system
@pytest.mark.asyncio
async def test_agent_failure_recovery():
    """System recovers when agent fails"""
    agents = await start_all_agents()
    
    # Kill Evolution Agent mid-task
    evolution_agent = agents["evolution"]
    task = asyncio.create_task(evolution_agent.execute_task(...))
    await asyncio.sleep(0.5)
    await evolution_agent.stop()  # Simulate crash
    
    # Start replacement agent
    new_evolution_agent = EvolutionAgent(...)
    await new_evolution_agent.start()
    
    # Task should be picked up by new agent
    # Verify task eventually completes
```

---

## 4. Chaos Engineering (2%)

### Chaos Scenarios

**File:** `backend/tests/chaos/test_chaos_scenarios.py`

```python
import pytest
from chaos_toolkit import run_experiment


@pytest.mark.chaos
def test_redis_failure():
    """System handles Redis failure gracefully"""
    experiment = {
        "title": "Redis Failure",
        "description": "Kill Redis and verify agents reconnect",
        "steady-state-hypothesis": {
            "title": "All agents healthy",
            "probes": [
                {
                    "type": "http",
                    "url": "http://localhost:8000/api/v2/agents",
                    "expect": [200],
                    "tolerance": {"status": 200}
                }
            ]
        },
        "method": [
            {
                "type": "action",
                "name": "kill-redis",
                "provider": {
                    "type": "process",
                    "command": "docker stop redis"
                }
            },
            {
                "type": "probe",
                "name": "check-agents",
                "provider": {
                    "type": "http",
                    "url": "http://localhost:8000/api/v2/agents"
                },
                "tolerance": {
                    "status": [200, 503]  # Some degradation acceptable
                }
            },
            {
                "type": "action",
                "name": "restart-redis",
                "provider": {
                    "type": "process",
                    "command": "docker start redis"
                }
            },
            {
                "type": "probe",
                "name": "verify-recovery",
                "provider": {
                    "type": "http",
                    "url": "http://localhost:8000/api/v2/agents"
                },
                "tolerance": {"status": 200}
            }
        ]
    }
    
    run_experiment(experiment)


@pytest.mark.chaos
def test_network_partition():
    """System handles network partition between agents"""
    # Inject network latency/packet loss using tc (traffic control)
    # Verify agents timeout and retry correctly


@pytest.mark.chaos
def test_cascading_failure():
    """One agent failure doesn't cascade"""
    # Kill Evolution Agent
    # Verify Orchestration Agent circuits break
    # Verify other agents continue functioning
```

---

## 🎯 Test Coverage Goals

### By Sprint

| Sprint | Unit Tests | Integration Tests | System Tests | Coverage % |
|--------|------------|-------------------|--------------|------------|
| Sprint 7 | 150+ | 10+ | 0 | 85% |
| Sprint 8 | 250+ | 25+ | 2 | 90% |
| Sprint 9 | 350+ | 40+ | 5 | 92% |
| Sprint 10 | 450+ | 55+ | 8 | 94% |
| Sprint 11 | 500+ | 65+ | 12 | 95% |
| Sprint 12 | 550+ | 70+ | 15 | 95%+ |

---

## 🚀 CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Phase 3 Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements-test.txt
      - run: pytest backend/tests/unit -v --cov=backend --cov-report=xml
      - uses: codecov/codecov-action@v3
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v3
      - run: pytest backend/tests/integration -v
  
  system-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - run: pytest backend/tests/system -v --timeout=600
```

---

## ✅ Success Criteria

**Phase 3 Ready for Production When:**
- ✅ 95%+ code coverage
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ System tests pass (load + resilience)
- ✅ Chaos tests pass 3 consecutive runs
- ✅ No critical security vulnerabilities (OWASP scan)
- ✅ <5% change failure rate (last 20 deployments)

---

**END OF TESTING STRATEGY**
