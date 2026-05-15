/**
 * RootCauseAnalysisPanel — Sprint 10.12
 *
 * Collapsible panel that displays the AI-generated root cause analysis for a
 * failed test step (error_type == "all_tiers_exhausted").
 *
 * Renders nothing when rootCauseAnalysis is null/undefined/empty.
 * Collapsed by default; expanded on button click.
 */

import { useState } from 'react';

interface RootCauseAnalysisPanelProps {
  rootCauseAnalysis: string | null | undefined;
}

export function RootCauseAnalysisPanel({ rootCauseAnalysis }: RootCauseAnalysisPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!rootCauseAnalysis) {
    return null;
  }

  return (
    <div className="mt-2 border border-amber-200 rounded bg-amber-50">
      <button
        type="button"
        aria-label="Root Cause Analysis"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="w-full flex items-center justify-between px-3 py-2 text-left text-sm font-medium text-amber-800 hover:bg-amber-100 rounded focus:outline-none"
      >
        <span>🔍 Root Cause Analysis</span>
        <span className="text-amber-600">{isExpanded ? '▲' : '▼'}</span>
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 pt-1">
          <em className="block text-sm text-amber-900 italic">{rootCauseAnalysis}</em>
        </div>
      )}
    </div>
  );
}
