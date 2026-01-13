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
  // Shared page for all tests to avoid rate limiting
  let sharedPage;
  let sharedContext;

  test.beforeAll(async ({ browser }) => {
    // Create a persistent context and page for all tests
    sharedContext = await browser.newContext();
    sharedPage = await sharedContext.newPage();
    
    // Navigate and login once
    await sharedPage.goto('/');
    await sharedPage.getByPlaceholder(/username/i).fill('admin');
    await sharedPage.getByPlaceholder(/password/i).fill('admin123');
    await sharedPage.getByRole('button', { name: /sign in/i }).click();
    await sharedPage.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test.afterAll(async () => {
    // Clean up
    if (sharedContext) {
      await sharedContext.close();
    }
  });

  test.beforeEach(async () => {
    // Navigate to test page before each test
    await sharedPage.goto('/tests/100');
    await sharedPage.waitForLoadState('networkidle');
    await sharedPage.waitForTimeout(1000);
  });

  test('should display test detail page with version number', async () => {
    // Verify test detail page loaded (checks for test title which is in h1)
    await expect(sharedPage.getByRole('heading', { name: /Login Flow Test/i })).toBeVisible();
    
    // Verify version number is displayed in the Test Steps label (e.g., "Test Steps (v1)")
    await expect(sharedPage.getByText(/Test Steps.*\(v\d+\)/i)).toBeVisible();
  });

  test('should show test step editor with editable steps', async () => {
    // Verify test step editor is displayed
    const stepEditor = sharedPage.locator('.test-step-editor');
    await expect(stepEditor).toBeVisible();
    
    // Verify textarea for steps is editable
    const textarea = stepEditor.locator('textarea');
    await expect(textarea).toBeVisible();
    await expect(textarea).toBeEditable();
  });

  test('should auto-save when editing test steps', async () => {
    // Find the textarea in test step editor
    const textarea = sharedPage.locator('.test-step-editor textarea');
    await expect(textarea).toBeVisible();
    
    // Get current content and add new text
    const currentText = await textarea.inputValue();
    await textarea.fill(currentText + '\nUpdated test step for version control testing');
    
    // Wait for auto-save (2 second debounce + processing)
    await sharedPage.waitForTimeout(3000);
    
    // Verify save indicator appears
    await expect(sharedPage.getByText(/Saving|Saved/)).toBeVisible({ timeout: 5000 });
  });

  test('should open version history panel', async () => {
    // Find and click "View History" button
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await expect(versionHistoryBtn).toBeVisible();
    await versionHistoryBtn.click();
    
    // Verify version history panel opens with heading
    await expect(sharedPage.getByRole('heading', { name: 'Version History' })).toBeVisible({ timeout: 3000 });
    
    // Verify version list is displayed
    const versionList = sharedPage.locator('.version-item');
    await expect(versionList.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display version list with version numbers', async () => {
    // Open version history
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await expect(versionHistoryBtn).toBeVisible();
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Verify at least one version is displayed
    const versions = sharedPage.locator('.version-item');
    const versionCount = await versions.count();
    expect(versionCount).toBeGreaterThan(0);
    
    // Verify version number is displayed
    await expect(versions.first()).toContainText(/v\d+|version \d+/i);
  });

  test('should allow selecting two versions for comparison', async () => {
    // Open version history
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Find version checkboxes
    const versionCheckboxes = sharedPage.locator('input[type="checkbox"]');
    const checkboxCount = await versionCheckboxes.count();
    expect(checkboxCount).toBeGreaterThanOrEqual(2);
    
    // Select first two versions
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    // Verify compare button is enabled
    const compareBtn = sharedPage.getByRole('button', { name: /Compare/i });
    await expect(compareBtn).toBeEnabled();
  });

  test('should open version comparison dialog', async () => {
    // Open version history
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Select two versions and click compare
    const versionCheckboxes = sharedPage.locator('input[type="checkbox"]');
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    const compareBtn = sharedPage.getByRole('button', { name: /Compare/i });
    await compareBtn.click();
    
    // Verify comparison dialog opens
    await expect(sharedPage.getByRole('heading', { name: /Compare Versions/i })).toBeVisible({ timeout: 3000 });
  });

  test('should display diff highlighting in comparison', async () => {
    // Open version history and compare
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    const versionCheckboxes = sharedPage.locator('input[type="checkbox"]');
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    const compareBtn = sharedPage.getByRole('button', { name: /Compare/i });
    await compareBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Verify comparison dialog is visible
    await expect(sharedPage.getByRole('heading', { name: /Compare Versions/i })).toBeVisible();
    
    // Verify diff content areas exist (span elements with font-mono class displaying steps)
    const diffAreas = sharedPage.locator('span.font-mono');
    const diffCount = await diffAreas.count();
    expect(diffCount).toBeGreaterThan(0);
  });

  test('should close comparison dialog', async () => {
    // Open version history and compare
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    const versionCheckboxes = sharedPage.locator('input[type="checkbox"]');
    await versionCheckboxes.nth(0).check();
    await versionCheckboxes.nth(1).check();
    
    const compareBtn = sharedPage.getByRole('button', { name: /Compare/i });
    await compareBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Verify dialog is open
    await expect(sharedPage.getByRole('heading', { name: /Compare Versions/i })).toBeVisible();
    
    // Press Escape to close
    await sharedPage.keyboard.press('Escape');
    
    // Verify dialog is closed
    await expect(sharedPage.getByRole('heading', { name: /Compare Versions/i })).not.toBeVisible({ timeout: 2000 });
  });

  test('should show rollback button for versions', async () => {
    // Open version history
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Find rollback buttons (should be on each version item except current)
    const rollbackBtns = sharedPage.getByRole('button', { name: /Rollback|Revert/i });
    const rollbackCount = await rollbackBtns.count();
    expect(rollbackCount).toBeGreaterThan(0);
    
    // Verify rollback button is visible
    await expect(rollbackBtns.first()).toBeVisible();
  });

  test('should open rollback confirmation dialog', async () => {
    // Open version history
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Click first rollback button
    const rollbackBtns = sharedPage.getByRole('button', { name: /Rollback|Revert/i });
    await rollbackBtns.first().click();
    
    // Verify confirmation dialog opens with heading
    await expect(sharedPage.getByRole('heading', { name: /Rollback to Version/i })).toBeVisible({ timeout: 3000 });
    
    // Verify reason textarea is present using label
    const reasonField = sharedPage.getByRole('textbox', { name: /Reason for Rollback/i });
    await expect(reasonField).toBeVisible();
  });

  test('should require reason for rollback', async () => {
    // Open version history and click rollback
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    const rollbackBtns = sharedPage.getByRole('button', { name: /Rollback|Revert/i });
    await rollbackBtns.first().click();
    await sharedPage.waitForTimeout(1000);
    
    // Find confirm button
    const confirmBtn = sharedPage.getByRole('button', { name: /Confirm Rollback|Confirm/i });
    
    // Verify confirm button is disabled when reason is empty
    await expect(confirmBtn).toBeDisabled();
    
    // Fill in reason using the specific textbox for rollback reason
    const reasonInput = sharedPage.getByRole('textbox', { name: /Reason for Rollback/i });
    await reasonInput.fill('E2E test rollback reason');
    
    // Verify confirm button is now enabled
    await expect(confirmBtn).toBeEnabled();
  });

  test('should close rollback dialog without confirming', async () => {
    // Open version history and click rollback
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    const rollbackBtns = sharedPage.getByRole('button', { name: /Rollback|Revert/i });
    await rollbackBtns.first().click();
    await sharedPage.waitForTimeout(1000);
    
    // Verify dialog is open
    await expect(sharedPage.getByRole('heading', { name: /Rollback to Version/i })).toBeVisible();
    
    // Click cancel button
    const cancelBtn = sharedPage.getByRole('button', { name: /Cancel/i });
    await cancelBtn.click();
    
    // Verify dialog is closed
    await expect(sharedPage.getByRole('heading', { name: /Rollback to Version/i })).not.toBeVisible({ timeout: 2000 });
  });

  test('should display version metadata in history', async () => {
    // Open version history
    const versionHistoryBtn = sharedPage.getByRole('button', { name: /View History/i });
    await versionHistoryBtn.click();
    await sharedPage.waitForTimeout(1000);
    
    // Verify version metadata is displayed (created date, created by, etc.)
    const versionItems = sharedPage.locator('.version-item');
    const itemCount = await versionItems.count();
    expect(itemCount).toBeGreaterThan(0);
    
    const firstVersion = versionItems.first();
    
    // Check for common metadata fields (dates, timestamps, etc.)
    const hasMetadata = await firstVersion.locator('text=/\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|ago|created|modified/i').count();
    expect(hasMetadata).toBeGreaterThan(0);
  });
});


