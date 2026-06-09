import type { ModelOption } from '../types/api';

/** Sentinel value in model dropdowns meaning "enter a custom model ID". */
export const CUSTOM_MODEL_SENTINEL = '__custom__';

export const CUSTOM_SENTINEL_OPTION: ModelOption = {
  id: CUSTOM_MODEL_SENTINEL,
  display_name: '⚙ Custom model...',
  is_free: false,
};

/**
 * Append the custom-model sentinel to every provider's option list.
 */
export function appendCustomSentinel(options: ModelOption[]): ModelOption[] {
  if (options.some((o) => o.id === CUSTOM_MODEL_SENTINEL)) {
    return options;
  }
  return [...options, CUSTOM_SENTINEL_OPTION];
}

/**
 * Return model options for a provider, falling back to constructing from plain ids.
 */
export function getModelOptionsForProvider(
  providerName: string,
  availableProviders: { name: string; models?: string[]; model_options?: ModelOption[] }[],
): ModelOption[] {
  const provider = availableProviders.find((p) => p.name === providerName);
  if (!provider) {
    return [];
  }
  if (provider.model_options && provider.model_options.length > 0) {
    return provider.model_options;
  }
  return (provider.models || []).map((id) => ({
    id,
    display_name: id,
    is_free: id.endsWith(':free'),
  }));
}

/**
 * Safe options for a dropdown: curated + registry + sentinel, with fallback for unknown saved model.
 */
export function getSafeModelOptionsForProvider(
  providerName: string,
  currentModel: string | null,
  availableProviders: { name: string; models?: string[]; model_options?: ModelOption[] }[],
): ModelOption[] {
  const options = appendCustomSentinel(getModelOptionsForProvider(providerName, availableProviders));

  if (options.length > 1) {
    return options;
  }

  if (!currentModel) {
    return options;
  }

  return appendCustomSentinel([
    {
      id: currentModel,
      display_name: currentModel,
      is_free: currentModel.endsWith(':free'),
    },
  ]);
}

/**
 * Map a saved model id to the <select> value (sentinel when not in known list).
 */
export function getSelectValue(
  providerName: string,
  modelId: string,
  availableProviders: { name: string; models?: string[]; model_options?: ModelOption[] }[],
): string {
  const knownIds = getModelOptionsForProvider(providerName, availableProviders).map((m) => m.id);
  if (knownIds.includes(modelId)) {
    return modelId;
  }
  return CUSTOM_MODEL_SENTINEL;
}

export function isCustomModelSelection(
  providerName: string,
  modelId: string,
  availableProviders: { name: string; models?: string[]; model_options?: ModelOption[] }[],
): boolean {
  return getSelectValue(providerName, modelId, availableProviders) === CUSTOM_MODEL_SENTINEL;
}
