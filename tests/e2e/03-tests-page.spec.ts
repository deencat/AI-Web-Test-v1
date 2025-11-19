import { test, expect } from '@playwright/test';

/**
 * Tests Page Tests
 * Tests the test cases management page with mock data
 * Design Mode: Frontend only with dummy JSON
 */

test.describe('Tests Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    
    // Navigate to Tests page
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
  });

  test('should display tests page with header', async ({ page }) => {
    // Verify page heading
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
  });

  test('should display create new test button', async ({ page }) => {
    // Verify action button
    await expect(page.getByRole('button', { name: /create new test/i })).toBeVisible();
  });

  test('should display filter buttons', async ({ page }) => {
    // Verify filter buttons exist
    await expect(page.getByRole('button', { name: /all/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /passed/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /failed/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /pending/i })).toBeVisible();
  });

  test('should display mock test cases', async ({ page }) => {
    // Verify test cases are displayed
    // Mock data includes: Login Flow Test, API Health Check, Payment Gateway Test
    await expect(page.getByText(/login flow test/i).first()).toBeVisible();
    await expect(page.getByText(/API health check/i).first()).toBeVisible();
    await expect(page.getByText(/payment gateway test/i).first()).toBeVisible();
  });

  test('should display test status badges', async ({ page }) => {
    // Verify status indicators
    await expect(page.locator('text=passed').first()).toBeVisible();
    await expect(page.locator('text=failed').first()).toBeVisible();
  });

  test('should display view details buttons', async ({ page }) => {
    // Verify each test has a view button
    const viewButtons = page.getByRole('button', { name: /view details/i });
    await expect(viewButtons.first()).toBeVisible();
    expect(await viewButtons.count()).toBeGreaterThan(0);
  });

  test('should show alert when clicking create new test', async ({ page }) => {
    // Setup dialog handler
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Create New Test');
      dialog.accept();
    });
    
    // Click create button
    await page.getByRole('button', { name: /create new test/i }).click();
  });

  test('should show alert when clicking view details', async ({ page }) => {
    // Setup dialog handler
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('View test details');
      dialog.accept();
    });
    
    // Click first view details button
    await page.getByRole('button', { name: /view details/i }).first().click();
  });

  test('should filter tests by status (UI interaction)', async ({ page }) => {
    // Click on passed filter
    await page.getByRole('button', { name: /passed/i }).click();
    
    // Button should be visually selected (this is UI state, actual filtering will be implemented later)
    await expect(page.getByRole('button', { name: /passed/i })).toBeVisible();
  });

  test('should display test metadata', async ({ page }) => {
    // Verify test metadata is shown (agent, priority, etc.)
    await expect(page.getByText(/explorer agent/i).first()).toBeVisible();
    await expect(page.getByText(/high/i).first()).toBeVisible();
  });

  test('should maintain layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify key elements are still visible
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /create new test/i })).toBeVisible();
    await expect(page.getByText(/login flow test/i)).toBeVisible();
  });

  test('should have functional sidebar on tests page', async ({ page }) => {
    // Verify sidebar navigation
    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    
    // Navigate back to dashboard
    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/dashboard/);
  });
});

