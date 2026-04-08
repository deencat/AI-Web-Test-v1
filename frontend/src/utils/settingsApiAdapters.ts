import type {
  ExecutionSettings,
  FallbackStrategy,
  StrategyEffectivenessStats,
  TierDistributionStats,
} from '../types/api';

type RawRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is RawRecord =>
  value !== null && typeof value === 'object';

const readNumber = (value: unknown, fallback = 0): number =>
  typeof value === 'number' && Number.isFinite(value) ? value : fallback;

const readBoolean = (value: unknown, fallback = false): boolean =>
  typeof value === 'boolean' ? value : fallback;

const readString = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : fallback;

const readFallbackStrategy = (
  value: unknown,
  fallback: FallbackStrategy = 'option_c',
): FallbackStrategy => {
  if (value === 'option_a' || value === 'option_b' || value === 'option_c') {
    return value;
  }
  return fallback;
};

const readCostLevel = (
  value: unknown,
  fallback: StrategyEffectivenessStats['estimated_cost'] = 'medium',
): StrategyEffectivenessStats['estimated_cost'] => {
  if (value === 'low' || value === 'medium' || value === 'high') {
    return value;
  }
  return fallback;
};

export const normalizeExecutionSettings = (raw: unknown): ExecutionSettings => {
  const data = isRecord(raw) ? raw : {};

  return {
    id: readNumber(data['id']),
    user_id: readNumber(data['user_id']),
    fallback_strategy: readFallbackStrategy(data['fallback_strategy']),
    timeout_per_tier_seconds: readNumber(data['timeout_per_tier_seconds'], 30),
    max_retry_per_tier: readNumber(data['max_retry_per_tier'], 1),
    track_fallback_reasons: readBoolean(
      data['track_fallback_reasons'],
      readBoolean(data['track_token_usage'], true),
    ),
    track_strategy_effectiveness: readBoolean(
      data['track_strategy_effectiveness'],
      readBoolean(data['track_execution_time'], readBoolean(data['track_success_rate'], true)),
    ),
    created_at: readString(data['created_at']),
    updated_at: readString(data['updated_at']),
  };
};

export const normalizeTierDistributionStats = (raw: unknown): TierDistributionStats => {
  const data = isRecord(raw) ? raw : {};
  const tier1Executions = readNumber(
    data['tier1_executions'],
    readNumber(data['tier1_success']),
  );
  const tier2Executions = readNumber(
    data['tier2_executions'],
    readNumber(data['tier2_success']),
  );
  const tier3Executions = readNumber(
    data['tier3_executions'],
    readNumber(data['tier3_success']) + readNumber(data['tier3_failure']),
  );
  const totalExecutions = readNumber(
    data['total_executions'],
    tier1Executions + tier2Executions + tier3Executions,
  );

  return {
    user_id: readNumber(data['user_id']),
    total_executions: totalExecutions,
    tier1_executions: tier1Executions,
    tier2_executions: tier2Executions,
    tier3_executions: tier3Executions,
    tier1_percentage: readNumber(
      data['tier1_percentage'],
      totalExecutions > 0 ? (tier1Executions / totalExecutions) * 100 : 0,
    ),
    tier2_percentage: readNumber(
      data['tier2_percentage'],
      totalExecutions > 0 ? (tier2Executions / totalExecutions) * 100 : 0,
    ),
    tier3_percentage: readNumber(
      data['tier3_percentage'],
      totalExecutions > 0 ? (tier3Executions / totalExecutions) * 100 : 0,
    ),
    tier1_success_rate: readNumber(data['tier1_success_rate']),
    tier2_success_rate: readNumber(data['tier2_success_rate']),
    tier3_success_rate: readNumber(data['tier3_success_rate']),
    tier1_avg_time_ms: readNumber(data['tier1_avg_time_ms'], readNumber(data['avg_tier1_time_ms'])),
    tier2_avg_time_ms: readNumber(data['tier2_avg_time_ms'], readNumber(data['avg_tier2_time_ms'])),
    tier3_avg_time_ms: readNumber(data['tier3_avg_time_ms'], readNumber(data['avg_tier3_time_ms'])),
  };
};

export const normalizeStrategyEffectivenessStats = (
  raw: unknown,
): StrategyEffectivenessStats[] => {
  const entries = Array.isArray(raw)
    ? raw
    : isRecord(raw) && Array.isArray(raw['strategies'])
    ? raw['strategies']
    : [];

  return entries.filter(isRecord).map((entry) => ({
    strategy: readFallbackStrategy(entry['strategy']),
    total_executions: readNumber(entry['total_executions']),
    successful_executions: readNumber(entry['successful_executions']),
    failed_executions: readNumber(entry['failed_executions']),
    success_rate: readNumber(entry['success_rate']),
    avg_execution_time_ms: readNumber(entry['avg_execution_time_ms']),
    tier1_final_count: readNumber(entry['tier1_final_count']),
    tier2_final_count: readNumber(entry['tier2_final_count']),
    tier3_final_count: readNumber(entry['tier3_final_count']),
    tier1_percentage: readNumber(entry['tier1_percentage']),
    tier2_percentage: readNumber(entry['tier2_percentage']),
    tier3_percentage: readNumber(entry['tier3_percentage']),
    estimated_cost: readCostLevel(
      entry['estimated_cost'],
      readCostLevel(entry['cost_estimate']),
    ),
  }));
};