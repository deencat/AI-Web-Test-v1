import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mockSettingsService = {
  getExecutionSettings: vi.fn(),
  getExecutionStrategies: vi.fn(),
  updateExecutionSettings: vi.fn(),
};

vi.mock('../../services/settingsService', () => ({
  default: mockSettingsService,
}));

describe('ExecutionSettingsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockSettingsService.getExecutionSettings.mockResolvedValue({
      fallback_strategy: 'option_c',
      max_retry_per_tier: 1,
      timeout_per_tier_seconds: 30,
      track_fallback_reasons: true,
      track_strategy_effectiveness: false,
      id: 1,
      user_id: 1,
      created_at: '2026-01-19T02:00:33',
      updated_at: '2026-03-31T06:47:53',
    });

    mockSettingsService.getExecutionStrategies.mockResolvedValue([
      {
        name: 'option_c',
        display_name: 'Option C: Maximum Reliability',
        description: 'Tier 1 -> Tier 2 -> Tier 3. Full cascade for highest success rate.',
        cost_level: 'medium',
        performance_level: 'high',
        fallback_chain: ['Tier 1: Playwright', 'Tier 2: Hybrid', 'Tier 3: Stagehand AI'],
        recommended_for: 'Production environments',
        pros: ['Highest success rate'],
        cons: ['Slightly slower on failures'],
      },
    ]);
  });

  it('renders current backend tracking flags with the updated labels', async () => {
    const { ExecutionSettingsPanel } = await import('../ExecutionSettingsPanel');

    render(<ExecutionSettingsPanel />);

    expect(await screen.findByText('3-Tier Execution Settings')).toBeInTheDocument();
    expect(screen.getByLabelText('Track Fallback Reasons')).toBeChecked();
    expect(screen.getByLabelText('Track Strategy Effectiveness')).not.toBeChecked();
  });
});