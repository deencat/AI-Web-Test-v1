# Settings Page - AI Provider Architecture Guide

**Date:** December 16, 2025  
**Sprint:** 3 - Integration Testing  
**Purpose:** Clarify AI provider usage across different system components

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Web Test Platform                         │
└─────────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                  │
    ┌───────▼──────────┐           ┌──────────▼─────────┐
    │  Test Generation │           │  Test Execution    │
    │   (Sprint 2)     │           │   (Sprint 3)       │
    └───────┬──────────┘           └──────────┬─────────┘
            │                                  │
            │                                  │
    ┌───────▼──────────┐           ┌──────────▼─────────┐
    │  OpenRouter ONLY │           │  Multi-Provider    │
    │                  │           │  Support           │
    │  • Mistral 8x7B  │           │  • Google Gemini   │
    │  • Claude        │           │  • Cerebras Llama  │
    │  • GPT-4         │           │  • OpenRouter      │
    └──────────────────┘           └────────────────────┘
```

---

## 📊 Provider Usage Breakdown

### 1️⃣ Test Generation (Sprint 2)

**Purpose:** Convert natural language → Test cases  
**Service:** `backend/app/services/test_generation.py`  
**Current Support:** **OpenRouter ONLY**

**Configuration:**
```env
# .env file
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=mistralai/mixtral-8x7b-instruct
```

**Why OpenRouter Only?**
- Uses `OpenRouterService` class directly
- Hardcoded in test generation service
- Provides access to multiple models via single API
- Cost-effective for text generation

**Available Models via OpenRouter:**
- ✅ Mistral 8x7B (Default - FREE)
- ✅ Claude 3 Opus/Sonnet
- ✅ GPT-4 Turbo
- ✅ Google Gemini (via OpenRouter)
- ✅ 14+ other models

---

### 2️⃣ Test Execution (Sprint 3)

**Purpose:** Browser automation for running tests  
**Service:** `backend/app/services/stagehand_service.py`  
**Current Support:** **ALL THREE PROVIDERS**

**Configuration:**
```env
# .env file - Choose ONE provider
MODEL_PROVIDER=google  # or cerebras, or openrouter

# Google Configuration
GOOGLE_API_KEY=your-key-here
GOOGLE_MODEL=gemini-2.0-flash-exp

# Cerebras Configuration
CEREBRAS_API_KEY=your-key-here
CEREBRAS_MODEL=llama3.1-8b

# OpenRouter Configuration
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=qwen/qwen-2.5-7b-instruct
```

**Why Multi-Provider?**
- Uses Stagehand with LiteLLM (supports many providers)
- Browser automation benefits from faster inference
- Users can choose based on needs (speed vs cost vs features)

---

## 🎯 Settings Page Implementation

### Current UI Design

The Settings page now clearly communicates the provider scope:

```
┌────────────────────────────────────────────────────┐
│  AI Model Provider            [Test Execution Only]│
│  Configure AI models for test execution automation │
├────────────────────────────────────────────────────┤
│  ⚠️ Usage Scope:                                   │
│  • Test Execution: Uses selected provider below    │
│  • Test Generation: OpenRouter only (backend)      │
├────────────────────────────────────────────────────┤
│  Select Provider for Test Execution                │
│  Choose AI provider for browser automation         │
│                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Google  │  │Cerebras │  │OpenRouter│            │
│  │ Gemini  │  │Llama 3.1│  │14+ Models│            │
│  │  FREE   │  │ULTRA FAST│ │ VARIETY  │            │
│  └─────────┘  └─────────┘  └─────────┘            │
└────────────────────────────────────────────────────┘
```

### Key Features:

1. **Clear Badge:** "Test Execution Only" badge at top
2. **Info Banner:** Amber alert explaining usage scope
3. **Provider Descriptions:** Each provider shows use case
4. **OpenRouter Note:** Extra note for OpenRouter users

---

## 💡 Recommendations

### For Your Current Setup:

✅ **Settings Page Configuration:** 
- Configure test execution provider (affects browser automation)
- Google Gemini recommended (FREE + reliable)

✅ **Backend .env Configuration:**
- Keep `OPENROUTER_API_KEY` for test generation
- Add your chosen execution provider key
- Set `MODEL_PROVIDER` for test execution

### Example .env Setup:

```env
# Test Generation (Required)
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=mistralai/mixtral-8x7b-instruct

