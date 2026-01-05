import { test, expect } from '@playwright/test';

/**
 * Login flow test to diagnose authentication issues
 */
test.describe('Login Flow Test', () => {
  test('should be able to complete login flow', async ({ page }) => {
    // Enable console logs
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
    page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText));
    
    console.log('Step 1: Navigate to homepage');
    await page.goto('/');
    await page.screenshot({ path: 'test-results/login-1-homepage.png' });
    
    console.log('Step 2: Fill username');
    await page.getByPlaceholder(/username/i).fill('admin');
    
    console.log('Step 3: Fill password');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.screenshot({ path: 'test-results/login-2-filled.png' });
    
    console.log('Step 4: Click sign in button');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.screenshot({ path: 'test-results/login-3-clicked.png' });
    
    console.log('Step 5: Wait for response (5 seconds)');
    await page.waitForTimeout(5000);
    
    console.log('Current URL:', page.url());
    await page.screenshot({ path: 'test-results/login-4-after-wait.png', fullPage: true });
    
    // Check if we're on dashboard
    if (page.url().includes('dashboard')) {
      console.log('✅ Successfully redirected to dashboard!');
    } else {
      console.log('❌ NOT on dashboard. Current URL:', page.url());
      
      // Check for error messages
      const bodyText = await page.locator('body').textContent();
      console.log('Page content:', bodyText);
    }
  });
});
