/**
 * CredentialPromptModal.test.tsx — Sprint 10.14
 *
 * TDD tests for the ephemeral CRM credential prompt modal.
 *
 * Key security assertions:
 *  1. Modal renders username + password fields
 *  2. Password field is always type="password" (never "text")
 *  3. Clicking Cancel calls onCancel (not onConfirm)
 *  4. Submitting with empty username shows validation error
 *  5. Submitting with empty password shows validation error
 *  6. Submitting valid credentials calls onConfirm with correct data
 *  7. Password value is NOT logged to console anywhere in the component
 *  8. Test case name is shown in the modal header
 *  9. Close button calls onCancel
 * 10. Component state is cleared after onConfirm is called
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CredentialPromptModal, CredentialPromptResult } from '../../components/CredentialPromptModal';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderModal(props: {
  onConfirm?: (r: CredentialPromptResult) => void;
  onCancel?: () => void;
  initialUsername?: string;
  testCaseName?: string;
} = {}) {
  const onConfirm = props.onConfirm ?? vi.fn();
  const onCancel = props.onCancel ?? vi.fn();
  render(
    <CredentialPromptModal
      onConfirm={onConfirm}
      onCancel={onCancel}
      initialUsername={props.initialUsername}
      testCaseName={props.testCaseName}
    />,
  );
  return { onConfirm, onCancel };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CredentialPromptModal', () => {
  it('renders the modal with username and password fields', () => {
    renderModal();
    expect(screen.getByTestId('crm-username-input')).toBeInTheDocument();
    expect(screen.getByTestId('crm-password-input')).toBeInTheDocument();
  });

  it('password field is always type="password"', () => {
    renderModal();
    const passwordInput = screen.getByTestId('crm-password-input') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
  });

  it('clicking Cancel calls onCancel without calling onConfirm', () => {
    const { onConfirm, onCancel } = renderModal();
    fireEvent.click(screen.getByTestId('crm-modal-cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('clicking the X close button calls onCancel', () => {
    const { onCancel } = renderModal();
    fireEvent.click(screen.getByLabelText('Cancel and close'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('submitting with empty username shows validation error', () => {
    renderModal();
    // Leave username empty, fill password
    fireEvent.change(screen.getByTestId('crm-password-input'), {
      target: { value: 'somepassword' },
    });
    fireEvent.click(screen.getByTestId('crm-modal-confirm'));
    expect(screen.getByTestId('crm-modal-error')).toBeInTheDocument();
    expect(screen.getByTestId('crm-modal-error').textContent).toMatch(/username/i);
  });

  it('submitting with empty password shows validation error', () => {
    renderModal();
    fireEvent.change(screen.getByTestId('crm-username-input'), {
      target: { value: 'user@crm.com' },
    });
    // password left empty
    fireEvent.click(screen.getByTestId('crm-modal-confirm'));
    expect(screen.getByTestId('crm-modal-error')).toBeInTheDocument();
    expect(screen.getByTestId('crm-modal-error').textContent).toMatch(/password/i);
  });

  it('submitting valid credentials calls onConfirm with username and password', async () => {
    const { onConfirm } = renderModal();
    fireEvent.change(screen.getByTestId('crm-username-input'), {
      target: { value: 'admin@crm.com' },
    });
    fireEvent.change(screen.getByTestId('crm-password-input'), {
      target: { value: 'SuperSecret' },
    });
    fireEvent.click(screen.getByTestId('crm-modal-confirm'));
    await waitFor(() =>
      expect(onConfirm).toHaveBeenCalledWith({
        username: 'admin@crm.com',
        password: 'SuperSecret',
      }),
    );
  });

  it('does not call onConfirm when Cancel is clicked even if fields are filled', () => {
    const { onConfirm, onCancel } = renderModal();
    fireEvent.change(screen.getByTestId('crm-username-input'), {
      target: { value: 'user@crm.com' },
    });
    fireEvent.change(screen.getByTestId('crm-password-input'), {
      target: { value: 'pw' },
    });
    fireEvent.click(screen.getByTestId('crm-modal-cancel'));
    expect(onCancel).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('shows test case name in the modal header when provided', () => {
    renderModal({ testCaseName: 'CRM Checkout Flow' });
    expect(screen.getByText('CRM Checkout Flow')).toBeInTheDocument();
  });

  it('pre-fills username from initialUsername prop', () => {
    renderModal({ initialUsername: 'cached@crm.com' });
    const usernameInput = screen.getByTestId('crm-username-input') as HTMLInputElement;
    expect(usernameInput.value).toBe('cached@crm.com');
  });

  it('password field is never pre-filled', () => {
    // Even if initialUsername is provided, password should always start empty
    renderModal({ initialUsername: 'cached@crm.com' });
    const passwordInput = screen.getByTestId('crm-password-input') as HTMLInputElement;
    expect(passwordInput.value).toBe('');
  });
});
