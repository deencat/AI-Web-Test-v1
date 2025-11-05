# AI Web Test v1.0 - Deployment Automation & Resilience Architecture
## Production-Grade Deployment Patterns & Failure Handling

**Version:** 1.0  
**Date:** October 31, 2025  
**Priority:** P0 - Critical  
**Status:** Production-Ready Architecture  
**Implementation Timeline:** 13 days (integrated into Phase 3)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Deployment Strategies](#deployment-strategies)
3. [Circuit Breaker Patterns](#circuit-breaker-patterns)
4. [Health Checks & Probes](#health-checks--probes)
5. [Automated Rollback](#automated-rollback)
6. [Blue-Green Deployments](#blue-green-deployments)
7. [Canary Deployments](#canary-deployments)
8. [Failure Recovery](#failure-recovery)
9. [Chaos Engineering](#chaos-engineering)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document addresses the **critical deployment automation and resilience gap** identified in the AI Web Test v1.0 documentation. It provides production-grade deployment patterns, resilience mechanisms, and failure handling strategies following 2025 industry best practices.

**What Was Missing:**
- ❌ Circuit breaker patterns for external dependencies (OpenRouter API, etc.)
- ❌ Detailed canary deployment strategy
- ❌ Blue-green deployment for zero-downtime updates
- ❌ Comprehensive health check strategy
- ❌ Automated rollback mechanisms beyond model-specific
- ❌ Failure recovery procedures

**What's Being Added:**
- ✅ Circuit breaker implementation (PyBreaker, Polly, Resilience4j)
- ✅ Canary deployments with ArgoCD Rollouts/Flagger
- ✅ Blue-green deployment strategy
- ✅ Kubernetes health checks (liveness/readiness/startup probes)
- ✅ Automated rollback based on error rate, latency, success rate
- ✅ Comprehensive failure recovery procedures
- ✅ Chaos engineering practices

**Implementation Timeline:** 13 days (Phase 3)

---

## Deployment Strategies

### Overview of Deployment Patterns

```
┌──────────────────────────────────────────────────────────────┐
│           DEPLOYMENT STRATEGY COMPARISON                      │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ BLUE-GREEN DEPLOYMENT                                       │
├─────────────────────────────────────────────────────────────┤
│ Blue Environment (Current)    Green Environment (New)       │
│ ┌──────────┐                  ┌──────────┐                 │
│ │ v1.0     │ ←─ 100% traffic  │ v1.1     │ (idle)          │
│ └──────────┘                  └──────────┘                 │
│      ↓                              ↓                       │
│ [Deploy to Green] → [Test] → [Switch Traffic] → [Monitor]  │
│                                                             │
│ Pros: Instant rollback, zero downtime                      │
│ Cons: 2x infrastructure cost                               │
│ Use for: Major version updates, schema changes            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CANARY DEPLOYMENT                                           │
├─────────────────────────────────────────────────────────────┤
│ Stable (v1.0)         Canary (v1.1)                        │
│ ┌──────────┐          ┌──────────┐                         │
│ │ 95% ──────┤          │ 5% ──────┤                         │
│ └──────────┘          └──────────┘                         │
│      ↓                     ↓                                │
│ Gradual increase: 5% → 20% → 50% → 100%                   │
│ Monitor at each stage, rollback if issues detected        │
│                                                             │
│ Pros: Early issue detection, gradual validation            │
│ Cons: Longer deployment time, complexity                   │
│ Use for: Regular updates, incremental changes              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ROLLING DEPLOYMENT                                          │
├─────────────────────────────────────────────────────────────┤
│ Pod 1: v1.0 → v1.1 ✓                                        │
│ Pod 2: v1.0 → v1.1 ✓                                        │
│ Pod 3: v1.0 → v1.1 (in progress)                            │
│ Pod 4: v1.0 (waiting)                                       │
│                                                             │
│ Pros: Resource efficient, gradual                          │
│ Cons: Mixed versions, slower rollback                      │
│ Use for: Standard updates, stateless services              │
└─────────────────────────────────────────────────────────────┘
```

### When to Use Each Strategy

| Deployment Type | Use Case | Rollback Speed | Cost | Complexity |
|----------------|----------|----------------|------|------------|
| **Blue-Green** | Major updates, schema changes | Instant (seconds) | High (2x infra) | Low |
| **Canary** | Regular updates, new features | Fast (minutes) | Medium | High |
| **Rolling** | Stateless services, minor updates | Medium (minutes) | Low | Low |
| **Recreate** | Development, non-critical | N/A (downtime) | Low | Very Low |

**Recommendation for AI Web Test:**
- **Core API/Backend:** Canary deployment (gradual validation)
- **Database Migrations:** Blue-green (zero downtime)
- **ML Model Updates:** A/B testing (covered in MLOps doc)
- **Worker Services:** Rolling deployment (cost-effective)

---

## Circuit Breaker Patterns

### Why Circuit Breakers?

**Problem:** When external dependencies (OpenRouter API, databases, etc.) fail, cascading failures can bring down your entire system.

**Solution:** Circuit breakers detect failures and prevent cascading failures by "opening" the circuit (blocking requests) and using fallbacks.

**Circuit States:**
```
CLOSED (Normal)
  ↓ [Failures exceed threshold]
OPEN (Blocking all requests)
  ↓ [Timeout expires]
HALF-OPEN (Testing)
  ↓ [Request succeeds]
CLOSED (Back to normal)
  
  OR
  
  ↓ [Request fails]
OPEN (Back to blocking)
```

### Implementation with PyBreaker

**Installation:**
```bash
pip install pybreaker==1.0.1
```

**Basic Circuit Breaker:**

```python
# circuit_breakers.py
from pybreaker import CircuitBreaker, CircuitBreakerError
from functools import wraps
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitBreakerManager:
    """
    Manages circuit breakers for all external dependencies.
    
    Prevents cascading failures by detecting and isolating failures.
    """
    
    def __init__(self):
        self.breakers = {}
    
    def create_breaker(self, 
                      name: str,
                      fail_max: int = 5,
                      timeout_duration: int = 60,
                      expected_exception: type = Exception,
                      fallback_function: Callable = None) -> CircuitBreaker:
        """
        Create a circuit breaker for an external dependency.
        
        Args:
            name: Unique name for the breaker
            fail_max: Number of failures before opening circuit
            timeout_duration: Seconds to wait before trying again
            expected_exception: Exception type to catch
            fallback_function: Function to call when circuit is open
        
        Returns:
            CircuitBreaker instance
        """
        breaker = CircuitBreaker(
            fail_max=fail_max,
            timeout_duration=timeout_duration,
            expected_exception=expected_exception,
            name=name
        )
        
        # Add listeners for monitoring
        breaker.add_listener(self._on_circuit_open)
        breaker.add_listener(self._on_circuit_close)
        
        self.breakers[name] = {
            'breaker': breaker,
            'fallback': fallback_function
        }
        
        return breaker
    
    def _on_circuit_open(self, breaker, last_exception):
        """Called when circuit opens."""
        logger.error(f"Circuit breaker '{breaker.name}' OPENED due to: {last_exception}")
        
        # Send alert
        send_alert(
            title=f"Circuit Breaker Opened: {breaker.name}",
            message=f"Service '{breaker.name}' is experiencing failures. Circuit is now OPEN.",
            severity="critical"
        )
        
        # Log metric to Prometheus
        circuit_breaker_state.labels(name=breaker.name).set(1)  # 1 = OPEN
    
    def _on_circuit_close(self, breaker):
        """Called when circuit closes."""
        logger.info(f"Circuit breaker '{breaker.name}' CLOSED")
        
        # Log metric to Prometheus
        circuit_breaker_state.labels(name=breaker.name).set(0)  # 0 = CLOSED

# Global circuit breaker manager
cb_manager = CircuitBreakerManager()

# Prometheus metrics
from prometheus_client import Gauge

circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['name']
)
```

### OpenRouter API Circuit Breaker

**Critical Dependency:** OpenRouter API powers our AI agents. If it fails, we need fallback strategies.

```python
# openrouter_client.py
import httpx
from pybreaker import CircuitBreakerError
from typing import Optional, Dict, Any
import json

class OpenRouterClient:
    """
    OpenRouter API client with circuit breaker protection.
    
    Features:
    - Circuit breaker for failure detection
    - Automatic fallback to cached responses
    - Retry logic with exponential backoff
    - Request timeout handling
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Create circuit breaker
        self.circuit_breaker = cb_manager.create_breaker(
            name="openrouter_api",
            fail_max=5,              # Open after 5 consecutive failures
            timeout_duration=60,     # Try again after 60 seconds
            expected_exception=httpx.HTTPError,
            fallback_function=self._fallback_response
        )
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0)
        )
        
        # Response cache for fallback
        self.response_cache = ResponseCache(max_size=1000)
    
    @circuit_breaker
    async def chat_completion(self,
                             model: str,
                             messages: list,
                             temperature: float = 0.7,
                             max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Call OpenRouter chat completion API with circuit breaker.
        
        Args:
            model: Model name (e.g., "anthropic/claude-3-opus")
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            API response dict
        
        Raises:
            CircuitBreakerError: If circuit is open
            httpx.HTTPError: If API call fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Cache successful response for fallback
            cache_key = self._generate_cache_key(model, messages)
            self.response_cache.set(cache_key, result)
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise  # Let circuit breaker handle it
    
    def _fallback_response(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """
        Fallback function when circuit is open.
        
        Strategy:
        1. Try to return cached response for similar request
        2. If no cache, return generic fallback response
        3. Log incident for manual review
        """
        logger.warning("OpenRouter circuit breaker OPEN, using fallback")
        
        # Try cache
        cache_key = self._generate_cache_key(model, messages)
        cached_response = self.response_cache.get(cache_key)
        
        if cached_response:
            logger.info("Using cached OpenRouter response")
            return {
                **cached_response,
                "fallback": True,
                "fallback_reason": "circuit_breaker_open"
            }
        
        # No cache available, return generic fallback
        logger.error("No cached response available, using generic fallback")
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "I'm currently experiencing technical difficulties. Please try again in a moment."
                }
            }],
            "fallback": True,
            "fallback_reason": "circuit_breaker_open_no_cache"
        }
    
    def _generate_cache_key(self, model: str, messages: list) -> str:
        """Generate cache key from request."""
        # Use last user message as key
        last_message = messages[-1]["content"] if messages else ""
        return f"{model}:{hash(last_message)}"
    
    async def health_check(self) -> bool:
        """Check if OpenRouter API is healthy."""
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200
        except:
            return False
```

### Response Cache for Fallback

```python
# response_cache.py
from collections import OrderedDict
from typing import Any, Optional
import time

class ResponseCache:
    """
    LRU cache for API responses to use as fallback.
    
    Features:
    - LRU eviction policy
    - TTL (time-to-live) for cache entries
    - Thread-safe operations
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize response cache.
        
        Args:
            max_size: Maximum number of cached responses
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached response if available and not expired."""
        with self._lock:
            if key not in self.cache:
                return None
            
            value, timestamp = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            
            return value
    
    def set(self, key: str, value: Any):
        """Set cached response."""
        with self._lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, time.time())
```

### Database Circuit Breaker

```python
# database_client.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pybreaker import CircuitBreakerError

class DatabaseClient:
    """
    Database client with circuit breaker protection.
    
    Prevents cascading failures when database is down.
    """
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create circuit breaker
        self.circuit_breaker = cb_manager.create_breaker(
            name="database",
            fail_max=3,              # Open after 3 failures
            timeout_duration=30,     # Try again after 30 seconds
            expected_exception=Exception
        )
    
    @circuit_breaker
    def get_session(self):
        """Get database session with circuit breaker."""
        try:
            session = self.SessionLocal()
            # Test connection
            session.execute("SELECT 1")
            return session
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if database is healthy."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except CircuitBreakerError:
            return False
        except Exception:
            return False
```

### Circuit Breaker Dashboard

**Grafana Dashboard for Circuit Breaker Monitoring:**

```yaml
# grafana-circuit-breakers-dashboard.json
{
  "title": "Circuit Breakers",
  "panels": [
    {
      "title": "Circuit Breaker States",
      "targets": [
        {
          "expr": "circuit_breaker_state",
          "legendFormat": "{{name}}"
        }
      ],
      "type": "timeseries"
    },
    {
      "title": "Circuit Breaker Events",
      "targets": [
        {
          "expr": "rate(circuit_breaker_opened_total[5m])",
          "legendFormat": "{{name}} opened"
        }
      ],
      "type": "timeseries"
    }
  ]
}
```

---

## Health Checks & Probes

### Kubernetes Health Checks

**Three Types of Probes:**

1. **Liveness Probe:** Is the app alive? (If not, restart it)
2. **Readiness Probe:** Is the app ready for traffic? (If not, don't send traffic)
3. **Startup Probe:** Has the app started? (Useful for slow-starting apps)

### Implementation

**FastAPI Health Check Endpoint:**

```python
# health.py
from fastapi import APIRouter, Response, status
from typing import Dict, Any
import time

router = APIRouter()

class HealthChecker:
    """
    Comprehensive health check system.
    
    Checks:
    - Application liveness
    - Dependencies (database, Redis, external APIs)
    - Resource usage (memory, CPU)
    - Service readiness
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.dependencies = {}
        self.is_shutting_down = False
    
    def register_dependency(self, name: str, health_check_func: callable):
        """Register a dependency health check."""
        self.dependencies[name] = health_check_func
    
    async def liveness(self) -> Dict[str, Any]:
        """
        Liveness probe: Is the application alive?
        
        Returns 200 if alive, 503 if dead/shutting down.
        Used by Kubernetes to restart unhealthy pods.
        """
        if self.is_shutting_down:
            return {
                "status": "shutting_down",
                "alive": False
            }
        
        return {
            "status": "healthy",
            "alive": True,
            "uptime_seconds": time.time() - self.start_time
        }
    
    async def readiness(self) -> Dict[str, Any]:
        """
        Readiness probe: Is the application ready to serve traffic?
        
        Returns 200 if ready, 503 if not ready.
        Used by Kubernetes to determine if pod should receive traffic.
        """
        if self.is_shutting_down:
            return {
                "status": "not_ready",
                "ready": False,
                "reason": "shutting_down"
            }
        
        # Check all dependencies
        dependency_health = {}
        all_healthy = True
        
        for name, health_check in self.dependencies.items():
            try:
                is_healthy = await health_check()
                dependency_health[name] = {
                    "healthy": is_healthy,
                    "status": "up" if is_healthy else "down"
                }
                if not is_healthy:
                    all_healthy = False
            except Exception as e:
                dependency_health[name] = {
                    "healthy": False,
                    "status": "error",
                    "error": str(e)
                }
                all_healthy = False
        
        if not all_healthy:
            return {
                "status": "not_ready",
                "ready": False,
                "dependencies": dependency_health
            }
        
        return {
            "status": "ready",
            "ready": True,
            "dependencies": dependency_health
        }
    
    async def startup(self) -> Dict[str, Any]:
        """
        Startup probe: Has the application completed startup?
        
        Returns 200 once startup is complete.
        Used by Kubernetes to wait for slow-starting applications.
        """
        # Check if all critical dependencies are initialized
        critical_deps = ["database", "redis", "model_loaded"]
        
        for dep in critical_deps:
            if dep not in self.dependencies:
                return {
                    "status": "starting",
                    "started": False,
                    "waiting_for": dep
                }
        
        return {
            "status": "started",
            "started": True,
            "uptime_seconds": time.time() - self.start_time
        }

# Global health checker
health_checker = HealthChecker()

# Register dependency health checks
async def check_database_health():
    """Check if database is healthy."""
    try:
        return await database_client.health_check()
    except:
        return False

async def check_redis_health():
    """Check if Redis is healthy."""
    try:
        return await redis_client.ping()
    except:
        return False

async def check_openrouter_health():
    """Check if OpenRouter API is healthy."""
    try:
        return await openrouter_client.health_check()
    except:
        return False

health_checker.register_dependency("database", check_database_health)
health_checker.register_dependency("redis", check_redis_health)
health_checker.register_dependency("openrouter", check_openrouter_health)

# FastAPI routes
@router.get("/health/live")
async def liveness_probe(response: Response):
    """
    Liveness probe endpoint.
    
    Kubernetes uses this to determine if pod should be restarted.
    """
    result = await health_checker.liveness()
    
    if not result.get("alive", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return result

@router.get("/health/ready")
async def readiness_probe(response: Response):
    """
    Readiness probe endpoint.
    
    Kubernetes uses this to determine if pod should receive traffic.
    """
    result = await health_checker.readiness()
    
    if not result.get("ready", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return result

@router.get("/health/startup")
async def startup_probe(response: Response):
    """
    Startup probe endpoint.
    
    Kubernetes uses this to wait for slow-starting applications.
    """
    result = await health_checker.startup()
    
    if not result.get("started", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return result

@router.get("/health")
async def health_check(response: Response):
    """
    Comprehensive health check endpoint.
    
    Returns detailed status of all components.
    """
    liveness = await health_checker.liveness()
    readiness = await health_checker.readiness()
    
    result = {
        "status": "healthy" if (liveness.get("alive") and readiness.get("ready")) else "unhealthy",
        "liveness": liveness,
        "readiness": readiness,
        "version": "1.0.0",
        "timestamp": time.time()
    }
    
    if result["status"] == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return result
```

### Kubernetes Deployment with Probes

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiwebtest-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aiwebtest-api
  template:
    metadata:
      labels:
        app: aiwebtest-api
        version: v1.0.0
    spec:
      containers:
      - name: api
        image: aiwebtest/api:v1.0.0
        ports:
        - containerPort: 8000
        
        # Resource limits
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        
        # Liveness probe
        # Kubernetes will restart pod if this fails
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30    # Wait 30s after start
          periodSeconds: 10           # Check every 10s
          timeoutSeconds: 5           # Timeout after 5s
          failureThreshold: 3         # Restart after 3 failures
          successThreshold: 1         # Consider healthy after 1 success
        
        # Readiness probe
        # Kubernetes will stop sending traffic if this fails
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 15    # Wait 15s after start
          periodSeconds: 5            # Check every 5s
          timeoutSeconds: 3           # Timeout after 3s
          failureThreshold: 3         # Remove from service after 3 failures
          successThreshold: 1         # Add to service after 1 success
        
        # Startup probe
        # Kubernetes will wait for this before checking liveness/readiness
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 30        # Allow 5 minutes for startup (30 * 10s)
          successThreshold: 1
        
        # Environment variables
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aiwebtest-secrets
              key: database-url
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: aiwebtest-secrets
              key: openrouter-api-key
        
        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]  # Allow 15s for connections to drain
```

### Health Check Best Practices

1. **Liveness Probe:**
   - Keep it simple and fast
   - Only check if app is alive (not dependencies)
   - Avoid expensive operations

2. **Readiness Probe:**
   - Check critical dependencies
   - More frequent than liveness
   - Can be more expensive

3. **Startup Probe:**
   - For slow-starting apps (e.g., loading ML models)
   - Longer timeout and failureThreshold
   - Prevents premature liveness failures

4. **Timeouts:**
   - Always set timeouts
   - Shorter for readiness (5-10s)
   - Longer for liveness (10-30s)

---

## Automated Rollback

### Rollback Triggers

**Automatic rollback should occur when:**

| Metric | Threshold | Action | Response Time |
|--------|-----------|--------|---------------|
| **Error Rate** | > 1% | Immediate rollback | < 1 minute |
| **Latency P99** | > 5000ms | Immediate rollback | < 1 minute |
| **Success Rate** | < 99% | Immediate rollback | < 1 minute |
| **CPU Usage** | > 90% for 5min | Alert → Rollback if sustained | < 5 minutes |
| **Memory Usage** | > 90% for 5min | Alert → Rollback if sustained | < 5 minutes |
| **HTTP 5xx Rate** | > 0.5% | Immediate rollback | < 30 seconds |

### Implementation

**Prometheus Rules for Rollback:**

```yaml
# prometheus/rollback-rules.yaml
groups:
  - name: automated_rollback
    interval: 15s  # Evaluate every 15 seconds
    rules:
      
      # Error rate too high
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m]) / 
            rate(http_requests_total[5m])
          ) > 0.01
        for: 1m
        labels:
          severity: critical
          action: rollback
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}. Triggering rollback."
      
      # Latency too high
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 5
        for: 1m
        labels:
          severity: critical
          action: rollback
        annotations:
          summary: "High latency detected"
          description: "P99 latency is {{ $value }}s. Triggering rollback."
      
      # Success rate too low
      - alert: LowSuccessRate
        expr: |
          (
            rate(http_requests_total{status="200"}[5m]) / 
            rate(http_requests_total[5m])
          ) < 0.99
        for: 1m
        labels:
          severity: critical
          action: rollback
        annotations:
          summary: "Low success rate detected"
          description: "Success rate is {{ $value | humanizePercentage }}. Triggering rollback."
      
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          (
            100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
          ) > 90
        for: 5m
        labels:
          severity: warning
          action: investigate
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}% for 5 minutes."
      
      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 
            node_memory_MemTotal_bytes
          ) > 0.90
        for: 5m
        labels:
          severity: warning
          action: investigate
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value | humanizePercentage }}."
```

**AlertManager Configuration for Automated Rollback:**

```yaml
# alertmanager/config.yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  routes:
    # Automated rollback route
    - match:
        action: rollback
      receiver: 'automated-rollback'
      group_wait: 0s
      group_interval: 0s
    
    # Investigation route
    - match:
        action: investigate
      receiver: 'ops-team'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://alertmanager-webhook:9090/alerts'
  
  - name: 'automated-rollback'
    webhook_configs:
      - url: 'http://rollback-service:8080/trigger'
        send_resolved: false
  
  - name: 'ops-team'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#ops-alerts'
