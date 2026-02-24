/**
 * Unit tests for AgentProgressPipeline component
 *
 * Sprint 10 Phase 2 — Developer B
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentProgressPipeline } from '../components/AgentProgressPipeline';
import type { AgentProgress, WorkflowStatus } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeProgress(
  stage: AgentProgress['stage'] = 'analyzing',
  percentage = 25,
  message = 'Observing page…'
): AgentProgress {
  return { stage, percentage, message };
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
        progress={makeProgress('generating', 60, 'Generating…')}
      />
    );
    const pct = screen.getByTestId('progress-percentage');
    expect(pct).toHaveTextContent('60%');
  });

  it('marks the active stage with aria-current="step"', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress('analyzing')}
      />
    );
    const activeStage = screen.getByTestId('stage-analyzing');
    expect(activeStage).toHaveAttribute('aria-current', 'step');
  });

  it('does NOT mark non-active stages with aria-current', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress('analyzing')}
      />
    );
    const pendingStage = screen.getByTestId('stage-generating');
    expect(pendingStage).not.toHaveAttribute('aria-current');
  });

  it('shows the error panel when error prop is provided', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="failed"
        progress={makeProgress('analyzing', 25, 'Error')}
        error="Something went wrong"
      />
    );
    const errorEl = screen.getByTestId('pipeline-error');
    expect(errorEl).toHaveTextContent('Something went wrong');
  });

  it('shows idle status when workflowStatus is null', () => {
    render(<AgentProgressPipeline workflowStatus={null} progress={null} />);
    expect(screen.getByTestId('workflow-status-badge')).toHaveTextContent('idle');
  });

  it.each<WorkflowStatus>(['pending', 'running', 'completed', 'failed', 'cancelled'])(
    'renders status badge for "%s"',
    (status) => {
      render(<AgentProgressPipeline workflowStatus={status} progress={null} />);
      expect(screen.getByTestId('workflow-status-badge')).toHaveTextContent(status);
    }
  );

  it('shows the progress bar with correct width style', () => {
    render(
      <AgentProgressPipeline
        workflowStatus="running"
        progress={makeProgress('generating', 70)}
      />
    );
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveStyle({ width: '70%' });
    expect(progressBar).toHaveAttribute('aria-valuenow', '70');
  });

  it('renders all five pipeline stages', () => {
    render(<AgentProgressPipeline workflowStatus={null} progress={null} />);
    const stageIds = ['initializing', 'analyzing', 'generating', 'validating', 'complete'];
    stageIds.forEach((id) => {
      expect(screen.getByTestId(`stage-${id}`)).toBeInTheDocument();
    });
  });
});
