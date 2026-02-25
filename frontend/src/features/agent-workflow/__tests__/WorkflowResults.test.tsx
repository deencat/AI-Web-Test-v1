/**
 * Unit tests for WorkflowResults component — Real API integration (Sprint 10)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { WorkflowResults } from '../components/WorkflowResults';
import type { WorkflowResultsResponse } from '../../../types/agentWorkflow.types';

const mockGetWorkflowResults = vi.fn();

vi.mock('../../../services/agentWorkflowService', () => ({
  default: {
    getWorkflowResults: (...args: unknown[]) => mockGetWorkflowResults(...args),
  },
}));

// ---------------------------------------------------------------------------
// Fixtures — real API shape
// ---------------------------------------------------------------------------

const MOCK_RESULTS: WorkflowResultsResponse = {
  workflow_id: 'wf-test-001',
  status: 'completed',
  test_case_ids: [101, 102, 103],
  test_count: 3,
  observation_result: {
    ui_elements: [{}, {}],
    page_context: { url: 'https://example.com', title: 'Example' },
  },
  requirements_result: {
    scenarios: [{ title: 'Login' }, { title: 'Checkout' }],
    coverage_metrics: {},
  },
  analysis_result: {
    risk_scores: [],
    final_prioritization: [],
  },
  evolution_result: {
    test_count: 3,
    test_case_ids: [101, 102, 103],
    test_cases: [
      {
        id: 101,
        title: 'Homepage loads correctly',
        description: 'Verify homepage renders',
        test_steps: [{ step: 1, action: 'navigate', target: 'https://example.com' }],
      },
    ],
  },
  completed_at: new Date().toISOString(),
  total_duration_seconds: 42,
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('WorkflowResults', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetWorkflowResults.mockResolvedValue(MOCK_RESULTS);
  });

  it('shows a loading indicator while fetching', async () => {
    mockGetWorkflowResults.mockReturnValue(new Promise(() => {}));
    render(<WorkflowResults workflowId="wf-test-001" />);
    expect(screen.getByTestId('results-loading')).toBeInTheDocument();
  });

  it('renders the results panel after fetch completes', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);
    await waitFor(() => {
      expect(screen.getByTestId('workflow-results')).toBeInTheDocument();
    });
  });

  it('displays the correct test count in the summary', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);
    await waitFor(() => {
      const summary = screen.getByTestId('results-summary');
      expect(summary).toHaveTextContent('3');
    });
  });

  it('displays total duration in the summary', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);
    await waitFor(() => {
      const summary = screen.getByTestId('results-summary');
      expect(summary).toHaveTextContent('42');
    });
  });

  it('shows error state when fetch fails', async () => {
    mockGetWorkflowResults.mockRejectedValue(new Error('Network failure'));
    render(<WorkflowResults workflowId="wf-fail" />);
    await waitFor(() => {
      expect(screen.getByTestId('results-error')).toBeInTheDocument();
    });
    expect(screen.getByText('Network failure')).toBeInTheDocument();
  });

  it('calls getWorkflowResults with the correct workflowId', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);
    await waitFor(() => {
      expect(mockGetWorkflowResults).toHaveBeenCalledWith('wf-test-001');
    });
  });

  it('shows test_case_ids count badge', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);
    await waitFor(() => {
      expect(screen.getByTestId('workflow-results')).toBeInTheDocument();
    });
    expect(screen.getByTestId('results-summary')).toHaveTextContent('3');
  });
});
