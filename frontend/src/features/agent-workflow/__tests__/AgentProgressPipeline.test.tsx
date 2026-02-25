/**
 * Unit tests for AgentProgressPipeline component — Real API integration (Sprint 10)
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentProgressPipeline } from '../components/AgentProgressPipeline';
import type { DisplayProgress, WorkflowStatus } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeProgress(
  currentAgent: DisplayProgress['currentAgent'] = 'observation',
  percentage = 25,
  message = 'Observing page…'
): DisplayProgress {
  return {
    currentAgent,
    percentage,
    message,
    agentProgress: {
      observation: {
        agent: 'observation',
        status: currentAgent === 'observation' ? 'running' : 'completed',
        progress: percentage / 100,
        message,
      },
    },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AgentProgressPipeline', () => {
  it('renders without crashing when props are null', () => {
    render(<AgentProgressPipeline workflowStatus={null} progress={null} />);
    expect(screen.getByTestId('agent-progress-pipeline')).toBeInTheDocument();
  });

  it('shows the current workflow status badge', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress()}
      />
    );
    expect(screen.getByTestId('workflow-status-badge')).toHaveTextContent('running');
  });

  it('displays the progress percentage', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress('requirements', 40, 'Generating…')}
      />
    );
    const pct = screen.getByTestId('progress-percentage');
    expect(pct).toHaveTextContent('40%');
  });

  it('marks the active stage with aria-current="step"', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress('observation')}
      />
    );
    const activeStage = screen.getByTestId('stage-observation');
    expect(activeStage).toHaveAttribute('aria-current', 'step');
  });

  it('does NOT mark non-active stages with aria-current', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress('observation')}
      />
    );
    const pendingStage = screen.getByTestId('stage-requirements');
    expect(pendingStage).not.toHaveAttribute('aria-current');
  });

  it('shows the error panel when error prop is provided', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="failed"
        progress={makeProgress('observation', 25, 'Error')}
        error="Something went wrong"
      />
    );
    expect(screen.getByTestId('workflow-error')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-error')).toHaveTextContent('Something went wrong');
  });

  it('shows 100% and complete stage when workflow is completed', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="completed"
        progress={makeProgress('complete', 100, 'Done!')}
      />
    );
    expect(screen.getByTestId('progress-percentage')).toHaveTextContent('100%');
    expect(screen.getByTestId('workflow-status-badge')).toHaveTextContent('completed');
  });
});
