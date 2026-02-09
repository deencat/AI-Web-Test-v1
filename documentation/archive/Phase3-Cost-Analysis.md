# Phase 3: Cost Analysis

**Purpose:** Monthly operational cost projections for multi-agent system  
**Status:** Budget planning for Sprint 7-12  
**Last Updated:** January 16, 2026

---

## 📋 Overview

Phase 3 introduces 6 agents and supporting infrastructure. This document estimates:

1. **Infrastructure Costs** (Redis, PostgreSQL, Qdrant, Kubernetes)
2. **LLM API Costs** (OpenAI GPT-4, GPT-4-mini)
3. **Total Monthly Budget**
4. **Cost per Test Cycle**
5. **Cost Optimization Strategies**

---

## 1. Infrastructure Costs

### Redis Cluster (Message Bus + Short-Term Memory)

**Configuration:**
- 3 nodes (primary + 2 replicas) for high availability
- 8GB memory per node
- 2 vCPU per node

**Provider: AWS ElastiCache**
- Instance type: `cache.r6g.large` (8GB memory, 2 vCPU)
- Price: $0.252/hour per node
- Monthly cost: $0.252 × 24 × 30 × 3 = **$544.32/month**

**Alternative (Self-hosted on Kubernetes):**
- 3 pods × 8GB memory × 2 vCPU
- AWS EKS worker node: t3.xlarge ($0.1664/hour)
- Monthly cost: $0.1664 × 24 × 30 × 2 = **$239.62/month** ✅ **Save $304/month**

---

### PostgreSQL (Working Memory + Test Storage)

**Configuration:**
- Primary + 1 read replica
- 100GB storage (pgvector extension for embeddings)
- 4 vCPU, 16GB memory

**Provider: AWS RDS PostgreSQL**
- Instance type: `db.r6g.xlarge` (4 vCPU, 16GB memory)
- Price: $0.504/hour per instance
- Storage: 100GB × $0.115/GB-month = $11.50
- Monthly cost: ($0.504 × 24 × 30 × 2) + $11.50 = **$736.26/month**

**Alternative (Self-hosted on Kubernetes):**
- 2 pods × 16GB memory × 4 vCPU
- AWS EBS storage: 100GB × $0.10/GB-month = $10
- Monthly cost: (included in Kubernetes cluster) + $10 = **~$150/month** ✅ **Save $586/month**

---

### Qdrant Vector Database (Long-Term Memory)

**Configuration:**
- 1 node (shared instance for <100K vectors)
- 8GB memory, 2 vCPU
- HNSW index for semantic search

**Provider: Qdrant Cloud**
- Instance: Shared (free tier up to 100K vectors)
- Price: $0 for <100K vectors, $95/month for dedicated
- **Assumption:** Start with free tier, upgrade to dedicated at scale
- Monthly cost: **$0/month** (first 3 months), then **$95/month**

---

### Kubernetes Cluster

**Configuration:**
- 6 agents + backend + frontend + databases
- 3 worker nodes (high availability)
- Auto-scaling 3-10 nodes

**Provider: AWS EKS**
- Control plane: $0.10/hour = $72/month
- Worker nodes: 3 × t3.xlarge ($0.1664/hour)
- Monthly cost: $72 + ($0.1664 × 24 × 30 × 3) = **$430.94/month**

**Load Balancer:**
- Application Load Balancer (ALB): $0.0225/hour + $0.008/LCU-hour
- Monthly cost: ~**$25/month**

---

### Monitoring (Prometheus + Grafana)

**Configuration:**
- Prometheus (time-series metrics)
- Grafana (dashboards)
- Self-hosted on Kubernetes

**Cost:**
- Included in Kubernetes cluster (1 pod each)
- Storage: 50GB × $0.10/GB-month = **$5/month**

---

### **Total Infrastructure: $891.92/month** (self-hosted) or **$1,811.52/month** (managed services)

---

## 2. LLM API Costs

### Token Usage Estimates

