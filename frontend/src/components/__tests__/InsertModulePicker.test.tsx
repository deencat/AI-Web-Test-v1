/**
 * InsertModulePicker.test.tsx — Sprint 10.11
 *
 * Tests cover:
 *  1. Picker renders a search input
 *  2. Modules list shown
 *  3. Search filters modules
 *  4. Selected module preview shows steps
 *  5. Parameters form shown for modules with params
 *  6. Insert button fires onInsert with @module: string (no params)
 *  7. Insert button fires onInsert with @module: string (with params)
 *  8. onClose called when Cancel clicked
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../../services/stepLibraryService', () => ({
  default: {
    list: vi.fn(),
  },
}));

import { InsertModulePicker } from '../../components/InsertModulePicker';
import stepLibraryService from '../../services/stepLibraryService';

const mockModules = [
  {
    id: 1,
    user_id: 1,
    name: 'login_three_hk',
    display_name: 'Three HK Login Flow',
    steps: ['Navigate to UAT', 'Click Login'],
    parameters: ['username'],
    tags: ['e2e'],
    created_at: '2026-05-01T00:00:00Z',
    updated_at: '2026-05-01T00:00:00Z',
  },
  {
    id: 2,
    user_id: 1,
    name: 'checkout_flow',
    display_name: 'Checkout Flow',
    steps: ['Click Checkout'],
    parameters: [],
    tags: [],
    created_at: '2026-05-02T00:00:00Z',
    updated_at: '2026-05-02T00:00:00Z',
  },
];

describe('InsertModulePicker', () => {
  const onInsert = vi.fn();
  const onClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stepLibraryService.list).mockResolvedValue(mockModules);
  });

  it('1. renders a search input', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => expect(screen.getByPlaceholderText(/search modules/i)).toBeInTheDocument());
  });

  it('2. modules list shown after load', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => {
      expect(screen.getByText('Three HK Login Flow')).toBeInTheDocument();
      expect(screen.getByText('Checkout Flow')).toBeInTheDocument();
    });
  });

  it('3. search filters visible modules', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    fireEvent.change(screen.getByPlaceholderText(/search modules/i), { target: { value: 'checkout' } });

    expect(screen.queryByText('Three HK Login Flow')).not.toBeInTheDocument();
    expect(screen.getByText('Checkout Flow')).toBeInTheDocument();
  });

  it('4. clicking a module shows its step preview', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    fireEvent.click(screen.getByText('Three HK Login Flow'));

    await waitFor(() => {
      expect(screen.getByText('Navigate to UAT')).toBeInTheDocument();
    });
  });

  it('5. parameters form shown for module with params', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    fireEvent.click(screen.getByText('Three HK Login Flow'));

    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });
  });

  it('6. Insert fires onInsert with @module: string (no params)', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => screen.getByText('Checkout Flow'));

    fireEvent.click(screen.getByText('Checkout Flow'));
    await waitFor(() => screen.getByRole('button', { name: /insert/i }));

    fireEvent.click(screen.getByRole('button', { name: /insert/i }));

    expect(onInsert).toHaveBeenCalledWith('@module:checkout_flow()');
  });

  it('7. Insert fires onInsert with @module: string with params', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => screen.getByText('Three HK Login Flow'));

    fireEvent.click(screen.getByText('Three HK Login Flow'));
    await waitFor(() => screen.getByLabelText(/username/i));

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'admin@test.com' } });
    fireEvent.click(screen.getByRole('button', { name: /insert/i }));

    expect(onInsert).toHaveBeenCalledWith('@module:login_three_hk(username=admin@test.com)');
  });

  it('8. onClose called when Cancel clicked', async () => {
    render(<InsertModulePicker onInsert={onInsert} onClose={onClose} />);
    await waitFor(() => screen.getByRole('button', { name: /cancel/i }));

    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
