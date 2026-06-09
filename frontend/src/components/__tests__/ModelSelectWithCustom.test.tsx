/**
 * ModelSelectWithCustom.test.tsx — Sprint 10.20
 *
 * TDD RED → GREEN: shared model dropdown with custom sentinel + optgroups.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelSelectWithCustom } from '../ModelSelectWithCustom';
import type { ModelOption } from '../../types/api';
import { CUSTOM_MODEL_SENTINEL } from '../../utils/modelSelectUtils';

const curatedOptions: ModelOption[] = [
  { id: 'google/gemini-2.0-flash-exp:free', display_name: 'Gemini Flash', is_free: true },
  { id: 'openai/gpt-4o', display_name: 'GPT-4o', is_free: false },
];

const myModelOptions: ModelOption[] = [
  ...curatedOptions,
  { id: 'my/custom:free', display_name: 'My Custom', is_free: true, is_custom: true },
];

describe('ModelSelectWithCustom', () => {
  it('renders custom sentinel option for openrouter provider', () => {
    render(
      <ModelSelectWithCustom
        providerName="openrouter"
        modelOptions={curatedOptions}
        selectedModel="google/gemini-2.0-flash-exp:free"
        onModelChange={vi.fn()}
      />,
    );

    expect(screen.getByRole('option', { name: /Custom model/i })).toBeTruthy();
  });

  it('groups saved custom models under My Models optgroup', () => {
    render(
      <ModelSelectWithCustom
        providerName="openrouter"
        modelOptions={myModelOptions}
        selectedModel="my/custom:free"
        onModelChange={vi.fn()}
      />,
    );

    const optgroups = document.querySelectorAll('optgroup');
    const myModelsGroup = Array.from(optgroups).find((g) =>
      g.getAttribute('label')?.includes('My Models'),
    );
    expect(myModelsGroup).toBeTruthy();
    expect(myModelsGroup?.querySelector(`option[value="my/custom:free"]`)).toBeTruthy();
  });

  it('fires onModelChange when user selects a curated model', () => {
    const onModelChange = vi.fn();
    render(
      <ModelSelectWithCustom
        providerName="openrouter"
        modelOptions={curatedOptions}
        selectedModel="google/gemini-2.0-flash-exp:free"
        onModelChange={onModelChange}
      />,
    );

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'openai/gpt-4o' },
    });

    expect(onModelChange).toHaveBeenCalledWith('openai/gpt-4o');
  });

  it('shows model ID input when custom sentinel is selected', () => {
    render(
      <ModelSelectWithCustom
        providerName="openrouter"
        modelOptions={curatedOptions}
        selectedModel={CUSTOM_MODEL_SENTINEL}
        onModelChange={vi.fn()}
        customFields={{ modelId: '' }}
        onCustomFieldsChange={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Model ID')).toBeTruthy();
  });

  it('shows vLLM endpoint fields only for local_vllm custom selection', () => {
    render(
      <ModelSelectWithCustom
        providerName="local_vllm"
        modelOptions={[{ id: 'DeepSeek-V4-Flash-4bit', display_name: 'DeepSeek', is_free: false }]}
        selectedModel={CUSTOM_MODEL_SENTINEL}
        onModelChange={vi.fn()}
        customFields={{ modelId: '', endpoint: '', apiKey: '' }}
        onCustomFieldsChange={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Endpoint URL')).toBeTruthy();
    expect(screen.getByLabelText('API Token')).toBeTruthy();
  });

  it('does not show vLLM endpoint fields for openrouter custom selection', () => {
    render(
      <ModelSelectWithCustom
        providerName="openrouter"
        modelOptions={curatedOptions}
        selectedModel={CUSTOM_MODEL_SENTINEL}
        onModelChange={vi.fn()}
        customFields={{ modelId: '' }}
        onCustomFieldsChange={vi.fn()}
      />,
    );

    expect(screen.queryByPlaceholderText(/endpoint url/i)).toBeNull();
  });

  it('shows Azure advanced endpoint fields for azure custom selection', () => {
    render(
      <ModelSelectWithCustom
        providerName="azure"
        modelOptions={[{ id: 'ChatGPT-UAT', display_name: 'ChatGPT-UAT', is_free: false }]}
        selectedModel={CUSTOM_MODEL_SENTINEL}
        onModelChange={vi.fn()}
        customFields={{ modelId: '', endpoint: '', apiVersion: '' }}
        onCustomFieldsChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText(/Advanced/i));
    expect(screen.getByLabelText('Azure Endpoint')).toBeTruthy();
    expect(screen.getByLabelText('API Version')).toBeTruthy();
  });
});
