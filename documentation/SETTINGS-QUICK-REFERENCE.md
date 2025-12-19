# Settings Page Dynamic Configuration - Quick Reference

## 🎯 What Is This?

Users can now configure AI provider settings through the UI instead of editing `.env` files.

## 🔑 Key Features

- **Dual Configuration**: Separate settings for Test Generation and Test Execution
- **20 AI Models**: Google (5), Cerebras (3), OpenRouter (12)
- **Live Updates**: Settings apply immediately without server restart
- **Persistent**: Settings saved to database per user
- **Secure**: API keys stay in .env, never exposed to frontend

---

## 📍 How to Use

### 1. Access Settings Page

```
http://localhost:5173/settings
```

Login required (admin / admin123)

### 2. Configure Test Generation

**What It Does**: Controls which AI generates your test cases

**Options**:
- **Google AI**: Best for quality (gemini-2.5-flash recommended)
- **Cerebras**: Best for speed (llama-3.3-70b recommended)
- **OpenRouter**: Best for variety (llama-3.3-70b-instruct:free is free!)

**Settings**:
- Provider dropdown
- Model dropdown (updates based on provider)
- Temperature: 0.0 (focused) to 1.0 (creative)
- Max Tokens: How much AI can generate

### 3. Configure Test Execution

**What It Does**: Controls which AI executes/validates your tests

**Same Options & Settings** as Generation

**Note**: Can use different providers for generation vs execution!

### 4. Save Settings

Click "Save Settings" button. You'll see:
- ✅ "Settings saved successfully!" - Success
- ❌ "Failed to save settings" - Check console

---

## 🔍 Verify It Works

### Check Backend Logs

**When Generating Tests**:
```
[DEBUG] 🎯 Loaded user generation config: provider=google, model=gemini-2.5-flash
[DEBUG] 🎯 Using user's generation config: google/gemini-2.5-flash (temp=0.7, max_tokens=2000)
```

**When Executing Tests**:
```
[DEBUG] 🎯 Loaded user execution config: provider=cerebras, model=llama-3.3-70b
[DEBUG] 🎯 Using user's configured provider: cerebras
[DEBUG] ✅ Using Cerebras with model: llama-3.3-70b
```

**If Using Defaults** (.env not overridden):
```
[DEBUG] 📋 Using .env default provider: openrouter
```

---

## 📊 Recommended Configurations

### Configuration 1: Quality First 🏆
- **Generation**: Google gemini-2.5-flash (temp: 0.7)
- **Execution**: Google gemini-2.5-flash (temp: 0.6)
- **Why**: Best accuracy, production-ready

### Configuration 2: Speed First ⚡
- **Generation**: Cerebras llama-3.3-70b (temp: 0.7)
- **Execution**: Cerebras llama-3.3-70b (temp: 0.6)
- **Why**: Fastest responses, real-time testing

### Configuration 3: Free Tier 💰
- **Generation**: OpenRouter llama-3.3-70b-instruct:free (temp: 0.7)
- **Execution**: OpenRouter llama-3.3-70b-instruct:free (temp: 0.6)
- **Why**: Zero cost, great for development

### Configuration 4: Hybrid Best 🎯
- **Generation**: Google gemini-2.5-flash (temp: 0.7)
- **Execution**: Cerebras llama-3.3-70b (temp: 0.6)
- **Why**: Quality generation + fast execution

---

## 🚨 Troubleshooting

### Problem: Settings save but execution still uses OpenRouter

**Check**:
1. Backend logs show `[DEBUG] 📋 Using .env default provider: openrouter`
2. User settings not loading

**Solution**:
```bash
# Restart backend server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Problem: "Failed to save settings"

**Check**:
1. Backend running? (http://localhost:8000)
2. Logged in? (JWT token valid)
3. Database migration applied?

**Solution**:
```bash
# Check backend logs for errors
cd backend
tail -f logs/app.log

# Reapply migration if needed
python migrations/add_user_settings_table.py
```

### Problem: Model dropdown empty

**Check**:
1. Provider selected first
2. API `/settings/available-providers` working

**Solution**:
```bash
# Test API directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/settings/available-providers
```

---

## 🔐 Security Notes

### What's Safe to Share?
- Provider name (google, cerebras, openrouter)
- Model name (e.g., gemini-2.5-flash)
- Temperature (0.0 - 1.0)
- Max tokens

### What's Secret? 🔒
- API keys (GOOGLE_API_KEY, CEREBRAS_API_KEY, OPENROUTER_API_KEY)
- Never in database
- Never sent to frontend
- Only in backend/.env

---

## 📚 API Endpoints

### Get Current Settings
```bash
GET /api/v1/settings/provider
Authorization: Bearer {token}

Response:
{
  "generation_provider": "google",
  "generation_model": "gemini-2.5-flash",
  "generation_temperature": 0.7,
  "generation_max_tokens": 2000,
  "execution_provider": "cerebras",
  "execution_model": "llama-3.3-70b",
  "execution_temperature": 0.6,
  "execution_max_tokens": 4096
}
```

### Update Settings
```bash
PUT /api/v1/settings/provider
Authorization: Bearer {token}
Content-Type: application/json

{
  "generation_provider": "google",
  "generation_model": "gemini-2.5-flash",
  "execution_provider": "cerebras",
  "execution_model": "llama-3.3-70b"
}
```

### Get Available Providers
```bash
GET /api/v1/settings/available-providers
Authorization: Bearer {token}

Response:
{
  "providers": [
    {
      "name": "google",
      "display_name": "Google AI",
      "description": "Google Gemini models",
      "models": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (New)"},
        ...
      ]
    },
    ...
  ]
}
```

---

## 🎯 Quick Start

```bash
# 1. Run integration tests
./test_settings_integration.sh

# 2. Open frontend
http://localhost:5173/settings

# 3. Select providers
# - Test Generation: Google / gemini-2.5-flash
# - Test Execution: Cerebras / llama-3.3-70b

# 4. Click "Save Settings"

# 5. Generate a test case
# - Go to Test Generation page
# - Enter requirement
# - Click "Generate Tests"

# 6. Check backend logs
# - Should see: [DEBUG] 🎯 Loaded user generation config: provider=google
```

---

## 📝 For Developers

### Add a New Provider

1. **Update `user_settings_service.py`**:
```python
PROVIDER_CONFIGS = {
    # ... existing providers
    "new_provider": {
        "name": "new_provider",
        "display_name": "New Provider",
        "description": "New AI provider",
        "models": [
            {"id": "model-1", "name": "Model 1"},
        ],
        "default_model": "model-1"
    }
}
```

2. **Update stagehand service** to support new provider

3. **Test**:
```bash
python test_settings_api.py
```

### Add a New Model

1. **Update provider's models array**:
```python
"models": [
    # ... existing models
    {"id": "new-model-id", "name": "New Model Name"}
]
```

2. **No code changes needed** - models are dynamically loaded!

---

## 🎉 Summary

- ✅ **20 models** across 3 providers
- ✅ **Dual config** (generation + execution)
- ✅ **Secure** (keys in .env only)
- ✅ **Live updates** (no restart needed)
- ✅ **Tested** (8/8 API tests passing)

**You're ready to go!** 🚀

---

**Need Help?**
- Check `SETTINGS-DYNAMIC-CONFIG-COMPLETE.md` for full implementation details
- Check `SETTINGS-PAGE-TESTING-CHECKLIST.md` for comprehensive testing guide
- Check backend logs for debug messages
