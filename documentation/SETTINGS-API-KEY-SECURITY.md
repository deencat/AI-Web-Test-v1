# Settings Page - API Key Security Analysis

**Date:** December 16, 2025  
**Status:** 🔴 **CRITICAL SECURITY NOTICE**  
**Component:** Settings Page (Frontend)

---

## 🚨 Current Security Status

### ❌ **API Keys Are NOT Saved**

**Current Implementation:**
```tsx
// frontend/src/pages/SettingsPage.tsx
const [googleApiKey, setGoogleApiKey] = useState('');
const [cerebrasApiKey, setCerebrasApiKey] = useState('');
const [openrouterApiKey, setOpenrouterApiKey] = useState('');
```

**What Happens When User Enters Key:**
1. ✅ User types API key in input field
2. ✅ Key stored in React component state (temporary, in-memory)
3. ❌ **Key is LOST when page refreshes**
4. ❌ **Key is NOT sent to backend**
5. ❌ **Key is NOT saved anywhere**

### 🎨 **This is a UI Prototype Only**

The Settings page is currently a **design mockup** showing how the interface would work. It does NOT actually save or use the API keys entered by users.

---

## 🔒 Security Concerns - Explained

### ⚠️ Why NOT Save Keys in Frontend?

**BAD Approach (Never Do This):**
```tsx
// ❌ NEVER DO THIS - Extremely Insecure!
localStorage.setItem('api_key', userApiKey);  // Exposed to XSS attacks
sessionStorage.setItem('api_key', userApiKey); // Exposed to XSS attacks
// Keys accessible via browser DevTools, extensions, etc.
```

**Security Risks:**
1. **XSS (Cross-Site Scripting)**: Malicious scripts can steal keys
2. **Browser Extensions**: Can read localStorage/sessionStorage
3. **DevTools Access**: Anyone with access to browser can see keys
4. **Client-Side Exposure**: Keys visible in browser memory/network tab
5. **No Encryption**: Keys stored in plain text

---

## ✅ Correct Approach - Backend Storage

### 🏆 **How API Keys SHOULD Be Handled**

```
┌─────────────────────────────────────────────────────────────┐
│                    Secure Architecture                       │
└─────────────────────────────────────────────────────────────┘

Frontend (Browser)              Backend (Server)
─────────────────              ─────────────────
                                                
User enters key                 ┌──────────────────┐
     │                          │  .env file       │
     │ POST /api/settings       │  ─────────────   │
     └────────────────────────► │  GOOGLE_API_KEY= │
                                │  CEREBRAS_KEY=   │
        Authenticated            │  OPENROUTER_KEY= │
        Request Only             └──────────────────┘
                                          │
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │  Environment     │
                                 │  Variables       │
                                 │  (Production)    │
                                 └──────────────────┘
                                          │
                                          │ Used by
                                          ▼
                                 ┌──────────────────┐
                                 │  Stagehand       │
                                 │  Test Generation │
                                 └──────────────────┘

✅ Keys never leave server
✅ Keys never sent to browser
✅ Keys encrypted at rest (production)
✅ Keys in environment variables
```

---

## 🔧 Current Configuration Method

### **How It Actually Works Now:**

**Step 1: Edit Backend .env File**
```bash
# /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/.env

# Test Generation (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=mistralai/mixtral-8x7b-instruct

# Test Execution - Choose ONE Provider
MODEL_PROVIDER=google

# Google Configuration
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_MODEL=gemini-2.5-flash

# Cerebras Configuration (Optional)
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CEREBRAS_MODEL=llama-3.3-70b

# OpenRouter for Execution (Optional)
# OPENROUTER_API_KEY already set above for generation
```

**Step 2: Restart Backend Server**
```bash
cd backend
source venv/bin/activate
python start_server.py
```

**Step 3: Keys Loaded from Environment**
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    GOOGLE_API_KEY: str | None = None
    CEREBRAS_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"  # ← Keys loaded from here
```

---

## 🎯 Where Keys Are Currently Stored

### **Development Environment:**

| Location | Purpose | Security | Status |
|----------|---------|----------|--------|
| `backend/.env` | Development config | ⚠️ Local only | ✅ Used |
| Frontend state | UI prototype | ❌ Not saved | ⚠️ Temporary |
| Database | - | - | ❌ Not implemented |
| Environment vars | - | - | ❌ Not used in prod |

### **What Happens to Keys:**

```python
# When backend starts:
# 1. Loads .env file
settings = Settings()  # Reads from .env

# 2. Keys available to services
stagehand = StagehandExecutionService()
await stagehand.initialize()  # Uses settings.GOOGLE_API_KEY

# 3. Keys NEVER sent to frontend
# Frontend makes API calls, backend uses keys internally
```

---

## 🔮 Recommended Implementation (Phase 2)

### **Option A: Backend API Endpoint (Recommended)**

**1. Create Settings API:**
```python
# backend/app/api/endpoints/settings.py

