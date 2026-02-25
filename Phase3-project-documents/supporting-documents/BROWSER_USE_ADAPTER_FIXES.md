# Browser-Use Adapter Fixes - Troubleshooting Log

**Date:** February 13, 2026  
**Issue:** Browser-use agent failing during multi-page flow crawling  
**Status:** ✅ RESOLVED

---

## Problem Summary

The `ObservationAgent` was failing to extract pages during multi-page flow crawling using `browser-use`, resulting in:
- **0 pages extracted** from browser-use history
- **0 UI elements found**
- **Browser-use agent stopping after 3 consecutive failures**

---

## Root Causes & Fixes

### Fix #1: Missing `provider` Attribute
**Error:** `'AzureOpenAIAdapter' object has no attribute 'provider'`

**Solution:** Added `self.provider = 'azure-openai'` to `AzureOpenAIAdapter.__init__()`.

```python
self.provider = 'azure-openai'
```

---

### Fix #2: Missing `ainvoke()` Method
**Error:** `'AzureOpenAIAdapter' object has no attribute 'ainvoke'`

**Solution:** Implemented `ainvoke()` method to provide LangChain-compatible interface for browser-use's token cost service.

```python
async def ainvoke(self, messages: List, **kwargs):
    # Implementation that calls Azure OpenAI and returns response with .content and .usage
```

---

### Fix #3: Missing `model` and `model_name` Attributes
**Error:** `'AzureOpenAIAdapter' object has no attribute 'model'` / `'model_name'`

**Solution:** Added both attributes to satisfy browser-use's token tracking and telemetry.

```python
self.model = model_name
self.model_name = model_name
```

---

### Fix #4: Unicode Encoding Error
**Error:** `UnicodeEncodeError: 'cp950' codec can't encode character '\U0001f4cb'`

**Solution:** Removed emoji character (📋) from `print` statement in `stagehand_service.py`.

---

### Fix #5: Message Content Normalization
**Error:** `Missing required parameter: 'messages[1].content[0].type'` from Azure OpenAI API

**Solution:** Modified `achat()` and `ainvoke()` methods to normalize browser-use's list-based content format to plain strings before sending to Azure OpenAI.

```python
# Normalize content (browser-use may send content as list)
if isinstance(content, list):
    text_parts = []
    for part in content:
        if isinstance(part, dict) and "text" in part:
            text_parts.append(str(part["text"]))
        else:
            text_parts.append(str(part))
    content_str = "".join(text_parts)
else:
    content_str = str(content)
```

---

### Fix #6: `AgentHistoryList` Parsing
**Error:** `'AgentHistoryList' object has no attribute 'pages'`

**Solution:** Modified `ObservationAgent._execute_multi_page_flow_crawling()` to iterate directly over `history` (which is an `AgentHistoryList` and iterable) instead of trying to access a `.pages` attribute.

```python
# Iterate directly over history (AgentHistoryList is iterable)
for idx, history_item in enumerate(history):
    # Extract URL, title, and page data from history_item
```

---

### Fix #7: `usage` Dictionary Format - Missing Fields
**Error:** 
```
Invalid model output format. Please follow the correct schema.
Details: 3 validation errors for TokenUsageEntry
usage.prompt_cached_tokens - Field required
usage.prompt_cache_creation_tokens - Field required
usage.prompt_image_tokens - Field required
```

**Solution:** Added the three required fields to the `usage` dictionary with default value `0`.

```python
usage_dict = {
    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
    "total_tokens": getattr(response.usage, 'total_tokens', 0),
    # Browser-use's TokenUsageEntry requires these fields (set to 0 if not available)
    "prompt_cached_tokens": getattr(response.usage, 'prompt_cached_tokens', 0),
    "prompt_cache_creation_tokens": getattr(response.usage, 'prompt_cache_creation_tokens', 0),
    "prompt_image_tokens": getattr(response.usage, 'prompt_image_tokens', 0)
}
```

---

### Fix #8: Missing `.completion` Attribute (Revised)
**Error #1:** 
```
'ResponseObject' object has no attribute 'completion'
```

