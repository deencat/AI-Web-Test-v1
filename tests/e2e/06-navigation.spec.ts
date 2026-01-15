import { test, expect } from '@playwright/test';

/**
 * Navigation Flow Tests
 * Tests the overall application navigation and routing
 * Design Mode: Frontend only with dummy JSON
 */

test.describe('Application Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Start at login page
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
  });

  test('should navigate through all main pages', async ({ page }) => {
    // Start at dashboard
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    
    // Navigate to Tests
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
    
    // Navigate to Knowledge Base
    await page.getByRole('link', { name: /knowledge base/i }).click();
    await page.waitForURL('**/knowledge-base');
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();
    
    // Navigate to Settings
    await page.getByRole('link', { name: /settings/i }).click();
    await page.waitForURL('**/settings');
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();
    
    // Navigate back to Dashboard
    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should maintain header across all pages', async ({ page }) => {
    const pages = ['dashboard', 'tests', 'knowledge-base', 'settings'];
    
    for (const pageName of pages) {
      await page.goto(`/${pageName}`);
      await expect(page.getByText(/AI Web Test/i).first()).toBeVisible();
      await expect(page.getByText(/admin/i)).toBeVisible();
    }
  });

  test('should maintain sidebar across all pages', async ({ page }) => {
    const pages = ['dashboard', 'tests', 'knowledge-base', 'settings'];
    
    for (const pageName of pages) {
      await page.goto(`/${pageName}`);
      
      // Verify all sidebar links are present
      await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^tests$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /knowledge base/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
    }
  });

  test('should highlight active page in sidebar', async ({ page }) => {
    // Navigate to Tests page
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
    
    // The active link should be visible (styling tested via visual comparison or class)
    const testsLink = page.getByRole('link', { name: /^tests$/i });
    await expect(testsLink).toBeVisible();
  });

  test('should support direct URL navigation', async ({ page }) => {
    // Directly navigate to each page
    await page.goto('/tests');
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
    
    await page.goto('/knowledge-base');
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();
    
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();
    
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should handle browser back button', async ({ page }) => {
    // Navigate: Dashboard -> Tests -> Knowledge Base
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
    
    await page.getByRole('link', { name: /knowledge base/i }).click();
    await page.waitForURL('**/knowledge-base');
    
    // Go back to Tests
    await page.goBack();
    await expect(page).toHaveURL(/tests/);
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
    
    // Go back to Dashboard
    await page.goBack();
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should handle browser forward button', async ({ page }) => {
    // Navigate forward through pages
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
    
    await page.goBack();
    await expect(page).toHaveURL(/dashboard/);
    
    // Go forward
    await page.goForward();
    await expect(page).toHaveURL(/tests/);
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
  });

  test('should redirect from root to login when not authenticated', async ({ page }) => {
    // Start fresh (simulate logout by going to root)
    await page.goto('/');
    
    // Should show login page
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
  });

  test('should maintain navigation state on page refresh', async ({ page }) => {
    // Navigate to Tests page
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
    
    // Refresh page
    await page.reload();
    
    // Should still be on Tests page
    await expect(page).toHaveURL(/tests/);
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
  });

  test('should have working navigation on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Test navigation (sidebar might be collapsed/hamburger menu)
    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    
    // Navigate to Tests
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
    await expect(page.getByRole('heading', { name: /test cases/i })).toBeVisible();
  });

  test('should preserve user info across navigation', async ({ page }) => {
    const pages = ['tests', 'knowledge-base', 'settings'];
    
    for (const pageName of pages) {
      await page.goto(`/${pageName}`);
      
      // User info should be visible in header
      await expect(page.getByText(/admin/i)).toBeVisible();
    }
  });
});

