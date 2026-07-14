import { test, expect } from '@playwright/test';
import { loginAsAdmin, waitForSavedTestsList } from './helpers/auth';

/**
 * Generate Tests Page Tests
 * Tests the test generation page with mock data
 */

test.describe('Generate Tests Page', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAsAdmin(page, request);
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
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 120000 });
    await expect(page.getByText(/test case 1/i)).toBeVisible();
  });

  test('should display test case cards with all details', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test checkout process');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 120000 });
    await expect(page.getByText(/test case 1/i)).toBeVisible();
    await expect(page.getByText(/test steps/i).first()).toBeVisible();
    await expect(page.getByText(/expected result/i).first()).toBeVisible();
    await expect(page.getByText(/high|medium|low/i).first()).toBeVisible();
  });

  test('should show save, edit, and delete buttons on generated tests', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test user profile');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 120000 });

    const saveButtons = page.getByRole('button', { name: /save/i });
    await expect(saveButtons.first()).toBeVisible();
    expect(await saveButtons.count()).toBeGreaterThan(0);
  });

  test('should allow generating more tests after viewing results', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test search');
    await page.getByRole('button', { name: /generate test cases/i }).click();

    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 120000 });
    await page.getByRole('button', { name: /generate more tests/i }).click();
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).toBeVisible();
  });

  test('should not show view saved tests button in header', async ({ page }) => {
    await expect(page.getByRole('button', { name: /view saved tests/i })).not.toBeVisible();
  });
});

