/**
 * useWorkflowProgress — React hook (Sprint 10 Real API)
 *
 * Connects to the SSE stream for a running workflow and provides live progress.
 * Falls back to polling every POLL_INTERVAL_MS when SSE delivers nothing within
 * 5 seconds (network proxy, test env, etc.).
 *
 * Usage:
 *   const { status, currentAgent, totalProgress, agentProgress, error, cancel } =
 *     useWorkflowProgress(workflowId);
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  AgentProgress,
  AgentProgressEvent,
  WorkflowStatus,
} from '../../../types/agentWorkflow.types';
import sseService from '../../../services/sseService';
import agentWorkflowService from '../../../services/agentWorkflowService';

const POLL_INTERVAL_MS = 3_000;
const SSE_FALLBACK_TIMEOUT_MS = 5_000;
const TERMINAL: WorkflowStatus[] = ['completed', 'failed', 'cancelled'];

// ---------------------------------------------------------------------------
// State Shape
// ---------------------------------------------------------------------------

export interface WorkflowProgressState {
  /** Lifecycle status; null before workflowId is set */
  status: WorkflowStatus | null;
  /** Currently active agent name; null when idle */
  currentAgent: string | null;
  /** Overall progress 0.0–1.0 */
  totalProgress: number;
  /** Per-agent progress map, keyed by agent name */
  agentProgress: Record<string, AgentProgress>;
  /** Error message when status === 'failed' */
  error: string | null;
  /** True while SSE / polling is active */
  isConnected: boolean;
  /** True during the initial load */
  isLoading: boolean;
}

const INITIAL_STATE: WorkflowProgressState = {
  status: null,
  currentAgent: null,
  totalProgress: 0,
  agentProgress: {},
  error: null,
  isConnected: false,
  isLoading: false,
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useWorkflowProgress(
  workflowId: string | null | undefined
): WorkflowProgressState & { cancel: () => void } {
  const [state, setState] = useState<WorkflowProgressState>(INITIAL_STATE);

  const workflowIdRef = useRef(workflowId);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sseSubIdRef = useRef<string | null>(null);
  const sseGotEventRef = useRef(false);

  workflowIdRef.current = workflowId;

  const isTerminal = (s: WorkflowStatus | null) => s !== null && TERMINAL.includes(s);

  // ---- stop helpers ----
  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const stopSSE = useCallback(() => {
    if (sseSubIdRef.current !== null) {
      sseService.disconnect(sseSubIdRef.current);
      sseSubIdRef.current = null;
    }
  }, []);

  // ---- apply a real WorkflowStatusResponse from poll ----
  const applyStatusResponse = useCallback(
    (res: Awaited<ReturnType<typeof agentWorkflowService.getWorkflowStatus>>) => {
      setState((prev) => ({
        ...prev,
        status: res.status,
        currentAgent: res.current_agent,
        totalProgress: res.total_progress,
        agentProgress: res.progress ?? {},
        error: res.error ?? null,
        isLoading: false,
      }));
      if (isTerminal(res.status)) {
        stopPolling();
        setState((prev) => ({ ...prev, isConnected: false }));
      }
    },
    [stopPolling] // eslint-disable-line react-hooks/exhaustive-deps
  );

  // ---- apply a real AgentProgressEvent from SSE ----
  const applySSEEvent = useCallback(
    (event: AgentProgressEvent) => {
      sseGotEventRef.current = true;
      stopPolling(); // SSE is working — stop polling

      setState((prev) => {
        const nextStatus: WorkflowStatus =
          event.event === 'workflow_completed' ? 'completed'
          : event.event === 'workflow_failed' ? 'failed'
          : 'running';

        // Merge per-agent progress if the event carries it
        const agentName = event.data?.agent as string | undefined;
        const agentProg = agentName
          ? {
              ...prev.agentProgress,
              [agentName]: {
                agent: agentName,
                status:
                  event.event === 'agent_completed' ? 'completed'
                  : event.event === 'agent_started' ? 'running'
                  : 'running',
                progress: typeof event.data?.progress === 'number' ? event.data.progress : 0,
                message: event.data?.message as string | undefined,
                elements_found: event.data?.elements_found as number | undefined,
                scenarios_generated: event.data?.scenarios_generated as number | undefined,
                tests_generated: event.data?.tests_generated as number | undefined,
              } as AgentProgress,
            }
          : prev.agentProgress;

        return {
          ...prev,
          status: nextStatus,
          currentAgent: agentName ?? prev.currentAgent,
          agentProgress: agentProg,
          error: (event.data?.error as string) ?? null,
          isConnected: !isTerminal(nextStatus),
          isLoading: false,
        };
      });

      if (['workflow_completed', 'workflow_failed'].includes(event.event)) {
        stopSSE();
      }
    },
    [stopPolling, stopSSE] // eslint-disable-line react-hooks/exhaustive-deps
  );

  // ---- poll once ----
  const pollOnce = useCallback(async () => {
    const id = workflowIdRef.current;
    if (!id) return;
    try {
      const res = await agentWorkflowService.getWorkflowStatus(id);
      applyStatusResponse(res);
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Polling error',
        isLoading: false,
      }));
    }
  }, [applyStatusResponse]);

  const startPolling = useCallback(() => {
    stopPolling();
    pollOnce();
    pollTimerRef.current = setInterval(pollOnce, POLL_INTERVAL_MS);
  }, [pollOnce, stopPolling]);

  // ---- cancel (public) ----
  const cancel = useCallback(async () => {
    const id = workflowIdRef.current;
    stopPolling();
    stopSSE();
    setState((prev) => ({ ...prev, status: 'cancelled', isConnected: false }));
    if (id) {
      try { await agentWorkflowService.cancelWorkflow(id); } catch { /* best-effort */ }
    }
  }, [stopPolling, stopSSE]);

  // ---- main effect ----
  useEffect(() => {
    if (!workflowId) {
      stopPolling();
      stopSSE();
      setState(INITIAL_STATE);
      return;
    }

    sseGotEventRef.current = false;
    setState({ ...INITIAL_STATE, isLoading: true, isConnected: true });

    // Start SSE
    const subId = sseService.connect(workflowId, applySSEEvent);
    sseSubIdRef.current = subId;

    // Immediate poll so we don't wait for first SSE frame
    pollOnce();

    // Start polling as fallback if SSE delivers nothing after timeout
    const fallbackTimer = setTimeout(() => {
      if (!sseGotEventRef.current) {
        startPolling();
      }
    }, SSE_FALLBACK_TIMEOUT_MS);

    return () => {
      clearTimeout(fallbackTimer);
      stopPolling();
      stopSSE();
    };
  }, [workflowId]); // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, cancel };
}
