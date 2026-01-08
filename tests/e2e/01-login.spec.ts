import { test, expect } from '@playwright/test';

/**
 * Login Page Tests
 * Tests the authentication flow with mock data
 * Design Mode: Frontend only with dummy JSON
 */

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login form', async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/AI Web Test/);
    
    // Verify login form elements
    await expect(page.getByRole('heading', { name: /AI Web Test/i })).toBeVisible();
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
    await expect(page.getByPlaceholder(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should show validation for empty fields', async ({ page }) => {
    // Click sign in without filling fields
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Verify validation message
    await expect(page.getByText(/please enter both username and password/i)).toBeVisible();
  });

  test('should successfully login with any credentials (mock)', async ({ page }) => {
    // Fill in login form with correct credentials
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    
    // Click sign in
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard');
    
    // Verify dashboard loaded
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should navigate to dashboard with specific username', async ({ page }) => {
    // Login with correct credentials
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Verify navigation
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should have responsive design', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
  });
});

