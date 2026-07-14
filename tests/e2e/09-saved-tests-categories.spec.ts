import { test, expect, APIRequestContext, Page } from '@playwright/test';
import { getApiToken, loginAsAdmin, waitForSavedTestsList } from './helpers/auth';

const API_BASE = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000/api/v1';

type SeedState = {
  categoryA: { id: number; name: string };
  categoryB: { id: number; name: string };
  emptyCategory: { id: number; name: string };
  testA: { id: number; title: string };
  testB: { id: number; title: string };
  testUncategorized: { id: number; title: string };
  createdCategoryIds: number[];
  createdTestIds: number[];
};

async function apiJson(
  request: APIRequestContext,
  method: 'get' | 'post' | 'put' | 'patch' | 'delete',
  path: string,
  token: string,
  data?: unknown
) {
  const response = await request.fetch(`${API_BASE}${path}`, {
    method: method.toUpperCase(),
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data,
  });

  if (!response.ok()) {
    throw new Error(`${method.toUpperCase()} ${path} failed: ${response.status()} ${await response.text()}`);
  }

  if (response.status() === 204) {
    return null;
  }

  return response.json();
}

async function createCategory(
  request: APIRequestContext,
  token: string,
  name: string,
  color = '#3B82F6'
): Promise<number> {
  const created = await apiJson(request, 'post', '/test-categories', token, {
    name,
    description: `${name} description`,
    color,
  });
  return created.id as number;
}

async function createTest(
  request: APIRequestContext,
  token: string,
  title: string
): Promise<number> {
  const created = await apiJson(request, 'post', '/tests', token, {
    title,
    description: `${title} description`,
    test_type: 'e2e',
    priority: 'medium',
    steps: ['Open page', 'Verify expected behavior'],
    expected_result: 'Scenario completes successfully',
  });
  return created.id as number;
}

async function assignCategory(
  request: APIRequestContext,
  token: string,
  testIds: number[],
  categoryId: number | null
): Promise<void> {
  await apiJson(request, 'patch', '/tests/batch/category', token, {
    test_ids: testIds,
    test_category_id: categoryId,
  });
}

async function cleanupSeed(request: APIRequestContext, token: string, seed: SeedState): Promise<void> {
  for (const id of seed.createdTestIds) {
    const response = await request.delete(`${API_BASE}/tests/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok() && response.status() !== 404) {
      throw new Error(`Cleanup failed for test ${id}: ${response.status()} ${await response.text()}`);
    }
  }

  for (const id of seed.createdCategoryIds) {
    const response = await request.delete(`${API_BASE}/test-categories/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok() && response.status() !== 404) {
      throw new Error(`Cleanup failed for category ${id}: ${response.status()} ${await response.text()}`);
    }
  }
}

async function openSavedTests(page: Page, request: APIRequestContext): Promise<void> {
  await loginAsAdmin(page, request);
  await page.goto('/tests/saved');
  await page.waitForURL('**/tests/saved');
  await waitForSavedTestsList(page);
}

