import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockGet = vi.fn();
const mockDelete = vi.fn();
const mockPost = vi.fn();
const mockUseMockData = vi.fn().mockReturnValue(false);

vi.mock('../../services/api', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
  apiHelpers: {
    useMockData: () => mockUseMockData(),
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

    expect(mockDelete).toHaveBeenCalledTimes(1);
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

  it('returns empty result without calling API when ids is empty', async () => {
    const result = await testsService.batchDeleteTests([]);

    expect(mockDelete).not.toHaveBeenCalled();
    expect(result).toEqual({ deleted: 0, failed: [] });
  });

  it('chunks 101 ids into two sequential DELETE requests of ≤100', async () => {
    const ids = Array.from({ length: 101 }, (_, i) => i + 1);

    mockDelete
      .mockResolvedValueOnce({ data: { deleted: 100, failed: [] } })
      .mockResolvedValueOnce({ data: { deleted: 1, failed: [] } });

    const result = await testsService.batchDeleteTests(ids);

    expect(mockDelete).toHaveBeenCalledTimes(2);
    expect(mockDelete).toHaveBeenNthCalledWith(1, '/tests/batch', {
      data: { ids: ids.slice(0, 100) },
    });
    expect(mockDelete).toHaveBeenNthCalledWith(2, '/tests/batch', {
      data: { ids: [101] },
    });
    expect(result).toEqual({ deleted: 101, failed: [] });
  });

  it('aggregates soft failures across chunks', async () => {
    const ids = Array.from({ length: 101 }, (_, i) => i + 1);

    mockDelete
      .mockResolvedValueOnce({ data: { deleted: 100, failed: [] } })
      .mockResolvedValueOnce({ data: { deleted: 0, failed: [101] } });

    const result = await testsService.batchDeleteTests(ids);

    expect(result).toEqual({ deleted: 100, failed: [101] });
  });

  it('stops and rejects when a later chunk fails hard', async () => {
    const ids = Array.from({ length: 101 }, (_, i) => i + 1);

    mockDelete
      .mockResolvedValueOnce({ data: { deleted: 100, failed: [] } })
      .mockRejectedValueOnce(new Error('Server error'));

    await expect(testsService.batchDeleteTests(ids)).rejects.toThrow('Server error');
    expect(mockDelete).toHaveBeenCalledTimes(2);
  });
});

// ---------------------------------------------------------------------------
// cloneTest
// ---------------------------------------------------------------------------

describe('testsService.cloneTest()', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseMockData.mockReturnValue(false);
  });

  it('POSTs to /tests/{id}/clone without body by default', async () => {
    mockPost.mockResolvedValueOnce({
      data: { id: 99, title: 'Login Flow (Copy)', status: 'pending' },
    });

    const result = await testsService.cloneTest(42);

    expect(mockPost).toHaveBeenCalledWith('/tests/42/clone', {});
    expect(result).toEqual({ id: 99, title: 'Login Flow (Copy)', status: 'pending' });
  });

  it('POSTs with new_title when options.newTitle is provided', async () => {
    mockPost.mockResolvedValueOnce({
      data: { id: 100, title: 'Custom Clone', status: 'pending' },
    });

    await testsService.cloneTest(42, { newTitle: 'Custom Clone' });

    expect(mockPost).toHaveBeenCalledWith('/tests/42/clone', { new_title: 'Custom Clone' });
  });

  it('throws a meaningful error when API call fails', async () => {
    mockPost.mockRejectedValueOnce(new Error('Conflict'));

    await expect(testsService.cloneTest(1)).rejects.toThrow('Conflict');
  });

  it('supports mock mode with (Copy) suffix and collision handling', async () => {
    mockUseMockData.mockReturnValue(true);

    const first = await testsService.cloneTest('TEST-001' as unknown as number);
    expect(first.name).toBe('Login Flow Test (Copy)');

    const second = await testsService.cloneTest('TEST-001' as unknown as number);
    expect(second.name).toBe('Login Flow Test (Copy 2)');
  });
});
