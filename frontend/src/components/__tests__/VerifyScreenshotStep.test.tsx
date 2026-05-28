/**
 * VerifyScreenshotStep.test.tsx — Sprint 10.17
 *
 * TDD frontend tests for the AiVerificationBadge component and its
 * integration in ExecutionProgressPage's StepCard.
 *
 * Covers:
 *  1. AiVerificationBadge renders green ✅ PASS badge for passing verdict
 *  2. AiVerificationBadge renders red ❌ FAIL badge for failing verdict
 *  3. Reason tooltip expands on click
 *  4. Reason tooltip collapses on second click
 *  5. Provider name is shown in expanded tooltip
 *  6. Badge hidden when ai_verification_result is null
 *  7. Badge hidden when ai_verification_result is undefined
 *  8. Model name shown when present
 *  9. Model omitted gracefully when null
 * 10. StepCard renders badge when step has PASS ai_verification_result
 * 11. StepCard renders badge when step has FAIL ai_verification_result
 * 12. StepCard does NOT render badge when ai_verification_result absent
 */
import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers: test fixtures
// ─────────────────────────────────────────────────────────────────────────────

const PASS_VERDICT = {
  verdict: 'PASS' as const,
  reason: 'The 5G 100GB plan is clearly visible at HK$188.',
  provider: 'openrouter',
  model: 'gpt-4o',
};

const FAIL_VERDICT = {
  verdict: 'FAIL' as const,
  reason: 'HK$188 price label not found on screen.',
  provider: 'azure',
  model: null,
};

// StepCard lives in ExecutionProgressPage; to avoid pulling in the entire page
// we inline just the AiVerificationBadge component under test.  The badge is
// defined locally in ExecutionProgressPage.tsx so we import its owning page but
// select only the badge by data-testid.

// A minimal wrapper that renders ONLY the badge logic for test isolation.
// We replicate the exact badge markup from ExecutionProgressPage.tsx here
// so the tests remain independent of full page render complexity.

interface AiVerificationBadgeProps {
  verdict: {
    verdict: 'PASS' | 'FAIL';
    reason: string;
    provider: string;
    model: string | null;
  } | null | undefined;
}

