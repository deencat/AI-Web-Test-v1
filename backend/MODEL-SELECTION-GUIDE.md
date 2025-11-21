# OpenRouter Model Selection Guide

This guide helps you choose the right LLM model for your needs in the AI Web Test project.

---

## 🆓 **Free Open-Source Models (Recommended for Development)**

### **Meta Llama 3.1 8B Instruct** ⭐ **DEFAULT**
```env
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```
- **Cost:** FREE (rate limited)
- **Quality:** Good for most tasks
- **Speed:** Fast
- **Best for:** Development, testing, learning
- **Limitations:** Rate limited, may be slower during peak times

### **Meta Llama 3.2 3B Instruct**
```env
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
```
- **Cost:** FREE
- **Quality:** Good for simple tasks
- **Speed:** Very fast
- **Best for:** Quick iterations, simple test generation

### **Google Gemma 2 9B IT**
```env
OPENROUTER_MODEL=google/gemma-2-9b-it:free
```
- **Cost:** FREE
- **Quality:** Good, Google's open model
- **Speed:** Fast
- **Best for:** Alternative to Llama

### **Mistral 7B Instruct**
```env
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```
- **Cost:** FREE
- **Quality:** Good for code and structured output
- **Speed:** Fast
- **Best for:** Code generation, technical tasks

### **Qwen 2 7B Instruct**
```env
OPENROUTER_MODEL=qwen/qwen-2-7b-instruct:free
```
- **Cost:** FREE
- **Quality:** Good, Alibaba's model
- **Speed:** Fast
- **Best for:** Multilingual tasks

---

## 💰 **Paid Premium Models (Better Quality)**

### **Anthropic Claude 3.5 Sonnet** ⭐ **BEST FOR PRODUCTION**
```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```
- **Cost:** ~$3 per million input tokens, ~$15 per million output tokens
- **Quality:** Excellent for structured output
- **Speed:** Fast
- **Best for:** Production test generation, complex tasks
- **Availability:** Works globally (no region restrictions)
- **Why choose:** Best at following instructions, great for JSON output

### **OpenAI GPT-4 Turbo**
```env
OPENROUTER_MODEL=openai/gpt-4-turbo
```
- **Cost:** ~$10 per million input tokens, ~$30 per million output tokens
- **Quality:** Excellent overall
- **Speed:** Moderate
- **Best for:** Complex reasoning, high-quality output
- **Availability:** ⚠️ May not work in all regions (403 errors)
- **Why choose:** Best overall model (if available in your region)

### **OpenAI GPT-3.5 Turbo**
```env
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```
- **Cost:** ~$0.50 per million input tokens, ~$1.50 per million output tokens
- **Quality:** Good, fast
- **Speed:** Very fast
- **Best for:** Quick tasks, cost-sensitive production
- **Availability:** ⚠️ May not work in all regions

### **Anthropic Claude 3 Haiku**
```env
OPENROUTER_MODEL=anthropic/claude-3-haiku
```
- **Cost:** ~$0.25 per million input tokens, ~$1.25 per million output tokens
- **Quality:** Good, fast
- **Speed:** Very fast
- **Best for:** High-volume, cost-sensitive production
- **Availability:** Works globally

### **Google Gemini Pro**
```env
OPENROUTER_MODEL=google/gemini-pro
```
- **Cost:** ~$0.50 per million input tokens, ~$1.50 per million output tokens
- **Quality:** Good
- **Speed:** Fast
- **Best for:** Alternative to GPT-3.5

---

## 📊 **Cost Comparison**

| Model | Cost per 1M tokens (in/out) | 1000 tests* | Quality |
|-------|------------------------------|-------------|---------|
| Llama 3.1 8B (free) | $0 / $0 | **$0** | ⭐⭐⭐ |
| Claude 3 Haiku | $0.25 / $1.25 | ~$0.75 | ⭐⭐⭐⭐ |
| GPT-3.5 Turbo | $0.50 / $1.50 | ~$1.00 | ⭐⭐⭐⭐ |
| Claude 3.5 Sonnet | $3 / $15 | ~$9.00 | ⭐⭐⭐⭐⭐ |
| GPT-4 Turbo | $10 / $30 | ~$20.00 | ⭐⭐⭐⭐⭐ |

*Estimated cost for generating 1000 test cases (assuming ~500 input + ~500 output tokens per test)

---

## 🎯 **Recommendation by Use Case**

### **Development & Learning**
```env
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```
- ✅ FREE
- ✅ Good enough for testing
- ✅ No cost concerns

