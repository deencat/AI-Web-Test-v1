"""
ASG observability — structured metrics logging and canary rollback checks.

Feature 3 Phase 3: operational metrics without external dashboard infra.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Rollback triggers per spec §8
CANARY_REPLAY_PASS_MIN = 0.80
CANARY_FALLBACK_RATE_MAX = 0.40


@dataclass
class ASGMetricsSnapshot:
    """In-memory counters for ASG pipeline stages."""

    build_count: int = 0
    build_duration_ms_total: int = 0
    node_count_total: int = 0
    edge_count_total: int = 0
    confidence_score_sum: float = 0.0
    confidence_below_threshold_count: int = 0
    plan_attempts: int = 0
    plan_successes: int = 0
    synthesis_attempts: int = 0
    synthesis_successes: int = 0
    fallback_total: int = 0
    fallback_reasons: Dict[str, int] = field(default_factory=dict)
    replay_attempts: int = 0
    replay_passes: int = 0


class ASGMetrics:
    """Record ASG metrics and emit structured logs with consistent keys."""

    def __init__(self) -> None:
        self._snapshot = ASGMetricsSnapshot()

    @property
    def snapshot(self) -> ASGMetricsSnapshot:
        return self._snapshot

    def record_build(
        self,
        *,
        graph_id: int,
        duration_ms: int,
        node_count: int,
        edge_count: int,
        confidence_mean: float,
        below_threshold_count: int = 0,
    ) -> None:
        self._snapshot.build_count += 1
        self._snapshot.build_duration_ms_total += duration_ms
        self._snapshot.node_count_total += node_count
        self._snapshot.edge_count_total += edge_count
        self._snapshot.confidence_score_sum += confidence_mean
        self._snapshot.confidence_below_threshold_count += below_threshold_count
        payload = {
            "metric": "asg_build",
            "graph_id": graph_id,
            "asg_build_duration_ms": duration_ms,
            "asg_node_count": node_count,
            "asg_edge_count": edge_count,
            "asg_confidence_score_mean": round(confidence_mean, 4),
            "asg_confidence_below_threshold_count": below_threshold_count,
        }
        logger.info("ASG build metrics", extra=payload)

    def record_plan(self, *, graph_id: int, success: bool, path_count: int = 0) -> None:
        self._snapshot.plan_attempts += 1
        if success:
            self._snapshot.plan_successes += 1
        rate = self._rate(self._snapshot.plan_successes, self._snapshot.plan_attempts)
        logger.info(
            "ASG plan metrics graph_id=%s success=%s path_count=%s asg_plan_success_rate=%.4f",
            graph_id,
            success,
            path_count,
            rate,
            extra={
                "metric": "asg_plan",
                "graph_id": graph_id,
                "asg_plan_success_rate": rate,
                "path_count": path_count,
            },
        )

    def record_synthesis(self, *, graph_id: int, success: bool, test_count: int = 0) -> None:
        self._snapshot.synthesis_attempts += 1
        if success:
            self._snapshot.synthesis_successes += 1
        rate = self._rate(self._snapshot.synthesis_successes, self._snapshot.synthesis_attempts)
        logger.info(
            "ASG synthesis metrics graph_id=%s success=%s test_count=%s asg_synthesis_success_rate=%.4f",
            graph_id,
            success,
            test_count,
            rate,
            extra={
                "metric": "asg_synthesis",
                "graph_id": graph_id,
                "asg_synthesis_success_rate": rate,
                "test_count": test_count,
            },
        )

    def record_fallback(self, reason_code: str, *, graph_id: Optional[int] = None) -> None:
        self._snapshot.fallback_total += 1
        self._snapshot.fallback_reasons[reason_code] = (
            self._snapshot.fallback_reasons.get(reason_code, 0) + 1
        )
        logger.info(
            "ASG fallback graph_id=%s fallback_reason_code=%s asg_fallback_total=%s",
            graph_id,
            reason_code,
            self._snapshot.fallback_total,
            extra={
                "metric": "asg_fallback",
                "graph_id": graph_id,
                "fallback_reason_code": reason_code,
                "asg_fallback_total": self._snapshot.fallback_total,
            },
        )

    def record_replay(
        self,
        *,
        passed: bool,
        graph_id: int,
        execution_id: int,
    ) -> None:
        self._snapshot.replay_attempts += 1
        if passed:
            self._snapshot.replay_passes += 1
        pass_rate = self._rate(self._snapshot.replay_passes, self._snapshot.replay_attempts)
        logger.info(
            "ASG replay graph_id=%s execution_id=%s passed=%s asg_replay_pass_rate=%.4f",
            graph_id,
            execution_id,
            passed,
            pass_rate,
            extra={
                "metric": "asg_replay",
                "graph_id": graph_id,
                "execution_id": execution_id,
                "asg_replay_pass_rate": pass_rate,
            },
        )

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(numerator / denominator, 4)

    def plan_success_rate(self) -> float:
        return self._rate(self._snapshot.plan_successes, self._snapshot.plan_attempts)

    def synthesis_success_rate(self) -> float:
        return self._rate(self._snapshot.synthesis_successes, self._snapshot.synthesis_attempts)

    def replay_pass_rate(self) -> float:
        return self._rate(self._snapshot.replay_passes, self._snapshot.replay_attempts)

    def fallback_rate(self) -> float:
        attempts = (
            self._snapshot.plan_attempts
            + self._snapshot.synthesis_attempts
            + self._snapshot.fallback_total
        )
        if attempts <= 0:
            return 0.0
        return round(self._snapshot.fallback_total / attempts, 4)


_metrics_singleton: Optional[ASGMetrics] = None


def get_asg_metrics() -> ASGMetrics:
    global _metrics_singleton
    if _metrics_singleton is None:
        _metrics_singleton = ASGMetrics()
    return _metrics_singleton


def reset_asg_metrics() -> None:
    """Reset in-memory counters (testing helper)."""
    global _metrics_singleton
    _metrics_singleton = ASGMetrics()


def evaluate_canary_rollback(
    *,
    replay_pass_rate: float,
    fallback_rate: float,
    replay_pass_min: float = CANARY_REPLAY_PASS_MIN,
    fallback_rate_max: float = CANARY_FALLBACK_RATE_MAX,
) -> Dict[str, Any]:
    """
    Detect rollback conditions per spec §8:
    replay pass < 80% or fallback rate > 40%.
    """
    triggers: list[str] = []
    if replay_pass_rate < replay_pass_min:
        triggers.append("replay_pass_below_threshold")
    if fallback_rate > fallback_rate_max:
        triggers.append("fallback_rate_above_threshold")

    return {
        "rollback_recommended": bool(triggers),
        "rollback_triggers": triggers,
        "replay_pass_rate": round(replay_pass_rate, 4),
        "fallback_rate": round(fallback_rate, 4),
        "replay_pass_min": replay_pass_min,
        "fallback_rate_max": fallback_rate_max,
    }
