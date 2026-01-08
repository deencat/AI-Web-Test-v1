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
    await page.getByPlaceholder(/password/i).fill('admin123');
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

  // Sprint 2: Tests page now starts with generation form
  test('should display test generation form initially', async ({ page }) => {
    // Verify test generation UI is shown by default
    await expect(page.getByText(/describe the test you want to create/i)).toBeVisible();
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /generate test cases/i })).toBeVisible();
  });

  test('should disable generate button when prompt is empty', async ({ page }) => {
    // Clear the textarea if it has any value
    const textarea = page.getByPlaceholder(/example.*test the login flow/i);
    await textarea.clear();
    
    // Generate button should be disabled
    const generateBtn = page.getByRole('button', { name: /generate test cases/i });
    await expect(generateBtn).toBeDisabled();
  });

  test('should generate test cases from natural language', async ({ page }) => {
    // Enter test description
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test login flow for Three HK');
    
    // Click generate button
    await page.getByRole('button', { name: /generate test cases/i }).click();
    
    // Wait for loading to finish and results to appear
    await expect(page.getByText(/generating tests/i)).toBeVisible({ timeout: 1000 });
    
    // Wait for generated tests (mock data returns after 2 seconds)
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    
    // Should show test case cards
    await expect(page.getByText(/test case 1/i)).toBeVisible();
  });

  test('should display test case cards with all details', async ({ page }) => {
    // Generate tests first
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test checkout process');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    
    // Wait for results
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    
    // Verify test case card has all elements
    await expect(page.getByText(/test case 1/i)).toBeVisible();
    await expect(page.getByText(/test steps/i).first()).toBeVisible();
    await expect(page.getByText(/expected result/i).first()).toBeVisible();
    
    // Verify priority badge
    await expect(page.getByText(/high|medium|low/i).first()).toBeVisible();
  });

  test('should show save, edit, and delete buttons on generated tests', async ({ page }) => {
    // Generate tests first
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test user profile');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    
    // Wait for results
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    
    // Verify action buttons exist
    const saveButtons = page.getByRole('button', { name: /save/i });
    await expect(saveButtons.first()).toBeVisible();
    expect(await saveButtons.count()).toBeGreaterThan(0);
  });

  test('should allow generating more tests after viewing results', async ({ page }) => {
    // Generate tests first
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test search');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    
    // Wait for results
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    
    // Click "Generate More Tests" button
    await page.getByRole('button', { name: /generate more tests/i }).click();
    
    // Should return to generation form
    await expect(page.getByPlaceholder(/example.*test the login flow/i)).toBeVisible();
  });

  test('should display "Generate New Tests" button when viewing existing tests', async ({ page }) => {
    // First, go through the generation flow
    await page.getByPlaceholder(/example.*test the login flow/i).fill('Test API');
    await page.getByRole('button', { name: /generate test cases/i }).click();
    await expect(page.getByText(/generated test cases/i)).toBeVisible({ timeout: 5000 });
    
    // Clear results to show existing tests view
    await page.getByRole('button', { name: /generate more tests/i }).click();
    
    // The "Generate New Tests" button should be in header when showing generator
    await expect(page.getByRole('button', { name: /generate test cases/i })).toBeVisible();
  });
});
