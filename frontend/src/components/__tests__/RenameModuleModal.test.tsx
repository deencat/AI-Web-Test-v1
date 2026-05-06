/**
 * RenameModuleModal.test.tsx — Sprint 10.11 task 10.11-B14
 *
 * TDD RED → GREEN cycle for the rename confirmation modal.
 *
 * Tests cover:
 *  1.  Modal renders with module's current name pre-filled
 *  2.  New name input is editable
 *  3.  "Preview" button is present and clickable
 *  4.  Preview call triggers renamePreview() service method
 *  5.  Affected test cases list shown after preview
 *  6.  "No affected tests" message when count === 0
 *  7.  Confirm button is enabled after preview completes
 *  8.  Confirm button calls service.update() with new name
 *  9.  Cancel button closes modal without saving
 * 10.  Error shown when renamePreview() call fails
 * 11.  Error shown when update() call fails
 * 12.  Toast shows updated test case count on success
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// ---------------------------------------------------------------------------
// Mock service
// ---------------------------------------------------------------------------
vi.mock('../../services/stepLibraryService', () => ({
  default: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    renamePreview: vi.fn(),
  },
}));

import stepLibraryService from '../../services/stepLibraryService';
import { RenameModuleModal } from '../../components/RenameModuleModal';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const mockModule = {
  id: 1,
  user_id: 1,
  name: 'login_three_hk',
  display_name: 'Three HK Login Flow',
  description: null,
  steps: ['Navigate to UAT', 'Click Login'],
  parameters: [],
  tags: [],
  created_at: '2026-05-01T00:00:00Z',
  updated_at: '2026-05-01T00:00:00Z',
  usage_count: 2,
};

function renderModal(overrides: Record<string, unknown> = {}) {
  const onClose = vi.fn();
  const onRenamed = vi.fn();
  return {
    onClose,
    onRenamed,
    ...render(
      <MemoryRouter>
        <RenameModuleModal
          module={mockModule}
          onClose={onClose}
          onRenamed={onRenamed}
          {...overrides}
        />
      </MemoryRouter>
    ),
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('RenameModuleModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Modal renders with current name pre-filled
  it('renders with current module name pre-filled in input', () => {
    renderModal();
    const input = screen.getByRole('textbox', { name: /new name/i });
    expect((input as HTMLInputElement).value).toBe('login_three_hk');
  });

  // 2. New name input is editable
  it('allows the user to type a new name', () => {
    renderModal();
    const input = screen.getByRole('textbox', { name: /new name/i });
    fireEvent.change(input, { target: { value: 'login_flow' } });
    expect((input as HTMLInputElement).value).toBe('login_flow');
  });

  // 3. Preview button is present
  it('renders a Preview button', () => {
    renderModal();
    expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
  });

  // 4. Preview button calls renamePreview()
  it('calls renamePreview() when Preview is clicked', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [],
      count: 0,
    });

    renderModal();
    const input = screen.getByRole('textbox', { name: /new name/i });
    fireEvent.change(input, { target: { value: 'login_flow' } });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));

    await waitFor(() => {
      expect(stepLibraryService.renamePreview).toHaveBeenCalledWith(1, 'login_flow');
    });
  });

  // 5. Affected test cases shown after preview
  it('lists affected test cases after preview', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [
        { id: 5, name: 'Login Test' },
        { id: 9, name: 'Checkout Test' },
      ],
      count: 2,
    });

    renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));

    await waitFor(() => {
      expect(screen.getByText('Login Test')).toBeInTheDocument();
      expect(screen.getByText('Checkout Test')).toBeInTheDocument();
    });
  });

  // 6. "No affected tests" message shown when count === 0
  it('shows no-affected message when count is 0', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [],
      count: 0,
    });

    renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));

    await waitFor(() => {
      expect(screen.getByText(/no test cases/i)).toBeInTheDocument();
    });
  });

  // 7. Confirm button enabled after preview
  it('enables Confirm button after preview completes', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [],
      count: 0,
    });

    renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));

    await waitFor(() => {
      const confirmBtn = screen.getByRole('button', { name: /confirm rename/i });
      expect(confirmBtn).not.toBeDisabled();
    });
  });

  // 8. Confirm calls service.update() with new name
  it('calls update() with new name on Confirm', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [],
      count: 0,
    });
    vi.mocked(stepLibraryService.update).mockResolvedValue({
      ...mockModule,
      name: 'login_flow',
    });

    const { onRenamed } = renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));
    await waitFor(() => screen.getByRole('button', { name: /confirm rename/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm rename/i }));

    await waitFor(() => {
      expect(stepLibraryService.update).toHaveBeenCalledWith(1, { name: 'login_flow' });
      expect(onRenamed).toHaveBeenCalled();
    });
  });

  // 9. Cancel closes without saving
  it('calls onClose when Cancel is clicked', () => {
    const { onClose } = renderModal();
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
    expect(stepLibraryService.update).not.toHaveBeenCalled();
  });

  // 10. Error shown when renamePreview() fails
  it('shows error when renamePreview() rejects', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockRejectedValue(new Error('Network error'));

    renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch preview/i)).toBeInTheDocument();
    });
  });

  // 11. Error shown when update() fails
  it('shows error when update() rejects', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [],
      count: 0,
    });
    vi.mocked(stepLibraryService.update).mockRejectedValue(new Error('Save failed'));

    renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));
    await waitFor(() => screen.getByRole('button', { name: /confirm rename/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm rename/i }));

    await waitFor(() => {
      expect(screen.getByText(/rename failed/i)).toBeInTheDocument();
    });
  });

  // 12. Toast shows updated count on success
  it('passes updated test case count to onRenamed', async () => {
    vi.mocked(stepLibraryService.renamePreview).mockResolvedValue({
      affected_test_cases: [
        { id: 5, name: 'Login Test' },
        { id: 9, name: 'Checkout Test' },
      ],
      count: 2,
    });
    vi.mocked(stepLibraryService.update).mockResolvedValue({
      ...mockModule,
      name: 'login_flow',
    });

    const { onRenamed } = renderModal();
    fireEvent.change(screen.getByRole('textbox', { name: /new name/i }), {
      target: { value: 'login_flow' },
    });
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));
    await waitFor(() => screen.getByRole('button', { name: /confirm rename/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm rename/i }));

    await waitFor(() => {
      expect(onRenamed).toHaveBeenCalledWith(expect.objectContaining({ name: 'login_flow' }), 2);
    });
  });
});
