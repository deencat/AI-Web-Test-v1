# Phase 3: Multi-Agent Test Generation System

**Branch:** `feature/phase3-agent-foundation`  
**Developer:** Developer A  
**Status:** 🚧 In Progress (3/6 tasks complete)  
**Progress:** 16/26 story points (61% complete)

---

## 📊 Task Progress

| Task | Description | Status | Points | Files Created |
|------|-------------|--------|--------|---------------|
| ✅ EA.1 | BaseAgent abstract class | COMPLETE | 8 | `agents/base_agent.py` (450 lines) |
| ✅ EA.2 | MessageBus stub | COMPLETE | 5 | `messaging/message_bus_stub.py` (300 lines) |
| ✅ EA.3 | AgentRegistry stub | COMPLETE | 3 | `agents/agent_registry_stub.py` (290 lines) |
| 🔄 EA.4 | ObservationAgent | TODO | 5 | `agents/observation_agent.py` |
| 🔄 EA.5 | RequirementsAgent | TODO | 5 | `agents/requirements_agent.py` |
| 🔄 EA.6 | Unit tests | TODO | 3 | `tests/agents/test_*.py` (50+ tests) |

**Total:** 26 story points, 6 days work

---

## 🏗️ Architecture Overview

```
backend/
├── agents/                          # Phase 3 agent implementations
│   ├── __init__.py                 # Package exports
│   ├── base_agent.py               # ✅ BaseAgent abstract class (EA.1)
│   ├── agent_registry_stub.py      # ✅ In-memory agent registry (EA.3)
│   ├── observation_agent.py        # 🔄 Code analysis agent (EA.4)
│   └── requirements_agent.py       # 🔄 Test requirement extraction (EA.5)
│
├── messaging/                       # Message bus for agent communication
│   ├── __init__.py                 # Package exports
│   └── message_bus_stub.py         # ✅ In-memory message bus (EA.2)
│
└── tests/
    └── agents/                      # 🔄 Unit tests (EA.6)
        ├── test_base_agent.py      # BaseAgent tests
        ├── test_message_bus.py     # MessageBus tests
        ├── test_agent_registry.py  # AgentRegistry tests
        ├── test_observation_agent.py
        └── test_requirements_agent.py
```

---

## 🎯 What We've Built

### 1. BaseAgent (agents/base_agent.py)

**Abstract base class** for all Phase 3 agents with:

**Rich Defaults (90% functionality):**
- `start()` / `stop()` - Agent lifecycle management
- `_heartbeat_loop()` - Periodic health checks (every 30s)
- `_message_loop()` - Receive tasks from message bus
- `get_metrics()` - Track tasks completed/failed, success rate, uptime
- Graceful shutdown with active task completion

**3 Abstract Methods (subclasses implement):**
1. `capabilities` - Declare what agent can do
2. `can_handle(task)` - Determine if agent can handle a task (returns bool + confidence)
3. `execute_task(task)` - Execute task and return result

**Data Classes:**
- `AgentCapability` - Capability declaration (name, version, threshold)
- `TaskContext` - Task input (task_id, type, payload, conversation_id, priority)
- `TaskResult` - Task output (success, result, error, confidence, execution_time)

**Example Usage:**
```python
class ObservationAgent(BaseAgent):
    @property
    def capabilities(self):
        return [AgentCapability("code_analysis", "1.0.0")]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        if task.task_type == "code_analysis":
            return True, 0.9
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        # Analyze code using AST
        code = task.payload["code"]
        functions = extract_functions(code)
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={"functions": functions},
            confidence=0.85
        )
```

---

### 2. MessageBusStub (messaging/message_bus_stub.py)

**In-memory message bus** (no Redis dependency) with:

**Key Features:**
- `send_message(stream, message)` - Send message to stream
- `receive_batch(stream, count, timeout)` - Receive messages (blocking with timeout)
- `acknowledge_message(stream, consumer_id, msg_id)` - Mark message as processed
- `create_consumer_group(stream, group)` - Create consumer group for parallel processing
- Stream statistics (length, pending count, etc.)

**Why Stub Implementation?**
- Developer A can build agents **without Redis installed**
- Fast testing (no network calls, instant message delivery)
- Same interface as real Redis implementation (easy swap later)

