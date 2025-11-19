# AI-Web-Test v1 - Operational Runbooks

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

This document defines the **comprehensive operational runbooks** for the AI-Web-Test v1 platform, providing step-by-step troubleshooting guides, incident response procedures, and recovery playbooks for production operations.

### Key Operational Runbook Capabilities

| Component | Coverage | Purpose |
|-----------|----------|---------|
| **Agent Failure Recovery** | 6 agents | Detect, diagnose, restart agents |
| **Database Issues** | Connection loss, slowness | Restore connectivity, optimize queries |
| **API Outages** | OpenRouter API | Fallback strategies, circuit breaker |
| **Performance Issues** | High latency, low throughput | Investigate, optimize, scale |
| **Model Degradation** | Accuracy drop, drift | Retrain, rollback, A/B test |
| **Security Incidents** | Breaches, attacks | Contain, investigate, remediate |
| **Disaster Recovery** | Complete system failure | Restore from backups, failover |

### Implementation Timeline
- **Total Effort**: 3 days
- **Phase 1** (Day 1): Agent & Database Runbooks
- **Phase 2** (Day 2): API Outage & Performance Runbooks
- **Phase 3** (Day 3): Model Degradation & Disaster Recovery

---

## Table of Contents
1. [Agent Failure Recovery](#agent-failure-recovery)
2. [Database Connection Loss](#database-connection-loss)
3. [OpenRouter API Outage](#openrouter-api-outage)
4. [High Latency Investigation](#high-latency-investigation)
5. [Model Performance Degradation](#model-performance-degradation)
6. [Security Incident Response](#security-incident-response)
7. [Disaster Recovery](#disaster-recovery)
8. [On-Call Procedures](#on-call-procedures)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Summary & Integration](#summary--integration)

---

## Agent Failure Recovery

### Runbook 1: Requirements Agent Failure

**Symptoms**:
- Test generation requests return 500 errors
- Prometheus alert: `agent_health{agent="requirements_agent"} == 0`
- Logs show: `RequirementsAgent is not responding`

**Diagnosis Steps**:

```bash
# 1. Check agent pod status
kubectl get pods -n aiwebtest -l app=requirements-agent

# 2. Check agent logs
kubectl logs -n aiwebtest -l app=requirements-agent --tail=100

# 3. Check agent metrics
curl http://prometheus:9090/api/v1/query?query=agent_health{agent="requirements_agent"}

# 4. Check OpenRouter API connectivity
kubectl exec -n aiwebtest requirements-agent-xxx -- curl -I https://openrouter.ai/api/v1/health
```

**Recovery Steps**:

```bash
# Step 1: Restart agent pod
kubectl rollout restart deployment/requirements-agent -n aiwebtest

# Step 2: Wait for pod to be ready (30-60 seconds)
kubectl wait --for=condition=ready pod -l app=requirements-agent -n aiwebtest --timeout=60s

# Step 3: Verify agent health
curl http://requirements-agent:8000/health

# Step 4: Test agent with sample request
curl -X POST http://requirements-agent:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"requirements_text": "Test user login"}'

# Step 5: Check metrics dashboard
# Grafana > Agents Dashboard > Requirements Agent > Success Rate
```

**Escalation**:
- If restart fails after 3 attempts: Page on-call engineer
- If OpenRouter API is down: Switch to fallback model (see Runbook 3)
- If persistent issue: Rollback to previous deployment

**Prevention**:
- Enable agent health checks (liveness, readiness probes)
- Set up circuit breakers for OpenRouter API calls
- Implement retry logic with exponential backoff

---

### Runbook 2: Generation Agent Failure

**Symptoms**:
- Tests generated but with low quality (confidence < 0.7)
- Prometheus alert: `agent_confidence{agent="generation_agent"} < 0.7`
- Slow response times (>60 seconds)

**Diagnosis Steps**:

```bash
# 1. Check agent pod resource usage
kubectl top pod -n aiwebtest -l app=generation-agent

# 2. Check agent logs for errors
kubectl logs -n aiwebtest -l app=generation-agent --tail=200 | grep ERROR

# 3. Check OpenRouter API rate limits
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/usage

# 4. Check agent decision logs
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT * FROM agent_decisions WHERE agent_id LIKE 'generation%' ORDER BY created_at DESC LIMIT 10;"
```

**Recovery Steps**:

```bash
# Step 1: Scale up agent replicas (if resource constrained)
kubectl scale deployment/generation-agent -n aiwebtest --replicas=3

# Step 2: Clear agent cache (if stale data)
kubectl exec -n aiwebtest generation-agent-xxx -- redis-cli FLUSHDB

# Step 3: Restart agent pods
kubectl rollout restart deployment/generation-agent -n aiwebtest

# Step 4: Verify generation quality
# Run test generation request and check confidence score

# Step 5: Monitor metrics
# Grafana > Agents Dashboard > Generation Agent > Confidence Score (should be >0.85)
```

**Escalation**:
- If confidence remains low: Check OpenRouter API model status
- If resource constrained: Scale horizontally (add more pods)
- If model issue: Switch to different model version

**Prevention**:
- Set resource limits (CPU: 2 cores, Memory: 4GB) and requests
- Enable horizontal pod autoscaling (HPA) based on CPU/memory
- Monitor model performance metrics daily

---

### Runbook 3: Execution Agent Failure

**Symptoms**:
- Tests stuck in "running" status for >10 minutes
- Prometheus alert: `test_execution_duration > 600`
- Browser automation failures (Chrome/Firefox crashes)

**Diagnosis Steps**:

```bash
# 1. Check active test executions
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT execution_id, started_at, NOW() - started_at AS duration FROM test_executions WHERE result = 'running' ORDER BY started_at;"

# 2. Check Selenium Grid status
kubectl exec -n aiwebtest execution-agent-xxx -- curl http://selenium-hub:4444/status

# 3. Check browser pods
kubectl get pods -n aiwebtest -l app=selenium-node

# 4. Check execution agent logs
kubectl logs -n aiwebtest -l app=execution-agent --tail=100
```

**Recovery Steps**:

```bash
# Step 1: Cancel stuck executions
psql -h postgres -U postgres -d aiwebtest \
  -c "UPDATE test_executions SET result = 'error', error_message = 'Execution timeout' WHERE result = 'running' AND started_at < NOW() - INTERVAL '10 minutes';"

# Step 2: Restart Selenium Grid
kubectl rollout restart deployment/selenium-hub -n aiwebtest
kubectl rollout restart deployment/selenium-node-chrome -n aiwebtest
kubectl rollout restart deployment/selenium-node-firefox -n aiwebtest

# Step 3: Restart execution agent
kubectl rollout restart deployment/execution-agent -n aiwebtest

# Step 4: Verify Selenium Grid
kubectl exec -n aiwebtest execution-agent-xxx -- curl http://selenium-hub:4444/status

# Step 5: Run sample test
# Execute a simple test to verify browser automation works
```

**Escalation**:
- If Selenium Grid is down: Scale up Selenium nodes
- If browser crashes persist: Check resource limits on Selenium nodes
- If persistent issue: Investigate test code for browser compatibility

**Prevention**:
- Set execution timeout (10 minutes max)
- Monitor Selenium Grid capacity (max 10 concurrent sessions per node)
- Enable Selenium Grid auto-scaling based on queue length

---

## Database Connection Loss

### Runbook 4: PostgreSQL Connection Loss

**Symptoms**:
- API returns 500 errors with "Connection refused"
- Prometheus alert: `pg_up == 0`
- Logs show: `psycopg2.OperationalError: could not connect to server`

**Diagnosis Steps**:

```bash
# 1. Check PostgreSQL pod status
kubectl get pods -n aiwebtest -l app=postgres

# 2. Check PostgreSQL logs
kubectl logs -n aiwebtest -l app=postgres --tail=100

# 3. Check PostgreSQL connection from app
kubectl exec -n aiwebtest backend-xxx -- psql -h postgres -U postgres -d aiwebtest -c "SELECT 1;"

# 4. Check PgBouncer status
kubectl exec -n aiwebtest pgbouncer-xxx -- psql -p 6432 -U postgres -d pgbouncer -c "SHOW POOLS;"

# 5. Check connection pool stats
kubectl exec -n aiwebtest pgbouncer-xxx -- psql -p 6432 -U postgres -d pgbouncer -c "SHOW STATS;"
```

**Recovery Steps**:

```bash
# Step 1: Restart PostgreSQL pod (if crashed)
kubectl rollout restart statefulset/postgres -n aiwebtest

# Step 2: Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n aiwebtest --timeout=120s

# Step 3: Restart PgBouncer (connection pooler)
kubectl rollout restart deployment/pgbouncer -n aiwebtest

# Step 4: Restart backend pods (to reset connections)
kubectl rollout restart deployment/backend -n aiwebtest

# Step 5: Verify connectivity
psql -h pgbouncer -p 6432 -U postgres -d aiwebtest -c "SELECT NOW();"

# Step 6: Check connection pool utilization
# Grafana > Database Dashboard > PgBouncer > Active Connections (should be 10-20)
```

**Escalation**:
- If PostgreSQL won't start: Check disk space, corruption
- If connection pool exhausted: Increase PgBouncer pool size
- If persistent issue: Failover to read replica or backup

**Prevention**:
- Enable PostgreSQL high availability (Patroni or Stolon)
- Set connection pool limits (25 default, 1000 max clients)
- Monitor connection pool utilization (alert at >80%)
- Enable automatic failover with health checks

---

### Runbook 5: Database Performance Issues

**Symptoms**:
- API response times >5 seconds
- Prometheus alert: `http_request_duration_p95 > 5000`
- Logs show: `Query execution time: 8.5 seconds`

**Diagnosis Steps**:

```bash
# 1. Check slow queries
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 2. Check active queries
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT pid, NOW() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' AND query NOT LIKE '%pg_stat%' ORDER BY duration DESC;"

# 3. Check database size
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;"

# 4. Check table bloat
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# 5. Check index usage
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes WHERE schemaname = 'public' AND idx_scan < 100 ORDER BY idx_scan;"
```

**Recovery Steps**:

```bash
# Step 1: Kill long-running queries (if blocking)
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND NOW() - query_start > INTERVAL '5 minutes' AND query NOT LIKE '%pg_stat%';"

# Step 2: Analyze slow queries and add indexes
# Example: If test_executions table scan is slow
psql -h postgres -U postgres -d aiwebtest \
  -c "CREATE INDEX CONCURRENTLY idx_test_executions_created_at ON test_executions(created_at DESC);"

# Step 3: VACUUM tables to reclaim space
psql -h postgres -U postgres -d aiwebtest \
  -c "VACUUM ANALYZE test_executions;"

# Step 4: Refresh materialized views
psql -h postgres -U postgres -d aiwebtest \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_stats;"

# Step 5: Monitor query performance
# Grafana > Database Dashboard > Query Performance > p95 Latency (should drop to <100ms)
```

**Escalation**:
- If queries remain slow: Review query execution plans (EXPLAIN ANALYZE)
- If database is undersized: Scale up PostgreSQL instance (CPU, memory)
- If disk I/O is slow: Migrate to faster storage (SSD, NVMe)

**Prevention**:
- Run VACUUM ANALYZE daily (automated)
- Monitor query performance with pg_stat_statements
- Set statement_timeout (30 seconds for API queries)
- Enable query logging for slow queries (>1 second)

---

## OpenRouter API Outage

### Runbook 6: OpenRouter API Complete Outage

**Symptoms**:
- All agent operations fail
- Prometheus alert: `openrouter_api_up == 0`
- Logs show: `OpenRouter API is unreachable`

**Diagnosis Steps**:

```bash
# 1. Check OpenRouter API status page
curl -I https://openrouter.ai/api/v1/health

# 2. Check circuit breaker status
curl http://backend:8000/api/v1/health | jq '.circuit_breakers.openrouter'

# 3. Check error rate
curl http://prometheus:9090/api/v1/query?query=openrouter_api_errors_total

# 4. Check OpenRouter status page
# Visit: https://status.openrouter.ai
```

**Recovery Steps**:

```bash
# Step 1: Switch to fallback model (local Ollama or different provider)
kubectl set env deployment/backend -n aiwebtest \
  OPENROUTER_FALLBACK=true \
  OLLAMA_URL=http://ollama:11434

# Step 2: Update circuit breaker to open state
curl -X POST http://backend:8000/api/v1/admin/circuit-breaker/openrouter/open

# Step 3: Notify users (via status page)
# Update https://status.aiwebtest.com with:
# "OpenRouter API is experiencing issues. Switched to fallback model. Response times may be slower."

# Step 4: Monitor fallback performance
# Grafana > Agents Dashboard > Model Provider > Current Provider (should show "ollama")

# Step 5: When OpenRouter recovers, switch back
kubectl set env deployment/backend -n aiwebtest \
  OPENROUTER_FALLBACK=false

curl -X POST http://backend:8000/api/v1/admin/circuit-breaker/openrouter/close
```

**Escalation**:
- If fallback also fails: Queue requests for retry later
- If outage exceeds 1 hour: Consider temporary service degradation
- If persistent issue: Contact OpenRouter support

**Prevention**:
- Enable circuit breaker for OpenRouter API calls (fail fast)
- Set up fallback model (local Ollama or different provider)
- Monitor OpenRouter API uptime (external monitoring)
- Cache recent responses (TTL 5 minutes) for repeated requests

---

### Runbook 7: OpenRouter API Rate Limit

**Symptoms**:
- 429 errors from OpenRouter API
- Prometheus alert: `openrouter_api_rate_limit_errors > 10`
- Logs show: `Rate limit exceeded. Retry after 60 seconds.`

**Diagnosis Steps**:

```bash
# 1. Check current API usage
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/usage

# 2. Check request rate
curl http://prometheus:9090/api/v1/query?query=rate(openrouter_api_requests_total[5m])

# 3. Check agent request queues
kubectl exec -n aiwebtest backend-xxx -- redis-cli LLEN agent:requests:queue
```

**Recovery Steps**:

```bash
# Step 1: Enable request queuing
kubectl set env deployment/backend -n aiwebtest \
  OPENROUTER_QUEUE_ENABLED=true \
  OPENROUTER_MAX_REQUESTS_PER_MINUTE=50

# Step 2: Throttle incoming requests
# Update Nginx rate limit to match OpenRouter API limit
kubectl edit configmap nginx-config -n aiwebtest
# Set: limit_req_rate=50r/m;

# Step 3: Clear request queue gradually
# Backend will process queued requests at throttled rate

# Step 4: Monitor request processing
# Grafana > Agents Dashboard > OpenRouter API > Request Rate (should be <50/min)

# Step 5: Notify users of slower response times
# Update https://status.aiwebtest.com
```

**Escalation**:
- If queue grows too large (>1000): Reject new requests temporarily
- If persistent rate limiting: Upgrade OpenRouter API plan
- If urgent: Use multiple API keys for load balancing

**Prevention**:
- Set request rate limit to 80% of OpenRouter API limit
- Enable request queuing with Redis (max queue size: 1000)
- Monitor API usage daily (alert at >80% of limit)
- Use multiple API keys with round-robin load balancing

---

## High Latency Investigation

### Runbook 8: API High Latency (p95 >2s)

**Symptoms**:
- Prometheus alert: `http_request_duration_p95 > 2000`
- Users report slow response times
- Grafana dashboard shows latency spike

**Diagnosis Steps**:

```bash
# 1. Check endpoint latency breakdown
curl http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))

# 2. Check distributed tracing
# Jaeger UI: http://jaeger:16686
# Search for slow traces (duration >2s)

# 3. Check agent processing times
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT agent_type, AVG(execution_time_ms), MAX(execution_time_ms) FROM agent_decisions WHERE created_at > NOW() - INTERVAL '10 minutes' GROUP BY agent_type;"

# 4. Check database query times
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements WHERE mean_exec_time > 1000 ORDER BY mean_exec_time DESC LIMIT 5;"

# 5. Check OpenRouter API latency
curl http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(openrouter_api_duration_seconds_bucket[5m]))
```

**Recovery Steps**:

```bash
# Step 1: Identify bottleneck from tracing
# Check Jaeger trace spans to find longest operation

# Step 2: If database is slow (queries >1s)
# Run: See Runbook 5 (Database Performance Issues)

# Step 3: If OpenRouter API is slow (>10s)
# Switch to faster model or enable caching
kubectl set env deployment/backend -n aiwebtest \
  OPENROUTER_CACHE_ENABLED=true \
  OPENROUTER_CACHE_TTL=300

# Step 4: If agent processing is slow
# Scale up agent replicas
kubectl scale deployment/generation-agent -n aiwebtest --replicas=3

# Step 5: If network latency is high
# Check inter-service network latency
kubectl exec -n aiwebtest backend-xxx -- ping -c 10 postgres
kubectl exec -n aiwebtest backend-xxx -- ping -c 10 redis

# Step 6: Monitor improvements
# Grafana > API Dashboard > p95 Latency (should drop to <500ms)
```

**Escalation**:
- If latency persists: Review application code for inefficiencies
- If infrastructure issue: Scale up resources (CPU, memory, network)
- If external dependency: Contact provider support

**Prevention**:
- Enable caching for frequently accessed data (Redis)
- Optimize database queries (indexes, materialized views)
- Use CDN for static assets
- Enable request compression (gzip)
- Monitor latency percentiles (p50, p95, p99) in real-time

---

### Runbook 9: Test Execution High Latency

**Symptoms**:
- Tests take >5 minutes to execute (expected <2 minutes)
- Prometheus alert: `test_execution_duration_p95 > 300`
- Users complain of slow test runs

**Diagnosis Steps**:

```bash
# 1. Check test execution times
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT test_id, execution_time, browser FROM test_executions WHERE execution_time > 300 ORDER BY created_at DESC LIMIT 10;"

# 2. Check Selenium Grid capacity
kubectl exec -n aiwebtest selenium-hub-xxx -- curl http://localhost:4444/status | jq '.value.nodes[].slots'

# 3. Check browser node resource usage
kubectl top pod -n aiwebtest -l app=selenium-node

# 4. Check test code complexity
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT test_id, title, LENGTH(code) AS code_length FROM test_cases WHERE test_id IN (SELECT test_id FROM test_executions WHERE execution_time > 300 LIMIT 5);"
```

**Recovery Steps**:

```bash
# Step 1: Scale up Selenium nodes
kubectl scale deployment/selenium-node-chrome -n aiwebtest --replicas=5
kubectl scale deployment/selenium-node-firefox -n aiwebtest --replicas=3

# Step 2: Enable parallel test execution
# Update backend config
kubectl set env deployment/backend -n aiwebtest \
  MAX_PARALLEL_TESTS=10

# Step 3: Optimize slow tests
# Review and optimize test code for slow tests
# Consider splitting long tests into multiple shorter tests

# Step 4: Enable test result caching
# Cache test results for unchanged tests
kubectl set env deployment/backend -n aiwebtest \
  TEST_RESULT_CACHE_ENABLED=true \
  TEST_RESULT_CACHE_TTL=3600

# Step 5: Monitor execution times
# Grafana > Test Execution Dashboard > Execution Time p95 (should drop to <120s)
```

**Escalation**:
- If Selenium Grid is at capacity: Add more nodes or upgrade instance types
- If test code is inefficient: Refactor tests (remove unnecessary waits, optimize selectors)
- If browser is slow: Check browser versions, consider headless mode

**Prevention**:
- Set test timeout (5 minutes max)
- Monitor Selenium Grid capacity (alert at >80% utilization)
- Enable parallel test execution (max 10 concurrent)
- Use headless browsers for faster execution
- Cache test results for unchanged tests

---

## Model Performance Degradation

### Runbook 10: Model Accuracy Drop

**Symptoms**:
- Prometheus alert: `model_accuracy < 0.85`
- Generated tests have low quality (confidence <0.7)
- Users report incorrect test scenarios

**Diagnosis Steps**:

```bash
# 1. Check current model accuracy
curl http://prometheus:9090/api/v1/query?query=model_accuracy

# 2. Check data drift
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT * FROM data_drift_reports ORDER BY created_at DESC LIMIT 1;"

# 3. Check concept drift
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT created_at, accuracy, accuracy_drop_percent FROM concept_drift_checks ORDER BY created_at DESC LIMIT 10;"

# 4. Check prediction logs
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT model_name, model_version, AVG(confidence), COUNT(*) FROM predictions WHERE created_at > NOW() - INTERVAL '24 hours' GROUP BY model_name, model_version;"

# 5. Check MLflow model registry
# MLflow UI: http://mlflow:5000
# Compare current model vs baseline
```

**Recovery Steps**:

```bash
# Step 1: Rollback to previous model version
# MLflow UI > Models > generation_model > Transition to Production
curl -X POST http://mlflow:5000/api/2.0/mlflow/transition-model-version-stage \
  -d '{"name": "generation_model", "version": "3", "stage": "Production"}'

# Step 2: Update backend to use previous model
kubectl set env deployment/backend -n aiwebtest \
  MLFLOW_MODEL_VERSION=3

# Step 3: Restart backend pods
kubectl rollout restart deployment/backend -n aiwebtest

# Step 4: Trigger model retraining
curl -X POST http://airflow:8080/api/v1/dags/model_retraining/dagRuns

# Step 5: Monitor model accuracy
# Grafana > ML Monitoring Dashboard > Model Accuracy (should recover to >0.85)

# Step 6: Compare retrained model with rolled-back model
# MLflow UI > Experiments > Compare Runs
```

**Escalation**:
- If rollback doesn't improve: Investigate training data quality
- If drift detected: Collect new training data from production
- If persistent issue: Review model architecture or hyperparameters

**Prevention**:
- Monitor model accuracy daily (alert at <0.85)
- Enable data drift detection (weekly checks)
- Enable concept drift detection (daily checks)
- Automate model retraining (weekly or on drift detected)
- Maintain model registry with versioning (MLflow)

---

### Runbook 11: Data Drift Detected

**Symptoms**:
- Prometheus alert: `model_data_drift_detected == 1`
- Evidently AI report shows >20% drifted features
- Model predictions have lower confidence

**Diagnosis Steps**:

```bash
# 1. Check latest data drift report
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT * FROM data_drift_reports ORDER BY created_at DESC LIMIT 1;"

# 2. Review Evidently AI HTML report
# S3: s3://aiwebtest-ml-reports/data-drift/report_YYYYMMDD_HHMMSS.html
aws s3 cp s3://aiwebtest-ml-reports/data-drift/report_$(date +%Y%m%d)_*.html ./drift_report.html

# 3. Check drifted features
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT feature_name, drift_score, drift_detected FROM data_drift_features WHERE report_id = (SELECT id FROM data_drift_reports ORDER BY created_at DESC LIMIT 1) AND drift_detected = true;"

# 4. Compare feature distributions
# Review Evidently AI report for feature distribution plots
```

**Recovery Steps**:

```bash
# Step 1: Collect new training data from production
psql -h postgres -U postgres -d aiwebtest \
  -c "COPY (SELECT features, prediction, ground_truth FROM predictions WHERE created_at > NOW() - INTERVAL '30 days' AND ground_truth IS NOT NULL) TO STDOUT WITH CSV HEADER" > new_training_data.csv

# Step 2: Upload to S3 for retraining
aws s3 cp new_training_data.csv s3://aiwebtest-ml-data/training/drift_recovery_$(date +%Y%m%d).csv

# Step 3: Trigger model retraining with new data
curl -X POST http://airflow:8080/api/v1/dags/model_retraining/dagRuns \
  -d '{"conf": {"training_data_path": "s3://aiwebtest-ml-data/training/drift_recovery_'$(date +%Y%m%d)'.csv"}}'

# Step 4: Wait for retraining to complete (check Airflow UI)
# Airflow UI: http://airflow:8080

# Step 5: Deploy retrained model to staging
curl -X POST http://mlflow:5000/api/2.0/mlflow/transition-model-version-stage \
  -d '{"name": "generation_model", "version": "4", "stage": "Staging"}'

# Step 6: Run A/B test (staging vs production model)
kubectl set env deployment/backend -n aiwebtest \
  AB_TEST_ENABLED=true \
  AB_TEST_TRAFFIC_SPLIT=0.1

# Step 7: Monitor A/B test results (24-48 hours)
# Grafana > ML Monitoring Dashboard > A/B Test Results

# Step 8: If new model performs better, promote to production
curl -X POST http://mlflow:5000/api/2.0/mlflow/transition-model-version-stage \
  -d '{"name": "generation_model", "version": "4", "stage": "Production"}'
```

**Escalation**:
- If drift persists: Investigate root cause (data quality, user behavior change)
- If retraining fails: Check training data quality, review feature engineering
- If new model doesn't improve: Keep current model, investigate drift source

**Prevention**:
- Run data drift checks weekly (Evidently AI)
- Collect ground truth feedback from production (for retraining)
- Automate retraining pipeline (trigger on drift detected)
- Maintain training data versioning (DVC)

---

## Security Incident Response

### Runbook 12: Security Breach Detected

**Symptoms**:
- Prometheus alert: `security_incident_detected == 1`
- ELK SIEM shows suspicious activity
- Failed login attempts >100 per minute

**Diagnosis Steps**:

```bash
# 1. Check security alerts
curl http://prometheus:9090/api/v1/query?query=security_incident_detected

# 2. Check audit logs for suspicious activity
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour' ORDER BY created_at DESC LIMIT 100;"

# 3. Check failed login attempts
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT username, ip_address, COUNT(*) FROM audit_logs WHERE action = 'login_failed' AND created_at > NOW() - INTERVAL '10 minutes' GROUP BY username, ip_address HAVING COUNT(*) > 10;"

# 4. Check ELK SIEM for patterns
# Kibana: http://kibana:5601
# Dashboard: Security Incidents

# 5. Check WAF logs for attacks
kubectl logs -n aiwebtest -l app=waf --tail=100 | grep -i "attack"
```

**Containment Steps**:

```bash
# Step 1: Block malicious IP addresses
kubectl exec -n aiwebtest waf-xxx -- iptables -A INPUT -s <MALICIOUS_IP> -j DROP

# Step 2: Disable compromised user accounts
psql -h postgres -U postgres -d aiwebtest \
  -c "UPDATE users SET status = 'locked', locked_reason = 'Security incident' WHERE username IN ('compromised_user1', 'compromised_user2');"

# Step 3: Rotate API keys and secrets
# Vault: http://vault:8200
vault write secret/api/openrouter api_key=<NEW_KEY>

# Step 4: Enable rate limiting (strict mode)
kubectl set env deployment/backend -n aiwebtest \
  RATE_LIMIT_STRICT=true \
  RATE_LIMIT_GLOBAL=10

# Step 5: Notify security team via PagerDuty
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -d '{"routing_key": "SECURITY_KEY", "event_action": "trigger", "payload": {"summary": "Security incident detected", "severity": "critical"}}'
```

**Investigation Steps**:

```bash
# 1. Review audit logs for scope of breach
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT action, resource, username, ip_address, created_at FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours' AND (username IN ('compromised_user1') OR ip_address IN ('MALICIOUS_IP')) ORDER BY created_at;"

# 2. Check data access logs
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT * FROM audit_logs WHERE action IN ('read', 'export') AND username IN ('compromised_user1') ORDER BY created_at DESC;"

# 3. Determine compromised data
# Review accessed resources and export audit logs

# 4. Check for backdoors or persistence
kubectl exec -n aiwebtest backend-xxx -- find /app -mtime -1 -type f
```

**Remediation Steps**:

```bash
# 1. Remove backdoors or malicious code
kubectl exec -n aiwebtest backend-xxx -- rm -f /app/backdoor.py

# 2. Patch vulnerabilities
# Update dependencies, apply security patches
kubectl set image deployment/backend backend=aiwebtest/backend:patched -n aiwebtest

# 3. Reset all user passwords (if credentials compromised)
# Send password reset emails to all users

# 4. Restore from clean backup (if data corrupted)
# See Runbook 13 (Disaster Recovery)

# 5. Document incident in security log
# Create incident report with timeline, impact, remediation
```

**Post-Incident**:
- Conduct security audit and penetration testing
- Review and update security policies
- Train team on security best practices
- Enable additional security monitoring

---

## Disaster Recovery

### Runbook 13: Complete System Failure

**Symptoms**:
- All services are down
- Prometheus alert: `system_health == 0`
- Users report complete service outage

**Diagnosis Steps**:

```bash
# 1. Check Kubernetes cluster status
kubectl cluster-info
kubectl get nodes

# 2. Check all pods
kubectl get pods -n aiwebtest -o wide

# 3. Check infrastructure (cloud provider)
# AWS: Check EC2 instances, RDS, ELB status
# Azure: Check VMs, SQL Database, Load Balancer status

# 4. Check recent changes
kubectl rollout history deployment/backend -n aiwebtest
kubectl get events -n aiwebtest --sort-by=.metadata.creationTimestamp
```

**Recovery Steps**:

```bash
# Step 1: Restore Kubernetes cluster (if cluster is down)
# If using managed Kubernetes (EKS, GKE, AKS), contact cloud support

# Step 2: Restore PostgreSQL from backup
# Point-in-Time Recovery (PITR) from WAL archive
pg_basebackup -h backup-server -D /var/lib/postgresql/data -P --wal-method=stream

# Or restore from S3 backup
aws s3 cp s3://aiwebtest-backups/postgres/aiwebtest_20250131_020000.sql.gz ./backup.sql.gz
gunzip backup.sql.gz
psql -h postgres -U postgres -d aiwebtest -f backup.sql

# Step 3: Restore Redis from RDB snapshot
kubectl cp redis-snapshot.rdb aiwebtest/redis-xxx:/data/dump.rdb
kubectl exec -n aiwebtest redis-xxx -- redis-cli SHUTDOWN
kubectl delete pod redis-xxx -n aiwebtest

# Step 4: Redeploy all services
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/agents.yaml
kubectl apply -f k8s/frontend.yaml

# Step 5: Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app -n aiwebtest --timeout=300s

# Step 6: Verify system health
curl http://backend:8000/health
psql -h postgres -U postgres -d aiwebtest -c "SELECT COUNT(*) FROM users;"

# Step 7: Notify users that system is back online
# Update https://status.aiwebtest.com
```

**Verification Steps**:

```bash
# 1. Run smoke tests
curl -X POST http://backend:8000/api/v1/tests/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"requirements_text": "Test user login"}'

# 2. Check data integrity
psql -h postgres -U postgres -d aiwebtest \
  -c "SELECT COUNT(*) FROM test_cases; SELECT COUNT(*) FROM test_executions; SELECT COUNT(*) FROM users;"

# 3. Check for data loss
# Compare current counts with pre-incident counts from monitoring

# 4. Monitor error rates
# Grafana > API Dashboard > Error Rate (should be <1%)

# 5. Monitor user feedback
# Check support tickets, social media, status page comments
```

**Post-Recovery**:
- Document incident timeline, root cause, recovery steps
- Conduct post-mortem meeting (blameless)
- Update disaster recovery procedures based on learnings
- Test disaster recovery plan quarterly

---

## On-Call Procedures

### On-Call Engineer Responsibilities

**1. Incident Response**:
- Acknowledge alerts within 5 minutes
- Begin diagnosis within 10 minutes
- Provide status update within 30 minutes
- Resolve P0 incidents within 4 hours

**2. Escalation Path**:
- Level 1: On-call engineer (P2-P3 incidents)
- Level 2: Senior engineer (P1 incidents)
- Level 3: Engineering manager (P0 incidents, >2 hours)
- Level 4: CTO (P0 incidents, >4 hours)

**3. Communication**:
- Update status page (https://status.aiwebtest.com) every 30 minutes
- Notify stakeholders via Slack (#incidents channel)
- Page backup on-call if not responding within 15 minutes

**4. Documentation**:
- Log all actions taken during incident
- Create incident report within 24 hours
- Schedule post-mortem meeting within 48 hours

### Alert Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P0 - Critical** | Complete service outage | 5 min | All services down, database corrupted |
| **P1 - High** | Major functionality broken | 15 min | Agent failures, API errors >10% |
| **P2 - Medium** | Degraded performance | 30 min | High latency, model accuracy drop |
| **P3 - Low** | Minor issues | 1 hour | Slow queries, UI glitches |

---

## Implementation Roadmap

### Phase 1: Agent & Database Runbooks (Day 1)

**Tasks**:
- Document agent failure recovery procedures (6 agents)
- Document database connection loss handling
- Document database performance troubleshooting
- Test runbooks with simulated failures

**Deliverables**: `runbooks/agent-failure.md` (500 lines), `runbooks/database-issues.md` (500 lines)

### Phase 2: API Outage & Performance Runbooks (Day 2)

**Tasks**:
- Document OpenRouter API outage response
- Document API high latency investigation
- Document test execution performance issues
- Test runbooks with chaos engineering

**Deliverables**: `runbooks/api-outage.md` (400 lines), `runbooks/performance-issues.md` (600 lines)

### Phase 3: Model Degradation & Disaster Recovery (Day 3)

**Tasks**:
- Document model accuracy drop response
- Document data drift recovery procedures
- Document security incident response
- Document complete system failure recovery
- Create on-call procedures document

**Deliverables**: `runbooks/model-degradation.md` (500 lines), `runbooks/disaster-recovery.md` (600 lines), `runbooks/on-call.md` (300 lines)

---

## Cost Analysis

### Infrastructure Costs (Monthly)
| Component | Cost | Notes |
|-----------|------|-------|
| Runbook Documentation | $0 | Markdown files in Git repository |
| PagerDuty (On-Call) | $0-100 | Free tier (5 users) or paid |
| Status Page | $0-29 | Statuspage.io free tier or paid |
| Incident Management Tools | $0 | Jira, Confluence (if already using) |
| **Total** | **$0-129/month** | Mostly free or existing tools |

### ROI Analysis

**Without Operational Runbooks**:
- Average incident resolution time: 4-8 hours (diagnosis + trial and error)
- Cost per hour of downtime: $1,000 - $10,000 (revenue loss, reputation)
- Incidents per month: 5-10
- **Total cost**: $20,000 - $800,000 per month in downtime

**With Operational Runbooks**:
- Average incident resolution time: 30 minutes - 2 hours (follow documented procedures)
- Cost per hour of downtime: $1,000 - $10,000
- Incidents per month: 5-10 (same frequency, but faster resolution)
- **Total cost**: $2,500 - $200,000 per month in downtime
- **Runbook cost**: $0-129/month

**Savings**: $17,500 - $600,000 per month (87.5-75% reduction in downtime costs!)

**ROI Calculation**:
- Average savings per incident: $3,500 - $60,000
- Runbook creation cost: $0-129/month
- **ROI**: **13,500% - 46,500,000% annually!**

**Conclusion**: Operational runbooks are a **no-brainer investment** that dramatically reduces Mean Time to Recovery (MTTR) and saves massive costs!

---

## Summary & Integration

### Key Achievements

✅ **Agent Failure Recovery**: Documented procedures for all 6 agents  
✅ **Database Issues**: Connection loss, performance troubleshooting  
✅ **API Outages**: OpenRouter API outage and rate limit handling  
✅ **Performance Issues**: High latency investigation and resolution  
✅ **Model Degradation**: Accuracy drop, data drift, concept drift response  
✅ **Security Incidents**: Breach detection, containment, investigation, remediation  
✅ **Disaster Recovery**: Complete system failure recovery procedures  
✅ **On-Call Procedures**: Alert severity, escalation path, responsibilities  

### Integration with Other Components

| Component | Integration Point |
|-----------|------------------|
| **Deployment & Resilience** | Automated rollback procedures, circuit breaker management |
| **ML Monitoring** | Model rollback, retraining triggers, A/B testing |
| **Security** | Incident response, breach containment, audit log review |
| **Database** | Query optimization, connection pool management, backup/restore |
| **Integration Testing** | Chaos engineering for runbook validation |

### Next Steps

1. **Review** this Operational Runbooks document
2. **Update PRD** with operational runbooks functional requirement
3. **Update SRS** with runbook tools and practices
4. **Begin Phase 1** implementation (Day 1)

---

**End of Operational Runbooks Architecture Document**

This architecture provides **comprehensive operational runbooks** for the AI-Web-Test v1 platform, enabling rapid incident response and minimizing downtime.