### **Production (Budget-Conscious)**
```env
OPENROUTER_MODEL=anthropic/claude-3-haiku
```
- ✅ Cheap (~$0.75 per 1000 tests)
- ✅ Fast
- ✅ Good quality
- ✅ Works globally

### **Production (Best Quality)**
```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```
- ✅ Excellent quality
- ✅ Best for structured output
- ✅ Works globally
- ⚠️ More expensive (~$9 per 1000 tests)

### **High-Volume Production**
```env
OPENROUTER_MODEL=anthropic/claude-3-haiku
```
- ✅ Fast
- ✅ Cheap
- ✅ Scales well
- ✅ Good enough for most tasks

---

## 🌍 **Regional Availability**

### **Works Everywhere:**
- ✅ All free open-source models (Llama, Mistral, Gemma, Qwen)
- ✅ Anthropic Claude models (Sonnet, Haiku)
- ✅ Google Gemini models

### **May Have Region Restrictions:**
- ⚠️ OpenAI models (GPT-4, GPT-3.5)
- **Error:** `unsupported_country_region_territory`
- **Solution:** Use Claude or free models instead

---

## 🔧 **How to Change Models**

### **Option 1: Edit `.env` file**
```bash
cd backend
nano .env  # or use any text editor
```

Change the line:
```env
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

To your preferred model, then restart the server.

### **Option 2: Override in Code**
```python
from app.services.openrouter import OpenRouterService

service = OpenRouterService()

# Use a specific model for this call
response = await service.chat_completion(
    messages=messages,
    model="anthropic/claude-3.5-sonnet"  # Override default
)
```

---

## 🧪 **Testing Different Models**

Run the test script to verify your model works:

```powershell
cd backend
.\venv\Scripts\python.exe test_openrouter.py
```

Expected output:
```
Model configured: meta-llama/llama-3.1-8b-instruct:free
[Test 1] Testing basic connection... ✅ SUCCESS
[Test 2] Testing chat completion... ✅ SUCCESS  
[Test 3] Testing test case generation... ✅ SUCCESS
```

---

## 📈 **Performance Comparison**

Based on our testing:

| Model | Speed | Quality | Cost | Availability |
|-------|-------|---------|------|--------------|
| Llama 3.1 8B (free) | ⚡⚡⚡ | ⭐⭐⭐ | 💰 FREE | 🌍 Global |
| Mistral 7B (free) | ⚡⚡⚡ | ⭐⭐⭐ | 💰 FREE | 🌍 Global |
| Claude 3 Haiku | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 💰💰 Cheap | 🌍 Global |
| GPT-3.5 Turbo | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 💰💰 Cheap | ⚠️ Limited |
| Claude 3.5 Sonnet | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 Medium | 🌍 Global |
| GPT-4 Turbo | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰💰 Expensive | ⚠️ Limited |

---

## 🎓 **Best Practices**

1. **Start with FREE models** for development
2. **Test with your actual prompts** before committing to a paid model
3. **Monitor costs** in OpenRouter dashboard
4. **Use cheaper models for simple tasks** (e.g., Haiku for basic test generation)
5. **Use premium models for complex tasks** (e.g., Sonnet for advanced test scenarios)
6. **Set max_tokens limits** to control costs
7. **Cache common responses** to reduce API calls

---

## 🔗 **Useful Links**

- **OpenRouter Models:** https://openrouter.ai/models
- **OpenRouter Pricing:** https://openrouter.ai/models (see individual model pages)
- **OpenRouter Dashboard:** https://openrouter.ai/activity
- **Get API Key:** https://openrouter.ai/keys

---

## ❓ **FAQ**

### **Q: Which model should I use for development?**
A: Use `meta-llama/llama-3.1-8b-instruct:free` - it's free and good enough for testing.

### **Q: Which model should I use for production?**
A: For best quality: `anthropic/claude-3.5-sonnet`  
For best cost: `anthropic/claude-3-haiku`

### **Q: Why am I getting 403 errors with GPT-4?**
A: OpenAI models don't work in all regions. Use Claude or free models instead.

### **Q: How much will this cost?**
A: With free models: $0  
With Haiku: ~$0.75 per 1000 tests  
With Sonnet: ~$9 per 1000 tests

### **Q: Can I use multiple models?**
A: Yes! Set a default in `.env` and override per-request in code.

### **Q: Are free models rate limited?**
A: Yes, but limits are generous for development. Upgrade to paid if you hit limits.

---

**Current Default:** `meta-llama/llama-3.1-8b-instruct:free` (FREE, works globally)

**Recommended for Production:** `anthropic/claude-3.5-sonnet` (Best quality) or `anthropic/claude-3-haiku` (Best value)

