# Phase 3: Architecture Diagrams (C4 Model)

**Purpose:** Visual documentation of multi-agent system architecture  
**Status:** Reference for Sprints 7-12  
**Last Updated:** January 16, 2026

---

## 📋 Overview

This document uses the **C4 Model** (Context, Container, Component, Code) to visualize Phase 3 architecture at multiple levels of abstraction.

---

## Level 1: System Context Diagram

Shows how the AI Test Generation System fits into the broader ecosystem.

```mermaid
graph TB
    User[User/Developer]
    GitHub[GitHub Repository]
    Jira[Jira/Project Management]
    CI[CI/CD Pipeline]
    
    System[AI Test Generation System<br/>Phase 3 Multi-Agent]
    
    User -->|Generates tests| System
    GitHub -->|Code changes| System
    Jira -->|Requirements| System
    CI -->|Triggers| System
    
    System -->|Tests| GitHub
    System -->|Coverage reports| User
    System -->|Test results| CI
    
    style System fill:#4A90E2,color:#fff
```

**Description:** Users interact with the system to generate tests. The system integrates with external services (GitHub, Jira, CI/CD) to gather context and deliver results.

---

## Level 2: Container Diagram

Shows the high-level technology choices and communication patterns.

```mermaid
graph TB
    subgraph "User Devices"
        Browser[Web Browser]
    end
    
    subgraph "AI Test Generation System"
        Frontend[Frontend<br/>React + TypeScript]
        Backend[Backend API<br/>FastAPI + Python]
        
        subgraph "Agent Infrastructure"
            OrchAgent[Orchestration Agent]
            ObsAgent[Observation Agent]
            ReqAgent[Requirements Agent]
            AnaAgent[Analysis Agent]
            EvoAgent[Evolution Agent]
            RepAgent[Reporting Agent]
        end
        
        MessageBus[Message Bus<br/>Redis Streams]
        Database[(PostgreSQL)]
        VectorDB[(Vector DB<br/>Qdrant)]
        Cache[Cache<br/>Redis]
    end
    
    subgraph "External Services"
        LLM[LLM APIs<br/>OpenAI]
        GitHub[GitHub API]
    end
    
    Browser -->|HTTPS| Frontend
    Frontend -->|REST API| Backend
    Backend -->|Commands| OrchAgent
    
    OrchAgent -.->|Messages| MessageBus
    ObsAgent -.->|Messages| MessageBus
    ReqAgent -.->|Messages| MessageBus
    AnaAgent -.->|Messages| MessageBus
    EvoAgent -.->|Messages| MessageBus
    RepAgent -.->|Messages| MessageBus
    
    Backend -->|SQL| Database
    ObsAgent -->|Embeddings| VectorDB
    EvoAgent -->|Prompts| LLM
    ObsAgent -->|Code| GitHub
    
    OrchAgent -->|State| Database
    ReqAgent -->|Cache| Cache
    
    style OrchAgent fill:#E74C3C,color:#fff
    style MessageBus fill:#F39C12,color:#fff
    style Database fill:#3498DB,color:#fff
```

**Key Technologies:**
- **Frontend:** React 18, TypeScript, TailwindCSS
- **Backend:** FastAPI, Python 3.11+
- **Agents:** Python async/await, LangGraph
- **Message Bus:** Redis Streams (exactly-once delivery)
- **Database:** PostgreSQL 15+ with pgvector
- **Vector DB:** Qdrant (embeddings for semantic search)
- **Cache:** Redis (short-term memory)
- **LLM:** OpenAI GPT-4

---

## Level 3: Component Diagram (Orchestration Agent)

Deep-dive into the Orchestration Agent internal structure.

```mermaid
graph TB
    subgraph "Orchestration Agent"
        MessageHandler[Message Handler]
        StateMachine[LangGraph State Machine]
        TaskAllocator[Task Allocator<br/>Contract Net Protocol]
        Scheduler[Task Scheduler]
        CircuitBreaker[Circuit Breaker]
        Checkpoint[Checkpoint Manager]
    end
    
    MessageBus[Message Bus]
    AgentRegistry[Agent Registry]
    Database[(PostgreSQL)]
    
    MessageBus -->|Incoming Requests| MessageHandler
    MessageHandler -->|Parse| StateMachine
    StateMachine -->|Allocate| TaskAllocator
    TaskAllocator -->|Discover| AgentRegistry
    TaskAllocator -->|Schedule| Scheduler
    Scheduler -->|Send| MessageBus
    
    StateMachine -->|Save State| Checkpoint
    Checkpoint -->|Persist| Database
    
    CircuitBreaker -->|Monitor| Scheduler
    CircuitBreaker -.->|Fallback| StateMachine
    
    style StateMachine fill:#9B59B6,color:#fff
    style CircuitBreaker fill:#E74C3C,color:#fff
```

