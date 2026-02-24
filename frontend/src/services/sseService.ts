/**
 * SSE Service — Mock Stub
 *
 * Sprint 10 Phase 1 — API Contract Definition (Developer B)
 *
 * Provides a mock implementation of the Server-Sent Events client.
 * In production this will open a real EventSource to:
 *   GET /api/v2/workflows/{workflow_id}/stream
 *
 * In mock mode (or in tests), use simulateEvent() to fire callbacks directly.
 *
 * Usage:
 *   const subId = sseService.connect(workflowId, (event) => { ... });
 *   sseService.disconnect(subId);
 */
import type { AgentProgressEvent, WorkflowEventCallback } from '../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Internal Types
// ---------------------------------------------------------------------------

interface Subscription {
  subscriptionId: string;
  workflowId: string;
  callback: WorkflowEventCallback;
  /** Real EventSource instance — null while in mock mode */
  eventSource: EventSource | null;
}

// ---------------------------------------------------------------------------
// SSEService
// ---------------------------------------------------------------------------

class SSEService {
  private readonly sseBaseUrl = '/api/v2/workflows';
  private subscriptions: Map<string, Subscription> = new Map();

  /**
   * Connect to the workflow SSE stream.
   * In mock mode no real HTTP connection is opened.
   *
   * @param workflowId  Workflow to subscribe to
   * @param callback    Called with each AgentProgressEvent
   * @returns subscriptionId  Use this to disconnect later
   */
  connect(workflowId: string, callback: WorkflowEventCallback): string {
    const subscriptionId = `sub-${workflowId}-${Math.random().toString(36).slice(2, 8)}`;

    const isMock = this.isMockMode();
    let eventSource: EventSource | null = null;

    if (!isMock) {
      const url = `${this.sseBaseUrl}/${workflowId}/stream`;
      eventSource = new EventSource(url);

      eventSource.onmessage = (messageEvent: MessageEvent) => {
        try {
          const event: AgentProgressEvent = JSON.parse(messageEvent.data as string);
          callback(event);
        } catch {
          console.error('[SSEService] Failed to parse SSE event:', messageEvent.data);
        }
      };

      eventSource.onerror = (err) => {
        console.error('[SSEService] SSE stream error for workflow', workflowId, err);
      };
    }

    this.subscriptions.set(subscriptionId, {
      subscriptionId,
      workflowId,
      callback,
      eventSource,
    });

    return subscriptionId;
  }

  /**
   * Disconnect a specific subscription by id.
   *
   * @returns true if the subscription existed and was removed, false otherwise
   */
  disconnect(subscriptionId: string): boolean {
    const sub = this.subscriptions.get(subscriptionId);
    if (!sub) return false;

    sub.eventSource?.close();
    this.subscriptions.delete(subscriptionId);
    return true;
  }

  /**
   * Disconnect all active subscriptions.
   */
  disconnectAll(): void {
    for (const sub of this.subscriptions.values()) {
      sub.eventSource?.close();
    }
    this.subscriptions.clear();
  }

  /**
   * Check whether a subscription is currently active.
   */
  isConnected(subscriptionId: string): boolean {
    return this.subscriptions.has(subscriptionId);
  }

  /**
   * Return the total number of active subscriptions.
   */
  getActiveCount(): number {
    return this.subscriptions.size;
  }

  /**
   * Manually push an event to all subscribers of a workflow.
   * Used in mock mode and unit tests to simulate SSE events without a real server.
   *
   * @param workflowId  Target workflow id
   * @param event       AgentProgressEvent to deliver
   */
  simulateEvent(workflowId: string, event: AgentProgressEvent): void {
    for (const sub of this.subscriptions.values()) {
      if (sub.workflowId === workflowId) {
        sub.callback(event);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Private Helpers
  // ---------------------------------------------------------------------------

  private isMockMode(): boolean {
    return import.meta.env.VITE_USE_MOCK !== 'false';
  }
}

export default new SSEService();