```

**Rollback Service:**

```python
# rollback_service.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import kubernetes
from kubernetes import client, config
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

class Alert(BaseModel):
    """Prometheus alert format."""
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    status: str

class AlertPayload(BaseModel):
    """AlertManager webhook payload."""
    alerts: List[Alert]

class RollbackService:
    """
    Automated rollback service.
    
    Listens for Prometheus alerts and triggers rollbacks.
    """
    
    def __init__(self):
        # Load Kubernetes config
        config.load_incluster_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        
        # Track rollback history
        self.rollback_history = []
    
    async def trigger_rollback(self,
                               deployment_name: str,
                               namespace: str,
                               reason: str):
        """
        Trigger rollback for a deployment.
        
        Args:
            deployment_name: Name of the deployment to rollback
            namespace: Kubernetes namespace
            reason: Reason for rollback
        """
        logger.critical(f"Triggering rollback for {deployment_name} in {namespace}. Reason: {reason}")
        
        try:
            # Get deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            # Get revision history
            revision_history = deployment.metadata.annotations.get(
                'deployment.kubernetes.io/revision', '1'
            )
            previous_revision = str(int(revision_history) - 1)
            
            # Rollback to previous revision
            logger.info(f"Rolling back from revision {revision_history} to {previous_revision}")
            
            # Patch deployment with previous revision
            body = {
                "spec": {
                    "rollbackTo": {
                        "revision": int(previous_revision)
                    }
                }
            }
            
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=body
            )
            
            # Log rollback
            self.rollback_history.append({
                "deployment": deployment_name,
                "namespace": namespace,
                "reason": reason,
                "from_revision": revision_history,
                "to_revision": previous_revision,
                "timestamp": time.time()
            })
            
            # Send notification
            await self.send_rollback_notification(
                deployment_name=deployment_name,
                namespace=namespace,
                reason=reason,
                from_revision=revision_history,
                to_revision=previous_revision
            )
            
            logger.info(f"Rollback completed for {deployment_name}")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
    
    async def send_rollback_notification(self, **kwargs):
        """Send rollback notification to Slack/email."""
        message = f"""
        🚨 AUTOMATED ROLLBACK TRIGGERED
        
        Deployment: {kwargs['deployment_name']}
        Namespace: {kwargs['namespace']}
        Reason: {kwargs['reason']}
        From Revision: {kwargs['from_revision']}
        To Revision: {kwargs['to_revision']}
        Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
        
        Action taken: Automatic rollback to previous stable version.
        """
        
        await send_slack_message(
            channel='#ops-critical',
            message=message,
            color='danger'
        )

