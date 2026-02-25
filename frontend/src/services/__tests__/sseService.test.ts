/**
 * Tests for sseService.ts — Real EventSource implementation (Sprint 10)
 *
 * Strategy: mock the global EventSource so tests run without a real HTTP server.
 * Verified behaviors:
 *   - connect() opens an EventSource at the correct URL
 *   - connect() registers named event listeners for all 5 SSE event types
 *   - connect() returns a unique subscription id
 *   - disconnect() closes the EventSource and removes the subscription
 *   - disconnectAll() closes every active EventSource
 *   - isConnected() / getActiveCount() reflect subscription state
 *   - Callbacks are fired with correctly-parsed AgentProgressEvent payloads
 *   - Parsing errors do not throw (they are silently logged)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { AgentProgressEvent } from '../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Mock EventSource
// ---------------------------------------------------------------------------

type Listener = (event: MessageEvent) => void;

class MockEventSource {
  static instances: MockEventSource[] = [];

  public onmessage: Listener | null = null;
  public onerror: ((e: Event) => void) | null = null;
  public close = vi.fn();
  private listenerMap = new Map<string, Listener[]>();

  constructor(public readonly url: string) {
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: Listener): void {
    const current = this.listenerMap.get(type) ?? [];
    this.listenerMap.set(type, [...current, listener]);
  }

  /** Test helper — fire a named SSE event to registered listeners. */
  triggerEvent(type: string, data: unknown): void {
    const event = new MessageEvent(type, { data: JSON.stringify(data) });
    (this.listenerMap.get(type) ?? []).forEach((l) => l(event));
  }

  /** Test helper — fire the generic onmessage handler. */
  triggerMessage(data: unknown): void {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  /** Returns the listeners registered for a given event type. */
  getListeners(type: string): Listener[] {
    return this.listenerMap.get(type) ?? [];
  }
}

// Install the mock globally before importing the service
vi.stubGlobal('EventSource', MockEventSource);

// ---------------------------------------------------------------------------
// Import service AFTER stubbing EventSource
// ---------------------------------------------------------------------------
import sseService from '../../services/sseService';

// ---------------------------------------------------------------------------
// Lifecycle helpers
// ---------------------------------------------------------------------------

beforeEach(() => {
  MockEventSource.instances = [];
  vi.clearAllMocks();
  sseService.disconnectAll();
  MockEventSource.instances = [];
});

