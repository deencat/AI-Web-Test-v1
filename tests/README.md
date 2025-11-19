# E2E Tests for AI Web Test Platform

This directory contains end-to-end tests using Playwright for the AI Web Test frontend application.

## Test Structure

```
tests/
├── e2e/
│   ├── 01-login.spec.ts           # Login page authentication tests
│   ├── 02-dashboard.spec.ts       # Dashboard page tests
│   ├── 03-tests-page.spec.ts      # Test cases management page tests
│   ├── 04-knowledge-base.spec.ts  # Knowledge Base page tests
│   ├── 05-settings.spec.ts        # Settings page tests
│   └── 06-navigation.spec.ts      # Application navigation flow tests
└── README.md
```

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install chromium
```

### Run All Tests

```bash
# Run all tests in headless mode
npm test

# Run all tests with UI
npm run test:ui

# Run tests in headed mode (see browser)
npm run test:headed

# Run tests in debug mode
npm run test:debug
```

### Run Specific Tests

```bash
# Run only login tests
npx playwright test 01-login

# Run only dashboard tests
npx playwright test 02-dashboard

# Run tests matching a pattern
npx playwright test knowledge-base
```

### View Test Results

```bash
# Open HTML test report
npm run test:report

# View test results in browser
npx playwright show-report
```

## Test Coverage

### 01-login.spec.ts
- ✅ Display login form
- ✅ Validation for empty fields
- ✅ Successful login with mock credentials
- ✅ Navigation to dashboard
- ✅ Responsive design testing

### 02-dashboard.spec.ts
- ✅ Display dashboard statistics
- ✅ Show recent test results
- ✅ Display agent activity
- ✅ Header and sidebar functionality
- ✅ Navigation to other pages
- ✅ Mobile responsiveness

### 03-tests-page.spec.ts
- ✅ Display test cases list
- ✅ Show filter buttons (All, Passed, Failed, Pending)
- ✅ Display test metadata (status, agent, priority)
- ✅ Create new test button functionality
- ✅ View test details functionality
- ✅ Mobile layout testing

### 04-knowledge-base.spec.ts
- ✅ Display KB documents
- ✅ Category filtering
- ✅ Upload document functionality
- ✅ Create category functionality
- ✅ Document metadata display
- ✅ Responsive layout

### 05-settings.spec.ts
- ✅ General settings configuration
- ✅ Notification settings
- ✅ Agent configuration toggles
- ✅ Form field interactions
- ✅ Save functionality
- ✅ Mobile layout

### 06-navigation.spec.ts
- ✅ Full navigation flow
- ✅ Header persistence
- ✅ Sidebar persistence
- ✅ Active page highlighting
- ✅ Direct URL navigation
- ✅ Browser back/forward buttons
- ✅ Page refresh handling
- ✅ Mobile navigation

## Design Mode Compliance

These tests are designed for **Prototyping/Design Mode**:
- ✅ Frontend-only testing
- ✅ Mock data validation
- ✅ UI/UX interaction testing
- ✅ Component navigation verification
- ✅ Responsive button and layout testing
- ✅ No backend integration required

## CI/CD Integration

The test suite is configured for CI/CD with:
- Automatic retries on failure (2 retries in CI)
- Screenshot capture on failure
- Video recording on failure
- HTML, JSON, and JUnit reports
- Headless execution in CI environment

## Test Development Guidelines

1. **Naming Convention**: Use descriptive test names with `should` prefix
2. **Test Isolation**: Each test should be independent
3. **Mock Data**: Use the mock data from `frontend/src/mock/`
4. **Selectors**: Prefer role-based selectors (accessibility)
5. **Waits**: Use `waitForURL` and `waitFor` methods appropriately
6. **Assertions**: Use explicit expects with descriptive messages

## Debugging Tests

```bash
# Run tests in debug mode with inspector
npx playwright test --debug

# Run specific test in debug mode
npx playwright test 01-login --debug

# Generate trace file for failed tests
npx playwright test --trace on
```

## Updating Tests

When frontend features are updated:
1. Update corresponding test spec file
2. Run tests locally to verify
3. Update this README if new test files are added
4. Commit tests along with feature changes

## Continuous Testing

As per Design Mode requirements:
- **Always add newly changed features to Playwright tests**
- **Run full regression test suite after each change**
- **Update tests before marking features as complete**

## Known Limitations (Design Mode)

- Tests use mock data (no real API calls)
- Alert/confirm dialogs used for button interactions (temporary)
- Actual filtering logic not yet implemented (UI interaction only)
- Form submissions show alerts instead of processing

These limitations will be addressed in later sprint phases when backend integration is implemented.