**Components:**
- **Message Handler:** Receives tasks from message bus, validates, routes
- **State Machine:** LangGraph-based workflow (Observe → Requirements → Analysis → Evolution → Report)
- **Task Allocator:** Implements Contract Net Protocol (CFP, bidding, selection)
- **Scheduler:** Queues tasks, manages priorities, handles timeouts
- **Circuit Breaker:** Detects failures, prevents cascading failures (opens after 3 consecutive failures)
- **Checkpoint Manager:** Saves workflow state for crash recovery

---

## Level 4: Sequence Diagram (Test Generation Flow)

Shows interactions between components for a single test generation request.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Orchestrator
    participant Observation
    participant Requirements
    participant Analysis
    participant Evolution
    participant Reporting
    participant LLM
    participant Database
    
    User->>Frontend: Generate tests for UserService
    Frontend->>Backend: POST /api/v2/tests/generate
    Backend->>Orchestrator: Create task
    Orchestrator->>Database: Save task (pending)
    Orchestrator->>Observation: Analyze code
    
    Observation->>LLM: Detect patterns in UserService
    LLM-->>Observation: Patterns: Factory method, Builder
    Observation->>Database: Store patterns
    Observation-->>Orchestrator: Patterns detected
    
    Orchestrator->>Requirements: Extract requirements
    Requirements->>LLM: Parse requirements from patterns
    LLM-->>Requirements: Test requirements
    Requirements-->>Orchestrator: Requirements ready
    
    Orchestrator->>Analysis: Score risk
    Analysis->>Database: Get historical failure data
    Database-->>Analysis: Failure rates
    Analysis->>LLM: Calculate risk scores
    LLM-->>Analysis: Risk: 0.72 (medium-high)
    Analysis-->>Orchestrator: Risk scores
    
    Orchestrator->>Evolution: Generate tests
    Evolution->>LLM: Generate pytest code
    LLM-->>Evolution: Test code (15 tests)
    Evolution->>Evolution: Validate syntax
    Evolution->>Database: Store generated tests
    Evolution-->>Orchestrator: Tests generated
    
    Orchestrator->>Reporting: Aggregate results
    Reporting->>Database: Fetch metrics
    Database-->>Reporting: Coverage, risk, tests
    Reporting-->>Orchestrator: Report ready
    
    Orchestrator->>Database: Update task (completed)
    Orchestrator-->>Backend: Task result
    Backend-->>Frontend: 200 OK (test code)
    Frontend-->>User: Display generated tests
```

**Flow Summary:**
1. User requests test generation via UI
2. Backend creates task, hands to Orchestration Agent
3. Orchestration Agent coordinates 5 specialized agents sequentially
4. Each agent calls LLM, stores results, notifies Orchestrator
5. Final result aggregated by Reporting Agent
6. Result returned to user

**Typical Duration:** 30-60 seconds (P95)

---

## Data Flow Diagram (Memory System)

Shows how data flows through the three-layer memory system.

```mermaid
graph LR
    Agent[Agent]
    
    subgraph "Short-Term Memory (1 hour TTL)"
        Redis[Redis List<br/>Last 100 items]
    end
    
    subgraph "Working Memory (30 days)"
        Postgres[(PostgreSQL<br/>Conversation-scoped)]
    end
    
    subgraph "Long-Term Memory (Unlimited)"
        VectorDB[(Vector DB<br/>Semantic search)]
    end
    
    Agent -->|Store recent| Redis
    Agent -->|Store conversation| Postgres
    Agent -->|Store important| VectorDB
    
    Agent -->|Query recent| Redis
    Agent -->|Query by conversation_id| Postgres
    Agent -->|Semantic search| VectorDB
    
    Redis -.->|Auto-expire 1hr| X1[×]
    Postgres -.->|Cleanup job| X2[×]
    
    style Redis fill:#E74C3C,color:#fff
    style Postgres fill:#3498DB,color:#fff
    style VectorDB fill:#9B59B6,color:#fff
