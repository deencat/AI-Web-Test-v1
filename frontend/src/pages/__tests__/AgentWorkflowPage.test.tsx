import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentWorkflowPage } from '../AgentWorkflowPage';

const mockUseWorkflowProgress = vi.fn();
const mockCancel = vi.fn();
const mockPipeline = vi.fn(() => <div data-testid="pipeline" />);
const mockStatusMonitor = vi.fn(() => <div data-testid="status-monitor" />);

vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div data-testid="layout">{children}</div>,
}));

vi.mock('../../features/agent-workflow', () => ({
  AgentWorkflowTrigger: ({ onWorkflowStarted }: { onWorkflowStarted: (id: string) => void }) => (
    <button data-testid="start-workflow" onClick={() => onWorkflowStarted('wf-123')}>Start</button>
  ),
  AgentProgressPipeline: (props: unknown) => mockPipeline(props),
  AgentStatusMonitor: (props: unknown) => mockStatusMonitor(props),
  WorkflowResults: () => <div data-testid="results" />,
  useWorkflowProgress: (workflowId: string | null) => mockUseWorkflowProgress(workflowId),
}));

describe('AgentWorkflowPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseWorkflowProgress.mockReturnValue({
      status: null,
      progress: null,
      error: null,
      agentProgress: {},
      currentAgent: null,
      totalProgress: 0,
      isLoading: false,
      cancel: mockCancel,
    });
  });

  it('wires stop action and structured monitor when workflow is active', () => {
    render(<AgentWorkflowPage />);

    fireEvent.click(screen.getByTestId('start-workflow'));

    mockUseWorkflowProgress.mockReturnValue({
      status: 'running',
      progress: { currentAgent: 'requirements', percentage: 30, message: 'Running...', agentProgress: {} },
      error: null,
      agentProgress: { requirements: { agent: 'requirements', status: 'running', progress: 0.3 } },
      currentAgent: 'requirements',
      totalProgress: 0.3,
      isLoading: false,
      cancel: mockCancel,
    });

    render(<AgentWorkflowPage />);

    expect(screen.getByTestId('status-monitor')).toBeInTheDocument();
    expect(screen.getByTestId('pipeline')).toBeInTheDocument();

    const pipelineProps = mockPipeline.mock.calls[mockPipeline.mock.calls.length - 1][0] as { onStop?: () => void };
    expect(typeof pipelineProps.onStop).toBe('function');

    pipelineProps.onStop?.();
    expect(mockCancel).toHaveBeenCalledTimes(1);
  });
});