test.describe('Saved Tests Page — Sprint 1', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeAll(async ({ request }) => {
    const { seedSavedTest } = await import('./helpers/auth');
    await seedSavedTest(request);
  });

  test.beforeEach(async ({ page, request }) => {
    await loginAsAdmin(page, request);
    await page.getByRole('link', { name: /saved tests/i }).click();
    await page.waitForURL('**/tests/saved');
    await waitForSavedTestsList(page);
  });

  test('should display saved tests page with header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
  });

  test('should display saved tests list with rows', async ({ page }) => {
    await expect(page.getByText(/showing \d+ of \d+ test/i)).toBeVisible();
    await expect(page.locator('[data-testid^="row-checkbox-"]').first()).toBeVisible();
    await expect(page.locator('[data-testid^="inline-title-button-"]').first()).toBeVisible();
  });

  test('should allow inline title rename via Enter', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    const testId = await titleButton.getAttribute('data-testid');
    expect(testId).toBeTruthy();

    const originalTitle = (await titleButton.textContent())?.trim() || 'Test';
    const baseTitle = originalTitle.replace(/\s+e2e\s+\d+$/, '').replace(/\s+blur\s+\d+$/, '').slice(0, 200);
    const newTitle = `${baseTitle} e2e ${Date.now()}`;

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await expect(input).toBeVisible();
    await input.fill(newTitle);
    await input.press('Enter');

    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(newTitle, { timeout: 15000 });
    await expect(page.getByText('Edit Test Case')).not.toBeVisible();

    await page.locator(`[data-testid="${testId}"]`).click();
    const revertInput = page.locator('[data-testid^="inline-title-input-"]').first();
    await revertInput.fill(baseTitle);
    await revertInput.press('Enter');
    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(baseTitle, { timeout: 15000 });
  });

  test('should cancel inline title edit with Escape', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    const originalTitle = (await titleButton.textContent())?.trim() || 'Test';

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await input.fill('Temporary Cancel Title');
    await input.press('Escape');

    await expect(input).not.toBeVisible();
    await expect(titleButton).toHaveText(originalTitle);
  });

  test('should enter inline edit via pencil icon', async ({ page }) => {
    const pencil = page.locator('[data-testid^="inline-title-pencil-"]').first();
    await pencil.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await expect(input).toBeVisible();
    await expect(input).toHaveAttribute('aria-label', 'Test title');
    await input.press('Escape');
  });

  test('should block empty title on inline edit', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await input.fill('');
    await input.press('Enter');

    await expect(page.getByText(/title is required/i)).toBeVisible();
    await expect(input).toBeVisible();
  });

  test('should save inline title edit on blur', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    const testId = await titleButton.getAttribute('data-testid');
    expect(testId).toBeTruthy();

    const originalTitle = (await titleButton.textContent())?.trim() || 'Test';
    const baseTitle = originalTitle.replace(/\s+e2e\s+\d+$/, '').replace(/\s+blur\s+\d+$/, '').slice(0, 200);
    const newTitle = `${baseTitle} blur ${Date.now()}`;

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await input.fill(newTitle);
    await page.getByRole('heading', { name: /saved tests/i }).click();

    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(newTitle, { timeout: 15000 });

    await page.locator(`[data-testid="${testId}"]`).click();
    const revertInput = page.locator('[data-testid^="inline-title-input-"]').first();
    await revertInput.fill(baseTitle);
    await revertInput.press('Enter');
    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(baseTitle, { timeout: 15000 });
  });

  test('should navigate back to saved tests from test detail', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    const testId = await titleButton.getAttribute('data-testid');
    const id = testId?.replace('inline-title-button-', '');
    expect(id).toBeTruthy();

    await page.getByTitle('View Details').first().click();
    await page.waitForURL(new RegExp(`/tests/${id}$`));
    await expect(page).toHaveURL(new RegExp(`/tests/${id}$`));

    await page.getByRole('button', { name: /back to saved tests/i }).click();
    await page.waitForURL('**/tests/saved');
    await expect(page).toHaveURL(/\/tests\/saved$/);
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /generate tests/i })).not.toBeVisible();
  });

  test('should revert title when inline save fails with API error', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    const testId = await titleButton.getAttribute('data-testid');
    expect(testId).toBeTruthy();
    const id = testId!.replace('inline-title-button-', '');
    const originalTitle = (await titleButton.textContent())?.trim() || 'Test';

    await page.route(`**/api/v1/tests/${id}`, async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Simulated save failure' }),
        });
      } else {
        await route.continue();
      }
    });

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await input.fill(`Failed Rename ${Date.now()}`);
    await input.press('Enter');

    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(originalTitle, {
      timeout: 15000,
    });
    await expect(page.locator('[data-testid^="inline-title-input-"]')).toHaveCount(0);
  });

  test('should show loading spinner during inline title save', async ({ page }) => {
    const titleButton = page.locator('[data-testid^="inline-title-button-"]').first();
    const testId = await titleButton.getAttribute('data-testid');
    expect(testId).toBeTruthy();
    const id = testId!.replace('inline-title-button-', '');
    const originalTitle = (await titleButton.textContent())?.trim() || 'Test';
    const baseTitle = originalTitle.replace(/\s+spin\s+\d+$/, '').slice(0, 200);
    const newTitle = `${baseTitle} spin ${Date.now()}`;

    await page.route(`**/api/v1/tests/${id}`, async (route) => {
      if (route.request().method() === 'PUT') {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        await route.continue();
      } else {
        await route.continue();
      }
    });

    await titleButton.click();
    const input = page.locator('[data-testid^="inline-title-input-"]').first();
    await input.fill(newTitle);
    await input.press('Enter');

    await expect(page.locator('.animate-spin').first()).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(newTitle, { timeout: 15000 });

    await page.unroute(`**/api/v1/tests/${id}`);
    await page.locator(`[data-testid="${testId}"]`).click();
    const revertInput = page.locator('[data-testid^="inline-title-input-"]').first();
    await revertInput.fill(baseTitle);
    await revertInput.press('Enter');
    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(baseTitle, { timeout: 15000 });
  });

  test('should navigate to saved tests after deleting from test detail', async ({ page, request }) => {
    const title = `E2E Delete Nav ${Date.now()}`;
    const { createDisposableTest } = await import('./helpers/auth');
    const testId = await createDisposableTest(request, title);

    await page.reload();
    await waitForSavedTestsList(page);

    await page.goto(`/tests/${testId}`);
    await page.waitForURL(new RegExp(`/tests/${testId}$`));
    await expect(page).toHaveURL(new RegExp(`/tests/${testId}$`));

    let dialogCount = 0;
    page.on('dialog', async (dialog) => {
      dialogCount++;
      if (dialogCount === 1) {
        expect(dialog.message()).toContain('Are you sure you want to delete');
        await dialog.accept();
      } else if (dialogCount === 2) {
        expect(dialog.message()).toContain('deleted successfully');
        await dialog.accept();
      }
    });

    await page.getByRole('button', { name: /delete test/i }).click();

    await page.waitForURL('**/tests/saved');
    await expect(page).toHaveURL(/\/tests\/saved$/);
    await expect(page.getByRole('heading', { name: /saved tests/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /generate tests/i })).not.toBeVisible();
  });

  test('should open edit drawer via ?edit= query param on saved tab', async ({ page }) => {
    const testId = await page
      .locator('[data-testid^="inline-title-button-"]')
      .first()
      .getAttribute('data-testid');
    const id = testId?.replace('inline-title-button-', '');
    expect(id).toBeTruthy();

    await page.goto(`/tests/saved?edit=${id}`);
    await expect(page).toHaveURL(new RegExp(`/tests/saved\\?edit=${id}`));
    await expect(page.getByRole('heading', { name: /edit test case/i })).toBeVisible({
      timeout: 15000,
    });
    await expect(page.locator('#saved-edit-title')).toBeVisible();
    await page.getByRole('button', { name: /close edit drawer/i }).click();
    await expect(page.getByRole('heading', { name: /edit test case/i })).not.toBeVisible();
  });
});