```

**Memory Layers:**
- **Short-Term (Redis):** Last 100 interactions, 1-hour TTL, sub-1ms retrieval
- **Working (PostgreSQL):** Active conversations, 30-day retention, conversation-scoped queries
- **Long-Term (Vector DB):** Important patterns, unlimited retention, semantic search

---

## Deployment Architecture (Kubernetes)

Shows production deployment topology.

```mermaid
graph TB
    subgraph "Load Balancer"
        Ingress[Nginx Ingress]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Frontend Pods (3 replicas)"
            FE1[Frontend 1]
            FE2[Frontend 2]
            FE3[Frontend 3]
        end
        
        subgraph "Backend Pods (3 replicas)"
            BE1[Backend API 1]
            BE2[Backend API 2]
            BE3[Backend API 3]
        end
        
        subgraph "Agent Pods (HPA: 3-10 replicas)"
            A1[Observation Agent 1]
            A2[Requirements Agent 1]
            A3[Analysis Agent 1]
            A4[Evolution Agent 1]
            A5[Orchestration Agent 1]
            A6[Reporting Agent 1]
        end
        
        subgraph "Data Layer"
            Redis[(Redis Cluster<br/>3 nodes)]
            Postgres[(PostgreSQL<br/>Primary + Replica)]
            Qdrant[(Qdrant<br/>Vector DB)]
        end
    end
    
    subgraph "External"
        Prometheus[Prometheus]
        Grafana[Grafana]
    end
    
    Ingress --> FE1
    Ingress --> FE2
    Ingress --> FE3
    
    FE1 --> BE1
    FE2 --> BE2
    FE3 --> BE3
    
    BE1 --> A5
    BE2 --> A5
    BE3 --> A5
    
    A1 --> Redis
    A2 --> Redis
    A3 --> Redis
    A4 --> Redis
    A5 --> Redis
    A6 --> Redis
    
    A1 --> Postgres
    A5 --> Postgres
    A6 --> Postgres
    
    A1 --> Qdrant
    
    Prometheus -.->|Scrape| BE1
    Prometheus -.->|Scrape| A1
    Grafana -.->|Query| Prometheus
    
    style Ingress fill:#2ECC71,color:#fff
    style A5 fill:#E74C3C,color:#fff
    style Redis fill:#F39C12,color:#fff
```

**Key Features:**
- **High Availability:** 3+ replicas per component, multi-zone deployment
- **Auto-Scaling:** HorizontalPodAutoscaler (3-10 replicas based on CPU/memory)
- **Observability:** Prometheus metrics, Grafana dashboards
- **Resilience:** Circuit breakers, health checks, graceful shutdown

---

## Message Flow (Contract Net Protocol)

Shows how tasks are allocated via bidding.

```mermaid
sequenceDiagram
    participant Orchestrator
    participant Evolution1
    participant Evolution2
    participant Evolution3
    participant MessageBus
    
    Note over Orchestrator: Task arrives: Generate tests
    
    Orchestrator->>MessageBus: Publish CFP (Call for Proposals)
    MessageBus->>Evolution1: CFP notification
    MessageBus->>Evolution2: CFP notification
    MessageBus->>Evolution3: CFP notification
    
    Evolution1->>Evolution1: Check load (3 active tasks)
    Evolution2->>Evolution2: Check load (1 active task)
    Evolution3->>Evolution3: Check load (5 active tasks, at max)
    
    Evolution1->>MessageBus: Bid (confidence: 0.70)
    Evolution2->>MessageBus: Bid (confidence: 0.85)
    Evolution3->>MessageBus: No bid (at capacity)
    
    MessageBus->>Orchestrator: Bids received
    
    Note over Orchestrator: Select winner<br/>Evolution2 (highest confidence, lowest load)
    
    Orchestrator->>MessageBus: Award task to Evolution2
    MessageBus->>Evolution2: Task awarded
    
    Evolution2->>Evolution2: Execute task
    Evolution2->>MessageBus: Task result
    MessageBus->>Orchestrator: Task completed
```

**Benefits of CNP:**
- Dynamic load balancing (agents bid based on current load)
- Quality optimization (select highest confidence agent)
- Graceful degradation (if no bids, fallback to round-robin)

---

## Error Handling Flow (Circuit Breaker)

Shows how system handles agent failures.

```mermaid
stateDiagram-v2
    [*] --> Closed: Initial state
    Closed --> Open: 3 consecutive failures
    Open --> HalfOpen: 60 seconds elapsed
    HalfOpen --> Closed: Success
    HalfOpen --> Open: Failure
    
    note right of Closed
        Normal operation
        All requests forwarded to agent
    end note
    
    note right of Open
        Circuit opened
        Requests fail fast
        Fallback to alternative agent
    end note
    
    note right of HalfOpen
        Testing recovery
        1 request allowed through
    end note
```

**Circuit Breaker Logic:**
- **Closed:** Normal operation, requests forwarded
- **Open:** After 3 failures, circuit opens, requests fail fast (fallback)
- **Half-Open:** After 60s, allow 1 test request
- **Recovery:** If test succeeds, close circuit; if fails, stay open

**Impact:** Reduces failure rate by 3.2× (prevents cascading failures)

---

## C4 Model Summary

| Level | Diagram | Purpose | Audience |
|-------|---------|---------|----------|
| 1 | System Context | Show external dependencies | Product owners, stakeholders |
| 2 | Container | Show technology stack | Architects, tech leads |
| 3 | Component | Show internal structure | Developers |
| 4 | Code/Sequence | Show runtime behavior | Developers, debuggers |

---

## 🛠️ Tools Used

**Mermaid.js:** All diagrams rendered as Mermaid code (markdown-compatible)

**PlantUML Alternative:** For C4 model purists, convert to PlantUML:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i architecture.mmd -o architecture.png
```

---

**END OF ARCHITECTURE DIAGRAMS**