@router.post("/api/v1/settings/providers")
async def save_provider_settings(
    settings: ProviderSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save provider settings (admin only).
    Keys encrypted before database storage.
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Encrypt API keys before storage
    encrypted_key = encrypt_api_key(settings.api_key)
    
    # Save to database
    db_settings = ProviderConfig(
        user_id=current_user.id,
        provider=settings.provider,
        encrypted_api_key=encrypted_key,
        model=settings.model
    )
    db.add(db_settings)
    db.commit()
    
    return {"status": "saved"}
```

**2. Database Schema:**
```sql
CREATE TABLE provider_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,
    encrypted_api_key TEXT NOT NULL,  -- AES-256 encrypted
    model VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**3. Encryption Service:**
```python
# backend/app/services/encryption.py
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        # Key from environment (NOT in code)
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt_api_key(self, plain_key: str) -> str:
        return self.cipher.encrypt(plain_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        return self.cipher.decrypt(encrypted_key.encode()).decode()
```

**4. Frontend Integration:**
```tsx
// frontend/src/pages/SettingsPage.tsx
const handleSaveSettings = async () => {
    try {
        const response = await fetch('/api/v1/settings/providers', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: modelProvider,
                api_key: googleApiKey,  // Sent over HTTPS
                model: googleModel
            })
        });
        
        if (response.ok) {
            alert('✅ Settings saved securely');
            setGoogleApiKey('');  // Clear from UI
        }
    } catch (error) {
        alert('❌ Failed to save settings');
    }
};
```

---

### **Option B: Secrets Manager (Production)**

**For Production Deployment:**

```yaml
# docker-compose.yml (Example)
services:
  backend:
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - CEREBRAS_API_KEY=${CEREBRAS_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    secrets:
      - google_api_key
      - cerebras_api_key
      
secrets:
  google_api_key:
    external: true
  cerebras_api_key:
    external: true
```

**Use Cloud Provider Secrets:**
- AWS Secrets Manager
- Google Cloud Secret Manager
- Azure Key Vault
- HashiCorp Vault

---

## 📋 Security Checklist

### **Current Implementation:**
- ✅ Keys stored in backend `.env` (development)
- ✅ Keys NOT exposed to frontend
- ✅ Keys used server-side only
- ⚠️ Settings page is UI prototype only
- ❌ No user-configurable settings (yet)
- ❌ No database storage
- ❌ No encryption at rest
- ❌ No secrets manager integration

### **For Production (Phase 2):**
- [ ] Implement backend settings API
- [ ] Add database encryption (AES-256)
- [ ] Use secrets manager for sensitive data
- [ ] Implement admin-only access control
- [ ] Add audit logging for key changes
- [ ] Use HTTPS for all API calls
- [ ] Implement key rotation mechanism
- [ ] Add rate limiting on settings endpoints
- [ ] Regular security audits

---

## 🎓 Best Practices Summary

### **DO:**
✅ Store API keys on backend server only  
✅ Use environment variables for configuration  
✅ Encrypt keys in database (if stored)  
✅ Use HTTPS for all API communication  
✅ Implement admin-only access for key management  
✅ Use secrets manager in production  
✅ Clear keys from UI after saving  
✅ Log all key access attempts  

### **DON'T:**
❌ Store keys in localStorage/sessionStorage  
❌ Store keys in browser cookies  
❌ Send keys to frontend (except masked view)  
❌ Commit keys to version control  
❌ Log keys in plain text  
❌ Store keys unencrypted in database  
❌ Share keys across multiple applications  
❌ Expose keys in client-side code  

---

## 📊 Implementation Effort

### **Phase 2: Full Implementation**

| Task | Effort | Priority |
|------|--------|----------|
| Backend settings API | 3-4 hours | High |
| Database schema + migrations | 2 hours | High |
| Encryption service | 2-3 hours | High |
| Frontend integration | 2 hours | Medium |
| Admin access control | 2 hours | High |
| Testing (unit + integration) | 3-4 hours | High |
| Secrets manager integration | 4-6 hours | Medium |
| Audit logging | 2 hours | Low |
| **Total** | **20-27 hours** | - |

---

## 🚀 Quick Start (Current Method)

### **For Development:**

1. **Edit `.env` file:**
```bash
cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend
nano .env
```

2. **Add your keys:**
```env
GOOGLE_API_KEY=your-actual-key-here
CEREBRAS_API_KEY=your-actual-key-here
OPENROUTER_API_KEY=your-actual-key-here
MODEL_PROVIDER=google
GOOGLE_MODEL=gemini-2.5-flash
```

3. **Restart backend:**
```bash
python start_server.py
```

4. **Keys are now active** - No frontend configuration needed!

---

## 📞 FAQ

**Q: Where are my API keys stored right now?**  
A: In `backend/.env` file on your local machine only.

**Q: Can users configure keys via the Settings page?**  
A: Not yet - it's a UI prototype. Keys must be set in `.env` file.

**Q: Is it safe to enter keys in the Settings page?**  
A: The keys are NOT saved, so it's safe but pointless currently.

**Q: When will Settings page actually work?**  
A: Phase 2 implementation (~20-27 hours of development).

**Q: How do I change providers?**  
A: Edit `MODEL_PROVIDER` in `backend/.env` and restart server.

**Q: Are my keys secure?**  
A: Yes, as long as they're in `.env` on the server (not in browser).

**Q: Should I commit `.env` to Git?**  
A: **NO!** It's already in `.gitignore`. Never commit API keys.

---

## 🎯 Conclusion

### **Current State:**
- ✅ Settings page is a **UI mockup** only
- ✅ Keys stored securely in backend `.env`
- ✅ Keys never exposed to frontend
- ⚠️ User configuration not yet implemented

### **Recommendation:**
- ✅ Keep using `.env` for development (current method)
- ✅ Clearly document that Settings page is prototype
- ⏳ Plan Phase 2 implementation for user-configurable settings
- ✅ Follow security best practices when implementing

---

**Last Updated:** December 16, 2025  
**Next Review:** Before Phase 2 implementation  
**Status:** ✅ Current approach is secure for development
