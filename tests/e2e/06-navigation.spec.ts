import { test, expect } from '@playwright/test';
import { loginAsAdmin, seedSavedTest, waitForSavedTestsList } from './helpers/auth';

/**
 * Navigation Flow Tests
 * Tests the overall application navigation and routing
 */

test.describe('Application Navigation', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeAll(async ({ request }) => {
    await seedSavedTest(request);
  });

  test.beforeEach(async ({ page, request }) => {
    await loginAsAdmin(page, request);
  });

  test('should navigate through all main pages', async ({ page }) => {
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();

    await page.getByRole('link', { name: /saved tests/i }).click();
    await page.waitForURL('**/tests/saved');
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();

    await page.getByRole('link', { name: /knowledge base/i }).click();
    await page.waitForURL('**/knowledge-base');
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();

    await page.getByRole('link', { name: /settings/i }).click();
    await page.waitForURL('**/settings');
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();

    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should maintain header across all pages', async ({ page }) => {
    const pages = ['dashboard', 'tests', 'tests/saved', 'knowledge-base', 'settings'];

    for (const pageName of pages) {
      await page.goto(`/${pageName}`);
      await expect(page.getByText(/Agentic QA/i).first()).toBeVisible();
      await expect(page.getByText(/admin/i)).toBeVisible();
    }
  });

  test('should maintain sidebar across all pages', async ({ page }) => {
    const pages = ['dashboard', 'tests', 'tests/saved', 'knowledge-base', 'settings'];

    for (const pageName of pages) {
      await page.goto(`/${pageName}`);

      await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /generate tests/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /saved tests/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /knowledge base/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
    }
  });

  test('should highlight active generate tests link', async ({ page }) => {
    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');

    const generateLink = page.getByRole('link', { name: /generate tests/i });
    await expect(generateLink).toBeVisible();
    await expect(generateLink).toHaveClass(/bg-blue-700/);
  });

  test('should highlight active saved tests link', async ({ page }) => {
    await page.getByRole('link', { name: /saved tests/i }).click();
    await page.waitForURL('**/tests/saved');

    const savedLink = page.getByRole('link', { name: /saved tests/i });
    await expect(savedLink).toBeVisible();
    await expect(savedLink).toHaveClass(/bg-blue-700/);
  });

  test('should support direct URL navigation', async ({ page }) => {
    await page.goto('/tests');
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();

    await page.goto('/tests/saved');
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();

    await page.goto('/knowledge-base');
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();

    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();

    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should redirect legacy /tests?edit= URLs to saved tests', async ({ page }) => {
    await page.goto('/tests?edit=1');
    await page.waitForURL('**/tests/saved?edit=1');
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
  });

  test('should open edit drawer on saved tab via legacy redirect', async ({ page }) => {
    await page.goto('/tests/saved');
    await waitForSavedTestsList(page);
    const testId = await page
      .locator('[data-testid^="inline-title-button-"]')
      .first()
      .getAttribute('data-testid');
    const id = testId?.replace('inline-title-button-', '');
    expect(id).toBeTruthy();

    await page.goto(`/tests?edit=${id}`);
    await page.waitForURL(new RegExp(`/tests/saved\\?edit=${id}`));
    await expect(page.getByRole('heading', { name: /edit test case/i })).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByRole('heading', { name: /generate tests/i })).not.toBeVisible();
  });

  test('should keep generate and saved tests as separate routes', async ({ page }) => {
    await page.goto('/tests');
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();
    await expect(page.locator('[data-testid^="inline-title-button-"]')).toHaveCount(0);
    await expect(page.getByText(/showing \d+ of \d+ test/i)).not.toBeVisible();

    await page.goto('/tests/saved');
    await waitForSavedTestsList(page);
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).not.toBeVisible();
  });

  test('should handle browser back button', async ({ page }) => {
    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');

    await page.getByRole('link', { name: /knowledge base/i }).click();
    await page.waitForURL('**/knowledge-base');

    await page.goBack();
    await expect(page).toHaveURL(/tests$/);
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();

    await page.goBack();
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should handle browser forward button', async ({ page }) => {
    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');

    await page.goBack();
    await expect(page).toHaveURL(/dashboard/);

    await page.goForward();
    await expect(page).toHaveURL(/tests$/);
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();
  });

  test('should redirect from root to login when not authenticated', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    });
    await page.goto('/');
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
  });

  test('should maintain navigation state on page refresh', async ({ page }) => {
    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');

    await page.reload();

    await expect(page).toHaveURL(/tests$/);
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();
  });

  test('should have working navigation on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();

    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();

    await page.getByRole('link', { name: /saved tests/i }).click();
    await page.waitForURL('**/tests/saved');
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
  });

  test('should preserve user info across navigation', async ({ page }) => {
    const pages = ['tests', 'tests/saved', 'knowledge-base', 'settings'];

    for (const pageName of pages) {
      await page.goto(`/${pageName}`);
      await expect(page.getByText(/admin/i)).toBeVisible();
    }
  });
});
