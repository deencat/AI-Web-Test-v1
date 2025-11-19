# AI-Web-Test v1 - Integration & End-to-End Testing Architecture

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-01-31
- **Status**: Architecture Specification
- **Related Documents**: 
  - [PRD](../AI-Web-Test-v1-PRD.md)
  - [SRS](../AI-Web-Test-v1-SRS.md)
  - [Deployment & Resilience](./AI-Web-Test-v1-Deployment-Resilience.md)

---

## Executive Summary

This document defines the **comprehensive integration and end-to-end testing architecture** for the AI-Web-Test v1 platform, implementing multi-agent integration tests, contract tests, chaos engineering, and performance testing.

### Key Testing Capabilities

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Integration Tests** | pytest + pytest-asyncio | Test agent-to-agent communication |
| **Contract Tests** | Pact / Custom | Validate agent message schemas |
| **Chaos Testing** | Chaos Mesh | Test resilience under failures |
| **Performance Tests** | Locust + k6 | Load testing, stress testing |
| **E2E Tests** | Playwright | Full workflow testing |
| **API Tests** | pytest + httpx | API endpoint testing |
| **Test Orchestration** | pytest-xdist | Parallel test execution |

### Implementation Timeline
- **Total Effort**: 8 days
- **Phase 1** (Days 1-3): Integration Tests + Contract Tests
- **Phase 2** (Days 4-6): Chaos Testing + Performance Tests
- **Phase 3** (Days 7-8): E2E Tests + CI/CD Integration

---

