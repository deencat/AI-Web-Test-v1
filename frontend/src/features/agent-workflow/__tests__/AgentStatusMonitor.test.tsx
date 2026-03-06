/**
 * Unit tests for AgentStatusMonitor — simplified Stage Details panel
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentStatusMonitor } from '../components/AgentStatusMonitor';
import type { AgentProgress } from '../../../types/agentWorkflow.types';

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
    message: 'Found 38 elements',
    elements_found: 38,
    confidence: 0.9,
  }),
  requirements: makeProgress({
    agent: 'requirements',
    status: 'running',
    progress: 0.47,
    message: 'Generating 8 BDD scenarios...',
    scenarios_generated: 8,
  }),
};

describe('AgentStatusMonitor (simplified)', () => {
  it('renders stage details panel', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('agent-status-monitor')).toBeInTheDocument();
    expect(screen.getByTestId('current-stage-card')).toBeInTheDocument();
  });

  it('shows current stage name and status', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('current-stage-name')).toHaveTextContent('Requirements');
    expect(screen.getByTestId('current-stage-status')).toHaveTextContent('running');
  });

  it('shows current stage message', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('current-stage-message')).toHaveTextContent('Generating 8 BDD scenarios...');
  });

  it('shows in-stage progress when progress is available', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('current-stage-progress')).toBeInTheDocument();
    expect(screen.getByTestId('current-stage-progress-pct')).toHaveTextContent('47%');
  });

  it('shows focused-stage metrics', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('metric-scenarios-current')).toHaveTextContent('8');
  });

  it('shows completed stage chips', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.getByTestId('completed-observation')).toBeInTheDocument();
  });

  it('does not show raw logs UI controls', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={RUNNING_PROGRESS}
        currentAgent="requirements"
        totalProgress={0.35}
      />
    );
    expect(screen.queryByTestId('toggle-logs-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('log-viewer')).not.toBeInTheDocument();
  });

  it('shows loading indicator when loading', () => {
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

  it('shows error state when provided', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="failed"
        agentProgress={{}}
        currentAgent={null}
        totalProgress={0}
        error="Workflow failed"
      />
    );
    expect(screen.getByTestId('status-error')).toHaveTextContent('Workflow failed');
  });

  it('shows None yet when no stages are completed', () => {
    render(
      <AgentStatusMonitor
        workflowStatus="running"
        agentProgress={{
          observation: makeProgress({ agent: 'observation', status: 'running', progress: 0.15 }),
        }}
        currentAgent="observation"
        totalProgress={0.1}
      />
    );
    expect(screen.getByTestId('no-completed-stages')).toBeInTheDocument();
  });
});
