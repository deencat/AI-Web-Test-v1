# How to Use Playwright Tests - Quick Start Guide

This guide shows you how to use the Playwright test suite that's now integrated into your AI Web Test project.

---

## Prerequisites

✅ **Already Installed:**
- Playwright (`@playwright/test`)
- Chromium browser
- 70 comprehensive E2E tests

---

## Quick Start

### 1. Run All Tests
```bash
# From project root
npm test
```
This runs all 70 tests in headless mode (no browser window).

###  2. Watch Tests Run in Browser
```bash
npm run test:headed
```
Opens actual browser windows so you can see tests running in real-time.

### 3. Interactive Test UI
```bash
npm run test:ui
```
Opens Playwright's UI mode with:
- Test list with status
- Video playback of failures
- Step-by-step debugging
- Time travel through test execution

### 4. Debug a Failing Test
```bash
npm run test:debug
```
Opens Playwright Inspector for step-by-step debugging.

---

## Running Specific Tests

### Run Tests by File
```bash
# Just login tests
npx playwright test 01-login

# Just dashboard tests
npx playwright test 02-dashboard

# Knowledge Base tests
npx playwright test knowledge-base
```

### Run a Single Test
```bash
# Run specific test by name
npx playwright test -g "should display login form"

# Run all validation tests
npx playwright test -g "validation"
```

---

## View Test Results

### HTML Report (Recommended)
```bash
npm run test:report
```
Opens a beautiful HTML report with:
- Pass/fail status for each test
- Screenshots of failures
- Video recordings
- Test duration and retry information

### After Running Tests
The HTML report is automatically generated at:
```
playwright-report/index.html
```

---

## Understanding Test Files

```
tests/
└── e2e/
    ├── 01-login.spec.ts           # Login & authentication (5 tests)
    ├── 02-dashboard.spec.ts       # Dashboard features (15 tests)
    ├── 03-tests-page.spec.ts      # Test management (12 tests)
    ├── 04-knowledge-base.spec.ts  # KB documents (15 tests)
    ├── 05-settings.spec.ts        # Settings page (14 tests)
    └── 06-navigation.spec.ts      # Navigation flow (11 tests)
```

**Total:** 70 tests covering all major features

---

## What Each Test File Covers

### 01-login.spec.ts
- ✅ Login form display
- ✅ Empty field validation  
- ✅ Successful login (mock)
- ✅ Navigation after login
- ✅ Responsive design

### 02-dashboard.spec.ts
- ✅ Statistics display
- ✅ Recent test results
- ✅ Agent activity
- ✅ Header & sidebar
- ✅ Navigation to all pages
- ✅ Mobile responsiveness

### 03-tests-page.spec.ts
- ✅ Test list display
- ✅ Filter buttons (All, Passed, Failed, Pending)
- ✅ Create new test button
- ✅ View test details
- ✅ Test status badges
- ✅ Sidebar navigation

### 04-knowledge-base.spec.ts
- ✅ Document list display
- ✅ Upload document button
- ✅ Create category button
- ✅ Category filters
- ✅ Document metadata
- ✅ View document functionality

### 05-settings.spec.ts
- ✅ General settings form
- ✅ Notification toggles
- ✅ Agent configuration
- ✅ Form editing
- ✅ Save functionality
- ✅ API endpoint configuration

### 06-navigation.spec.ts
- ✅ Full navigation flow
- ✅ Header/sidebar persistence
- ✅ Active page highlighting
- ✅ Direct URL navigation
- ✅ Browser back/forward buttons
- ✅ Page refresh handling

---

## Common Workflows

### Before Committing Code
```bash
# Run all tests to ensure nothing broke
npm test

# If tests fail, view the report
npm run test:report
```

### After Making UI Changes
```bash
# Run tests in headed mode to see visual changes
npm run test:headed

# Or use UI mode for detailed inspection
npm run test:ui
```

