/**
 * Unit tests for StopAgentButton — Sprint 10 (10B.12)
 *
 * TDD: Tests written BEFORE implementation.
 * Covers: enabled/disabled states, click behaviour, confirmation feedback.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StopAgentButton } from '../components/StopAgentButton';
import type { WorkflowStatus } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('StopAgentButton', () => {
  const onStop = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --- Rendering ---

  it('renders the stop button with expected text', () => {
    render(<StopAgentButton workflowStatus="running" onStop={onStop} />);
    expect(screen.getByTestId('stop-agent-button')).toBeInTheDocument();
    expect(screen.getByTestId('stop-agent-button')).toHaveTextContent('Stop Agent');
  });

  it('includes the stop icon character', () => {
    render(<StopAgentButton workflowStatus="running" onStop={onStop} />);
    expect(screen.getByTestId('stop-agent-button').textContent).toContain('⏹');
  });

  // --- Disabled states ---

  it.each(['completed', 'failed', 'cancelled'] as WorkflowStatus[])(
    'is disabled when workflowStatus is "%s"',
    (status) => {
      render(<StopAgentButton workflowStatus={status} onStop={onStop} />);
      expect(screen.getByTestId('stop-agent-button')).toBeDisabled();
    }
  );

  it('is disabled when workflowStatus is null', () => {
    render(<StopAgentButton workflowStatus={null} onStop={onStop} />);
    expect(screen.getByTestId('stop-agent-button')).toBeDisabled();
  });

  it('is disabled when isLoading is true (even if status is running)', () => {
    render(<StopAgentButton workflowStatus="running" onStop={onStop} isLoading={true} />);
    expect(screen.getByTestId('stop-agent-button')).toBeDisabled();
  });

  // --- Enabled states ---

  it.each(['running', 'pending'] as WorkflowStatus[])(
    'is enabled when workflowStatus is "%s"',
    (status) => {
      render(<StopAgentButton workflowStatus={status} onStop={onStop} />);
      expect(screen.getByTestId('stop-agent-button')).not.toBeDisabled();
    }
  );

  // --- Click behaviour ---

  it('calls onStop once when clicked', async () => {
    const user = userEvent.setup();
    render(<StopAgentButton workflowStatus="running" onStop={onStop} />);
    await user.click(screen.getByTestId('stop-agent-button'));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it('does NOT call onStop when button is disabled (completed)', async () => {
    const user = userEvent.setup();
    render(<StopAgentButton workflowStatus="completed" onStop={onStop} />);
    await user.click(screen.getByTestId('stop-agent-button'));
    expect(onStop).not.toHaveBeenCalled();
  });

  it('does NOT call onStop when button is disabled (null status)', async () => {
    const user = userEvent.setup();
    render(<StopAgentButton workflowStatus={null} onStop={onStop} />);
    await user.click(screen.getByTestId('stop-agent-button'));
    expect(onStop).not.toHaveBeenCalled();
  });

  // --- Confirmation toast feedback ---

  it('shows a confirmation message after clicking stop', async () => {
    const user = userEvent.setup();
    render(<StopAgentButton workflowStatus="running" onStop={onStop} />);
    expect(screen.queryByTestId('stop-confirmation')).not.toBeInTheDocument();
    await user.click(screen.getByTestId('stop-agent-button'));
    expect(screen.getByTestId('stop-confirmation')).toBeInTheDocument();
  });

  it('confirmation message contains stopping text', async () => {
    const user = userEvent.setup();
    render(<StopAgentButton workflowStatus="pending" onStop={onStop} />);
    await user.click(screen.getByTestId('stop-agent-button'));
    expect(screen.getByTestId('stop-confirmation').textContent?.toLowerCase()).toContain('stop');
  });

  it('does NOT show confirmation before any interaction', () => {
    render(<StopAgentButton workflowStatus="running" onStop={onStop} />);
    expect(screen.queryByTestId('stop-confirmation')).not.toBeInTheDocument();
  });

  // --- Accessibility ---

  it('has an aria-label on the button', () => {
    render(<StopAgentButton workflowStatus="running" onStop={onStop} />);
    expect(screen.getByTestId('stop-agent-button')).toHaveAttribute('aria-label');
  });
});
