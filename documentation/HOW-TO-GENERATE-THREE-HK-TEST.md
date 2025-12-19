# What to Type in Tests Page - Three.com.hk 5G Broadband Example

## 📝 Copy and Paste This Into the Text Area:

```
Test the Three.com.hk 5G Broadband subscription flow at https://web.three.com.hk/5gbroadband/plan-hsbc-en.html

Requirements:
1. Navigate to the 5G Broadband plan page
2. Scroll down to see all contract period options (12, 24, 30 months)
3. Select the "30 months" contract period option by clicking the button
4. Verify the selected plan shows pricing: $135/month (discounted from $198)
5. Verify plan details: 5G Broadband Wi-Fi 6 Service Plan, Infinite 5G Data
6. Click the "Subscribe Now" button under the selected plan
7. Handle customer notice popup - check "Don't show this again" and close it
8. Verify subscription form is visible with all plan details
9. Verify pricing shows: FREE 6-month promotion, Waived $28 Admin Fee, 30 months contract
10. Click "Next" button to proceed to service plan details page
11. Verify Service Plan Details section shows correct information
12. Verify payment breakdown: Prepayment SIM Card Fee $100, Total Amount Due $100
13. Check the "I confirm that I have reviewed details and agree" checkbox
14. Click "Subscribe Now" to proceed to login
15. Click "Login" button to open login form
16. Enter email: pmo.andrewchan+010@gmail.com
17. Click "Login" to proceed to password screen
18. Enter password: cA8mn49&
19. Click "Login" to submit credentials
20. Wait for authentication to complete
21. Select service effective date (3 days from today)
22. Click "Confirm" to complete the subscription

Expected Result:
Successfully complete the full 5G Broadband subscription flow including plan selection, checkout, login authentication, and service date selection. All pages should load correctly, pricing should be displayed accurately, and the user should be able to proceed through all steps without errors.

Test Data:
- URL: https://web.three.com.hk/5gbroadband/plan-hsbc-en.html
- Contract: 30 months
- Plan: 5G Broadband Wi-Fi 6 Service Plan
- Price: $135/month (from $198)
- Email: pmo.andrewchan+010@gmail.com
- Password: cA8mn49&
```

---

## 🎯 Shorter Version (If you want AI to fill in details):

```
Test the Three.com.hk 5G Broadband subscription flow at https://web.three.com.hk/5gbroadband/plan-hsbc-en.html

The test should:
- Select 30 months contract period
- Verify pricing: $135/month (discounted from $198)
- Click "Subscribe Now"
- Handle customer notice popup
- Proceed through checkout pages
- Verify payment breakdown (SIM Card $100, Total $100)
- Complete login with email: pmo.andrewchan+010@gmail.com and password: cA8mn49&
- Select service date (3 days from today)
- Complete subscription

Expected: Full subscription flow completes successfully with all validations passing.
```

---

## 📋 Step-by-Step Instructions:

### 1. **Open the Tests Page**
   - Navigate to: `http://localhost:5173/tests`
   - You should see "Test Cases" page with a text area

### 2. **Copy the Requirement**
   - Copy EITHER the detailed or shorter version above
   - The detailed version gives AI more context
   - The shorter version lets AI generate more creative steps

### 3. **Paste Into Text Area**
   - Click in the text area where it says "Example: Test the login flow..."
   - Paste the requirement text

### 4. **Click "Generate Test Cases"**
   - Click the blue button with sparkles icon ✨
   - Wait 2-5 seconds for AI to generate

### 5. **Review Generated Test**
   - AI will generate a test case with:
     * Title: "Three.com.hk - 5G Broadband Complete Subscription Flow"
     * Description: Summary of what the test does
     * Steps: 15-25 detailed steps
     * Priority: High/Medium/Low
     * Type: e2e (end-to-end)

### 6. **Edit if Needed (Optional)**
   - Click "Edit" if you want to modify any steps
   - Change title, priority, or step descriptions
   - Add/remove steps

### 7. **Save to Tests**
   - Click "Save to Tests" button
   - Test will be saved to database
   - You'll be redirected to "Saved Tests" section

### 8. **Run the Test**
   - Find your test in the "Saved Tests" list
   - Click "Run Test" button
   - Test will execute using Stagehand/Playwright
   - Navigate to Executions page to see results

---

## 🎨 Visual Guide:

```
┌─────────────────────────────────────────────────────────────────┐
│ Test Cases                                                      │
│ Generate test cases using natural language                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Describe the test you want to create:                          │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Test the Three.com.hk 5G Broadband subscription flow at   │ │
│ │ https://web.three.com.hk/5gbroadband/plan-hsbc-en.html    │ │
│ │                                                            │ │
│ │ The test should:                                           │ │
│ │ - Select 30 months contract period                        │ │
│ │ - Verify pricing: $135/month (discounted from $198)       │ │
│ │ - Click "Subscribe Now"                                    │ │
│ │ - Handle customer notice popup                            │ │
│ │ - Proceed through checkout pages                          │ │
│ │ - Verify payment breakdown (SIM Card $100, Total $100)    │ │
│ │ - Complete login with email: pmo.andrewchan+010@...       │ │
│ │ - Select service date (3 days from today)                 │ │
│ │ - Complete subscription                                    │ │
│ │                                                            │ │
│ │ Expected: Full subscription flow completes successfully    │ │
│ │ with all validations passing.                             │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [ ✨ Generate Test Cases ]                                     │ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼ (Click Generate)
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Generated Test Case                                          │
├─────────────────────────────────────────────────────────────────┤
│ Title: Three.com.hk - 5G Broadband Complete Subscription Flow  │
│ Priority: High                                                  │
│ Steps: 24 steps                                                 │
│                                                                 │
│ 1. Navigate to https://web.three.com.hk/5gbroadband/...        │
│ 2. Scroll down to see contract period options                  │
│ 3. Click "30 months" button                                    │
│ ... (21 more steps)                                            │
│                                                                 │
│ [ Edit ]  [ Save to Tests ]  [ Discard ]                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 Tips for Better Test Generation:

### Include These Details:
1. **URL**: Always include the exact URL to test
2. **Actions**: Click, type, verify, wait
3. **Expected Data**: Prices, text, values to verify
4. **Credentials**: Email, password (if needed)
5. **Expected Result**: What success looks like

### Example Format:
```
Test [FEATURE] at [URL]

The test should:
- [Action 1]: [Details]
- [Action 2]: [Details]
- [Verification]: [What to check]

Test Data:
- [Field]: [Value]
- [Field]: [Value]

Expected Result: [Success criteria]
```

---

## 🚀 Try It Now!

1. Copy the requirement text from the top
2. Open: `http://localhost:5173/tests`
3. Paste into the text area
4. Click "Generate Test Cases"
5. Review the AI-generated test
6. Click "Save to Tests"
7. Click "Run Test"
8. Watch it execute! 🎉

The AI will generate all the detailed steps automatically, just like the manual test in `test_three_5g_broadband.py`!
