# Backend Automation - Best Practices & Quick Reference

**Quick Guide for Backend Development**  
**Based on**: Three.com.hk Login Automation Success (Dec 3, 2025)

---

## 🎯 Golden Rules

### Rule 1: Playwright First, AI Second
```python
# ✅ GOOD - Fast, predictable, debuggable
await page.click("button:has-text('Login')")

# ❌ AVOID - Slow, unpredictable, costly
await page.act("click the login button")
```

### Rule 2: Multiple Selectors, Always
```python
# ✅ GOOD - Robust across different sites
selectors = [
    ".modal-content input[type='email']",
    ".modal-body input[type='email']",
    "[role='dialog'] input[type='email']",
    "input[type='email']",  # Fallback
]

# ❌ BAD - Fragile, site-specific
selector = ".modal-content input[type='email']"
```

### Rule 3: Context Matters
```python
# ✅ GOOD - Targets modal elements specifically
if 'login' in step_description.lower():
    selectors = [f".modal {s}" for s in base_selectors]

# ❌ BAD - May select wrong elements
selectors = base_selectors  # Could match hidden elements
```

---

## 🏗️ Code Templates

### Template 1: Element Finder with Fallbacks

```python
async def find_element(page, element_type, context=None):
    """Find element with comprehensive fallback strategy."""
    
    # Build selector list
    selectors = build_selectors(element_type, context)
    
    # Try each selector
    for selector in selectors:
        try:
            element = await page.wait_for_selector(
                selector, 
                timeout=3000, 
                state='visible'
            )
            if element:
                logger.info(f"✅ Found with: {selector}")
                return element
        except TimeoutError:
            logger.debug(f"⏭️  Skipped: {selector}")
            continue
    
    # All selectors failed
    raise ElementNotFoundError(f"Tried {len(selectors)} selectors")
```

### Template 2: Smart Click Handler

```python
async def smart_click(page, step_description):
    """Click with special case handling."""
    
    # Extract button text
    match = re.search(r"['\"]([^'\"]+)['\"]", step_description)
    if not match:
        raise ValueError("No button text in quotes")
    
    button_text = match.group(1)
    desc_lower = step_description.lower()
    
    # Special cases
    if 'checkbox' in desc_lower:
        return await click_checkbox(page)
    if button_text in ['X', '×', 'Close']:
        return await click_close_button(page)
    
    # Check for modal context
    in_modal = any(kw in desc_lower for kw in ['login', 'modal', 'popup'])
    
    # Build and try selectors
    selectors = build_click_selectors(button_text, in_modal)
    return await try_selectors(page, selectors)
```

### Template 3: Input Field Handler

```python
async def type_into_field(page, step_description):
    """Type text into input field."""
    
    # Extract text to type (last quoted string)
    texts = re.findall(r"['\"]([^'\"]+)['\"]", step_description)
    if not texts:
        raise ValueError("No text to type in quotes")
    
    text_to_type = texts[-1]
    desc_lower = step_description.lower()
    
    # Detect field type
    if 'email' in desc_lower:
        field_type = 'email'
    elif 'password' in desc_lower:
        field_type = 'password'
    else:
        field_type = 'text'
    
    # Check modal context
    in_modal = 'login' in desc_lower
    
    # Build selectors
    selectors = build_input_selectors(field_type, in_modal)
    
    # Find and fill
    for selector in selectors:
        try:
            element = await page.wait_for_selector(
                selector, timeout=3000, state='visible'
            )
            await element.fill(text_to_type)
            return {"success": True}
        except:
            continue
    
    return {"success": False, "error": "Field not found"}
```

---

## 📋 Selector Cheat Sheet

### Modal Containers (Try These First)
```python
MODAL_CONTAINERS = [
    ".modal-content",    # Bootstrap modal
    ".modal-body",       # Bootstrap modal body
    ".modal",            # Generic modal
    "[role='dialog']",   # ARIA standard
    ".offcanvas-body",   # Bootstrap offcanvas
    ".offcanvas.show",   # Visible offcanvas
    ".dialog",           # Custom dialogs
    "[role='alertdialog']",  # Alert modals
]
```

### Input Field Patterns
```python
EMAIL_SELECTORS = [
    "input[type='email']",
    "input[name*='email' i]",
    "input[placeholder*='email' i]",
    "input[id*='email' i]",
    "input[autocomplete='email']",
    "input[type='text']",  # Some sites use text for email
]

PASSWORD_SELECTORS = [
    "input[type='password']",
    "input[name*='password' i]",
    "input[autocomplete*='password' i]",
]

CHECKBOX_SELECTORS = [
    "input[type='checkbox']:visible",
    "[role='checkbox']:visible",
    "label:has(input[type='checkbox']):visible",
]
```