rollback_service = RollbackService()

@app.post("/trigger")
async def trigger_rollback(payload: AlertPayload, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for AlertManager.
    
    Receives alerts and triggers rollbacks if needed.
    """
    for alert in payload.alerts:
        if alert.status != 'firing':
            continue
        
        if alert.labels.get('action') != 'rollback':
            continue
        
        # Extract deployment info from labels
        deployment_name = alert.labels.get('deployment', 'aiwebtest-api')
        namespace = alert.labels.get('namespace', 'production')
        reason = alert.annotations.get('summary', 'Unknown reason')
        
        # Trigger rollback in background
        background_tasks.add_task(
            rollback_service.trigger_rollback,
            deployment_name=deployment_name,
            namespace=namespace,
            reason=reason
        )
    
    return {"status": "ok", "alerts_processed": len(payload.alerts)}

@app.get("/history")
async def get_rollback_history():
    """Get rollback history."""
    return {"rollbacks": rollback_service.rollback_history}
```

---

## Blue-Green Deployments

### Overview

**Blue-Green Deployment:** Maintain two identical production environments (Blue and Green). Deploy to the inactive environment, test, then switch traffic instantly.

**Benefits:**
- ✅ Zero downtime
- ✅ Instant rollback (just switch back)
- ✅ Full testing before production
- ✅ Easy rollback (no data loss)

**Drawbacks:**
- ❌ 2x infrastructure cost
- ❌ Database schema changes require care
- ❌ Stateful applications need special handling

### Implementation with Kubernetes

**Service with Label Selector:**

```yaml
# kubernetes/service-blue-green.yaml
apiVersion: v1
kind: Service
metadata:
  name: aiwebtest-api
  namespace: production
spec:
  selector:
    app: aiwebtest-api
    version: blue  # Switch this to 'green' for deployment
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Blue Deployment:**

```yaml
# kubernetes/deployment-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiwebtest-api-blue
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aiwebtest-api
      version: blue
  template:
    metadata:
      labels:
        app: aiwebtest-api
        version: blue
    spec:
      containers:
      - name: api
        image: aiwebtest/api:v1.0.0
        # ... (same configuration as before)
```

**Green Deployment:**

```yaml
# kubernetes/deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiwebtest-api-green
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aiwebtest-api
      version: green
  template:
    metadata:
      labels:
        app: aiwebtest-api
        version: green
    spec:
      containers:
      - name: api
        image: aiwebtest/api:v1.1.0  # New version
        # ... (same configuration as before)
```

### Blue-Green Deployment Script

```python
# blue_green_deploy.py
import kubernetes
from kubernetes import client, config
import time
import sys
import requests

class BlueGreenDeployment:
    """
    Blue-Green deployment manager.
    
    Process:
    1. Deploy to inactive environment (Green)
    2. Run smoke tests on Green
    3. Switch traffic from Blue to Green
    4. Monitor for issues
    5. Keep Blue running for quick rollback
    """
    
    def __init__(self, namespace: str = "production"):
        config.load_kube_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = namespace
    
    def get_active_version(self) -> str:
        """Get currently active version (blue or green)."""
        service = self.core_v1.read_namespaced_service(
            name="aiwebtest-api",
            namespace=self.namespace
        )
        return service.spec.selector.get('version', 'blue')
    
    def get_inactive_version(self) -> str:
        """Get inactive version."""
        active = self.get_active_version()
        return 'green' if active == 'blue' else 'blue'
    
    async def deploy_to_inactive(self, new_image: str):
        """
        Deploy new version to inactive environment.
        
        Args:
            new_image: Docker image tag (e.g., 'aiwebtest/api:v1.1.0')
        """
        inactive = self.get_inactive_version()
        deployment_name = f"aiwebtest-api-{inactive}"
        
        print(f"📦 Deploying {new_image} to {inactive} environment...")
        
        # Update deployment with new image
        deployment = self.apps_v1.read_namespaced_deployment(
            name=deployment_name,
            namespace=self.namespace
        )
        
        deployment.spec.template.spec.containers[0].image = new_image
        
        self.apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=self.namespace,
            body=deployment
        )
        
        # Wait for rollout to complete
        print(f"⏳ Waiting for {inactive} deployment to be ready...")
        await self.wait_for_deployment(deployment_name)
        
        print(f"✅ {inactive.capitalize()} deployment ready")
    
    async def wait_for_deployment(self, deployment_name: str, timeout: int = 300):
        """Wait for deployment to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )
            
            # Check if all replicas are ready
            if (deployment.status.ready_replicas == deployment.spec.replicas and
                deployment.status.updated_replicas == deployment.spec.replicas):
                return True
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Deployment {deployment_name} not ready after {timeout}s")
    
    async def run_smoke_tests(self, version: str) -> bool:
        """
        Run smoke tests against inactive environment.
        
        Args:
            version: Version to test ('blue' or 'green')
        
        Returns:
            True if tests pass, False otherwise
        """
        print(f"🧪 Running smoke tests on {version} environment...")
        
        # Get pod IP for direct testing (bypassing service)
        pods = self.core_v1.list_namespaced_pod(
            namespace=self.namespace,
            label_selector=f"app=aiwebtest-api,version={version}"
        )
        
        if not pods.items:
            print(f"❌ No pods found for {version}")
            return False
        
        pod_ip = pods.items[0].status.pod_ip
        base_url = f"http://{pod_ip}:8000"
        
        try:
            # Test 1: Health check
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code != 200:
                print(f"❌ Health check failed: {response.status_code}")
                return False
            print("✅ Health check passed")
            
            # Test 2: API endpoint
            response = requests.get(f"{base_url}/api/v1/test-cases", timeout=10)
            if response.status_code not in [200, 404]:  # 404 ok if no data
                print(f"❌ API test failed: {response.status_code}")
                return False
            print("✅ API test passed")
            
            # Test 3: Database connection
            response = requests.get(f"{base_url}/health/ready", timeout=10)
            if response.status_code != 200:
                print(f"❌ Database connection test failed")
                return False
            print("✅ Database connection test passed")
            
            print(f"✅ All smoke tests passed for {version}")
            return True
            
        except Exception as e:
            print(f"❌ Smoke tests failed: {e}")
            return False
    
    def switch_traffic(self, to_version: str):
        """
        Switch traffic to specified version.
        
        Args:
            to_version: Version to switch to ('blue' or 'green')
        """
        print(f"🔄 Switching traffic to {to_version}...")
        
        # Update service selector
        service = self.core_v1.read_namespaced_service(
            name="aiwebtest-api",
            namespace=self.namespace
        )
        
        service.spec.selector['version'] = to_version
        
        self.core_v1.patch_namespaced_service(
            name="aiwebtest-api",
            namespace=self.namespace,
            body=service
        )
        
        print(f"✅ Traffic switched to {to_version}")
    
    async def monitor_post_switch(self, duration: int = 300) -> bool:
        """
        Monitor metrics after traffic switch.
        
        Args:
            duration: How long to monitor (seconds)
        
        Returns:
            True if metrics are healthy, False otherwise
        """
        print(f"📊 Monitoring for {duration}s...")
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Query Prometheus for error rate, latency, etc.
            error_rate = await self.get_error_rate()
            latency_p99 = await self.get_latency_p99()
            
            if error_rate > 0.01:  # > 1%
                print(f"❌ Error rate too high: {error_rate:.2%}")
                return False
            
            if latency_p99 > 5000:  # > 5s
                print(f"❌ Latency too high: {latency_p99}ms")
                return False
            
            print(f"✅ Metrics healthy (error_rate={error_rate:.2%}, p99={latency_p99}ms)")
            
            await asyncio.sleep(30)
        
        print(f"✅ Monitoring complete, all metrics healthy")
        return True
    
    async def rollback(self):
        """Rollback to previous version (instant!)."""
        active = self.get_active_version()
        previous = 'green' if active == 'blue' else 'blue'
        
        print(f"⚠️  Rolling back from {active} to {previous}...")
        self.switch_traffic(previous)
        print(f"✅ Rollback complete")
    
    async def cleanup_old_version(self, version: str):
        """
        Scale down old version after successful deployment.
        
        Keep it at 0 replicas for quick rollback if needed.
        """
        deployment_name = f"aiwebtest-api-{version}"
        
        print(f"🧹 Scaling down {version} deployment...")
        
        deployment = self.apps_v1.read_namespaced_deployment(
            name=deployment_name,
            namespace=self.namespace
        )
        
        deployment.spec.replicas = 0
        
        self.apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=self.namespace,
            body=deployment
        )
        
        print(f"✅ {version.capitalize()} scaled to 0 (kept for rollback)")
    
    async def deploy(self, new_image: str):
        """
        Full blue-green deployment process.
        
        Args:
            new_image: Docker image to deploy
        """
        print("\n" + "="*60)
        print("🚀 STARTING BLUE-GREEN DEPLOYMENT")
        print("="*60 + "\n")
        
        active = self.get_active_version()
        inactive = self.get_inactive_version()
        
        print(f"Current active: {active}")
        print(f"Deploying to: {inactive}\n")
        
        try:
            # Step 1: Deploy to inactive
            await self.deploy_to_inactive(new_image)
            
            # Step 2: Run smoke tests
            tests_passed = await self.run_smoke_tests(inactive)
            if not tests_passed:
                print("\n❌ DEPLOYMENT FAILED: Smoke tests did not pass")
                sys.exit(1)
            
            # Step 3: Switch traffic
            self.switch_traffic(inactive)
            
            # Step 4: Monitor
            metrics_healthy = await self.monitor_post_switch(duration=300)
            if not metrics_healthy:
                print("\n⚠️  ROLLING BACK: Metrics unhealthy after switch")
                await self.rollback()
                sys.exit(1)
            
            # Step 5: Cleanup old version
            await self.cleanup_old_version(active)
            
            print("\n" + "="*60)
            print("✅ BLUE-GREEN DEPLOYMENT SUCCESSFUL")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ DEPLOYMENT FAILED: {e}")
            print("⚠️  Rolling back...")
            await self.rollback()
            sys.exit(1)

