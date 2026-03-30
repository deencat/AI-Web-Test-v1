/**
 * RunTestButton.test.tsx — Sprint 10.7
 *
 * TDD RED → GREEN cycle.
 *
 * Tests cover:
 *  (a) UAT URL: Run button rendered, UAT badge rendered, profile picker absent
 *  (b) Non-UAT URL: Run button rendered, badge absent, profile picker absent
 *  (c) isUatUrl returns correct values for UAT and non-UAT hostnames
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RunTestButton } from '../RunTestButton';
import { isUatUrl } from '../../utils/urlUtils';

// ---------------------------------------------------------------------------
// Mock executionService so tests never make real HTTP calls
// ---------------------------------------------------------------------------
vi.mock('../../services/executionService', () => ({
  default: {
    startExecution: vi.fn().mockResolvedValue({ id: 99, status: 'pending' }),
  },
}));

// ---------------------------------------------------------------------------
// (c) isUatUrl unit tests
// ---------------------------------------------------------------------------
describe('isUatUrl', () => {
  it('returns true for wwwuat.three.com.hk URLs', () => {
    expect(isUatUrl('https://wwwuat.three.com.hk/')).toBe(true);
    expect(isUatUrl('https://wwwuat.three.com.hk/some/path')).toBe(true);
    expect(isUatUrl('http://wwwuat.three.com.hk/')).toBe(true);
  });

  it('returns false for non-UAT URLs', () => {
    expect(isUatUrl('https://www.three.com.hk/')).toBe(false);
    expect(isUatUrl('https://www.example.com/')).toBe(false);
    expect(isUatUrl('https://staging.example.com/')).toBe(false);
    expect(isUatUrl('')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// RunTestButton rendering tests
// ---------------------------------------------------------------------------
describe('RunTestButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // (a) UAT URL: Run button + badge present, no profile picker
  it('shows Run button and UAT badge for a UAT URL', () => {
    render(
      <RunTestButton
        testCaseId={1}
        testUrl="https://wwwuat.three.com.hk/some/path"
      />
    );

    expect(screen.getByRole('button', { name: /run test/i })).toBeInTheDocument();
    expect(screen.getByText(/uat credentials auto-applied/i)).toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });

  // (b) Non-UAT URL: Run button only, no badge, no picker
  it('shows only Run button for a non-UAT URL — no badge, no picker', () => {
    render(
      <RunTestButton
        testCaseId={2}
        testUrl="https://www.example.com/"
      />
    );

    expect(screen.getByRole('button', { name: /run test/i })).toBeInTheDocument();
    expect(screen.queryByText(/uat credentials auto-applied/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });

  // also verify no picker when testUrl is omitted entirely
  it('shows no profile picker when testUrl is omitted', () => {
    render(<RunTestButton testCaseId={3} />);

    expect(screen.getByRole('button', { name: /run test/i })).toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });
});