test.describe('Saved Tests Categories — Sprint 3', () => {
  let token: string;
  let seed: SeedState;

  test.beforeEach(async ({ request, page }, testInfo) => {
    token = await getApiToken(request);
    const suffix = `${Date.now()}-${testInfo.retry}-${testInfo.parallelIndex}`;

    const categoryAName = `Sprint3-Category-A-${suffix}`;
    const categoryBName = `Sprint3-Category-B-${suffix}`;
    const emptyCategoryName = `Sprint3-Category-Empty-${suffix}`;

    const categoryAId = await createCategory(request, token, categoryAName, '#2563EB');
    const categoryBId = await createCategory(request, token, categoryBName, '#7C3AED');
    const emptyCategoryId = await createCategory(request, token, emptyCategoryName, '#0EA5E9');

    const testATitle = `Sprint3 Test A ${suffix}`;
    const testBTitle = `Sprint3 Test B ${suffix}`;
    const uncategorizedTitle = `Sprint3 Test U ${suffix}`;

    const testAId = await createTest(request, token, testATitle);
    const testBId = await createTest(request, token, testBTitle);
    const testUncategorizedId = await createTest(request, token, uncategorizedTitle);

    await assignCategory(request, token, [testAId], categoryAId);
    await assignCategory(request, token, [testBId], categoryBId);

    seed = {
      categoryA: { id: categoryAId, name: categoryAName },
      categoryB: { id: categoryBId, name: categoryBName },
      emptyCategory: { id: emptyCategoryId, name: emptyCategoryName },
      testA: { id: testAId, title: testATitle },
      testB: { id: testBId, title: testBTitle },
      testUncategorized: { id: testUncategorizedId, title: uncategorizedTitle },
      createdCategoryIds: [categoryAId, categoryBId, emptyCategoryId],
      createdTestIds: [testAId, testBId, testUncategorizedId],
    };

    await openSavedTests(page, request);
    await page.getByPlaceholder('Search by title or description...').fill('Sprint3 Test');
    await expect(page.getByTestId(`row-category-select-${seed.testA.id}`)).toBeVisible();
    await expect(page.getByTestId(`row-category-select-${seed.testB.id}`)).toBeVisible();
    await expect(page.getByTestId(`row-category-select-${seed.testUncategorized.id}`)).toBeVisible();
  });

  test.afterEach(async ({ request }) => {
    await cleanupSeed(request, token, seed);
  });

  test('scenario 1: manage categories create', async ({ page }) => {
    const createdName = `Sprint3-Created-${Date.now()}`;

    await page.getByTestId('manage-categories-button').click();
    await expect(page.getByTestId('manage-categories-modal')).toBeVisible();
    await page.getByTestId('category-name-input').fill(createdName);
    await page.getByTestId('category-description-input').fill('Created by sprint 3 category E2E');
    await page.getByTestId('save-category-button').click();

    await expect(page.getByTestId('manage-categories-modal')).not.toBeVisible();
    await expect(
      page.locator('button[data-testid^="category-filter-"]', { hasText: createdName })
    ).toBeVisible();
  });

  test('scenario 2: manage categories edit', async ({ page }) => {
    const renamed = `${seed.categoryA.name}-Renamed`;

    await page.getByTestId('manage-categories-button').click();
    await page.getByTestId(`edit-category-${seed.categoryA.id}`).click();
    await page.getByTestId('category-name-input').fill(renamed);
    await page.getByTestId('save-category-button').click();

    await expect(page.getByTestId('manage-categories-modal')).not.toBeVisible();
    await expect(
      page.locator('button[data-testid^="category-filter-"]', { hasText: renamed })
    ).toBeVisible();
  });

  test('scenario 3: manage categories delete and linked tests become uncategorized', async ({ page }) => {
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });

    await page.getByTestId('manage-categories-button').click();
    await page.getByTestId(`delete-category-${seed.categoryA.id}`).click();
    await expect(page.getByTestId(`category-item-${seed.categoryA.id}`)).toHaveCount(0);
    await page.getByTestId('close-category-modal-button').click();

    await expect(page.getByTestId(`row-category-select-${seed.testA.id}`)).toHaveValue('uncategorized');
  });

  test('scenario 4: single test assignment via row selector', async ({ page }) => {
    const select = page.getByTestId(`row-category-select-${seed.testUncategorized.id}`);
    await select.selectOption(String(seed.categoryA.id));
    await expect(select).toHaveValue(String(seed.categoryA.id));
  });

  test('scenario 5: single test assignment via edit drawer category field', async ({ page }) => {
    await page.goto(`/tests/saved?edit=${seed.testUncategorized.id}`);
    await expect(page.getByRole('heading', { name: /edit test case/i })).toBeVisible();
    await page.getByTestId('saved-edit-category-select').selectOption(String(seed.categoryB.id));
    await page.getByRole('button', { name: /save changes/i }).click();
    await expect(page.getByRole('heading', { name: /edit test case/i })).toHaveCount(0);

    await expect(page.getByTestId(`row-category-select-${seed.testUncategorized.id}`)).toHaveValue(
      String(seed.categoryB.id)
    );
  });

  test('scenario 6: bulk assign category to selected tests', async ({ page }) => {
    await page.getByTestId(`row-checkbox-${seed.testA.id}`).check();
    await page.getByTestId(`row-checkbox-${seed.testUncategorized.id}`).check();

    await page.getByTestId('set-category-button').selectOption(String(seed.categoryB.id));
    await expect(page.getByTestId(`row-category-select-${seed.testA.id}`)).toHaveValue(String(seed.categoryB.id));
    await expect(page.getByTestId(`row-category-select-${seed.testUncategorized.id}`)).toHaveValue(
      String(seed.categoryB.id)
    );
  });

  test('scenario 7: bulk set uncategorized', async ({ page }) => {
    await page.getByTestId(`row-checkbox-${seed.testA.id}`).check();
    await page.getByTestId(`row-checkbox-${seed.testB.id}`).check();

    await page.getByTestId('set-category-button').selectOption('uncategorized');
    await expect(page.getByTestId(`row-category-select-${seed.testA.id}`)).toHaveValue('uncategorized');
    await expect(page.getByTestId(`row-category-select-${seed.testB.id}`)).toHaveValue('uncategorized');
  });

  test('scenario 8: filter by specific category', async ({ page }) => {
    await page.getByTestId(`category-filter-${seed.categoryB.id}`).click();
    await expect(page.getByTestId(`inline-title-button-${seed.testB.id}`)).toBeVisible();
    await expect(page.getByTestId(`inline-title-button-${seed.testA.id}`)).toHaveCount(0);
    await expect(page.getByTestId(`inline-title-button-${seed.testUncategorized.id}`)).toHaveCount(0);
  });

  test('scenario 9: filter by uncategorized', async ({ page }) => {
    await page.getByTestId('category-filter-uncategorized').click();
    await expect(page.getByTestId(`inline-title-button-${seed.testUncategorized.id}`)).toBeVisible();
    await expect(page.getByTestId(`inline-title-button-${seed.testA.id}`)).toHaveCount(0);
    await expect(page.getByTestId(`inline-title-button-${seed.testB.id}`)).toHaveCount(0);
  });

  test('scenario 10: empty state for selected category', async ({ page }) => {
    await page.getByTestId(`category-filter-${seed.emptyCategory.id}`).click();
    await expect(page.getByTestId('category-filter-empty-state')).toContainText(
      `No tests match your filters in ${seed.emptyCategory.name}.`
    );
  });
});
