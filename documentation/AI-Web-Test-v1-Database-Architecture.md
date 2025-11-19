# AI-Web-Test v1 - Database Architecture & Indexing Strategy

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-01-31
- **Status**: Architecture Specification
- **Related Documents**: 
  - [PRD](../AI-Web-Test-v1-PRD.md)
  - [SRS](../AI-Web-Test-v1-SRS.md)
  - [Data Governance](./AI-Web-Test-v1-Data-Governance.md)

---

## Executive Summary

This document defines the **comprehensive database architecture and indexing strategy** for the AI-Web-Test v1 platform, implementing optimized schemas, indexing strategies, query optimization, connection pooling, and database monitoring.

### Key Database Capabilities

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary Database** | PostgreSQL 15+ | Transactional data, ACID compliance |
| **Indexing Strategy** | B-Tree, Composite, Partial | Query optimization for common patterns |
| **Connection Pooling** | PgBouncer | Efficient connection management |
| **Query Optimization** | EXPLAIN ANALYZE | Performance tuning |
| **Database Monitoring** | pg_stat_statements | Query performance tracking |
| **Time-Series Data** | TimescaleDB extension | Metrics and logs |
| **Full-Text Search** | PostgreSQL FTS | Test case search |

### Implementation Timeline
- **Total Effort**: 3 days
- **Phase 1** (Day 1): Schema Design + Core Indexes
- **Phase 2** (Day 2): Query Optimization + Connection Pooling
- **Phase 3** (Day 3): Monitoring + Maintenance

---