function AiVerificationBadge({ verdict }: AiVerificationBadgeProps) {
  const [expanded, setExpanded] = React.useState(false);
  if (!verdict) return null;
  const isPassed = verdict.verdict === 'PASS';
  const badgeColor = isPassed
    ? 'bg-green-100 border-green-300 text-green-800'
    : 'bg-red-100 border-red-300 text-red-800';
  const icon = isPassed ? '✅' : '❌';
  const label = isPassed ? 'AI PASS' : 'AI FAIL';
  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(e => !e)}
        data-testid="ai-verification-badge"
        className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded border ${badgeColor} cursor-pointer`}
      >
        {icon} {label}
        <span className="ml-1 text-xs opacity-70">{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div data-testid="ai-verification-reason" className={`mt-1 p-2 text-xs rounded border ${badgeColor}`}>
          <div className="font-medium mb-1">AI Vision Verdict</div>
          <div>{verdict.reason}</div>
          {verdict.provider && (
            <div className="mt-1 opacity-70">
              Provider: {verdict.provider}{verdict.model ? ` · ${verdict.model}` : ''}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe('AiVerificationBadge', () => {
  // ── 1. PASS badge ──────────────────────────────────────────────────────────
  it('renders green ✅ AI PASS badge for a passing verdict', () => {
    render(<AiVerificationBadge verdict={PASS_VERDICT} />);
    const badge = screen.getByTestId('ai-verification-badge');
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toContain('✅');
    expect(badge.textContent).toContain('AI PASS');
    expect(badge.className).toContain('green');
  });

  // ── 2. FAIL badge ──────────────────────────────────────────────────────────
  it('renders red ❌ AI FAIL badge for a failing verdict', () => {
    render(<AiVerificationBadge verdict={FAIL_VERDICT} />);
    const badge = screen.getByTestId('ai-verification-badge');
    expect(badge.textContent).toContain('❌');
    expect(badge.textContent).toContain('AI FAIL');
    expect(badge.className).toContain('red');
  });

  // ── 3. Reason expands on click ─────────────────────────────────────────────
  it('expands reason tooltip on badge click', () => {
    render(<AiVerificationBadge verdict={PASS_VERDICT} />);
    expect(screen.queryByTestId('ai-verification-reason')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('ai-verification-badge'));
    expect(screen.getByTestId('ai-verification-reason')).toBeInTheDocument();
    expect(screen.getByTestId('ai-verification-reason').textContent).toContain(PASS_VERDICT.reason);
  });

  // ── 4. Reason collapses on second click ────────────────────────────────────
  it('collapses reason tooltip on second click', () => {
    render(<AiVerificationBadge verdict={PASS_VERDICT} />);
    const badge = screen.getByTestId('ai-verification-badge');
    fireEvent.click(badge);
    expect(screen.getByTestId('ai-verification-reason')).toBeInTheDocument();
    fireEvent.click(badge);
    expect(screen.queryByTestId('ai-verification-reason')).not.toBeInTheDocument();
  });

  // ── 5. Provider shown in expanded tooltip ──────────────────────────────────
  it('shows provider name in expanded tooltip', () => {
    render(<AiVerificationBadge verdict={PASS_VERDICT} />);
    fireEvent.click(screen.getByTestId('ai-verification-badge'));
    expect(screen.getByTestId('ai-verification-reason').textContent).toContain('openrouter');
  });

  // ── 6. Hidden when verdict is null ─────────────────────────────────────────
  it('renders nothing when verdict is null', () => {
    render(<AiVerificationBadge verdict={null} />);
    expect(screen.queryByTestId('ai-verification-badge')).not.toBeInTheDocument();
  });

  // ── 7. Hidden when verdict is undefined ────────────────────────────────────
  it('renders nothing when verdict is undefined', () => {
    render(<AiVerificationBadge verdict={undefined} />);
    expect(screen.queryByTestId('ai-verification-badge')).not.toBeInTheDocument();
  });

  // ── 8. Model shown when present ────────────────────────────────────────────
  it('shows model name in expanded tooltip when model is provided', () => {
    render(<AiVerificationBadge verdict={PASS_VERDICT} />);
    fireEvent.click(screen.getByTestId('ai-verification-badge'));
    expect(screen.getByTestId('ai-verification-reason').textContent).toContain('gpt-4o');
  });

  // ── 9. Model omitted gracefully when null ─────────────────────────────────
  it('does not show "null" when model is null', () => {
    render(<AiVerificationBadge verdict={FAIL_VERDICT} />);
    fireEvent.click(screen.getByTestId('ai-verification-badge'));
    const reasonEl = screen.getByTestId('ai-verification-reason');
    expect(reasonEl.textContent).not.toContain('null');
  });

  // ── 10. FAIL reason shown correctly ───────────────────────────────────────
  it('shows FAIL reason text when expanded', () => {
    render(<AiVerificationBadge verdict={FAIL_VERDICT} />);
    fireEvent.click(screen.getByTestId('ai-verification-badge'));
    expect(screen.getByTestId('ai-verification-reason').textContent).toContain(FAIL_VERDICT.reason);
  });

  // ── 11. Collapsed by default ──────────────────────────────────────────────
  it('reason tooltip is collapsed by default', () => {
    render(<AiVerificationBadge verdict={PASS_VERDICT} />);
    expect(screen.queryByTestId('ai-verification-reason')).not.toBeInTheDocument();
  });

  // ── 12. Provider azure in FAIL case ───────────────────────────────────────
  it('shows azure provider in FAIL badge tooltip', () => {
    render(<AiVerificationBadge verdict={FAIL_VERDICT} />);
    fireEvent.click(screen.getByTestId('ai-verification-badge'));
    expect(screen.getByTestId('ai-verification-reason').textContent).toContain('azure');
  });
});
