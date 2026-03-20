/**
 * AgentModelConfig.test.tsx — Sprint 10.6 Phase 2
 *
 * TDD RED → GREEN cycle.
 *
 * Tests cover:
 *  - Default option renders "Default (Azure / ChatGPT-UAT)" label in provider dropdown
 *  - onChange fires with (null, null) when user selects the default option
 *  - onChange fires with correct (provider, model) when user selects a real provider+model
 *  - Unconfigured providers are disabled in the dropdown
 *  - Model dropdown only shows models belonging to the selected provider
 *  - Badge shows "Default (Azure / ChatGPT-UAT)" when no override is set
 *  - Badge shows resolved provider/model when an override is set
 *  - Selecting a different provider resets the model selection to null
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentModelConfig } from '../AgentModelConfig';
import type { AvailableProvider } from '../../types/api';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const googleProvider: AvailableProvider = {
  name: 'google',
  display_name: 'Google Gemini',
  is_configured: true,
  models: ['gemini-2.0-flash', 'gemini-1.5-pro'],
  recommended_model: 'gemini-2.0-flash',
};

const cerebrasProvider: AvailableProvider = {
  name: 'cerebras',
  display_name: 'Cerebras',
  is_configured: true,
  models: ['llama-4-scout-17b-16e-instruct', 'llama-3.3-70b'],
  recommended_model: 'llama-4-scout-17b-16e-instruct',
};

const unconfiguredProvider: AvailableProvider = {
  name: 'openrouter',
  display_name: 'OpenRouter',
  is_configured: false,
  models: [],
  recommended_model: '',
};

const allProviders: AvailableProvider[] = [
  googleProvider,
  cerebrasProvider,
  unconfiguredProvider,
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderComponent(
  provider: string | null,
  model: string | null,
  onChange = vi.fn(),
) {
  return render(
    <AgentModelConfig
      label="Observation Agent"
      providers={allProviders}
      provider={provider}
      model={model}
      onChange={onChange}
    />,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AgentModelConfig', () => {
  // ── 2.3-A: Default option ─────────────────────────────────────────────────
  describe('provider dropdown — default option', () => {
    it('renders "Default (Azure / ChatGPT-UAT)" as the first option', () => {
      renderComponent(null, null);

      const select = screen.getByRole('combobox', { name: /provider/i });
      const firstOption = select.querySelectorAll('option')[0];

      expect(firstOption).toBeTruthy();
      expect(firstOption.textContent).toMatch(/Default.*Azure.*ChatGPT-UAT/i);
    });

    it('shows "Default" option as selected when provider is null', () => {
      renderComponent(null, null);

      const select = screen.getByRole('combobox', { name: /provider/i }) as HTMLSelectElement;
      expect(select.value).toBe('');
    });
  });

  // ── 2.3-B: onChange fires correctly ──────────────────────────────────────
  describe('onChange callback', () => {
    it('fires (null, null) when user picks the default option', () => {
      const onChange = vi.fn();
      renderComponent('google', 'gemini-2.0-flash', onChange);

      const select = screen.getByRole('combobox', { name: /provider/i });
      fireEvent.change(select, { target: { value: '' } });

      expect(onChange).toHaveBeenCalledOnce();
      expect(onChange).toHaveBeenCalledWith(null, null);
    });

    it('fires (provider, null) with null model when user picks a new provider', () => {
      const onChange = vi.fn();
      renderComponent(null, null, onChange);

      const select = screen.getByRole('combobox', { name: /provider/i });
      fireEvent.change(select, { target: { value: 'google' } });

      expect(onChange).toHaveBeenCalledOnce();
      expect(onChange).toHaveBeenCalledWith('google', null);
    });

    it('fires (provider, model) when user selects a model from the model dropdown', () => {
      const onChange = vi.fn();
      renderComponent('google', null, onChange);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      fireEvent.change(modelSelect, { target: { value: 'gemini-1.5-pro' } });

      expect(onChange).toHaveBeenCalledOnce();
      expect(onChange).toHaveBeenCalledWith('google', 'gemini-1.5-pro');
    });
  });

  // ── 2.3-C: Unconfigured providers are disabled ───────────────────────────
  describe('disabled options for unconfigured providers', () => {
    it('renders unconfigured provider option as disabled', () => {
      renderComponent(null, null);

      const select = screen.getByRole('combobox', { name: /provider/i });
      const options = Array.from(select.querySelectorAll('option'));
      const openrouterOption = options.find((o) => o.value === 'openrouter');

      expect(openrouterOption).toBeTruthy();
      expect(openrouterOption!.disabled).toBe(true);
    });

    it('does NOT disable configured providers', () => {
      renderComponent(null, null);

      const select = screen.getByRole('combobox', { name: /provider/i });
      const options = Array.from(select.querySelectorAll('option'));
      const googleOption = options.find((o) => o.value === 'google');

      expect(googleOption).toBeTruthy();
      expect(googleOption!.disabled).toBe(false);
    });
  });

  // ── 2.3-D: Model dropdown filtered by selected provider ──────────────────
  describe('model dropdown', () => {
    it('only renders models belonging to the selected provider', () => {
      renderComponent('google', null);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      const options = Array.from(modelSelect.querySelectorAll('option')).filter(
        (o) => o.value !== '',
      );
      const modelValues = options.map((o) => o.value);

      expect(modelValues).toEqual(['gemini-2.0-flash', 'gemini-1.5-pro']);
      // No Cerebras models should appear
      expect(modelValues).not.toContain('llama-4-scout-17b-16e-instruct');
    });

    it('is hidden when provider is null (default/azure)', () => {
      renderComponent(null, null);

      const modelSelect = screen.queryByRole('combobox', { name: /model/i });
      expect(modelSelect).toBeNull();
    });

    it('shows the selected model as selected', () => {
      renderComponent('google', 'gemini-1.5-pro');

      const modelSelect = screen.getByRole('combobox', { name: /model/i }) as HTMLSelectElement;
      expect(modelSelect.value).toBe('gemini-1.5-pro');
    });
  });

  // ── 2.3-E: Badge display ─────────────────────────────────────────────────
  describe('active value badge', () => {
    it('shows "Default (Azure / ChatGPT-UAT)" badge when no override is set', () => {
      renderComponent(null, null);

      // The badge element has data-testid="agent-model-badge"
      const badge = screen.getByTestId('agent-model-badge');
      expect(badge.textContent).toMatch(/Default.*Azure.*ChatGPT-UAT/i);
    });

    it('shows the resolved provider + model when an override is set', () => {
      renderComponent('google', 'gemini-2.0-flash');

      const badge = screen.getByTestId('agent-model-badge');
      expect(badge.textContent).toMatch(/google/i);
      expect(badge.textContent).toMatch(/gemini-2\.0-flash/i);
    });
  });

  // ── 2.3-F: Label renders ─────────────────────────────────────────────────
  describe('label', () => {
    it('renders the agent label text', () => {
      renderComponent(null, null);

      expect(screen.getByText('Observation Agent')).toBeTruthy();
    });
  });
});