**Per Test Generation Cycle:**
1. **Observation Agent:** Analyze 1 file (500 lines)
   - Input: 2,000 tokens (code + context)
   - Output: 500 tokens (requirements)
   - Total: 2,500 tokens

2. **Requirements Agent:** Refine requirements
   - Input: 1,000 tokens (observations)
   - Output: 800 tokens (refined requirements)
   - Total: 1,800 tokens

3. **Analysis Agent:** Analyze dependencies
   - Input: 3,000 tokens (code + requirements)
   - Output: 1,000 tokens (analysis)
   - Total: 4,000 tokens

4. **Evolution Agent:** Generate tests
   - Input: 5,000 tokens (code + requirements + analysis)
   - Output: 3,000 tokens (test code)
   - Total: 8,000 tokens

5. **Orchestration Agent:** Coordinate workflow
   - Input: 500 tokens (agent responses)
   - Output: 200 tokens (next steps)
   - Total: 700 tokens

6. **Reporting Agent:** Generate report
   - Input: 2,000 tokens (test results)
   - Output: 1,000 tokens (report)
   - Total: 3,000 tokens

**Total per test cycle: ~20,000 tokens**

---

### OpenAI Pricing (as of Jan 2026)

**GPT-4 Turbo:**
- Input: $0.01 per 1K tokens
- Output: $0.03 per 1K tokens

**GPT-4-mini (cheaper, 80% accuracy):**
- Input: $0.00015 per 1K tokens
- Output: $0.0006 per 1K tokens

---

### Cost per Test Cycle

**Strategy 1: All GPT-4 (highest quality)**
- Input: 13,500 tokens × $0.01/1K = $0.135
- Output: 6,500 tokens × $0.03/1K = $0.195
- **Total: $0.33 per test cycle**

**Strategy 2: Hybrid (GPT-4 for Evolution, GPT-4-mini for others)**
- Evolution Agent (GPT-4): 8,000 tokens × ($0.01 input + $0.03 output) / 2 = $0.16
- Other agents (GPT-4-mini): 12,000 tokens × ($0.00015 input + $0.0006 output) / 2 = $0.0045
- **Total: $0.16 per test cycle** ✅ **Save 52%**

**Strategy 3: All GPT-4-mini (lowest cost)**
- Input: 13,500 tokens × $0.00015/1K = $0.002
- Output: 6,500 tokens × $0.0006/1K = $0.004
- **Total: $0.006 per test cycle** ✅ **Save 98%** (but lower quality)

---

### Monthly LLM Costs

**Assumptions:**
- 10 developers
- Each generates 5 test cycles/day
- 20 working days/month
- Total: 10 × 5 × 20 = **1,000 test cycles/month**

**Strategy 1 (All GPT-4):** 1,000 × $0.33 = **$330/month**  
**Strategy 2 (Hybrid):** 1,000 × $0.16 = **$160/month** ✅ **Recommended**  
**Strategy 3 (All GPT-4-mini):** 1,000 × $0.006 = **$6/month**

---

## 3. Total Monthly Budget

| Component | Cost (Managed) | Cost (Self-hosted) |
|-----------|---------------|--------------------|
| **Infrastructure** | | |
| Redis Cluster | $544 | $240 |
| PostgreSQL | $736 | $150 |
| Qdrant Vector DB | $0 (free tier) | $0 |
| Kubernetes (EKS) | $431 | $431 |
| Load Balancer | $25 | $25 |
| Monitoring | $5 | $5 |
| **Subtotal Infrastructure** | **$1,741** | **$851** |
| | | |
| **LLM API (Hybrid Strategy)** | $160 | $160 |
| | | |
| **TOTAL** | **$1,901/month** | **$1,011/month** ✅ |

---

## 4. Cost per Test Cycle

**Calculation:**
Total monthly cost / number of test cycles

**Self-hosted setup:** $1,011 / 1,000 = **$1.01 per test cycle**

