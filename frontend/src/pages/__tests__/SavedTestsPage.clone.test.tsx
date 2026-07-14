/**
 * SavedTestsPage.clone.test.tsx — Clone Test Case feature
 *
 * Tests Clone button rendering, service invocation, and loading state.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

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
  cloneTest: vi.fn(),
};

vi.mock('../../services/testsService', () => ({
  default: mockTestsService,
}));

vi.mock('../../services/executionService', () => ({
  default: { startExecution: vi.fn() },
}));

vi.mock('../../services/testCategoriesService', () => ({
  default: {
    getAll: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../../services/schedulesService', () => ({
  default: {
    listAll: vi.fn().mockResolvedValue([]),
    listForTest: vi.fn(),
    create: vi.fn(),
    toggle: vi.fn(),
    remove: vi.fn(),
  },
}));

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

async function renderPage() {
  const { SavedTestsPage } = await import('../SavedTestsPage');
  render(<SavedTestsPage />);
  await screen.findByTestId('clone-test-button-1', {}, { timeout: 3000 });
}

describe('SavedTestsPage — clone test case', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    mockTestsService.getAllTests.mockResolvedValue([
      makeSavedTest(1, 'Login Flow'),
      makeSavedTest(2, 'Checkout'),
    ]);
    mockTestsService.cloneTest.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () =>
              resolve({
                id: 99,
                title: 'Login Flow (Copy)',
                description: 'Description 1',
                status: 'pending',
              }),
            50
          );
        })
    );
  });

  it('renders Clone button on each test row', async () => {
    await renderPage();
    expect(screen.getByTestId('clone-test-button-1')).toBeInTheDocument();
    expect(screen.getByTestId('clone-test-button-2')).toBeInTheDocument();
  });

  it('calls cloneTest service when Clone is clicked', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.click(screen.getByTestId('clone-test-button-1'));

    await waitFor(() => {
      expect(mockTestsService.cloneTest).toHaveBeenCalledWith(1);
      expect(mockNavigate).toHaveBeenCalledWith('/tests/saved?edit=99');
    });
  });

  it('disables Clone button while cloning is in progress', async () => {
    const user = userEvent.setup();
    let resolveClone: (value: unknown) => void = () => {};
    mockTestsService.cloneTest.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveClone = resolve;
        })
    );

    await renderPage();
    const cloneButton = screen.getByTestId('clone-test-button-1');
    await user.click(cloneButton);

    await waitFor(() => {
      expect(cloneButton).toBeDisabled();
    });

    resolveClone({ id: 99, title: 'Login Flow (Copy)' });

    await waitFor(() => {
      expect(cloneButton).not.toBeDisabled();
    });
  });

  it('uses blue secondary styling on Clone button (not destructive)', async () => {
    await renderPage();
    const cloneButton = screen.getByTestId('clone-test-button-1');
    expect(cloneButton.className).toMatch(/text-blue-600/);
    expect(cloneButton.className).not.toMatch(/text-red-600/);
    expect(cloneButton).toHaveAttribute('aria-label', 'Clone Test Case');
  });

  it('refreshes list after successful clone', async () => {
    const user = userEvent.setup();
    await renderPage();

    const initialCalls = mockTestsService.getAllTests.mock.calls.length;
    await user.click(screen.getByTestId('clone-test-button-1'));

    await waitFor(() => {
      expect(mockTestsService.getAllTests.mock.calls.length).toBeGreaterThan(initialCalls);
    });
  });
});