## Table of Contents
1. [Testing Architecture](#testing-architecture)
2. [Multi-Agent Integration Tests](#multi-agent-integration-tests)
3. [Contract Testing](#contract-testing)
4. [Chaos Engineering](#chaos-engineering)
5. [Performance Testing](#performance-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Test Infrastructure](#test-infrastructure)
8. [CI/CD Integration](#cicd-integration)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Summary & Integration](#summary--integration)

---

## Testing Architecture

### Overview
Comprehensive testing ensures multi-agent system reliability, performance, and resilience.

```mermaid
graph TB
    subgraph "Testing Pyramid"
        E2E[E2E Tests - Playwright]
        Integration[Integration Tests - Multi-Agent]
        Contract[Contract Tests - Message Schemas]
        Unit[Unit Tests - pytest]
    end
    
    subgraph "Specialized Testing"
        Chaos[Chaos Testing - Chaos Mesh]
        Performance[Performance Tests - Locust + k6]
        Security[Security Tests - OWASP ZAP]
    end
    
    subgraph "CI/CD Pipeline"
        CI[GitHub Actions / Jenkins]
        TestEnv[Test Environment]
        Reports[Test Reports - Allure]
    end
    
    Unit --> Integration
    Integration --> Contract
    Contract --> E2E
    
    Chaos --> TestEnv
    Performance --> TestEnv
    E2E --> TestEnv
    
    TestEnv --> CI
    CI --> Reports
```

### Testing Levels

| Level | Technology | Coverage | Execution Time |
|-------|-----------|----------|----------------|
| **Unit Tests** | pytest | 80% code coverage | <5 min |
| **Integration Tests** | pytest + docker | Agent coordination | <15 min |
| **Contract Tests** | Pact / Custom | Message schemas | <10 min |
| **E2E Tests** | Playwright | Full workflows | <30 min |
| **Chaos Tests** | Chaos Mesh | Resilience | <20 min |
| **Performance Tests** | Locust + k6 | Load/Stress | <60 min |

---

## Multi-Agent Integration Tests

### 1.1 Agent-to-Agent Communication Tests

**Test Complete Workflow**:
```python
# tests/integration/test_multi_agent_workflow.py
import pytest
from datetime import datetime
from app.agents import (
    RequirementsAgent,
    GenerationAgent,
    ExecutionAgent,
    ObservationAgent,
    AnalysisAgent
)
from app.messaging import MessageBus

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_test_generation_workflow():
    """Test complete workflow from requirements to test execution"""
    
    # Setup
    message_bus = MessageBus()
    req_agent = RequirementsAgent(message_bus)
    gen_agent = GenerationAgent(message_bus)
    exec_agent = ExecutionAgent(message_bus)
    obs_agent = ObservationAgent(message_bus)
    analysis_agent = AnalysisAgent(message_bus)
    
    workflow_id = f"workflow_{datetime.utcnow().timestamp()}"
    
    # 1. Requirements Agent analyzes input
    sample_prd = {
        "title": "User Login",
        "description": "Test user login with valid and invalid credentials"
    }
    
    req_result = await req_agent.process(
        input_data=sample_prd,
        workflow_id=workflow_id
    )
    
    assert req_result is not None
    assert req_result.confidence > 0.85
    assert len(req_result.scenarios) >= 2  # At least 2 scenarios (valid, invalid)
    
    # 2. Generation Agent creates tests
    gen_result = await gen_agent.process(
        scenarios=req_result.scenarios,
        workflow_id=workflow_id
    )
    
    assert gen_result is not None
    assert len(gen_result.tests) > 0
    assert all(test.code is not None for test in gen_result.tests)
    
    # 3. Execution Agent runs tests
    exec_result = await exec_agent.execute(
        tests=gen_result.tests,
        workflow_id=workflow_id
    )
    
    assert exec_result is not None
    assert exec_result.status == 'completed'
    assert exec_result.total_tests == len(gen_result.tests)
    
    # 4. Observation Agent monitors execution
    obs_result = await obs_agent.observe(
        execution_id=exec_result.execution_id,
        workflow_id=workflow_id
    )
    
    assert obs_result is not None
    assert obs_result.anomalies_detected is not None
    
    # 5. Analysis Agent analyzes results
    analysis_result = await analysis_agent.analyze(
        execution_result=exec_result,
        observation_data=obs_result,
        workflow_id=workflow_id
    )
    
    assert analysis_result is not None
    assert analysis_result.pass_rate is not None
    
    # 6. Verify message passing
    messages = await message_bus.get_messages(workflow_id=workflow_id)
    
    assert len(messages) >= 5  # At least 5 agent interactions
    
    # Verify message order
    message_types = [msg.message_type for msg in messages]
    assert 'requirements_analyzed' in message_types
    assert 'tests_generated' in message_types
    assert 'tests_executed' in message_types
    assert 'execution_observed' in message_types
    assert 'results_analyzed' in message_types

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_failure_handling():
    """Test system handles agent failures gracefully"""
    
    message_bus = MessageBus()
    req_agent = RequirementsAgent(message_bus)
    
    # Simulate agent failure
    with pytest.raises(Exception):
        await req_agent.process(
            input_data=None,  # Invalid input
            workflow_id="test_failure"
        )
    
    # Verify error message was published
    messages = await message_bus.get_messages(workflow_id="test_failure")
    error_messages = [msg for msg in messages if msg.message_type == 'agent_error']
    
    assert len(error_messages) > 0
    assert error_messages[0].payload['error_type'] is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_agent_workflows():
    """Test multiple workflows running concurrently"""
    
    message_bus = MessageBus()
    req_agent = RequirementsAgent(message_bus)
    
    # Start 10 concurrent workflows
    workflows = []
    for i in range(10):
        workflow_id = f"workflow_{i}"
        result = req_agent.process(
            input_data={"title": f"Test {i}"},
            workflow_id=workflow_id
        )
        workflows.append(result)
    
    # Wait for all to complete
    results = await asyncio.gather(*workflows)
    
    # Verify all completed successfully
    assert all(result is not None for result in results)
    assert all(result.confidence > 0.7 for result in results)
```

### 1.2 Message Bus Integration Tests

**Test Message Delivery**:
```python
# tests/integration/test_message_bus.py
import pytest
from app.messaging import MessageBus, Message

@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_delivery():
    """Test messages are delivered to correct subscribers"""
    
    message_bus = MessageBus()
    
    # Subscribe to messages
    received_messages = []
    
    async def subscriber(message: Message):
        received_messages.append(message)
    
    await message_bus.subscribe(
        message_type='test_generated',
        subscriber=subscriber
    )
    
    # Publish message
    await message_bus.publish(
        message_type='test_generated',
        payload={'test_id': 'TEST-000001'},
        sender_id='generation_agent',
        receiver_id='execution_agent'
    )
    
    # Wait for delivery
    await asyncio.sleep(0.1)
    
    # Verify delivery
    assert len(received_messages) == 1
    assert received_messages[0].payload['test_id'] == 'TEST-000001'

@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_ordering():
    """Test messages are processed in order"""
    
    message_bus = MessageBus()
    
    processed_order = []
    
    async def subscriber(message: Message):
        processed_order.append(message.sequence_number)
    
    await message_bus.subscribe(
        message_type='test_event',
        subscriber=subscriber
    )
    
    # Publish 10 messages
    for i in range(10):
        await message_bus.publish(
            message_type='test_event',
            payload={'sequence': i},
            sender_id='test'
        )
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Verify order
    assert processed_order == list(range(10))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_persistence():
    """Test messages are persisted to database"""
    
    message_bus = MessageBus()
    
    # Publish message
    message_id = await message_bus.publish(
        message_type='test_event',
        payload={'data': 'test'},
        sender_id='agent_1',
        receiver_id='agent_2'
    )
    
    # Retrieve from database
    db_message = await db.query(AgentMessage).filter(
        AgentMessage.id == message_id
    ).first()
    
    assert db_message is not None
    assert db_message.message_type == 'test_event'
    assert db_message.sender_id == 'agent_1'
    assert db_message.receiver_id == 'agent_2'
```

---

## Contract Testing

### 2.1 Agent Message Schema Validation

**Define Message Contracts**:
```python
# app/contracts/agent_messages.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RequirementsAnalyzedMessage(BaseModel):
    """Contract for requirements_analyzed message"""
    message_type: str = Field(..., regex='^requirements_analyzed$')
    workflow_id: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    scenarios: List[dict] = Field(..., min_items=1)
    timestamp: datetime
    sender_id: str = Field(..., regex='^requirements_agent')
    
    class Config:
        schema_extra = {
            "example": {
                "message_type": "requirements_analyzed",
                "workflow_id": "workflow_123",
                "confidence": 0.92,
                "scenarios": [
                    {"title": "Valid login", "priority": "high"}
                ],
                "timestamp": "2025-01-31T10:00:00Z",
                "sender_id": "requirements_agent_001"
            }
        }

class TestsGeneratedMessage(BaseModel):
    """Contract for tests_generated message"""
    message_type: str = Field(..., regex='^tests_generated$')
    workflow_id: str = Field(..., min_length=1)
    tests: List[dict] = Field(..., min_items=1)
    generation_time_ms: float = Field(..., gt=0)
    timestamp: datetime
    sender_id: str = Field(..., regex='^generation_agent')
    receiver_id: str = Field(..., regex='^execution_agent')

class TestsExecutedMessage(BaseModel):
    """Contract for tests_executed message"""
    message_type: str = Field(..., regex='^tests_executed$')
    workflow_id: str = Field(..., min_length=1)
    execution_id: str = Field(..., min_length=1)
    total_tests: int = Field(..., gt=0)
    passed: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    execution_time_ms: float = Field(..., gt=0)
    timestamp: datetime
    sender_id: str = Field(..., regex='^execution_agent')
```

**Contract Tests**:
```python
# tests/contract/test_agent_contracts.py
import pytest
from app.contracts.agent_messages import (
    RequirementsAnalyzedMessage,
    TestsGeneratedMessage,
    TestsExecutedMessage
)
from app.agents import RequirementsAgent, GenerationAgent

@pytest.mark.contract
@pytest.mark.asyncio
async def test_requirements_agent_message_contract():
    """Test Requirements Agent produces valid contract messages"""
    
    agent = RequirementsAgent()
    
    result = await agent.process(
        input_data={"title": "Test login"},
        workflow_id="test_workflow"
    )
    
    # Verify message adheres to contract
    message = result.to_message()
    
    try:
        RequirementsAnalyzedMessage(**message)
    except ValidationError as e:
        pytest.fail(f"Message does not adhere to contract: {e}")

@pytest.mark.contract
@pytest.mark.asyncio
async def test_generation_agent_message_contract():
    """Test Generation Agent produces valid contract messages"""
    
    agent = GenerationAgent()
    
    result = await agent.process(
        scenarios=[{"title": "Test scenario"}],
        workflow_id="test_workflow"
    )
    
    message = result.to_message()
    
    try:
        TestsGeneratedMessage(**message)
    except ValidationError as e:
        pytest.fail(f"Message does not adhere to contract: {e}")

@pytest.mark.contract
@pytest.mark.asyncio
async def test_contract_backward_compatibility():
    """Test old messages still validate with new contracts"""
    
    # Old message format (v1.0)
    old_message = {
        "message_type": "requirements_analyzed",
        "workflow_id": "workflow_123",
        "confidence": 0.92,
        "scenarios": [{"title": "Test"}],
        "timestamp": "2025-01-31T10:00:00Z",
        "sender_id": "requirements_agent_001"
    }
    
    # Should still validate with current contract
    try:
        RequirementsAnalyzedMessage(**old_message)
    except ValidationError as e:
        pytest.fail(f"Backward compatibility broken: {e}")
```

### 2.2 Pact Contract Testing

**Producer (Requirements Agent)**:
```python
# tests/contract/test_requirements_agent_pact.py
import pytest
from pact import Consumer, Provider

pact = Consumer('ExecutionAgent').has_pact_with(Provider('RequirementsAgent'))

@pytest.mark.contract
def test_requirements_agent_pact():
    """Test Requirements Agent contract with Pact"""
    
    expected = {
        'message_type': 'requirements_analyzed',
        'workflow_id': 'workflow_123',
        'confidence': 0.92
    }
    
    (pact
     .given('requirements are analyzed')
     .upon_receiving('a requirements analyzed message')
     .with_request('POST', '/messages')
     .will_respond_with(200, body=expected))
    
    with pact:
        # Test actual agent
        result = requirements_agent.process(...)
        assert result['confidence'] == 0.92
```

---

## Chaos Engineering

### 3.1 Chaos Mesh Experiments

**Agent Failure Scenarios**:
```yaml
# tests/chaos/pod-kill-generation-agent.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: agent-failure-test
  namespace: aiwebtest
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - aiwebtest
    labelSelectors:
      app: generation-agent
  scheduler:
    cron: '@every 5m'
```

**Network Latency Test**:
```yaml
# tests/chaos/network-latency.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-latency-test
  namespace: aiwebtest
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - aiwebtest
    labelSelectors:
      app: backend
  delay:
    latency: "500ms"
    correlation: "25"
    jitter: "50ms"
  duration: "5m"
```

**Database Failure Test**:
```yaml
# tests/chaos/database-partition.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: database-partition
  namespace: aiwebtest
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - aiwebtest
    labelSelectors:
      app: postgres
  direction: both
  duration: "30s"
```

### 3.2 Chaos Testing with Python

**Chaos Toolkit**:
```python
# tests/chaos/experiments/agent_failure.py
from chaoslib.types import Configuration, Secrets
from kubernetes import client, config

def kill_generation_agent(configuration: Configuration, secrets: Secrets):
    """Kill Generation Agent pod to test resilience"""
    
    config.load_kube_config()
    v1 = client.CoreV1Api()
    
    # Find Generation Agent pod
    pods = v1.list_namespaced_pod(
        namespace='aiwebtest',
        label_selector='app=generation-agent'
    )
    
    if pods.items:
        pod_name = pods.items[0].metadata.name
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace='aiwebtest'
        )
        
        return {
            "killed_pod": pod_name,
            "timestamp": datetime.utcnow().isoformat()
        }

def verify_system_continues_functioning(
    configuration: Configuration,
    secrets: Secrets
) -> bool:
    """Verify system continues to function after agent failure"""
    
    # Wait for pod to restart
    time.sleep(30)
    
    # Try to generate tests
    response = requests.post(
        'http://api.aiwebtest.local/api/tests/generate',
        json={'requirements': 'Test user login'}
    )
    
    return response.status_code == 200

# Experiment definition
{
    "title": "Generation Agent Failure Resilience",
    "description": "Verify system continues when Generation Agent fails",
    "steady-state-hypothesis": {
        "title": "System is functioning",
        "probes": [
            {
                "name": "system_responds",
                "type": "probe",
                "tolerance": True,
                "provider": {
                    "type": "python",
                    "module": "experiments.agent_failure",
                    "func": "verify_system_continues_functioning"
                }
            }
        ]
    },
    "method": [
        {
            "name": "kill_generation_agent",
            "type": "action",
            "provider": {
                "type": "python",
                "module": "experiments.agent_failure",
                "func": "kill_generation_agent"
            }
        }
    ]
}
```

---

## Performance Testing

### 4.1 Load Testing with Locust

**Locust Test**:
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class AIWebTestUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()['access_token']
    
    @task(3)
    def generate_tests(self):
        """Test generation endpoint (most common)"""
        self.client.post(
            "/api/tests/generate",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "requirements_text": "Test user login with valid credentials",
                "test_types": ["unit", "integration"],
                "max_tests": 10
            },
            name="Generate Tests"
        )
    
    @task(2)
    def execute_tests(self):
        """Test execution endpoint"""
        self.client.post(
            "/api/tests/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "test_ids": ["TEST-000001", "TEST-000002"]
            },
            name="Execute Tests"
        )
    
    @task(1)
    def get_test_results(self):
        """Get test results endpoint"""
        self.client.get(
            "/api/tests/executions?limit=50",
            headers={"Authorization": f"Bearer {self.token}"},
            name="Get Test Results"
        )

# Run with: locust -f locustfile.py --host=http://localhost:8000
# Web UI: http://localhost:8089
# CLI: locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

### 4.2 Stress Testing with k6

**k6 Test**:
```javascript
// tests/performance/stress_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 for 5 minutes
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 for 5 minutes
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
    errors: ['rate<0.1'],              // Error rate < 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export function setup() {
  // Login and get token
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    username: 'test_user',
    password: 'test_password',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  return { token: loginRes.json('access_token') };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`,
  };
  
  // Test generation request
  const genRes = http.post(
    `${BASE_URL}/api/tests/generate`,
    JSON.stringify({
      requirements_text: 'Test user login',
      test_types: ['unit'],
      max_tests: 5,
    }),
    { headers }
  );
  
  check(genRes, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
    'has tests': (r) => JSON.parse(r.body).tests.length > 0,
  }) || errorRate.add(1);
  
  sleep(1);
}

// Run with: k6 run stress_test.js
```

### 4.3 Spike Testing

**k6 Spike Test**:
```javascript
// tests/performance/spike_test.js
export const options = {
  stages: [
    { duration: '1m', target: 50 },    // Baseline
    { duration: '10s', target: 500 },  // Sudden spike!
    { duration: '3m', target: 500 },   // Sustain spike
    { duration: '10s', target: 50 },   // Drop back
    { duration: '1m', target: 0 },     // Ramp down
  ],
};

export default function (data) {
  // Same test logic as stress_test.js
}

// Run with: k6 run spike_test.js
```

---

## End-to-End Testing

### 5.1 Playwright E2E Tests

**Full Workflow Test**:
```typescript
// tests/e2e/test_full_workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Complete Test Generation Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="username"]', 'test_user');
    await page.fill('input[name="password"]', 'test_password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('http://localhost:3000/dashboard');
  });
  
  test('should generate and execute tests from requirements', async ({ page }) => {
    // Navigate to test generation
    await page.click('a[href="/tests/generate"]');
    await expect(page).toHaveURL('http://localhost:3000/tests/generate');
    
    // Input requirements
    await page.fill('textarea[name="requirements"]', 
      'Test user login with valid and invalid credentials');
    
    // Select test types
    await page.check('input[value="unit"]');
    await page.check('input[value="integration"]');
    
    // Generate tests
    await page.click('button:has-text("Generate Tests")');
    
    // Wait for generation (with AI, may take 30s)
    await page.waitForSelector('.test-list', { timeout: 60000 });
    
    // Verify tests were generated
    const testItems = await page.locator('.test-item').count();
    expect(testItems).toBeGreaterThan(0);
    
    // Check first test
    const firstTest = page.locator('.test-item').first();
    await expect(firstTest).toContainText('TEST-');
    
    // Execute tests
    await page.click('button:has-text("Execute All")');
    
    // Wait for execution
    await page.waitForSelector('.execution-results', { timeout: 120000 });
    
    // Verify results
    await expect(page.locator('.execution-status')).toContainText('Completed');
    
    // Check pass/fail counts
    const passCount = await page.locator('.passed-count').textContent();
    const failCount = await page.locator('.failed-count').textContent();
    
    expect(parseInt(passCount!)).toBeGreaterThanOrEqual(0);
    expect(parseInt(failCount!)).toBeGreaterThanOrEqual(0);
    
    // View test details
    await firstTest.click();
    await expect(page.locator('.test-details')).toBeVisible();
    await expect(page.locator('.test-code')).toBeVisible();
  });
  
  test('should show agent activity in real-time', async ({ page }) => {
    // Navigate to agent monitoring
    await page.click('a[href="/agents/monitor"]');
    
    // Verify agent status
    const agents = ['requirements', 'generation', 'execution', 'observation', 'analysis', 'evolution'];
    
    for (const agent of agents) {
      const agentStatus = page.locator(`[data-agent="${agent}"] .status`);
      await expect(agentStatus).toContainText(/active|idle/);
    }
    
    // Generate tests to trigger agent activity
    await page.goto('http://localhost:3000/tests/generate');
    await page.fill('textarea[name="requirements"]', 'Test simple workflow');
    await page.click('button:has-text("Generate Tests")');
    
    // Go back to monitoring
    await page.goto('http://localhost:3000/agents/monitor');
    
    // Verify agent activity updates
    const reqAgentActivity = page.locator('[data-agent="requirements"] .activity');
    await expect(reqAgentActivity).toContainText(/analyzing|completed/, { timeout: 30000 });
  });
});
```

---

## Test Infrastructure

### 6.1 Test Environment Setup

**Docker Compose for Testing**:
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres_test:
    image: postgres:15
    environment:
      POSTGRES_DB: aiwebtest_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
  
  redis_test:
    image: redis:7
    ports:
      - "6380:6379"
  
  backend_test:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://test_user:test_password@postgres_test:5432/aiwebtest_test
      REDIS_URL: redis://redis_test:6379
      TESTING: "true"
    ports:
      - "8001:8000"
    depends_on:
      - postgres_test
      - redis_test
    command: pytest tests/ -v

# Run with: docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 6.2 Test Data Management

**Test Fixtures**:
```python
# tests/fixtures/database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope='session')
def test_db():
    """Create test database"""
    engine = create_engine('postgresql://test_user:test_password@localhost:5433/aiwebtest_test')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def sample_user(test_db):
    """Create sample user"""
    user = User(
        username='test_user',
        email='test@example.com',
        password_hash=hash_password('test_password'),
        role='qa_engineer'
    )
    test_db.add(user)
    test_db.commit()
    
    yield user
    
    test_db.delete(user)
    test_db.commit()

