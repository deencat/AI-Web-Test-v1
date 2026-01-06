import { test, expect } from '@playwright/test';

/**
 * Sprint 4: Test Version Control E2E Tests
 * Tests the complete version control workflow:
 * - Test editing with auto-save
 * - Version history viewing
 * - Version comparison
 * - Rollback functionality
 */

test.describe('Sprint 4: Test Version Control', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    
    // Navigate directly to test #100 (the test we created)
    await page.goto('/tests/100');
    await page.waitForLoadState('networkidle');
    
    // Wait for page to fully load
    await page.waitForTimeout(1000);
  });

  test('should display test detail page with version number', async ({ page }) => {
    // Verify test detail page loaded (checks for test title which is in h1)
    await expect(page.getByRole('heading', { name: /Login Flow Test/i })).toBeVisible();
    
    // Verify version number is displayed in the Test Steps label (e.g., "Test Steps (v1)")
    await expect(page.getByText(/Test Steps.*\(v\d+\)/i)).toBeVisible();
  });

  test('should show test step editor with editable steps', async ({ page }) => {
    // Verify test step editor is displayed
    const stepEditor = page.locator('.test-step-editor');
    await expect(stepEditor).toBeVisible();
    
    // Verify textarea for steps is editable
    const textarea = stepEditor.locator('textarea');
    await expect(textarea).toBeVisible();
    await expect(textarea).toBeEditable();
  });

  test('should auto-save when editing test steps', async ({ page }) => {
    // Find the textarea in test step editor
    const textarea = page.locator('.test-step-editor textarea');
    await expect(textarea).toBeVisible();
    
    // Get current content and add new text
    const currentText = await textarea.inputValue();
    await textarea.fill(currentText + '\nUpdated test step for version control testing');
    
    // Wait for auto-save (2 second debounce + processing)
    await page.waitForTimeout(3000);
    
    // Verify save indicator appears
    await expect(page.getByText(/Saving|Saved/)).toBeVisible({ timeout: 5000 });
  });

  test('should open version history panel', async ({ page }) => {
    // Find and click "View History" button
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await expect(versionHistoryBtn).toBeVisible();
    await versionHistoryBtn.click();
    
    // Verify version history panel opens with heading
    await expect(page.getByRole('heading', { name: 'Version History' })).toBeVisible({ timeout: 3000 });
    
    // Verify version list is displayed
    const versionList = page.locator('.version-item');
    await expect(versionList.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display version list with version numbers', async ({ page }) => {
    // Open version history
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await expect(versionHistoryBtn).toBeVisible();
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    // Verify at least one version is displayed
    const versions = page.locator('.version-item');
    const versionCount = await versions.count();
    expect(versionCount).toBeGreaterThan(0);
    
    // Verify version number is displayed
    await expect(versions.first()).toContainText(/v\d+|version \d+/i);
  });

  test('should allow selecting two versions for comparison', async ({ page }) => {
    // Open version history
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    // Find version checkboxes
    const versionCheckboxes = page.locator('input[type="checkbox"]');
    const checkboxCount = await versionCheckboxes.count();
    expect(checkboxCount).toBeGreaterThanOrEqual(2);
    
    // Select first two versions
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    // Verify compare button is enabled
    const compareBtn = page.getByRole('button', { name: /Compare/i });
    await expect(compareBtn).toBeEnabled();
  });

  test('should open version comparison dialog', async ({ page }) => {
    // Open version history
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    // Select two versions and click compare
    const versionCheckboxes = page.locator('input[type="checkbox"]');
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    const compareBtn = page.getByRole('button', { name: /Compare/i });
    await compareBtn.click();
    
    // Verify comparison dialog opens
    await expect(page.getByRole('heading', { name: /Compare Versions/i })).toBeVisible({ timeout: 3000 });
  });

  test('should display diff highlighting in comparison', async ({ page }) => {
    // Open version history and compare
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    const versionCheckboxes = page.locator('input[type="checkbox"]');
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    const compareBtn = page.getByRole('button', { name: /Compare/i });
    await compareBtn.click();
    await page.waitForTimeout(1000);
    
    // Verify comparison dialog is visible
    await expect(page.getByRole('heading', { name: /Compare Versions/i })).toBeVisible();
    
    // Verify diff content areas exist (two text areas for side-by-side comparison)
    const diffAreas = page.locator('textarea[readonly], pre');
    const diffCount = await diffAreas.count();
    expect(diffCount).toBeGreaterThan(0);
  });

  test('should close comparison dialog', async ({ page }) => {
    // Open version history and compare
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    const versionCheckboxes = page.locator('input[type="checkbox"]');
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    const compareBtn = page.getByRole('button', { name: /Compare/i });
    await compareBtn.click();
    await page.waitForTimeout(1000);
    
    // Verify dialog is open
    await expect(page.getByRole('heading', { name: /Compare Versions/i })).toBeVisible();
    
    // Press Escape to close
    await page.keyboard.press('Escape');
    
    // Verify dialog is closed
    await expect(page.getByRole('heading', { name: /Compare Versions/i })).not.toBeVisible({ timeout: 2000 });
  });

  test('should show rollback button for versions', async ({ page }) => {
    // Open version history
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    // Find rollback buttons (should be on each version item except current)
    const rollbackBtns = page.getByRole('button', { name: /Rollback|Revert/i });
    const rollbackCount = await rollbackBtns.count();
    expect(rollbackCount).toBeGreaterThan(0);
    
    // Verify rollback button is visible
    await expect(rollbackBtns.first()).toBeVisible();
  });

  test('should open rollback confirmation dialog', async ({ page }) => {
    // Open version history
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    // Click first rollback button
    const rollbackBtns = page.getByRole('button', { name: /Rollback|Revert/i });
    await rollbackBtns.first().click();
    
    // Verify confirmation dialog opens with heading
    await expect(page.getByRole('heading', { name: /Confirm Rollback/i })).toBeVisible({ timeout: 3000 });
    
    // Verify reason textarea is present using label
    const reasonField = page.getByRole('textbox', { name: /Reason for Rollback/i });
    await expect(reasonField).toBeVisible();
  });

  test('should require reason for rollback', async ({ page }) => {
    // Open version history and click rollback
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    const rollbackBtns = page.getByRole('button', { name: /Rollback|Revert/i });
    await rollbackBtns.first().click();
    await page.waitForTimeout(1000);
    
    // Find confirm button
    const confirmBtn = page.getByRole('button', { name: /Confirm Rollback|Confirm/i });
    
    // Verify confirm button is disabled when reason is empty
    await expect(confirmBtn).toBeDisabled();
    
    // Fill in reason using the specific textbox for rollback reason
    const reasonInput = page.getByRole('textbox', { name: /Reason for Rollback/i });
    await reasonInput.fill('E2E test rollback reason');
    
    // Verify confirm button is now enabled
    await expect(confirmBtn).toBeEnabled();
  });

  test('should close rollback dialog without confirming', async ({ page }) => {
    // Open version history and click rollback
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    const rollbackBtns = page.getByRole('button', { name: /Rollback|Revert/i });
    await rollbackBtns.first().click();
    await page.waitForTimeout(1000);
    
    // Verify dialog is open
    await expect(page.getByRole('heading', { name: /Confirm Rollback/i })).toBeVisible();
    
    // Click cancel button
    const cancelBtn = page.getByRole('button', { name: /Cancel/i });
    await cancelBtn.click();
    
    // Verify dialog is closed
    await expect(page.getByRole('heading', { name: /Confirm Rollback/i })).not.toBeVisible({ timeout: 2000 });
  });

  test('should display version metadata in history', async ({ page }) => {
    // Open version history
    const versionHistoryBtn = page.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await page.waitForTimeout(1000);
    
    // Verify version metadata is displayed (created date, created by, etc.)
    const versionItems = page.locator('.version-item');
    const itemCount = await versionItems.count();
    expect(itemCount).toBeGreaterThan(0);
    
    const firstVersion = versionItems.first();
    
    // Check for common metadata fields (dates, timestamps, etc.)
    const hasMetadata = await firstVersion.locator('text=/\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|ago|created|modified/i').count();
    expect(hasMetadata).toBeGreaterThan(0);
  });
});

