/**
 * Unit tests for AgentWorkflowTrigger component
 *
 * Sprint 10 Phase 2 — Developer B
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentWorkflowTrigger } from '../components/AgentWorkflowTrigger';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGenerateTests = vi.fn();

vi.mock('../../../services/agentWorkflowService', () => ({
  default: {
    generateTests: (...args: unknown[]) => mockGenerateTests(...args),
  },
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AgentWorkflowTrigger', () => {
  const onWorkflowStarted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockGenerateTests.mockResolvedValue({
      workflow_id: 'wf-test-001',
      status: 'pending',
      message: 'Queued',
      estimated_duration_seconds: 45,
    });
  });

  it('renders the form with expected fields', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    expect(screen.getByTestId('url-input')).toBeInTheDocument();
    expect(screen.getByTestId('max-tests-input')).toBeInTheDocument();
    expect(screen.getByTestId('assertions-checkbox')).toBeInTheDocument();
    expect(screen.getByTestId('context-textarea')).toBeInTheDocument();
    expect(screen.getByTestId('generate-button')).toBeInTheDocument();
  });

  it('shows an error if the user submits without a URL', async () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    // Submit the form directly (bypasses native HTML5 validation in jsdom)
    fireEvent.submit(screen.getByTestId('agent-workflow-form'));

    await waitFor(() => {
      expect(screen.getByTestId('submit-error')).toBeInTheDocument();
    });
    expect(onWorkflowStarted).not.toHaveBeenCalled();
  });

  it('calls generateTests with the correct payload on valid submit', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.clear(screen.getByTestId('url-input'));
    await user.type(screen.getByTestId('url-input'), 'https://example.com');

    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({ url: 'https://example.com' })
      );
    });
  });

  it('invokes onWorkflowStarted with the returned workflow_id', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(onWorkflowStarted).toHaveBeenCalledWith('wf-test-001');
    });
  });

  it('shows a loading state while submitting', async () => {
    // Never resolves during this test
    mockGenerateTests.mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();

    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  it('shows error message when generateTests rejects', async () => {
    mockGenerateTests.mockRejectedValue(new Error('Server error'));
    const user = userEvent.setup();

    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(screen.getByTestId('submit-error')).toHaveTextContent('Server error');
    });
    expect(onWorkflowStarted).not.toHaveBeenCalled();
  });

  it('includes include_assertions in the request by default', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({ include_assertions: true })
      );
    });
  });
});