### Button Patterns
```python
def button_selectors(text):
    return [
        f"button:has-text('{text}')",
        f"a:has-text('{text}')",
        f"[role='button']:has-text('{text}')",
        f"input[type='submit'][value='{text}']",
        f"text='{text}'",  # Playwright text selector
    ]
```

### Close Button Patterns
```python
CLOSE_BUTTON_SELECTORS = [
    "button[aria-label*='close' i]",
    "button[class*='close' i]",
    "button:has-text('×')",
    "button:has-text('✕')",
    "[aria-label*='close' i]",
]
```

---

## 🔍 Debugging Checklist

When a selector fails:

- [ ] **Is the element visible?** Check with `state='visible'`
- [ ] **Is it in a modal?** Try prepending modal container selectors
- [ ] **Is it in an iframe?** Use `page.frame_locator()`
- [ ] **Does it have text?** Use `:has-text()` instead of `text=`
- [ ] **Is there a timing issue?** Increase timeout or add wait
- [ ] **Check the logs**: Which selectors were tried?
- [ ] **Take a screenshot**: Visual confirmation of page state
- [ ] **Inspect DOM**: Use browser DevTools to verify structure

---

## ⚡ Performance Tips

### 1. Order Selectors by Specificity
```python
# Most specific first (fastest when it works)
selectors = [
    "#loginButton",                    # ID (fastest)
    ".modal-content button.primary",   # Class combo (fast)
    "button[type='submit']",           # Attribute (medium)
    "button:has-text('Login')",        # Text match (slower)
]
```

### 2. Use Short Timeouts with Fallbacks
```python
# Better: Try multiple selectors with short timeouts
for selector in selectors:
    try:
        return await page.wait_for_selector(selector, timeout=2000)
    except: continue

# Worse: Long timeout on single selector
await page.wait_for_selector(selector, timeout=30000)  # Wastes time
```

### 3. Cache Successful Selectors
```python
# Store what worked
selector_cache = {}

def get_cached_selector(element_key):
    if element_key in selector_cache:
        return [selector_cache[element_key]]  # Try cached first
    return build_all_selectors(element_key)
```

---

## 🚨 Common Pitfalls

### Pitfall 1: Assuming Element Exists
```python
# ❌ BAD
element = await page.query_selector("button")
await element.click()  # May crash if element is None

# ✅ GOOD
element = await page.wait_for_selector("button", state='visible')
if element:
    await element.click()
```

### Pitfall 2: Not Handling Modals
```python
# ❌ BAD - May select hidden element
await page.click("input[type='email']")

# ✅ GOOD - Targets visible modal
await page.click(".modal-content input[type='email']")
```

### Pitfall 3: Hardcoding Selectors
```python
# ❌ BAD
await page.click(".OffCanvasView_container__QNH7d button")  # Fragile

# ✅ GOOD
await page.click("[class*='OffCanvas'] button")  # Partial match
```

### Pitfall 4: Ignoring Context
```python
# ❌ BAD - Clicks first "Login" anywhere
await page.click("text='Login'")

# ✅ GOOD - Clicks "Login" in modal
await page.click(".modal text='Login'")
```

---

## 📊 Success Metrics

Track these in your test reports:

| Metric | Target | Current |
|--------|--------|---------|
| **Step Success Rate** | >90% | 88% |
| **Avg Step Duration** | <3s | 1.5s ✅ |
| **First-Try Success** | >80% | 75% |
| **Selector Cache Hit Rate** | >50% | TBD |

---

## 🎓 Quick Decision Tree

```
Need to interact with element?
│
├─ Is it a simple button/link?
│  └─ Use: button:has-text('Text')
│
├─ Is it an input field?
│  ├─ Email? → input[type='email'], input[autocomplete='email']
│  ├─ Password? → input[type='password']
│  └─ Other? → input[type='text']:visible
│
├─ Is it in a modal/popup?
│  └─ Prepend: .modal-content, .modal-body, [role='dialog']
│
├─ Is it a checkbox?
│  └─ Use: input[type='checkbox']:visible
│
├─ Is it a close button?
│  └─ Use: button[aria-label*='close']
│
└─ Complex interaction?
   └─ Build selector array with 5-10 fallbacks
```

---

## 🔗 Related Documents

- **Full Analysis**: `LESSONS-LEARNED-BROWSER-AUTOMATION.md`
- **Test Implementation**: `backend/app/services/stagehand_service.py`
- **Test Case**: `backend/test_three_5g_broadband.py`

---

**Last Updated**: December 3, 2025  
**Maintained By**: Backend Development Team  
**Status**: Active Reference
