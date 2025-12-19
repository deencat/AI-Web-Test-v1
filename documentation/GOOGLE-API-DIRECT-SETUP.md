# Google API Direct Setup Guide

**Date:** December 8, 2025  
**Purpose:** Configure Google AI Studio API directly to bypass OpenRouter credit limits

---

## ✅ What Changed

We've updated the backend to support **direct Google API integration**, which means:
- ✅ No OpenRouter credits needed
- ✅ Use Google AI Studio's FREE tier
- ✅ No max_tokens limits from OpenRouter
- ✅ Faster (no middleman)

---

## 🔑 Step 1: Get Your Google API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the API key (starts with `AIza...`)

---

## 📝 Step 2: Update Your `.env` File

Open `backend/.env` and add your Google API key:

```env
# ============================================
# Google AI Studio Configuration (Direct)
# ============================================
GOOGLE_API_KEY=AIzaSy...your-actual-key-here

# ============================================
# Model Selection
# ============================================
USE_GOOGLE_DIRECT=true
GOOGLE_MODEL=gemini-1.5-flash
```

**Available Models:**
- `gemini-1.5-flash` - Fast and efficient (RECOMMENDED)
- `gemini-1.5-pro` - More capable, slower
- `gemini-2.0-flash-exp` - Latest experimental version

---

## 🔄 Step 3: Restart Backend Server

In your `python` terminal:

1. Press **Ctrl+C** to stop the server
2. Restart with:
   ```bash
   cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend
   source venv/bin/activate
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

---

## 🧪 Step 4: Test It

Look for this message in the console when running a test:
```
[DEBUG] ✅ Using Google API directly with model: gemini-1.5-flash
[DEBUG] This will use your Google AI Studio free tier (no OpenRouter credits needed)
```

---

## 🔀 How to Switch Back to OpenRouter

If you want to use OpenRouter again:

```env
USE_GOOGLE_DIRECT=false
```

Then restart the backend.

---

## 💰 Cost Comparison

| Method | Cost | Rate Limits |
|--------|------|-------------|
| **Google Direct** (NEW) | FREE* | 15 RPM (free tier) |
| OpenRouter BYOK | Uses your credits | Varies |
| OpenRouter (no key) | Uses OR credits | Often rate-limited |

*Google AI Studio free tier includes generous limits for development

---

## 🐛 Troubleshooting

### Error: "GOOGLE_API_KEY not set"
- Make sure you added `GOOGLE_API_KEY=AIza...` to `backend/.env`
- Make sure `USE_GOOGLE_DIRECT=true`
- Restart the backend server

### Error: "API key not valid"
- Check your API key at: https://aistudio.google.com/app/apikey
- Make sure you copied the entire key
- Try generating a new API key

### Still seeing OpenRouter errors?
- Check that `USE_GOOGLE_DIRECT=true` (not "True" or "1", must be lowercase "true")
- Restart the backend server
- Check the console logs for the "Using Google API directly" message

---

## 📚 References

- Google AI Studio: https://aistudio.google.com/
- Gemini API Docs: https://ai.google.dev/docs
- LiteLLM Gemini Integration: https://docs.litellm.ai/docs/providers/gemini

---

## ✨ Benefits for Sprint 1-3 Integration Testing

1. **No Credit Worries:** Test freely without OpenRouter credit limits
2. **Better Quality:** Gemini 1.5 Flash is fast and high-quality
3. **Free Tier:** Google provides generous free quotas for testing
4. **Direct Control:** You control your own API usage and limits