**Migration Path (Sprint 7):**
```python
# Before (stub)
from messaging.message_bus_stub import MessageBusStub
bus = MessageBusStub()

# After (real Redis - Developer B builds this)
from messaging.message_bus import MessageBus
bus = MessageBus(redis_client)

# Agent code doesn't change!
```

---

### 3. AgentRegistryStub (agents/agent_registry_stub.py)

**In-memory agent registry** (no Redis dependency) with:

**Key Features:**
- `register(agent_id, type, capabilities, priority)` - Register agent
- `deregister(agent_id)` - Unregister agent (graceful shutdown)
- `heartbeat(agent_id, metrics)` - Update agent liveness
- `get_agents_by_type(type)` - Find all observation agents
- `get_agents_by_capability(capability)` - Find agents that can do code_analysis
- `cleanup_dead_agents()` - Remove agents without heartbeat (>90s timeout)

**Agent Discovery:**
```python
# Find all agents that can analyze code
agents = await registry.get_agents_by_capability("code_analysis")

# Pick highest priority agent
best_agent = max(agents, key=lambda a: a["priority"])
```

---

## 🚀 Next Steps (Developer A)

### Task EA.4: ObservationAgent (5 points, 2 days)

**Goal:** Analyze Python code structure and complexity

**Implementation:**
```python
# backend/agents/observation_agent.py

import ast
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult

class ObservationAgent(BaseAgent):
    @property
    def capabilities(self):
        return [AgentCapability("code_analysis", "1.0.0", confidence_threshold=0.8)]
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        code = task.payload.get("code", "")
        
        # Parse Python code using AST
        tree = ast.parse(code)
        
        # Extract functions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        # Extract classes
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        # Calculate complexity (simple LOC count)
        lines = [line for line in code.split('\n') if line.strip()]
        
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={
                "functions": functions,
                "classes": classes,
                "complexity": len(lines),
                "language": "python"
            },
            confidence=0.85
        )
```

**Deliverables:**
- Extract functions, classes, imports
- Calculate complexity (LOC, cyclomatic complexity)
- Works with stub dependencies (no external APIs)
- 150+ lines of code

---

### Task EA.5: RequirementsAgent (5 points, 2 days)

**Goal:** Extract test requirements from code observations

**Implementation:**
```python
# backend/agents/requirements_agent.py

class RequirementsAgent(BaseAgent):
    @property
    def capabilities(self):
        return [AgentCapability("requirement_extraction", "1.0.0")]
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        observations = task.payload.get("observations", {})
        functions = observations.get("functions", [])
        
        requirements = []
        for func_name in functions:
            requirements.append({
                "requirement_id": f"REQ-{len(requirements) + 1}",
                "description": f"Test {func_name} function behavior",
                "test_scenarios": [
                    f"Given valid input, When {func_name} is called, Then it should return expected output",
                    f"Given invalid input, When {func_name} is called, Then it should handle errors gracefully"
                ],
                "priority": "high" if "main" in func_name else "medium"
            })
        
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={"requirements": requirements},
            confidence=0.75
        )
```

**Deliverables:**
- Pattern matching for common test requirements
- Given/When/Then scenario generation
- Priority assignment based on function importance
- 120+ lines of code

---

### Task EA.6: Unit Tests (3 points, 1 day)

**Goal:** 50+ unit tests, 95%+ coverage

**Test Files:**
```
tests/agents/
├── conftest.py                    # Pytest fixtures
├── test_base_agent.py             # BaseAgent lifecycle tests
├── test_message_bus_stub.py       # MessageBus send/receive tests
├── test_agent_registry_stub.py    # AgentRegistry register/heartbeat tests
├── test_observation_agent.py      # ObservationAgent code analysis tests
└── test_requirements_agent.py     # RequirementsAgent extraction tests
```

**Key Test Scenarios:**
1. **BaseAgent:**
   - Test start()/stop() lifecycle
   - Test heartbeat loop
   - Test metrics tracking (tasks completed/failed)
   - Test graceful shutdown with active tasks

2. **MessageBusStub:**
   - Test send_message() -> receive_batch()
   - Test consumer groups
   - Test acknowledgment
   - Test timeout behavior

