/**
 * AgentModelConfig — Sprint 10.6 Phase 2 (Task 2.2)
 *
 * A self-contained row that renders:
 *  - Agent label
 *  - Provider dropdown (first option = "Default (Azure / ChatGPT-UAT)")
 *  - Model dropdown filtered to the selected provider (hidden when default is chosen)
 *  - Active-value badge
 *
 * Selecting the default option fires onChange(null, null).
 * Selecting a provider fires onChange(provider, null) — model resets.
 * Selecting a model fires onChange(currentProvider, model).
 */
import React from 'react';
import type { AvailableProvider } from '../types/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentModelConfigProps {
  /** Display label, e.g. "Observation Agent" */
  label: string;
  /** Full list of available providers (from /api/settings/providers) */
  providers: AvailableProvider[];
  /**
   * Currently selected provider name.
   * `null` means "no override — use the Azure default".
   */
  provider: string | null;
  /**
   * Currently selected model id.
   * `null` means either no override or provider just changed.
   */
  model: string | null;
  /** Called whenever the user changes provider or model. */
  onChange: (provider: string | null, model: string | null) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_LABEL = 'Default (Azure / ChatGPT-UAT)';
const DEFAULT_VALUE = '';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Renders a single agent-model configuration row for the Agent Workflow
 * Configuration section in SettingsPage.
 */
export const AgentModelConfig: React.FC<AgentModelConfigProps> = ({
  label,
  providers,
  provider,
  model,
  onChange,
}) => {
  // The provider whose models to list in the model dropdown.
  const activeProviderData = providers.find((p) => p.name === provider) ?? null;
  const hasUnavailableProvider = provider != null && activeProviderData == null;
  const modelOptions = activeProviderData?.models ?? (model ? [model] : []);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === DEFAULT_VALUE) {
      onChange(null, null);
    } else {
      // Reset model when the provider changes.
      onChange(value, null);
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    // Keep current provider; update model (empty string → null).
    onChange(provider, value === DEFAULT_VALUE ? null : value);
  };

  // ── Badge ─────────────────────────────────────────────────────────────────

  const badgeContent =
    provider == null
      ? DEFAULT_LABEL
      : model
        ? `${provider} / ${model}`
        : provider;

  const isDefault = provider == null;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-1.5 py-3 border-b border-gray-100 last:border-b-0">
      {/* Row: label + selects */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Agent name label */}
        <span className="w-48 text-sm font-medium text-gray-700 shrink-0">
          {label}
        </span>

        {/* Provider dropdown */}
        <div className="flex flex-col gap-0.5">
          <label
            htmlFor={`provider-${label}`}
            className="sr-only"
          >
            provider
          </label>
          <select
            id={`provider-${label}`}
            aria-label="provider"
            value={provider ?? DEFAULT_VALUE}
            onChange={handleProviderChange}
            className="rounded border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value={DEFAULT_VALUE}>{DEFAULT_LABEL}</option>
            {hasUnavailableProvider && (
              <option value={provider}>
                {provider} (current setting)
              </option>
            )}
            {providers.map((p) => (
              <option
                key={p.name}
                value={p.name}
                disabled={!p.is_configured}
              >
                {p.display_name}
                {!p.is_configured ? ' (not configured)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Model dropdown — only visible when a non-default provider is chosen */}
        {(activeProviderData != null || modelOptions.length > 0) && (
          <div className="flex flex-col gap-0.5">
            <label
              htmlFor={`model-${label}`}
              className="sr-only"
            >
              model
            </label>
            <select
              id={`model-${label}`}
              aria-label="model"
              value={model ?? DEFAULT_VALUE}
              onChange={handleModelChange}
              className="rounded border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value={DEFAULT_VALUE}>— select model —</option>
              {modelOptions.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Active value badge */}
      <div>
        <span
          data-testid="agent-model-badge"
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
            isDefault
              ? 'bg-gray-100 text-gray-600'
              : 'bg-blue-50 text-blue-700 border border-blue-200'
          }`}
        >
          {isDefault ? (
            <>
              <span className="text-gray-400">⟳</span>
              {DEFAULT_LABEL}
            </>
          ) : (
            badgeContent
          )}
        </span>
      </div>
    </div>
  );
};

export default AgentModelConfig;
