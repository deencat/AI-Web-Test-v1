/**
 * AddWaitControl.test.tsx — Feature 4 timed wait UI
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AddWaitControl } from '../AddWaitControl';

describe('AddWaitControl', () => {
  it('renders Add Wait button with data-testid', () => {
    const onInsert = vi.fn();
    render(<AddWaitControl onInsert={onInsert} />);
    expect(screen.getByTestId('add-wait-button')).toBeInTheDocument();
    expect(screen.getByText('+ Add Wait')).toBeInTheDocument();
  });

  it('inserts wait: 10s when preset 10s is chosen', () => {
    const onInsert = vi.fn();
    render(<AddWaitControl onInsert={onInsert} />);
    fireEvent.click(screen.getByTestId('add-wait-button'));
    fireEvent.click(screen.getByTestId('add-wait-preset-10'));
    expect(onInsert).toHaveBeenCalledWith('wait: 10s');
  });

  it('inserts wait: 5s for 5s preset', () => {
    const onInsert = vi.fn();
    render(<AddWaitControl onInsert={onInsert} />);
    fireEvent.click(screen.getByTestId('add-wait-button'));
    fireEvent.click(screen.getByTestId('add-wait-preset-5'));
    expect(onInsert).toHaveBeenCalledWith('wait: 5s');
  });

  it('clamps custom duration above 120 to 120', () => {
    const onInsert = vi.fn();
    render(<AddWaitControl onInsert={onInsert} />);
    fireEvent.click(screen.getByTestId('add-wait-button'));
    fireEvent.change(screen.getByTestId('add-wait-custom-input'), {
      target: { value: '200' },
    });
    fireEvent.click(screen.getByTestId('add-wait-custom-confirm'));
    expect(onInsert).toHaveBeenCalledWith('wait: 120s');
    expect(screen.getByTestId('add-wait-error')).toHaveTextContent(/max 120/i);
  });

  it('does not insert when custom duration is empty', () => {
    const onInsert = vi.fn();
    render(<AddWaitControl onInsert={onInsert} />);
    fireEvent.click(screen.getByTestId('add-wait-button'));
    expect(screen.getByTestId('add-wait-custom-confirm')).toBeDisabled();
    expect(onInsert).not.toHaveBeenCalled();
  });
});
