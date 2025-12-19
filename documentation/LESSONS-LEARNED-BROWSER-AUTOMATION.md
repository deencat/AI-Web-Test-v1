# Lessons Learned: Browser Automation with Stagehand + Playwright

**Date**: December 3, 2025  
**Context**: Three.com.hk 5G Broadband Subscription Flow - Login Modal Automation  
**Result**: Improved from 16/25 (64%) to 22/25 (88%) step success rate

---

## 🎯 Executive Summary

When automating complex web applications with dynamic modals/overlays, **direct Playwright selectors with multiple fallback strategies** proved more reliable than pure AI-driven automation. The key breakthrough was understanding modal container diversity and implementing a comprehensive selector cascade.

---

## 📊 Problem Statement

### Initial Challenges
1. **AI Method Selection Failures**: Stagehand's `page.act()` was choosing "not-supported" methods
2. **Login Modal Not Responding**: Email/password fields not being found despite being visible
3. **Selector Specificity Issues**: Generic selectors couldn't target elements within modals
4. **Inconsistent Results**: Same test would pass/fail randomly depending on AI interpretation

### Impact
- Login flow (Steps 16-23) completely failing
- Test execution blocking at authentication
- ~36% failure rate (9/25 steps failing)

---

## 💡 Solution: Hybrid Approach with Selector Cascading

### Architecture Decision

**Abandoned**: Pure AI approach (`page.act()`)  
**Adopted**: Direct Playwright selectors with intelligent fallbacks

### Implementation Strategy

```python
# Core Pattern: Modal Context Detection + Selector Multiplication
if in_modal:
    for modal_container in modal_prefixes:
        for base_selector in base_selectors:
            try: f"{modal_container} {base_selector}"
```

---

## 🔑 Key Technical Insights

### 1. **Modal Container Diversity**

**Learning**: Different websites use different modal frameworks/patterns. Don't assume a single selector pattern.

**Implementation**:
```python
modal_prefixes = [
    ".modal-content",    # Bootstrap modal content area
    ".modal-body",       # Bootstrap modal body
    ".modal",            # Generic modal wrapper
    "[role='dialog']",   # ARIA accessibility standard
    ".offcanvas-body",   # Bootstrap offcanvas body
    ".offcanvas.show",   # Visible offcanvas state
]
```

**Why It Works**:
- Different sites use different frameworks (Bootstrap, custom, etc.)
- Trying 6 variations = 6x higher chance of matching actual DOM structure
- Three.com.hk used `.modal-content` or `.modal-body` (not `.offcanvas.show` as initially assumed)

### 2. **Input Field Attribute Variations**

**Learning**: Email/password fields may not always use obvious type attributes.

**Before** (Limited):
```python
email_selectors = [
    "input[type='email']",
    "input[name*='email' i]",
]
```

**After** (Comprehensive):
```python
email_selectors = [
    "input[type='email']",           # Standard email input
    "input[name*='email' i]",        # Name contains "email"
    "input[placeholder*='email' i]", # Placeholder hints
    "input[id*='email' i]",          # ID contains "email"
    "input[autocomplete='email']",   # Autocomplete attribute
    "input[type='text']",            # Email as text field (!)
]
```

**Critical Discovery**: Some sites use `type="text"` for email fields for styling/validation reasons.

### 3. **Selector Cascade Priority**

**Learning**: Order matters. Try most specific selectors first, fall back to generic.

**Strategy**:
```python
selectors = []
# 1. Modal-scoped + specific (highest priority)
for prefix in modal_prefixes:
    selectors.extend([f"{prefix} {s}" for s in base_selectors])

# 2. Global selectors (fallback)
selectors.extend(base_selectors)
```

**Why This Order**:
- Modal-scoped prevents accidentally selecting hidden/duplicate elements
- Generic fallback handles non-modal contexts
- First match wins = faster execution

### 4. **Action Type Detection**

**Learning**: Parse step descriptions to choose appropriate handlers.

**Implementation**:
```python
if any(word in desc_lower for word in ['type', 'enter', 'fill', 'input']):
    return await self._execute_type_simple(step_description)
elif any(word in desc_lower for word in ['click', 'select', 'choose', 'press']):
    return await self._execute_click_simple(step_description)
```

