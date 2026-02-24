/**
 * useWorkflowProgress — React hook
 *
 * Sprint 10 Phase 2 — Developer B
 *
 * Connects to the SSE stream for a running workflow and provides
 * live progress updates.  Falls back to polling every POLL_INTERVAL_MS
 * when SSE is not supported or when the EventSource errors out.
 *
 * Usage:
 *   const { status, progress, error, isConnected, cancel } =
 *     useWorkflowProgress(workflowId);
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { AgentProgress, AgentProgressEvent, WorkflowStatus } from '../../../types/agentWorkflow.types';
import sseService from '../../../services/sseService';
import agentWorkflowService from '../../../services/agentWorkflowService';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 3_000;
const TERMINAL_STATUSES: WorkflowStatus[] = ['completed', 'failed', 'cancelled'];

// ---------------------------------------------------------------------------
// State Shape
// ---------------------------------------------------------------------------

export interface WorkflowProgressState {
  /** Latest lifecycle status, null while workflow_id is not yet set */
  status: WorkflowStatus | null;
  /** Granular progress detail; null until first update */
  progress: AgentProgress | null;
  /** Human-readable error message, present when status === 'failed' */
  error: string | null;
  /** True while the SSE stream (or polling) is active */
  isConnected: boolean;
  /** True during the initial load before any update arrives */
  isLoading: boolean;
}

const INITIAL_STATE: WorkflowProgressState = {
  status: null,
  progress: null,
  error: null,
  isConnected: false,
  isLoading: false,
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Subscribe to a workflow's progress via SSE (with polling fallback).
 *
 * @param workflowId  The workflow to track. Pass null/undefined to idle.
 * @returns           Live progress state and a cancel function.
 */
export function useWorkflowProgress(workflowId: string | null | undefined): WorkflowProgressState & {
  cancel: () => void;
} {
  const [state, setState] = useState<WorkflowProgressState>(INITIAL_STATE);

  // Stable refs so callbacks can always read the latest value
  const workflowIdRef = useRef<string | null | undefined>(workflowId);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sseSubIdRef = useRef<string | null>(null);
  const sseErroredRef = useRef(false);
  const sseReceivedEventRef = useRef(false);

  workflowIdRef.current = workflowId;

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

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

  const isTerminal = (s: WorkflowStatus | null) =>
    s !== null && TERMINAL_STATUSES.includes(s);

  // -------------------------------------------------------------------------
  // Apply an SSE event to local state
  // -------------------------------------------------------------------------
  const applyEvent = useCallback((event: AgentProgressEvent) => {
    setState((prev) => {
      const next: WorkflowProgressState = {
        ...prev,
        status: event.event_type === 'completed'
          ? 'completed'
          : event.event_type === 'failed'
          ? 'failed'
          : event.event_type === 'cancelled'
          ? 'cancelled'
          : 'running',
        progress: event.progress,
        error: event.error ?? null,
        isConnected: true,
        isLoading: false,
      };
      return next;
    });
  }, []);

  // -------------------------------------------------------------------------
  // Poll the status endpoint
  // -------------------------------------------------------------------------
  const pollOnce = useCallback(async () => {
    const id = workflowIdRef.current;
    if (!id) return;

    try {
      const response = await agentWorkflowService.getWorkflowStatus(id);
      setState((prev) => ({
        ...prev,
        status: response.status,
        progress: response.progress,
        error: response.error ?? null,
        isLoading: false,
      }));

      // Stop polling once workflow reaches a terminal state
      if (isTerminal(response.status)) {
        stopPolling();
        setState((prev) => ({ ...prev, isConnected: false }));
      }
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Polling error',
        isLoading: false,
      }));
    }
  }, [stopPolling]);

  const startPolling = useCallback(() => {
    stopPolling();
    pollOnce();
    pollTimerRef.current = setInterval(pollOnce, POLL_INTERVAL_MS);
  }, [pollOnce, stopPolling]);

  // -------------------------------------------------------------------------
  // Start SSE stream
  // -------------------------------------------------------------------------
  const startSSE = useCallback(
    (id: string) => {
      sseErroredRef.current = false;

      sseReceivedEventRef.current = false;

      const subId = sseService.connect(id, (event: AgentProgressEvent) => {
        sseReceivedEventRef.current = true;
        applyEvent(event);

        // Stop polling if SSE is now delivering updates
        stopPolling();

        if (isTerminal(event.event_type === 'completed'
          ? 'completed'
          : event.event_type === 'failed'
          ? 'failed'
          : event.event_type === 'cancelled'
          ? 'cancelled'
          : null)) {
          stopSSE();
          setState((prev) => ({ ...prev, isConnected: false }));
        }
      });

      sseSubIdRef.current = subId;

      // Kick off one polling pass immediately so we don't wait for first SSE frame
      pollOnce();

      // Ensure polling starts as fallback if SSE delivers nothing within 5 s
      const fallbackTimer = setTimeout(() => {
        // Start polling if SSE errored OR if SSE never delivered any event
        // (covers mock mode where SSE silently does nothing)
        if (!sseErroredRef.current && sseReceivedEventRef.current) return;
        startPolling();
      }, 5_000);

      return () => clearTimeout(fallbackTimer);
    },
    [applyEvent, pollOnce, startPolling, stopPolling, stopSSE]
  );

  // -------------------------------------------------------------------------
  // Cancel (public API)
  // -------------------------------------------------------------------------
  const cancel = useCallback(async () => {
    const id = workflowIdRef.current;
    stopPolling();
    stopSSE();
    setState((prev) => ({ ...prev, status: 'cancelled', isConnected: false }));
    if (id) {
      try {
        await agentWorkflowService.cancelWorkflow(id);
      } catch {
        // Best-effort cancel
      }
    }
  }, [stopPolling, stopSSE]);

  // -------------------------------------------------------------------------
  // Main effect — reacts to workflowId changes
  // -------------------------------------------------------------------------
  useEffect(() => {
    // Reset when no workflow is set
    if (!workflowId) {
      stopPolling();
      stopSSE();
      setState(INITIAL_STATE);
      return;
    }

    setState({ ...INITIAL_STATE, isLoading: true, isConnected: true });

    const cleanupFallback = startSSE(workflowId);

    return () => {
      cleanupFallback?.();
      stopPolling();
      stopSSE();
    };
  }, [workflowId]); // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, cancel };
}
