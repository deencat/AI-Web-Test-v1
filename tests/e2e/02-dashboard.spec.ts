import { test, expect } from '@playwright/test';

/**
 * Dashboard Page Tests
 * Tests the main dashboard with mock data
 * Design Mode: Frontend only with dummy JSON
 */

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to root and login
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
  });

  test('should display dashboard with statistics', async ({ page }) => {
    // Verify dashboard heading
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    
    // Verify statistics cards are visible - use more specific selectors
    await expect(page.getByText(/total tests/i).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    
    // Check for stat cards by looking for the emoji icons (use first() to handle duplicates in header)
    await expect(page.getByText('📊')).toBeVisible();
    await expect(page.getByText('✅')).toBeVisible();
    await expect(page.getByText('❌')).toBeVisible();
    await expect(page.getByText('🤖').first()).toBeVisible();
  });

  test('should display mock statistics numbers', async ({ page }) => {
    // Verify mock data is displayed - just check the section exists
    await expect(page.getByText(/total tests/i).first()).toBeVisible();
    
    // Check that numbers are displayed (our mock has 156 total tests)
    await expect(page.getByText('156')).toBeVisible();
  });

  test('should display recent test results', async ({ page }) => {
    // Verify recent tests section
    await expect(page.getByRole('heading', { name: /recent test results/i })).toBeVisible();
    
    // Verify at least one test is listed (mock data has 3 tests)
    const testItems = page.locator('div').filter({ hasText: /test/i }).first();
    await expect(testItems).toBeVisible();
  });

  test('should show agent activity section', async ({ page }) => {
    // Verify agent activity section exists
    await expect(page.getByRole('heading', { name: /agent activity/i })).toBeVisible();
  });

  test('should have functional header with user info', async ({ page }) => {
    // Verify header elements
    await expect(page.getByText(/AI Web Test/i)).toBeVisible();
    await expect(page.getByText(/admin/i)).toBeVisible();
  });

  test('should have functional sidebar navigation', async ({ page }) => {
    // Verify sidebar links
    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /tests/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /knowledge base/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
  });

  test('should navigate to Tests page from sidebar', async ({ page }) => {
    // Click Tests link in sidebar
    await page.getByRole('link', { name: /^tests$/i }).click();
    
    // Verify navigation
    await page.waitForURL('**/tests');
    await expect(page).toHaveURL(/tests/);
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
  });

  test('should navigate to Knowledge Base page from sidebar', async ({ page }) => {
    // Click Knowledge Base link in sidebar
    await page.getByRole('link', { name: /knowledge base/i }).click();
    
    // Verify navigation
    await page.waitForURL('**/knowledge-base');
    await expect(page).toHaveURL(/knowledge-base/);
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();
  });

  test('should navigate to Settings page from sidebar', async ({ page }) => {
    // Click Settings link in sidebar
    await page.getByRole('link', { name: /settings/i }).click();
    
    // Verify navigation
    await page.waitForURL('**/settings');
    await expect(page).toHaveURL(/settings/);
    await expect(page.getByRole('heading', { name: /settings/i }).first()).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify dashboard is still functional
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByText(/total tests/i)).toBeVisible();
  });
});

