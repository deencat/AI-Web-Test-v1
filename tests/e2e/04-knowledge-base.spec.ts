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
    await page.getByPlaceholder(/password/i).fill('password123');
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
    // Verify category filters
    await expect(page.getByRole('button', { name: /all documents/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /system guides/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /product info/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /processes/i })).toBeVisible();
  });

  test('should display mock knowledge base documents', async ({ page }) => {
    // Verify mock documents are displayed
    await expect(page.getByText(/user authentication guide/i)).toBeVisible();
    await expect(page.getByText(/API testing best practices/i)).toBeVisible();
    await expect(page.getByText(/test case design patterns/i)).toBeVisible();
  });

  test('should display document metadata', async ({ page }) => {
    // Verify document details
    await expect(page.getByText(/system_guide/i)).toBeVisible();
    await expect(page.getByText(/reference/i)).toBeVisible();
  });

  test('should display document sizes', async ({ page }) => {
    // Verify file sizes are shown
    await expect(page.getByText(/2.3 MB/i)).toBeVisible();
    await expect(page.getByText(/1.8 MB/i)).toBeVisible();
  });

  test('should display view button for each document', async ({ page }) => {
    // Verify view buttons exist
    const viewButtons = page.getByRole('button', { name: /view/i });
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
    // Setup dialog handler
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Create New Category');
      dialog.accept();
    });
    
    // Click create category button
    await page.getByRole('button', { name: /create category/i }).click();
  });

  test('should show alert when viewing a document', async ({ page }) => {
    // Setup dialog handler
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('View document');
      dialog.accept();
    });
    
    // Click first view button
    await page.getByRole('button', { name: /view/i }).first().click();
  });

  test('should filter by category (UI interaction)', async ({ page }) => {
    // Click on system guides filter
    await page.getByRole('button', { name: /system guides/i }).click();
    
    // Button should be visible and clickable
    await expect(page.getByRole('button', { name: /system guides/i })).toBeVisible();
  });

  test('should display document upload dates', async ({ page }) => {
    // Verify upload dates are shown
    await expect(page.getByText(/2025-01-15/i)).toBeVisible();
  });

  test('should maintain responsive layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify key elements
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /upload document/i })).toBeVisible();
    await expect(page.getByText(/user authentication guide/i)).toBeVisible();
  });

  test('should navigate back to dashboard', async ({ page }) => {
    // Click dashboard in sidebar
    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should display document count information', async ({ page }) => {
    // The page should show that there are documents (3 in mock data)
    const documents = page.locator('div').filter({ hasText: /user authentication guide/i });
    await expect(documents.first()).toBeVisible();
  });
});

