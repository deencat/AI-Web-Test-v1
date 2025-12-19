# Cerebras Integration Guide

## 🧠 Overview

This guide explains how to integrate **Cerebras** for ultra-fast test execution in the AI Web Test platform. Cerebras provides industry-leading inference speeds using their custom Wafer-Scale Engine (WSE) hardware.

---

## 🎯 Why Cerebras?

### **Key Benefits:**
- ⚡ **Ultra-Fast Inference**: Up to 10x faster than traditional GPU-based inference
- 🎯 **Low Latency**: Optimized for real-time applications
- 💪 **High Quality**: Powered by Llama 3.1 models (8B and 70B)
- 🔧 **Easy Integration**: Works seamlessly with Stagehand via LiteLLM

### **Performance Comparison:**
| Provider | Model | Avg. Response Time |
|----------|-------|-------------------|
| Cerebras | llama3.1-8b | ~0.5-1s |
| OpenRouter | qwen-2.5-7b | ~2-4s |
| Google | gemini-1.5-flash | ~1-2s |

---

## 🚀 Quick Start

### **1. Get Cerebras API Key**

1. Visit: https://cloud.cerebras.ai/
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key

### **2. Configure Environment**

Add to your `backend/.env` file:

```env
# Cerebras Configuration
CEREBRAS_API_KEY=your-cerebras-api-key-here
CEREBRAS_MODEL=llama3.1-8b

# Set Cerebras as your provider
MODEL_PROVIDER=cerebras

# Or use legacy flag
USE_CEREBRAS=true
```

### **3. Test the Integration**

```bash
cd backend
python test_cerebras_stagehand.py
```

**Expected Output:**
```
🧠 Testing Stagehand with Cerebras API
======================================================================

[INFO] Using Cerebras model: llama3.1-8b
[OK] ✅ Stagehand initialized successfully!

[TEST 1] Navigation
[OK] ✅ Page loaded!

[TEST 2] AI-Powered Observation (Cerebras)
[OK] ✅ AI observation successful!
[PERFORMANCE] ⚡ Cerebras inference time: 0.68 seconds

🎉 Cerebras Test Complete!
```

---

## 🔧 Configuration Options

### **Method 1: Using MODEL_PROVIDER (Recommended)**

```env
# Set the provider
MODEL_PROVIDER=cerebras

# Configure the model
CEREBRAS_API_KEY=your-api-key-here
CEREBRAS_MODEL=llama3.1-8b
```

### **Method 2: Using USE_CEREBRAS Flag (Legacy)**

```env
# Enable Cerebras
USE_CEREBRAS=true

# Configure the model
CEREBRAS_API_KEY=your-api-key-here
CEREBRAS_MODEL=llama3.1-8b
```

### **Available Models:**

| Model | Parameters | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `llama3.1-8b` | 8 billion | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | General testing, fast iteration |
| `llama3.1-70b` | 70 billion | ⚡⚡ Moderate | ⭐⭐⭐⭐⭐ Excellent | Complex tests, high accuracy needed |

---

## 💻 Code Integration

### **Stagehand Service (Automatic)**

The `StagehandExecutionService` automatically detects and uses Cerebras:

```python
# backend/app/services/stagehand_service.py
# No code changes needed - it reads from .env automatically!

# When MODEL_PROVIDER=cerebras or USE_CEREBRAS=true:
config = StagehandConfig(
    env="LOCAL",
    headless=True,
    verbose=1,
    model_name=f"cerebras/{cerebras_model}",  # e.g., "cerebras/llama3.1-8b"
    model_api_key=cerebras_api_key,
)
```

### **Custom Test Script**

```python
import os
from dotenv import load_dotenv
from stagehand import Stagehand, StagehandConfig

load_dotenv()

async def test_with_cerebras():
    # Get Cerebras configuration
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    cerebras_model = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")
    
    # Configure Stagehand
    config = StagehandConfig(
        env="LOCAL",
        headless=False,
        verbose=1,
        model_name=f"cerebras/{cerebras_model}",
        model_api_key=cerebras_key,
    )
    
    stagehand = Stagehand(config)
    await stagehand.init()
    page = stagehand.page
    
    # Use Cerebras-powered AI actions
    await page.goto("https://example.com")
    result = await page.observe("find the main heading")
    await page.act("click the 'More information' link")
    
    await stagehand.close()
```

---

## 🎯 Best Practices

### **1. Model Selection**

