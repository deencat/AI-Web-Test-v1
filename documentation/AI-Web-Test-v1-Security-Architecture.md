# AI-Web-Test v1 - Security Architecture

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-01-31
- **Status**: Architecture Specification
- **Related Documents**: 
  - [PRD](../AI-Web-Test-v1-PRD.md)
  - [SRS](../AI-Web-Test-v1-SRS.md)
  - [MLOps Architecture](./AI-Web-Test-v1-MLOps-Architecture.md)
  - [Deployment & Resilience](./AI-Web-Test-v1-Deployment-Resilience.md)

---

## Executive Summary

This document defines the **comprehensive security architecture** for the AI-Web-Test v1 platform, implementing **defense-in-depth** principles with 5 security layers, fine-grained RBAC, PII protection, API rate limiting, and real-time security monitoring.

### Key Security Capabilities

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Rate Limiting** | slowapi + Redis | Per-role quotas, DDoS protection |
| **Defense-in-Depth** | Multi-layer security | 5 security layers (Network → Monitoring) |
| **Fine-Grained RBAC** | Casbin | Endpoint + HTTP method permissions |
| **PII Protection** | Presidio + AES-256 | Data masking, encryption at rest |
| **Security Monitoring** | SIEM (ELK Stack) | Real-time threat detection |
| **WAF** | ModSecurity | SQL injection, XSS prevention |
| **Secrets Management** | HashiCorp Vault | API key rotation, secure storage |

### Implementation Timeline
- **Total Effort**: 16 days
- **Phase 1** (Days 1-5): API Rate Limiting + RBAC
- **Phase 2** (Days 6-11): PII Protection + Defense-in-Depth
- **Phase 3** (Days 12-16): Security Monitoring + SIEM

---

