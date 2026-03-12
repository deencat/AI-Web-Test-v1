import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockGet = vi.fn();
const mockDelete = vi.fn();

vi.mock('../../services/api', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
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

// ---------------------------------------------------------------------------
// batchDeleteTests
// ---------------------------------------------------------------------------

describe('testsService.batchDeleteTests()', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls DELETE /tests/batch with the provided ids', async () => {
    mockDelete.mockResolvedValueOnce({
      data: { deleted: 3, failed: [] },
    });

    const result = await testsService.batchDeleteTests([1, 2, 3]);

    expect(mockDelete).toHaveBeenCalledWith('/tests/batch', { data: { ids: [1, 2, 3] } });
    expect(result).toEqual({ deleted: 3, failed: [] });
  });

  it('returns partial success when some ids fail', async () => {
    mockDelete.mockResolvedValueOnce({
      data: { deleted: 1, failed: [2] },
    });

    const result = await testsService.batchDeleteTests([1, 2]);

    expect(result.deleted).toBe(1);
    expect(result.failed).toEqual([2]);
  });

  it('throws a meaningful error when API call fails', async () => {
    mockDelete.mockRejectedValueOnce(new Error('Network error'));

    await expect(testsService.batchDeleteTests([1])).rejects.toThrow('Network error');
  });
});