3. **AgentRegistryStub:**
   - Test register()/deregister()
   - Test heartbeat updates
   - Test dead agent detection (>90s timeout)
   - Test agent discovery by type/capability

4. **ObservationAgent:**
   - Test Python code parsing (functions, classes)
   - Test complexity calculation
   - Test error handling (invalid syntax)

5. **RequirementsAgent:**
   - Test requirement extraction from observations
   - Test Given/When/Then generation
   - Test priority assignment

**Run Tests:**
```bash
cd backend
pytest tests/agents/ -v --cov=agents --cov-report=html
```

**Expected Output:**
```
✅ 50+ tests passing
✅ 95%+ code coverage
✅ <5 seconds execution time (no external dependencies)
```

---

## 📚 Documentation

### For Developers

- **[Phase3-Project-Management-Plan-Complete.md](../Phase3-project-documents/Phase3-Project-Management-Plan-Complete.md)** - Sprint 7-12 plan
- **[Phase3-Implementation-Guide-Complete.md](../Phase3-project-documents/Phase3-Implementation-Guide-Complete.md)** - Detailed implementation guide
- **[Phase3-Architecture-Design-Complete.md](../Phase3-project-documents/Phase3-Architecture-Design-Complete.md)** - Architecture design

### For Code Understanding

Each module has comprehensive docstrings explaining:
- What the module does
- Why we designed it this way
- How to use it (with code examples)
- When to swap stub for real implementation (migration path)

---

## 🎯 Success Criteria (End of Pre-Sprint)

By Jan 23 (Sprint 7 kickoff), Developer A should have:

- ✅ **BaseAgent abstract class** - Foundation for all agents
- ✅ **MessageBus stub** - Agent communication without Redis
- ✅ **AgentRegistry stub** - Agent tracking without Redis
- 🔄 **ObservationAgent** - Code analysis agent
- 🔄 **RequirementsAgent** - Test requirement extraction
- 🔄 **50+ unit tests** - 95%+ coverage, all passing

**Total:** 26 story points, 1,000+ lines of production code, zero external dependencies

---

## 🔄 Integration with Sprint 7 (When Developer B Joins)

### Developer B's Tasks (Sprint 7):

1. **Add agent tables to PostgreSQL** (2 days)
   - `agents` table (agent_id, type, capabilities, status)
   - `agent_heartbeats` table (agent_id, timestamp, metrics)
   - `agent_tasks` table (task_id, agent_id, status, result)

2. **Implement real MessageBus with Redis** (2 days)
   - Replace `MessageBusStub` with `MessageBus(redis_client)`
   - Same interface, real Redis Streams backend
   - Send/receive 1000+ messages/sec

3. **Implement real AgentRegistry with Redis** (1 day)
   - Replace `AgentRegistryStub` with `AgentRegistry(redis_client)`
   - Store agent metadata in Redis hashes
   - Heartbeat tracking with Redis expiry

### Integration (1 day):

**Swap stubs for real implementations:**
```python
# Before (Developer A's stub code)
from messaging.message_bus_stub import MessageBusStub
from agents.agent_registry_stub import AgentRegistryStub

bus = MessageBusStub()
registry = AgentRegistryStub()

# After (Developer B's real infrastructure)
from messaging.message_bus import MessageBus
from agents.agent_registry import AgentRegistry

bus = MessageBus(redis_client)
registry = AgentRegistry(redis_client)
```

**Agent code doesn't change!** That's the power of dependency injection + interface matching.

---

## 🐛 Troubleshooting

### Issue: Import errors

```bash
# Make sure you're in backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Tests not finding modules

```bash
# Create conftest.py in tests/agents/
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))
```

### Issue: Async warnings in tests

```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Add to pytest.ini or pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## 📞 Questions?

**Developer A:** Check [Phase3-Project-Management-Plan-Complete.md](../Phase3-project-documents/Phase3-Project-Management-Plan-Complete.md) Section 2.4 for detailed task breakdown

**Developer B:** Tasks start in Sprint 7 (Jan 23). See Section 2.4 Sprint 7 for infrastructure tasks.

---

**Last Updated:** January 20, 2026  
**Branch:** `feature/phase3-agent-foundation`  
**Next Milestone:** Sprint 7 Integration (Jan 23-Feb 5, 2026)
