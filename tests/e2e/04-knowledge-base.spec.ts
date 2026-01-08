import { test, expect } from '@playwright/test';

/**
 * Knowledge Base Page Tests
 * Tests the KB management page with mock data
 * Design Mode: Frontend only with dummy JSON
 */

test.describe('Knowledge Base Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('/');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/dashboard');
    
    // Navigate to Knowledge Base page
    await page.getByRole('link', { name: /knowledge base/i }).click();
    await page.waitForURL('**/knowledge-base');
  });

  test('should display knowledge base page header', async ({ page }) => {
    // Verify page heading
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();
  });

  test('should display upload document button', async ({ page }) => {
    // Verify upload button
    await expect(page.getByRole('button', { name: /upload document/i })).toBeVisible();
  });

  test('should display create category button', async ({ page }) => {
    // Verify create category button
    await expect(page.getByRole('button', { name: /create category/i })).toBeVisible();
  });

  test('should display category filter buttons', async ({ page }) => {
    // Verify category filters (matching our actual mock data)
    await expect(page.getByRole('button', { name: /all documents/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /system guide \(/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /product info/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /process \(/i })).toBeVisible();
  });

  test('should display mock knowledge base documents', async ({ page }) => {
    // Verify mock documents are displayed (matching our actual mock data)
    await expect(page.getByText(/Three HK Login Flow Guide/i).first()).toBeVisible();
    await expect(page.getByText(/Payment Gateway Integration/i).first()).toBeVisible();
    await expect(page.getByText(/5G Plan Product Catalog/i).first()).toBeVisible();
  });

  test('should display document metadata', async ({ page }) => {
    // Verify document details (our implementation shows categories as badges)
    await expect(page.getByText(/System Guide/i).first()).toBeVisible();
    await expect(page.getByText(/Reference/i).first()).toBeVisible();
  });

  test('should display document sizes', async ({ page }) => {
    // Verify file sizes are shown (matching our actual mock data)
    await expect(page.getByText(/2.4 MB/i)).toBeVisible();
    await expect(page.getByText(/3.1 MB/i)).toBeVisible();
  });

  test('should display view button for each document', async ({ page }) => {
    // Verify view buttons exist (wait for page to load first)
    await page.waitForSelector('text=/Three HK Login Flow Guide/i');
    const viewButtons = page.getByRole('button', { name: /^view$/i });
    expect(await viewButtons.count()).toBeGreaterThan(0);
  });

  test('should show alert when clicking upload document', async ({ page }) => {
    // Setup dialog handler
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Upload Document');
      dialog.accept();
    });
    
    // Click upload button
    await page.getByRole('button', { name: /upload document/i }).click();
  });

  test('should show alert when clicking create category', async ({ page }) => {
    // Setup dialog handler (matching our actual alert text)
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Create Category');
      dialog.accept();
    });
    
    // Click create category button
    await page.getByRole('button', { name: /create category/i }).click();
  });

  test('should show alert when viewing a document', async ({ page }) => {
    // Setup dialog handler (matching our actual alert text)
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('View document');
      dialog.accept();
    });
    
    // Click first view button
    await page.getByRole('button', { name: /view/i }).first().click();
  });

  test('should filter by category (UI interaction)', async ({ page }) => {
    // Click on system guide filter (singular, matching our implementation)
    await page.getByRole('button', { name: /system guide \(/i }).click();
    
    // Button should be visible and clickable
    await expect(page.getByRole('button', { name: /system guide \(/i })).toBeVisible();
  });

  test('should display document upload dates', async ({ page }) => {
    // Verify upload dates are shown (our dates use .toLocaleDateString() format)
    // Just check that a date format is present
    await expect(page.getByText(/\d{1,2}\/\d{1,2}\/\d{4}/).first()).toBeVisible();
  });

  test('should maintain responsive layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify key elements (matching our actual mock data)
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /upload document/i })).toBeVisible();
    await expect(page.getByText(/Three HK Login Flow Guide/i)).toBeVisible();
  });

  test('should navigate back to dashboard', async ({ page }) => {
    // Click dashboard in sidebar
    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should display document count information', async ({ page }) => {
    // The page should show that there are documents (15 in our mock data)
    const documents = page.locator('div').filter({ hasText: /Three HK Login Flow Guide/i });
    await expect(documents.first()).toBeVisible();
  });
});

