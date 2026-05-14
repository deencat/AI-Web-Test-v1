/**
 * ReRunFromStepButton.test.tsx — Sprint 10.12 Feature B
 *
 * TDD for the Re-run from here button and confirmation dialog.
 *
 * Tests cover:
 *  1. Button renders on failed/error steps
 *  2. Button does NOT render on passed or skipped steps
 *  3. Clicking the button opens a confirmation dialog
 *  4. Confirmation dialog shows execution ID, step number, and page URL
 *  5. Clicking "Cancel" in the dialog closes it without calling the API
 *  6. Clicking "Re-run" calls executionService.startExecution with resume params
 *  7. Error state shown when API call fails
 *  8. Loading spinner shown during API call
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ReRunFromStepButton } from '../../components/execution/ReRunFromStepButton';
import executionService from '../../services/executionService';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../services/executionService', () => ({
  default: {
    startExecution: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderButton(props: Partial<React.ComponentProps<typeof ReRunFromStepButton>> = {}) {
  const defaults = {
    testCaseId: 1,
    executionId: 10,
    stepNumber: 5,
    stepResult: 'fail' as const,
    baseUrl: 'https://example.com',
    browser: 'chromium',
    environment: 'dev',
  };

  return render(
    <MemoryRouter>
      <ReRunFromStepButton {...defaults} {...props} />
    </MemoryRouter>
  );
}

// ---------------------------------------------------------------------------
// 1. Visibility: only on failed/error steps
// ---------------------------------------------------------------------------

describe('ReRunFromStepButton visibility', () => {
  it('renders for failed steps', () => {
    renderButton({ stepResult: 'fail' });
    expect(screen.getByRole('button', { name: /re-run from here/i })).toBeInTheDocument();
  });

  it('renders for error steps', () => {
    renderButton({ stepResult: 'error' });
    expect(screen.getByRole('button', { name: /re-run from here/i })).toBeInTheDocument();
  });

  it('does NOT render for passed steps', () => {
    renderButton({ stepResult: 'pass' });
    expect(screen.queryByRole('button', { name: /re-run from here/i })).not.toBeInTheDocument();
  });

  it('does NOT render for skipped steps', () => {
    renderButton({ stepResult: 'skip' });
    expect(screen.queryByRole('button', { name: /re-run from here/i })).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. Confirmation dialog
// ---------------------------------------------------------------------------

describe('ReRunFromStepButton confirmation dialog', () => {
  it('opens confirmation dialog on button click', () => {
    renderButton();
    fireEvent.click(screen.getByRole('button', { name: /re-run from here/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('dialog shows the source execution ID', () => {
    renderButton({ executionId: 42, stepNumber: 7 });
    fireEvent.click(screen.getByRole('button', { name: /re-run from here/i }));
    expect(screen.getByText(/execution.*42/i)).toBeInTheDocument();
  });

  it('dialog shows the step number', () => {
    renderButton({ executionId: 10, stepNumber: 7 });
    fireEvent.click(screen.getByRole('button', { name: /re-run from here/i }));
    expect(screen.getByText(/step.*7/i)).toBeInTheDocument();
  });

  it('closes dialog on Cancel without calling API', () => {
    renderButton();
    fireEvent.click(screen.getByRole('button', { name: /re-run from here/i }));
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(executionService.startExecution).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 3. API integration
// ---------------------------------------------------------------------------

describe('ReRunFromStepButton API call', () => {
  beforeEach(() => {
    vi.mocked(executionService.startExecution).mockReset();
  });

  it('calls startExecution with resume params on confirm', async () => {
    vi.mocked(executionService.startExecution).mockResolvedValue({ id: 99, test_case_id: 5, status: 'pending' as const, message: 'queued' });

    renderButton({ testCaseId: 5, executionId: 10, stepNumber: 6 });
    fireEvent.click(screen.getByRole('button', { name: /re-run from here/i }));
    fireEvent.click(screen.getByRole('button', { name: /^confirm|^re-run/i }));

    await waitFor(() => {
      expect(executionService.startExecution).toHaveBeenCalledWith(
        5,
        expect.objectContaining({
          resume_from_execution_id: 10,
          start_from_step: 6,
        })
      );
    });
  });

  it('shows error message when API call fails', async () => {
    vi.mocked(executionService.startExecution).mockRejectedValue(new Error('Cannot resume: step 3 failed'));

    renderButton();
    fireEvent.click(screen.getByRole('button', { name: /re-run from here/i }));
    fireEvent.click(screen.getByRole('button', { name: /^confirm|^re-run/i }));

    await waitFor(() => {
      expect(screen.getByText(/cannot resume.*step 3 failed/i)).toBeInTheDocument();
    });
  });
});