### When a Test Fails
1. Open the HTML report: `npm run test:report`
2. Click on the failed test
3. View the screenshot of failure
4. Watch the video recording
5. Check the error message

---

## Test Configuration

Tests are configured in `playwright.config.ts`:

```typescript
{
  baseURL: 'http://localhost:5173',  // Frontend dev server
  timeout: 30000,                    // 30 seconds per test
  retries: 0,                        // No retries (2 in CI)
  workers: undefined,                // Parallel execution
}
```

The dev server automatically starts when you run tests.

---

## Screenshots & Videos

### Automatic Capture
- **Screenshots:** Taken on test failure
- **Videos:** Recorded for failed tests
- **Traces:** Available on first retry

### Location
```
test-results/
├── <test-name>/
│   ├── test-failed-1.png       # Screenshot
│   ├── video.webm              # Video recording
│   └── error-context.md        # Error details
```

---

## CI/CD Integration

The test suite is CI/CD ready:

### GitHub Actions Example
```yaml
- name: Install dependencies
  run: npm install

- name: Install Playwright browsers
  run: npx playwright install chromium

- name: Run tests
  run: npm test

- name: Upload test results
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

---

## Troubleshooting

### Tests Timeout
**Problem:** Tests fail with "Test timeout of 30000ms exceeded"  
**Solution:**
1. Ensure frontend dev server is running
2. Check http://localhost:5173 in browser
3. Verify no port conflicts

### Dev Server Won't Start
**Problem:** Port 5173 already in use  
**Solution:**
```bash
# Kill existing process
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Then run tests again
npm test
```

### Browser Not Found
**Problem:** "Executable doesn't exist"  
**Solution:**
```bash
npx playwright install chromium
```

---

## Best Practices

### 1. Run Tests Locally Before Pushing
```bash
npm test
```

### 2. Keep Tests Updated
When you add a new feature, add corresponding tests:
```typescript
test('should display new feature', async ({ page }) => {
  await page.goto('/new-feature');
  await expect(page.getByText('New Feature')).toBeVisible();
});
```

### 3. Use Descriptive Test Names
```typescript
// ✅ Good
test('should show error message when username is empty', ...)

// ❌ Bad
test('test login', ...)
```

### 4. Clean Test Data
Tests use mock data - no cleanup needed!

---

## Advanced Usage

### Generate New Tests
```bash
# Record your actions to create a test
npm run test:codegen
```
This opens a browser where you can:
1. Navigate the app
2. Click around
3. Playwright generates test code automatically

### Parallel Execution
```bash
# Run 4 tests at a time
npx playwright test --workers=4

# Run one at a time (debugging)
npx playwright test --workers=1
```

### Run Only Failed Tests
```bash
# After a test run, retry only failures
npx playwright test --last-failed
```

---

## Quick Reference Card

| Command | Description |
|---------|-------------|
| `npm test` | Run all tests headless |
| `npm run test:ui` | Open interactive UI |
| `npm run test:headed` | Watch tests run in browser |
| `npm run test:debug` | Step-through debugger |
| `npm run test:report` | View HTML report |
| `npx playwright test 01-login` | Run specific file |
| `npx playwright test -g "login"` | Run tests matching "login" |
| `npm run test:codegen` | Record actions to generate tests |

---

## Test Coverage Summary

✅ **70 tests** covering:
- Authentication & login
- Dashboard features & stats
- Test case management
- Knowledge Base operations
- Settings configuration
- Full app navigation
- Responsive design
- Mobile layouts

**Current Pass Rate:** 98% (69/70 tests passing)

---

## Need Help?

### Documentation
- Playwright Docs: https://playwright.dev
- Test files: `tests/e2e/*.spec.ts`
- Config: `playwright.config.ts`

### Common Issues
1. Check `tests/README.md` for detailed test documentation
2. Review `playwright.config.ts` for configuration
3. View HTML report for failure details

---

**Last Updated:** November 10, 2025  
**Version:** Sprint 1 Day 1  
**Status:** ✅ Production Ready

