/**
 * Unit tests for AgentStatusMonitor — Sprint 10 (10B.11)
 *
 * TDD: Tests written BEFORE implementation.
 * Covers: agent timeline rendering, status states, log viewer toggle, metrics,
 *         loading/error states, edge cases (empty progress, null status).
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentStatusMonitor } from '../components/AgentStatusMonitor';
import type { AgentProgress, WorkflowStatus } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeProgress(overrides: Partial<AgentProgress> = {}): AgentProgress {
  return {
    agent: 'observation',
    status: 'running',
    progress: 0.5,
    message: null,
    ...overrides,
  };
}

const RUNNING_PROGRESS: Record<string, AgentProgress> = {
  observation: makeProgress({
    agent: 'observation',
    status: 'completed',
    progress: 1,
    message: '38 elements found',
    elements_found: 38,
    duration_seconds: 12,
    confidence: 0.9,
  }),
  requirements: makeProgress({
    agent: 'requirements',
    status: 'running',
    progress: 0.5,
    message: 'Generating BDD scenarios...',
    scenarios_generated: 8,
  }),
};

const COMPLETED_PROGRESS: Record<string, AgentProgress> = {
  observation: makeProgress({ agent: 'observation', status: 'completed', progress: 1, message: 'Done' }),
  requirements: makeProgress({ agent: 'requirements', status: 'completed', progress: 1, message: 'Done', scenarios_generated: 12 }),
  analysis: makeProgress({ agent: 'analysis', status: 'completed', progress: 1, message: 'Done' }),
  evolution: makeProgress({
    agent: 'evolution',
    status: 'completed',
    progress: 1,
    message: 'Done',
    tests_generated: 17,
    duration_seconds: 45,
  }),
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AgentStatusMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --- Core rendering ---

  it('renders the monitor container', () => {
    render(
      <AgentStatusMonitor
        workflowStatus={null}
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
      />
    );
    expect(screen.getByTestId('agent-status-monitor')).toBeInTheDocument();
  });

  it('renders all 4 agent stage rows', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('agent-stage-observation')).toBeInTheDocument();
    expect(screen.getByTestId('agent-stage-requirements')).toBeInTheDocument();
    expect(screen.getByTestId('agent-stage-analysis')).toBeInTheDocument();
    expect(screen.getByTestId('agent-stage-evolution')).toBeInTheDocument();
  });

  // --- Status states ---

  it('marks a completed agent with data-status="completed"', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('agent-stage-observation')).toHaveAttribute('data-status', 'completed');
  });

  it('marks the current agent with data-status="running"', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('agent-stage-requirements')).toHaveAttribute('data-status', 'running');
  });

  it('marks future agents with data-status="pending"', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('agent-stage-analysis')).toHaveAttribute('data-status', 'pending');
    expect(screen.getByTestId('agent-stage-evolution')).toHaveAttribute('data-status', 'pending');
  });

  it('marks all agents completed when workflowStatus is "completed"', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="completed"
        agentProgress={COMPLETED_PROGRESS}
        currentAgent={null}
        totalProgress={1}
      />
    );
    expect(screen.getByTestId('agent-stage-observation')).toHaveAttribute('data-status', 'completed');
    expect(screen.getByTestId('agent-stage-requirements')).toHaveAttribute('data-status', 'completed');
    expect(screen.getByTestId('agent-stage-analysis')).toHaveAttribute('data-status', 'completed');
    expect(screen.getByTestId('agent-stage-evolution')).toHaveAttribute('data-status', 'completed');
  });

  // --- Messages ---

  it('shows the agent message from agentProgress', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByText('Generating BDD scenarios...')).toBeInTheDocument();
  });

  // --- Metrics ---

  it('shows elements_found metric for observation agent', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('metric-elements-observation').textContent).toContain('38');
  });

  it('shows scenarios_generated metric for requirements agent', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('metric-scenarios-requirements').textContent).toContain('8');
  });

  it('shows tests_generated metric for evolution agent', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="completed"
        agentProgress={COMPLETED_PROGRESS}
        currentAgent={null}
        totalProgress={1}
      />
    );
    expect(screen.getByTestId('metric-tests-evolution').textContent).toContain('17');
  });

  it('shows confidence metric for observation agent', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('metric-confidence-observation').textContent).toContain('90');
  });

  // --- Progress bar ---

  it('displays the overall progress percentage', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('overall-progress-pct')).toHaveTextContent('35%');
  });

  // --- Log viewer toggle ---

  it('renders the "View Logs" toggle button', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('toggle-logs-button')).toBeInTheDocument();
  });

  it('hides the log viewer by default', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.queryByTestId('log-viewer')).not.toBeInTheDocument();
  });

  it('shows the log viewer after clicking "View Logs"', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    fireEvent.click(screen.getByTestId('toggle-logs-button'));
    expect(screen.getByTestId('log-viewer')).toBeInTheDocument();
  });

  it('hides the log viewer after toggling twice', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    fireEvent.click(screen.getByTestId('toggle-logs-button'));
    fireEvent.click(screen.getByTestId('toggle-logs-button'));
    expect(screen.queryByTestId('log-viewer')).not.toBeInTheDocument();
  });

  it('shows log entries from agentProgress messages when logs are expanded', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    fireEvent.click(screen.getByTestId('toggle-logs-button'));
    expect(screen.getByTestId('log-viewer').textContent).toContain('38 elements found');
  });

  it('shows "No log entries yet" when agentProgress has no messages', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={{ observation: makeProgress({ message: null }) }}
        currentAgent="observation"
        totalProgress={0.1}
      />
    );
    fireEvent.click(screen.getByTestId('toggle-logs-button'));
    expect(screen.getByTestId('log-viewer').textContent).toContain('No log entries yet');
  });

  it('toggle button shows "Hide Logs" when expanded', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    fireEvent.click(screen.getByTestId('toggle-logs-button'));
    expect(screen.getByTestId('toggle-logs-button').textContent).toContain('Hide Logs');
  });

  it('toggle button shows "View Logs" when collapsed', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('toggle-logs-button').textContent).toContain('View Logs');
  });

  // --- Loading state ---

  it('shows a loading indicator when isLoading is true', () => {
    render(
      <AgentStatusMonitor
        workflowStatus={null}
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
        isLoading={true}
      />
    );
    expect(screen.getByTestId('status-loading')).toBeInTheDocument();
  });

  it('does NOT show loading indicator when isLoading is false', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
        isLoading={false}
      />
    );
    expect(screen.queryByTestId('status-loading')).not.toBeInTheDocument();
  });

  // --- Error state ---

  it('shows the error message when error prop is set', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="failed"
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
        error="Network error: connection refused"
      />
    );
    expect(screen.getByText(/Network error: connection refused/i)).toBeInTheDocument();
  });

  it('does NOT show error element when error is null', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
        error={null}
      />
    );
    expect(screen.queryByTestId('status-error')).not.toBeInTheDocument();
  });

  // --- Edge cases ---

  it('renders without crashing when agentProgress is empty', () => {
    render(
      <AgentStatusMonitor
        workflowStatus={null}
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
      />
    );
    expect(screen.getByTestId('agent-status-monitor')).toBeInTheDocument();
  });

  it('renders 0% progress when totalProgress is 0', () => {
    render(
      <AgentStatusMonitor
        workflowStatus={null}
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
      />
    );
    expect(screen.getByTestId('overall-progress-pct')).toHaveTextContent('0%');
  });

  it('renders 100% progress when totalProgress is 1', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="completed"
        agentProgress={COMPLETED_PROGRESS}
        currentAgent={null}
        totalProgress={1}
      />
    );
    expect(screen.getByTestId('overall-progress-pct')).toHaveTextContent('100%');
  });
});
