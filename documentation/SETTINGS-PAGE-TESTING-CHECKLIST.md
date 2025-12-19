# Settings Page Dynamic Configuration - Browser Testing Checklist

**Date:** December 16, 2025  
**Status:** Ready for Manual Testing  
**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

---

## ✅ Pre-Test Checklist

- [x] Backend server running (port 8000)
- [x] Frontend server running (port 5173)
- [x] Database migration executed
- [x] Test user exists (admin/admin123)
- [x] API endpoints tested via script (8/8 passed)

---

## 🧪 Manual Browser Testing Steps

### Test 1: Login and Access Settings
1. Navigate to http://localhost:5173
2. Login with credentials: `admin` / `admin123`
3. Click "Settings" in navigation menu
4. **Expected:** Settings page loads without errors

### Test 2: View Available Providers
1. Scroll to "AI Provider - Test Generation" section
2. **Expected:** See 3 provider cards (Google, Cerebras, OpenRouter)
3. **Expected:** Each card shows:
   - Provider name
   - Number of models
   - Status (✓ Configured or ✗ No API Key)

### Test 3: View Current Settings
1. Check the selected provider (should be highlighted)
2. Check the selected model in dropdown
3. Check temperature slider value
4. Check max tokens input value
5. **Expected:** Values match default or previously saved settings

### Test 4: Update Generation Settings
1. Click on a different provider card (e.g., Google Gemini)
2. Select a model from dropdown
3. Adjust temperature slider to 0.8
4. Change max tokens to 8192
5. Click "Save Settings" button
6. **Expected:** 
   - Button shows "Saving..." briefly
   - Green success message appears
   - Message says "Using GOOGLE for generation"

### Test 5: Update Execution Settings
1. Scroll to "AI Provider - Test Execution" section
2. Select a different provider than generation
3. Choose a model optimized for execution
4. Adjust temperature to 0.6
5. Set max tokens to 4096
6. Click "Save Settings" button
7. **Expected:** Success message shows both providers

### Test 6: Verify Settings Persist
1. Click away from Settings page (e.g., Dashboard)
2. Navigate back to Settings page
3. **Expected:** 
   - Previously selected providers still selected
   - Model dropdowns show correct values
   - Temperature sliders in correct positions
   - Max tokens values preserved

### Test 7: Test Partial Update
1. Only change temperature slider (don't change provider/model)
2. Click "Save Settings"
3. **Expected:** 
   - Save succeeds
   - Other settings remain unchanged

### Test 8: Reset to Defaults
1. Click "Reset to Defaults" button
2. Confirm the dialog
3. **Expected:**
   - Page reloads with default values
   - Success message appears
   - Providers reset to environment defaults

### Test 9: Provider Not Configured
1. Look for providers with "✗ No API Key" status
2. Try to click on unconfigured provider
3. **Expected:** 
   - Button should be disabled (opacity reduced)
   - Cursor shows "not-allowed"
   - Cannot select unconfigured provider

### Test 10: Real-Time Updates
1. Open browser dev console (F12)
2. Go to Network tab
3. Make a settings change and save
4. **Expected:**
   - See PUT request to `/api/v1/settings/provider`
   - Status 200 OK
   - Response contains updated settings

---

## 🎯 Integration Testing

### Test 11: Test Generation with New Settings
1. Save generation settings with specific provider/model
2. Navigate to Tests page
3. Click "Generate Tests" button
4. Enter a requirement
5. Generate tests
6. **Expected:** 
   - Tests generated using your selected provider
   - Check backend logs to confirm model used

### Test 12: Test Execution with New Settings
1. Save execution settings with specific provider/model
2. Navigate to Tests page
3. Run an existing test
4. **Expected:**
   - Execution uses your selected execution provider
   - Check backend logs to confirm model used

---

## 🔍 Edge Cases to Test

### Test 13: Model Dropdown Population
1. Switch between providers
2. **Expected:** Model dropdown updates with provider-specific models

### Test 14: Temperature Slider Bounds
1. Try to set temperature to 0.0
2. Try to set temperature to 2.0
3. **Expected:** Both extremes work correctly

### Test 15: Max Tokens Validation
1. Try to enter 50 (below minimum)
2. Try to enter 100000 (above maximum)
3. **Expected:** Validation errors or clamping to valid range

### Test 16: Concurrent User Settings
1. Login as admin user
2. Set Google for generation
3. Logout
4. Login as different user (create if needed)
5. **Expected:** Settings are per-user, not shared

---

## 🐛 Common Issues to Check

### UI Issues
- [ ] Loading spinner shows while fetching data
- [ ] Success messages disappear after 5 seconds
- [ ] Error messages display properly
- [ ] Buttons disabled during save operation
- [ ] Form inputs properly styled and accessible

### API Issues
- [ ] 401 errors handled (redirect to login)
- [ ] Network errors show user-friendly messages
- [ ] Timeouts handled gracefully

### Performance Issues
- [ ] Page loads in < 2 seconds
- [ ] Save operation completes in < 1 second
- [ ] No console errors or warnings

---

## 📸 Screenshots to Capture

1. Settings page with all sections visible
2. Provider selection with status indicators
3. Success message after save
4. Reset confirmation dialog
5. Provider not configured state
6. Network tab showing API calls

---

## ✅ Expected Outcomes

After completing all tests:

1. ✅ Users can view available AI providers
2. ✅ Users can see which providers are configured
3. ✅ Users can select different providers for generation vs execution
4. ✅ Users can update model, temperature, and max tokens
5. ✅ Settings save successfully and persist
6. ✅ Settings load correctly on page refresh
7. ✅ Partial updates work (only changed fields)
8. ✅ Reset to defaults works
9. ✅ Unconfigured providers cannot be selected
10. ✅ Settings integrate with test generation/execution

---

## 🎉 Success Criteria

**All tests pass if:**
- No console errors
- All API calls return 200 OK
- Settings persist correctly
- UI is responsive and intuitive
- Integration with test generation/execution works

---

## 📋 Bug Report Template (if issues found)

```
### Bug Description
[Clear description of the issue]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Screenshots
[Attach screenshots if applicable]

### Console Errors
[Copy any console errors]

### Environment
- Browser: [Chrome/Firefox/Safari]
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
```

---

**Ready to test?** Start with Test 1 and work through sequentially! 🚀
