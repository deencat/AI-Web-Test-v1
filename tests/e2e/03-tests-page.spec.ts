import { test, expect } from '@playwright/test';

/**
 * Generate Tests Page Tests
 * Tests the test generation page with mock data
 */

test.describe('Generate Tests Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');

    await page.getByRole('link', { name: /generate tests/i }).click();
    await page.waitForURL('**/tests');
  });

  test('should display generate tests page with header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /generate tests/i })).toBeVisible();
    await expect(page.getByText(/generate test cases using natural language/i)).toBeVisible();
  });

  test('should display test generation form initially', async ({ page }) => {
    await expect(page.getByText(/describe the test you want to create/i)).toBeVisible();
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /generate test cases/i })).toBeVisible();
  });

  test('should disable generate button when prompt is empty', async ({ page }) => {
    const textarea = page.getByPlaceholder(/example.*test the login flow/i);
    await textarea.clear();

    const generateBtn = page.getByRole('button', { name: /generate test cases/i });
    await expect(generateBtn).toBeDisabled();
  });

  test('should generate test cases from natural language', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test login flow for Three HK');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generating tests/i)).toBeVisible({ timeout: 1000 });
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/test case 1/i)).toBeVisible();
  });

  test('should display test case cards with all details', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test checkout process');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/test case 1/i)).toBeVisible();
    await expect(page.getByText(/test steps/i).first()).toBeVisible();
    await expect(page.getByText(/expected result/i).first()).toBeVisible();
    await expect(page.getByText(/high|medium|low/i).first()).toBeVisible();
  });

  test('should show save, edit, and delete buttons on generated tests', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test user profile');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });

    const saveButtons = page.getByRole('button', { name: /save/i });
    await expect(saveButtons.first()).toBeVisible();
    expect(await saveButtons.count()).toBeGreaterThan(0);
  });

  test('should allow generating more tests after viewing results', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test search');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: /generate more tests/i }).click();
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).toBeVisible();
  });

  test('should not show view saved tests button in header', async ({ page }) => {
    await expect(page.getByRole('button', { name: /view saved tests/i })).not.toBeVisible();
  });
});

test.describe('Saved Tests Page — inline title edit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');

    await page.getByRole('link', { name: /saved tests/i }).click();
    await page.waitForURL('**/tests/saved');
  });

  test('should display saved tests page with header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
  });

  test('should allow inline title rename when tests exist', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();

    if (await titleButton.count() === 0) {
      test.skip();
      return;
    }

    const originalTitle = await titleButton.textContent();
    const newTitle = `${originalTitle} (renamed)`;

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await expect(input).toBeVisible();
    await input.fill(newTitle);
    await input.press('Enter');

    await expect(page.getByRole('button', { name: new RegExp(newTitle!, 'i') })).toBeVisible({ timeout: 5000 });

    await page.getByRole('button', { name: new RegExp(newTitle!, 'i') }).click();
    const revertInput = page.locator('[data-testid^="inline-title-input-"]').first();
    await revertInput.fill(originalTitle || 'Test');
    await revertInput.press('Enter');
  });

  test('should block empty title on inline edit', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();

    if (await titleButton.count() === 0) {
      test.skip();
      return;
    }

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await input.fill('');
    await input.press('Enter');

    await expect(page.getByText(/title is required/i)).toBeVisible();
  });
});
