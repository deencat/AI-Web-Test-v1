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
const mockSetSearchParams = vi.fn();
let mockSearchParams = new URLSearchParams();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useSearchParams: () => [mockSearchParams, mockSetSearchParams],
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
  getTestById: vi.fn(),
  updateTest: vi.fn(),
  deleteTest: vi.fn(),
  batchDeleteTests: vi.fn(),
  batchAssignCategory: vi.fn(),
  batchAssignReadiness: vi.fn(),
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

const mockTestCategoriesService = {
  getAll: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
};

vi.mock('../../services/testCategoriesService', () => ({
  default: mockTestCategoriesService,
}));

const mockSchedulesService = {
  listAll: vi.fn(),
  listForTest: vi.fn(),
  create: vi.fn(),
  toggle: vi.fn(),
  remove: vi.fn(),
};

vi.mock('../../services/schedulesService', () => ({
  default: mockSchedulesService,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const makeSavedTest = (
  id: number,
  title = `Test ${id}`,
  extras: { readiness_status?: string; test_category_id?: number | null } = {}
) => ({
  id,
  title,
  description: `Description ${id}`,
  test_type: 'e2e',
  priority: 'medium' as const,
  status: 'pending',
  readiness_status: extras.readiness_status ?? 'draft',
  test_category_id: extras.test_category_id ?? null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
});

const THREE_TESTS = [makeSavedTest(1), makeSavedTest(2), makeSavedTest(3)];
const TEST_CATEGORIES = [
  { id: 10, name: 'Billing', description: null, color: '#3B82F6', test_count: 2 },
  { id: 20, name: 'Checkout', description: null, color: '#10B981', test_count: 1 },
];

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
    mockSearchParams = new URLSearchParams();
    mockTestsService.getAllTests.mockResolvedValue(THREE_TESTS);
    mockTestsService.getTestById.mockResolvedValue({
      id: 1,
      title: 'Test 1',
      description: 'Description 1',
      steps: ['step 1'],
      expected_result: 'done',
      priority: 'medium',
      requires_runtime_credentials: false,
      test_category_id: null,
    });
    mockTestCategoriesService.getAll.mockResolvedValue(TEST_CATEGORIES);
    mockSchedulesService.listAll.mockResolvedValue([]);
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

  it('shows category options in batch set category control', async () => {
    await renderPage();
    const setCategory = screen.getByTestId('set-category-button');
    expect(within(setCategory).getByText('Billing')).toBeInTheDocument();
    expect(within(setCategory).getByText('Checkout')).toBeInTheDocument();
  });

  it('calls batchAssignCategory with selected ids and category id', async () => {
    const user = userEvent.setup();
    mockTestsService.batchAssignCategory.mockResolvedValue({ updated: 2, failed: [] });

    await renderPage();
    await user.click(screen.getByTestId('row-checkbox-1'));
    await user.click(screen.getByTestId('row-checkbox-2'));
    await user.selectOptions(screen.getByTestId('set-category-button'), '10');

    expect(mockTestsService.batchAssignCategory).toHaveBeenCalledWith([1, 2], 10);
  });

  it('opens saved edit drawer when ?edit is present', async () => {
    mockSearchParams = new URLSearchParams('edit=1');
    const { SavedTestsPage } = await import('../SavedTestsPage');
    render(<SavedTestsPage />);

    expect(await screen.findByText('Edit Test Case')).toBeInTheDocument();
    expect(mockTestsService.getTestById).toHaveBeenCalledWith('1');
  });

  it('clears edit query param when edit target load fails', async () => {
    mockSearchParams = new URLSearchParams('edit=9999');
    mockTestsService.getTestById.mockRejectedValue(new Error('not found'));
    const { SavedTestsPage } = await import('../SavedTestsPage');
    render(<SavedTestsPage />);

    expect(await screen.findByText('Unable to load test for editing.')).toBeInTheDocument();
    expect(mockSetSearchParams).toHaveBeenCalledWith(expect.any(URLSearchParams), { replace: true });
  });
});

describe('SavedTestsPage — readiness status (Feature 4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    mockTestsService.getAllTests.mockResolvedValue([
      makeSavedTest(1, 'Draft One', { readiness_status: 'draft', test_category_id: 10 }),
      makeSavedTest(2, 'Ready Two', { readiness_status: 'ready_to_test', test_category_id: 10 }),
      makeSavedTest(3, 'Blocked Three', { readiness_status: 'blocked', test_category_id: 20 }),
    ]);
    mockTestsService.getTestById.mockResolvedValue({
      id: 1,
      title: 'Draft One',
      description: 'Description 1',
      steps: ['step 1'],
      expected_result: 'done',
      priority: 'medium',
      requires_runtime_credentials: false,
      test_category_id: 10,
      readiness_status: 'draft',
    });
    mockTestsService.updateTest.mockResolvedValue({});
    mockTestsService.batchAssignReadiness.mockResolvedValue({ updated: 1, failed: [] });
    mockTestCategoriesService.getAll.mockResolvedValue(TEST_CATEGORIES);
    mockSchedulesService.listAll.mockResolvedValue([]);
  });

  it('filters to Ready to Test only', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.selectOptions(screen.getByTestId('saved-tests-readiness-filter'), 'ready_to_test');

    expect(screen.getByText('Ready Two')).toBeInTheDocument();
    expect(screen.queryByText('Draft One')).not.toBeInTheDocument();
    expect(screen.queryByText('Blocked Three')).not.toBeInTheDocument();
  });

  it('ANDs readiness filter with category filter', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.selectOptions(screen.getByTestId('saved-tests-readiness-filter'), 'draft');
    await user.selectOptions(screen.getByTestId('saved-tests-category-filter'), '10');

    expect(screen.getByText('Draft One')).toBeInTheDocument();
    expect(screen.queryByText('Ready Two')).not.toBeInTheDocument();
    expect(screen.queryByText('Blocked Three')).not.toBeInTheDocument();
  });

  it('row readiness change calls updateTest', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.selectOptions(screen.getByTestId('row-readiness-select-1'), 'ready_to_test');

    expect(mockTestsService.updateTest).toHaveBeenCalledWith('1', {
      readiness_status: 'ready_to_test',
    });
  });

  it('failed row readiness update reverts prior value', async () => {
    const user = userEvent.setup();
    mockTestsService.updateTest.mockRejectedValueOnce(new Error('network fail'));
    await renderPage();

    const select = screen.getByTestId('row-readiness-select-1') as HTMLSelectElement;
    expect(select.value).toBe('draft');

    await user.selectOptions(select, 'blocked');

    await vi.waitFor(() => {
      expect(select.value).toBe('draft');
    });
    expect(screen.getByText('network fail')).toBeInTheDocument();
  });

  it('edit drawer save includes readiness_status', async () => {
    mockSearchParams = new URLSearchParams('edit=1');
    mockTestsService.updateTest.mockResolvedValue({});
    const user = userEvent.setup();
    const { SavedTestsPage } = await import('../SavedTestsPage');
    render(<SavedTestsPage />);

    expect(await screen.findByText('Edit Test Case')).toBeInTheDocument();
    await user.selectOptions(screen.getByTestId('saved-edit-readiness-select'), 'blocked');
    await user.click(screen.getByRole('button', { name: 'Save Changes' }));

    await vi.waitFor(() => {
      expect(mockTestsService.updateTest).toHaveBeenCalled();
    });
    const payload = mockTestsService.updateTest.mock.calls[0][1];
    expect(payload.readiness_status).toBe('blocked');
  });

  it('bulk set readiness calls batchAssignReadiness', async () => {
    const user = userEvent.setup();
    await renderPage();
    await user.click(screen.getByTestId('row-checkbox-1'));
    await user.selectOptions(screen.getByTestId('set-readiness-button'), 'ready_to_test');

    expect(mockTestsService.batchAssignReadiness).toHaveBeenCalledWith([1], 'ready_to_test');
  });
});
