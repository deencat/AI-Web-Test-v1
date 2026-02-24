/**
 * Tests for agentWorkflow.types.ts
 * Validates that all API contract types are correctly shaped and exported.
 * These tests enforce the API contract agreed with Developer A (Sprint 10 Phase 1).
 */
import { describe, it, expect } from 'vitest';
import type {
  WorkflowId,
  WorkflowStatus,
  AgentStage,
  AgentProgress,
  GenerateTestsRequest,
  WorkflowStatusResponse,
  AgentProgressEvent,
  WorkflowResultsResponse,
  GeneratedTestCase,
} from '../../types/agentWorkflow.types';

describe('agentWorkflow.types - API Contract Types', () => {
  // ---------------------------------------------------------------------------
  // WorkflowId
  // ---------------------------------------------------------------------------
  describe('WorkflowId', () => {
    it('should accept a valid string workflow id', () => {
      const id: WorkflowId = 'wf-abc-123';
      expect(typeof id).toBe('string');
    });
  });

  // ---------------------------------------------------------------------------
  // WorkflowStatus
  // ---------------------------------------------------------------------------
  describe('WorkflowStatus', () => {
    it('should accept all valid status values', () => {
      const statuses: WorkflowStatus[] = [
        'pending',
        'running',
        'completed',
        'failed',
        'cancelled',
      ];
      expect(statuses).toHaveLength(5);
    });
  });

  // ---------------------------------------------------------------------------
  // AgentStage
  // ---------------------------------------------------------------------------
  describe('AgentStage', () => {
    it('should accept all valid stage values', () => {
      const stages: AgentStage[] = [
        'initializing',
        'analyzing',
        'generating',
        'validating',
        'complete',
      ];
      expect(stages).toHaveLength(5);
    });
  });

  // ---------------------------------------------------------------------------
  // AgentProgress
  // ---------------------------------------------------------------------------
  describe('AgentProgress', () => {
    it('should accept a fully populated AgentProgress object', () => {
      const progress: AgentProgress = {
        stage: 'generating',
        percentage: 60,
        message: 'Generating test steps...',
        current_step: 3,
        total_steps: 5,
      };
      expect(progress.percentage).toBe(60);
      expect(progress.stage).toBe('generating');
    });

    it('should allow optional fields to be omitted', () => {
      const progress: AgentProgress = {
        stage: 'analyzing',
        percentage: 20,
        message: 'Analyzing page structure',
      };
      expect(progress.current_step).toBeUndefined();
      expect(progress.total_steps).toBeUndefined();
    });
  });

  // ---------------------------------------------------------------------------
  // GenerateTestsRequest — mirrors Pydantic GenerateTestsRequest
  // ---------------------------------------------------------------------------
  describe('GenerateTestsRequest', () => {
    it('should accept a complete request object', () => {
      const request: GenerateTestsRequest = {
        url: 'https://example.com',
        test_types: ['smoke', 'regression'],
        max_tests: 10,
        browser: 'chromium',
        include_assertions: true,
        context: 'Login flow for admin users',
      };
      expect(request.url).toBe('https://example.com');
    });

    it('should allow optional fields to be omitted (only url required)', () => {
      const request: GenerateTestsRequest = { url: 'https://example.com' };
      expect(request.test_types).toBeUndefined();
      expect(request.max_tests).toBeUndefined();
    });
  });

  // ---------------------------------------------------------------------------
  // WorkflowStatusResponse — mirrors Pydantic WorkflowStatusResponse
  // ---------------------------------------------------------------------------
  describe('WorkflowStatusResponse', () => {
    it('should accept a complete status response object', () => {
      const response: WorkflowStatusResponse = {
        workflow_id: 'wf-abc-123',
        status: 'running',
        progress: {
          stage: 'generating',
          percentage: 55,
          message: 'Generating tests...',
        },
        created_at: '2026-02-23T10:00:00Z',
        updated_at: '2026-02-23T10:01:00Z',
      };
      expect(response.workflow_id).toBe('wf-abc-123');
      expect(response.status).toBe('running');
    });

    it('should allow optional error field', () => {
      const response: WorkflowStatusResponse = {
        workflow_id: 'wf-xyz-999',
        status: 'failed',
        progress: { stage: 'analyzing', percentage: 10, message: 'Failed' },
        created_at: '2026-02-23T10:00:00Z',
        updated_at: '2026-02-23T10:00:30Z',
        error: 'Page unreachable',
      };
      expect(response.error).toBe('Page unreachable');
    });
  });

  // ---------------------------------------------------------------------------
  // AgentProgressEvent — mirrors Pydantic AgentProgressEvent (SSE payload)
  // ---------------------------------------------------------------------------
  describe('AgentProgressEvent', () => {
    it('should accept a complete progress event', () => {
      const event: AgentProgressEvent = {
        workflow_id: 'wf-abc-123',
        event_type: 'progress',
        progress: {
          stage: 'validating',
          percentage: 85,
          message: 'Validating generated tests',
        },
        timestamp: '2026-02-23T10:01:30Z',
      };
      expect(event.event_type).toBe('progress');
    });

    it('should accept all valid event_type values', () => {
      const types: AgentProgressEvent['event_type'][] = [
        'progress',
        'completed',
        'failed',
        'cancelled',
      ];
      expect(types).toHaveLength(4);
    });
  });

  // ---------------------------------------------------------------------------
  // GeneratedTestCase — sub-type of WorkflowResultsResponse
  // ---------------------------------------------------------------------------
  describe('GeneratedTestCase', () => {
    it('should accept a complete generated test case', () => {
      const testCase: GeneratedTestCase = {
        id: 'tc-001',
        title: 'User can log in with valid credentials',
        description: 'Verify login flow',
        test_type: 'smoke',
        steps: [
          { step_number: 1, action: 'navigate', target: 'https://example.com/login', value: '' },
          { step_number: 2, action: 'fill', target: '#username', value: 'admin' },
        ],
        assertions: [{ assertion_type: 'visible', target: '.dashboard', expected_value: '' }],
        estimated_duration_seconds: 30,
        confidence_score: 0.92,
      };
      expect(testCase.confidence_score).toBe(0.92);
    });
  });

  // ---------------------------------------------------------------------------
  // WorkflowResultsResponse — mirrors Pydantic WorkflowResultsResponse
  // ---------------------------------------------------------------------------
  describe('WorkflowResultsResponse', () => {
    it('should accept a complete results response', () => {
      const results: WorkflowResultsResponse = {
        workflow_id: 'wf-abc-123',
        status: 'completed',
        test_cases: [],
        summary: {
          total_tests: 0,
          test_types: {},
          avg_confidence_score: 0,
          total_steps: 0,
        },
        generated_at: '2026-02-23T10:02:00Z',
      };
      expect(results.workflow_id).toBe('wf-abc-123');
      expect(results.test_cases).toEqual([]);
    });
  });
});
