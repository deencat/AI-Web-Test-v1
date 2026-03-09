/**
 * SettingsPage.test.tsx — Sprint 10.5 Feature 1: OpenRouter Free Models UI
 *
 * TDD RED → GREEN cycle.
 * Tests render behaviour of model dropdowns in the AI Provider sections:
 *  - Free models grouped under "Free Models ($0/M tokens)" optgroup
 *  - Paid models grouped under "Paid Models" optgroup
 *  - Free models have "(Free)" label appended
 *  - Works with model_options if available, falls back to :free suffix detection
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { AvailableProvider } from '../../types/api';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

vi.mock('../../components/common/Card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('../../components/common/Input', () => ({
  Input: ({ label }: { label: string }) => <input aria-label={label} />,
}));

vi.mock('../../components/common/Button', () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}));

vi.mock('../../components/FeedbackDataSync', () => ({
  FeedbackDataSync: () => <div data-testid="feedback-sync" />,
}));

vi.mock('../../components/ExecutionSettingsPanel', () => ({
  ExecutionSettingsPanel: () => <div data-testid="execution-settings" />,
}));

vi.mock('../../components/TierAnalyticsPanel', () => ({
  TierAnalyticsPanel: () => <div data-testid="tier-analytics" />,
}));

const mockSettingsService = {
  getStagehandProvider: vi.fn(),
  checkStagehandHealth: vi.fn(),
  getAvailableProviders: vi.fn(),
  getUserProviderSettings: vi.fn(),
  getSettings: vi.fn(),
  updateUserProviderSettings: vi.fn(),
  deleteUserProviderSettings: vi.fn(),
  updateStagehandProvider: vi.fn(),
  getExecutionSettings: vi.fn(),
};

vi.mock('../../services/settingsService', () => ({
  default: mockSettingsService,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/** An OpenRouter provider with model_options (Sprint 10.5 rich schema) */
const openrouterProviderWithOptions: AvailableProvider = {
  name: 'openrouter',
  display_name: 'OpenRouter',
  is_configured: true,
  models: [
    'qwen/qwen3-coder-480b-a35b:free',
    'meta-llama/llama-3.3-70b-instruct:free',
    'openai/gpt-oss-120b:free',
    'google/gemini-2.0-flash-exp:free',
    'google/gemini-flash-1.5:free',
    'openai/o1',                          // paid model — no :free suffix
  ],
  recommended_model: 'qwen/qwen3-coder-480b-a35b:free',
  model_options: [
    { id: 'qwen/qwen3-coder-480b-a35b:free', display_name: 'qwen/qwen3-coder-480b-a35b:free', is_free: true },
    { id: 'meta-llama/llama-3.3-70b-instruct:free', display_name: 'meta-llama/llama-3.3-70b-instruct:free', is_free: true },
    { id: 'openai/gpt-oss-120b:free', display_name: 'openai/gpt-oss-120b:free', is_free: true },
    { id: 'google/gemini-2.0-flash-exp:free', display_name: 'google/gemini-2.0-flash-exp:free', is_free: true },
    { id: 'google/gemini-flash-1.5:free', display_name: 'google/gemini-flash-1.5:free', is_free: true },
    { id: 'openai/o1', display_name: 'openai/o1', is_free: false },  // paid
  ],
};

/** A non-OpenRouter provider (no free models) */
const googleProvider: AvailableProvider = {
  name: 'google',
  display_name: 'Google Gemini',
  is_configured: true,
  models: ['gemini-2.0-flash', 'gemini-1.5-pro'],
  recommended_model: 'gemini-2.0-flash',
  model_options: [
    { id: 'gemini-2.0-flash', display_name: 'gemini-2.0-flash', is_free: false },
    { id: 'gemini-1.5-pro', display_name: 'gemini-1.5-pro', is_free: false },
  ],
};

const mockProvidersResponse = {
  providers: [googleProvider, openrouterProviderWithOptions],
  default_generation_provider: 'openrouter',
  default_generation_model: 'qwen/qwen3-coder-480b-a35b:free',
  default_execution_provider: 'openrouter',
  default_execution_model: 'qwen/qwen3-coder-480b-a35b:free',
};