@pytest.fixture
def sample_test_case(test_db, sample_user):
    """Create sample test case"""
    test_case = TestCase(
        test_id='TEST-000001',
        title='Test user login',
        description='Verify user can login with valid credentials',
        test_type='integration',
        created_by=sample_user.id
    )
    test_db.add(test_case)
    test_db.commit()
    
    yield test_case
    
    test_db.delete(test_case)
    test_db.commit()
```

---

## CI/CD Integration

### 7.1 GitHub Actions Workflow

**Comprehensive Test Pipeline**:
```yaml
# .github/workflows/test.yml
name: Test Suite

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
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        run: pytest tests/unit -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: aiwebtest_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/aiwebtest_test
          REDIS_URL: redis://localhost:6379
        run: pytest tests/integration -v --maxfail=5
  
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      
      - name: Run contract tests
        run: pytest tests/contract -v
  
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Playwright
        run: |
          npm install -D @playwright/test
          npx playwright install --with-deps
      
      - name: Start services
        run: docker-compose -f docker-compose.test.yml up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run E2E tests
        run: npx playwright test tests/e2e
      
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
  
  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Locust
        run: pip install locust
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run load tests
        run: |
          locust -f tests/performance/locustfile.py \
            --host=http://localhost:8000 \
            --users 50 \
            --spawn-rate 5 \
            --run-time 5m \
            --headless \
            --csv=performance_results
      
      - name: Upload performance results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: performance_results*.csv