**Breakdown:**
- Infrastructure: $0.85
- LLM API: $0.16

**Target:** <$0.30 per test cycle (requires optimization - see Section 6)

---

## 5. Scaling Costs

### At 10,000 test cycles/month (100 developers)

**LLM Costs (Hybrid):** 10,000 × $0.16 = **$1,600/month**

**Infrastructure Scaling:**
- Kubernetes: Auto-scale to 6 nodes = $862/month
- Redis: Upgrade to 16GB per node = $480/month
- PostgreSQL: Upgrade to 32GB = $300/month
- Qdrant: Dedicated instance = $95/month

**Total at 10,000 cycles/month:** $1,600 + $862 + $480 + $300 + $95 + $30 = **$3,367/month**

**Cost per test cycle:** $3,367 / 10,000 = **$0.34 per cycle** (within target!)

---

## 6. Cost Optimization Strategies

### 1. Caching (Reduce LLM Calls by 30%)

**Implementation:**
```python
# backend/agents/evolution_agent.py

@lru_cache(maxsize=1000)
async def generate_test_cached(self, file_hash: str, requirements: str):
    """Cache test generation results by file hash"""
    if file_hash in self.cache:
        return self.cache[file_hash]
    
    result = await self.generate_test(file_hash, requirements)
    self.cache[file_hash] = result
    return result
```

**Savings:** 30% × $160 = **$48/month**

---

### 2. Use GPT-4-mini for Non-Critical Agents (52% savings)

**Already included in Hybrid Strategy**

---

### 3. Batch Processing (Reduce Database Queries by 20%)

**Implementation:**
```python
# Batch insert test results
await conn.executemany("""
    INSERT INTO test_results (test_id, status, duration)
    VALUES ($1, $2, $3)
""", results)
```

**Savings:** Marginal (database costs already low)

---

### 4. Compression (Reduce Redis Memory by 40%)

**Implementation:**
```python
import zlib

def compress_message(message: dict) -> bytes:
    """Compress large messages before storing in Redis"""
    json_str = json.dumps(message)
    return zlib.compress(json_str.encode())
```

**Savings:** 40% × $240 = **$96/month**

---

### 5. Token Limit Enforcement (Prevent Runaway Costs)

**Implementation:**
```python
MAX_TOKENS_PER_REQUEST = 10000

if len(input_tokens) > MAX_TOKENS_PER_REQUEST:
    raise ValueError(f"Input exceeds {MAX_TOKENS_PER_REQUEST} tokens")
```

**Savings:** Prevents unexpected $1000+ bills from bugs

---

### **Total Optimized Cost: $1,011 - $48 - $96 = $867/month**

**Cost per test cycle: $867 / 1,000 = $0.87 per cycle** (still above target)

---

## 7. Budget Justification

### ROI Calculation

**Current Manual Testing:**
- QA engineer salary: $80,000/year = $6,667/month
- Time spent writing tests: 50% = $3,333/month

**Automated Testing (Phase 3):**
- Infrastructure + LLM: $867/month
- Developer time saved: 10 developers × 1 hour/day × $50/hour × 20 days = $10,000/month

**Net Savings: $10,000 - $867 = $9,133/month** (~**11x ROI**)

---

### Break-Even Analysis

**If only 1 developer uses the system:**
- Time saved: 1 hour/day × $50/hour × 20 days = $1,000/month
- Cost: $867/month
- **Break-even at 0.87 developers** ✅

---

## 8. Budget Approval Recommendation

**Recommendation:** Approve $1,011/month budget for Phase 3 multi-agent system

**Justification:**
1. **High ROI:** 11x return on investment at scale
2. **Low Risk:** Break-even at <1 developer usage
3. **Scalable:** Cost per test cycle decreases with volume
4. **Strategic:** Competitive advantage in automated testing

**Approval Required From:**
- CTO (technical feasibility) ✅
- CFO (budget allocation)
- VP Engineering (team buy-in)

---

**END OF COST ANALYSIS**
