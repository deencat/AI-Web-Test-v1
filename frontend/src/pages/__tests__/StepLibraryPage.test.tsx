/**
 * StepLibraryPage.test.tsx — Sprint 10.11
 *
 * TDD RED → GREEN cycle.
 *
 * Tests cover:
 *  1. Page renders "Step Library" heading
 *  2. "+ New Module" button present
 *  3. Module list items shown after load
 *  4. Search filters visible modules
 *  5. New module form shown on Create click
 *  6. Create form submits with correct data
 *  7. Delete action calls service.delete
 *  8. Edit action launches edit form pre-filled
 *  9. Empty state shown when no modules exist
 * 10. Error state shown on load failure
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
  },
}));

import stepLibraryService from '../../services/stepLibraryService';
import { StepLibraryPage } from '../../pages/StepLibraryPage';

const mockModules = [
  {
    id: 1,
    user_id: 1,
    name: 'login_three_hk',
    display_name: 'Three HK Login Flow',
    description: 'Logs into the Three HK UAT environment',
    steps: ['Navigate to https://wwwuat.three.com.hk', 'Click Login'],
    parameters: ['username'],
    tags: ['e2e'],
    created_at: '2026-05-01T00:00:00Z',
    updated_at: '2026-05-01T00:00:00Z',
    usage_count: 3,
  },
  {
    id: 2,
    user_id: 1,
    name: 'checkout_flow',
    display_name: 'Checkout Flow',
    description: null,
    steps: ['Click Checkout'],
    parameters: [],
    tags: ['checkout'],
    created_at: '2026-05-02T00:00:00Z',
    updated_at: '2026-05-02T00:00:00Z',
    usage_count: 0,
  },
];

// ---------------------------------------------------------------------------
// Helper: render with router
// ---------------------------------------------------------------------------
function renderPage() {
  return render(
    <MemoryRouter>
      <StepLibraryPage />
    </MemoryRouter>
  );
}

describe('StepLibraryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stepLibraryService.list).mockResolvedValue(mockModules);
    vi.mocked(stepLibraryService.create).mockResolvedValue({ ...mockModules[0], id: 3, name: 'new_module', display_name: 'New Module', steps: ['Step one'] });
    vi.mocked(stepLibraryService.update).mockResolvedValue(mockModules[0]);
    vi.mocked(stepLibraryService.delete).mockResolvedValue(undefined);
  });

  it('1. renders "Step Library" heading', async () => {
    renderPage();
    expect(screen.getByRole('heading', { name: /step library/i })).toBeInTheDocument();
  });

  it('2. "+ New Module" button is present', async () => {
    renderPage();
    expect(screen.getByRole('button', { name: /new module/i })).toBeInTheDocument();
  });

  it('3. module list items shown after load', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Three HK Login Flow')).toBeInTheDocument();
      expect(screen.getByText('Checkout Flow')).toBeInTheDocument();
    });
  });

  it('4. search filters visible modules', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    const searchInput = screen.getByPlaceholderText(/search modules/i);
    fireEvent.change(searchInput, { target: { value: 'checkout' } });

    expect(screen.queryByText('Three HK Login Flow')).not.toBeInTheDocument();
    expect(screen.getByText('Checkout Flow')).toBeInTheDocument();
  });

  it('5. new module form shown on Create click', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /new module/i }));
    await waitFor(() => {
      expect(screen.getByLabelText(/module name/i)).toBeInTheDocument();
    });
  });

  it('6. create form submits with correct data', async () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /new module/i }));
    await waitFor(() => screen.getByLabelText(/module name \(slug\)/i));

    fireEvent.change(screen.getByLabelText(/module name \(slug\)/i), { target: { value: 'new_module' } });
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'New Module' } });
    fireEvent.change(screen.getByLabelText(/steps/i), { target: { value: 'Step one' } });

    fireEvent.click(screen.getByRole('button', { name: /save module/i }));

    await waitFor(() => {
      expect(stepLibraryService.create).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'new_module', display_name: 'New Module', steps: ['Step one'] })
      );
    });
  });

  it('7. delete action calls service.delete', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPage();
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    // Find the first delete button
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    // Confirm in dialog (if present) or direct call
    await waitFor(() => {
      expect(stepLibraryService.delete).toHaveBeenCalledWith(1);
    });
  });

  it('8. edit action launches form pre-filled with module data', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      const nameInput = screen.getByLabelText(/module name \(slug\)/i) as HTMLInputElement;
      expect(nameInput.value).toBe('login_three_hk');
    });
  });

  it('9. empty state shown when no modules exist', async () => {
    vi.mocked(stepLibraryService.list).mockResolvedValue([]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/no step library modules/i)).toBeInTheDocument();
    });
  });

  it('10. error state shown on load failure', async () => {
    vi.mocked(stepLibraryService.list).mockRejectedValue(new Error('Network error'));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });
});
