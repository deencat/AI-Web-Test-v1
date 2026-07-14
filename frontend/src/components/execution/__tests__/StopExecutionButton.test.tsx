/**
 * Unit tests for StopExecutionButton
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StopExecutionButton } from '../StopExecutionButton';
import type { ExecutionStatus } from '../../../types/execution';

describe('StopExecutionButton', () => {
  const onStop = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the stop button with expected text', () => {
    render(<StopExecutionButton executionStatus="running" onStop={onStop} />);
    expect(screen.getByTestId('stop-execution-button')).toBeInTheDocument();
    expect(screen.getByTestId('stop-execution-button')).toHaveTextContent('Stop Execution');
  });

  it('includes the stop icon character', () => {
    render(<StopExecutionButton executionStatus="running" onStop={onStop} />);
    expect(screen.getByTestId('stop-execution-button').textContent).toContain('⏹');
  });

  it.each(['completed', 'failed', 'cancelled'] as ExecutionStatus[])(
    'is disabled when executionStatus is "%s"',
    (status) => {
      render(<StopExecutionButton executionStatus={status} onStop={onStop} />);
      expect(screen.getByTestId('stop-execution-button')).toBeDisabled();
    }
  );

  it('is disabled when executionStatus is null', () => {
    render(<StopExecutionButton executionStatus={null} onStop={onStop} />);
    expect(screen.getByTestId('stop-execution-button')).toBeDisabled();
  });

  it('is disabled when isLoading is true (even if status is running)', () => {
    render(<StopExecutionButton executionStatus="running" onStop={onStop} isLoading={true} />);
    expect(screen.getByTestId('stop-execution-button')).toBeDisabled();
  });

  it.each(['running', 'pending'] as ExecutionStatus[])(
    'is enabled when executionStatus is "%s"',
    (status) => {
      render(<StopExecutionButton executionStatus={status} onStop={onStop} />);
      expect(screen.getByTestId('stop-execution-button')).not.toBeDisabled();
    }
  );

  it('calls onStop once when clicked', async () => {
    const user = userEvent.setup();
    render(<StopExecutionButton executionStatus="running" onStop={onStop} />);
    await user.click(screen.getByTestId('stop-execution-button'));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it('does NOT call onStop when button is disabled (completed)', async () => {
    const user = userEvent.setup();
    render(<StopExecutionButton executionStatus="completed" onStop={onStop} />);
    await user.click(screen.getByTestId('stop-execution-button'));
    expect(onStop).not.toHaveBeenCalled();
  });

  it('does NOT call onStop when button is disabled (null status)', async () => {
    const user = userEvent.setup();
    render(<StopExecutionButton executionStatus={null} onStop={onStop} />);
    await user.click(screen.getByTestId('stop-execution-button'));
    expect(onStop).not.toHaveBeenCalled();
  });

  it('shows a confirmation message after clicking stop', async () => {
    const user = userEvent.setup();
    render(<StopExecutionButton executionStatus="running" onStop={onStop} />);
    expect(screen.queryByTestId('stop-execution-confirmation')).not.toBeInTheDocument();
    await user.click(screen.getByTestId('stop-execution-button'));
    expect(screen.getByTestId('stop-execution-confirmation')).toBeInTheDocument();
  });

  it('confirmation message contains stopping text', async () => {
    const user = userEvent.setup();
    render(<StopExecutionButton executionStatus="pending" onStop={onStop} />);
    await user.click(screen.getByTestId('stop-execution-button'));
    expect(screen.getByTestId('stop-execution-confirmation').textContent?.toLowerCase()).toContain('stop');
  });

  it('does NOT show confirmation before any interaction', () => {
    render(<StopExecutionButton executionStatus="running" onStop={onStop} />);
    expect(screen.queryByTestId('stop-execution-confirmation')).not.toBeInTheDocument();
  });

  it('has an aria-label on the button', () => {
    render(<StopExecutionButton executionStatus="running" onStop={onStop} />);
    expect(screen.getByTestId('stop-execution-button')).toHaveAttribute('aria-label');
  });
});
