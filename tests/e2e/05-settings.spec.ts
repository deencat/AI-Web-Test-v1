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
    await page.getByPlaceholder(/password/i).fill('admin123');
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
    
    // Verify form fields (using text matching instead of label)
    await expect(page.getByText(/project name/i).first()).toBeVisible();
    await expect(page.getByText(/default timeout/i).first()).toBeVisible();
  });

  test('should display notification settings section', async ({ page }) => {
    // Verify section heading
    await expect(page.getByRole('heading', { name: /notification settings/i })).toBeVisible();
    
    // Verify notification toggles (matching our actual implementation)
    await expect(page.getByText(/email notifications/i).first()).toBeVisible();
    await expect(page.getByText(/slack notifications/i)).toBeVisible();
    await expect(page.getByText(/test failure alerts/i)).toBeVisible();
  });

  test('should display AI model provider section', async ({ page }) => {
    // Verify section heading (updated to "AI Model Provider")
    await expect(page.getByRole('heading', { name: /ai model provider/i })).toBeVisible();
    
    // Verify provider selection buttons
    await expect(page.getByText(/google/i).first()).toBeVisible();
    await expect(page.getByText(/cerebras/i).first()).toBeVisible();
    await expect(page.getByText(/openrouter/i).first()).toBeVisible();
    
    // Verify advanced settings are present
    await expect(page.getByText(/temperature/i).first()).toBeVisible();
    await expect(page.getByText(/max tokens/i).first()).toBeVisible();
  });

  test('should have pre-filled form values', async ({ page }) => {
    // Verify default values are displayed (using placeholder text to find inputs)
    const projectNameInput = page.getByPlaceholder(/enter project name/i);
    await expect(projectNameInput).toHaveValue('AI Web Test v1.0');
    
    const timeoutInput = page.locator('input[type="number"]').first();
    await expect(timeoutInput).toHaveValue('30');
  });

  test('should allow editing general settings fields', async ({ page }) => {
    // Edit project name
    const projectNameInput = page.getByPlaceholder(/enter project name/i);
    await projectNameInput.clear();
    await projectNameInput.fill('New Project Name');
    await expect(projectNameInput).toHaveValue('New Project Name');
    
    // Edit timeout
    const timeoutInput = page.locator('input[type="number"]').first();
    await timeoutInput.clear();
    await timeoutInput.fill('60');
    await expect(timeoutInput).toHaveValue('60');
  });

  test('should have toggle switches for notifications', async ({ page }) => {
    // Our implementation uses custom toggle switches (not standard checkboxes)
    // Verify the toggle exists by checking for the parent container
    const emailNotifications = page.getByText(/email notifications/i);
    await expect(emailNotifications).toBeVisible();
    
    // Verify the checkbox input exists (hidden but functional)
    const allCheckboxes = page.locator('input[type="checkbox"]');
    expect(await allCheckboxes.count()).toBeGreaterThan(0);
  });

  test('should allow switching between model providers', async ({ page }) => {
    // Click Cerebras provider button
    await page.getByRole('button', { name: /cerebras/i }).click();
    
    // Verify Cerebras configuration appears (backend config guide)
    await expect(page.getByText(/CEREBRAS_API_KEY/i)).toBeVisible();
    await expect(page.getByText(/llama.*70b.*latest/i)).toBeVisible();
    
    // Click OpenRouter provider button
    await page.getByRole('button', { name: /openrouter/i }).click();
    
    // Verify OpenRouter configuration appears (backend config guide)
    await expect(page.getByText(/OPENROUTER_API_KEY/i)).toBeVisible();
    
    // Click Google provider button
    await page.getByRole('button', { name: /google/i }).click();
    
    // Verify Google configuration appears (backend config guide)
    await expect(page.getByText(/GOOGLE_API_KEY/i)).toBeVisible();
  });

  test('should display save changes button', async ({ page }) => {
    // Verify save button (our actual button text is "Save Settings")
    await expect(page.getByRole('button', { name: /save settings/i })).toBeVisible();
  });

  test('should show backend configuration instructions', async ({ page }) => {
    // Verify Google provider shows backend configuration guide
    await page.getByRole('button', { name: /google/i }).click();
    await expect(page.getByText(/Configuration Required in Backend/i)).toBeVisible();
    await expect(page.getByText(/GOOGLE_API_KEY=your-key-here/i)).toBeVisible();
    await expect(page.getByText(/GOOGLE_MODEL=gemini-2.5-flash/i)).toBeVisible();
    
    // Verify link to get API key is present
    const googleLink = page.getByRole('link', { name: /Google AI Studio/i });
    await expect(googleLink).toBeVisible();
    await expect(googleLink).toHaveAttribute('href', 'https://aistudio.google.com/app/apikey');
  });

  test('should show reference message when saving preferences', async ({ page }) => {
    // Setup dialog handler (expecting reference message)
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain('Preferences Noted');
      expect(dialog.message()).toContain('reference selections only');
      expect(dialog.message()).toContain('backend/.env');
      await dialog.accept();
    });
    
    // Click save button
    await page.getByRole('button', { name: /save settings/i }).click();
  });

  test('should display system information section', async ({ page }) => {
    // Verify section heading (updated to "System Information")
    await expect(page.getByRole('heading', { name: /system information/i })).toBeVisible();
    await expect(page.getByText(/http:\/\/localhost:8000\/api/i)).toBeVisible();
    
    // Verify API documentation links
    await expect(page.getByRole('link', { name: /swagger ui/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /redoc/i })).toBeVisible();
  });

  test('should display version information', async ({ page }) => {
    // Verify version information section exists
    await expect(page.getByText(/version information/i)).toBeVisible();
    
    // Verify the version info grid container with 2 columns
    const versionGrid = page.locator('.grid.grid-cols-2.gap-4');
    await expect(versionGrid).toBeVisible();
    
    // Verify version numbers are displayed (at least one v1.0.0 visible)
    await expect(page.locator('text=v1.0.0').first()).toBeVisible();
  });

  test('should maintain layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify key elements are still visible (matching our actual button text)
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /general settings/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /save settings/i })).toBeVisible();
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
    
    // Scroll to AI Model Provider section
    await page.getByRole('heading', { name: /ai model provider/i }).scrollIntoViewIfNeeded();
    await expect(page.getByRole('heading', { name: /ai model provider/i })).toBeVisible();
    
    // Scroll to System Information section
    await page.getByRole('heading', { name: /system information/i }).scrollIntoViewIfNeeded();
    await expect(page.getByRole('heading', { name: /system information/i })).toBeVisible();
  });

  test('should reset settings to defaults', async ({ page }) => {
    // Change some settings first
    const projectNameInput = page.getByPlaceholder(/enter project name/i);
    await projectNameInput.clear();
    await projectNameInput.fill('Custom Project');
    
    // Setup dialog handlers (confirmation then success)
    let dialogCount = 0;
    page.on('dialog', async dialog => {
      dialogCount++;
      if (dialogCount === 1) {
        // First dialog: confirmation
        expect(dialog.message()).toContain('reset all preferences');
        await dialog.accept();
      } else if (dialogCount === 2) {
        // Second dialog: success message
        expect(dialog.message()).toContain('Preferences reset');
        await dialog.accept();
      }
    });
    
    // Click reset button
    await page.getByRole('button', { name: /reset to defaults/i }).click();
    
    // Wait a bit for the reset to complete
    await page.waitForTimeout(100);
    
    // Verify project name is back to default
    await expect(projectNameInput).toHaveValue('AI Web Test v1.0');
  });
});