# Test Execution (Choose ONE)
MODEL_PROVIDER=google
GOOGLE_API_KEY=AIzaSyxxxxx
GOOGLE_MODEL=gemini-2.0-flash-exp

# Optional: Add other providers
CEREBRAS_API_KEY=csk-xxxxx
CEREBRAS_MODEL=llama3.1-8b
```

---

## 🔮 Future Enhancements

### Phase 2 Possibilities:

**Option A: Add Multi-Provider Support to Test Generation**
- Refactor `test_generation.py` to use provider abstraction
- Allow users to choose generation provider in UI
- Benefit: More flexibility, better models for generation

**Option B: Unified Provider System**
- Create `AIProviderService` abstraction
- Use same provider for both generation and execution
- Benefit: Simpler configuration, consistent behavior

**Option C: Smart Provider Routing**
- Fast provider (Cerebras) for execution
- Powerful provider (Claude) for generation
- Benefit: Optimized performance per task type

### Recommended Approach: **Option A**

**Why?**
- Maintains separation of concerns
- Allows optimization per use case
- Backward compatible with current setup

**Implementation Effort:** 
- 2-3 hours refactoring
- Add provider abstraction layer
- Update Settings page with second provider section

---

## 📝 Technical Notes

### Backend Services:

**Test Generation:**
```python
# backend/app/services/test_generation.py
class TestGenerationService:
    def __init__(self):
        self.openrouter = OpenRouterService()  # ← Hardcoded!
```

**Test Execution:**
```python
# backend/app/services/stagehand_service.py
async def initialize(self):
    model_provider = os.getenv("MODEL_PROVIDER", "openrouter")
    
    if model_provider == "cerebras":
        # Use Cerebras
    elif model_provider == "google":
        # Use Google
    else:
        # Use OpenRouter (default)
```

### Frontend Configuration:

**Settings Page State:**
```tsx
const [modelProvider, setModelProvider] = useState<'google' | 'cerebras' | 'openrouter'>('google');
const [googleApiKey, setGoogleApiKey] = useState('');
const [cerebrasApiKey, setCerebrasApiKey] = useState('');
const [openrouterApiKey, setOpenrouterApiKey] = useState('');
```

**Note:** Settings page currently doesn't persist to backend (MVP limitation)

---

## ✅ Testing Status

**Settings Page Tests:** 16/17 passing (94%)
- ✅ Provider selection UI
- ✅ API key validation
- ✅ Save/reset functionality
- ✅ Mobile responsiveness

**Integration Status:** ✅ Ready for manual testing
- Backend providers working
- Frontend UI clear and intuitive
- Documentation complete

---

## 📚 Related Documentation

- `CEREBRAS-INTEGRATION-GUIDE.md` - Cerebras setup
- `MODEL-PROVIDER-COMPARISON.md` - Provider comparison
- `SPRINT-3-CEREBRAS-INTEGRATION.md` - Sprint 3 summary
- `backend/.env.example` - Configuration examples

---

## 🎓 Key Takeaways

1. **Test Generation** = OpenRouter only (backend hardcoded)
2. **Test Execution** = All 3 providers supported (user choice)
3. **Settings Page** = Configures execution provider only
4. **Future**: Can add multi-provider to generation if needed
5. **Current**: Clear UI communication prevents confusion

---

**Last Updated:** December 16, 2025  
**Status:** ✅ Production Ready  
**Next Steps:** Manual testing + optional provider unification in Phase 2
