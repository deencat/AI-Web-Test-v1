import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InlineTitleEditor } from '../InlineTitleEditor';

const { mockUpdateTest } = vi.hoisted(() => ({
  mockUpdateTest: vi.fn(),
}));

vi.mock('../../../services/testsService', () => ({
  default: {
    updateTest: mockUpdateTest,
  },
}));

describe('InlineTitleEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('saves changed title on Enter', async () => {
    const user = userEvent.setup();
    const onTitleChange = vi.fn();
    mockUpdateTest.mockResolvedValue({});

    render(
      <InlineTitleEditor testId={7} title="Original title" onTitleChange={onTitleChange} />
    );

    await user.click(screen.getByTestId('inline-title-button-7'));
    const input = screen.getByTestId('inline-title-input-7');
    await user.clear(input);
    await user.type(input, 'Renamed title{Enter}');

    expect(mockUpdateTest).toHaveBeenCalledWith('7', { title: 'Renamed title' });
    expect(onTitleChange).toHaveBeenCalledWith('Renamed title');
  });

  it('cancels edits on Escape without API call', async () => {
    const user = userEvent.setup();

    render(<InlineTitleEditor testId={8} title="Original" onTitleChange={vi.fn()} />);

    await user.click(screen.getByTestId('inline-title-button-8'));
    const input = screen.getByTestId('inline-title-input-8');
    await user.clear(input);
    await user.type(input, 'Discard me{Escape}');

    expect(mockUpdateTest).not.toHaveBeenCalled();
    expect(screen.getByText('Original')).toBeInTheDocument();
  });

  it('blocks empty title and shows validation message', async () => {
    const user = userEvent.setup();

    render(<InlineTitleEditor testId={9} title="Keep me" onTitleChange={vi.fn()} />);

    await user.click(screen.getByTestId('inline-title-button-9'));
    const input = screen.getByTestId('inline-title-input-9');
    await user.clear(input);
    await user.type(input, '{Enter}');

    expect(mockUpdateTest).not.toHaveBeenCalled();
    expect(screen.getByText('Title is required')).toBeInTheDocument();
  });

  it('reverts on failed save and shows error message', async () => {
    const user = userEvent.setup();
    mockUpdateTest.mockRejectedValue(new Error('Network down'));

    render(<InlineTitleEditor testId={10} title="Stable title" onTitleChange={vi.fn()} />);

    await user.click(screen.getByTestId('inline-title-button-10'));
    const input = screen.getByTestId('inline-title-input-10');
    await user.clear(input);
    await user.type(input, 'Will fail{Enter}');

    expect(mockUpdateTest).toHaveBeenCalledWith('10', { title: 'Will fail' });
    expect(await screen.findByText('Stable title')).toBeInTheDocument();
    expect(await screen.findByText('Network down')).toBeInTheDocument();
  });
});
