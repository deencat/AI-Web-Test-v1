/**
 * Tests for sseService.ts (mock stub)
 * Verifies the SSE client stub correctly manages subscriptions
 * and fires callbacks with mock AgentProgressEvent payloads.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import sseService from '../../services/sseService';
import type { AgentProgressEvent } from '../../types/agentWorkflow.types';

describe('sseService - Mock SSE Stub', () => {
  beforeEach(() => {
    // Disconnect any lingering connections between tests
    sseService.disconnectAll();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  // ---------------------------------------------------------------------------
  // connect / disconnect lifecycle
  // ---------------------------------------------------------------------------
  describe('connect()', () => {
    it('should return a subscription id when connecting to a workflow stream', () => {
      const subscriptionId = sseService.connect('wf-mock-001', vi.fn());
      expect(typeof subscriptionId).toBe('string');
      expect(subscriptionId.length).toBeGreaterThan(0);
    });

    it('should return unique subscription ids for different workflows', () => {
      const id1 = sseService.connect('wf-mock-001', vi.fn());
      const id2 = sseService.connect('wf-mock-002', vi.fn());
      expect(id1).not.toBe(id2);
    });
  });

  describe('disconnect()', () => {
    it('should disconnect a specific subscription without throwing', () => {
      const subscriptionId = sseService.connect('wf-mock-001', vi.fn());
      expect(() => sseService.disconnect(subscriptionId)).not.toThrow();
    });

    it('should return true when disconnecting an active subscription', () => {
      const subscriptionId = sseService.connect('wf-mock-001', vi.fn());
      expect(sseService.disconnect(subscriptionId)).toBe(true);
    });

    it('should return false when disconnecting a non-existent subscription', () => {
      expect(sseService.disconnect('nonexistent-sub-id')).toBe(false);
    });
  });

  describe('disconnectAll()', () => {
    it('should disconnect all active subscriptions without throwing', () => {
      sseService.connect('wf-001', vi.fn());
      sseService.connect('wf-002', vi.fn());
      expect(() => sseService.disconnectAll()).not.toThrow();
    });
  });

  // ---------------------------------------------------------------------------
  // isConnected
  // ---------------------------------------------------------------------------
  describe('isConnected()', () => {
    it('should return true for an active subscription', () => {
      const subscriptionId = sseService.connect('wf-mock-001', vi.fn());
      expect(sseService.isConnected(subscriptionId)).toBe(true);
    });

    it('should return false after disconnecting', () => {
      const subscriptionId = sseService.connect('wf-mock-001', vi.fn());
      sseService.disconnect(subscriptionId);
      expect(sseService.isConnected(subscriptionId)).toBe(false);
    });

    it('should return false for an unknown subscription id', () => {
      expect(sseService.isConnected('unknown-id')).toBe(false);
    });
  });

  // ---------------------------------------------------------------------------
  // getActiveCount
  // ---------------------------------------------------------------------------
  describe('getActiveCount()', () => {
    it('should return 0 when there are no active subscriptions', () => {
      expect(sseService.getActiveCount()).toBe(0);
    });

    it('should increment when a subscription is connected', () => {
      sseService.connect('wf-001', vi.fn());
      expect(sseService.getActiveCount()).toBe(1);
    });

    it('should decrement when a subscription is disconnected', () => {
      const id = sseService.connect('wf-001', vi.fn());
      sseService.connect('wf-002', vi.fn());
      sseService.disconnect(id);
      expect(sseService.getActiveCount()).toBe(1);
    });

    it('should return 0 after disconnectAll', () => {
      sseService.connect('wf-001', vi.fn());
      sseService.connect('wf-002', vi.fn());
      sseService.disconnectAll();
      expect(sseService.getActiveCount()).toBe(0);
    });
  });

  // ---------------------------------------------------------------------------
  // Mock event delivery (simulated SSE events)
  // ---------------------------------------------------------------------------
  describe('simulateEvent() - mock event delivery', () => {
    it('should call the registered callback when an event is simulated', () => {
      const callback = vi.fn();
      sseService.connect('wf-mock-001', callback);

      const event: AgentProgressEvent = {
        workflow_id: 'wf-mock-001',
        event_type: 'progress',
        progress: { stage: 'generating', percentage: 50, message: 'Half way' },
        timestamp: new Date().toISOString(),
      };

      sseService.simulateEvent('wf-mock-001', event);
      expect(callback).toHaveBeenCalledOnce();
      expect(callback).toHaveBeenCalledWith(event);
    });

    it('should not call callback for a different workflow id', () => {
      const callback = vi.fn();
      sseService.connect('wf-mock-001', callback);

      const event: AgentProgressEvent = {
        workflow_id: 'wf-mock-002',
        event_type: 'progress',
        progress: { stage: 'analyzing', percentage: 20, message: 'Analyzing' },
        timestamp: new Date().toISOString(),
      };

      sseService.simulateEvent('wf-mock-002', event);
      expect(callback).not.toHaveBeenCalled();
    });

    it('should not call callback after disconnection', () => {
      const callback = vi.fn();
      const id = sseService.connect('wf-mock-001', callback);
      sseService.disconnect(id);

      const event: AgentProgressEvent = {
        workflow_id: 'wf-mock-001',
        event_type: 'completed',
        progress: { stage: 'complete', percentage: 100, message: 'Done' },
        timestamp: new Date().toISOString(),
      };

      sseService.simulateEvent('wf-mock-001', event);
      expect(callback).not.toHaveBeenCalled();
    });

    it('should deliver events to all subscribers of the same workflow', () => {
      const cb1 = vi.fn();
      const cb2 = vi.fn();
      sseService.connect('wf-shared', cb1);
      sseService.connect('wf-shared', cb2);

      const event: AgentProgressEvent = {
        workflow_id: 'wf-shared',
        event_type: 'progress',
        progress: { stage: 'validating', percentage: 75, message: 'Validating' },
        timestamp: new Date().toISOString(),
      };

      sseService.simulateEvent('wf-shared', event);
      expect(cb1).toHaveBeenCalledOnce();
      expect(cb2).toHaveBeenCalledOnce();
    });
  });
});
