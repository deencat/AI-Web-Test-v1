/**
 * useWorkflowProgress — React hook (Sprint 10 Real API)
 *
 * Connects to the SSE stream for a running workflow AND keeps a polling loop
 * running throughout. SSE provides real-time updates; polling (every
 * POLL_INTERVAL_MS) is a guaranteed safety net for when SSE events are
 * delayed by event-loop contention inside long-running LLM/browser-use calls.
 *
 * Usage:
 *   const { status, currentAgent, totalProgress, agentProgress, error, cancel } =
 *     useWorkflowProgress(workflowId);
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type {
  AgentProgress,
  AgentProgressEvent,
  DisplayProgress,
  WorkflowStatus,
} from '../../../types/agentWorkflow.types';
import sseService from '../../../services/sseService';
import agentWorkflowService from '../../../services/agentWorkflowService';

const POLL_INTERVAL_MS = 3_000;
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
          currentAgent: nextStatus === 'completed' ? null : (agentName ?? prev.currentAgent),
          totalProgress: typeof event.data?.total_progress === 'number'
            ? event.data.total_progress
            : prev.totalProgress,
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
    [stopSSE] // eslint-disable-line react-hooks/exhaustive-deps
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
    if (!id) return;

    // Keep SSE + polling active so UI reflects real backend state transition.
    // Cancellation is cooperative on the backend (checked between stages).
    setState((prev) => ({ ...prev, error: null }));
    try {
      await agentWorkflowService.cancelWorkflow(id);
      await pollOnce();
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Failed to cancel workflow',
      }));
    }
  }, [pollOnce]);

  // ---- main effect ----
  useEffect(() => {
    if (!workflowId) {
      stopPolling();
      stopSSE();
      setState(INITIAL_STATE);
      return;
    }

    setState({ ...INITIAL_STATE, isLoading: true, isConnected: true });
    const subId = sseService.connect(workflowId, applySSEEvent);
    sseSubIdRef.current = subId;

    // Poll immediately, then every POLL_INTERVAL_MS throughout the workflow.
    // Polling acts as a guaranteed safety net when SSE events are delayed
    // (e.g. event-loop contention during long-running LLM/browser-use calls).
    startPolling();

    return () => {
      stopPolling();
      stopSSE();
    };
  }, [workflowId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- derived DisplayProgress for AgentProgressPipeline ----
  const progress = useMemo<DisplayProgress | null>(() => {
    if (!state.currentAgent && state.totalProgress === 0 && !state.status) return null;

    // Derive percentage: prefer totalProgress from SSE/polling, otherwise count completed agents
    const AGENT_ORDER = ['observation', 'requirements', 'analysis', 'evolution'] as const;
    const completedCount = AGENT_ORDER.filter(
      (a) => state.agentProgress[a]?.status === 'completed'
    ).length;
    const derivedPercentage = state.totalProgress > 0
      ? Math.round(state.totalProgress * 100)
      : Math.round((completedCount / AGENT_ORDER.length) * 100);

    const AGENT_INDEX: Record<string, number> = {
      idle: -1,
      observation: 0,
      requirements: 1,
      analysis: 2,
      evolution: 3,
      complete: 4,
    };

    const stageFromProgress: DisplayProgress['currentAgent'] =
      state.totalProgress >= 1 ? 'complete'
      : state.totalProgress >= 0.80 ? 'evolution'
      : state.totalProgress >= 0.55 ? 'analysis'
      : state.totalProgress >= 0.30 ? 'requirements'
      : state.totalProgress >= 0.05 ? 'observation'
      : 'idle';

    const stageFromCurrent = (state.currentAgent ?? 'idle') as DisplayProgress['currentAgent'];
    const resolvedStage =
      AGENT_INDEX[stageFromCurrent] >= AGENT_INDEX[stageFromProgress]
        ? stageFromCurrent
        : stageFromProgress;

    return {
      currentAgent: resolvedStage,
      percentage: derivedPercentage,
      message: state.currentAgent ? `Running ${state.currentAgent} agent…` : (state.status ?? ''),
      agentProgress: state.agentProgress,
    };
  }, [state.currentAgent, state.totalProgress, state.agentProgress, state.status]);

  return { ...state, progress, cancel };
}
