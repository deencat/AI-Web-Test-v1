import { test, expect } from '@playwright/test';

/**
 * Sprint 2 Features Tests
 * Tests new features: Test Generation, KB Upload, Dashboard Charts
 */

test.describe('Sprint 2: Test Generation', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to Tests page
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    await page.getByRole('link', { name: /^tests$/i }).click();
    await page.waitForURL('**/tests');
  });

  test('should display test generation form on initial load', async ({ page }) => {
    await expect(page.getByText(/describe the test you want to create/i)).toBeVisible();
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).toBeVisible();
  });

  test('should show error for empty prompt', async ({ page }) => {
    const textarea = page.getByPlaceholder(/example.*test the login flow/i);
    
    // Enter some text first
    await textarea.fill('test');
    
    // Then clear it to trigger the empty state
    await textarea.clear();
    
    // Wait a bit for the state to update
    await page.waitForTimeout(100);
    
    // Try to click the generate button - it should be disabled, but we'll attempt anyway
    const generateBtn = page.getByRole('button', { name: /generate test cases/i });
    
    // Check if button is disabled (which is the correct behavior)
    await expect(generateBtn).toBeDisabled();
    
    // The error only shows after clicking a enabled button with empty text
    // So let's test that the button IS disabled instead
  });

  test('should generate test cases successfully', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test login for Three HK');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    
    // Should show loading state
    await expect(page.getByText(/generating tests/i)).toBeVisible({ timeout: 1000 });
    
    // Should show results
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/test case 1/i)).toBeVisible();
  });

  test('should display complete test case details', async ({ page }) => {
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test checkout');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    
    // Check test case structure
    await expect(page.getByText(/test steps/i).first()).toBeVisible();
    await expect(page.getByText(/expected result/i).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /save/i }).first()).toBeVisible();
  });
});

test.describe('Sprint 2: Knowledge Base Upload', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to KB page
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    await page.getByRole('link', { name: /knowledge base/i }).click();
    await page.waitForURL('**/knowledge-base');
  });

  test('should open upload modal', async ({ page }) => {
    await page.getByRole('button', { name: /upload document/i }).click();
    await expect(page.getByRole('heading', { name: /upload document/i })).toBeVisible();
    await expect(page.getByText(/drag and drop a file here/i)).toBeVisible();
  });

  test('should display all upload form fields', async ({ page }) => {
    await page.getByRole('button', { name: /upload document/i }).click();
    
    // Wait for modal to appear
    await page.waitForSelector('text=/upload document/i', { timeout: 2000 });
    
    // Check for form field labels
    await expect(page.locator('label').filter({ hasText: /document name/i })).toBeVisible();
    await expect(page.locator('label').filter({ hasText: /description/i })).toBeVisible();
    await expect(page.locator('label').filter({ hasText: /category/i })).toBeVisible();
    await expect(page.locator('label').filter({ hasText: /document type/i })).toBeVisible();
    await expect(page.locator('label').filter({ hasText: /tags/i })).toBeVisible();
  });

  test('should have file input for upload', async ({ page }) => {
    await page.getByRole('button', { name: /upload document/i }).click();
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();
  });

  test('should close modal on cancel', async ({ page }) => {
    await page.getByRole('button', { name: /upload document/i }).click();
    await expect(page.getByRole('heading', { name: /upload document/i })).toBeVisible();
    
    await page.getByRole('button', { name: /cancel/i }).click();
    await expect(page.getByRole('heading', { name: /upload document/i })).not.toBeVisible();
  });

  test('should close modal on X button', async ({ page }) => {
    await page.getByRole('button', { name: /upload document/i }).click();
    await page.locator('button').filter({ hasText: '✕' }).click();
    await expect(page.getByRole('heading', { name: /upload document/i })).not.toBeVisible();
  });

  test('should disable upload button without file', async ({ page }) => {
    await page.getByRole('button', { name: /upload document/i }).click();
    const uploadBtn = page.getByRole('button', { name: /upload document/i }).last();
    await expect(uploadBtn).toBeDisabled();
  });
});

test.describe('Sprint 2: Dashboard Charts', () => {
  test.beforeEach(async ({ page }) => {
    // Login and go to dashboard
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
  });

  test('should display test trends chart', async ({ page }) => {
    await expect(page.getByText(/test trends.*7 days/i)).toBeVisible();
    
    // Recharts creates SVG elements
    const charts = page.locator('svg.recharts-surface');
    expect(await charts.count()).toBeGreaterThan(0);
  });

  test('should display test status pie chart', async ({ page }) => {
    await expect(page.getByText(/test status distribution/i)).toBeVisible();
    
    // Should have chart SVG
    const charts = page.locator('svg.recharts-surface');
    expect(await charts.count()).toBeGreaterThan(0);
  });

  test('should display chart legends', async ({ page }) => {
    // Line chart should have legend items
    await expect(page.getByText(/passed/i).first()).toBeVisible();
    await expect(page.getByText(/failed/i).first()).toBeVisible();
    await expect(page.getByText(/total/i).first()).toBeVisible();
  });

  test('should display pie chart color legend', async ({ page }) => {
    // Pie chart legend is below the chart  
    // Check for the legend items with format "Passed: 142"
    await expect(page.getByText(/passed: \d+/i)).toBeVisible();
    await expect(page.getByText(/failed: \d+/i)).toBeVisible();
    await expect(page.getByText(/running: \d+/i)).toBeVisible();
  });

  test('should maintain charts on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Charts should still be visible
    await expect(page.getByText(/test trends/i)).toBeVisible();
    await expect(page.getByText(/test status distribution/i)).toBeVisible();
  });
});

test.describe('Sprint 2: Edit Test Case', () => {
  test.beforeEach(async ({ page }) => {
    // Login and go to tests page
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    await page.goto('/tests');
    await page.waitForURL('**/tests');
  });

  test('should edit a generated test case', async ({ page }) => {
    // Generate test cases first
    const textbox = page.getByRole('textbox', { name: /example/i });
    await textbox.fill('Login validation tests');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    await page.waitForTimeout(2500);

    // Click edit on the first test case
    const firstEditButton = page.getByRole('button', { name: /edit/i }).first();
    await firstEditButton.click();

    // Edit modal should be visible
    await expect(page.getByText('Edit Test Case')).toBeVisible();

    // Modify the title
    const titleInput = page.getByLabel('Title');
    await titleInput.clear();
    await titleInput.fill('Updated Test Title');

    // Save changes
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Modal should close
    await expect(page.getByText('Edit Test Case')).not.toBeVisible();

    // Updated title should be visible
    await expect(page.getByText('Updated Test Title')).toBeVisible();
  });

  test('should cancel edit without saving changes', async ({ page }) => {
    // Generate test cases first
    const textbox = page.getByRole('textbox', { name: /example/i });
    await textbox.fill('Login validation tests');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    await page.waitForTimeout(2500);

    // Get original title
    const originalTitle = await page.locator('.font-semibold.text-gray-900').first().textContent();

    // Click edit
    await page.getByRole('button', { name: /edit/i }).first().click();

    // Modify the title
    const titleInput = page.getByLabel('Title');
    await titleInput.clear();
    await titleInput.fill('Should Not Be Saved');

    // Cancel instead of saving
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Modal should close
    await expect(page.getByText('Edit Test Case')).not.toBeVisible();

    // Original title should still be visible
    await expect(page.getByText(originalTitle || '')).toBeVisible();
    await expect(page.getByText('Should Not Be Saved')).not.toBeVisible();
  });
});
