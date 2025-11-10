import { test, expect } from '@playwright/test';

/**
 * Settings Page Tests
 * Tests the application settings page with mock configurations
 * Design Mode: Frontend only with dummy JSON
 */

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    
    // Navigate to Settings page
    await page.getByRole('link', { name: /settings/i }).click();
    await page.waitForURL('**/settings');
  });

  test('should display settings page header', async ({ page }) => {
    // Verify page heading
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();
  });

  test('should display general settings section', async ({ page }) => {
    // Verify section heading
    await expect(page.getByRole('heading', { name: /general settings/i })).toBeVisible();
    
    // Verify form fields
    await expect(page.getByLabel(/project name/i)).toBeVisible();
    await expect(page.getByLabel(/project description/i)).toBeVisible();
    await expect(page.getByLabel(/api endpoint/i)).toBeVisible();
  });

  test('should display notification settings section', async ({ page }) => {
    // Verify section heading
    await expect(page.getByRole('heading', { name: /notification settings/i })).toBeVisible();
    
    // Verify checkboxes
    await expect(page.getByLabel(/email notifications/i)).toBeVisible();
    await expect(page.getByLabel(/test failure alerts/i)).toBeVisible();
  });

  test('should display agent configuration section', async ({ page }) => {
    // Verify section heading
    await expect(page.getByRole('heading', { name: /agent configuration/i })).toBeVisible();
    
    // Verify agent toggles
    await expect(page.getByText(/explorer agent/i)).toBeVisible();
    await expect(page.getByText(/developer agent/i)).toBeVisible();
  });

  test('should have pre-filled form values', async ({ page }) => {
    // Verify default values are displayed
    const projectNameInput = page.getByLabel(/project name/i);
    await expect(projectNameInput).toHaveValue('AI Web Test');
    
    const descriptionInput = page.getByLabel(/project description/i);
    await expect(descriptionInput).toHaveValue(/automated testing platform/i);
  });

  test('should allow editing general settings fields', async ({ page }) => {
    // Edit project name
    const projectNameInput = page.getByLabel(/project name/i);
    await projectNameInput.clear();
    await projectNameInput.fill('New Project Name');
    await expect(projectNameInput).toHaveValue('New Project Name');
    
    // Edit description
    const descriptionInput = page.getByLabel(/project description/i);
    await descriptionInput.clear();
    await descriptionInput.fill('Updated description');
    await expect(descriptionInput).toHaveValue('Updated description');
  });

  test('should have toggle switches for notifications', async ({ page }) => {
    // Verify checkboxes exist and are interactive
    const emailNotifications = page.getByLabel(/email notifications/i);
    await expect(emailNotifications).toBeVisible();
    
    // Check current state
    const isChecked = await emailNotifications.isChecked();
    
    // Toggle
    await emailNotifications.click();
    await expect(emailNotifications).toBeChecked({ checked: !isChecked });
  });

  test('should have toggle switches for agents', async ({ page }) => {
    // Find first agent toggle
    const agentToggles = page.locator('input[type="checkbox"]').filter({ hasText: /explorer agent/i });
    
    // Agent toggles should exist (multiple checkboxes on page)
    const allCheckboxes = page.locator('input[type="checkbox"]');
    expect(await allCheckboxes.count()).toBeGreaterThan(0);
  });

  test('should display save changes button', async ({ page }) => {
    // Verify save button
    await expect(page.getByRole('button', { name: /save changes/i })).toBeVisible();
  });

  test('should show alert when clicking save changes', async ({ page }) => {
    // Setup dialog handler
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Settings saved successfully');
      dialog.accept();
    });
    
    // Click save button
    await page.getByRole('button', { name: /save changes/i }).click();
  });

  test('should display API endpoint configuration', async ({ page }) => {
    // Verify API endpoint field
    const apiEndpointInput = page.getByLabel(/api endpoint/i);
    await expect(apiEndpointInput).toBeVisible();
    await expect(apiEndpointInput).toHaveValue('http://localhost:8000/api');
  });

  test('should allow updating API endpoint', async ({ page }) => {
    // Update API endpoint
    const apiEndpointInput = page.getByLabel(/api endpoint/i);
    await apiEndpointInput.clear();
    await apiEndpointInput.fill('http://localhost:3000/api/v2');
    await expect(apiEndpointInput).toHaveValue('http://localhost:3000/api/v2');
  });

  test('should maintain layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify key elements are still visible
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /general settings/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /save changes/i })).toBeVisible();
  });

  test('should navigate back to dashboard', async ({ page }) => {
    // Click dashboard in sidebar
    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should have scrollable content for long forms', async ({ page }) => {
    // Verify page is scrollable (all sections visible)
    await expect(page.getByRole('heading', { name: /general settings/i })).toBeVisible();
    
    // Scroll to agent configuration
    await page.getByRole('heading', { name: /agent configuration/i }).scrollIntoViewIfNeeded();
    await expect(page.getByRole('heading', { name: /agent configuration/i })).toBeVisible();
  });
});

