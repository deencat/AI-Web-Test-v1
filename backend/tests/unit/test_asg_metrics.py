"""Unit tests for ASG metrics and canary rollback helpers."""
from __future__ import annotations

import pytest

from app.services.asg_metrics import (
    ASGMetrics,
    CANARY_FALLBACK_RATE_MAX,
    CANARY_REPLAY_PASS_MIN,
    evaluate_canary_rollback,
    get_asg_metrics,
    reset_asg_metrics,
)


@pytest.fixture(autouse=True)
def _reset_metrics():
    reset_asg_metrics()
    yield
    reset_asg_metrics()


class TestASGMetricsRates:
    def test_rate_getters_zero_denominator(self):
        metrics = ASGMetrics()
        assert metrics.plan_success_rate() == 0.0
        assert metrics.synthesis_success_rate() == 0.0
        assert metrics.replay_pass_rate() == 0.0
        assert metrics.fallback_rate() == 0.0

    def test_rate_static_zero_denominator(self):
        assert ASGMetrics._rate(0, 0) == 0.0
        assert ASGMetrics._rate(1, -1) == 0.0

    def test_rate_getters_after_records(self):
        metrics = ASGMetrics()
        metrics.record_plan(graph_id=1, success=True, path_count=2)
        metrics.record_plan(graph_id=1, success=False, path_count=0)
        assert metrics.plan_success_rate() == 0.5

        metrics.record_synthesis(graph_id=1, success=True, test_count=1)
        assert metrics.synthesis_success_rate() == 1.0

        metrics.record_replay(passed=True, graph_id=1, execution_id=10)
        metrics.record_replay(passed=False, graph_id=1, execution_id=11)
        assert metrics.replay_pass_rate() == 0.5

        metrics.record_fallback("low_confidence", graph_id=1)
        rate = metrics.fallback_rate()
        assert 0.0 < rate <= 1.0

    def test_get_asg_metrics_singleton(self):
        a = get_asg_metrics()
        b = get_asg_metrics()
        assert a is b


class TestEvaluateCanaryRollback:
    def test_no_rollback_when_healthy(self):
        result = evaluate_canary_rollback(replay_pass_rate=0.9, fallback_rate=0.1)
        assert result["rollback_recommended"] is False
        assert result["rollback_triggers"] == []

    def test_rollback_low_replay(self):
        result = evaluate_canary_rollback(
            replay_pass_rate=0.75,
            fallback_rate=0.1,
            replay_pass_min=CANARY_REPLAY_PASS_MIN,
        )
        assert result["rollback_recommended"] is True
        assert "replay_pass_below_threshold" in result["rollback_triggers"]

    def test_rollback_high_fallback(self):
        result = evaluate_canary_rollback(
            replay_pass_rate=0.9,
            fallback_rate=0.5,
            fallback_rate_max=CANARY_FALLBACK_RATE_MAX,
        )
        assert result["rollback_recommended"] is True
        assert "fallback_rate_above_threshold" in result["rollback_triggers"]
