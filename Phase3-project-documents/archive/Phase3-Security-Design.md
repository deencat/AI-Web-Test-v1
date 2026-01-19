# Phase 3: Security Design

**Purpose:** Authentication, authorization, encryption, and security best practices  
**Status:** Implementation guide for Sprint 11-12  
**Last Updated:** January 16, 2026

---

## 📋 Overview

Security is critical for a multi-agent system handling code and potentially sensitive data. This document covers:

1. **Agent Authentication** (agent-to-agent)
2. **User Authorization** (RBAC)
3. **Data Encryption** (at rest and in transit)
4. **API Security** (rate limiting, validation)
5. **Audit Logging** (compliance)
6. **Secret Management**

---

## 1. Agent Authentication

### Challenge
Agents communicate via message bus. Need to verify messages come from legitimate agents (prevent spoofing).

### Solution: JWT-Based Agent Identity

**Implementation:**

```python
# backend/agents/security/agent_auth.py

import jwt
from datetime import datetime, timedelta

class AgentAuthenticator:
    """Issues and verifies JWT tokens for agents"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    def issue_token(self, agent_id: str, agent_type: str) -> str:
        """Issue JWT for agent on registration"""
        payload = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT from agent message"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                raise ValueError("Token expired")
            
            return payload
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")


# Usage in message sending
async def send_authenticated_message(self, stream_name: str, message: dict):
    """Send message with authentication token"""
    message["auth_token"] = self.auth.issue_token(self.agent_id, self.agent_type)
    await self.message_bus.send_message(stream_name, message)

# Usage in message receiving
async def process_message(self, message: dict):
    """Verify sender before processing"""
    try:
        payload = self.auth.verify_token(message["auth_token"])
        # Verify sender matches
        if payload["agent_id"] != message["sender_id"]:
            raise ValueError("Agent ID mismatch")
    except ValueError as e:
        logger.error(f"Authentication failed: {e}")
        return  # Reject message
    
    # Process authenticated message
    await super().process_message(message)
```

**Key Rotation:**
- Rotate secret key every 90 days
- Issue new tokens on rotation, old tokens valid for 24 hours (grace period)

---

## 2. User Authorization (RBAC)

### Roles

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | All operations | System administrators |
| **Developer** | Generate tests, view results, edit settings | Individual developers |
| **Viewer** | View tests, view results (read-only) | QA team, managers |
| **Service Account** | API access only | CI/CD pipelines |

### Database Schema

```sql
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB NOT NULL
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(role_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    key_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,  -- For identification (e.g., "sk_test_abc...")
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed roles
INSERT INTO roles (role_name, permissions) VALUES
('admin', '{"tests": ["create", "read", "update", "delete"], "settings": ["read", "update"], "agents": ["read", "restart"]}'),
('developer', '{"tests": ["create", "read"], "settings": ["read"]}'),
('viewer', '{"tests": ["read"], "settings": ["read"]}'),
('service_account', '{"tests": ["create", "read"]}');
```

### FastAPI RBAC Middleware

```python
# backend/api/auth.py

from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Authorization header"""
    api_key = credentials.credentials
    
    # Hash and lookup
    key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt())
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT u.user_id, u.role_id, r.permissions
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.user_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE ak.key_hash = $1 AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
        """, key_hash)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user

def require_permission(resource: str, action: str):
    """Decorator to check permissions"""
    async def permission_checker(user = Depends(verify_api_key)):
        permissions = user["permissions"]
        if resource not in permissions or action not in permissions[resource]:
            raise HTTPException(status_code=403, detail=f"Permission denied: {resource}.{action}")
        return user
    return permission_checker


# Usage in routes
@app.post("/api/v2/tests/generate")
async def generate_tests(
    request: TestGenerationRequest,
    user = Depends(require_permission("tests", "create"))
):
    # User has permission to create tests
    ...
```

---

## 3. Data Encryption

### At Rest

**PostgreSQL Transparent Data Encryption (TDE):**
```bash
# Enable encryption
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/server.key';
```

**Redis Encryption:**
```bash
# redis.conf
requirepass YOUR_STRONG_PASSWORD
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
```

**Vector DB (Qdrant):**
```yaml
# qdrant-config.yaml
service:
  api_key: YOUR_QDRANT_API_KEY
  enable_tls: true
  tls_cert: /path/to/qdrant.crt
  tls_key: /path/to/qdrant.key
```

### In Transit

**All HTTP Traffic:**
- Frontend ↔ Backend: HTTPS only (TLS 1.3)
- Agent ↔ Message Bus: TLS encryption on Redis connections
- Agent ↔ Database: PostgreSQL SSL mode=require

**nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.aitest.example.com;
    
    ssl_certificate /etc/letsencrypt/live/api.aitest.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.aitest.example.com/privkey.pem;
    
    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384';
    ssl_prefer_server_ciphers on;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 4. API Security

### Rate Limiting

**Per-User Limits:**
```python
# backend/api/rate_limit.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v2/tests/generate")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def generate_tests(request: Request, ...):
    ...
```

**Per-Tenant Limits (Database):**
```sql
CREATE TABLE tenant_quotas (
    tenant_id INTEGER PRIMARY KEY,
    daily_token_limit INTEGER DEFAULT 1000000,
    daily_request_limit INTEGER DEFAULT 1000,
    tokens_used_today INTEGER DEFAULT 0,
    requests_made_today INTEGER DEFAULT 0,
    quota_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 day'
);

-- Check quota before processing
SELECT * FROM tenant_quotas 
WHERE tenant_id = $1 
AND (requests_made_today < daily_request_limit AND tokens_used_today < daily_token_limit);
```