afterEach(() => {
  sseService.disconnectAll();
  MockEventSource.instances = [];
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AGENT_PROGRESS_EVENT: AgentProgressEvent = {
  event: 'agent_progress',
  data: { agent: 'observation', status: 'running', progress: 0.5 },
  timestamp: new Date().toISOString(),
};

const WORKFLOW_COMPLETED_EVENT: AgentProgressEvent = {
  event: 'workflow_completed',
  data: { workflow_id: 'wf-001', status: 'completed', total_progress: 1.0 },
  timestamp: new Date().toISOString(),
};

// ---------------------------------------------------------------------------
// connect()
// ---------------------------------------------------------------------------

describe('connect()', () => {
  it('returns a non-empty subscription id', () => {
    const id = sseService.connect('wf-001', vi.fn());
    expect(typeof id).toBe('string');
    expect(id.length).toBeGreaterThan(0);
  });

  it('returns unique ids for different workflows', () => {
    const id1 = sseService.connect('wf-001', vi.fn());
    const id2 = sseService.connect('wf-002', vi.fn());
    expect(id1).not.toBe(id2);
  });

  it('returns unique ids for the same workflow (multiple subscribers)', () => {
    const id1 = sseService.connect('wf-001', vi.fn());
    const id2 = sseService.connect('wf-001', vi.fn());
    expect(id1).not.toBe(id2);
  });

  it('opens EventSource at the correct URL', () => {
    sseService.connect('wf-abc-123', vi.fn());
    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].url).toBe('/api/v2/workflows/wf-abc-123/stream');
  });

  it('registers named listeners for all 5 SSE event types', () => {
    sseService.connect('wf-001', vi.fn());
    const es = MockEventSource.instances[0];
    for (const type of [
      'agent_started',
      'agent_progress',
      'agent_completed',
      'workflow_completed',
      'workflow_failed',
    ]) {
      expect(es.getListeners(type).length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// disconnect()
// ---------------------------------------------------------------------------

describe('disconnect()', () => {
  it('returns true for an active subscription', () => {
    const id = sseService.connect('wf-001', vi.fn());
    expect(sseService.disconnect(id)).toBe(true);
  });

  it('returns false for an unknown subscription id', () => {
    expect(sseService.disconnect('non-existent-id')).toBe(false);
  });

  it('calls EventSource.close()', () => {
    const id = sseService.connect('wf-001', vi.fn());
    const es = MockEventSource.instances[0];
    sseService.disconnect(id);
    expect(es.close).toHaveBeenCalledOnce();
  });

  it('makes isConnected return false', () => {
    const id = sseService.connect('wf-001', vi.fn());
    sseService.disconnect(id);
    expect(sseService.isConnected(id)).toBe(false);
  });

  it('does not throw when called twice for the same id', () => {
    const id = sseService.connect('wf-001', vi.fn());
    sseService.disconnect(id);
    expect(() => sseService.disconnect(id)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// disconnectAll()
// ---------------------------------------------------------------------------

describe('disconnectAll()', () => {
  it('does not throw when there are no subscriptions', () => {
    expect(() => sseService.disconnectAll()).not.toThrow();
  });

  it('closes all EventSources', () => {
    sseService.connect('wf-001', vi.fn());
    sseService.connect('wf-002', vi.fn());
    sseService.disconnectAll();
    expect(MockEventSource.instances[0].close).toHaveBeenCalledOnce();
    expect(MockEventSource.instances[1].close).toHaveBeenCalledOnce();
  });

  it('sets getActiveCount to 0', () => {
    sseService.connect('wf-001', vi.fn());
    sseService.connect('wf-002', vi.fn());
    sseService.disconnectAll();
    expect(sseService.getActiveCount()).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// isConnected()
// ---------------------------------------------------------------------------

describe('isConnected()', () => {
  it('returns true for an active subscription', () => {
    const id = sseService.connect('wf-001', vi.fn());
    expect(sseService.isConnected(id)).toBe(true);
  });

  it('returns false after disconnection', () => {
    const id = sseService.connect('wf-001', vi.fn());
    sseService.disconnect(id);
    expect(sseService.isConnected(id)).toBe(false);
  });

  it('returns false for unknown id', () => {
    expect(sseService.isConnected('ghost-id')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// getActiveCount()
// ---------------------------------------------------------------------------

describe('getActiveCount()', () => {
  it('returns 0 when no subscriptions', () => {
    expect(sseService.getActiveCount()).toBe(0);
  });

  it('increments on each connect()', () => {
    sseService.connect('wf-001', vi.fn());
    expect(sseService.getActiveCount()).toBe(1);
    sseService.connect('wf-002', vi.fn());
    expect(sseService.getActiveCount()).toBe(2);
  });

  it('decrements on disconnect()', () => {
    const id = sseService.connect('wf-001', vi.fn());
    sseService.connect('wf-002', vi.fn());
    sseService.disconnect(id);
    expect(sseService.getActiveCount()).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Callback delivery via named events
// ---------------------------------------------------------------------------

describe('callback delivery', () => {
  it('calls callback when a named agent_progress event fires', () => {
    const callback = vi.fn();
    sseService.connect('wf-001', callback);
    const es = MockEventSource.instances[0];

    es.triggerEvent('agent_progress', AGENT_PROGRESS_EVENT);

    expect(callback).toHaveBeenCalledOnce();
    expect(callback).toHaveBeenCalledWith(AGENT_PROGRESS_EVENT);
  });

  it('calls callback when a workflow_completed event fires', () => {
    const callback = vi.fn();
    sseService.connect('wf-001', callback);
    const es = MockEventSource.instances[0];

    es.triggerEvent('workflow_completed', WORKFLOW_COMPLETED_EVENT);

    expect(callback).toHaveBeenCalledOnce();
    expect(callback).toHaveBeenCalledWith(WORKFLOW_COMPLETED_EVENT);
  });

  it('calls callback via generic onmessage fallback', () => {
    const callback = vi.fn();
    sseService.connect('wf-001', callback);
    const es = MockEventSource.instances[0];

    es.triggerMessage(AGENT_PROGRESS_EVENT);

    expect(callback).toHaveBeenCalledOnce();
  });

  it('does not throw when event data is malformed JSON', () => {
    sseService.connect('wf-001', vi.fn());
    const es = MockEventSource.instances[0];
    const badEvent = new MessageEvent('agent_progress', { data: '{not: valid json}' });
    expect(() =>
      es.getListeners('agent_progress').forEach((l) => l(badEvent))
    ).not.toThrow();
  });

  it('delivers events to multiple subscribers of the same workflow independently', () => {
    const cb1 = vi.fn();
    const cb2 = vi.fn();
    sseService.connect('wf-shared', cb1);
    sseService.connect('wf-shared', cb2);

    // Two separate EventSource instances — each fires its own event
    MockEventSource.instances[0].triggerEvent('agent_progress', AGENT_PROGRESS_EVENT);
    MockEventSource.instances[1].triggerEvent('agent_progress', AGENT_PROGRESS_EVENT);

    expect(cb1).toHaveBeenCalledOnce();
    expect(cb2).toHaveBeenCalledOnce();
  });
});
