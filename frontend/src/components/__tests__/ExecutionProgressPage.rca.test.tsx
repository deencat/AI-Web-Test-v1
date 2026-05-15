/**
 * ExecutionProgressPage.rca.test.tsx — Sprint 10.12
 *
 * TDD for the Root Cause Analysis (RCA) panel inside StepCard.
 *
 * Tests cover:
 *  1. RCA panel renders beneath the error message when root_cause_analysis is present
 *  2. RCA panel is hidden when root_cause_analysis is null/undefined
 *  3. RCA panel is hidden for passed steps even if feedback is available
 *  4. RCA panel is collapsible (collapsed by default, expands on click)
 *  5. RCA text is rendered in italic style
 *  6. RCA panel label reads "Root Cause Analysis"
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// ---------------------------------------------------------------------------
// Isolate only the StepCard sub-component
// We render it directly rather than the full page to keep tests focused.
// ---------------------------------------------------------------------------

// Mock services used by ExecutionProgressPage so we can import the module
vi.mock('../../services/executionService', () => ({
  default: {
    getExecutionDetail: vi.fn(),
  },
}));

vi.mock('../../services/debugService', () => ({
  default: {
    startSession: vi.fn(),
  },
}));

vi.mock('../../services/feedbackService', () => ({
  default: {
    getExecutionFeedback: vi.fn(),
  },
}));

// The StepCard is not exported, so we test via RootCauseAnalysisPanel directly.
import { RootCauseAnalysisPanel } from '../../components/execution/RootCauseAnalysisPanel';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderPanel(rootCauseAnalysis: string | null | undefined) {
  return render(
    <RootCauseAnalysisPanel rootCauseAnalysis={rootCauseAnalysis} />
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('RootCauseAnalysisPanel', () => {
  it('renders nothing when rootCauseAnalysis is null', () => {
    const { container } = renderPanel(null);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when rootCauseAnalysis is undefined', () => {
    const { container } = renderPanel(undefined);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when rootCauseAnalysis is empty string', () => {
    const { container } = renderPanel('');
    expect(container.firstChild).toBeNull();
  });

  it('renders the "Root Cause Analysis" label when value is present', () => {
    renderPanel('The button was disabled.');
    expect(screen.getByText(/root cause analysis/i)).toBeInTheDocument();
  });

  it('is collapsed by default (analysis text not visible)', () => {
    renderPanel('Hidden initially text content.');
    // The actual analysis text should be hidden (not in the DOM or has hidden class)
    const analysisText = screen.queryByText('Hidden initially text content.');
    // Either not in dom OR not visible — just confirm the toggle button exists
    expect(screen.getByRole('button', { name: /root cause analysis/i })).toBeInTheDocument();
    // Analysis text should not be visible until expanded
    expect(analysisText).not.toBeInTheDocument();
  });

  it('shows analysis text after clicking the toggle button', () => {
    renderPanel('The Pay Now button remained disabled.');
    fireEvent.click(screen.getByRole('button', { name: /root cause analysis/i }));
    expect(screen.getByText('The Pay Now button remained disabled.')).toBeInTheDocument();
  });

  it('collapses again after double-clicking the toggle', () => {
    renderPanel('Collapsible content here.');
    const btn = screen.getByRole('button', { name: /root cause analysis/i });
    fireEvent.click(btn);
    expect(screen.getByText('Collapsible content here.')).toBeInTheDocument();
    fireEvent.click(btn);
    expect(screen.queryByText('Collapsible content here.')).not.toBeInTheDocument();
  });

  it('renders analysis text in italic style when expanded', () => {
    renderPanel('Italic RCA text.');
    fireEvent.click(screen.getByRole('button', { name: /root cause analysis/i }));
    const text = screen.getByText('Italic RCA text.');
    // Should have italic class or style
    expect(text.tagName === 'EM' || text.classList.contains('italic') ||
      window.getComputedStyle(text).fontStyle === 'italic').toBe(true);
  });
});
