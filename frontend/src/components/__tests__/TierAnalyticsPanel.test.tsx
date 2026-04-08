import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mockSettingsService = {
  getTierDistribution: vi.fn(),
  getStrategyEffectiveness: vi.fn(),
};

vi.mock('../../services/settingsService', () => ({
  default: mockSettingsService,
}));

describe('TierAnalyticsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockSettingsService.getTierDistribution.mockResolvedValue({
      total_executions: 175,
      tier1_success: 11,
      tier1_failure: 164,
      tier2_success: 134,
      tier2_failure: 30,
      tier3_success: 28,
      tier3_failure: 2,
      overall_success_rate: 98.86,
      tier1_success_rate: 6.29,
      tier2_success_rate: 81.71,
      tier3_success_rate: 93.33,
      avg_tier1_time_ms: 798.17,
      avg_tier2_time_ms: 7811.27,
      avg_tier3_time_ms: 8860.28,
    });

    mockSettingsService.getStrategyEffectiveness.mockResolvedValue([
      {
        strategy: 'option_c',
        total_executions: 175,
        successful_executions: 173,
        failed_executions: 2,
        success_rate: 98.86,
        avg_execution_time_ms: 11090.51,
        tier1_percentage: 6.29,
        tier2_percentage: 76.57,
        tier3_percentage: 16.0,
        cost_estimate: 'medium',
      },
    ]);
  });

  it('renders analytics from the current backend response shape', async () => {
    const { TierAnalyticsPanel } = await import('../TierAnalyticsPanel');

    render(<TierAnalyticsPanel />);

    expect(await screen.findByText('Tier Distribution')).toBeInTheDocument();
    expect(screen.getAllByText('175').length).toBeGreaterThan(0);
    expect(screen.getAllByText('76.6%').length).toBeGreaterThan(0);
    expect(screen.getByText('Option C: Maximum Reliability')).toBeInTheDocument();
    expect(screen.getByText(/medium cost/i)).toBeInTheDocument();
  });
});