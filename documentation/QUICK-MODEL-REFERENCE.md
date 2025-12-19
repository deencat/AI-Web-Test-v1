# Quick Model Provider Reference

## 🚀 One-Line Configuration Changes

### Switch to Google (FREE)
```bash
echo "MODEL_PROVIDER=google" >> backend/.env
```

### Switch to Cerebras (FAST)
```bash
echo "MODEL_PROVIDER=cerebras" >> backend/.env
echo "CEREBRAS_API_KEY=your-key-here" >> backend/.env
```

### Switch to OpenRouter (FLEXIBLE)
```bash
echo "MODEL_PROVIDER=openrouter" >> backend/.env
```

---

## ⚙️ Complete .env Examples

### Google Configuration
```env
MODEL_PROVIDER=google
GOOGLE_API_KEY=your-google-key-here
GOOGLE_MODEL=gemini-2.5-flash
```

### Cerebras Configuration
```env
MODEL_PROVIDER=cerebras
CEREBRAS_API_KEY=your-cerebras-key-here
CEREBRAS_MODEL=llama3.1-8b
```

### OpenRouter Configuration
```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

---

## 🔑 Getting API Keys

| Provider | Get Key From | Free Tier? |
|----------|--------------|------------|
| **Google** | https://aistudio.google.com/app/apikey | ✅ Yes |
| **Cerebras** | https://cloud.cerebras.ai/ | ❌ No |
| **OpenRouter** | https://openrouter.ai/keys | ⚠️ Some models |

---

## ✅ Quick Test Commands

```bash
# Test current configuration
cd backend
python test_cerebras_stagehand.py

# Test specific provider
MODEL_PROVIDER=google python test_stagehand_openrouter.py
MODEL_PROVIDER=cerebras python test_cerebras_stagehand.py

# Test backend service
MODEL_PROVIDER=cerebras uvicorn app.main:app --reload
```

---

## 📊 When to Use What

```
┌─────────────────────────────────────────────┐
│ Need FREE?           → Google               │
│ Need SPEED?          → Cerebras             │
│ Need QUALITY?        → OpenRouter (Claude)  │
│ Need FLEXIBILITY?    → OpenRouter           │
└─────────────────────────────────────────────┘
```

---

## 🎯 Recommended Models

| Provider | Recommended Model | Why |
|----------|------------------|-----|
| Google | `gemini-2.5-flash` | Latest, balanced |
| Cerebras | `llama3.1-8b` | Fast, cost-effective |
| OpenRouter | `anthropic/claude-3.5-sonnet` | Best quality |

---

## 🔄 Switching Checklist

- [ ] Set `MODEL_PROVIDER` in `.env`
- [ ] Add provider-specific API key
- [ ] Choose model for that provider
- [ ] Restart backend server
- [ ] Run test to verify

---

## ⚡ Performance Reference

| Provider | Model | Speed | Cost/1K tests |
|----------|-------|-------|---------------|
| Google | gemini-2.5-flash | ~1.2s | FREE |
| Cerebras | llama3.1-8b | ~0.7s | ~$5 |
| OpenRouter | claude-3-haiku | ~1.9s | ~$12 |
| OpenRouter | claude-3.5-sonnet | ~2.3s | ~$150 |

---

**For detailed information, see:**
- [Cerebras Integration Guide](./CEREBRAS-INTEGRATION-GUIDE.md)
- [Model Provider Comparison](./MODEL-PROVIDER-COMPARISON.md)
- [Model Configuration Summary](./MODEL-CONFIGURATION-SUMMARY.md)