## Table of Contents
1. [Defense-in-Depth Principles](#defense-in-depth-principles)
2. [Layer 1: Network Security](#layer-1-network-security)
3. [Layer 2: Application Security](#layer-2-application-security)
4. [Layer 3: Data Security](#layer-3-data-security)
5. [Layer 4: Identity & Access Management](#layer-4-identity--access-management)
6. [Layer 5: Security Monitoring](#layer-5-security-monitoring)
7. [API Rate Limiting](#api-rate-limiting)
8. [Fine-Grained RBAC](#fine-grained-rbac)
9. [PII Protection](#pii-protection)
10. [Security Monitoring & Alerting](#security-monitoring--alerting)
11. [Secrets Management](#secrets-management)
12. [Security Audit & Compliance](#security-audit--compliance)
13. [Implementation Roadmap](#implementation-roadmap)
14. [Summary & Integration](#summary--integration)

---

## Defense-in-Depth Principles

### Overview
Defense-in-depth implements **5 security layers** to ensure that if one layer is breached, others remain intact.

```mermaid
graph TB
    subgraph "Layer 5: Security Monitoring"
        SIEM[SIEM - ELK Stack]
        IDS[Intrusion Detection]
        Alerts[Real-time Alerts]
    end
    
    subgraph "Layer 4: Identity & Access"
        OAuth[OAuth 2.0]
        MFA[Multi-Factor Auth]
        RBAC[Fine-Grained RBAC]
        Rotation[API Key Rotation]
    end
    
    subgraph "Layer 3: Data Security"
        Encryption[AES-256 Encryption]
        TLS[TLS 1.3]
        Masking[PII Masking]
        Backup[Encrypted Backups]
    end
    
    subgraph "Layer 2: Application Security"
        Validation[Input Validation]
        CSRF[CSRF Tokens]
        XSS[XSS Prevention]
        RateLimit[Rate Limiting]
    end
    
    subgraph "Layer 1: Network Security"
        WAF[Web Application Firewall]
        VPC[VPC Isolation]
        Firewall[Firewall Rules]
        DDoS[DDoS Protection]
    end
    
    Internet --> WAF
    WAF --> Validation
    Validation --> OAuth
    OAuth --> Encryption
    Encryption --> SIEM
```

### Security Layers

| Layer | Components | Purpose |
|-------|-----------|---------|
| **1. Network** | WAF, VPC, Firewall, DDoS | Perimeter defense |
| **2. Application** | Input validation, CSRF, XSS, Rate limiting | Prevent injection attacks |
| **3. Data** | AES-256, TLS 1.3, PII masking | Protect data at rest/transit |
| **4. Identity** | OAuth 2.0, MFA, RBAC, Key rotation | Authentication & authorization |
| **5. Monitoring** | SIEM, IDS, Audit logs | Detect & respond to threats |

---

## Layer 1: Network Security

### 1.1 Web Application Firewall (ModSecurity)

**Purpose**: Protect against OWASP Top 10 vulnerabilities.

#### ModSecurity Configuration
```nginx
# nginx.conf with ModSecurity
load_module modules/ngx_http_modsecurity_module.so;

http {
    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsec/main.conf;

    server {
        listen 443 ssl http2;
        server_name api.aiwebtest.com;

        # TLS 1.3 only
        ssl_protocols TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # ModSecurity rules
        location / {
            modsecurity_rules '
                SecRuleEngine On
                SecRule ARGS "@detectSQLi" "id:1,phase:2,deny,status:403"
                SecRule ARGS "@detectXSS" "id:2,phase:2,deny,status:403"
                SecRule REQUEST_HEADERS:Content-Type "!@rx ^(application/json|multipart/form-data)" "id:3,phase:1,deny,status:403"
            ';
            proxy_pass http://backend:8000;
        }
    }
}
```

#### OWASP Core Rule Set (CRS)
```bash
# Install OWASP CRS
cd /etc/nginx/modsec
git clone https://github.com/coreruleset/coreruleset.git
cp coreruleset/crs-setup.conf.example crs-setup.conf
cp coreruleset/rules/*.conf rules/

# main.conf
Include /etc/nginx/modsec/modsecurity.conf
Include /etc/nginx/modsec/crs-setup.conf
Include /etc/nginx/modsec/rules/*.conf
```

### 1.2 VPC & Network Isolation

**Architecture**:
```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-isolation
  namespace: aiwebtest
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### 1.3 DDoS Protection

**CloudFlare Configuration** (or similar CDN):
```yaml
# cloudflare-config.yaml
rate_limiting:
  - name: "API Protection"
    match:
      request:
        url_pattern: "/api/*"
    action:
      mode: "challenge"
    threshold: 100  # requests per minute
    period: 60

ddos_protection:
  - name: "L7 DDoS"
    sensitivity: "high"
    action: "challenge"
```

---

## Layer 2: Application Security

### 2.1 Input Validation

**Pydantic Models with Strict Validation**:
```python
# app/models/validation.py
from pydantic import BaseModel, Field, validator, constr
from typing import List, Optional
import re

class TestGenerationRequest(BaseModel):
    """Strict validation for test generation"""
    requirements_text: constr(min_length=10, max_length=10000) = Field(
        ..., 
        description="Requirements text (10-10000 chars)"
    )
    test_types: List[str] = Field(
        ..., 
        description="Test types to generate"
    )
    max_tests: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Max tests to generate (1-100)"
    )
    
    @validator('test_types')
    def validate_test_types(cls, v):
        allowed = ['unit', 'integration', 'e2e', 'performance']
        invalid = set(v) - set(allowed)
        if invalid:
            raise ValueError(f"Invalid test types: {invalid}")
        return v
    
    @validator('requirements_text')
    def sanitize_input(cls, v):
        # Remove potential XSS vectors
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potentially malicious content detected")
        return v

class CodeExecutionRequest(BaseModel):
    """Validation for code execution (high-risk operation)"""
    test_code: constr(max_length=50000) = Field(...)
    language: str = Field(..., regex=r'^(python|javascript|java)$')
    timeout: int = Field(default=30, ge=5, le=300)
    
    @validator('test_code')
    def validate_code_safety(cls, v):
        # Prevent dangerous operations
        dangerous_imports = [
            'os.system',
            'subprocess',
            'eval(',
            'exec(',
            '__import__',
        ]
        for dangerous in dangerous_imports:
            if dangerous in v:
                raise ValueError(f"Dangerous operation not allowed: {dangerous}")
        return v
```

### 2.2 CSRF Protection

**FastAPI CSRF Middleware**:
```python
# app/middleware/csrf.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import hmac

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return await call_next(request)
        
        # Check CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        csrf_cookie = request.cookies.get('csrf_token')
        
        if not csrf_token or not csrf_cookie:
            raise HTTPException(status_code=403, detail="CSRF token missing")
        
        # Validate token
        if not hmac.compare_digest(csrf_token, csrf_cookie):
            raise HTTPException(status_code=403, detail="CSRF token invalid")
        
        return await call_next(request)

# Generate CSRF token endpoint
@app.get("/api/csrf-token")
async def get_csrf_token(response: Response):
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600
    )
    return {"csrf_token": token}
```

### 2.3 XSS Prevention

**Content Security Policy (CSP)**:
```python
# app/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.openrouter.ai; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
```

---

## Layer 3: Data Security

### 3.1 Encryption at Rest (AES-256)

**Database Encryption with SQLAlchemy**:
```python
# app/db/encryption.py
from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, String
import os

class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string fields"""
    impl = String
    cache_ok = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load encryption key from environment
        key = os.environ.get('DB_ENCRYPTION_KEY')
        if not key:
            raise ValueError("DB_ENCRYPTION_KEY not set")
        self.fernet = Fernet(key.encode())
    
    def process_bind_param(self, value, dialect):
        """Encrypt before storing"""
        if value is not None:
            value = self.fernet.encrypt(value.encode())
            return value.decode()
        return value
    
    def process_result_value(self, value, dialect):
        """Decrypt after retrieving"""
        if value is not None:
            value = self.fernet.decrypt(value.encode())
            return value.decode()
        return value

# Usage in models
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TestCase(Base):
    __tablename__ = 'test_cases'
    
    id = Column(Integer, primary_key=True)
    code = Column(EncryptedString(50000))  # Encrypted test code
    expected_output = Column(EncryptedString(10000))  # Encrypted
```

**Generate Encryption Key**:
```python
# scripts/generate_encryption_key.py
from cryptography.fernet import Fernet

# Generate key (run once, store securely)
key = Fernet.generate_key()
print(f"DB_ENCRYPTION_KEY={key.decode()}")
# Store in HashiCorp Vault or AWS Secrets Manager
```

### 3.2 TLS 1.3 Configuration

**PostgreSQL TLS Configuration**:
```bash
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_min_protocol_version = 'TLSv1.3'
ssl_ciphers = 'HIGH:!aNULL:!MD5'
```

**Python Client TLS Configuration**:
```python
# app/db/connection.py
from sqlalchemy import create_engine
import ssl

# PostgreSQL connection with TLS 1.3
engine = create_engine(
    "postgresql://user:pass@localhost:5432/aiwebtest",
    connect_args={
        "sslmode": "verify-full",
        "sslrootcert": "/etc/ssl/certs/ca.crt",
        "ssl_min_protocol_version": ssl.TLSVersion.TLSv1_3
    }
)
```

### 3.3 Field-Level Encryption

**Selective Field Encryption**:
```python
# app/db/models.py
from sqlalchemy import Column, Integer, String, Text
from app.db.encryption import EncryptedString

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(EncryptedString(255), unique=True)  # Encrypted
    name = Column(String(255))  # Not encrypted (for search)
    api_key = Column(EncryptedString(100))  # Encrypted
    role = Column(String(50))  # Not encrypted (for RBAC)

class TestData(Base):
    __tablename__ = 'test_data'
    
    id = Column(Integer, primary_key=True)
    test_input = Column(EncryptedString(10000))  # Encrypted (may contain PII)
    test_output = Column(EncryptedString(10000))  # Encrypted
    status = Column(String(50))  # Not encrypted (for filtering)
```

---

## Layer 4: Identity & Access Management

### 4.1 OAuth 2.0 + MFA

**OAuth 2.0 Implementation with FastAPI**:
```python
# app/auth/oauth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import pyotp

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from DB
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# MFA Verification
class MFAVerification:
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

@app.post("/api/auth/login")
async def login(username: str, password: str, mfa_token: str):
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify MFA
    if not MFAVerification.verify_totp(user.mfa_secret, mfa_token):
        raise HTTPException(status_code=401, detail="Invalid MFA token")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

### 4.2 API Key Rotation

**Automatic API Key Rotation**:
```python
# app/auth/api_keys.py
from datetime import datetime, timedelta
import secrets

class APIKeyManager:
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_api_key(self, user_id: int, expires_days: int = 90) -> str:
        """Generate new API key with expiration"""
        api_key = f"aiwebtest_{secrets.token_urlsafe(32)}"
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Store in DB (encrypted)
        self.db.execute(
            "INSERT INTO api_keys (user_id, key_hash, expires_at) VALUES (?, ?, ?)",
            (user_id, hash_api_key(api_key), expires_at)
        )
        return api_key
    
    def rotate_api_key(self, user_id: int) -> str:
        """Rotate API key (keep old key valid for 24 hours)"""
        # Mark old key as deprecated
        self.db.execute(
            "UPDATE api_keys SET deprecated_at = ? WHERE user_id = ? AND deprecated_at IS NULL",
            (datetime.utcnow() + timedelta(hours=24), user_id)
        )
        
        # Generate new key
        return self.generate_api_key(user_id)
    
    async def validate_api_key(self, api_key: str) -> Optional[User]:
        """Validate API key and return user"""
        key_hash = hash_api_key(api_key)
        result = self.db.execute(
            "SELECT user_id, expires_at, deprecated_at FROM api_keys WHERE key_hash = ?",
            (key_hash,)
        ).fetchone()
        
        if not result:
            return None
        
        user_id, expires_at, deprecated_at = result
        
        # Check expiration
        if expires_at < datetime.utcnow():
            return None
        
        # Warn if deprecated
        if deprecated_at and deprecated_at < datetime.utcnow():
            return None
        
        return await get_user_by_id(user_id)

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()
```

---

## API Rate Limiting

### 5.1 Role-Based Rate Limits

**slowapi Integration with Redis**:
```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import redis

# Redis connection for distributed rate limiting
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_user_role(request: Request) -> str:
    """Extract user role from JWT token"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return "guest"
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role", "user")
    except:
        return "guest"

# Role-based rate limits
RATE_LIMITS = {
    'guest': '10/minute',
    'user': '100/minute',
    'premium': '500/minute',
    'admin': '1000/minute',
    'service': '10000/minute'
}

limiter = Limiter(
    key_func=get_user_role,
    storage_uri="redis://localhost:6379"
)

# Apply rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/tests/generate")
@limiter.limit(lambda: RATE_LIMITS[get_user_role()])
async def generate_tests(request: Request):
    """Generate tests with role-based rate limiting"""
    pass

@app.post("/api/tests/execute")
@limiter.limit(lambda: RATE_LIMITS[get_user_role()])
async def execute_tests(request: Request):
    """Execute tests with rate limiting"""
    pass
```

### 5.2 Custom Rate Limit Strategies

**Adaptive Rate Limiting**:
```python
# app/middleware/adaptive_rate_limit.py
from collections import defaultdict
from datetime import datetime, timedelta

class AdaptiveRateLimiter:
    def __init__(self):
        self.request_history = defaultdict(list)
        self.user_scores = defaultdict(lambda: 100)  # Trust score (0-100)
    
    def calculate_limit(self, user_id: str, role: str) -> int:
        """Calculate dynamic rate limit based on behavior"""
        base_limit = {
            'guest': 10,
            'user': 100,
            'premium': 500,
            'admin': 1000
        }[role]
        
        # Adjust based on trust score
        trust_score = self.user_scores[user_id]
        adjusted_limit = int(base_limit * (trust_score / 100))
        
        return max(adjusted_limit, 5)  # Minimum 5 req/min
    
    def record_request(self, user_id: str, success: bool):
        """Record request and update trust score"""
        now = datetime.utcnow()
        
        # Clean old history (keep last hour)
        cutoff = now - timedelta(hours=1)
        self.request_history[user_id] = [
            req for req in self.request_history[user_id]
            if req['timestamp'] > cutoff
        ]
        
        # Record request
        self.request_history[user_id].append({
            'timestamp': now,
            'success': success
        })
        
        # Update trust score
        recent_requests = self.request_history[user_id][-20:]  # Last 20 requests
        success_rate = sum(1 for r in recent_requests if r['success']) / len(recent_requests)
        
        # Adjust trust score
        if success_rate > 0.9:
            self.user_scores[user_id] = min(100, self.user_scores[user_id] + 5)
        elif success_rate < 0.5:
            self.user_scores[user_id] = max(0, self.user_scores[user_id] - 10)
```

---

## Fine-Grained RBAC

### 6.1 Casbin Policy Engine

**Installation**:
```bash
pip install casbin casbin-sqlalchemy-adapter
```

**Casbin Model Configuration**:
```ini
# config/rbac_model.conf
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

**Casbin Policy Implementation**:
```python
# app/auth/rbac.py
import casbin
from casbin_sqlalchemy_adapter import Adapter

# Initialize Casbin
adapter = Adapter('postgresql://user:pass@localhost:5432/aiwebtest')
enforcer = casbin.Enforcer('config/rbac_model.conf', adapter)

# Define policies
def initialize_policies():
    """Initialize RBAC policies"""
    
    # Role hierarchy
    enforcer.add_grouping_policy("alice", "admin")
    enforcer.add_grouping_policy("bob", "user")
    enforcer.add_grouping_policy("charlie", "guest")
    
    # Admin permissions (full access)
    enforcer.add_policy("admin", "/api/tests/generate", "POST")
    enforcer.add_policy("admin", "/api/tests/execute", "POST")
    enforcer.add_policy("admin", "/api/tests/*", "GET")
    enforcer.add_policy("admin", "/api/tests/*", "DELETE")
    enforcer.add_policy("admin", "/api/users/*", "*")
    enforcer.add_policy("admin", "/api/config/*", "*")
    
    # User permissions (standard access)
    enforcer.add_policy("user", "/api/tests/generate", "POST")
    enforcer.add_policy("user", "/api/tests/execute", "POST")
    enforcer.add_policy("user", "/api/tests/*", "GET")
    enforcer.add_policy("user", "/api/users/me", "GET")
    
    # Guest permissions (read-only)
    enforcer.add_policy("guest", "/api/tests/*", "GET")
    enforcer.add_policy("guest", "/api/docs", "GET")

# FastAPI dependency
async def check_permission(request: Request, user: User = Depends(get_current_user)):
    """Check if user has permission for this endpoint"""
    path = request.url.path
    method = request.method
    
    if not enforcer.enforce(user.username, path, method):
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {user.role} cannot {method} {path}"
        )

# Apply to routes
@app.post("/api/tests/generate", dependencies=[Depends(check_permission)])
async def generate_tests():
    pass

@app.delete("/api/tests/{test_id}", dependencies=[Depends(check_permission)])
async def delete_test(test_id: int):
    pass
```

### 6.2 Dynamic Permission Management

**Admin API for Permission Management**:
```python
# app/api/admin/permissions.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin/permissions", tags=["Admin - Permissions"])

@router.post("/assign-role")
async def assign_role(
    username: str,
    role: str,
    admin: User = Depends(require_admin)
):
    """Assign role to user"""
    enforcer.add_grouping_policy(username, role)
    return {"status": "success", "message": f"Assigned {role} to {username}"}

@router.post("/grant-permission")
async def grant_permission(
    role: str,
    resource: str,
    action: str,
    admin: User = Depends(require_admin)
):
    """Grant permission to role"""
    enforcer.add_policy(role, resource, action)
    return {"status": "success", "message": f"Granted {action} on {resource} to {role}"}

@router.get("/user-permissions/{username}")
async def get_user_permissions(
    username: str,
    admin: User = Depends(require_admin)
):
    """Get all permissions for user"""
    permissions = enforcer.get_permissions_for_user(username)
    return {"username": username, "permissions": permissions}
```

---

## PII Protection

### 7.1 PII Detection with Presidio

**Installation**:
```bash
pip install presidio-analyzer presidio-anonymizer
```

**Presidio Configuration**:
```python
# app/security/pii_protection.py
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class PIIProtector:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    def detect_pii(self, text: str, language: str = 'en') -> List[dict]:
        """Detect PII entities in text"""
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                'EMAIL_ADDRESS',
                'PHONE_NUMBER',
                'CREDIT_CARD',
                'PERSON',
                'LOCATION',
                'IP_ADDRESS',
                'IBAN_CODE'
            ]
        )
        return [
            {
                'type': r.entity_type,
                'start': r.start,
                'end': r.end,
                'score': r.score,
                'text': text[r.start:r.end]
            }
            for r in results
        ]
    
    def mask_pii(self, text: str) -> str:
        """Mask PII in text"""
        results = self.analyzer.analyze(text, language='en')
        return self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                'EMAIL_ADDRESS': OperatorConfig('mask', {'chars_to_mask': 10, 'masking_char': '*'}),
                'PHONE_NUMBER': OperatorConfig('mask', {'chars_to_mask': 8, 'masking_char': '*'}),
                'CREDIT_CARD': OperatorConfig('mask', {'chars_to_mask': 12, 'masking_char': '*'}),
                'PERSON': OperatorConfig('replace', {'new_value': '[PERSON]'}),
                'LOCATION': OperatorConfig('replace', {'new_value': '[LOCATION]'}),
            }
        ).text
    
    def pseudonymize_pii(self, text: str) -> tuple[str, dict]:
        """Pseudonymize PII (reversible with mapping)"""
        results = self.analyzer.analyze(text, language='en')
        
        # Generate pseudonyms
        pseudonym_map = {}
        for result in results:
            original = text[result.start:result.end]
            pseudonym = f"<{result.entity_type}_{hash(original) % 10000}>"
            pseudonym_map[pseudonym] = original
        
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                entity: OperatorConfig('replace', {'new_value': f"<{entity}_{hash(text[r.start:r.end]) % 10000}>"})
                for entity in ['EMAIL_ADDRESS', 'PHONE_NUMBER', 'PERSON']
                for r in results if r.entity_type == entity
            }
        )
        
        return anonymized.text, pseudonym_map

# Usage in API
pii_protector = PIIProtector()

@app.post("/api/tests/generate")
async def generate_tests(request: TestGenerationRequest):
    """Generate tests with PII protection"""
    
    # Detect PII in requirements
    pii_entities = pii_protector.detect_pii(request.requirements_text)
    
    if pii_entities:
        # Log PII detection
        logger.warning(f"PII detected in requirements: {pii_entities}")
        
        # Mask PII
        masked_requirements = pii_protector.mask_pii(request.requirements_text)
        request.requirements_text = masked_requirements
    
    # Proceed with test generation
    tests = await generate_tests_from_requirements(request.requirements_text)
    return tests
```

### 7.2 Data Masking Strategies

**Database-Level Masking**:
```python
# app/db/masking.py
import hashlib

class DataMasking:
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address"""
        local, domain = email.split('@')
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number"""
        return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
    
    @staticmethod
    def hash_identifier(identifier: str) -> str:
        """Hash identifier (one-way)"""
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    @staticmethod
    def tokenize(value: str, secret: str) -> str:
        """Tokenize value (reversible with secret)"""
        key = hashlib.sha256(secret.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(key))
        return fernet.encrypt(value.encode()).decode()

# Apply masking to query results
@app.get("/api/users")
async def get_users(current_user: User = Depends(get_current_user)):
    """Get users with data masking"""
    users = await db.fetch_all("SELECT * FROM users")
    
    # Mask PII if not admin
    if current_user.role != 'admin':
        for user in users:
            user['email'] = DataMasking.mask_email(user['email'])
            user['phone'] = DataMasking.mask_phone(user['phone'])
    
    return users
```

---

## Security Monitoring & Alerting

### 8.1 SIEM Integration (ELK Stack)

**Logging Configuration**:
```python
# app/logging/security_logger.py
import logging
from pythonjsonlogger import jsonlogger

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter for ELK Stack
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(user)s %(ip)s %(action)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_authentication(self, user: str, ip: str, success: bool, mfa: bool = False):
        """Log authentication attempts"""
        self.logger.info(
            "Authentication attempt",
            extra={
                'user': user,
                'ip': ip,
                'success': success,
                'mfa_enabled': mfa,
                'action': 'login',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_authorization(self, user: str, resource: str, action: str, allowed: bool):
        """Log authorization checks"""
        self.logger.info(
            "Authorization check",
            extra={
                'user': user,
                'resource': resource,
                'action': action,
                'allowed': allowed,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_suspicious_activity(self, user: str, ip: str, reason: str):
        """Log suspicious activity"""
        self.logger.warning(
            "Suspicious activity detected",
            extra={
                'user': user,
                'ip': ip,
                'reason': reason,
                'action': 'suspicious_activity',
                'timestamp': datetime.utcnow().isoformat()
            }
        )

security_logger = SecurityLogger()

# Usage in middleware
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    
    # Log request
    user = getattr(request.state, 'user', None)
    security_logger.log_authorization(
        user=user.username if user else 'anonymous',
        resource=request.url.path,
        action=request.method,
        allowed=True
    )
    
    response = await call_next(request)
    
    # Detect suspicious patterns
    if response.status_code == 403:
        security_logger.log_suspicious_activity(
            user=user.username if user else 'anonymous',
            ip=request.client.host,
            reason='Multiple 403 responses'
        )
    
    return response
```

**Logstash Configuration**:
```yaml
# config/logstash.conf
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parse security logs
  if [action] == "login" {
    mutate {
      add_tag => ["authentication"]
    }
  }
  
  if [action] == "suspicious_activity" {
    mutate {
      add_tag => ["security_alert"]
    }
  }
  
  # GeoIP enrichment
  geoip {
    source => "ip"
    target => "geo"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "security-logs-%{+YYYY.MM.dd}"
  }
}
```

### 8.2 Intrusion Detection System (IDS)

**Custom IDS Rules**:
```python
# app/security/ids.py
from collections import defaultdict
from datetime import datetime, timedelta

class IntrusionDetectionSystem:
    def __init__(self):
        self.failed_logins = defaultdict(list)
        self.rate_limit_violations = defaultdict(list)
        self.suspicious_ips = set()
    
    def check_brute_force(self, user: str, ip: str, failed: bool) -> bool:
        """Detect brute force attacks"""
        if not failed:
            return False
        
        # Track failed logins
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=5)
        
        self.failed_logins[user] = [
            timestamp for timestamp in self.failed_logins[user]
            if timestamp > cutoff
        ]
        self.failed_logins[user].append(now)
        
        # Alert if >5 failures in 5 minutes
        if len(self.failed_logins[user]) > 5:
            security_logger.log_suspicious_activity(
                user=user,
                ip=ip,
                reason=f"Brute force detected: {len(self.failed_logins[user])} failed logins"
            )
            self.suspicious_ips.add(ip)
            return True
        
        return False
    
    def check_sql_injection(self, params: dict) -> bool:
        """Detect SQL injection attempts"""
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bOR\b.*=.*)",
            r"(--|\#|\/\*)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bEXEC\b|\bEXECUTE\b)",
        ]
        
        for key, value in params.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        security_logger.log_suspicious_activity(
                            user='unknown',
                            ip='unknown',
                            reason=f"SQL injection attempt: {pattern} in {key}"
                        )
                        return True
        
        return False
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.suspicious_ips

ids = IntrusionDetectionSystem()

# Middleware integration
@app.middleware("http")
async def ids_middleware(request: Request, call_next):
    ip = request.client.host
    
    # Check if IP is blocked
    if ids.is_ip_blocked(ip):
        raise HTTPException(status_code=403, detail="IP blocked due to suspicious activity")
    
    # Check for SQL injection
    if ids.check_sql_injection(dict(request.query_params)):
        raise HTTPException(status_code=403, detail="SQL injection detected")
    
    response = await call_next(request)
    return response
```

### 8.3 Real-Time Alerting

**AlertManager Integration**:
```python
# app/monitoring/alerting.py
import requests

class SecurityAlerter:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_alert(self, severity: str, title: str, description: str):
        """Send alert to AlertManager or Slack"""
        payload = {
            'severity': severity,
            'title': title,
            'description': description,
            'timestamp': datetime.utcnow().isoformat(),
            'labels': {
                'component': 'aiwebtest',
                'environment': 'production'
            }
        }
        
        requests.post(self.webhook_url, json=payload)
    
    def alert_brute_force(self, user: str, ip: str, attempts: int):
        """Alert on brute force attack"""
        self.send_alert(
            severity='high',
            title='Brute Force Attack Detected',
            description=f"User '{user}' from IP {ip} has {attempts} failed login attempts"
        )
    
    def alert_sql_injection(self, ip: str, payload: str):
        """Alert on SQL injection attempt"""
        self.send_alert(
            severity='critical',
            title='SQL Injection Attempt',
            description=f"SQL injection attempt from IP {ip}: {payload}"
        )
    
    def alert_unauthorized_access(self, user: str, resource: str):
        """Alert on unauthorized access"""
        self.send_alert(
            severity='medium',
            title='Unauthorized Access Attempt',
            description=f"User '{user}' attempted to access {resource} without permission"
        )

alerter = SecurityAlerter(webhook_url=os.environ.get('ALERT_WEBHOOK_URL'))
```

---

## Secrets Management

### 9.1 HashiCorp Vault Integration

**Vault Configuration**:
```python
# app/security/vault.py
import hvac

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.environ.get('VAULT_ADDR', 'http://localhost:8200'),
            token=os.environ.get('VAULT_TOKEN')
        )
    
    def get_secret(self, path: str) -> dict:
        """Get secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']
    
    def set_secret(self, path: str, secret: dict):
        """Store secret in Vault"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secret
        )
    
    def rotate_database_credentials(self):
        """Rotate database credentials"""
        # Get current credentials
        current = self.get_secret('database/postgres')
        
        # Generate new password
        new_password = secrets.token_urlsafe(32)
        
        # Update database password
        # (implementation depends on database)
        
        # Store new credentials
        self.set_secret('database/postgres', {
            'username': current['username'],
            'password': new_password,
            'host': current['host'],
            'port': current['port'],
            'database': current['database']
        })

vault = VaultClient()

# Get database connection from Vault
db_config = vault.get_secret('database/postgres')
engine = create_engine(
    f"postgresql://{db_config['username']}:{db_config['password']}@"
    f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
)
```

**Docker Compose with Vault**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  vault:
    image: vault:latest
    container_name: vault
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: "dev-token"
      VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    cap_add:
      - IPC_LOCK
    volumes:
      - ./vault/data:/vault/data
      - ./vault/config:/vault/config
    command: server -dev

  backend:
    build: .
    environment:
      VAULT_ADDR: "http://vault:8200"
      VAULT_TOKEN: "dev-token"
    depends_on:
      - vault
```

---

## Security Audit & Compliance

### 10.1 Audit Logging

**Comprehensive Audit Trail**:
```python
# app/audit/audit_logger.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer)
    username = Column(String(255))
    action = Column(String(100))
    resource = Column(String(255))
    resource_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(String(500))
    response_status = Column(Integer)
    changes = Column(Text)  # JSON of before/after

class AuditLogger:
    def __init__(self, db_session):
        self.db = db_session
    
    def log_action(
        self,
        user: User,
        action: str,
        resource: str,
        resource_id: str,
        request: Request,
        changes: dict = None
    ):
        """Log auditable action"""
        audit_entry = AuditLog(
            user_id=user.id,
            username=user.username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent'),
            request_method=request.method,
            request_path=str(request.url),
            changes=json.dumps(changes) if changes else None
        )
        self.db.add(audit_entry)
        self.db.commit()

# Middleware for automatic audit logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    user = getattr(request.state, 'user', None)
    
    # Capture request body for auditing
    body = await request.body()
    request._body = body  # Store for later
    
    response = await call_next(request)
    
    # Log auditable actions
    if user and request.method in ['POST', 'PUT', 'DELETE']:
        audit_logger.log_action(
            user=user,
            action=f"{request.method} {request.url.path}",
            resource=request.url.path.split('/')[2] if len(request.url.path.split('/')) > 2 else 'unknown',
            resource_id=request.url.path.split('/')[-1],
            request=request
        )
    
    return response
```

### 10.2 Compliance Reporting

**GDPR Compliance**:
```python
# app/compliance/gdpr.py
class GDPRCompliance:
    def __init__(self, db_session):
        self.db = db_session
    
    async def export_user_data(self, user_id: int) -> dict:
        """Export all user data (GDPR Article 15)"""
        user = await self.db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        test_cases = await self.db.fetch_all("SELECT * FROM test_cases WHERE user_id = ?", (user_id,))
        audit_logs = await self.db.fetch_all("SELECT * FROM audit_logs WHERE user_id = ?", (user_id,))
        
        return {
            'user': dict(user),
            'test_cases': [dict(tc) for tc in test_cases],
            'audit_logs': [dict(al) for al in audit_logs],
            'export_date': datetime.utcnow().isoformat()
        }
    
    async def delete_user_data(self, user_id: int):
        """Delete all user data (GDPR Article 17 - Right to be forgotten)"""
        # Anonymize audit logs (keep for compliance)
        await self.db.execute(
            "UPDATE audit_logs SET username = 'deleted_user', user_id = NULL WHERE user_id = ?",
            (user_id,)
        )
        
        # Delete test cases
        await self.db.execute("DELETE FROM test_cases WHERE user_id = ?", (user_id,))
        
        # Delete user
        await self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    async def consent_management(self, user_id: int, consent_type: str, granted: bool):
        """Manage user consent"""
        await self.db.execute(
            "INSERT INTO user_consents (user_id, consent_type, granted, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, consent_type, granted, datetime.utcnow())
        )

@app.post("/api/gdpr/export")
async def export_data(user: User = Depends(get_current_user)):
    """Export user data (GDPR compliance)"""
    gdpr = GDPRCompliance(db)
    data = await gdpr.export_user_data(user.id)
    return data

@app.post("/api/gdpr/delete")
async def delete_data(user: User = Depends(get_current_user)):
    """Delete user data (Right to be forgotten)"""
    gdpr = GDPRCompliance(db)
    await gdpr.delete_user_data(user.id)
    return {"status": "success", "message": "User data deleted"}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Days 1-5)

#### Day 1-2: API Rate Limiting & RBAC
- [ ] Install and configure slowapi
- [ ] Set up Redis for distributed rate limiting
- [ ] Implement role-based rate limits
- [ ] Install and configure Casbin
- [ ] Define RBAC policies
- [ ] Integrate with FastAPI routes

**Deliverables**:
- `app/middleware/rate_limit.py`
- `app/auth/rbac.py`
- `config/rbac_model.conf`

#### Day 3-5: Defense-in-Depth (Layers 1-2)
- [ ] Set up ModSecurity WAF
- [ ] Configure OWASP Core Rule Set
- [ ] Implement Kubernetes NetworkPolicy
- [ ] Add input validation with Pydantic
- [ ] Implement CSRF protection
- [ ] Add XSS prevention (CSP headers)

**Deliverables**:
- `nginx.conf` with ModSecurity
- `k8s/networkpolicy.yaml`
- `app/middleware/csrf.py`
- `app/middleware/security_headers.py`

### Phase 2: Data Protection (Days 6-11)

#### Day 6-8: PII Protection
- [ ] Install Presidio
- [ ] Implement PII detection
- [ ] Add data masking strategies
- [ ] Implement pseudonymization
- [ ] Test with sample data

**Deliverables**:
- `app/security/pii_protection.py`
- `app/db/masking.py`

#### Day 9-11: Encryption & Secrets
- [ ] Implement AES-256 encryption at rest
- [ ] Configure TLS 1.3 for PostgreSQL
- [ ] Set up HashiCorp Vault
- [ ] Implement API key rotation
- [ ] Add field-level encryption

**Deliverables**:
- `app/db/encryption.py`
- `app/security/vault.py`
- `app/auth/api_keys.py`

### Phase 3: Monitoring & Compliance (Days 12-16)

#### Day 12-14: Security Monitoring
- [ ] Set up ELK Stack (SIEM)
- [ ] Implement security logging
- [ ] Configure Logstash pipelines
- [ ] Create Kibana dashboards
- [ ] Implement IDS rules
- [ ] Set up real-time alerting

**Deliverables**:
- `app/logging/security_logger.py`
- `app/security/ids.py`
- `app/monitoring/alerting.py`
- `config/logstash.conf`

#### Day 15-16: Audit & Compliance
- [ ] Implement audit logging
- [ ] Create GDPR compliance endpoints
- [ ] Set up compliance reporting
- [ ] Document security policies
- [ ] Conduct security review

**Deliverables**:
- `app/audit/audit_logger.py`
- `app/compliance/gdpr.py`
- `documentation/SECURITY-POLICIES.md`

---

## Cost Analysis

### Open-Source Tools (Free)
- **ModSecurity**: $0
- **Presidio**: $0
- **Casbin**: $0
- **slowapi**: $0
- **ELK Stack (self-hosted)**: $0
- **HashiCorp Vault (self-hosted)**: $0

### Infrastructure Costs (Monthly)
| Component | Cost | Notes |
|-----------|------|-------|
| Redis (rate limiting) | $10-30 | AWS ElastiCache or self-hosted |
| ELK Stack (3 nodes) | $100-200 | Self-hosted on cloud VMs |
| Vault (HA setup) | $50-100 | Self-hosted or managed |
| WAF (CloudFlare) | $0-200 | Free tier available |
| **Total** | **$160-530/month** | Scales with traffic |

### ROI Analysis
- **Cost of a security breach**: $50,000 - $1,000,000+ (GDPR fines, data loss, reputation)
- **Monthly security investment**: $160-530
- **Break-even**: Preventing 1 breach = 100-6000 months of security costs

**Conclusion**: Security is critical and cost-effective.

---

## Testing Strategy

### Security Testing Checklist

#### Unit Tests
- [ ] Test rate limiting for each role
- [ ] Test RBAC permission checks
- [ ] Test PII detection accuracy
- [ ] Test encryption/decryption
- [ ] Test input validation

#### Integration Tests
- [ ] Test WAF rule effectiveness
- [ ] Test CSRF protection
- [ ] Test MFA flow
- [ ] Test API key rotation
- [ ] Test audit logging

#### Penetration Testing
- [ ] SQL injection attempts
- [ ] XSS attempts
- [ ] CSRF attempts
- [ ] Brute force attacks
- [ ] Authorization bypass attempts

#### Compliance Testing
- [ ] GDPR data export
- [ ] GDPR data deletion
- [ ] Audit log completeness
- [ ] Encryption verification

---

## Summary & Integration

### Key Achievements

✅ **Defense-in-Depth**: 5 security layers implemented  
✅ **API Rate Limiting**: Role-based quotas with slowapi  
✅ **Fine-Grained RBAC**: Casbin policy engine  
✅ **PII Protection**: Presidio + data masking  
✅ **Encryption**: AES-256 at rest, TLS 1.3 in transit  
✅ **Security Monitoring**: ELK Stack SIEM + IDS  
✅ **Secrets Management**: HashiCorp Vault  
✅ **Compliance**: GDPR-compliant audit logging  

### Integration with Other Components

| Component | Integration Point |
|-----------|------------------|
| **MLOps** | Model governance, A/B testing authentication |
| **Deployment** | Circuit breakers for security services |
| **RL** | Secure storage of RL model weights |
| **Multi-Agent** | RBAC for agent-to-agent communication |

### Next Steps

1. **Review** this architecture document
2. **Update PRD** with security functional requirements
3. **Update SRS** with security technology stack
4. **Begin Phase 1** implementation (Days 1-5)
5. **Conduct security audit** after implementation

---

## Appendix

### Security Metrics Dashboard

**Key Metrics to Track**:
- Failed login attempts per minute
- Rate limit violations per user
- PII detection rate
- Unauthorized access attempts
- Average response time impact of security layers
- Audit log volume
- Security alerts per day

### Security Incident Response Plan

1. **Detection**: SIEM alerts + IDS
2. **Triage**: Security team reviews alert
3. **Containment**: Block IP, revoke tokens
4. **Investigation**: Review audit logs
5. **Remediation**: Patch vulnerability
6. **Post-Mortem**: Document lessons learned

---

**End of Security Architecture Document**

This architecture provides **enterprise-grade security** for the AI-Web-Test v1 platform, implementing industry best practices (2025 standards) with defense-in-depth, PII protection, fine-grained RBAC, and comprehensive monitoring.