**Benefits**:
- No AI needed for action classification
- Predictable, debuggable routing
- Can optimize selectors per action type

### 5. **Special Case Handling**

**Learning**: Common UI patterns deserve dedicated handlers.

**Implemented**:
- **Checkboxes**: `input[type='checkbox']:visible`
- **Close Buttons**: `button[aria-label*='close' i]`, `button:has-text('×')`
- **Modal Context Detection**: Keywords like 'login', 'email', 'password' trigger modal selectors

---

## 📈 Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Success Rate** | 64% (16/25) | 88% (22/25) | +24% |
| **Login Flow** | 0% (0/8 steps) | 100% (8/8 steps) | +100% |
| **Avg Step Duration** | ~12s (with retries) | ~1.5s (direct match) | 8x faster |
| **AI Dependencies** | 100% | 12% (verification only) | 88% reduction |

---

## 🏗️ Architectural Patterns for Future Development

### Pattern 1: Context-Aware Selector Builder

```python
def build_selectors(element_type, context_hints):
    """
    Build comprehensive selector list based on:
    - Element type (input, button, link, etc.)
    - Context (modal, page, iframe, etc.)
    - Semantic hints (email, password, submit, etc.)
    """
    base = get_base_selectors(element_type, context_hints)
    containers = detect_containers(context_hints)
    return cascade_selectors(containers, base)
```

### Pattern 2: Graceful Degradation

```
1. Try modal-scoped + specific attributes
2. Try modal-scoped + generic attributes  
3. Try global + specific attributes
4. Try global + generic attributes
5. Fall back to AI (if available)
6. Report failure with diagnostic info
```

### Pattern 3: Smart Wait Strategies

```python
# Don't just wait for selector, wait for state
element = await page.wait_for_selector(
    selector, 
    timeout=3000,
    state='visible'  # Ensure element is actually visible
)
```

---

## 🚨 Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: AI-First for Simple Actions
**Don't**: `await page.act("click the login button")`  
**Do**: `await page.click("button:has-text('Login')")`  
**Reason**: AI adds latency, unpredictability, and API costs

### ❌ Anti-Pattern 2: Single Selector Assumption
**Don't**: Only try `.modal-content input[type='email']`  
**Do**: Try 6 modal containers × 6 input patterns = 36 attempts  
**Reason**: Websites vary; robustness requires flexibility

### ❌ Anti-Pattern 3: Ignoring Element State
**Don't**: `await page.click(selector)`  
**Do**: `await page.click(selector, state='visible')`  
**Reason**: Elements may exist in DOM but be hidden

### ❌ Anti-Pattern 4: Hardcoded Container Classes
**Don't**: Assume all modals use `.modal-content`  
**Do**: Try common patterns from major frameworks  
**Reason**: Sites use different UI frameworks

---

## 🔧 Recommended Backend Development Practices

### 1. **Selector Library Approach**
Create reusable selector generators:

```python
# backend/app/utils/selectors.py
class SelectorBuilder:
    MODAL_CONTAINERS = [...]
    INPUT_PATTERNS = {
        'email': [...],
        'password': [...],
        'text': [...]
    }
    
    @staticmethod
    def for_input(field_type, in_modal=False):
        """Generate comprehensive input selectors"""
        pass
```

### 2. **Logging & Diagnostics**
Log every selector attempt:

```python
for selector in selectors:
    logger.debug(f"Trying: {selector}")
    try:
        element = await page.wait_for_selector(selector, timeout=3000)
        logger.info(f"✅ Match: {selector}")
        return element
    except TimeoutError:
        logger.debug(f"❌ Timeout: {selector}")
```

**Benefit**: When tests fail, logs show exactly which selectors were tried.

### 3. **Configuration Over Code**
Store selector patterns in config:

```yaml
# config/selectors.yml
modal_containers:
  - .modal-content
  - .modal-body
  - "[role='dialog']"

input_fields:
  email:
    - "input[type='email']"
    - "input[autocomplete='email']"
```

**Benefit**: Update selectors without code changes.

### 4. **Test Data Extraction**
Use regex to parse test step descriptions:

