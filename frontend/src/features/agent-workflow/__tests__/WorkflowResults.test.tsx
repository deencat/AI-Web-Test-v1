/**
 * Unit tests for WorkflowResults component
 *
 * Sprint 10 Phase 2 — Developer B
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { WorkflowResults } from '../components/WorkflowResults';
import type { WorkflowResultsResponse } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetWorkflowResults = vi.fn();

vi.mock('../../../services/agentWorkflowService', () => ({
  default: {
    getWorkflowResults: (...args: unknown[]) => mockGetWorkflowResults(...args),
  },
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_RESULTS: WorkflowResultsResponse = {
  workflow_id: 'wf-test-001',
  status: 'completed',
  test_cases: [
    {
      id: 'tc-001',
      title: 'Homepage loads correctly',
      description: 'Verify the homepage renders without errors',
      test_type: 'smoke',
      steps: [
        { step_number: 1, action: 'navigate', target: 'https://example.com', value: '' },
      ],
      assertions: [
        { assertion_type: 'visible', target: 'h1', expected_value: '', description: 'Heading visible' },
      ],
      estimated_duration_seconds: 8,
      confidence_score: 0.95,
      tags: ['smoke', 'homepage'],
    },
    {
      id: 'tc-002',
      title: 'Login flow with valid credentials',
      description: 'User can log in with correct details',
      test_type: 'regression',
      steps: [
        { step_number: 1, action: 'navigate', target: 'https://example.com/login', value: '' },
        { step_number: 2, action: 'fill', target: '#email', value: 'user@example.com' },
        { step_number: 3, action: 'click', target: '#submit', value: '' },
      ],
      assertions: [
        { assertion_type: 'url_contains', target: '', expected_value: '/dashboard' },
      ],
      estimated_duration_seconds: 12,
      confidence_score: 0.82,
      tags: ['regression', 'login'],
    },
  ],
  summary: {
    total_tests: 2,
    test_types: { smoke: 1, regression: 1 },
    avg_confidence_score: 0.885,
    total_steps: 4,
  },
  generated_at: new Date().toISOString(),
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
    // Keep promise pending to observe loading state
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
      expect(summary).toHaveTextContent('2');
    });
  });

  it('renders a card for each test case', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);

    await waitFor(() => {
      expect(screen.getByTestId('test-case-tc-001')).toBeInTheDocument();
      expect(screen.getByTestId('test-case-tc-002')).toBeInTheDocument();
    });
  });

  it('expands a test case card on click to reveal steps', async () => {
    render(<WorkflowResults workflowId="wf-test-001" />);

    await waitFor(() => screen.getByTestId('test-case-tc-001'));

    const expandButton = screen
      .getByTestId('test-case-tc-001')
      .querySelector('button')!;

    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText('navigate')).toBeInTheDocument();
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

  it('calls onReset when "New workflow" button is clicked', async () => {
    const onReset = vi.fn();
    render(<WorkflowResults workflowId="wf-test-001" onReset={onReset} />);

    await waitFor(() => screen.getByTestId('reset-button'));
    fireEvent.click(screen.getByTestId('reset-button'));

    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it('shows "no test cases" message when result is empty', async () => {
    mockGetWorkflowResults.mockResolvedValue({
      ...MOCK_RESULTS,
      test_cases: [],
      summary: { ...MOCK_RESULTS.summary, total_tests: 0, total_steps: 0 },
    });

    render(<WorkflowResults workflowId="wf-empty" />);

    await waitFor(() => {
      expect(screen.getByText(/no test cases were generated/i)).toBeInTheDocument();
    });
  });
});
