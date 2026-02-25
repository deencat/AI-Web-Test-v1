import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockGet = vi.fn();

vi.mock('../../services/api', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
  },
  apiHelpers: {
    useMockData: vi.fn().mockReturnValue(false),
    getErrorMessage: vi.fn((e: unknown) => (e instanceof Error ? e.message : String(e))),
  },
}));

import testsService from '../../services/testsService';

describe('testsService.getAllTests()', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads all pages when backend total exceeds first page limit', async () => {
    const firstPageItems = Array.from({ length: 100 }, (_, index) => ({ id: index + 1 }));
    const secondPageItems = Array.from({ length: 30 }, (_, index) => ({ id: index + 101 }));

    mockGet
      .mockResolvedValueOnce({
        data: {
          items: firstPageItems,
          total: 130,
          skip: 0,
          limit: 100,
        },
      })
      .mockResolvedValueOnce({
        data: {
          items: secondPageItems,
          total: 130,
          skip: 100,
          limit: 100,
        },
      });

    const result = await testsService.getAllTests();

    expect(mockGet).toHaveBeenCalledTimes(2);
    expect(mockGet).toHaveBeenNthCalledWith(1, '/tests', {
      params: {
        skip: 0,
        limit: 100,
      },
    });
    expect(mockGet).toHaveBeenNthCalledWith(2, '/tests', {
      params: {
        skip: 100,
        limit: 100,
      },
    });
    expect(result).toHaveLength(130);
  });
});
