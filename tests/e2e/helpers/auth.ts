import { APIRequestContext, Page, expect } from '@playwright/test';

const API_BASE = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000/api/v1';

let cachedApiToken: string | null = null;

export async function getApiToken(request: APIRequestContext): Promise<string> {
  if (cachedApiToken) {
    return cachedApiToken;
  }

  const response = await request.post(`${API_BASE}/auth/login`, {
    form: { username: 'admin', password: 'admin123' },
  });
  if (!response.ok()) {
    throw new Error(`Login failed: ${response.status()} ${await response.text()}`);
  }
  const body = await response.json();
  cachedApiToken = body.access_token as string;
  return cachedApiToken;
}

export async function seedSavedTest(request: APIRequestContext): Promise<number> {
  const token = await getApiToken(request);
  const headers = { Authorization: `Bearer ${token}` };

  const listResponse = await request.get(`${API_BASE}/tests?limit=1`, { headers });
  if (listResponse.ok()) {
    const listBody = await listResponse.json();
    const items = Array.isArray(listBody) ? listBody : listBody.items ?? [];
    if (items.length > 0) {
      return items[0].id as number;
    }
  }

  const createResponse = await request.post(`${API_BASE}/tests`, {
    headers,
    data: {
      title: `E2E Seed Test ${Date.now()}`,
      description: 'Seeded for Sprint 1 saved-tests E2E coverage',
      test_type: 'e2e',
      priority: 'medium',
      steps: ['Navigate to login page', 'Enter valid credentials'],
      expected_result: 'User is logged in successfully',
    },
  });

  if (!createResponse.ok()) {
    throw new Error(`Failed to seed test: ${createResponse.status()} ${await createResponse.text()}`);
  }

  const created = await createResponse.json();
  return created.id as number;
}

/** Saved test with ≥5 steps for stop-execution E2E (cooperative cancel). */
export async function createMultiStepCancelTest(
  request: APIRequestContext,
  title?: string
): Promise<number> {
  const token = await getApiToken(request);
  const headers = { Authorization: `Bearer ${token}` };

  const createResponse = await request.post(`${API_BASE}/tests`, {
    headers,
    data: {
      title: title ?? `E2E Cancel Test ${Date.now()}`,
      description: 'Multi-step test for cooperative execution cancel E2E',
      test_type: 'e2e',
      priority: 'medium',
      steps: [
        'Navigate to https://example.com',
        'Verify the page title contains Example',
        'Scroll to the bottom of the page',
        'Verify the page body is visible',
        'Navigate to https://example.org',
        'Verify the page loaded successfully',
      ],
      expected_result: 'All navigation steps complete without error',
    },
  });

  if (!createResponse.ok()) {
    throw new Error(
      `Failed to create multi-step cancel test: ${createResponse.status()} ${await createResponse.text()}`
    );
  }

  const created = await createResponse.json();
  return created.id as number;
}

export async function createDisposableTest(
  request: APIRequestContext,
  title?: string
): Promise<number> {
  const token = await getApiToken(request);
  const headers = { Authorization: `Bearer ${token}` };

  const createResponse = await request.post(`${API_BASE}/tests`, {
    headers,
    data: {
      title: title ?? `E2E Disposable Test ${Date.now()}`,
      description: 'Disposable test for E2E delete navigation coverage',
      test_type: 'e2e',
      priority: 'medium',
      steps: ['Navigate to login page', 'Enter valid credentials'],
      expected_result: 'User is logged in successfully',
    },
  });

  if (!createResponse.ok()) {
    throw new Error(
      `Failed to create disposable test: ${createResponse.status()} ${await createResponse.text()}`
    );
  }

  const created = await createResponse.json();
  return created.id as number;
}

export async function loginAsAdmin(page: Page, request?: APIRequestContext): Promise<void> {
  if (request) {
    const token = await getApiToken(request);
    const userResponse = await request.get(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!userResponse.ok()) {
      throw new Error(`Failed to fetch user profile: ${userResponse.status()} ${await userResponse.text()}`);
    }
    const user = await userResponse.json();

    await page.goto('/');
    await page.evaluate(
      ({ authToken, authUser }) => {
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(authUser));
      },
      { authToken: token, authUser: user }
    );
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    return;
  }

  await page.goto('/');
  await page.getByPlaceholder(/username/i).fill('admin');
  await page.getByPlaceholder(/password/i).fill('admin123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL('**/dashboard', { timeout: 60000 });
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
}

export async function waitForSavedTestsList(page: Page): Promise<void> {
  await page.locator('[data-testid^="inline-title-button-"]').first().waitFor({
    timeout: 120000,
  });
}
