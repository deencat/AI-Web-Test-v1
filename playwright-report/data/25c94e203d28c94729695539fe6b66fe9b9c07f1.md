# Test info

- Name: Sprint 3 - Test Execution Features >> should show execution progress page with correct elements
- Location: /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/tests/e2e/08-sprint3-executions.spec.ts:114:7

# Error details

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[type="email"]')

    at /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/tests/e2e/08-sprint3-executions.spec.ts:7:16
```

# Page snapshot

```yaml
- heading "🤖 AI Web Test" [level=1]
- paragraph: Intelligent Test Automation Platform
- heading "Sign In" [level=2]
- text: Username
- textbox "Enter your username"
- text: Password
- textbox "Enter your password"
- button "Sign In"
- paragraph: "Demo credentials: any username/password"
```

# Test source

```ts
   1 | import { test, expect } from '@playwright/test';
   2 |
   3 | test.describe('Sprint 3 - Test Execution Features', () => {
   4 |   test.beforeEach(async ({ page }) => {
   5 |     // Login
   6 |     await page.goto('http://localhost:5173/login');
>  7 |     await page.fill('input[type="email"]', 'admin@aiwebtest.com');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
   8 |     await page.fill('input[type="password"]', 'admin123');
   9 |     await page.click('button[type="submit"]');
   10 |     await page.waitForURL('**/dashboard');
   11 |   });
   12 |
   13 |   test('should show Executions link in sidebar', async ({ page }) => {
   14 |     // Check if Executions link exists in sidebar
   15 |     const executionsLink = page.locator('nav a[href="/executions"]');
   16 |     await expect(executionsLink).toBeVisible();
   17 |     await expect(executionsLink).toContainText('Executions');
   18 |   });
   19 |
   20 |   test('should navigate to execution history page', async ({ page }) => {
   21 |     // Click on Executions in sidebar
   22 |     await page.click('nav a[href="/executions"]');
   23 |     await page.waitForURL('**/executions');
   24 |
   25 |     // Check page title
   26 |     await expect(page.locator('h1')).toContainText('Execution History');
   27 |   });
   28 |
   29 |   test('should display execution history table', async ({ page }) => {
   30 |     // Navigate to executions page
   31 |     await page.goto('http://localhost:5173/executions');
   32 |
   33 |     // Wait for the page to load
   34 |     await page.waitForSelector('table, div:has-text("No executions found")');
   35 |
   36 |     // Check for table headers
   37 |     const table = page.locator('table');
   38 |     if (await table.isVisible()) {
   39 |       await expect(table.locator('thead th').first()).toContainText('ID');
   40 |       await expect(table.locator('thead th').nth(1)).toContainText('Test Case');
   41 |       await expect(table.locator('thead th').nth(2)).toContainText('Status');
   42 |       await expect(table.locator('thead th').nth(3)).toContainText('Result');
   43 |     }
   44 |   });
   45 |
   46 |   test('should filter executions by status', async ({ page }) => {
   47 |     await page.goto('http://localhost:5173/executions');
   48 |
   49 |     // Find the status filter dropdown
   50 |     const statusFilter = page.locator('select').first();
   51 |     await expect(statusFilter).toBeVisible();
   52 |
   53 |     // Select "Completed" status
   54 |     await statusFilter.selectOption('completed');
   55 |
   56 |     // Wait for filter to apply
   57 |     await page.waitForTimeout(500);
   58 |
   59 |     // Verify the filter was applied (URL or UI should reflect the filter)
   60 |     const selectedValue = await statusFilter.inputValue();
   61 |     expect(selectedValue).toBe('completed');
   62 |   });
   63 |
   64 |   test('should filter executions by result', async ({ page }) => {
   65 |     await page.goto('http://localhost:5173/executions');
   66 |
   67 |     // Find the result filter dropdown
   68 |     const resultFilter = page.locator('select').nth(1);
   69 |     await expect(resultFilter).toBeVisible();
   70 |
   71 |     // Select "Pass" result
   72 |     await resultFilter.selectOption('pass');
   73 |
   74 |     // Wait for filter to apply
   75 |     await page.waitForTimeout(500);
   76 |
   77 |     // Verify the filter was applied
   78 |     const selectedValue = await resultFilter.inputValue();
   79 |     expect(selectedValue).toBe('pass');
   80 |   });
   81 |
   82 |   test('should have refresh button', async ({ page }) => {
   83 |     await page.goto('http://localhost:5173/executions');
   84 |
   85 |     // Check for refresh button
   86 |     const refreshButton = page.locator('button:has-text("Refresh")');
   87 |     await expect(refreshButton).toBeVisible();
   88 |
   89 |     // Click refresh button
   90 |     await refreshButton.click();
   91 |     await page.waitForTimeout(500);
   92 |   });
   93 |
   94 |   test('should navigate to execution detail page when clicking a row', async ({ page }) => {
   95 |     await page.goto('http://localhost:5173/executions');
   96 |
   97 |     // Wait for table to load
   98 |     await page.waitForSelector('table tbody tr, div:has-text("No executions found")');
   99 |
  100 |     // Check if there are any executions
  101 |     const rows = page.locator('table tbody tr');
  102 |     const rowCount = await rows.count();
  103 |
  104 |     if (rowCount > 0) {
  105 |       // Click on first row
  106 |       await rows.first().click();
  107 |
```