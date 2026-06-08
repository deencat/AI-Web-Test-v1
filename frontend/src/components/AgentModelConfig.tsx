/**
 * AgentModelConfig — Sprint 10.6 Phase 2 (Task 2.2)
 * Sprint 10.20: ModelSelectWithCustom for per-agent custom model support.
 */
import React, { useState } from 'react';
import type { AvailableProvider } from '../types/api';
import { ModelSelectWithCustom } from './ModelSelectWithCustom';
import type { CustomFieldValues } from './ModelSelectWithCustom';
import {
  getModelOptionsForProvider,
  getSafeModelOptionsForProvider,
  isCustomModelSelection,
} from '../utils/modelSelectUtils';

export interface AgentModelConfigProps {
  label: string;
  providers: AvailableProvider[];
  provider: string | null;
  model: string | null;
  onChange: (provider: string | null, model: string | null) => void;
}

const DEFAULT_LABEL = 'Default (Azure / ChatGPT-UAT)';
const DEFAULT_VALUE = '';

export const AgentModelConfig: React.FC<AgentModelConfigProps> = ({
  label,
  providers,
  provider,
  model,
  onChange,
}) => {
  const [customFields, setCustomFields] = useState<CustomFieldValues>({
    modelId: model ?? '',
    endpoint: '',
    apiVersion: '',
    apiKey: '',
  });

  const activeProviderData = providers.find((p) => p.name === provider) ?? null;
  const hasUnavailableProvider = provider != null && activeProviderData == null;

  const modelOptions =
    provider != null
      ? getSafeModelOptionsForProvider(provider, model, providers)
      : [];

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === DEFAULT_VALUE) {
      onChange(null, null);
    } else {
      onChange(value, null);
    }
  };

  const handleModelChange = (modelId: string) => {
    onChange(provider, modelId || null);
    setCustomFields((prev) => ({ ...prev, modelId }));
  };

  const badgeContent =
    provider == null
      ? DEFAULT_LABEL
      : model
        ? `${provider} / ${model}`
        : provider;

  const isDefault = provider == null;
  const showCustomFields =
    provider != null &&
    model != null &&
    isCustomModelSelection(provider, model, providers);

  return (
    <div className="flex flex-col gap-1.5 py-3 border-b border-gray-100 last:border-b-0">
      <div className="flex flex-wrap items-center gap-3">
        <span className="w-48 text-sm font-medium text-gray-700 shrink-0">
          {label}
        </span>

        <div className="flex flex-col gap-0.5">
          <label htmlFor={`provider-${label}`} className="sr-only">
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
              <option value={provider}>{provider} (current setting)</option>
            )}
            {providers.map((p) => (
              <option key={p.name} value={p.name} disabled={!p.is_configured}>
                {p.display_name}
                {!p.is_configured ? ' (not configured)' : ''}
              </option>
            ))}
          </select>
        </div>

        {(activeProviderData != null || modelOptions.length > 0) && provider && (
          <div className="flex flex-col gap-0.5 min-w-[220px] flex-1">
            <label htmlFor={`model-${label}`} className="sr-only">
              model
            </label>
            <ModelSelectWithCustom
              providerName={provider}
              modelOptions={getModelOptionsForProvider(provider, providers)}
              selectedModel={model ?? ''}
              onModelChange={handleModelChange}
              customFields={
                showCustomFields || !model
                  ? customFields
                  : undefined
              }
              onCustomFieldsChange={setCustomFields}
              availableProviders={providers}
              className="rounded border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full"
              aria-label="model"
            />
          </div>
        )}
      </div>

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