```python
# Extract quoted text for button labels/input values
quoted_match = re.search(r"['\"]([^'\"]+)['\"]", step_description)

# Extract action type
if re.search(r'\b(click|press|select)\b', desc_lower):
    action = 'click'
```

### 5. **Fallback Chains**
Always have multiple strategies:

```
Primary: Direct selector (fastest)
↓
Secondary: Modal-scoped selector (more specific)
↓
Tertiary: AI interpretation (most flexible)
↓
Failure: Detailed error with screenshots
```

---

## 📝 Decision Log

### Decision 1: Use Playwright Over Pure AI
**Date**: Dec 3, 2025  
**Rationale**: AI `page.act()` was unreliable, choosing "not-supported" methods  
**Impact**: Reduced step execution time from 12s to 1.5s average  
**Trade-off**: Less flexible for complex instructions, but more predictable

### Decision 2: Multiple Modal Container Patterns
**Date**: Dec 3, 2025  
**Rationale**: `.offcanvas.show` didn't match Three.com.hk's modal structure  
**Impact**: Login flow went from 0% to 100% success rate  
**Trade-off**: More selector attempts = slightly longer initial execution

### Decision 3: Extract Text from Quotes
**Date**: Dec 3, 2025  
**Rationale**: Needed to parse button text from natural language descriptions  
**Impact**: Enabled automated extraction of "Login", "Subscribe Now", etc.  
**Trade-off**: Requires consistent quote usage in test step descriptions

---

## 🎓 Training Recommendations

### For QA Engineers Writing Test Cases
1. **Always use quotes** around button text: `Click 'Login'` not `Click Login`
2. **Be specific about fields**: `email input field` not just `input field`
3. **Mention context**: `Click 'Next' button in the modal` not just `Click Next`

### For Developers Implementing Automation
1. **Start with simple Playwright selectors** before considering AI
2. **Build selector arrays** with fallbacks, don't rely on single selectors
3. **Log extensively** - future debugging depends on it
4. **Test against multiple sites** to validate selector diversity

---

## 🔮 Future Enhancements

### Short-term (Next Sprint)
1. **Fix remaining 3 failing steps**:
   - Step 6: Checkbox with text "Don't" (quote parsing issue)
   - Step 10: "Next" button (may need scroll or different selector)
   - Step 24: Date picker (needs custom handler)

2. **Add selector caching**: Store successful selectors for reuse

3. **Implement retry logic**: Auto-retry failed steps with different strategies

### Medium-term (Next Month)
1. **Build selector library**: Reusable patterns for common elements
2. **Add visual regression**: Screenshot comparison for verification steps
3. **Create selector debugger**: Tool to test selector patterns interactively

### Long-term (Next Quarter)
1. **Self-healing selectors**: Learn from failures, adapt patterns
2. **Cross-browser validation**: Test selectors in Chrome, Firefox, Safari
3. **Performance benchmarking**: Track selector performance over time

---

## 📚 References

### Related Documentation
- `BACKEND-DAY-4-5-COMPLETION-REPORT.md` - Earlier automation work
- `SPRINT-2-DAY-7-8-EXECUTION-TRACKING-COMPLETE.md` - Test execution tracking
- `test_three_5g_broadband.py` - Current test implementation

### External Resources
- [Playwright Selectors Best Practices](https://playwright.dev/docs/selectors)
- [Bootstrap Modal Structure](https://getbootstrap.com/docs/5.0/components/modal/)
- [ARIA Dialog Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

---

## ✅ Success Criteria Met

- [x] Login flow fully automated (8/8 steps passing)
- [x] Email and password input working reliably
- [x] Modal element targeting solved
- [x] Execution time reduced by 8x for successful steps
- [x] Knowledge documented for future development

---

## 🤝 Contributors & Acknowledgments

**Problem Identified By**: User observation - "didn't even fill in the email address"  
**Root Cause Analysis**: Selector mismatch between `.offcanvas.show` and actual `.modal-content`  
**Solution Implemented**: Multi-prefix selector cascade approach  
**Validation**: 22/25 steps passing, login flow 100% successful

---

**Document Owner**: Backend Development Team  
**Last Updated**: December 3, 2025  
**Status**: Active - Reference for ongoing automation development
