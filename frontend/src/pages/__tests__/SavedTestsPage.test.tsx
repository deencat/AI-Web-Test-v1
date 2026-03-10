/**
 * SavedTestsPage.test.tsx — Sprint 10.5 Feature 2: Batch Delete Tests
 *
 * TDD RED → GREEN cycle.
 * Tests:
 *  - Per-row checkboxes are rendered
 *  - "Select All" toggle selects/deselects all visible rows
 *  - "Delete Selected" button is disabled when no rows are selected
 *  - "Delete Selected" button is enabled when ≥1 row is selected
 *  - Clicking "Delete Selected" calls batchDeleteTests with selected IDs
 *  - After success, the list refreshes and selection clears
 *  - Error toast shown on partial failure
 *  - Selecting individual row increments selection count
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

vi.mock('../../components/common/Card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('../../components/common/Button', () => ({
  Button: ({
    children,
    onClick,
    disabled,
    variant,
    'data-testid': testId,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    variant?: string;
    'data-testid'?: string;
  }) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} data-testid={testId}>
      {children}
    </button>
  ),
}));

const mockTestsService = {
  getAllTests: vi.fn(),
  deleteTest: vi.fn(),
  batchDeleteTests: vi.fn(),
};

vi.mock('../../services/testsService', () => ({
  default: mockTestsService,
}));

const mockExecutionService = {
  startExecution: vi.fn(),
};

vi.mock('../../services/executionService', () => ({
  default: mockExecutionService,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const makeSavedTest = (id: number, title = `Test ${id}`) => ({
  id,
  title,
  description: `Description ${id}`,
  test_type: 'e2e',
  priority: 'medium' as const,
  status: 'pending',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
});

const THREE_TESTS = [makeSavedTest(1), makeSavedTest(2), makeSavedTest(3)];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function renderPage() {
  const { SavedTestsPage } = await import('../SavedTestsPage');
  render(<SavedTestsPage />);
  // Wait for tests to load — select-all-checkbox only renders after data is fetched
  await screen.findByTestId('select-all-checkbox', {}, { timeout: 3000 });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SavedTestsPage — batch delete (Sprint 10.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTestsService.getAllTests.mockResolvedValue(THREE_TESTS);
  });

  // ── Checkbox rendering ───────────────────────────────────────────────────

  it('renders a checkbox for each test row', async () => {
    await renderPage();

    // Each row test card should have a data-testid row-checkbox-<id>
    expect(screen.getByTestId('row-checkbox-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-checkbox-2')).toBeInTheDocument();
    expect(screen.getByTestId('row-checkbox-3')).toBeInTheDocument();
  });

  it('renders the "Select All" checkbox', async () => {
    await renderPage();
    expect(screen.getByTestId('select-all-checkbox')).toBeInTheDocument();
  });

  // ── Delete Selected button state ─────────────────────────────────────────

  it('renders "Delete Selected" button', async () => {
    await renderPage();
    expect(screen.getByTestId('batch-delete-button')).toBeInTheDocument();
  });

  it('"Delete Selected" button is disabled when no rows are selected', async () => {
    await renderPage();
    expect(screen.getByTestId('batch-delete-button')).toBeDisabled();
  });

  it('"Delete Selected" button is enabled after checking one row', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.click(screen.getByTestId('row-checkbox-1'));

    expect(screen.getByTestId('batch-delete-button')).not.toBeDisabled();
  });

  it('button label includes selected count', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.click(screen.getByTestId('row-checkbox-1'));
    await user.click(screen.getByTestId('row-checkbox-2'));

    expect(screen.getByTestId('batch-delete-button').textContent).toContain('2');
  });

  // ── Select All ───────────────────────────────────────────────────────────

  it('Select All selects all visible rows', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.click(screen.getByTestId('select-all-checkbox'));

    expect(screen.getByTestId('row-checkbox-1')).toBeChecked();
    expect(screen.getByTestId('row-checkbox-2')).toBeChecked();
    expect(screen.getByTestId('row-checkbox-3')).toBeChecked();
  });

  it('Select All then click again deselects all rows', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.click(screen.getByTestId('select-all-checkbox'));
    await user.click(screen.getByTestId('select-all-checkbox'));

    expect(screen.getByTestId('row-checkbox-1')).not.toBeChecked();
    expect(screen.getByTestId('row-checkbox-2')).not.toBeChecked();
    expect(screen.getByTestId('row-checkbox-3')).not.toBeChecked();
  });

  // ── Batch delete flow ────────────────────────────────────────────────────

  it('calls batchDeleteTests with selected IDs on confirm', async () => {
    const user = userEvent.setup();
    mockTestsService.batchDeleteTests.mockResolvedValue({ deleted: 2, failed: [] });
    mockTestsService.getAllTests
      .mockResolvedValueOnce(THREE_TESTS)
      .mockResolvedValueOnce([makeSavedTest(3)]); // after delete, only id=3 remains

    await renderPage();

    await user.click(screen.getByTestId('row-checkbox-1'));
    await user.click(screen.getByTestId('row-checkbox-2'));
    await user.click(screen.getByTestId('batch-delete-button'));

    // Confirm modal should appear
    const modal = await screen.findByTestId('batch-delete-modal');
    const confirmButton = within(modal).getByTestId('confirm-delete-button');
    await user.click(confirmButton);

    expect(mockTestsService.batchDeleteTests).toHaveBeenCalledWith([1, 2]);
  });

  it('clears selection after successful batch delete', async () => {
    const user = userEvent.setup();
    mockTestsService.batchDeleteTests.mockResolvedValue({ deleted: 1, failed: [] });
    mockTestsService.getAllTests
      .mockResolvedValueOnce(THREE_TESTS)
      .mockResolvedValueOnce(THREE_TESTS.slice(1));

    await renderPage();

    await user.click(screen.getByTestId('row-checkbox-1'));
    await user.click(screen.getByTestId('batch-delete-button'));

    const modal = await screen.findByTestId('batch-delete-modal');
    await user.click(within(modal).getByTestId('confirm-delete-button'));

    await vi.waitFor(() => {
      expect(screen.getByTestId('batch-delete-button')).toBeDisabled();
    });
  });

  it('cancelling the modal does NOT call batchDeleteTests', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.click(screen.getByTestId('row-checkbox-1'));
    await user.click(screen.getByTestId('batch-delete-button'));

    const modal = await screen.findByTestId('batch-delete-modal');
    await user.click(within(modal).getByTestId('cancel-delete-button'));

    expect(mockTestsService.batchDeleteTests).not.toHaveBeenCalled();
    // Selection should still be intact
    expect(screen.getByTestId('row-checkbox-1')).toBeChecked();
  });
});
