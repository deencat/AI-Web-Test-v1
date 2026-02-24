/**
 * Unit tests for useWorkflowProgress hook
 *
 * Sprint 10 Phase 2 — Developer B
 *
 * Uses real timers so that waitFor can poll without timer advancement.
 * setInterval is spied on (not mocked) to prevent indefinite intervals in tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWorkflowProgress } from '../hooks/useWorkflowProgress';
import type { AgentProgressEvent } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockConnect = vi.fn().mockReturnValue('sub-mock-001');
const mockDisconnect = vi.fn();

vi.mock('../../../services/sseService', () => ({
  default: {
    connect: (...args: unknown[]) => mockConnect(...args),
    disconnect: (...args: unknown[]) => mockDisconnect(...args),
  },
}));

const mockGetWorkflowStatus = vi.fn();
const mockCancelWorkflow = vi.fn();

vi.mock('../../../services/agentWorkflowService', () => ({
  default: {
    getWorkflowStatus: (...args: unknown[]) => mockGetWorkflowStatus(...args),
    cancelWorkflow:    (...args: unknown[]) => mockCancelWorkflow(...args),
  },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makePendingStatus(workflowId = 'wf-001') {
  return {
    workflow_id: workflowId,
    status: 'running' as const,
    progress: {
      stage: 'analyzing' as const,
      percentage: 25,
      message: 'Observing page…',
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

function makeProgressEvent(workflowId = 'wf-001'): AgentProgressEvent {
  return {
    workflow_id: workflowId,
    event_type: 'progress',
    progress: {
      stage: 'generating',
      percentage: 60,
      message: 'Generating test scenarios…',
      current_step: 3,
      total_steps: 5,
    },
    timestamp: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useWorkflowProgress', () => {
  // Spy on setInterval to avoid indefinite intervals keeping tests alive
  let setIntervalSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    setIntervalSpy = vi.spyOn(globalThis, 'setInterval').mockReturnValue(undefined as unknown as ReturnType<typeof setInterval>);
    mockGetWorkflowStatus.mockResolvedValue(makePendingStatus());
    mockCancelWorkflow.mockResolvedValue({ success: true, message: 'Cancelled' });
    mockConnect.mockReturnValue('sub-mock-001');
  });

  afterEach(() => {
    setIntervalSpy.mockRestore();
    vi.clearAllMocks();
  });

  // ----

  it('should start with null state when workflowId is null', () => {
    const { result } = renderHook(() => useWorkflowProgress(null));
    expect(result.current.status).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isConnected).toBe(false);
  });

  it('should set isLoading and isConnected true when workflowId is provided', () => {
    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isConnected).toBe(true);
  });

  it('should call sseService.connect with the workflowId', () => {
    renderHook(() => useWorkflowProgress('wf-001'));
    expect(mockConnect).toHaveBeenCalledWith('wf-001', expect.any(Function));
  });

  it('should poll for status on mount', async () => {
    renderHook(() => useWorkflowProgress('wf-001'));
    await waitFor(() => expect(mockGetWorkflowStatus).toHaveBeenCalledWith('wf-001'));
  });

  it('should update status after first poll', async () => {
    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    // Flush the async pollOnce() Promise that runs inside useEffect
    await act(async () => { await Promise.resolve(); });
    expect(result.current.status).toBe('running');
    expect(result.current.progress?.stage).toBe('analyzing');
  });

  it('should update from SSE event when callback is fired', async () => {
    let sseCallback: ((event: AgentProgressEvent) => void) | undefined;
    mockConnect.mockImplementation((_id: string, cb: (event: AgentProgressEvent) => void) => {
      sseCallback = cb;
      return 'sub-sse-001';
    });

    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    // Allow effect to run
    await act(async () => { await Promise.resolve(); });

    expect(sseCallback).toBeDefined();

    await act(async () => {
      sseCallback!(makeProgressEvent('wf-001'));
    });

    expect(result.current.progress?.stage).toBe('generating');
    expect(result.current.progress?.percentage).toBe(60);
  });

  it('should call disconnect on unmount', async () => {
    const { unmount } = renderHook(() => useWorkflowProgress('wf-001'));
    // Allow effect to set up
    await act(async () => { await Promise.resolve(); });
    unmount();
    expect(mockDisconnect).toHaveBeenCalledWith('sub-mock-001');
  });

  it('should reset to idle when workflowId changes to null', async () => {
    const { result, rerender } = renderHook(
      ({ id }: { id: string | null }) => useWorkflowProgress(id),
      { initialProps: { id: 'wf-001' as string | null } }
    );

    await act(async () => { await Promise.resolve(); });
    expect(result.current.status).toBe('running');

    rerender({ id: null });

    expect(result.current.status).toBeNull();
    expect(result.current.isConnected).toBe(false);
  });

  it('should set status to cancelled when cancel() is called', async () => {
    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });
    expect(result.current.status).toBe('running');

    await act(async () => {
      await result.current.cancel();
    });

    expect(result.current.status).toBe('cancelled');
    expect(mockCancelWorkflow).toHaveBeenCalledWith('wf-001');
  });

  it('should expose error from failed poll', async () => {
    mockGetWorkflowStatus.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useWorkflowProgress('wf-fail'));
    await act(async () => { await Promise.resolve(); });
    expect(result.current.error).toBe('Network error');
  });
});
