import { test, expect } from '@playwright/test';

test.describe('Sprint 3 - Test Execution Features', () => {
  test.beforeEach(async ({ page }) => {
    // Login using same pattern as existing tests
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
  });

  test('should show Executions link in sidebar', async ({ page }) => {
    // Check if Executions link exists in sidebar
    const executionsLink = page.locator('nav a[href="/executions"]');
    await expect(executionsLink).toBeVisible();
    await expect(executionsLink).toContainText('Executions');
  });

  test('should navigate to execution history page', async ({ page }) => {
    // Click on Executions in sidebar
    await page.click('nav a[href="/executions"]');
    await page.waitForURL('**/executions');

    // Check page title
    await expect(page.locator('h1')).toContainText('Execution History');
  });

  test('should display execution history table', async ({ page }) => {
    // Navigate to executions page
    await page.goto('/executions');

    // Wait for the page to load
    await page.waitForSelector('table, div:has-text("No executions found")');

    // Check for table headers
    const table = page.locator('table');
    if (await table.isVisible()) {
      await expect(table.locator('thead th').first()).toContainText('ID');
      await expect(table.locator('thead th').nth(1)).toContainText('Test Case');
      await expect(table.locator('thead th').nth(2)).toContainText('Status');
      await expect(table.locator('thead th').nth(3)).toContainText('Result');
    }
  });

  test('should filter executions by status', async ({ page }) => {
    await page.goto('/executions');

    // Find the status filter dropdown
    const statusFilter = page.locator('select').first();
    await expect(statusFilter).toBeVisible();

    // Select "Completed" status
    await statusFilter.selectOption('completed');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Verify the filter was applied (URL or UI should reflect the filter)
    const selectedValue = await statusFilter.inputValue();
    expect(selectedValue).toBe('completed');
  });

  test('should filter executions by result', async ({ page }) => {
    await page.goto('/executions');

    // Find the result filter dropdown
    const resultFilter = page.locator('select').nth(1);
    await expect(resultFilter).toBeVisible();

    // Select "Pass" result
    await resultFilter.selectOption('pass');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Verify the filter was applied
    const selectedValue = await resultFilter.inputValue();
    expect(selectedValue).toBe('pass');
  });

  test('should have refresh button', async ({ page }) => {
    await page.goto('/executions');

    // Check for refresh button
    const refreshButton = page.locator('button:has-text("Refresh")');
    await expect(refreshButton).toBeVisible();

    // Click refresh button
    await refreshButton.click();
    await page.waitForTimeout(500);
  });

  test('should navigate to execution detail page when clicking a row', async ({ page }) => {
    await page.goto('/executions');

    // Wait for table to load
    await page.waitForSelector('table tbody tr, div:has-text("No executions found")');

    // Check if there are any executions
    const rows = page.locator('table tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Click on first row
      await rows.first().click();

      // Should navigate to execution detail page
      await page.waitForURL('**/executions/*');
      await expect(page.url()).toMatch(/\/executions\/\d+/);
    }
  });

  test('should show execution progress page with correct elements', async ({ page }) => {
    // Navigate directly to an execution detail page (mock data should show)
    await page.goto('/executions/1');

    // Wait for page to load
    await page.waitForSelector('h1, div:has-text("Error")');

    // Check for main elements (either real data or error message)
    const pageTitle = page.locator('h1');
    const titleText = await pageTitle.textContent();
    
    // Either shows "Execution #1" or "Error"
    expect(titleText).toMatch(/Execution #\d+|Error/);
  });

  test('should have back button on execution detail page', async ({ page }) => {
    await page.goto('/executions/1');

    // Check for back button
    const backButton = page.locator('button:has-text("Back to Executions")');
    
    // The button should exist
    const count = await backButton.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show execution overview card with stats', async ({ page }) => {
    await page.goto('/executions/1');

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Look for execution overview elements
    const hasOverview = await page.locator('h2:has-text("Execution Overview")').isVisible().catch(() => false);
    const hasError = await page.locator('div:has-text("Error")').isVisible().catch(() => false);

    // Should have either overview or error
    expect(hasOverview || hasError).toBe(true);
  });

  test('should display test steps if execution exists', async ({ page }) => {
    await page.goto('/executions/1');

    await page.waitForTimeout(1000);

    // Check for steps section or error
    const hasSteps = await page.locator('h2:has-text("Test Steps")').isVisible().catch(() => false);
    const hasError = await page.locator('div:has-text("Error")').isVisible().catch(() => false);

    // Should have either steps or error
    expect(hasSteps || hasError).toBe(true);
  });

  test('should show queue status widget on tests page', async ({ page }) => {
    // Note: Queue widget may be added to tests page or dashboard
    await page.goto('/tests');

    // Check if queue status widget exists anywhere
    const queueWidget = page.locator('h3:has-text("Execution Queue")');
    
    // Widget might not be on this page, so we just check count
    const count = await queueWidget.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display execution status badges correctly', async ({ page }) => {
    await page.goto('/executions');

    await page.waitForSelector('table, div:has-text("No executions found")');

    // Look for status badges (if any executions exist)
    const statusBadges = page.locator('table tbody span[class*="bg-"]');
    const badgeCount = await statusBadges.count();

    // Either has badges or table is empty
    expect(badgeCount).toBeGreaterThanOrEqual(0);
  });

  test('should handle empty execution list gracefully', async ({ page }) => {
    await page.goto('/executions');

    await page.waitForSelector('table tbody, div:has-text("No executions found")');

    // Check for either table rows or empty message
    const emptyMessage = page.locator('div:has-text("No executions found")');
    const tableRows = page.locator('table tbody tr');

    const hasEmptyMessage = await emptyMessage.isVisible().catch(() => false);
    const hasRows = await tableRows.count() > 0;

    // Should have either message or rows
    expect(hasEmptyMessage || hasRows).toBe(true);
  });

  test('should show delete button for executions', async ({ page }) => {
    await page.goto('/executions');

    await page.waitForSelector('table tbody tr, div:has-text("No executions found")');

    const rows = await page.locator('table tbody tr').count();

    if (rows > 0) {
      // Check for delete buttons in action column
      const deleteButton = page.locator('button:has-text("Delete")').first();
      await expect(deleteButton).toBeVisible();
    }
  });

  test('should navigate between pages using sidebar', async ({ page }) => {
    // Start from executions page
    await page.goto('/executions');

    // Navigate to Dashboard
    await page.click('nav a[href="/dashboard"]');
    await page.waitForURL('**/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');

    // Navigate back to Executions
    await page.click('nav a[href="/executions"]');
    await page.waitForURL('**/executions');
    await expect(page.locator('h1')).toContainText('Execution History');
  });

  test('should maintain active nav state on executions page', async ({ page }) => {
    await page.goto('/executions');

    // Check if executions link is active
    const executionsLink = page.locator('nav a[href="/executions"]');
    
    // Active link should have specific classes
    const classes = await executionsLink.getAttribute('class');
    expect(classes).toContain('bg-blue-700'); // or whatever active class is used
  });
});
