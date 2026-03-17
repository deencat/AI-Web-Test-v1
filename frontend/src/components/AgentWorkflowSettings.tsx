/**
 * AgentWorkflowSettings — Sprint 10.6 Phase 3 (Task 3.1)
 *
 * Wraps 4 × AgentModelConfig rows (Observation, Requirements, Analysis,
 * Evolution) into a single collapsible card section that plugs into
 * SettingsPage.tsx.
 *
 * Design constraints:
 *  - Visually and functionally separate from "Test Generation Settings" and
 *    "Test Execution Settings" sections.
 *  - Each agent defaults to "Default (Azure / ChatGPT-UAT)" when unset.
 *  - SettingsPage passes 8 nullable state vars + 4 onChange callbacks.
 */
import React, { useState } from 'react';
import { AgentModelConfig } from './AgentModelConfig';
import type { AvailableProvider } from '../types/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentConfig {
  provider: string | null;
  model: string | null;
}

export interface AgentWorkflowSettingsProps {
  /** Available providers list from /api/settings/providers */
  providers: AvailableProvider[];

  // ── Per-agent state ──────────────────────────────────────────────────────
  observation: AgentConfig;
  requirements: AgentConfig;
  analysis: AgentConfig;
  evolution: AgentConfig;

  // ── Per-agent change callbacks ───────────────────────────────────────────
  onObservationChange: (provider: string | null, model: string | null) => void;
  onRequirementsChange: (provider: string | null, model: string | null) => void;
  onAnalysisChange: (provider: string | null, model: string | null) => void;
  onEvolutionChange: (provider: string | null, model: string | null) => void;
}

// ---------------------------------------------------------------------------
// Row definitions (avoids repetition inside JSX)
// ---------------------------------------------------------------------------

type AgentRow = {
  label: string;
  config: AgentConfig;
  onChange: (provider: string | null, model: string | null) => void;
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Renders the "Agent Workflow Configuration" collapsible section.
 * Four agents each get an AgentModelConfig row with independent provider and
 * model dropdowns. Collapsed by default to keep the settings page scannable.
 */
export const AgentWorkflowSettings: React.FC<AgentWorkflowSettingsProps> = ({
  providers,
  observation,
  requirements,
  analysis,
  evolution,
  onObservationChange,
  onRequirementsChange,
  onAnalysisChange,
  onEvolutionChange,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  const agentRows: AgentRow[] = [
    { label: 'Observation Agent', config: observation, onChange: onObservationChange },
    { label: 'Requirements Agent', config: requirements, onChange: onRequirementsChange },
    { label: 'Analysis Agent', config: analysis, onChange: onAnalysisChange },
    { label: 'Evolution Agent', config: evolution, onChange: onEvolutionChange },
  ];

  // Count of agents that have an active override (for the summary badge).
  const configuredCount = agentRows.filter((r) => r.config.provider != null).length;

  return (
    <div>
      {/* ── Section header ─────────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Agent Workflow Configuration
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Override the LLM provider and model for each agent in the 4-agent
            pipeline. Agents without an override use the Azure default
            (ChatGPT-UAT).
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* Summary badge */}
          <span
            className={`px-3 py-1 text-xs font-medium rounded-full ${
              configuredCount > 0
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {configuredCount > 0
              ? `${configuredCount} override${configuredCount > 1 ? 's' : ''} active`
              : 'All using Azure default'}
          </span>
          {/* Collapse toggle */}
          <button
            type="button"
            aria-label={collapsed ? 'Expand agent config' : 'Collapse agent config'}
            onClick={() => setCollapsed((c) => !c)}
            className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          >
            {collapsed ? '▼ Expand' : '▲ Collapse'}
          </button>
        </div>
      </div>

      {/* ── Agent rows ─────────────────────────────────────────────────── */}
      {!collapsed && (
        <div>
          {agentRows.map((row) => (
            <AgentModelConfig
              key={row.label}
              label={row.label}
              providers={providers}
              provider={row.config.provider}
              model={row.config.model}
              onChange={row.onChange}
            />
          ))}

          {/* Informational note */}
          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex gap-2">
              <span className="text-amber-600 text-sm">ℹ</span>
              <p className="text-xs text-amber-800">
                Agent Workflow settings are completely independent of Test
                Generation and Test Execution provider settings. Changing one
                does not affect the others.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentWorkflowSettings;
