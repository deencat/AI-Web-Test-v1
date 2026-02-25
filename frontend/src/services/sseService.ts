/**
 * SSE Service — Real EventSource implementation (Sprint 10)
 *
 * Opens a real EventSource to:
 *   GET /api/v2/workflows/{workflow_id}/stream
 *
 * Named SSE events from the backend:
 *   agent_started | agent_progress | agent_completed |
 *   workflow_completed | workflow_failed
 *
 * Usage:
 *   const subId = sseService.connect(workflowId, (event) => { ... });
 *   sseService.disconnect(subId);
 */
import type { AgentProgressEvent, WorkflowEventCallback } from '../types/agentWorkflow.types';

const SSE_BASE = '/api/v2/workflows';

const SSE_EVENT_TYPES = [
  'agent_started',
  'agent_progress',
  'agent_completed',
  'workflow_completed',
  'workflow_failed',
] as const;

interface Subscription {
  subscriptionId: string;
  workflowId: string;
  callback: WorkflowEventCallback;
  eventSource: EventSource;
}

class SSEService {
  private subscriptions = new Map<string, Subscription>();

  /**
   * Connect to the real SSE stream for a workflow.
   *
   * @param workflowId  Workflow to subscribe to
   * @param callback    Called with each AgentProgressEvent
   * @returns subscriptionId  Use this to disconnect later
   */
  connect(workflowId: string, callback: WorkflowEventCallback): string {
    const subscriptionId = `sub-${workflowId}-${Math.random().toString(36).slice(2, 8)}`;
    const url = `${SSE_BASE}/${workflowId}/stream`;
    const eventSource = new EventSource(url);

    // The backend sends named events; attach a listener for each type
    for (const eventType of SSE_EVENT_TYPES) {
      eventSource.addEventListener(eventType, (messageEvent: MessageEvent) => {
        try {
          const parsed = JSON.parse(messageEvent.data as string) as AgentProgressEvent;
          callback(parsed);
        } catch (err) {
          console.error(`[SSEService] Failed to parse "${eventType}" event:`, err);
        }
      });
    }

    // Fallback for generic messages (no event name)
    eventSource.onmessage = (messageEvent: MessageEvent) => {
      try {
        const parsed = JSON.parse(messageEvent.data as string) as AgentProgressEvent;
        callback(parsed);
      } catch {
        // Ignore unparseable keepalives
      }
    };

    eventSource.onerror = (err) => {
      console.error('[SSEService] SSE stream error for workflow', workflowId, err);
    };

    this.subscriptions.set(subscriptionId, {
      subscriptionId,
      workflowId,
      callback,
      eventSource,
    });

    return subscriptionId;
  }

  /**
   * Disconnect a specific subscription.
   * @returns true if the subscription existed and was removed
   */
  disconnect(subscriptionId: string): boolean {
    const sub = this.subscriptions.get(subscriptionId);
    if (!sub) return false;
    sub.eventSource.close();
    this.subscriptions.delete(subscriptionId);
    return true;
  }

  /** Close all active subscriptions. */
  disconnectAll(): void {
    for (const sub of this.subscriptions.values()) {
      sub.eventSource.close();
    }
    this.subscriptions.clear();
  }

  /** Check whether a subscription is active. */
  isConnected(subscriptionId: string): boolean {
    return this.subscriptions.has(subscriptionId);
  }

  /** Total active subscriptions. */
  getActiveCount(): number {
    return this.subscriptions.size;
  }
}

export default new SSEService();