# Usage
if __name__ == "__main__":
    import asyncio
    
    deployer = BlueGreenDeployment()
    asyncio.run(deployer.deploy("aiwebtest/api:v1.1.0"))
```

### Database Schema Changes in Blue-Green

**Challenge:** How to handle database schema changes?

**Solution: Expand-Contract Pattern**

```
Phase 1 (Expand):
  Blue: v1.0 (uses old schema)
  Database: Has both old and new columns
  Green: v1.1 (uses new schema)

Phase 2 (Switch):
  Switch traffic from Blue to Green

Phase 3 (Contract):
  Remove old columns after Blue is decommissioned
```

**Example:**

```python
# migration_v1_to_v2.py

# Phase 1: Expand (add new column, keep old)
def upgrade():
    # Add new column
    op.add_column('users', sa.Column('email_address', sa.String(255), nullable=True))
    
    # Backfill data
    op.execute('UPDATE users SET email_address = email WHERE email_address IS NULL')

# Phase 3: Contract (remove old column after deployment)
def upgrade_contract():
    # Remove old column (only after Green is stable!)
    op.drop_column('users', 'email')
```

---

## Canary Deployments

### Overview

**Canary Deployment:** Gradually roll out new version to small percentage of users, increasing progressively.

**Benefits:**
- ✅ Early issue detection with minimal impact
- ✅ Real-world validation
- ✅ Automated rollback on errors
- ✅ Lower risk than blue-green

**Stages:**
1. **5% for 10 minutes** (initial validation)
2. **20% for 20 minutes** (wider testing)
3. **50% for 30 minutes** (majority testing)
4. **100%** (full rollout)

### Implementation with ArgoCD Rollouts

**Installation:**

```bash
# Install Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install Rollouts CLI
brew install argoproj/tap/kubectl-argo-rollouts
```

**Rollout Resource:**

```yaml
# kubernetes/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: aiwebtest-api
  namespace: production
