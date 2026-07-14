import { test, expect, APIRequestContext } from '@playwright/test';
import { getApiToken, loginAsAdmin, waitForSavedTestsList } from './helpers/auth';

const API_BASE = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000/api/v1';

async function createCloneSeedTest(
  request: APIRequestContext,
  title: string
): Promise<{ id: number; title: string; steps: unknown[] }> {
  const token = await getApiToken(request);
  const headers = { Authorization: `Bearer ${token}` };

  const response = await request.post(`${API_BASE}/tests`, {
    headers,
    data: {
      title,
      description: 'Clone E2E seed test',
      test_type: 'e2e',
      priority: 'high',
      steps: [
        { action: 'navigate', url: 'https://example.com' },
        { action: 'click', selector: '#submit' },
      ],
      expected_result: 'Page loads successfully',
      preconditions: 'User is logged in',
      tags: ['e2e', 'clone'],
      requires_runtime_credentials: true,
    },
  });

  if (!response.ok()) {
    throw new Error(`Failed to seed clone test: ${response.status()} ${await response.text()}`);
  }

  const created = await response.json();
  return {
    id: created.id as number,
    title: created.title as string,
    steps: created.steps as unknown[],
  };
}

async function deleteTest(request: APIRequestContext, testId: number): Promise<void> {
  const token = await getApiToken(request);
  await request.delete(`${API_BASE}/tests/${testId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

test.describe('Clone Test Case — Feature 2 E2E', () => {
  let sourceTestId: number;
  let sourceTitle: string;
  let sourceSteps: unknown[];
  const createdTestIds: number[] = [];

  test.beforeAll(async ({ request }) => {
    const uniqueTitle = `E2E Clone Source ${Date.now()}`;
    const seeded = await createCloneSeedTest(request, uniqueTitle);
    sourceTestId = seeded.id;
    sourceTitle = seeded.title;
    sourceSteps = seeded.steps;
    createdTestIds.push(sourceTestId);
  });

  test.afterAll(async ({ request }) => {
    const token = await getApiToken(request);
    const headers = { Authorization: `Bearer ${token}` };
    for (const id of createdTestIds) {
      await request.delete(`${API_BASE}/tests/${id}`, { headers });
    }
  });

  test('clones a saved test with (Copy) suffix and preserves source', async ({
    page,
    request,
  }) => {
    await loginAsAdmin(page, request);
    await page.goto('/tests/saved');
    await waitForSavedTestsList(page);

    const cloneButton = page.getByTestId(`clone-test-button-${sourceTestId}`);
    await expect(cloneButton).toBeVisible();
    await cloneButton.click();

    await expect(page.getByRole('status')).toContainText(`${sourceTitle} (Copy)`, {
      timeout: 15000,
    });
    await expect(
      page.locator('[data-testid^="inline-title-button-"]').filter({
        hasText: `${sourceTitle} (Copy)`,
      })
    ).toBeVisible();
    await expect(
      page.locator('[data-testid^="inline-title-button-"]').filter({
        hasText: sourceTitle,
        hasNotText: '(Copy)',
      })
    ).toBeVisible();

    const token = await getApiToken(request);
    const headers = { Authorization: `Bearer ${token}` };

    const listResponse = await request.get(`${API_BASE}/tests?limit=100`, { headers });
    expect(listResponse.ok()).toBeTruthy();
    const listBody = await listResponse.json();
    const items = Array.isArray(listBody) ? listBody : listBody.items ?? [];

    const source = items.find((t: { id: number }) => t.id === sourceTestId);
    const clone = items.find((t: { title: string }) => t.title === `${sourceTitle} (Copy)`);

    expect(source).toBeTruthy();
    expect(clone).toBeTruthy();
    expect(clone.id).not.toBe(sourceTestId);
    expect(clone.status).toBe('pending');
    expect(clone.steps).toEqual(sourceSteps);
    expect(source.title).toBe(sourceTitle);

    if (clone?.id) {
      createdTestIds.push(clone.id);
    }
  });

  test('API: duplicate new_title returns 409; missing test returns 404', async ({ request }) => {
    const token = await getApiToken(request);
    const headers = { Authorization: `Bearer ${token}` };

    const conflictResponse = await request.post(`${API_BASE}/tests/${sourceTestId}/clone`, {
      headers,
      data: { new_title: sourceTitle },
    });
    expect(conflictResponse.status()).toBe(409);

    const notFoundResponse = await request.post(`${API_BASE}/tests/99999/clone`, { headers });
    expect(notFoundResponse.status()).toBe(404);
  });

  test('re-clone assigns (Copy 2) title', async ({ page, request }) => {
    const token = await getApiToken(request);
    const headers = { Authorization: `Bearer ${token}` };

    const firstClone = await request.post(`${API_BASE}/tests/${sourceTestId}/clone`, { headers });
    expect(firstClone.status()).toBe(201);
    const firstBody = await firstClone.json();
    createdTestIds.push(firstBody.id);

    const secondClone = await request.post(`${API_BASE}/tests/${sourceTestId}/clone`, { headers });
    expect(secondClone.status()).toBe(201);
    const secondBody = await secondClone.json();
    createdTestIds.push(secondBody.id);
    expect(secondBody.title).toBe(`${sourceTitle} (Copy 2)`);

    await loginAsAdmin(page, request);
    await page.goto('/tests/saved');
    await waitForSavedTestsList(page);
    await expect(page.getByText(`${sourceTitle} (Copy 2)`)).toBeVisible({ timeout: 15000 });
  });
});
