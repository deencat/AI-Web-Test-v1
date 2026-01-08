import { test, expect } from '@playwright/test';

/**
 * Quick connectivity test to verify application is accessible
 */
test.describe('Connectivity Test', () => {
  test('should be able to load the homepage', async ({ page }) => {
    console.log('Navigating to http://localhost:5173');
    
    // Just try to load the homepage
    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 10000 });
    
    console.log('Page loaded, URL:', page.url());
    console.log('Page title:', await page.title());
    
    // Take a screenshot
    await page.screenshot({ path: 'test-results/connectivity-test.png', fullPage: true });
    
    // Check if we can see the page
    const body = await page.locator('body').textContent();
    console.log('Body content length:', body?.length);
    
    // Just verify the page loaded
    expect(page.url()).toContain('localhost:5173');
  });
  
  test('should be able to interact with login form', async ({ page }) => {
    await page.goto('/');
    
    // Try to find username field
    const usernameField = page.getByPlaceholder(/username/i);
    await expect(usernameField).toBeVisible({ timeout: 5000 });
    
    await usernameField.fill('admin');
    
    const passwordField = page.getByPlaceholder(/password/i);
    await expect(passwordField).toBeVisible();
    
    await passwordField.fill('admin123');
    
    console.log('Login fields filled successfully');
  });
});
