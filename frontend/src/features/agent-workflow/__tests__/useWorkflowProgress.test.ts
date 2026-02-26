/**
 * Unit tests for useWorkflowProgress hook — Real API integration (Sprint 10)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWorkflowProgress } from '../hooks/useWorkflowProgress';
import type { AgentProgressEvent, WorkflowStatusResponse } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockConnect = vi.fn().mockReturnValue('sub-mock-001');
const mockDisconnect = vi.fn();

vi.mock('../../../services/sseService', () => ({
  default: {
    connect:    (...args: unknown[]) => mockConnect(...args),
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
// Helpers — real API shapes
// ---------------------------------------------------------------------------

function makeRunningStatus(workflowId = 'wf-001'): WorkflowStatusResponse {
  return {
    workflow_id: workflowId,
    status: 'running',
    current_agent: 'observation',
    progress: {
      observation: {
        agent: 'observation',
        status: 'running',
        progress: 0.5,
        message: 'Extracting UI elements…',
      },
    },
    total_progress: 0.125,
    started_at: new Date().toISOString(),
    estimated_completion: null,
    error: null,
  };
}

function makeProgressEvent(workflowId = 'wf-001'): AgentProgressEvent {
  return {
    event: 'agent_progress',
    data: {
      agent: 'requirements',
      progress: 0.6,
      message: 'Generating scenarios…',
    },
    timestamp: new Date().toISOString(),
  };
}

function makeCompletedEvent(workflowId = 'wf-001'): AgentProgressEvent {
  return {
    event: 'workflow_completed',
    data: { workflow_id: workflowId, test_count: 5, total_duration_seconds: 42 },
    timestamp: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useWorkflowProgress', () => {
  let setIntervalSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    setIntervalSpy = vi.spyOn(globalThis, 'setInterval').mockReturnValue(undefined as unknown as ReturnType<typeof setInterval>);
    mockGetWorkflowStatus.mockResolvedValue(makeRunningStatus());
    mockCancelWorkflow.mockResolvedValue(undefined);
    mockConnect.mockReturnValue('sub-mock-001');
  });

  afterEach(() => {
    setIntervalSpy.mockRestore();
    vi.clearAllMocks();
  });

  it('starts with null state when workflowId is null', () => {
    const { result } = renderHook(() => useWorkflowProgress(null));
    expect(result.current.status).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isConnected).toBe(false);
  });

  it('sets isLoading and isConnected true when workflowId is provided', () => {
    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isConnected).toBe(true);
  });

  it('calls sseService.connect with the workflowId', () => {
    renderHook(() => useWorkflowProgress('wf-001'));
    expect(mockConnect).toHaveBeenCalledWith('wf-001', expect.any(Function));
  });

  it('polls getWorkflowStatus on mount', async () => {
    renderHook(() => useWorkflowProgress('wf-001'));
    await waitFor(() => expect(mockGetWorkflowStatus).toHaveBeenCalledWith('wf-001'));
  });

  it('updates status after first poll returns real-API WorkflowStatusResponse', async () => {
    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });

    expect(result.current.status).toBe('running');
    expect(result.current.currentAgent).toBe('observation');
    expect(typeof result.current.totalProgress).toBe('number');
  });

  it('applies SSE agent_progress event to state', async () => {
    let sseCallback: ((event: AgentProgressEvent) => void) | undefined;
    mockConnect.mockImplementation((_id: string, cb: (event: AgentProgressEvent) => void) => {
      sseCallback = cb;
      return 'sub-sse-001';
    });

    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });

    expect(sseCallback).toBeDefined();

    await act(async () => {
      sseCallback!(makeProgressEvent('wf-001'));
    });

    // After a progress event the workflow should still be running
    expect(result.current.status).toBe('running');
  });

  it('sets status to completed after workflow_completed SSE event', async () => {
    let sseCallback: ((event: AgentProgressEvent) => void) | undefined;
    mockConnect.mockImplementation((_id: string, cb: (event: AgentProgressEvent) => void) => {
      sseCallback = cb;
      return 'sub-sse-001';
    });

    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });

    await act(async () => {
      sseCallback!(makeCompletedEvent('wf-001'));
    });

    expect(result.current.status).toBe('completed');
  });

  it('calls disconnect on unmount', async () => {
    const { unmount } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });
    unmount();
    expect(mockDisconnect).toHaveBeenCalledWith('sub-mock-001');
  });

  it('resets to idle when workflowId changes to null', async () => {
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

  it('requests backend cancellation without forcing local cancelled state', async () => {
    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });

    await act(async () => { await result.current.cancel(); });

    expect(result.current.status).toBe('running');
    expect(mockCancelWorkflow).toHaveBeenCalledWith('wf-001');
  });

  it('shows error when cancel request fails', async () => {
    mockCancelWorkflow.mockRejectedValueOnce(new Error('Cancel failed'));

    const { result } = renderHook(() => useWorkflowProgress('wf-001'));
    await act(async () => { await Promise.resolve(); });

    await act(async () => { await result.current.cancel(); });

    expect(result.current.status).toBe('running');
    expect(result.current.error).toBe('Cancel failed');
  });

  it('exposes error from failed poll', async () => {
    mockGetWorkflowStatus.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useWorkflowProgress('wf-fail'));
    await act(async () => { await Promise.resolve(); });
    expect(result.current.error).toBe('Network error');
  });
});