### Input Validation

**Pydantic Schemas:**
```python
from pydantic import BaseModel, Field, validator

class TestGenerationRequest(BaseModel):
    repository_url: str = Field(..., regex=r'^https://github\.com/[\w-]+/[\w-]+$')
    target_files: list[str] = Field(..., max_items=10)
    coverage_target: float = Field(0.80, ge=0.5, le=1.0)
    
    @validator('target_files')
    def validate_file_paths(cls, files):
        # Prevent directory traversal
        for file in files:
            if '..' in file or file.startswith('/'):
                raise ValueError("Invalid file path")
        return files
```

### SQL Injection Prevention

**Always use parameterized queries:**
```python
# ✅ SAFE
await conn.fetchrow("SELECT * FROM tests WHERE test_id = $1", test_id)

# ❌ UNSAFE
await conn.fetchrow(f"SELECT * FROM tests WHERE test_id = {test_id}")
```

---

## 5. Audit Logging

### Requirements
- **Compliance:** Track all user actions for audit
- **Forensics:** Investigate security incidents
- **Monitoring:** Detect anomalous behavior

### Implementation

**Database Schema:**
```sql
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,  -- 'test_generated', 'settings_updated', 'agent_restarted'
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    request_payload JSONB,
    response_status INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_log(action, timestamp DESC);
```

**Middleware:**
```python
# backend/api/audit.py

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API requests"""
    user_id = request.state.user.get("user_id") if hasattr(request.state, "user") else None
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Log to database
    await db_pool.execute("""
        INSERT INTO audit_log (user_id, action, resource_type, ip_address, user_agent, response_status)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, user_id, request.url.path, "api", request.client.host, request.headers.get("user-agent"), response.status_code)
    
    return response
```

### Retention Policy
- Audit logs retained for **2 years**
- Archive to cold storage (S3 Glacier) after 90 days
- Automatic cleanup job runs monthly

---

## 6. Secret Management

### Never Hardcode Secrets ❌

**Bad:**
```python
OPENAI_API_KEY = "sk-1234567890abcdef"  # ❌ NEVER DO THIS
```

### Use Environment Variables + Secrets Manager

**Good (Development):**
```bash
# .env (not committed to git)
OPENAI_API_KEY=sk-...
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
```

**Production (Kubernetes Secrets):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
type: Opaque
data:
  openai-api-key: c2stLi4uCg==  # Base64 encoded
  postgres-password: cGFzc3dvcmQ=
  redis-password: cmVkaXNwYXNz
```

```python
# backend/agents/base_agent.py

import os

class BaseAgent:
    def __init__(self, ...):
        # Load from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
```

### Secrets Rotation

**Automated Rotation (90 days):**
```python
# backend/security/secrets_rotation.py

async def rotate_api_keys():
    """Rotate all API keys older than 90 days"""
    async with db_pool.acquire() as conn:
        old_keys = await conn.fetch("""
            SELECT key_id, user_id FROM api_keys
            WHERE created_at < NOW() - INTERVAL '90 days'
        """)
        
        for key in old_keys:
            # Generate new key
            new_key = generate_secure_key()
            new_key_hash = bcrypt.hashpw(new_key.encode(), bcrypt.gensalt())
            
            # Update database
            await conn.execute("""
                UPDATE api_keys SET key_hash = $1, created_at = NOW()
                WHERE key_id = $2
            """, new_key_hash, key["key_id"])
            
            # Notify user
            await send_email(key["user_id"], "API Key Rotated", f"New key: {new_key}")
```

---

## 7. Security Checklist

**Pre-Production:**
- [ ] All secrets moved to environment variables/Kubernetes secrets
- [ ] TLS enabled for all connections (PostgreSQL, Redis, HTTP)
- [ ] RBAC implemented and tested
- [ ] Rate limiting configured (10 req/min per IP)
- [ ] Input validation on all API endpoints (Pydantic)
- [ ] SQL injection prevented (parameterized queries only)
- [ ] Audit logging enabled
- [ ] OWASP scan completed (no critical/high vulnerabilities)
- [ ] Dependency scan (no known vulnerabilities)
- [ ] Secret rotation policy documented

**Continuous:**
- [ ] Monthly security reviews
- [ ] Quarterly penetration testing
- [ ] Automated vulnerability scanning (GitHub Dependabot)
- [ ] Audit log review (monthly)
- [ ] Secrets rotation (90 days)

---

## 8. Incident Response Plan

**If security breach detected:**

1. **Immediate (< 5 minutes):**
   - Disable affected API keys
   - Block suspicious IP addresses
   - Alert security team

2. **Short-term (< 1 hour):**
   - Rotate all secrets
   - Review audit logs
   - Identify scope of breach

3. **Long-term (< 24 hours):**
   - Patch vulnerability
   - Notify affected users (if data exposed)
   - Post-mortem analysis

**Contacts:**
- Security Lead: Developer A
- On-call Engineer: Rotation schedule
- Compliance Officer: (TBD)

---

## 9. Compliance

**GDPR (if handling EU user data):**
- Right to deletion: Implement `/api/v2/users/{id}/delete`
- Data portability: Export user data as JSON
- Privacy by design: Minimize data collection

**SOC 2 (for enterprise customers):**
- Audit logging (covered above)
- Access control (RBAC)
- Encryption at rest and in transit
- Incident response plan

---

**END OF SECURITY DESIGN**