```

---

## Implementation Roadmap

### Phase 1: Integration Tests + Contract Tests (Days 1-3)

#### Day 1: Integration Test Framework
- [ ] Set up pytest with pytest-asyncio
- [ ] Create test database fixtures
- [ ] Implement multi-agent workflow tests
- [ ] Test agent-to-agent communication

**Deliverables**: `tests/integration/` (500 lines)

#### Day 2: Message Bus Tests
- [ ] Test message delivery
- [ ] Test message ordering
- [ ] Test message persistence
- [ ] Test concurrent workflows

**Deliverables**: `tests/integration/test_message_bus.py` (300 lines)

#### Day 3: Contract Tests
- [ ] Define message contracts (Pydantic)
- [ ] Implement contract validation tests
- [ ] Test backward compatibility
- [ ] Optional: Set up Pact

**Deliverables**: `app/contracts/` (400 lines), `tests/contract/` (300 lines)

### Phase 2: Chaos + Performance Tests (Days 4-6)

#### Day 4: Chaos Engineering Setup
- [ ] Install Chaos Mesh on Kubernetes
- [ ] Create pod-kill experiments
- [ ] Create network latency experiments
- [ ] Test database partition scenarios

**Deliverables**: `tests/chaos/` (400 lines YAML + Python)

#### Day 5: Load Testing
- [ ] Set up Locust
- [ ] Create load test scenarios
- [ ] Test with 100 concurrent users
- [ ] Analyze performance bottlenecks

**Deliverables**: `tests/performance/locustfile.py` (300 lines)

#### Day 6: Stress & Spike Testing
- [ ] Set up k6
- [ ] Create stress test (ramp to failure)
- [ ] Create spike test (sudden load)
- [ ] Document performance thresholds

**Deliverables**: `tests/performance/*.js` (400 lines)

### Phase 3: E2E Tests + CI/CD (Days 7-8)

#### Day 7: E2E Tests
- [ ] Set up Playwright
- [ ] Test complete workflows (UI)
- [ ] Test agent monitoring dashboard
- [ ] Test error scenarios

**Deliverables**: `tests/e2e/` (600 lines TypeScript)

#### Day 8: CI/CD Integration
- [ ] Create GitHub Actions workflow
- [ ] Integrate all test types
- [ ] Set up test reporting (Allure)
- [ ] Document testing procedures

**Deliverables**: `.github/workflows/test.yml` (300 lines), `documentation/TESTING-GUIDE.md` (500 lines)

---

## Cost Analysis

### Infrastructure Costs (Monthly)
| Component | Cost | Notes |
|-----------|------|-------|
| Test Environment | $50-100 | Dedicated K8s namespace for testing |
| Chaos Mesh | $0 | Open-source |
| Locust | $0 | Open-source |
| k6 | $0 | Open-source (Cloud optional: $49+/mo) |
| Playwright | $0 | Open-source |
| CI/CD Minutes (GitHub Actions) | $0-50 | Free tier (2,000 min/mo) or paid |
| **Total** | **$50-150/month** | Mostly test infrastructure |

### ROI Analysis
- **Cost of production bugs**: $10,000 - $100,000+ (downtime, hotfixes, reputation)
- **Cost of comprehensive testing**: $50-150/month
- **Break-even**: Catching 1 critical bug = 67-2,000 months of testing investment

**Conclusion**: Comprehensive testing prevents costly production incidents!

---

## Summary & Integration

### Key Achievements

✅ **Multi-Agent Integration Tests**: Test agent-to-agent communication and workflows  
✅ **Contract Tests**: Validate agent message schemas with Pydantic  
✅ **Chaos Engineering**: Test resilience with Chaos Mesh  
✅ **Performance Tests**: Load, stress, spike testing with Locust + k6  
✅ **E2E Tests**: Full workflow testing with Playwright  
✅ **CI/CD Integration**: Automated testing in GitHub Actions  

### Integration with Other Components

| Component | Integration Point |
|-----------|------------------|
| **Deployment** | Chaos tests validate resilience, health checks during tests |
| **ML Monitoring** | Performance tests for ML inference, contract tests for predictions |
| **Database** | Integration tests validate queries, performance tests for database load |
| **Security** | Security tests (OWASP ZAP), penetration tests |

### Next Steps

1. **Review** this Integration Testing architecture document
2. **Update PRD** with integration testing functional requirement
3. **Update SRS** with enhanced testing stack
4. **Begin Phase 1** implementation (Days 1-3)

---

**End of Integration & End-to-End Testing Architecture Document**

This architecture provides **comprehensive testing coverage** for the AI-Web-Test v1 platform, ensuring multi-agent system reliability, performance, and resilience.

