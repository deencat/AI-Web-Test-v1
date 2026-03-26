/**
 * Unit tests for AgentWorkflowTrigger — Real API integration (Sprint 10)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentWorkflowTrigger } from '../components/AgentWorkflowTrigger';
import type { WorkflowStatusResponse } from '../../../types/agentWorkflow.types';
import type { BrowserProfileListResponse, BrowserProfileData } from '../../../types/browserProfile';

const mockGenerateTests = vi.fn();
const mockGetAllProfiles = vi.fn();
const mockLoadProfileSession = vi.fn();
const mockUploadWorkflowFile = vi.fn();

vi.mock('../../../services/agentWorkflowService', () => ({
  default: {
    generateTests: (...args: unknown[]) => mockGenerateTests(...args),
    uploadWorkflowFile: (...args: unknown[]) => mockUploadWorkflowFile(...args),
  },
}));

vi.mock('../../../services/browserProfileService', () => ({
  default: {
    getAllProfiles: (...args: unknown[]) => mockGetAllProfiles(...args),
    loadProfileSession: (...args: unknown[]) => mockLoadProfileSession(...args),
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

const MOCK_PROFILE_RESPONSE: BrowserProfileListResponse = {
  profiles: [
    {
      id: 7,
      user_id: 1,
      profile_name: 'Three HK Logged In',
      os_type: 'linux',
      browser_type: 'chromium',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      has_session_data: true,
      has_http_credentials: true,
      http_username: 'uat_user',
    },
  ],
  total: 1,
};

const MOCK_PROFILE_DATA: BrowserProfileData = {
  cookies: [],
  localStorage: { journey: 'active' },
  sessionStorage: { selectedPlan: 'world' },
  http_credentials: { username: 'uat_user', password: 'secret' },
  exported_at: new Date().toISOString(),
};

describe('AgentWorkflowTrigger', () => {
  const onWorkflowStarted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockGenerateTests.mockResolvedValue(MOCK_WORKFLOW_RESPONSE);
    mockGetAllProfiles.mockResolvedValue(MOCK_PROFILE_RESPONSE);
    mockLoadProfileSession.mockResolvedValue(MOCK_PROFILE_DATA);
    mockUploadWorkflowFile.mockResolvedValue({
      server_path: '/uploads/workflow-files/abc123/hkid.jpg',
      filename: 'hkid.jpg',
      size: 1024,
    });
  });

  it('renders the form with expected fields', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);
    expect(screen.getByTestId('url-input')).toBeInTheDocument();
    expect(screen.getByTestId('instruction-input')).toBeInTheDocument();
    expect(screen.getByTestId('depth-select')).toBeInTheDocument();
    expect(screen.getByTestId('browser-profile-select')).toBeInTheDocument();
    expect(screen.getByTestId('generate-button')).toBeInTheDocument();
  });

  it('loads available browser profiles for selection', async () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await waitFor(() => {
      expect(mockGetAllProfiles).toHaveBeenCalled();
    });

    expect(screen.getByRole('option', { name: /Three HK Logged In/i })).toBeInTheDocument();
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

  // ---------------------------------------------------------------------------
  // HTTP Basic auth credentials (preprod)
  // ---------------------------------------------------------------------------

  it('keeps HTTP Basic auth fields collapsed by default', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    expect(screen.queryByTestId('http-username-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('http-password-input')).not.toBeInTheDocument();
  });

  it('shows HTTP Basic auth fields when expanded', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.click(screen.getByTestId('http-auth-toggle'));

    expect(screen.getByTestId('http-username-input')).toBeInTheDocument();
    expect(screen.getByTestId('http-password-input')).toBeInTheDocument();
    expect(screen.getByTestId('http-password-input')).toHaveAttribute('type', 'password');
  });

  it('includes http_credentials when both HTTP Basic auth fields are filled', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://wwwuat.three.com.hk');
    await user.click(screen.getByTestId('http-auth-toggle'));
    await user.type(screen.getByTestId('http-username-input'), 'uat_user');
    await user.type(screen.getByTestId('http-password-input'), 'uat_pass');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          http_credentials: { username: 'uat_user', password: 'uat_pass' },
        })
      );
    });
  });

  it('omits http_credentials when only HTTP username is filled', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://wwwuat.three.com.hk');
    await user.click(screen.getByTestId('http-auth-toggle'));
    await user.type(screen.getByTestId('http-username-input'), 'uat_user');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ http_credentials: expect.anything() })
      );
    });
  });

  it('omits http_credentials when only HTTP password is filled', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://wwwuat.three.com.hk');
    await user.click(screen.getByTestId('http-auth-toggle'));
    await user.type(screen.getByTestId('http-password-input'), 'uat_pass');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ http_credentials: expect.anything() })
      );
    });
  });

  it('loads selected browser profile session data and includes it in the request', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await waitFor(() => {
      expect(mockGetAllProfiles).toHaveBeenCalled();
    });

    await user.type(screen.getByTestId('url-input'), 'https://wwwuat.three.com.hk');
    await user.selectOptions(screen.getByTestId('browser-profile-select'), '7');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockLoadProfileSession).toHaveBeenCalledWith(7);
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          browser_profile_data: MOCK_PROFILE_DATA,
          http_credentials: { username: 'uat_user', password: 'secret' },
        })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // Sprint 10.8 — AgentWorkflowTrigger Missing Fields
  // ---------------------------------------------------------------------------

  it('Advanced options section is collapsed by default', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    const details = screen.getByTestId('advanced-options');
    expect(details).toBeInTheDocument();
    expect(details).not.toHaveAttribute('open');
  });

  it('Adding a file path and submitting includes available_file_paths in payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    // Switch to manual path mode first, then type the path
    await user.click(screen.getByTestId('file-path-toggle-0'));
    await user.type(screen.getByTestId('file-path-input-0'), 'C:\\Users\\test\\file.jpg');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          available_file_paths: ['C:\\Users\\test\\file.jpg'],
        })
      );
    });
  });

  it('Blank file path entries are filtered before submission', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    // Default first entry is blank — do not type anything
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ available_file_paths: expect.anything() })
      );
    });
  });

  it('Checking functional + accessibility scenario types includes scenario_types in payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('scenario-type-functional'));
    await user.click(screen.getByTestId('scenario-type-accessibility'));
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          scenario_types: expect.arrayContaining(['functional', 'accessibility']),
        })
      );
    });

    const call = mockGenerateTests.mock.calls[0][0];
    expect(call.scenario_types).toHaveLength(2);
  });

  it('Leaving scenario types unchecked omits scenario_types from payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ scenario_types: expect.anything() })
      );
    });
  });

  it('Setting max_scenarios to 12 includes max_scenarios: 12 in payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.clear(screen.getByTestId('max-scenarios-input'));
    await user.type(screen.getByTestId('max-scenarios-input'), '12');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({ max_scenarios: 12 })
      );
    });
  });

  it('Leaving max_scenarios empty omits field from payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ max_scenarios: expect.anything() })
      );
    });
  });

  it('Setting max_browser_steps to 200 includes max_browser_steps: 200 in payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.clear(screen.getByTestId('max-browser-steps-input'));
    await user.type(screen.getByTestId('max-browser-steps-input'), '200');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({ max_browser_steps: 200 })
      );
    });
  });

  it('Enabling focus_goal_only includes focus_goal_only: true in payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('focus-goal-only-checkbox'));
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({ focus_goal_only: true })
      );
    });
  });

  it('focus_goal_only unchecked omits field from payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    // focus_goal_only default is unchecked — do not click
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ focus_goal_only: expect.anything() })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // Sprint 10.8 — Hybrid file upload / path input
  // ---------------------------------------------------------------------------

  it('file entry row shows upload button and path toggle by default', () => {
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    expect(screen.getByTestId('file-upload-btn-0')).toBeInTheDocument();
    expect(screen.getByTestId('file-path-toggle-0')).toBeInTheDocument();
  });

  it('clicking "type path instead" toggle shows text input', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.click(screen.getByTestId('file-path-toggle-0'));

    expect(screen.getByTestId('file-path-input-0')).toBeInTheDocument();
  });

  it('uploading a file calls uploadWorkflowFile and shows filename', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    const file = new File([new Uint8Array(100)], 'hkid.jpg', { type: 'image/jpeg' });
    const hiddenInput = screen.getByTestId('file-input-0');
    await user.upload(hiddenInput, file);

    await waitFor(() => {
      expect(mockUploadWorkflowFile).toHaveBeenCalledWith(file);
    });
    expect(screen.getByText('hkid.jpg')).toBeInTheDocument();
  });

  it('uploaded server path is included in payload as available_file_paths', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    const file = new File([new Uint8Array(100)], 'hkid.jpg', { type: 'image/jpeg' });
    await user.upload(screen.getByTestId('file-input-0'), file);

    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          available_file_paths: ['/uploads/workflow-files/abc123/hkid.jpg'],
        })
      );
    });
  });

  it('typed server path is included in payload when using path mode', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    await user.click(screen.getByTestId('file-path-toggle-0'));
    await user.type(screen.getByTestId('file-path-input-0'), '/server/path/file.jpg');
    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.objectContaining({
          available_file_paths: ['/server/path/file.jpg'],
        })
      );
    });
  });

  it('upload error is shown inline when uploadWorkflowFile rejects', async () => {
    mockUploadWorkflowFile.mockRejectedValue(new Error('File type not allowed'));
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    const file = new File([new Uint8Array(10)], 'bad.exe', { type: 'application/octet-stream' });
    await user.upload(screen.getByTestId('file-input-0'), file);

    await waitFor(() => {
      expect(screen.getByTestId('file-upload-error-0')).toHaveTextContent('File type not allowed');
    });
  });

  it('row with no upload and blank path is omitted from payload', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflowTrigger onWorkflowStarted={onWorkflowStarted} />);

    // Do not interact with file row — leave blank
    await user.type(screen.getByTestId('url-input'), 'https://example.com');
    await user.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockGenerateTests).toHaveBeenCalledWith(
        expect.not.objectContaining({ available_file_paths: expect.anything() })
      );
    });
  });
});