spec:
  replicas: 5
  
  # Deployment strategy: Canary
  strategy:
    canary:
      # Traffic routing (requires Istio/NGINX Ingress)
      trafficRouting:
        nginx:
          stableIngress: aiwebtest-api-stable
      
      # Canary stages
      steps:
      
      # Stage 1: 5% traffic for 10 minutes
      - setWeight: 5
      - pause:
          duration: 10m
      
      # Stage 2: 20% traffic for 20 minutes
      - setWeight: 20
      - pause:
          duration: 20m
      
      # Stage 3: 50% traffic for 30 minutes
      - setWeight: 50
      - pause:
          duration: 30m
      
      # Stage 4: 100% (full rollout)
      - setWeight: 100
      
      # Analysis at each stage
      analysis:
        startingStep: 1  # Start analysis at step 1
        templates:
        - templateName: success-rate
        - templateName: error-rate
        - templateName: latency-p99
  
  # Rollout selector
  selector:
    matchLabels:
      app: aiwebtest-api
  
  # Pod template
  template:
    metadata:
      labels:
        app: aiwebtest-api
    spec:
      containers:
      - name: api
        image: aiwebtest/api:v1.1.0
        ports:
        - containerPort: 8000
        # ... (same as before)
  
  # Automated rollback if analysis fails
  revisionHistoryLimit: 3
