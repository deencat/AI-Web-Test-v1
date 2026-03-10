/**
 * Unit tests for AgentWorkflowTrigger — Real API integration (Sprint 10)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentWorkflowTrigger } from '../components/AgentWorkflowTrigger';
import type { WorkflowStatusResponse } from '../../../types/agentWorkflow.types';

const mockGenerateTests = vi.fn();

vi.mock('../../../services/agentWorkflowService', () => ({
  default: {
    generateTests: (...args: unknown[]) => mockGenerateTests(...args),
  },
}));

// Real API response shape (WorkflowStatusResponse, 202)
const MOCK_WORKFLOW_RESPONSE: WorkflowStatusResponse = {
  workflow_id: 'wf-real-001',
  status: 'pending',
  current_agent: null,
  progress: {},
  total_progress: 0.0,
  started_at: new Date().toISOString(),
  estimated_completion: null,
  error: null,
};

describe('AgentWorkflowTrigger', () => {
  const onWorkflowStarted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockGenerateTests.mockResolvedValue(MOCK_WORKFLOW_RESPONSE);
  });

  it('renders the form with expected fields', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    expect(screen.getByTestId('url-input')).toBeInTheDocument();
    expect(screen.getByTestId('instruction-input')).toBeInTheDocument();
    expect(screen.getByTestId('depth-select')).toBeInTheDocument();
    expect(screen.getByTestId('generate-button')).toBeInTheDocument();
  });

  it('shows an error if the user submits without a URL', async () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    fireEvent.submit(screen.getByTestId('agent-workflow-form'));
    await waitFor(() => {
      expect(screen.getByTestId('submit-error')).toBeInTheDocument();
    });
    expect(onWorkflowStarted).not.toHaveBeenCalled();
  });

  it('calls generateTests with the correct payload on valid submit', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('instruction-input'), 'Test login');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({ url: 'https://example.com', user_instruction: 'Test login' })
      );
    });
  });

  it('invokes onWorkflowStarted with the returned workflow_id', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(onWorkflowStarted).toHaveBeenCalledWith('wf-real-001');
    });
  });

  it('shows a loading state while submitting', async () => {
    mockGenerateTests.mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(screen.getByTestId('generate-button')).toBeDisabled();
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
  });

  // ---------------------------------------------------------------------------
  // Login credentials (website)
  // ---------------------------------------------------------------------------

  it('renders login credential fields', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    expect(screen.getByTestId('login-email-input')).toBeInTheDocument();
    expect(screen.getByTestId('login-password-input')).toBeInTheDocument();
    expect(screen.getByTestId('login-password-input')).toHaveAttribute('type', 'password');
  });

  it('includes login_credentials when website email and password are both filled', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('login-email-input'), 'user@example.com');
    await user.type(screen.getByTestId('login-password-input'), 'secret123');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          login_credentials: { email: 'user@example.com', password: 'secret123' },
        })
      );
    });
  });

  it('omits login_credentials when login email is empty', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('login-password-input'), 'secret123');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ login_credentials: expect.anything() })
      );
    });
  });

  it('omits login_credentials when login password is empty', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('login-email-input'), 'user@example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ login_credentials: expect.anything() })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // Gmail credentials (for OTP)
  // ---------------------------------------------------------------------------

  it('renders Gmail credential fields', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    expect(screen.getByTestId('gmail-email-input')).toBeInTheDocument();
    expect(screen.getByTestId('gmail-password-input')).toBeInTheDocument();
    expect(screen.getByTestId('gmail-password-input')).toHaveAttribute('type', 'password');
  });

  it('includes gmail_credentials when Gmail email and password are both filled', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('gmail-email-input'), 'user@gmail.com');
    await user.type(screen.getByTestId('gmail-password-input'), 'gmailpass');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          gmail_credentials: { email: 'user@gmail.com', password: 'gmailpass' },
        })
      );
    });
  });

  it('omits gmail_credentials when Gmail email is empty', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('gmail-password-input'), 'gmailpass');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ gmail_credentials: expect.anything() })
      );
    });
  });

  it('omits gmail_credentials when Gmail password is empty', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('gmail-email-input'), 'user@gmail.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ gmail_credentials: expect.anything() })
      );
    });
  });

  it('includes both login_credentials and gmail_credentials when all credential fields are filled', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.type(screen.getByTestId('login-email-input'), 'user@example.com');
    await user.type(screen.getByTestId('login-password-input'), 'websitepass');
    await user.type(screen.getByTestId('gmail-email-input'), 'user@gmail.com');
    await user.type(screen.getByTestId('gmail-password-input'), 'gmailpass');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          login_credentials: { email: 'user@example.com', password: 'websitepass' },
          gmail_credentials: { email: 'user@gmail.com', password: 'gmailpass' },
        })
      );
    });
  });
});