## Table of Contents
1. [Database Schema Design](#database-schema-design)
2. [Indexing Strategy](#indexing-strategy)
3. [Query Optimization](#query-optimization)
4. [Connection Pooling](#connection-pooling)
5. [Database Monitoring](#database-monitoring)
6. [Backup & Recovery](#backup--recovery)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Summary & Integration](#summary--integration)

---

## Database Schema Design

### 1.1 Core Tables

**Entity Relationship Overview**:
```
users (1) ─┬─ (n) test_cases
           ├─ (n) test_executions
           ├─ (n) agent_decisions
           └─ (n) ml_models

test_cases (1) ── (n) test_executions
ml_models (1) ── (n) predictions
agents (1) ── (n) agent_decisions
projects (1) ──┬─ (n) test_cases
               └─ (n) test_executions
```

### 1.2 Table Definitions

```sql
-- database/schema.sql

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'qa_lead', 'qa_engineer', 'developer', 'business_user')),
    mfa_secret VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Test cases table
CREATE TABLE test_cases (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(20) NOT NULL UNIQUE CHECK (test_id ~ '^TEST-\d{6}$'),
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    test_type VARCHAR(20) NOT NULL CHECK (test_type IN ('unit', 'integration', 'e2e', 'performance')),
    priority VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    code TEXT,
    expected_output TEXT,
    tags TEXT[],
    estimated_duration INTEGER,
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    tsv tsvector  -- Full-text search vector
);

-- Test executions table (high volume)
CREATE TABLE test_executions (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(30) NOT NULL UNIQUE,
    test_id INTEGER NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    result VARCHAR(10) NOT NULL CHECK (result IN ('pass', 'fail', 'skip', 'error')),
    execution_time FLOAT NOT NULL CHECK (execution_time >= 0.1 AND execution_time <= 3600),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL CHECK (completed_at >= started_at),
    browser VARCHAR(20) NOT NULL CHECK (browser IN ('chrome', 'firefox', 'edge')),
    error_message TEXT,
    screenshots TEXT[],
    logs TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent decisions table
CREATE TABLE agent_decisions (
    id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    agent_type VARCHAR(50) NOT NULL CHECK (agent_type IN ('requirements', 'generation', 'execution', 'observation', 'analysis', 'evolution')),
    decision_type VARCHAR(50) NOT NULL,
    context JSONB NOT NULL,
    decision JSONB NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    execution_time_ms FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ML models table
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(30) NOT NULL UNIQUE CHECK (model_id ~ '^MODEL-\d{6}$'),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('generation', 'analysis', 'evolution')),
    framework VARCHAR(50) NOT NULL,
    metrics JSONB NOT NULL,
    artifact_path VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deprecated')),
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Predictions table (ML monitoring)
CREATE TABLE predictions (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    features JSONB NOT NULL,
    prediction INTEGER NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    ground_truth INTEGER,
    latency_ms FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent messages table (inter-agent communication)
CREATE TABLE agent_messages (
    id BIGSERIAL PRIMARY KEY,
    sender_id VARCHAR(50) NOT NULL,
    receiver_id VARCHAR(50) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'processed', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Audit logs table (GDPR compliance)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255) NOT NULL,
    resource_id VARCHAR(100),
    ip_address VARCHAR(50),
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    response_status INTEGER,
    changes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Indexing Strategy

### 2.1 Primary Indexes (Automatically Created)

**Primary Key Indexes** (B-Tree):
- `users_pkey` on `users(id)`
- `projects_pkey` on `projects(id)`
- `test_cases_pkey` on `test_cases(id)`
- `test_executions_pkey` on `test_executions(id)`
- `ml_models_pkey` on `ml_models(id)`
- `predictions_pkey` on `predictions(id)`
- `agent_decisions_pkey` on `agent_decisions(id)`

### 2.2 Unique Indexes

**Unique Constraints** (B-Tree):
```sql
-- Unique indexes for business keys
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_test_cases_test_id ON test_cases(test_id);
CREATE UNIQUE INDEX idx_test_executions_execution_id ON test_executions(execution_id);
CREATE UNIQUE INDEX idx_ml_models_model_id ON ml_models(model_id);
```

### 2.3 Foreign Key Indexes

**Foreign Key Indexes** (B-Tree):
```sql
-- Test cases foreign keys
CREATE INDEX idx_test_cases_project_id ON test_cases(project_id);
CREATE INDEX idx_test_cases_created_by ON test_cases(created_by);

-- Test executions foreign keys (high volume table)
CREATE INDEX idx_test_executions_test_id ON test_executions(test_id);
CREATE INDEX idx_test_executions_project_id ON test_executions(project_id);
CREATE INDEX idx_test_executions_user_id ON test_executions(user_id);

-- Predictions foreign keys
CREATE INDEX idx_predictions_model_id ON predictions(model_id);

-- Agent messages foreign keys
CREATE INDEX idx_agent_messages_sender_id ON agent_messages(sender_id);
CREATE INDEX idx_agent_messages_receiver_id ON agent_messages(receiver_id);

-- Audit logs foreign keys
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
```

### 2.4 Common Query Indexes

**Timestamp Indexes** (B-Tree, DESC for recent-first queries):
```sql
-- Recent executions (most common query pattern)
CREATE INDEX idx_test_executions_created_at 
  ON test_executions(created_at DESC);

-- Recent predictions
CREATE INDEX idx_predictions_created_at 
  ON predictions(created_at DESC);

-- Recent agent decisions
CREATE INDEX idx_agent_decisions_created_at 
  ON agent_decisions(created_at DESC);

-- Recent audit logs
CREATE INDEX idx_audit_logs_created_at 
  ON audit_logs(created_at DESC);
```

### 2.5 Composite Indexes

**Multi-Column Indexes** (B-Tree):
```sql
-- Test executions by project and status (common dashboard query)
CREATE INDEX idx_test_exec_project_status_created 
  ON test_executions(project_id, result, created_at DESC);

-- Test cases by project and status
CREATE INDEX idx_test_cases_project_status_created 
  ON test_cases(project_id, status, created_at DESC);

-- Agent decisions by agent and confidence (monitoring)
CREATE INDEX idx_agent_decision_agent_confidence 
  ON agent_decisions(agent_id, confidence_score DESC, created_at DESC);

-- Predictions by model and created_at (ML monitoring)
CREATE INDEX idx_predictions_model_created 
  ON predictions(model_name, model_version, created_at DESC);

-- Test executions by test and result (test history)
CREATE INDEX idx_test_exec_test_result_created 
  ON test_executions(test_id, result, created_at DESC);
```

### 2.6 Partial Indexes

**Filtered Indexes** (B-Tree with WHERE clause):
```sql
-- Active test cases only (most queries filter for active)
CREATE INDEX idx_test_cases_active 
  ON test_cases(id, created_at DESC) 
  WHERE status = 'active';

-- Running/pending test executions (real-time monitoring)
CREATE INDEX idx_test_exec_running 
  ON test_executions(id, started_at DESC, project_id) 
  WHERE result IN ('running', 'pending');

-- Failed executions (debugging)
CREATE INDEX idx_test_exec_failed 
  ON test_executions(id, test_id, created_at DESC, error_message) 
  WHERE result IN ('fail', 'error');

-- Active ML models
CREATE INDEX idx_ml_models_active 
  ON ml_models(id, name, version, created_at DESC) 
  WHERE status = 'active';

-- Predictions without ground truth (need feedback)
CREATE INDEX idx_predictions_no_ground_truth 
  ON predictions(id, model_name, created_at DESC) 
  WHERE ground_truth IS NULL;

-- Unprocessed agent messages
CREATE INDEX idx_agent_messages_unprocessed 
  ON agent_messages(id, sender_id, receiver_id, created_at) 
  WHERE status IN ('sent', 'delivered');
```

### 2.7 Full-Text Search Index

**GIN Index for Full-Text Search**:
```sql
-- Full-text search on test cases
CREATE INDEX idx_test_cases_tsv 
  ON test_cases USING GIN(tsv);

-- Trigger to maintain tsvector
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
ON test_cases FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(tsv, 'pg_catalog.english', title, description);

-- Usage:
-- SELECT * FROM test_cases 
-- WHERE tsv @@ to_tsquery('login & authentication')
-- ORDER BY ts_rank(tsv, to_tsquery('login & authentication')) DESC;
```

### 2.8 JSONB Indexes

**GIN Indexes for JSONB Columns**:
```sql
-- Agent decision context (frequently queried)
CREATE INDEX idx_agent_decisions_context 
  ON agent_decisions USING GIN(context);

-- ML model metrics
CREATE INDEX idx_ml_models_metrics 
  ON ml_models USING GIN(metrics);

-- Prediction features
CREATE INDEX idx_predictions_features 
  ON predictions USING GIN(features);

-- Usage:
-- SELECT * FROM agent_decisions 
-- WHERE context @> '{"test_id": "TEST-000001"}';
```

### 2.9 Index Monitoring

**Track Index Usage**:
```sql
-- Query to identify unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan AS scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC;

-- Identify missing indexes (table scans)
SELECT 
    schemaname,
    tablename,
    seq_scan AS table_scans,
    seq_tup_read AS tuples_read,
    idx_scan AS index_scans,
    seq_scan - idx_scan AS table_scans_vs_index,
    pg_size_pretty(pg_relation_size(relid)) AS table_size
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND seq_scan > 0
ORDER BY seq_scan DESC;
```

---

## Query Optimization

### 3.1 Common Query Patterns

**Dashboard Query (Recent Test Executions by Project)**:
```sql
-- Optimized query
EXPLAIN ANALYZE
SELECT 
    te.id,
    te.execution_id,
    tc.title AS test_title,
    te.result,
    te.execution_time,
    te.started_at,
    u.username
FROM test_executions te
JOIN test_cases tc ON te.test_id = tc.id
JOIN users u ON te.user_id = u.id
WHERE te.project_id = 123
  AND te.created_at >= NOW() - INTERVAL '7 days'
ORDER BY te.created_at DESC
LIMIT 100;

-- Uses index: idx_test_exec_project_status_created
-- Execution time: ~50ms for 10,000 rows
```

**Test History Query (All Executions for a Test)**:
```sql
-- Optimized query
EXPLAIN ANALYZE
SELECT 
    execution_id,
    result,
    execution_time,
    started_at,
    completed_at
FROM test_executions
WHERE test_id = 456
ORDER BY created_at DESC
LIMIT 50;

-- Uses index: idx_test_exec_test_result_created
-- Execution time: ~10ms for 1,000 rows
```

**Agent Performance Query (Agent Decisions by Confidence)**:
```sql
-- Optimized query
EXPLAIN ANALYZE
SELECT 
    agent_id,
    decision_type,
    confidence_score,
    execution_time_ms,
    created_at
FROM agent_decisions
WHERE agent_id = 'generation_agent_001'
  AND confidence_score >= 0.8
  AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY confidence_score DESC, created_at DESC
LIMIT 100;

-- Uses index: idx_agent_decision_agent_confidence
-- Execution time: ~30ms for 5,000 rows
```

**Full-Text Search Query (Search Test Cases)**:
```sql
-- Optimized full-text search
EXPLAIN ANALYZE
SELECT 
    test_id,
    title,
    description,
    ts_rank(tsv, query) AS rank
FROM test_cases, to_tsquery('english', 'login & authentication') AS query
WHERE tsv @@ query
  AND status = 'active'
ORDER BY rank DESC
LIMIT 20;

-- Uses indexes: idx_test_cases_tsv, idx_test_cases_active
-- Execution time: ~100ms for 10,000 rows
```

### 3.2 Query Performance Tuning

**Analyze Query Plans**:
```sql
-- Enable timing
\timing on

-- Analyze query
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM test_executions 
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 100;

-- Look for:
-- - Seq Scan (should be Index Scan for large tables)
-- - High "cost" values (> 10000)
-- - High "Buffers" values (> 1000 shared hits)
```

**Materialized Views for Complex Queries**:
```sql
-- Create materialized view for dashboard stats
CREATE MATERIALIZED VIEW mv_project_stats AS
SELECT 
    p.id AS project_id,
    p.name AS project_name,
    COUNT(DISTINCT tc.id) AS total_tests,
    COUNT(DISTINCT CASE WHEN tc.status = 'active' THEN tc.id END) AS active_tests,
    COUNT(te.id) AS total_executions_last_30_days,
    COUNT(CASE WHEN te.result = 'pass' THEN 1 END) AS passed_executions,
    COUNT(CASE WHEN te.result = 'fail' THEN 1 END) AS failed_executions,
    AVG(te.execution_time) AS avg_execution_time
FROM projects p
LEFT JOIN test_cases tc ON tc.project_id = p.id
LEFT JOIN test_executions te ON te.project_id = p.id 
    AND te.created_at >= NOW() - INTERVAL '30 days'
WHERE p.status = 'active'
GROUP BY p.id, p.name;

-- Create index on materialized view
CREATE INDEX idx_mv_project_stats_project_id ON mv_project_stats(project_id);

-- Refresh materialized view (scheduled job, every 15 minutes)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_stats;

-- Query is now instant!
SELECT * FROM mv_project_stats WHERE project_id = 123;
```

---

## Connection Pooling

### 4.1 PgBouncer Configuration

**PgBouncer Setup**:
```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
aiwebtest = host=localhost port=5432 dbname=aiwebtest

[pgbouncer]
# Connection pool settings
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3

# Server connection settings
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15

# Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1

# Admin
admin_users = postgres
stats_users = stats_reader
```

**Application Configuration**:
```python
# app/db/connection.py
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Connect to PgBouncer (not directly to PostgreSQL)
engine = create_engine(
    "postgresql://app_user:password@pgbouncer:6432/aiwebtest",
    poolclass=NullPool,  # Let PgBouncer handle pooling
    echo=False,
    connect_args={
        "application_name": "aiwebtest_api",
        "connect_timeout": 10
    }
)

# For async (FastAPI)
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    "postgresql+asyncpg://app_user:password@pgbouncer:6432/aiwebtest",
    poolclass=NullPool,
    echo=False
)
```

### 4.2 Connection Pool Monitoring

**Monitor PgBouncer**:
```sql
-- Connect to PgBouncer admin console
psql -p 6432 -U postgres -d pgbouncer

-- Show pools
SHOW POOLS;

-- Show active connections
SHOW CLIENTS;

-- Show server connections
SHOW SERVERS;

-- Show stats
SHOW STATS;
```

---

## Database Monitoring

### 5.1 pg_stat_statements

**Enable Query Performance Tracking**:
```sql
-- postgresql.conf
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.max = 10000
pg_stat_statements.track = all

-- Restart PostgreSQL
-- Then create extension
CREATE EXTENSION pg_stat_statements;

-- Top 10 slowest queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Top 10 most frequent queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;

-- Queries with high I/O
SELECT 
    query,
    calls,
    shared_blks_hit,
    shared_blks_read,
    shared_blks_read / NULLIF(shared_blks_hit + shared_blks_read, 0) AS cache_miss_ratio
FROM pg_stat_statements
WHERE shared_blks_read > 0
ORDER BY cache_miss_ratio DESC
LIMIT 10;
```

### 5.2 Database Size Monitoring

**Track Database Growth**:
```sql
-- Database size
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index sizes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 5.3 Prometheus Exporter

**PostgreSQL Exporter for Prometheus**:
```yaml
# docker-compose.yml
services:
  postgres_exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      DATA_SOURCE_NAME: "postgresql://exporter:password@postgres:5432/aiwebtest?sslmode=disable"
    ports:
      - "9187:9187"
    depends_on:
      - postgres

# Prometheus metrics available:
# - pg_stat_database_*
# - pg_stat_user_tables_*
# - pg_stat_user_indexes_*
# - pg_stat_statements_*
# - pg_database_size_bytes
# - pg_up (1 = healthy, 0 = down)
```

---

## Backup & Recovery

### 6.1 Automated Backups

**pg_dump Backup Script**:
```bash
#!/bin/bash
# /scripts/backup_postgres.sh

# Configuration
DB_NAME="aiwebtest"
DB_USER="postgres"
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30

# Create backup
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

# Dump database
pg_dump -U ${DB_USER} -d ${DB_NAME} | gzip > ${BACKUP_FILE}

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup successful: ${BACKUP_FILE}"
    
    # Upload to S3
    aws s3 cp ${BACKUP_FILE} s3://aiwebtest-backups/postgres/
    
    # Delete old backups
    find ${BACKUP_DIR} -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
else
    echo "Backup failed!"
    exit 1
fi
```

**Cron Schedule**:
```cron
# Daily backup at 2 AM
0 2 * * * /scripts/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
```

### 6.2 Point-in-Time Recovery (PITR)

**Enable WAL Archiving**:
```sql
-- postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /backup/wal/%f && cp %p /backup/wal/%f'
archive_timeout = 300  # Archive every 5 minutes

# Or use wal-g for S3 archiving:
# archive_command = 'wal-g wal-push %p'
```

---

## Implementation Roadmap

### Phase 1: Schema Design + Core Indexes (Day 1)

**Tasks**:
- [ ] Create database schema (tables, constraints)
- [ ] Create primary key and unique indexes
- [ ] Create foreign key indexes
- [ ] Create timestamp indexes
- [ ] Test schema with sample data

**Deliverables**:
- `database/schema.sql` (500 lines)
- `database/migrations/001_initial_schema.sql` (500 lines)

### Phase 2: Query Optimization + Connection Pooling (Day 2)

**Tasks**:
- [ ] Create composite indexes for common queries
- [ ] Create partial indexes for filtered queries
- [ ] Create full-text search indexes
- [ ] Create JSONB indexes
- [ ] Set up PgBouncer
- [ ] Create materialized views for dashboard
- [ ] Optimize slow queries

**Deliverables**:
- `database/indexes.sql` (300 lines)
- `database/views.sql` (200 lines)
- `/etc/pgbouncer/pgbouncer.ini` (100 lines)

### Phase 3: Monitoring + Maintenance (Day 3)

**Tasks**:
- [ ] Enable pg_stat_statements
- [ ] Set up PostgreSQL Exporter for Prometheus
- [ ] Create Grafana dashboard for database metrics
- [ ] Set up automated backups (pg_dump + S3)
- [ ] Enable WAL archiving for PITR
- [ ] Create index monitoring queries
- [ ] Document query optimization process

**Deliverables**:
- `database/monitoring.sql` (200 lines)
- `scripts/backup_postgres.sh` (100 lines)
- `grafana/dashboards/postgres-monitoring.json` (500 lines)

---

## Cost Analysis

### Infrastructure Costs (Monthly)
| Component | Cost | Notes |
|-----------|------|-------|
| PostgreSQL (100 GB) | $30-50 | RDS db.t3.medium or self-hosted |
| PgBouncer | $0 | Open-source, minimal resources |
| Backups (S3) | $5-10 | 100 GB compressed backups |
| Monitoring (Exporter) | $0 | Open-source Prometheus exporter |
| **Total** | **$35-60/month** | Scales with data volume |

### Performance Improvements

**Without Proper Indexing**:
- Dashboard query: 5,000ms (table scan)
- Test history query: 2,000ms (table scan)
- Search query: 10,000ms (full table scan)

**With Proper Indexing**:
- Dashboard query: 50ms (index scan) - **100x faster**
- Test history query: 10ms (index scan) - **200x faster**
- Search query: 100ms (GIN index) - **100x faster**

**ROI**: Proper indexing improves user experience dramatically and reduces database load by 100-200x.

---

## Summary & Integration

### Key Achievements

✅ **Optimized Schema Design**: Normalized tables with proper constraints  
✅ **Comprehensive Indexing**: B-Tree, Composite, Partial, GIN indexes  
✅ **Query Optimization**: EXPLAIN ANALYZE, materialized views  
✅ **Connection Pooling**: PgBouncer for efficient connection management  
✅ **Database Monitoring**: pg_stat_statements, Prometheus exporter  
✅ **Backup & Recovery**: Automated backups, PITR with WAL archiving  

### Integration with Other Components

| Component | Integration Point |
|-----------|------------------|
| **Data Governance** | Retention policies for old test_executions, audit_logs archival |
| **ML Monitoring** | predictions table with indexes for drift detection queries |
| **Security** | audit_logs table with indexes, encrypted sensitive columns |
| **Deployment** | Health checks for database connectivity, connection pool monitoring |

### Next Steps

1. **Review** this Database Architecture document
2. **Update PRD** with database functional requirements
3. **Update SRS** with database technology details
4. **Begin Phase 1** implementation (Day 1)

---

**End of Database Architecture & Indexing Strategy Document**

This architecture provides **production-grade database performance** for the AI-Web-Test v1 platform with optimized indexing, query performance, and monitoring.