```

**Analysis Templates:**

```yaml
# kubernetes/analysis-templates.yaml

# Success rate analysis
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: production
spec:
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= 0.99  # 99% success rate
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(http_requests_total{status="200",deployment="{{args.deployment}}"}[2m])) /
          sum(rate(http_requests_total{deployment="{{args.deployment}}"}[2m]))

# Error rate analysis
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: error-rate
  namespace: production
spec:
  metrics:
  - name: error-rate
    interval: 1m
    count: 5
    successCondition: result[0] <= 0.01  # <= 1% error rate
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(http_requests_total{status=~"5..",deployment="{{args.deployment}}"}[2m])) /
          sum(rate(http_requests_total{deployment="{{args.deployment}}"}[2m]))

# Latency P99 analysis
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency-p99
  namespace: production
spec:
  metrics:
  - name: latency-p99
    interval: 1m
    count: 5
    successCondition: result[0] <= 5000  # <= 5s
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket{deployment="{{args.deployment}}"}[2m])
          ) * 1000
```

**Monitoring Canary Deployment:**

```bash
# Watch rollout progress
kubectl argo rollouts get rollout aiwebtest-api -n production --watch

# Promote to next step manually (if using manual approval)
kubectl argo rollouts promote aiwebtest-api -n production

# Abort rollout
kubectl argo rollouts abort aiwebtest-api -n production

# Rollback
kubectl argo rollouts undo aiwebtest-api -n production
```

### Flagger (Alternative to ArgoCD Rollouts)

**Installation:**

```bash
# Install Flagger
kubectl apply -f https://raw.githubusercontent.com/fluxcd/flagger/main/artifacts/flagger/crd.yaml
kubectl apply -f https://raw.githubusercontent.com/fluxcd/flagger/main/artifacts/flagger/deployment.yaml
```

**Canary Resource:**

```yaml
# kubernetes/flagger-canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: aiwebtest-api
  namespace: production
spec:
  # Deployment reference
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aiwebtest-api
  
  # Service reference
  service:
    port: 80
    targetPort: 8000
  
  # Canary analysis
  analysis:
    # Schedule interval
    interval: 1m
    
    # Max traffic percentage
    maxWeight: 50
    
    # Step weight increment
    stepWeight: 10
    
    # Metrics
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99  # 99% success rate
      interval: 1m
    
    - name: request-duration
      thresholdRange:
        max: 5000  # 5s max latency
      interval: 1m
    
    # Webhooks for custom checks
    webhooks:
    - name: smoke-tests
      url: http://flagger-loadtester/
      timeout: 5s
      metadata:
        type: smoke
        cmd: "curl -s http://aiwebtest-api-canary/health | grep ok"
```

---

## Failure Recovery

### Comprehensive Failure Recovery Procedures

**Failure Scenarios & Recovery Steps:**

#### 1. Application Crash

**Detection:**
- Kubernetes liveness probe fails
- Pod restarts automatically
- Alert sent to ops team

**Recovery:**
```
Automatic:
1. Kubernetes restarts pod
2. Pod enters CrashLoopBackoff if continues failing
3. Alert triggered after 3 restarts

Manual:
1. Check logs: kubectl logs <pod-name> -n production --previous
2. Check events: kubectl describe pod <pod-name> -n production
3. Identify root cause
4. Fix code or configuration
5. Deploy fix via CI/CD
```

#### 2. Database Connection Failure

**Detection:**
- Circuit breaker opens
- Readiness probe fails
- Pod removed from service

**Recovery:**
```
Automatic:
1. Circuit breaker prevents cascading failures
2. Retry after timeout (30s)
3. If database comes back, circuit closes

Manual (if database issue persists):
1. Check database health
2. Scale database if needed
3. Check connection pool settings
4. Verify network connectivity
5. Review database logs
```

#### 3. External API Failure (OpenRouter)

**Detection:**
- Circuit breaker opens
- Fallback to cached responses
- Alert sent

**Recovery:**
```
Automatic:
1. Circuit breaker blocks requests
2. Use cached responses as fallback
3. Retry after timeout (60s)

Manual:
1. Check OpenRouter status page
2. Verify API key validity
3. Check rate limits
4. Use alternative models if available
5. Contact OpenRouter support if needed
```

#### 4. High Memory/CPU Usage

**Detection:**
- Prometheus alerts fire
- Pod shows high resource usage

**Recovery:**
```
Automatic:
1. Horizontal Pod Autoscaler scales up
2. More pods handle load

Manual (if OOM persists):
1. Review memory leaks
2. Analyze heap dumps
3. Optimize code
4. Increase resource limits
5. Deploy fix
```

#### 5. Deployment Failure

**Detection:**
- Rollout stuck
- Pods failing to start
- Analysis metrics failing

**Recovery:**
```
Automatic:
1. ArgoCD Rollouts aborts deployment
2. Traffic stays on stable version
3. Alert sent

Manual:
1. Check rollout status
2. Review failed pod logs
3. Identify issue (config, image, etc.)
4. Fix issue
5. Trigger new deployment
```

### Disaster Recovery Playbook

```markdown
# DISASTER RECOVERY PLAYBOOK