**Use `llama3.1-8b` for:**
- ✅ Fast development and iteration
- ✅ Simple to moderate complexity tests
- ✅ When speed is critical
- ✅ Budget-conscious projects

**Use `llama3.1-70b` for:**
- ✅ Complex multi-step workflows
- ✅ High-accuracy requirements
- ✅ Production critical tests
- ✅ Advanced reasoning needed

### **2. Error Handling**

```python
try:
    # Cerebras-powered action
    await page.act("click the login button")
except Exception as e:
    # Fallback to simple selector
    await page.click("button:has-text('Login')")
```

### **3. Performance Optimization**

```python
# Enable verbose logging to measure performance
config = StagehandConfig(
    env="LOCAL",
    verbose=1,  # See inference times
    model_name="cerebras/llama3.1-8b"
)

# Monitor response times
import time
start = time.time()
await page.observe("...")
print(f"Cerebras inference: {time.time() - start:.2f}s")
```

---

## 📊 Provider Comparison

### **When to Use Each Provider:**

| Provider | Best For | Speed | Cost | Quality |
|----------|----------|-------|------|---------|
| **Cerebras** | Production, speed-critical | ⚡⚡⚡ | 💰💰 | ⭐⭐⭐⭐ |
| **Google** | Free tier, development | ⚡⚡ | 💰 FREE | ⭐⭐⭐⭐ |
| **OpenRouter** | Flexibility, model variety | ⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ |

### **Switching Between Providers:**

```env
# Development (Free)
MODEL_PROVIDER=google
GOOGLE_MODEL=gemini-2.5-flash

# Fast iteration
MODEL_PROVIDER=cerebras
CEREBRAS_MODEL=llama3.1-8b

# High accuracy
MODEL_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

---

## 🔍 Troubleshooting

### **Error: CEREBRAS_API_KEY not set**

**Solution:**
```bash
# Check .env file
cat backend/.env | grep CEREBRAS

# Add if missing
echo "CEREBRAS_API_KEY=your-key-here" >> backend/.env
```

### **Error: Model not found**

**Solution:**
```env
# Use correct model names (no version suffix)
CEREBRAS_MODEL=llama3.1-8b  # ✅ Correct
CEREBRAS_MODEL=llama-3.1-8b  # ❌ Wrong
```

### **Slow Response Times**

**Possible causes:**
1. Using `llama3.1-70b` instead of `llama3.1-8b`
2. Network latency
3. Complex prompts

**Solutions:**
```env
# Switch to faster model
CEREBRAS_MODEL=llama3.1-8b

# Simplify prompts
await page.act("click login")  # Instead of long descriptions
```

### **API Rate Limits**

Cerebras has rate limits based on your plan:

**Solution:**
```python
# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def execute_with_retry():
    await page.act("click button")
```

---

## 📚 Additional Resources

### **Documentation:**
- Cerebras Cloud: https://cloud.cerebras.ai/
- Stagehand Models: https://docs.stagehand.dev/v3/configuration/models
- LiteLLM Cerebras: https://docs.litellm.ai/docs/providers/cerebras

### **Related Files:**
- `backend/app/services/stagehand_service.py` - Service implementation
- `backend/app/core/config.py` - Configuration settings
- `backend/test_cerebras_stagehand.py` - Test script
- `backend/.env` - Environment configuration

### **Getting Help:**
1. Check Cerebras status: https://status.cerebras.ai/
2. Review Stagehand logs: Set `verbose=2` for detailed output
3. Test with simplified prompts
4. Try fallback to Google or OpenRouter

---

## ✅ Verification Checklist

After setting up Cerebras, verify:

- [ ] CEREBRAS_API_KEY is set in `.env`
- [ ] MODEL_PROVIDER is set to `cerebras` (or USE_CEREBRAS=true)
- [ ] Test script runs successfully: `python test_cerebras_stagehand.py`
- [ ] Response times are under 2 seconds
- [ ] AI actions work correctly
- [ ] Backend service initializes without errors

---

## 🎉 Success!

You're now ready to use Cerebras for ultra-fast test execution! 

**Next Steps:**
1. Run your existing tests with Cerebras
2. Compare performance with other providers
3. Monitor API usage and costs
4. Optimize prompts for best results

**Questions?** Check the troubleshooting section or review the Stagehand documentation.

---

**Last Updated:** December 9, 2025  
**Sprint:** 3 - Integration & Testing  
**Status:** ✅ Ready for Use
