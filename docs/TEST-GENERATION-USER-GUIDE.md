# 📘 Test Case Generation - User Guide

**Date:** January 9, 2026  
**Status:** ✅ Improved for Business Users

---

## 🎯 Overview

The test generation feature now supports **two input modes**:

1. **Simple Requirements** (Business-friendly) - NEW!
2. **Detailed Requirements** (Technical)

---

## ✨ Key Improvements

### 1. **Business-Friendly Input**
You can now write simple, high-level requirements like:

```
Purchase $154 plan with 48 months contract, login, select date, confirm
```

The system will automatically:
- ✅ Generate detailed, executable test steps
- ✅ Infer standard web flows (navigate, click, verify)
- ✅ Handle login modals/popups explicitly
- ✅ Add verification steps after major actions

### 2. **Consistency**
- Temperature lowered from **0.7 → 0.2**
- Same input = nearly identical output
- No more 5 different results from same requirement!

### 3. **Smart Detection**
System automatically detects if your requirement is:
- **Simple** (business language) → Uses enhanced prompting
- **Detailed** (step-by-step) → Uses standard processing

---

## 📝 How to Write Requirements

### ✅ **Option 1: Simple Requirements (RECOMMENDED for Business Users)**

**What to write:**
```
Test [action] on [website]:
- [Key action 1]
- [Key action 2]
- [Key action 3]

URL: [website URL]
Additional context: [any special notes]
```

**Example:**
```
Test Three HK broadband purchase:
- Purchase $154/month plan with 48 months contract
- Login with test credentials
- Select earliest activation date
- Confirm subscription

URL: https://web.three.com.hk/5gbroadband/plan-monthly.html
Note: Login uses modal dialog
```

**System generates:**
1. Navigate to https://web.three.com.hk/5gbroadband/plan-monthly.html
2. Wait for page to load completely
3. Locate plan card showing '$154/month' price
4. Verify plan details: 5G寬頻Wi-Fi 6
5. Click '48個月' button in contract period selector
6. Verify '48個月' button shows selected state
7. Click '立即上台' button within $154 plan card
8. Verify navigation to checkout page
9. In the login modal dialog, enter email
10. In the modal, enter password
11. Click '登入' button in modal
12. Verify modal closes
13. Select earliest available date from date picker
14. Click 'Confirm' button
15. Verify subscription confirmation displayed

### ✅ **Option 2: Detailed Requirements (Technical)**

If you already have detailed steps, just provide them:

```
Step 1: Navigate to URL
Step 2: Click button X
Step 3: Verify page shows Y
```

System will recognize this as detailed and process accordingly.

---

## 🎨 Example Templates

### E-commerce Purchase
```
Test product purchase:
- Add [product name] to cart
- Proceed to checkout
- Enter shipping details
- Complete payment
- Verify order confirmation

Product: [specific product]
Payment: Use test card
```

### User Registration
```
Test new user signup:
- Navigate to registration page
- Fill in required fields
- Accept terms and conditions
- Submit form
- Verify welcome email sent

Test data: Use random email generator
```

### Login Flow with Modal
```
Test login functionality:
- Click 'Login' button
- In the login modal, enter credentials
- Submit login form
- Verify successful authentication
- Check user dashboard displayed

Note: Login uses modal dialog overlay
```

---

## 🔧 Configuration

### Temperature Settings

**For Test Generation:**
- Default: `0.2` (high consistency)
- Range: `0.0 - 1.0`
- Lower = more consistent
- Higher = more creative/varied

To change (advanced users):
1. Go to Settings → User Preferences
2. Find "Generation Temperature"
3. Adjust as needed (recommend keeping ≤ 0.3)

---

## 📊 Comparison

### Before (Old System)
| Aspect | Result |
|--------|---------|
| Input required | 22 detailed steps |
| Consistency | Different results each time |
| Business user friendly | ❌ No - too technical |
| Temperature | 0.7 (high variance) |

### After (Improved System)
| Aspect | Result |
|--------|---------|
| Input required | Simple sentence/bullet points |
| Consistency | ✅ Same results every time |
| Business user friendly | ✅ Yes! |
| Temperature | 0.2 (low variance) |

---

## 💡 Tips for Best Results

### 1. **Include Context**
```
✅ Good: "Purchase $154 plan (48 months) on Three HK website"
❌ Bad: "Test purchase"
```

### 2. **Specify Important Details**
```
✅ Good: "Login with email in modal dialog"
❌ Bad: "Login"
```

### 3. **Mention Special UI Elements**
```
✅ Good: "In the popup/modal, click Submit"
❌ Bad: "Click Submit"
```

### 4. **Include Test Data**
```
✅ Good: "Use email: test@example.com, password: Test123"
❌ Bad: "Enter credentials"
```

---

## 🐛 Troubleshooting

### Issue: Results still inconsistent
**Solution:** Check temperature setting. Should be 0.1-0.3 for test generation.

### Issue: Generated steps too vague
**Solution:** Provide more context in requirement:
- Exact button text
- Field names
- Expected outcomes

### Issue: Missing verification steps
**Solution:** Add "Verify [expected result]" to your requirements.

### Issue: Modal/dialog not handled
**Solution:** Explicitly mention "in the modal" or "in the popup" in requirements.

---

## 🚀 Real-World Example: Three HK Test Case

**Your Simple Input:**
```
Purchase $154 plan with 48 months, login, select date, confirm
```

**System Output (Consistent):**
- ✅ Navigate to plan page
- ✅ Locate $154/month plan
- ✅ Select 48 months contract
- ✅ Verify selection
- ✅ Click subscribe button
- ✅ Handle login modal
- ✅ Enter credentials
- ✅ Submit login
- ✅ Select appointment date
- ✅ Confirm subscription
- ✅ Verify success

**Character count:** ~60 characters input → generates 15+ detailed steps

---

## 📞 Support

**Questions?**
- Check [BACKEND-AUTOMATION-BEST-PRACTICES.md](../project-documents/BACKEND-AUTOMATION-BEST-PRACTICES.md) for modal handling
- Review example test cases in the system
- Contact development team

**Technical Details:**
- Implementation: `backend/app/services/test_generation.py`
- Detection logic: `_detect_requirement_complexity()`
- Prompts: `_build_system_prompt()` and `_build_user_prompt()`

---

## ✅ Summary

**Old Way:**
```
Step 1: Navigate to: https://...
Step 2: Scroll down until...
Step 3: Locate the $154/month...
Step 4: Verify pricing...
[... 18 more steps ...]
```
Character count: ~1,500+ characters

**New Way:**
```
Purchase $154 plan (48 months), login, select date, confirm
URL: https://...
```
Character count: ~100 characters

**Result:** ✅ Same quality, 15x easier to write!

---

**Last Updated:** January 9, 2026  
**Version:** 2.0 (Improved)