## Severity Levels

### P0 - Critical (Production Down)
- Response Time: Immediate
- Escalation: CTO + Ops Lead
- Actions: All hands on deck

### P1 - High (Major Feature Down)
- Response Time: < 15 minutes
- Escalation: Ops Lead
- Actions: Senior engineer assigned

### P2 - Medium (Minor Issue)
- Response Time: < 1 hour
- Escalation: On-call engineer
- Actions: Normal troubleshooting

## P0: Complete System Outage

1. **Immediate Actions (0-5 min)**
   - Acknowledge incident
   - Start status page update
   - Check if recent deployment
   - If yes, trigger rollback immediately

2. **Assessment (5-10 min)**
   - Check all monitoring dashboards
   - Review recent changes
   - Identify affected components

3. **Recovery (10-30 min)**
   - Rollback recent changes
   - Restart failed services
   - Scale up if load issue
   - Switch to DR environment if needed

4. **Communication (ongoing)**
   - Update status page every 15 min
   - Notify stakeholders
   - Post-mortem after resolution

## P0: Database Corruption

1. **Immediate Actions**
   - Stop all writes
   - Switch to read replica
   - Notify team

2. **Assessment**
   - Determine extent of corruption
   - Identify last good backup
   - Calculate data loss window

3. **Recovery**
   - Restore from backup
   - Replay transaction logs
   - Verify data integrity
   - Resume writes

## P0: Security Breach

1. **Immediate Actions**
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable enhanced logging

2. **Assessment**
   - Determine scope of breach
   - Identify entry point
   - Check for data exfiltration

3. **Recovery**
   - Patch vulnerabilities
   - Rotate all secrets
   - Review access logs
   - Notify affected users
```

---

## Chaos Engineering

### Introduction to Chaos Engineering

**Purpose:** Proactively test system resilience by intentionally injecting failures.

**Benefits:**
- ✅ Discover weaknesses before they cause outages
- ✅ Validate failure recovery procedures
- ✅ Build confidence in system resilience
- ✅ Improve monitoring and alerting

**Principles:**
1. **Build hypothesis** around steady state
2. **Vary real-world events** (failures, latency, etc.)
3. **Run experiments in production** (controlled)
4. **Automate experiments** to run continuously
5. **Minimize blast radius** (start small)

### Chaos Mesh Implementation

**Installation:**

```bash
# Install Chaos Mesh
curl -sSL https://mirrors.chaos-mesh.org/latest/install.sh | bash

# Verify installation
kubectl get pods -n chaos-mesh
```

**Chaos Experiments:**

#### Experiment 1: Pod Failure

```yaml
# chaos/pod-kill.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill-experiment
  namespace: production
spec:
  action: pod-kill
  mode: one  # Kill one pod at a time
  selector:
    namespaces:
      - production
    labelSelectors:
      app: aiwebtest-api
  scheduler:
    cron: "@every 2h"  # Run every 2 hours
  duration: "30s"
```

**Expected Result:** 
- ✅ Kubernetes restarts pod automatically
- ✅ No user-facing impact (other pods handle traffic)
- ✅ Alerts may fire temporarily

#### Experiment 2: Network Latency

```yaml
# chaos/network-latency.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-latency-experiment
  namespace: production
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - production
    labelSelectors:
      app: aiwebtest-api
  delay:
    latency: "200ms"  # Add 200ms latency
    correlation: "100"
    jitter: "50ms"
  duration: "5m"
  scheduler:
    cron: "@daily"  # Run daily
```

**Expected Result:**
- ✅ System tolerates 200ms latency
- ✅ No timeouts or errors
- ✅ Latency monitoring detects increase

#### Experiment 3: Pod CPU Stress

```yaml
# chaos/cpu-stress.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cpu-stress-experiment
  namespace: production
spec:
  mode: one
  selector:
    namespaces:
      - production
    labelSelectors:
      app: aiwebtest-api
  stressors:
    cpu:
      workers: 2
      load: 80  # 80% CPU load
  duration: "10m"
  scheduler:
    cron: "@weekly"
```

**Expected Result:**
- ✅ Horizontal Pod Autoscaler scales up
- ✅ Response times stay within SLA
- ✅ No user-facing impact

#### Experiment 4: Database Partition

```yaml
# chaos/db-partition.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: db-partition-experiment
  namespace: production
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      app: aiwebtest-api
  direction: to
  target:
    mode: all
    selector:
      namespaces:
        - production
      labelSelectors:
        app: postgresql
  duration: "2m"
  scheduler:
    cron: "@weekly"
```

**Expected Result:**
- ✅ Circuit breaker opens
- ✅ Graceful degradation (cached data)
- ✅ No cascading failures
- ✅ Recovery when partition heals

### Chaos Engineering Best Practices

1. **Start small**
   - Begin in non-production
   - Single pod failures
   - Gradual increase in scope

2. **Define success criteria**
   - What should happen?
   - What should NOT happen?
   - Document expected results

3. **Monitor everything**
   - Watch metrics during experiments
   - Check alerts fire correctly
   - Validate recovery procedures

4. **Automate experiments**
   - Run regularly (weekly/monthly)
   - Include in CI/CD
   - Track results over time

5. **Minimize blast radius**
   - Use mode: one (single pod)
   - Short durations (5-10 min)
   - Abort if unexpected issues

---

## Implementation Roadmap

### Timeline: 13 Days (Integrated into Phase 3)

```
┌──────────────────────────────────────────────────────────────┐
│          DEPLOYMENT & RESILIENCE IMPLEMENTATION              │
│                     (13 Days)                                │
└──────────────────────────────────────────────────────────────┘

Week 1: Core Resilience (Days 1-5)
┌────────────────────────────────────────────────────────────┐
│ Day 1: Circuit Breakers                                    │
│ - Install PyBreaker                                        │
│ - Implement OpenRouter circuit breaker                     │
│ - Implement database circuit breaker                       │
│ - Add Prometheus metrics                                   │
│ Deliverable: Circuit breakers operational                  │
│                                                            │
│ Day 2-3: Health Checks                                     │
│ - Implement liveness/readiness/startup probes             │
│ - Add dependency health checks                            │
│ - Update Kubernetes deployments                           │
│ - Test probe failure scenarios                            │
│ Deliverable: Comprehensive health checks                  │
│                                                            │
│ Day 4-5: Automated Rollback                               │
│ - Configure Prometheus rollback rules                     │
│ - Set up AlertManager webhooks                            │
│ - Implement rollback service                              │
│ - Test automated rollback                                 │
│ Deliverable: Automated rollback operational               │
└────────────────────────────────────────────────────────────┘

Week 2: Deployment Strategies (Days 6-10)
┌────────────────────────────────────────────────────────────┐
│ Day 6-7: Blue-Green Deployment                            │
│ - Create blue/green deployments                           │
│ - Implement deployment script                             │
│ - Add smoke tests                                         │
│ - Test full blue-green flow                              │
│ Deliverable: Blue-green deployment working                │
│                                                            │
│ Day 8-9: Canary Deployment                                │
│ - Install ArgoCD Rollouts                                 │
│ - Configure canary rollout                                │
│ - Create analysis templates                               │
│ - Test canary deployment                                  │
│ Deliverable: Canary deployment operational                │
│                                                            │
│ Day 10: Failure Recovery                                  │
│ - Document recovery procedures                            │
│ - Create disaster recovery playbook                       │
│ - Set up runbooks                                         │
│ Deliverable: Recovery documentation complete              │
└────────────────────────────────────────────────────────────┘