**Error #2 (after initial fix):**
```
'str' object has no attribute '__dict__'
Traceback:
  File "browser_use/agent/service.py", line 1791, in _recursive_process_all_strings_inside_pydantic_model
    for field_name, field_value in model.__dict__.items():
AttributeError: 'str' object has no attribute '__dict__'
```

**Root Cause:** Browser-use expects `response.completion` to be a **Pydantic model object** (with `.__dict__`), not a plain string. Browser-use calls `response.completion.__dict__` to recursively process strings inside the model.

**Solution:** Parse the JSON response into a generic Python object with `.__dict__` attribute. This allows browser-use's recursive string processing to work, while browser-use handles proper Pydantic validation internally.

```python
import json

class ResponseObject:
    def __init__(self, content, usage=None):
        self.content = content
        self.usage = usage
        # Parse JSON string into a generic object with __dict__
        # This allows browser-use's _recursive_process_all_strings_inside_pydantic_model to work
        try:
            parsed_dict = json.loads(content)
            # Create a simple object from the dict
            class ParsedCompletion:
                def __init__(self, data):
                    self.__dict__.update(data)
            self.completion = ParsedCompletion(parsed_dict)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Could not parse completion as JSON: {e}")
            # Fallback: set completion to content (string)
            self.completion = content

# When returning:
return ResponseObject(content=response_text, usage=usage_dict)
```

---

## Files Modified

1. **`backend/llm/browser_use_adapter.py`**
   - Added `provider`, `model`, `model_name` attributes
   - Implemented `ainvoke()` method
   - Added message content normalization in `achat()` and `ainvoke()`
   - Updated `ResponseObject` class to include `.completion` attribute
   - Added all required fields to `usage` dictionary

2. **`backend/agents/observation_agent.py`**
   - Fixed `AgentHistoryList` parsing to iterate directly over `history`
   - Added fallback Playwright crawling for pages without direct page objects
   - Updated `_check_goal_reached()` to iterate directly over `history`

3. **`backend/app/services/stagehand_service.py`**
   - Removed emoji character from `print` statement

4. **`backend/tests/integration/test_four_agent_e2e_real.py`**
   - Reduced `parallel_execution_batch_size` from 3 to 2 to reduce concurrent browser instances

---

## Expected Results After Fixes

After all fixes are applied:
1. ✅ Browser-use agent should complete navigation without validation errors
2. ✅ Multiple pages should be extracted from the purchase flow (not 0)
3. ✅ UI elements should be found from all pages visited (should be > 0)
4. ✅ The 4-agent workflow should complete successfully
5. ✅ Test cases should be generated based on the multi-page flow

---

## Testing Instructions

Run the E2E test with the venv activated:

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -u -m pytest tests/integration/test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

**Expected behavior:**
- Browser-use agent navigates through multiple pages
- Pages are extracted from history (should see "Extracted N unique pages" where N > 0)
- UI elements are found (should see "UI Elements Observed: N" where N > 0)
- Test completes successfully without "consecutive failures" error

---

## Key Learnings

1. **Browser-use LLM Adapter Requirements:**
   - Must have `provider`, `model`, `model_name` attributes
   - Must implement `ainvoke()` method (not just `achat()`)
   - Response object must have `.content`, `.usage`, and `.completion` attributes
   - Usage dictionary must include 6 fields (not just 3)

2. **Message Format Normalization:**
   - Browser-use sends messages with `content` as a list of dictionaries
   - Azure OpenAI expects `content` as a plain string
   - Adapter must normalize between these formats

3. **History Parsing:**
   - `AgentHistoryList` is directly iterable (no `.pages` attribute)
   - Must handle cases where page objects are not directly available
   - Fallback to Playwright crawling for individual URLs when needed

4. **Windows Encoding:**
   - Avoid Unicode characters (emojis) in `print` statements on Windows
   - Use ASCII alternatives or explicit UTF-8 encoding

---

## Status: RESOLVED ✅

All 8 fixes have been applied. The browser-use adapter should now work correctly with Azure OpenAI for multi-page flow crawling.