const mockUserSettings = {
  id: 1,
  user_id: 1,
  generation_provider: 'openrouter',
  generation_model: 'qwen/qwen3-coder-480b-a35b:free',
  generation_temperature: 0.7,
  generation_max_tokens: 4096,
  execution_provider: 'openrouter',
  execution_model: 'qwen/qwen3-coder-480b-a35b:free',
  execution_temperature: 0.7,
  execution_max_tokens: 4096,
  stagehand_provider: 'python',
  created_at: '2026-03-09T00:00:00Z',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function renderSettingsPage() {
  const { SettingsPage } = await import('../SettingsPage');
  render(<SettingsPage />);
  // Wait for async data load to complete
  await vi.waitFor(() => {
    expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
  }, { timeout: 3000 });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SettingsPage — OpenRouter free model dropdown grouping (Sprint 10.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockSettingsService.getStagehandProvider.mockResolvedValue({ provider: 'python' });
    mockSettingsService.checkStagehandHealth.mockResolvedValue({ status: 'healthy' });
    mockSettingsService.getAvailableProviders.mockResolvedValue(mockProvidersResponse);
    mockSettingsService.getUserProviderSettings.mockResolvedValue(mockUserSettings);
    mockSettingsService.getSettings.mockResolvedValue({});
    mockSettingsService.getExecutionSettings.mockResolvedValue({});
  });

  // -------------------------------------------------------------------------
  // Grouped optgroup rendering
  // -------------------------------------------------------------------------

  it('renders Free Models optgroup in the generation model dropdown', async () => {
    await renderSettingsPage();
    const freeGroups = screen.getAllByRole('group', { name: /free models/i });
    expect(freeGroups.length).toBeGreaterThanOrEqual(1);
  });

  it('renders Paid Models optgroup in the generation model dropdown', async () => {
    await renderSettingsPage();
    const paidGroups = screen.getAllByRole('group', { name: /paid models/i });
    expect(paidGroups.length).toBeGreaterThanOrEqual(1);
  });

  it('renders Free Models optgroup in the execution model dropdown', async () => {
    await renderSettingsPage();
    const freeGroups = screen.getAllByRole('group', { name: /free models/i });
    // Should appear in both generation AND execution selects
    expect(freeGroups.length).toBeGreaterThanOrEqual(2);
  });

  // -------------------------------------------------------------------------
  // (Free) label on free model options
  // -------------------------------------------------------------------------

  it('appends (Free) label to free model options', async () => {
    await renderSettingsPage();
    const freeModelOption = screen.getAllByRole('option', {
      name: /qwen\/qwen3-coder-480b-a35b:free \(Free\)/i,
    });
    expect(freeModelOption.length).toBeGreaterThanOrEqual(1);
  });

  it('does NOT append (Free) label to paid model options', async () => {
    await renderSettingsPage();
    // Google models are paid; they should not have "(Free)" suffix
    const geminiOptions = screen.queryAllByRole('option', { name: /gemini-2\.0-flash \(Free\)/i });
    expect(geminiOptions.length).toBe(0);
  });

  // -------------------------------------------------------------------------
  // Fallback: no model_options (legacy provider shape)
  // -------------------------------------------------------------------------

  it('falls back to :free suffix detection when model_options is absent', async () => {
    const legacyProvider: AvailableProvider = {
      name: 'openrouter',
      display_name: 'OpenRouter',
      is_configured: true,
      models: ['google/gemini-flash-1.5:free', 'some-paid-model'],
      recommended_model: 'google/gemini-flash-1.5:free',
      // model_options intentionally absent to test fallback
    };
    mockSettingsService.getAvailableProviders.mockResolvedValue({
      ...mockProvidersResponse,
      providers: [googleProvider, legacyProvider],
    });

    await renderSettingsPage();

    const freeGroups = screen.getAllByRole('group', { name: /free models/i });
    expect(freeGroups.length).toBeGreaterThanOrEqual(1);
  });

  // -------------------------------------------------------------------------
  // Model count
  // -------------------------------------------------------------------------

  it('shows all free model options within the Free Models optgroup', async () => {
    await renderSettingsPage();
    const freeGroups = screen.getAllByRole('group', { name: /free models/i });
    // At least one group should contain options
    const firstGroupOptions = freeGroups[0].querySelectorAll('option');
    expect(firstGroupOptions.length).toBeGreaterThanOrEqual(1);
  });
});