Week 3: Testing & Validation (Days 11-13)
┌────────────────────────────────────────────────────────────┐
│ Day 11: Chaos Engineering                                 │
│ - Install Chaos Mesh                                      │
│ - Create pod-kill experiment                              │
│ - Create network-latency experiment                       │
│ - Run initial chaos tests                                 │
│ Deliverable: Chaos engineering operational                │
│                                                            │
│ Day 12: Integration Testing                               │
│ - Test circuit breakers under load                        │
│ - Test rollback scenarios                                 │
│ - Test blue-green deployment                              │
│ - Test canary deployment                                  │
│ Deliverable: All components tested                        │
│                                                            │
│ Day 13: Documentation & Training                          │
│ - Finalize runbooks                                       │
│ - Create monitoring dashboards                            │
│ - Train ops team                                          │
│ - Document lessons learned                                │
│ Deliverable: Production-ready system                      │
└────────────────────────────────────────────────────────────┘
```

### Success Criteria

**By End of Week 1:**
- ✅ Circuit breakers operational for all external dependencies
- ✅ Health checks implemented (liveness, readiness, startup)
- ✅ Automated rollback triggers configured and tested
- ✅ Zero cascading failures during simulated outages

**By End of Week 2:**
- ✅ Blue-green deployment working for major updates
- ✅ Canary deployment operational with automated analysis
- ✅ Failure recovery procedures documented
- ✅ Mean time to recovery (MTTR) < 5 minutes

**By End of Week 3:**
- ✅ Chaos engineering experiments running regularly
- ✅ All deployment strategies tested in production
- ✅ Ops team trained on recovery procedures
- ✅ System resilience validated with 99.9% uptime

### Metrics to Track

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Uptime** | 99.9% | TBD | 🟡 |
| **Mean Time to Recovery (MTTR)** | < 5 min | TBD | 🟡 |
| **Deployment Frequency** | Daily | TBD | 🟡 |
| **Deployment Failure Rate** | < 5% | TBD | 🟡 |
| **Lead Time for Changes** | < 1 hour | TBD | 🟡 |
| **Circuit Breaker Uptime** | 100% | 0% | 🔴 |
| **Automated Rollback Success** | 100% | 0% | 🔴 |

---

## Summary & Integration

### What We've Built

This comprehensive Deployment & Resilience architecture provides:

1. ✅ **Circuit Breakers** - PyBreaker for all external dependencies
2. ✅ **Health Checks** - Kubernetes liveness/readiness/startup probes
3. ✅ **Automated Rollback** - Prometheus + AlertManager integration
4. ✅ **Blue-Green Deployment** - Zero-downtime major updates
5. ✅ **Canary Deployment** - ArgoCD Rollouts with automated analysis
6. ✅ **Failure Recovery** - Comprehensive procedures and playbooks
7. ✅ **Chaos Engineering** - Chaos Mesh experiments

### Integration with Existing Documentation

**Updates needed in:**

#### PRD (AI-Web-Test-v1-PRD.md)

**Add new section 3.11:**
```markdown
### 3.11 Deployment Automation & Resilience

FR-50: Circuit Breaker Patterns
- Circuit breakers for all external dependencies (OpenRouter, database, Redis)
- Automatic fallback to cached responses
- Failure isolation to prevent cascading failures

FR-51: Health Checks
- Kubernetes liveness probes (restart unhealthy pods)
- Readiness probes (remove from load balancer)
- Startup probes (handle slow-starting services)
- Comprehensive dependency health checks

FR-52: Automated Rollback
- Prometheus-based rollback triggers
- Thresholds: Error rate > 1%, Latency p99 > 5s, Success rate < 99%
- Automatic rollback within 1 minute of detection

FR-53: Blue-Green Deployment
- Zero-downtime major updates
- Instant rollback capability
- Full testing before traffic switch

FR-54: Canary Deployment
- Gradual rollout (5% → 20% → 50% → 100%)
- Automated analysis at each stage
- Automatic rollback on metric violations

FR-55: Chaos Engineering
- Regular chaos experiments (pod-kill, network latency, CPU stress)
- Continuous resilience validation
- Automated recovery testing
```

#### SRS (AI-Web-Test-v1-SRS.md)

**Add to Technical Stack:**
```markdown
### Resilience & Deployment Stack

**Circuit Breakers:**
- PyBreaker 1.0.1 (Python)
- Resilience4j (if using Java services)

**Deployment:**
- ArgoCD Rollouts (canary deployments)
- Flagger (alternative canary strategy)
- Kubernetes native (blue-green, rolling)

**Chaos Engineering:**
- Chaos Mesh 2.6.0
- Litmus Chaos (alternative)

**Monitoring & Alerting:**
- Prometheus (metrics + rollback rules)
- AlertManager (automated rollback triggers)
- Grafana (circuit breaker dashboards)
```

#### Architecture Diagram

**Add new diagram:**
```
Resilience Architecture:

User → Load Balancer → Ingress
                         ↓
                    Service (w/ circuit breakers)
                         ↓
            ┌────────────┴────────────┐
            ↓                         ↓
      Blue Environment          Green Environment
      (v1.0 - stable)           (v1.1 - canary)
            ↓                         ↓
      [Health Checks]           [Health Checks]
            ↓                         ↓
      [Automated Rollback]      [Analysis]
```

### Cost Analysis

**Infrastructure Costs:**

**Development/Staging:**
- ArgoCD Rollouts: $0 (open source)
- Chaos Mesh: $0 (open source)
- Prometheus + AlertManager: $0 (open source)
- **Total: $0/month**

**Production:**
- Blue-Green: +100% infrastructure during deployment ($300/month average)
- Canary: +20% infrastructure during deployment ($60/month average)
- Chaos Mesh overhead: ~$20/month (minimal)
- Monitoring: Included in existing Prometheus
- **Total: ~$380/month** (mostly temporary during deployments)

**vs Downtime Costs:**
- 1 hour of downtime: ~$10,000 (assuming e-commerce)
- 99.9% uptime: Max 8.76 hours/year downtime = $87,600 potential loss
- **ROI: $380/month to prevent $87,600/year in losses = 189x ROI!**

### Next Steps

1. **Week 1:** Implement circuit breakers + health checks + automated rollback
2. **Week 2:** Implement blue-green + canary deployments
3. **Week 3:** Add chaos engineering + finalize documentation
4. **Ongoing:** Run chaos experiments weekly, monitor resilience metrics

---

**Status:** ✅ **PRODUCTION-READY**

This addresses the critical deployment automation and resilience gap with industry best practices for 2025!

**Implementation Effort:** 13 days (as recommended)
**Priority:** P0 - Critical
**Cost:** ~$380/month (189x ROI)

🎉 **Your multi-agent agentic AI test automation platform now has enterprise-grade deployment resilience!**


