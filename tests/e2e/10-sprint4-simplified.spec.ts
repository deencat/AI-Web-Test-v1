import { test, expect } from '@playwright/test';

/**
 * Sprint 4: Simplified Version Control Tests
 * Tests the actual implemented features on test detail page
 */
test.describe('Sprint 4: Version Control - Simplified', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    
    // Navigate directly to test #100
    await page.goto('/tests/100');
    await page.waitForLoadState('networkidle');
  });

  test('should display test detail page', async ({ page }) => {
    // Verify test title is visible
    await expect(page.getByRole('heading', { name: /login flow test/i })).toBeVisible();
    
    // Verify test ID
    await expect(page.getByText(/#100/)).toBeVisible();
    
    // Verify Test Information section
    await expect(page.getByRole('heading', { name: /test information/i })).toBeVisible();
  });

  test('should display View History button', async ({ page }) => {
    // Verify View History button is present
    const viewHistoryButton = page.getByRole('button', { name: /view history/i });
    await expect(viewHistoryButton).toBeVisible();
  });

  test('should display test steps section', async ({ page }) => {
    // Verify Test Steps heading
    await expect(page.getByRole('heading', { name: /test steps/i })).toBeVisible();
    
    // Verify there's a textarea for editing steps
    const textarea = page.locator('textarea').first();
    await expect(textarea).toBeVisible();
  });

  test('should open version history panel', async ({ page }) => {
    // Click View History button
    await page.getByRole('button', { name: /view history/i }).click();
    
    // Wait for panel to appear
    await page.waitForTimeout(500);
    
    // Verify version history panel is visible
    // Look for "Version History" heading or close button
    const versionHistoryHeading = page.getByRole('heading', { name: /version history/i });
    await expect(versionHistoryHeading).toBeVisible({ timeout: 5000 });
  });

  test('should edit test steps', async ({ page }) => {
    // Find the textarea
    const textarea = page.locator('textarea').first();
    await expect(textarea).toBeVisible();
    
    // Get current content
    const originalContent = await textarea.inputValue();
    
    // Edit the content
    await textarea.click();
    await textarea.fill(originalContent + '\nNew test step added');
    
    // Wait for auto-save (2 seconds debounce + save time)
    await page.waitForTimeout(3000);
    
    // Look for "Saved" indicator
    const savedIndicator = page.getByText(/saved/i);
    await expect(savedIndicator).toBeVisible({ timeout: 5000 });
  });

  test('should show version history with versions', async ({ page }) => {
    // Open version history
    await page.getByRole('button', { name: /view history/i }).click();
    await page.waitForTimeout(1000);
    
    // Verify the Version History heading is visible (confirms panel opened)
    const versionHistoryHeading = page.getByRole('heading', { name: /version history/i });
    await expect(versionHistoryHeading).toBeVisible({ timeout: 5000 });
    
    // Verify the panel shows test ID and current version
    await expect(page.getByText(/test case #100/i)).toBeVisible();
    await expect(page.getByText(/current: v/i)).toBeVisible();
    
    // Panel is working - test passes!
  });

  test('should close version history panel', async ({ page }) => {
    // Open version history
    await page.getByRole('button', { name: /view history/i }).click();
    await page.waitForTimeout(500);
    
    // Click close button using specific aria-label
    const closeButton = page.locator('button[aria-label="Close panel"]');
    await expect(closeButton).toBeVisible();
    await closeButton.click();
    
    // Wait for panel to close
    await page.waitForTimeout(500);
    
    // Verify panel is no longer visible
    const versionHistoryHeading = page.getByRole('heading', { name: /version history/i });
    await expect(versionHistoryHeading).not.toBeVisible();
  });
});
