'use client';

import React, { useState } from 'react';
import type { ModelOption } from '../types/api';
import {
  CUSTOM_MODEL_SENTINEL,
  appendCustomSentinel,
  getSelectValue,
} from '../utils/modelSelectUtils';

export interface CustomFieldValues {
  modelId: string;
  endpoint?: string;
  apiVersion?: string;
  apiKey?: string;
}

export interface ModelSelectWithCustomProps {
  providerName: string;
  modelOptions: ModelOption[];
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  customFields?: CustomFieldValues;
  onCustomFieldsChange?: (fields: CustomFieldValues) => void;
  availableProviders?: { name: string; models?: string[]; model_options?: ModelOption[] }[];
  className?: string;
  'aria-label'?: string;
}

/**
 * Shared model dropdown with Free / Paid / My Models / Custom optgroups
 * and provider-specific custom-model input fields (Sprint 10.20).
 */
export const ModelSelectWithCustom: React.FC<ModelSelectWithCustomProps> = ({
  providerName,
  modelOptions,
  selectedModel,
  onModelChange,
  customFields,
  onCustomFieldsChange,
  availableProviders = [],
  className = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white',
  'aria-label': ariaLabel = 'model',
}) => {
  const [showAzureAdvanced, setShowAzureAdvanced] = useState(false);

  const options = appendCustomSentinel(modelOptions);
  const selectValue =
    availableProviders.length > 0
      ? getSelectValue(providerName, selectedModel, availableProviders)
      : options.some((o) => o.id === selectedModel)
        ? selectedModel
        : CUSTOM_MODEL_SENTINEL;

  const isCustomSelected = selectValue === CUSTOM_MODEL_SENTINEL;

  const free = options.filter(
    (m) => m.is_free && !m.is_custom && m.id !== CUSTOM_MODEL_SENTINEL,
  );
  const paid = options.filter(
    (m) => !m.is_free && !m.is_custom && m.id !== CUSTOM_MODEL_SENTINEL,
  );
  const myModels = options.filter((m) => m.is_custom);
  const custom = options.filter((m) => m.id === CUSTOM_MODEL_SENTINEL);

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === CUSTOM_MODEL_SENTINEL) {
      onModelChange(customFields?.modelId || '');
      return;
    }
    onModelChange(value);
  };

  const updateCustomFields = (patch: Partial<CustomFieldValues>) => {
    if (!onCustomFieldsChange) return;
    onCustomFieldsChange({
      modelId: customFields?.modelId ?? '',
      endpoint: customFields?.endpoint,
      apiVersion: customFields?.apiVersion,
      apiKey: customFields?.apiKey,
      ...patch,
    });
  };

  return (
    <div>
      <select
        aria-label={ariaLabel}
        value={selectValue}
        onChange={handleSelectChange}
        className={className}
      >
        {free.length > 0 && (
          <optgroup label="🆓 Free Models ($0/M tokens)">
            {free.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name} (Free)
              </option>
            ))}
          </optgroup>
        )}
        {paid.length > 0 && (
          <optgroup label="💰 Paid Models">
            {paid.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name}
              </option>
            ))}
          </optgroup>
        )}
        {myModels.length > 0 && (
          <optgroup label="⭐ My Models">
            {myModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name}
              </option>
            ))}
          </optgroup>
        )}
        {custom.length > 0 && (
          <optgroup label="⚙ Custom">
            {custom.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name}
              </option>
            ))}
          </optgroup>
        )}
      </select>

      {isCustomSelected && onCustomFieldsChange && (
        <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-lg space-y-3">
          <p className="text-xs font-medium text-orange-800">
            Custom model — enter a model ID not in the curated list
          </p>
          <div>
            <label htmlFor={`${providerName}-custom-model-id`} className="block text-xs font-medium text-gray-700 mb-1">Model ID</label>
            <input
              id={`${providerName}-custom-model-id`}
              type="text"
              value={customFields?.modelId ?? ''}
              onChange={(e) => {
                updateCustomFields({ modelId: e.target.value });
                onModelChange(e.target.value);
              }}
              placeholder="e.g. my/vendor-model:free"
              className="w-full px-3 py-1.5 text-sm border border-orange-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-400"
            />
          </div>

          {providerName === 'local_vllm' && (
            <>
              <div>
                <label htmlFor={`${providerName}-custom-endpoint`} className="block text-xs font-medium text-gray-700 mb-1">Endpoint URL</label>
                <input
                  id={`${providerName}-custom-endpoint`}
                  type="text"
                  value={customFields?.endpoint ?? ''}
                  onChange={(e) => updateCustomFields({ endpoint: e.target.value })}
                  placeholder="e.g. http://192.168.206.164:1235/v1"
                  className="w-full px-3 py-1.5 text-sm border border-orange-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>
              <div>
                <label htmlFor={`${providerName}-custom-api-key`} className="block text-xs font-medium text-gray-700 mb-1">API Token</label>
                <input
                  id={`${providerName}-custom-api-key`}
                  type="password"
                  value={customFields?.apiKey ?? ''}
                  onChange={(e) => updateCustomFields({ apiKey: e.target.value })}
                  placeholder="e.g. 1235"
                  className="w-full px-3 py-1.5 text-sm border border-orange-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>
            </>
          )}

          {providerName === 'azure' && (
            <div>
              <button
                type="button"
                onClick={() => setShowAzureAdvanced((v) => !v)}
                className="text-xs font-medium text-orange-800 hover:text-orange-900"
              >
                {showAzureAdvanced ? '▲ Hide Advanced' : '▼ Advanced (endpoint + API version)'}
              </button>
              {showAzureAdvanced && (
                <div className="mt-2 space-y-2">
                  <div>
                    <label htmlFor={`${providerName}-azure-endpoint`} className="block text-xs font-medium text-gray-700 mb-1">
                      Azure Endpoint
                    </label>
                    <input
                      id={`${providerName}-azure-endpoint`}
                      type="text"
                      value={customFields?.endpoint ?? ''}
                      onChange={(e) => updateCustomFields({ endpoint: e.target.value })}
                      placeholder="https://myresource.openai.azure.com"
                      className="w-full px-3 py-1.5 text-sm border border-orange-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-400"
                    />
                  </div>
                  <div>
                    <label htmlFor={`${providerName}-azure-api-version`} className="block text-xs font-medium text-gray-700 mb-1">
                      API Version
                    </label>
                    <input
                      id={`${providerName}-azure-api-version`}
                      type="text"
                      value={customFields?.apiVersion ?? ''}
                      onChange={(e) => updateCustomFields({ apiVersion: e.target.value })}
                      placeholder="2024-12-01-preview"
                      className="w-full px-3 py-1.5 text-sm border border-orange-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-400"
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ModelSelectWithCustom;
